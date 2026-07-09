"""Filter generated dataset examples and emit summary statistics."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "id",
    "essay",
    "rubric_score",
    "score_explanation",
    "strongest_evidence",
    "weakest_reasoning",
    "revision",
    "teacher_reasoning",
)


@dataclass(frozen=True)
class FilterSummary:
    """Summary of filtering decisions."""

    total_files: int
    kept: int
    removed_malformed: int
    removed_empty: int
    removed_duplicate_ids: int
    removed_invalid_scores: int
    removed_incomplete: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Filter malformed/incomplete generated examples.")
    parser.add_argument(
        "--input-dir",
        default="datasets/processed/training_examples",
        help="Directory containing one JSON file per generated example.",
    )
    parser.add_argument(
        "--output-jsonl",
        default="datasets/processed/training_dataset.filtered.jsonl",
        help="Filtered JSONL output path.",
    )
    parser.add_argument(
        "--summary-path",
        default="outputs/dataset_validation/filter_summary.json",
        help="Summary statistics output path.",
    )
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--max-score", type=int, default=6)
    return parser.parse_args()


def is_empty_text(value: Any) -> bool:
    return str(value).strip() == ""


def is_incomplete(payload: dict[str, Any]) -> bool:
    for field in REQUIRED_FIELDS:
        if field not in payload:
            return True
        if field != "rubric_score" and is_empty_text(payload.get(field, "")):
            return True
    return False


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_jsonl = Path(args.output_jsonl)
    summary_path = Path(args.summary_path)

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    files = sorted(path for path in input_dir.glob("*.json") if path.is_file())
    seen_ids: set[str] = set()
    kept_records: list[dict[str, Any]] = []

    removed_malformed = 0
    removed_empty = 0
    removed_duplicate_ids = 0
    removed_invalid_scores = 0
    removed_incomplete = 0

    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            removed_malformed += 1
            continue

        if not isinstance(payload, dict):
            removed_malformed += 1
            continue

        if is_empty_text(payload.get("essay", "")):
            removed_empty += 1
            continue

        if is_incomplete(payload):
            removed_incomplete += 1
            continue

        score = payload.get("rubric_score")
        if not isinstance(score, int) or score < args.min_score or score > args.max_score:
            removed_invalid_scores += 1
            continue

        record_id = str(payload.get("id", "")).strip()
        if not record_id:
            removed_incomplete += 1
            continue
        if record_id in seen_ids:
            removed_duplicate_ids += 1
            continue

        seen_ids.add(record_id)
        kept_records.append(payload)

    with output_jsonl.open("w", encoding="utf-8") as handle:
        for record in kept_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    summary = FilterSummary(
        total_files=len(files),
        kept=len(kept_records),
        removed_malformed=removed_malformed,
        removed_empty=removed_empty,
        removed_duplicate_ids=removed_duplicate_ids,
        removed_invalid_scores=removed_invalid_scores,
        removed_incomplete=removed_incomplete,
    )

    summary_payload = {
        "total_files": summary.total_files,
        "kept": summary.kept,
        "removed_malformed": summary.removed_malformed,
        "removed_empty": summary.removed_empty,
        "removed_duplicate_ids": summary.removed_duplicate_ids,
        "removed_invalid_scores": summary.removed_invalid_scores,
        "removed_incomplete": summary.removed_incomplete,
        "output_jsonl": str(output_jsonl),
    }
    summary_path.write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(summary_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
