#!/usr/bin/env python3
"""Prepare AP tutor labeling dataset with filtering, deduplication, and split exports."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Row:
    payload: dict[str, Any]
    word_count: int
    quality_score: float


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"Expected JSON object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _word_count(text: str) -> int:
    return len([token for token in text.split(" ") if token])


def _quality_score(word_count: int) -> float:
    # Simple deterministic quality proxy based on argument length.
    if word_count <= 0:
        return 0.0
    if word_count >= 180:
        return 1.0
    return round(word_count / 180.0, 4)


def _deterministic_split(example_id: str) -> str:
    digest = hashlib.sha256(example_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def _prepare_rows(
    rows: list[dict[str, Any]],
    *,
    min_words: int,
) -> tuple[list[Row], Counter[str], Counter[str]]:
    accepted: list[Row] = []
    rejected = Counter()
    source_counts = Counter()

    seen_text: set[str] = set()

    for payload in rows:
        essay = _normalize_text(payload.get("essay"))
        if not essay:
            rejected["missing_essay"] += 1
            continue

        wc = _word_count(essay)
        if wc < min_words:
            rejected["below_min_words"] += 1
            continue

        dedup_key = essay.lower()
        if dedup_key in seen_text:
            rejected["duplicate_essay"] += 1
            continue
        seen_text.add(dedup_key)

        example_id = (
            _normalize_text(payload.get("example_id")) or f"example-{len(accepted) + 1:06d}"
        )
        split = _normalize_text(payload.get("split")).lower()
        if split not in {"train", "validation", "test"}:
            split = _deterministic_split(example_id)

        source = _normalize_text(payload.get("source")) or "unknown"
        source_counts[source] += 1

        record = {
            "example_id": example_id,
            "instruction": (
                "Follow the 7-step AP fallacy tutoring behavior: summarize, assumptions, "
                "one primary fallacy or none, explanation, one cross-domain analogy, one "
                "transfer check without answer, one reflective question."
            ),
            "prompt": _normalize_text(payload.get("prompt")),
            "essay": essay,
            "split": split,
            "source": source,
            "license": _normalize_text(payload.get("license")) or "unknown",
            "metadata": payload.get("metadata")
            if isinstance(payload.get("metadata"), dict)
            else {},
            "word_count": wc,
            "quality_score": _quality_score(wc),
        }
        accepted.append(Row(payload=record, word_count=wc, quality_score=record["quality_score"]))

    return accepted, rejected, source_counts


def _build_report(summary: dict[str, Any]) -> str:
    lines = [
        "# AP Tutor Dataset Preparation Report",
        "",
        f"- Input rows: `{summary['input_rows']}`",
        f"- Accepted rows: `{summary['accepted_rows']}`",
        f"- Rejected rows: `{summary['rejected_rows']}`",
        f"- Min words: `{summary['min_words']}`",
        "",
        "## Split Counts",
        "",
        "| Split | Rows |",
        "|---|---:|",
    ]
    for split, count in summary["split_counts"].items():
        lines.append(f"| {split} | {count} |")

    lines.extend(["", "## Source Counts", "", "| Source | Rows |", "|---|---:|"])
    for source, count in summary["source_counts"].items():
        lines.append(f"| {source} | {count} |")

    lines.extend(["", "## Rejections", "", "| Reason | Count |", "|---|---:|"])
    for reason, count in summary["rejections"].items():
        lines.append(f"| {reason} | {count} |")

    return "\n".join(lines) + "\n"


def _build_dataset_card(summary: dict[str, Any]) -> str:
    lines = [
        "# AP Tutor Candidate Dataset Card",
        "",
        "## Purpose",
        "Label-ready dataset for supervised fine-tuning of Cogni AP fallacy tutor behavior.",
        "",
        "## Construction",
        "- Source blend: AP Lang private docs + public fallacy corpus",
        "- Deterministic filtering and deduplication",
        "- Fixed train/validation/test split",
        "",
        "## Stats",
        f"- Total accepted rows: {summary['accepted_rows']}",
        f"- Train: {summary['split_counts'].get('train', 0)}",
        f"- Validation: {summary['split_counts'].get('validation', 0)}",
        f"- Test: {summary['split_counts'].get('test', 0)}",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare AP tutor dataset candidates.")
    parser.add_argument(
        "--input-jsonl",
        default="datasets/training_candidates/ap_fallacy_labeling_v1/labeling_input.jsonl",
    )
    parser.add_argument("--output-root", default="datasets/sft_ap_tutor/v1")
    parser.add_argument("--min-words", type=int, default=40)
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    output_root = Path(args.output_root)

    rows = _read_jsonl(input_path)
    accepted, rejected, source_counts = _prepare_rows(rows, min_words=int(args.min_words))

    by_split: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for row in accepted:
        split = str(row.payload["split"])
        by_split[split].append(row.payload)

    merged: list[dict[str, Any]] = []
    for split in ("train", "validation", "test"):
        split_rows = by_split.get(split, [])
        _write_jsonl(output_root / f"{split}.jsonl", split_rows)
        merged.extend(split_rows)
    _write_jsonl(output_root / "merged.jsonl", merged)

    summary = {
        "input_rows": len(rows),
        "accepted_rows": len(accepted),
        "rejected_rows": int(sum(rejected.values())),
        "min_words": int(args.min_words),
        "split_counts": {
            split: len(by_split.get(split, [])) for split in ("train", "validation", "test")
        },
        "source_counts": dict(sorted(source_counts.items())),
        "rejections": dict(sorted(rejected.items())),
        "artifacts": {
            "train": str(output_root / "train.jsonl"),
            "validation": str(output_root / "validation.jsonl"),
            "test": str(output_root / "test.jsonl"),
            "merged": str(output_root / "merged.jsonl"),
            "report": str(output_root / "report.md"),
            "dataset_card": str(output_root / "dataset_card.md"),
        },
    }

    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_root / "report.md").write_text(_build_report(summary), encoding="utf-8")
    (output_root / "dataset_card.md").write_text(_build_dataset_card(summary), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
