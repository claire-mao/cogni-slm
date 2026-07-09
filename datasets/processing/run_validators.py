"""Run reusable dataset validators and write markdown report."""

from __future__ import annotations

import argparse
from pathlib import Path

from validators import ValidatorConfig, render_markdown_report, validate_directory


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Validate normalized dataset files.")
    parser.add_argument(
        "--input-dir",
        default="datasets/processed/normalized",
        help="Directory with normalized JSONL files.",
    )
    parser.add_argument(
        "--report-path",
        default="reports/validation_report.md",
        help="Markdown report output path.",
    )
    parser.add_argument("--label-min", type=float, default=0.0)
    parser.add_argument("--label-max", type=float, default=60.0)
    parser.add_argument("--min-words", type=int, default=20)
    parser.add_argument("--max-words", type=int, default=1500)
    parser.add_argument("--max-examples", type=int, default=25)
    parser.add_argument(
        "--include-combined",
        action="store_true",
        help="Also validate all_datasets.jsonl (excluded by default to avoid duplicate counting).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    input_dir = Path(args.input_dir)
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    config = ValidatorConfig(
        label_min=args.label_min,
        label_max=args.label_max,
        min_word_count=args.min_words,
        max_word_count=args.max_words,
        max_examples_per_check=args.max_examples,
    )

    results = validate_directory(input_dir, config, include_combined=args.include_combined)
    report = render_markdown_report(results, config)
    report_path.write_text(report, encoding="utf-8")

    print(f"files_validated={len(results)}")
    print(f"report={report_path}")


if __name__ == "__main__":
    main()
