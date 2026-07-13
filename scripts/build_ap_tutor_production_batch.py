#!/usr/bin/env python3
"""Build a 15k AP fallacy-tutor teacher-labeling batch from local real sources."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROMPT = (
    "Analyze this argument as an AP English Language logical-fallacy tutor. "
    "Identify one primary fallacy or explicitly state that no clear fallacy is present."
)


def clean(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def label_slug(value: Any) -> str:
    text = clean(value).lower().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "unknown"


def stable_split(group: str) -> str:
    bucket = int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 90:
        return "train"
    if bucket < 95:
        return "validation"
    return "test"


def read_normalized(path: Path, min_words: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            item = json.loads(raw)
            text = clean(item.get("argument_text"))
            if len(text.split()) < min_words:
                continue
            source_dataset = clean(item.get("source_dataset")) or "normalized_fallacy"
            origin = clean(item.get("example_id"))
            rows.append(
                {
                    "text": text,
                    "label": label_slug(item.get("primary_fallacy_label")),
                    "source": source_dataset,
                    "group": f"{source_dataset}:{origin}",
                    "license": "source_dataset_terms; research_use",
                    "origin": origin,
                }
            )
    return rows


def read_mafalda(path: Path, min_words: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for index, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            argument = clean(item.get("text"))
            if len(argument.split()) < min_words:
                continue
            rows.append(
                {
                    "text": argument,
                    "label": "unknown",
                    "source": "mafalda_unannotated",
                    "group": f"mafalda:{index}",
                    "license": "MAFALDA research dataset terms",
                    "origin": f"non_annotated_dataset.jsonl:{index}",
                }
            )
    return rows


def read_large_csv(path: Path, min_words: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for index, item in enumerate(csv.DictReader(handle), start=1):
            context = f"{clean(item.get('source_url'))} {clean(item.get('test_name'))}".lower()
            # The source file also contains unrelated quizzes. Only fallacy-specific
            # quiz groups are eligible; the teacher will determine the actual label.
            if "fallac" not in context:
                continue
            text = clean(item.get("sentence"))
            if len(text.split()) < min_words:
                continue
            source_url = clean(item.get("source_url"))
            test_name = clean(item.get("test_name"))
            # A URL/test represents a shared source group and must stay in one split.
            group = source_url or test_name or f"large-csv-row-{index}"
            rows.append(
                {
                    "text": text,
                    "label": label_slug(item.get("Logical Fallacy Types")),
                    "source": "logical_fallacy_detection_intermediate",
                    "group": group,
                    "license": "source_dataset_terms; research_use",
                    "origin": f"{path.name}:{index}",
                }
            )
    return rows


def select_rows(rows: list[dict[str, Any]], target: int, seed: int) -> list[dict[str, Any]]:
    unique: dict[str, dict[str, Any]] = {}
    for row in rows:
        key = clean(row["text"]).casefold()
        if key and key not in unique:
            unique[key] = row

    rng = random.Random(seed)
    by_source: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in unique.values():
        by_source[row["source"]].append(row)
    for bucket in by_source.values():
        rng.shuffle(bucket)

    # Prefer the two curated research corpora. The fallacy-only quiz corpus fills
    # the remaining capacity without allowing unrelated quiz topics into the run.
    source_order = [
        "mafalda_unannotated",
        "logical_fallacy_edu",
        "logical_fallacy_climate",
        "argotario",
        "mafalda_gold",
        "logical_fallacy_detection_intermediate",
    ]
    chosen: list[dict[str, Any]] = []
    for source in source_order:
        room = target - len(chosen)
        if room <= 0:
            break
        chosen.extend(by_source.get(source, [])[:room])
    return chosen


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=15_000)
    parser.add_argument("--min-words", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--mafalda",
        default=("datasets/raw/fallacy/source_files/MAFALDA/datasets/non_annotated_dataset.jsonl"),
    )
    parser.add_argument(
        "--normalized",
        default="datasets/raw/fallacy/normalized/fallacy_corpus_v1.jsonl",
    )
    parser.add_argument(
        "--large-csv",
        default=(
            "datasets/raw/fallacy/source_files/logical-fallacy/"
            "codes_to_get_data/intermediate_data_files/20210901_final_data.csv"
        ),
    )
    parser.add_argument(
        "--output-root", default="datasets/training_candidates/ap_fallacy_production_v1"
    )
    args = parser.parse_args()

    candidates = read_normalized(Path(args.normalized), args.min_words)
    candidates.extend(read_mafalda(Path(args.mafalda), args.min_words))
    candidates.extend(read_large_csv(Path(args.large_csv), args.min_words))
    selected = select_rows(candidates, args.target, args.seed)
    if len(selected) < args.target:
        raise RuntimeError(f"Only {len(selected)} unique candidates available; need {args.target}")

    output_root = Path(args.output_root)
    output: list[dict[str, Any]] = []
    split_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    for index, row in enumerate(selected, start=1):
        split = stable_split(row["group"])
        record = {
            "example_id": f"ap-prod-{index:06d}",
            "prompt": PROMPT,
            "essay": row["text"],
            "score": None,
            "source": row["source"],
            "license": row["license"],
            "split": split,
            "metadata": {
                "expected_fallacies": [] if row["label"] == "unknown" else [row["label"]],
                "source_group": row["group"],
                "source_origin": row["origin"],
            },
        }
        output.append(record)
        split_counts[split] += 1
        label_counts[row["label"]] += 1
        source_counts[row["source"]] += 1

    write_jsonl(output_root / "labeling_input.jsonl", output)
    for split in ("train", "validation", "test"):
        write_jsonl(output_root / f"{split}.jsonl", [r for r in output if r["split"] == split])

    summary = {
        "target": args.target,
        "selected": len(output),
        "min_words": args.min_words,
        "seed": args.seed,
        "split_counts": dict(sorted(split_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "label_counts": dict(label_counts.most_common()),
        "input_path": str(output_root / "labeling_input.jsonl"),
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
