"""CLI for offline teacher benchmarking against gold_v1 examples.

This command does not call model APIs. It evaluates precomputed prediction rows.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from .benchmark import run_benchmark, write_benchmark_outputs
from .io import load_gold_examples, load_predictions
from .models import SUPPORTED_MODELS, canonical_model_id


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("teacher-benchmark-%Y%m%dT%H%M%SZ")


def parse_args() -> argparse.Namespace:
    """Parse command arguments."""
    parser = argparse.ArgumentParser(description="Run offline teacher benchmark.")
    parser.add_argument(
        "--gold-path",
        default="datasets/gold/gold_v1.jsonl",
        help="Path to gold benchmark jsonl.",
    )
    parser.add_argument(
        "--predictions-path",
        required=True,
        help="Prediction jsonl file or directory of jsonl files.",
    )
    parser.add_argument(
        "--output-root",
        default="outputs/teacher_benchmark",
        help="Root output directory.",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id; generated automatically when omitted.",
    )
    parser.add_argument(
        "--models",
        default=",".join(SUPPORTED_MODELS),
        help="Comma-separated model ids/aliases to evaluate.",
    )
    parser.add_argument(
        "--strict-full-coverage",
        action="store_true",
        help="Fail if any selected model is missing predictions for any gold example.",
    )
    return parser.parse_args()


def main() -> None:
    """Execute benchmark and write artifacts."""
    args = parse_args()

    gold_path = Path(args.gold_path)
    predictions_path = Path(args.predictions_path)
    run_id = args.run_id or _default_run_id()
    output_dir = Path(args.output_root) / run_id

    selected_models = tuple(
        canonical_model_id(item.strip()) for item in args.models.split(",") if item.strip()
    )
    if not selected_models:
        raise ValueError("No models selected.")

    gold_examples = load_gold_examples(gold_path)
    predictions = load_predictions(predictions_path)

    per_example_rows, summaries, manifest = run_benchmark(
        gold_examples=gold_examples,
        predictions=predictions,
        model_ids=selected_models,
    )
    manifest["run_id"] = run_id
    manifest["gold_path"] = str(gold_path)
    manifest["predictions_path"] = str(predictions_path)

    if args.strict_full_coverage:
        missing = [row for row in summaries if row.coverage < 1.0]
        if missing:
            names = ", ".join(item.model_id for item in missing)
            raise ValueError(f"Strict coverage failed. Missing predictions for models: {names}")

    write_benchmark_outputs(
        output_dir=output_dir,
        run_id=run_id,
        per_example_rows=per_example_rows,
        summaries=summaries,
        manifest=manifest,
    )

    print(f"Wrote benchmark artifacts to: {output_dir}")


if __name__ == "__main__":
    main()
