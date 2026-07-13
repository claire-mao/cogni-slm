#!/usr/bin/env python3
"""Build a 30-example held-out benchmark from consolidated public fallacy corpus."""

from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

TASK_MODES = ["teach", "diagnose", "quiz_feedback"]
EXPECTED_SECTIONS = [
    "fallacy_hypothesis",
    "reasoning_diagnosis",
    "analogy",
    "repair",
    "confidence_note",
]
REQUIRED_BEHAVIORS = ["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
PROHIBITED_BEHAVIORS = ["P1", "P2", "P3", "P4", "P5"]
RUBRIC_HOOKS = [
    "rubric.diagnosis",
    "rubric.analogy_mapping",
    "rubric.repair_quality",
    "rubric.confidence_calibration",
]


def read_jsonl(path: Path):
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def infer_difficulty(text: str) -> str:
    words = len(text.split())
    if words < 18:
        return "beginner"
    if words < 45:
        return "intermediate"
    return "advanced"


def build_heldout(corpus: list[dict], n: int, seed: int) -> list[dict]:
    random.seed(seed)

    by_label: dict[str, list[dict]] = defaultdict(list)
    for row in corpus:
        label = row.get("primary_fallacy_label") or "none"
        by_label[label].append(row)

    for rows in by_label.values():
        random.shuffle(rows)

    labels_sorted = sorted(by_label.keys(), key=lambda k: len(by_label[k]), reverse=True)
    selected: list[dict] = []

    # Round-robin label sampling for diversity.
    exhausted = False
    idx = 0
    while len(selected) < n and not exhausted:
        exhausted = True
        for label in labels_sorted:
            rows = by_label[label]
            if idx < len(rows):
                selected.append(rows[idx])
                exhausted = False
                if len(selected) >= n:
                    break
        idx += 1

    out = []
    for i, row in enumerate(selected[:n], start=1):
        label = row.get("primary_fallacy_label")
        if label == "none":
            label = None

        text = (row.get("argument_text") or "").strip()
        task_mode = TASK_MODES[(i - 1) % len(TASK_MODES)]
        rec = {
            "example_id": f"heldout-public-v1-{i:04d}",
            "dataset_version": "1.0.0-public-heldout-v1",
            "taxonomy_version": "v1",
            "source_id": (
                f"public::{row.get('source_dataset', 'unknown')}::{row.get('example_id', 'na')}"
            ),
            "argument_text": text,
            "task_mode": task_mode,
            "difficulty_level": infer_difficulty(text),
            "context": {
                "placeholder": False,
                "source_dataset": row.get("source_dataset"),
                "source_file": row.get("source_file"),
                "source_example_id": row.get("example_id"),
            },
            "primary_fallacy_label": label,
            "acceptable_alternative_labels": row.get("acceptable_alternative_labels", []),
            "expected_sections": EXPECTED_SECTIONS,
            "required_behaviors": REQUIRED_BEHAVIORS,
            "prohibited_behaviors": PROHIBITED_BEHAVIORS,
            "rubric_hooks": RUBRIC_HOOKS,
            "is_adversarial": False,
            "adversarial_type": None,
            "attack_target": None,
            "metadata": {
                "placeholder": False,
                "source": "public_fallacy_corpus_v1",
                "build_seed": seed,
            },
        }
        out.append(rec)

    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build public held-out set JSONL.")
    parser.add_argument(
        "--input-jsonl",
        default="datasets/raw/fallacy/normalized/fallacy_corpus_v1.jsonl",
        help="Input corpus JSONL path.",
    )
    parser.add_argument(
        "--output-jsonl",
        default="datasets/eval/heldout_benchmark_public_v1.jsonl",
        help="Output held-out JSONL path.",
    )
    parser.add_argument(
        "--output-report",
        default="outputs/data_ingestion/heldout_public_v1_report.json",
        help="Output report JSON path.",
    )
    parser.add_argument("--n", type=int, default=30)
    parser.add_argument("--seed", type=int, default=20260711)
    args = parser.parse_args()

    input_path = Path(args.input_jsonl)
    output_path = Path(args.output_jsonl)
    report_path = Path(args.output_report)

    corpus = read_jsonl(input_path)
    heldout = build_heldout(corpus, args.n, args.seed)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        for row in heldout:
            fh.write(json.dumps(row, ensure_ascii=True) + "\n")

    label_counts: dict[str, int] = defaultdict(int)
    task_counts: dict[str, int] = defaultdict(int)
    for row in heldout:
        label_counts[str(row.get("primary_fallacy_label"))] += 1
        task_counts[row["task_mode"]] += 1

    report = {
        "input_jsonl": str(input_path),
        "output_jsonl": str(output_path),
        "n": len(heldout),
        "seed": args.seed,
        "label_counts": dict(sorted(label_counts.items(), key=lambda kv: kv[0])),
        "task_mode_counts": dict(task_counts),
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(output_path)
    print(report_path)


if __name__ == "__main__":
    main()
