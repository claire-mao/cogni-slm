"""Configuration objects for the local Unsloth training pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class QLoRAConfig:
    """QLoRA and adapter settings."""

    max_seq_length: int = 2048
    load_in_4bit: bool = True
    lora_r: int = 16
    lora_alpha: int = 16
    lora_dropout: float = 0.0
    bias: str = "none"
    use_gradient_checkpointing: str = "unsloth"
    random_state: int = 42
    target_modules: list[str] = field(
        default_factory=lambda: [
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ]
    )


@dataclass
class DatasetConfig:
    """Dataset loading and preprocessing settings."""

    dataset_path: str = "datasets/training"
    train_split: str = "train"
    eval_split: str = "validation"
    text_field: str = "text"
    prompt_field: str = "prompt"
    essay_field: str = "essay"
    score_field: str = "score"
    max_train_samples: int = 0
    max_eval_samples: int = 0


@dataclass
class TrainerConfig:
    """Trainer/runtime arguments for SFT."""

    output_dir: str = "models/unsloth_qlora"
    logging_dir: str = "outputs/training_logs"
    num_train_epochs: float = 1.0
    learning_rate: float = 2e-4
    weight_decay: float = 0.0
    warmup_ratio: float = 0.03
    lr_scheduler_type: str = "cosine"
    seed: int = 42

    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8

    eval_steps: int = 50
    save_steps: int = 50
    logging_steps: int = 10
    save_total_limit: int = 3

    evaluation_strategy: str = "steps"
    save_strategy: str = "steps"
    logging_strategy: str = "steps"

    report_to: list[str] = field(default_factory=list)


@dataclass
class PipelineConfig:
    """Top-level training pipeline configuration."""

    model_id: str = "Qwen/Qwen3-1.7B-Instruct"
    qlora: QLoRAConfig = field(default_factory=QLoRAConfig)
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    trainer: TrainerConfig = field(default_factory=TrainerConfig)

    checkpoint_dir: str = "models/unsloth_qlora/checkpoints"
    metadata_path: str = "models/unsloth_qlora/run_metadata.json"
    eval_log_path: str = "outputs/training_logs/eval_metrics.jsonl"


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Recursively update dict values."""
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


def load_pipeline_config(path: str | Path) -> PipelineConfig:
    """Load PipelineConfig from JSON file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    payload = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Config payload must be a JSON object.")

    base = asdict(PipelineConfig())
    merged = _deep_update(base, payload)

    return PipelineConfig(
        model_id=str(merged["model_id"]),
        qlora=QLoRAConfig(**merged["qlora"]),
        dataset=DatasetConfig(**merged["dataset"]),
        trainer=TrainerConfig(**merged["trainer"]),
        checkpoint_dir=str(merged["checkpoint_dir"]),
        metadata_path=str(merged["metadata_path"]),
        eval_log_path=str(merged["eval_log_path"]),
    )


def save_pipeline_config(config: PipelineConfig, path: str | Path) -> None:
    """Save pipeline config to JSON."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
