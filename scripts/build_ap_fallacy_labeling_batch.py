#!/usr/bin/env python3
"""Build merged AP+fallacy labeling batch for teacher inference.

Outputs under `datasets/training_candidates/ap_fallacy_labeling_v1/`:
- labeling_input.jsonl
- data/train.jsonl
- data/validation.jsonl
- data/test.jsonl
- summary.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _split_for_id(example_id: str) -> str:
    digest = hashlib.sha256(example_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def _is_none_label(value: Any) -> bool:
    text = _normalize_text(value).lower()
    return text in {"", "none", "null", "none_label", "no_fallacy", "no fallacy"}


def _pick_fallacy_examples(
    rows: list[dict[str, Any]],
    *,
    target: int,
    seed: int,
) -> list[dict[str, Any]]:
    random.seed(seed)
    by_label: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        label_raw = row.get("primary_fallacy_label")
        label = "no_fallacy" if _is_none_label(label_raw) else _normalize_text(label_raw).lower()
        if not label:
            label = "no_fallacy"
        by_label[label].append(row)

    for bucket in by_label.values():
        random.shuffle(bucket)

    ordered_labels = sorted(by_label.keys(), key=lambda item: len(by_label[item]), reverse=True)
    selected: list[dict[str, Any]] = []
    idx = 0
    while len(selected) < target:
        added = False
        for label in ordered_labels:
            items = by_label[label]
            if idx < len(items):
                selected.append(items[idx])
                added = True
                if len(selected) >= target:
                    break
        if not added:
            break
        idx += 1
    return selected


def _pick_ap_examples(
    rows: list[dict[str, Any]],
    *,
    target: int,
    seed: int,
) -> list[dict[str, Any]]:
    random.seed(seed + 1)

    keep: list[dict[str, Any]] = []
    for row in rows:
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        filename = _normalize_text(meta.get("filename")).lower()
        text = _normalize_text(row.get("essay"))
        if not text:
            continue
        if "score-distributions" in filename or "scoring-statistics" in filename:
            continue
        if len(text.split()) < 60:
            continue
        keep.append(row)

    by_file: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in keep:
        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        filename = _normalize_text(meta.get("filename")) or "unknown_file"
        by_file[filename].append(row)

    for bucket in by_file.values():
        random.shuffle(bucket)

    ordered_files = sorted(by_file.keys(), key=lambda item: len(by_file[item]), reverse=True)
    selected: list[dict[str, Any]] = []
    idx = 0
    while len(selected) < target:
        added = False
        for filename in ordered_files:
            items = by_file[filename]
            if idx < len(items):
                selected.append(items[idx])
                added = True
                if len(selected) >= target:
                    break
        if not added:
            break
        idx += 1
    return selected


def build_batch(
    *,
    fallacy_jsonl: Path,
    ap_jsonl: Path,
    output_root: Path,
    total_target: int,
    ap_target: int,
    seed: int,
) -> dict[str, Any]:
    fallacy_rows = _read_jsonl(fallacy_jsonl)
    ap_rows = _read_jsonl(ap_jsonl)

    ap_target = max(0, min(ap_target, total_target))
    fallacy_target = max(0, total_target - ap_target)

    selected_fallacy = _pick_fallacy_examples(fallacy_rows, target=fallacy_target, seed=seed)
    selected_ap = _pick_ap_examples(ap_rows, target=ap_target, seed=seed)

    merged: list[dict[str, Any]] = []
    seen_essay: set[str] = set()

    for idx, row in enumerate(selected_fallacy, start=1):
        essay = _normalize_text(row.get("argument_text"))
        if not essay:
            continue
        key = essay.lower()
        if key in seen_essay:
            continue
        seen_essay.add(key)

        primary = _normalize_text(row.get("primary_fallacy_label"))
        if _is_none_label(primary):
            primary = "none"
        alt = row.get("acceptable_alternative_labels")
        alternatives = [
            _normalize_text(item)
            for item in (alt if isinstance(alt, list) else [])
            if _normalize_text(item)
        ]

        example_id = f"fallacy-batch-{idx:06d}"
        merged.append(
            {
                "example_id": example_id,
                "prompt": (
                    "AP English Language and Composition argument analysis task: "
                    "identify the strongest logical fallacy (or state none) and "
                    "justify with textual evidence."
                ),
                "essay": essay,
                "score": None,
                "source": "public_fallacy_corpus_v1",
                "license": "mixed_public_research",
                "split": _split_for_id(example_id),
                "metadata": {
                    "source_dataset": row.get("source_dataset"),
                    "source_file": row.get("source_file"),
                    "source_example_id": row.get("example_id"),
                    "expected_fallacies": [] if primary == "none" else [primary],
                    "acceptable_alternative_labels": alternatives,
                    "domain": "fallacy_corpus",
                },
            }
        )

    for offset, row in enumerate(selected_ap, start=1):
        essay = _normalize_text(row.get("essay"))
        if not essay:
            continue
        key = essay.lower()
        if key in seen_essay:
            continue
        seen_essay.add(key)

        meta = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        filename = _normalize_text(meta.get("filename"))
        page = meta.get("page_number")

        example_id = f"ap-batch-{offset:06d}"
        merged.append(
            {
                "example_id": example_id,
                "prompt": (
                    "AP English Language and Composition source excerpt "
                    f"from {filename} page {page}. Analyze the argumentation and reasoning quality."
                ),
                "essay": essay,
                "score": None,
                "source": "collegeboard_ap_lang_2023_2026",
                "license": "collegeboard_materials_personal_project",
                "split": _split_for_id(example_id),
                "metadata": {
                    "source_dataset": "ap_lang_private_docs",
                    "filename": filename,
                    "page_number": page,
                    "total_pages": meta.get("total_pages"),
                    "domain": "ap_lang_docs",
                },
            }
        )

    data_dir = output_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    merged_path = output_root / "labeling_input.jsonl"

    by_split: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    for row in merged:
        split = _normalize_text(row.get("split")).lower()
        if split not in by_split:
            split = _split_for_id(_normalize_text(row.get("example_id")))
            row["split"] = split
        by_split[split].append(row)

    for split in ("train", "validation", "test"):
        split_path = data_dir / f"{split}.jsonl"
        with split_path.open("w", encoding="utf-8") as handle:
            for row in by_split[split]:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    with merged_path.open("w", encoding="utf-8") as handle:
        for split in ("train", "validation", "test"):
            for row in by_split[split]:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    source_counts = Counter(_normalize_text(row.get("source")) for row in merged)
    split_counts = {k: len(v) for k, v in by_split.items()}
    fallacy_label_counts = Counter()
    for row in merged:
        if _normalize_text(row.get("source")) == "public_fallacy_corpus_v1":
            labels = row.get("metadata", {}).get("expected_fallacies")
            if isinstance(labels, list) and labels:
                fallacy_label_counts[_normalize_text(labels[0]) or "none"] += 1
            else:
                fallacy_label_counts["none"] += 1

    summary = {
        "fallacy_input_rows": len(fallacy_rows),
        "ap_input_rows": len(ap_rows),
        "selected_fallacy_rows": len(selected_fallacy),
        "selected_ap_rows": len(selected_ap),
        "final_rows": len(merged),
        "target_total_rows": total_target,
        "target_ap_rows": ap_target,
        "source_counts": dict(source_counts),
        "split_counts": split_counts,
        "fallacy_primary_label_counts": dict(fallacy_label_counts.most_common()),
        "artifacts": {
            "merged": str(merged_path),
            "train": str(data_dir / "train.jsonl"),
            "validation": str(data_dir / "validation.jsonl"),
            "test": str(data_dir / "test.jsonl"),
        },
    }

    (output_root / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build AP+fallacy merged labeling batch.")
    parser.add_argument(
        "--fallacy-jsonl",
        default="datasets/raw/fallacy/normalized/fallacy_corpus_v1.jsonl",
    )
    parser.add_argument(
        "--ap-jsonl",
        default="datasets/raw/ap_lang/normalized/ap_lang_private_docs.jsonl",
    )
    parser.add_argument(
        "--output-root",
        default="datasets/training_candidates/ap_fallacy_labeling_v1",
    )
    parser.add_argument("--total-target", type=int, default=1200)
    parser.add_argument("--ap-target", type=int, default=250)
    parser.add_argument("--seed", type=int, default=20260711)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_batch(
        fallacy_jsonl=Path(args.fallacy_jsonl),
        ap_jsonl=Path(args.ap_jsonl),
        output_root=Path(args.output_root),
        total_target=int(args.total_target),
        ap_target=int(args.ap_target),
        seed=int(args.seed),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
