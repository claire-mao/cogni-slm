"""Training pipeline assembly for Unsloth + QLoRA."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from transformers import TrainingArguments

from .callbacks import EvalMetricsCallback
from .config import PipelineConfig
from .data import prepare_train_eval_datasets
from .model import load_model_and_tokenizer


def build_training_arguments(config: PipelineConfig, has_eval: bool) -> TrainingArguments:
    """Create transformers.TrainingArguments for SFT training."""
    bf16_available = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    fp16_available = torch.cuda.is_available() and not bf16_available

    evaluation_strategy = config.trainer.evaluation_strategy if has_eval else "no"

    return TrainingArguments(
        output_dir=config.trainer.output_dir,
        logging_dir=config.trainer.logging_dir,
        num_train_epochs=config.trainer.num_train_epochs,
        learning_rate=config.trainer.learning_rate,
        weight_decay=config.trainer.weight_decay,
        warmup_ratio=config.trainer.warmup_ratio,
        lr_scheduler_type=config.trainer.lr_scheduler_type,
        seed=config.trainer.seed,
        per_device_train_batch_size=config.trainer.per_device_train_batch_size,
        per_device_eval_batch_size=config.trainer.per_device_eval_batch_size,
        gradient_accumulation_steps=config.trainer.gradient_accumulation_steps,
        evaluation_strategy=evaluation_strategy,
        eval_steps=config.trainer.eval_steps,
        save_strategy=config.trainer.save_strategy,
        save_steps=config.trainer.save_steps,
        save_total_limit=config.trainer.save_total_limit,
        logging_strategy=config.trainer.logging_strategy,
        logging_steps=config.trainer.logging_steps,
        report_to=config.trainer.report_to,
        fp16=fp16_available,
        bf16=bf16_available,
        remove_unused_columns=False,
    )


def _build_trainer(
    *,
    model: Any,
    tokenizer: Any,
    train_dataset: Any,
    eval_dataset: Any,
    training_args: TrainingArguments,
    max_seq_length: int,
    eval_log_path: str,
) -> Any:
    """Construct TRL SFTTrainer instance."""
    try:
        from trl import SFTTrainer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("trl is required. Install with: pip install trl") from exc

    callbacks = [EvalMetricsCallback(eval_log_path)] if eval_dataset is not None else []

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        dataset_text_field="text",
        max_seq_length=max_seq_length,
        packing=False,
        args=training_args,
        callbacks=callbacks,
    )
    return trainer


def _write_metadata(path: str | Path, payload: dict[str, Any]) -> None:
    metadata_path = Path(path)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def initialize_pipeline(config: PipelineConfig) -> dict[str, Any]:
    """Initialize model, tokenizer, datasets, training args, and trainer."""
    model, tokenizer = load_model_and_tokenizer(config)
    train_dataset, eval_dataset = prepare_train_eval_datasets(config)
    training_args = build_training_arguments(config, has_eval=eval_dataset is not None)

    trainer = _build_trainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        training_args=training_args,
        max_seq_length=config.qlora.max_seq_length,
        eval_log_path=config.eval_log_path,
    )

    return {
        "model": model,
        "tokenizer": tokenizer,
        "train_dataset": train_dataset,
        "eval_dataset": eval_dataset,
        "training_args": training_args,
        "trainer": trainer,
    }


def run_pipeline(config: PipelineConfig, do_train: bool = False) -> dict[str, Any]:
    """Initialize pipeline and optionally run training."""
    state = initialize_pipeline(config)

    train_dataset = state["train_dataset"]
    eval_dataset = state["eval_dataset"]

    metadata: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": config.model_id,
        "config": asdict(config),
        "train_rows": int(len(train_dataset)),
        "eval_rows": int(len(eval_dataset)) if eval_dataset is not None else 0,
        "training_started": bool(do_train),
        "status": "initialized",
    }

    if do_train:
        trainer = state["trainer"]
        trainer.train()
        trainer.save_model(config.checkpoint_dir)
        state["tokenizer"].save_pretrained(config.checkpoint_dir)
        metadata["status"] = "trained"

    _write_metadata(config.metadata_path, metadata)
    return metadata
