"""Merge and stratify datasets from datasets/hf into datasets/final.

Pipeline:
1. Load datasets from a Hugging Face DatasetDict at datasets/hf/dataset_dict.
2. Normalize records while preserving source and metadata.
3. Deduplicate by ID and normalized text fingerprint.
4. Stratify split assignment by task and score buckets.
5. Write merged JSONL files under datasets/final.
6. Generate statistics report at docs/reports/final_dataset.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from typing import Any

from datasets import Dataset, DatasetDict, load_from_disk

BASE_FIELDS = {"id", "text", "score", "source", "prompt", "split", "task", "metadata"}


@dataclass(frozen=True)
class NormalizedRecord:
    """One merged record in final schema."""

    id: str
    text: str
    score: float
    source: str
    prompt: str
    task: str
    split: str
    metadata: dict[str, Any]


@dataclass
class MergeStats:
    """Aggregate merger statistics."""

    input_rows: int = 0
    rows_missing_text: int = 0
    rows_missing_score: int = 0
    rows_bad_score: int = 0
    kept_before_dedup: int = 0
    dedup_id_removed: int = 0
    dedup_text_removed: int = 0
    final_rows: int = 0


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Merge datasets/hf into datasets/final.")
    parser.add_argument("--input-root", default="datasets/hf", help="Input datasets root.")
    parser.add_argument(
        "--output-dir",
        default="datasets/final",
        help="Final dataset output directory.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/final_dataset.md",
        help="Markdown report output path.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for stratification.")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio.")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Validation split ratio.")
    parser.add_argument("--test-ratio", type=float, default=0.1, help="Test split ratio.")
    return parser.parse_args()


def load_dataset_dict(input_root: Path) -> DatasetDict:
    """Load DatasetDict from input root.

    Expected location: <input_root>/dataset_dict
    """
    dataset_dir = input_root / "dataset_dict"
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Expected dataset directory not found: {dataset_dir}")

    loaded = load_from_disk(str(dataset_dir))
    if isinstance(loaded, DatasetDict):
        return loaded
    if isinstance(loaded, Dataset):
        return DatasetDict({"train": loaded})
    raise TypeError(f"Unsupported loaded dataset type: {type(loaded)!r}")


def parse_score(value: Any) -> float:
    """Parse score as float."""
    if value is None:
        raise ValueError("missing score")
    if isinstance(value, int | float):
        return float(value)
    raw = str(value).strip()
    if not raw:
        raise ValueError("empty score")
    return float(raw)


def normalize_text(text: str) -> str:
    """Whitespace-normalized text."""
    return " ".join(text.split())


def infer_task(row: dict[str, Any]) -> str:
    """Infer task label when not explicitly provided."""
    task = row.get("task")
    if isinstance(task, str) and task.strip():
        return task.strip()

    prompt = row.get("prompt")
    if isinstance(prompt, str) and prompt.strip():
        return "essay_scoring"

    return "unknown"


def extract_metadata(row: dict[str, Any], source_split: str, source_index: int) -> dict[str, Any]:
    """Preserve metadata and any additional fields not in base schema."""
    metadata: dict[str, Any] = {}

    raw_metadata = row.get("metadata")
    if isinstance(raw_metadata, dict):
        metadata.update(raw_metadata)

    extra_fields = {key: value for key, value in row.items() if key not in BASE_FIELDS}
    if extra_fields:
        metadata["extra_fields"] = extra_fields

    metadata.setdefault("source_split", source_split)
    metadata.setdefault("source_row_index", source_index)
    return metadata


def normalize_dataset(dataset_dict: DatasetDict, stats: MergeStats) -> list[NormalizedRecord]:
    """Normalize records from DatasetDict into a uniform in-memory list."""
    normalized: list[NormalizedRecord] = []

    for split_name, dataset in dataset_dict.items():
        for row_index, row in enumerate(dataset, start=1):
            stats.input_rows += 1
            text_raw = row.get("text", row.get("essay"))
            text = normalize_text(str(text_raw or ""))
            if not text:
                stats.rows_missing_text += 1
                continue

            try:
                score = parse_score(row.get("score", row.get("label")))
            except ValueError:
                score_value = row.get("score", row.get("label"))
                if score_value in (None, ""):
                    stats.rows_missing_score += 1
                else:
                    stats.rows_bad_score += 1
                continue

            source = str(row.get("source") or "unknown").strip() or "unknown"
            prompt = str(row.get("prompt") or "").strip()
            task = infer_task(row)
            record_id = str(row.get("id") or f"{source}:{split_name}:{row_index}").strip()
            metadata = extract_metadata(dict(row), source_split=split_name, source_index=row_index)

            normalized.append(
                NormalizedRecord(
                    id=record_id,
                    text=text,
                    score=score,
                    source=source,
                    prompt=prompt,
                    task=task,
                    split="",
                    metadata=metadata,
                )
            )

    stats.kept_before_dedup = len(normalized)
    return normalized


def deduplicate(records: list[NormalizedRecord], stats: MergeStats) -> list[NormalizedRecord]:
    """Deduplicate first by ID then by normalized text fingerprint."""
    seen_ids: set[str] = set()
    seen_text_hashes: set[str] = set()

    deduped: list[NormalizedRecord] = []
    for record in records:
        if record.id in seen_ids:
            stats.dedup_id_removed += 1
            continue
        seen_ids.add(record.id)

        text_key = normalize_text(record.text).lower()
        text_hash = hashlib.sha256(text_key.encode("utf-8")).hexdigest()
        if text_hash in seen_text_hashes:
            stats.dedup_text_removed += 1
            continue
        seen_text_hashes.add(text_hash)

        deduped.append(record)

    stats.final_rows = len(deduped)
    return deduped


def build_score_bucket_fn(records: list[NormalizedRecord]) -> callable:
    """Return a function mapping scores to stable bins for stratification."""
    scores = sorted(record.score for record in records)
    if not scores:
        return lambda score: "score_unknown"

    unique = sorted(set(scores))
    if len(unique) <= 20:
        rounded = {value: f"s_{value:.3f}" for value in unique}
        return lambda score: rounded.get(score, f"s_{score:.3f}")

    min_score = scores[0]
    max_score = scores[-1]
    if math.isclose(min_score, max_score):
        return lambda _score: f"s_{min_score:.3f}"

    bucket_count = 10
    width = (max_score - min_score) / bucket_count

    def bucket(score: float) -> str:
        index = int((score - min_score) / width)
        if index >= bucket_count:
            index = bucket_count - 1
        if index < 0:
            index = 0
        return f"b{index:02d}"

    return bucket


def stratified_split(
    records: list[NormalizedRecord],
    seed: int,
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
) -> list[NormalizedRecord]:
    """Assign train/validation/test split stratified by task and score bucket."""
    ratio_sum = train_ratio + val_ratio + test_ratio
    if not math.isclose(ratio_sum, 1.0, rel_tol=1e-6, abs_tol=1e-6):
        raise ValueError("Split ratios must sum to 1.0")

    rng = random.Random(seed)
    score_bucket = build_score_bucket_fn(records)

    grouped: dict[tuple[str, str], list[NormalizedRecord]] = defaultdict(list)
    for record in records:
        grouped[(record.task, score_bucket(record.score))].append(record)

    assigned: list[NormalizedRecord] = []
    for key in sorted(grouped):
        group = grouped[key]
        rng.shuffle(group)
        n = len(group)

        train_n = int(n * train_ratio)
        val_n = int(n * val_ratio)
        test_n = n - train_n - val_n

        # Keep all splits non-negative and adjust rounding drift deterministically.
        while train_n + val_n + test_n > n:
            if train_n >= val_n and train_n >= test_n and train_n > 0:
                train_n -= 1
            elif val_n >= test_n and val_n > 0:
                val_n -= 1
            elif test_n > 0:
                test_n -= 1

        idx = 0
        for _ in range(train_n):
            record = group[idx]
            assigned.append(
                NormalizedRecord(
                    id=record.id,
                    text=record.text,
                    score=record.score,
                    source=record.source,
                    prompt=record.prompt,
                    task=record.task,
                    split="train",
                    metadata=record.metadata,
                )
            )
            idx += 1
        for _ in range(val_n):
            record = group[idx]
            assigned.append(
                NormalizedRecord(
                    id=record.id,
                    text=record.text,
                    score=record.score,
                    source=record.source,
                    prompt=record.prompt,
                    task=record.task,
                    split="validation",
                    metadata=record.metadata,
                )
            )
            idx += 1
        for _ in range(test_n):
            record = group[idx]
            assigned.append(
                NormalizedRecord(
                    id=record.id,
                    text=record.text,
                    score=record.score,
                    source=record.source,
                    prompt=record.prompt,
                    task=record.task,
                    split="test",
                    metadata=record.metadata,
                )
            )
            idx += 1

    return assigned


def write_jsonl(records: list[NormalizedRecord], path: Path) -> None:
    """Write records as JSONL."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            payload = {
                "id": record.id,
                "source": record.source,
                "task": record.task,
                "prompt": record.prompt,
                "text": record.text,
                "label": record.score,
                "metadata": record.metadata,
                "split": record.split,
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def summarize_scores(records: list[NormalizedRecord]) -> dict[str, float]:
    """Return summary statistics for scores."""
    if not records:
        return {"count": 0.0, "min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0}

    values = [record.score for record in records]
    return {
        "count": float(len(values)),
        "min": float(min(values)),
        "max": float(max(values)),
        "mean": float(mean(values)),
        "median": float(median(values)),
    }


def render_report(
    *,
    input_root: Path,
    output_dir: Path,
    stats: MergeStats,
    records: list[NormalizedRecord],
) -> str:
    """Build markdown report text."""
    by_split: dict[str, list[NormalizedRecord]] = defaultdict(list)
    by_source: Counter[str] = Counter()
    by_task: Counter[str] = Counter()
    for record in records:
        by_split[record.split].append(record)
        by_source[record.source] += 1
        by_task[record.task] += 1

    lines = [
        "# Final Dataset Merge Report",
        "",
        f"- Input root: `{input_root}`",
        f"- Output directory: `{output_dir}`",
        f"- Input rows: `{stats.input_rows}`",
        f"- Dropped missing text: `{stats.rows_missing_text}`",
        f"- Dropped missing score: `{stats.rows_missing_score}`",
        f"- Dropped invalid score: `{stats.rows_bad_score}`",
        f"- Rows kept before dedup: `{stats.kept_before_dedup}`",
        f"- Dedup removed (duplicate ID): `{stats.dedup_id_removed}`",
        f"- Dedup removed (duplicate text): `{stats.dedup_text_removed}`",
        f"- Final rows: `{stats.final_rows}`",
        "",
        "## Split Counts",
        "",
        "| split | count |",
        "|---|---:|",
    ]

    for split in ("train", "validation", "test"):
        lines.append(f"| {split} | {len(by_split.get(split, []))} |")

    lines.extend(["", "## Source Distribution", "", "| source | count |", "|---|---:|"])
    for source, count in sorted(by_source.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {source} | {count} |")

    lines.extend(["", "## Task Distribution", "", "| task | count |", "|---|---:|"])
    for task, count in sorted(by_task.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| {task} | {count} |")

    lines.extend(
        [
            "",
            "## Score Statistics",
            "",
            "| split | count | min | max | mean | median |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )

    for split in ("train", "validation", "test"):
        summary = summarize_scores(by_split.get(split, []))
        lines.append(
            "| "
            f"{split} | "
            f"{int(summary['count'])} | "
            f"{summary['min']:.4f} | "
            f"{summary['max']:.4f} | "
            f"{summary['mean']:.4f} | "
            f"{summary['median']:.4f} |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Source field is preserved per record.")
    lines.append("- Metadata is preserved and includes source split and row index provenance.")
    lines.append("- Splits are assigned using stratification by task and score buckets.")

    return "\n".join(lines)


def main() -> None:
    """Run the dataset merger."""
    args = parse_args()
    input_root = Path(args.input_root)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    stats = MergeStats()
    dataset_dict = load_dataset_dict(input_root)
    normalized = normalize_dataset(dataset_dict, stats)
    deduped = deduplicate(normalized, stats)
    assigned = stratified_split(
        deduped,
        seed=args.seed,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
    )

    train_records = [record for record in assigned if record.split == "train"]
    val_records = [record for record in assigned if record.split == "validation"]
    test_records = [record for record in assigned if record.split == "test"]

    write_jsonl(assigned, output_dir / "merged_all.jsonl")
    write_jsonl(train_records, output_dir / "train.jsonl")
    write_jsonl(val_records, output_dir / "validation.jsonl")
    write_jsonl(test_records, output_dir / "test.jsonl")

    report = render_report(
        input_root=input_root,
        output_dir=output_dir,
        stats=stats,
        records=assigned,
    )
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "input_rows": stats.input_rows,
                "final_rows": stats.final_rows,
                "train": len(train_records),
                "validation": len(val_records),
                "test": len(test_records),
                "output_dir": str(output_dir),
                "report_path": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
