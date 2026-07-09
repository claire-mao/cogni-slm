"""Initialize an Unsloth + LoRA training pipeline without running training."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Initialize Unsloth training components (no training run)."
    )
    parser.add_argument(
        "--model-id",
        default=os.getenv("COGNI_BASE_MODEL", "Qwen/Qwen3-1.7B-Instruct"),
        help="Base model identifier.",
    )
    parser.add_argument(
        "--dataset-path",
        default="datasets/processed/placeholder_train.jsonl",
        help="Placeholder dataset path for initialization checks.",
    )
    parser.add_argument("--max-seq-length", type=int, default=2048)
    parser.add_argument("--load-in-4bit", action="store_true")
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=16)
    parser.add_argument("--lora-dropout", type=float, default=0.0)
    return parser.parse_args()


def ensure_dataset_placeholder(dataset_path: Path) -> dict[str, Any]:
    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    if not dataset_path.exists():
        sample = {
            "text": (
                "fallacy_hypothesis: hasty_generalization\n"
                "reasoning_diagnosis: The argument generalizes from too few examples.\n"
                "analogy: source_scenario: ... mapping: ... limits: ...\n"
                "repair: Use broader evidence before concluding.\n"
                "confidence_note: Moderate confidence."
            )
        }
        dataset_path.write_text(json.dumps(sample, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"dataset_path": str(dataset_path), "exists": dataset_path.exists()}


def main() -> None:
    args = parse_args()
    dataset_info = ensure_dataset_placeholder(Path(args.dataset_path))

    try:
        from unsloth import FastLanguageModel
    except ImportError as exc:
        raise RuntimeError(
            "Unsloth is not installed. Install required packages first, for example:\n"
            "pip install 'unsloth[colab-new]' datasets trl peft bitsandbytes "
            "accelerate transformers"
        ) from exc

    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise RuntimeError("datasets package is not installed. Run: pip install datasets") from exc

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model_id,
        max_seq_length=args.max_seq_length,
        dtype=None,
        load_in_4bit=args.load_in_4bit,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=args.lora_r,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
    )

    dataset = load_dataset("json", data_files={"train": str(dataset_info["dataset_path"])})
    train_rows = len(dataset["train"])

    print("Unsloth training scaffold initialized successfully.")
    print(f"model_id={args.model_id}")
    print(f"tokenizer_loaded={tokenizer is not None}")
    print(f"dataset_path={dataset_info['dataset_path']}")
    print(f"dataset_rows={train_rows}")
    print("training_started=False")


if __name__ == "__main__":
    main()
