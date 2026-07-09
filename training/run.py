"""CLI entrypoint for Unsloth QLoRA training pipeline.

Default behavior: initialize only (no training starts).
Pass --do-train to explicitly start training.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import PipelineConfig, load_pipeline_config, save_pipeline_config
from .pipeline import run_pipeline

NEW_DEFAULT_CONFIG = Path("configs/training/qlora_default.json")
LEGACY_DEFAULT_CONFIG = Path("training/configs/qlora_default.json")
NEW_DEFAULT_RESOLVED = Path("configs/training/qlora_resolved.json")
LEGACY_DEFAULT_RESOLVED = Path("training/configs/qlora_resolved.json")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Run Unsloth QLoRA training pipeline.")
    parser.add_argument("--config", default=str(NEW_DEFAULT_CONFIG))
    parser.add_argument("--model-id", default="")
    parser.add_argument("--dataset-path", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--checkpoint-dir", default="")
    parser.add_argument("--metadata-path", default="")
    parser.add_argument("--eval-log-path", default="")
    parser.add_argument("--do-train", action="store_true")
    parser.add_argument("--save-resolved-config", default=str(NEW_DEFAULT_RESOLVED))
    return parser.parse_args()


def apply_overrides(config: PipelineConfig, args: argparse.Namespace) -> PipelineConfig:
    """Apply CLI overrides to loaded config."""
    if args.model_id:
        config.model_id = args.model_id
    if args.dataset_path:
        config.dataset.dataset_path = args.dataset_path
    if args.output_dir:
        config.trainer.output_dir = args.output_dir
    if args.checkpoint_dir:
        config.checkpoint_dir = args.checkpoint_dir
    if args.metadata_path:
        config.metadata_path = args.metadata_path
    if args.eval_log_path:
        config.eval_log_path = args.eval_log_path
    return config


def main() -> None:
    """Run pipeline initialization/training."""
    args = parse_args()

    config_path = Path(args.config)
    if (
        not config_path.exists()
        and config_path == NEW_DEFAULT_CONFIG
        and LEGACY_DEFAULT_CONFIG.exists()
    ):
        config_path = LEGACY_DEFAULT_CONFIG
    if config_path.exists():
        config = load_pipeline_config(config_path)
    else:
        config = PipelineConfig()

    config = apply_overrides(config, args)

    resolved_config_path = Path(args.save_resolved_config)
    if (
        resolved_config_path == NEW_DEFAULT_RESOLVED
        and not resolved_config_path.parent.exists()
        and LEGACY_DEFAULT_RESOLVED.parent.exists()
    ):
        resolved_config_path = LEGACY_DEFAULT_RESOLVED
    save_pipeline_config(config, resolved_config_path)

    metadata = run_pipeline(config, do_train=args.do_train)

    print(json.dumps(metadata, indent=2, ensure_ascii=False))
    if not args.do_train:
        print("training_started=False")


if __name__ == "__main__":
    main()
