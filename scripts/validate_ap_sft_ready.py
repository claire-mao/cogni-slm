#!/usr/bin/env python3
"""Fail-closed readiness checks for compiled AP tutor SFT JSONL splits."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

REQUIRED_HEADINGS = (
    "## Argument Summary",
    "## Assumptions",
    "## Primary Fallacy",
    "## Why This Applies",
    "## Cross-Domain Analogy",
    "## Transfer Check",
    "## Reflective Question",
)


def read_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Non-object row at {path}:{line_number}")
            rows.append(value)
    return rows


def message_content(row: dict[str, Any], role: str) -> str:
    messages = row.get("messages")
    if not isinstance(messages, list):
        return ""
    for message in messages:
        if isinstance(message, dict) and message.get("role") == role:
            return str(message.get("content", "")).strip()
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="datasets/sft_ap_tutor/production_v1")
    parser.add_argument("--min-total", type=int, default=10_000)
    parser.add_argument("--min-train", type=int, default=9_000)
    args = parser.parse_args()

    root = Path(args.dataset_root)
    rows_by_split = {
        split: read_rows(root / f"{split}.jsonl") for split in ("train", "validation", "test")
    }
    errors: Counter[str] = Counter()
    ids_by_split: dict[str, set[str]] = {}
    input_hashes_by_split: dict[str, set[str]] = {}

    for split, rows in rows_by_split.items():
        ids: set[str] = set()
        hashes: set[str] = set()
        for row in rows:
            example_id = str(row.get("id", "")).strip()
            user = message_content(row, "user")
            assistant = message_content(row, "assistant")
            if not example_id:
                errors[f"{split}:missing_id"] += 1
            if example_id in ids:
                errors[f"{split}:duplicate_id"] += 1
            ids.add(example_id)
            if not user:
                errors[f"{split}:empty_user"] += 1
            if not assistant:
                errors[f"{split}:empty_assistant"] += 1
            positions = [assistant.find(heading) for heading in REQUIRED_HEADINGS]
            if any(position < 0 for position in positions) or positions != sorted(positions):
                errors[f"{split}:section_contract"] += 1
            if user:
                digest = hashlib.sha256(user.casefold().encode()).hexdigest()
                if digest in hashes:
                    errors[f"{split}:duplicate_input"] += 1
                hashes.add(digest)
        ids_by_split[split] = ids
        input_hashes_by_split[split] = hashes

    for left, right in (("train", "validation"), ("train", "test"), ("validation", "test")):
        errors[f"id_leakage:{left}:{right}"] += len(ids_by_split[left] & ids_by_split[right])
        errors[f"input_leakage:{left}:{right}"] += len(
            input_hashes_by_split[left] & input_hashes_by_split[right]
        )

    errors = Counter({key: value for key, value in errors.items() if value})
    counts = {split: len(rows) for split, rows in rows_by_split.items()}
    total = sum(counts.values())
    ready = total >= args.min_total and counts["train"] >= args.min_train and not errors
    report = {"counts": counts, "total": total, "errors": dict(errors), "ready": ready}
    print(json.dumps(report, indent=2, sort_keys=True))
    if not ready:
        raise SystemExit("Dataset failed AP tutor SFT readiness checks")


if __name__ == "__main__":
    main()
