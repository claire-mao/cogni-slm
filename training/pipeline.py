"""Training pipeline assembly for Unsloth + QLoRA."""

from __future__ import annotations

import inspect
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
    kwargs: dict[str, Any] = {
        "output_dir": config.trainer.output_dir,
        "logging_dir": config.trainer.logging_dir,
        "num_train_epochs": config.trainer.num_train_epochs,
        "learning_rate": config.trainer.learning_rate,
        "weight_decay": config.trainer.weight_decay,
        "warmup_ratio": config.trainer.warmup_ratio,
        "lr_scheduler_type": config.trainer.lr_scheduler_type,
        "seed": config.trainer.seed,
        "per_device_train_batch_size": config.trainer.per_device_train_batch_size,
        "per_device_eval_batch_size": config.trainer.per_device_eval_batch_size,
        "gradient_accumulation_steps": config.trainer.gradient_accumulation_steps,
        "eval_steps": config.trainer.eval_steps,
        "save_strategy": config.trainer.save_strategy,
        "save_steps": config.trainer.save_steps,
        "save_total_limit": config.trainer.save_total_limit,
        "logging_strategy": config.trainer.logging_strategy,
        "logging_steps": config.trainer.logging_steps,
        "report_to": config.trainer.report_to,
        "fp16": fp16_available,
        "bf16": bf16_available,
        "remove_unused_columns": False,
    }

    params = inspect.signature(TrainingArguments.__init__).parameters
    if "evaluation_strategy" in params:
        kwargs["evaluation_strategy"] = evaluation_strategy
    elif "eval_strategy" in params:
        kwargs["eval_strategy"] = evaluation_strategy

    return TrainingArguments(**kwargs)


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
    """Construct a trainer (TRL SFTTrainer preferred, Transformers Trainer fallback)."""
    callbacks = [EvalMetricsCallback(eval_log_path)] if eval_dataset is not None else []

    try:
        from trl import SFTTrainer

        signature = inspect.signature(SFTTrainer.__init__).parameters
        kwargs: dict[str, Any] = {
            "model": model,
            "train_dataset": train_dataset,
            "eval_dataset": eval_dataset,
            "args": training_args,
            "callbacks": callbacks,
        }
        if "tokenizer" in signature:
            kwargs["tokenizer"] = tokenizer
        if "processing_class" in signature:
            kwargs["processing_class"] = tokenizer
        if "dataset_text_field" in signature:
            kwargs["dataset_text_field"] = "text"
        if "max_seq_length" in signature:
            kwargs["max_seq_length"] = max_seq_length
        if "packing" in signature:
            kwargs["packing"] = False

        return SFTTrainer(**kwargs)
    except Exception:
        # Fallback for TRL/Transformers compatibility issues in constrained envs.
        from transformers import DataCollatorForLanguageModeling, Trainer

        def tokenize_batch(batch: dict[str, Any]) -> dict[str, Any]:
            return tokenizer(
                batch["text"],
                truncation=True,
                max_length=max_seq_length,
            )

        tokenized_train = train_dataset.map(
            tokenize_batch,
            batched=True,
            remove_columns=train_dataset.column_names,
        )
        tokenized_eval = (
            eval_dataset.map(
                tokenize_batch,
                batched=True,
                remove_columns=eval_dataset.column_names,
            )
            if eval_dataset is not None
            else None
        )

        collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
        return Trainer(
            model=model,
            args=training_args,
            train_dataset=tokenized_train,
            eval_dataset=tokenized_eval,
            data_collator=collator,
            callbacks=callbacks,
        )


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
