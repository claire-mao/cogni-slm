"""Build final training dataset from unified data.

Output dataset fields (and only these fields):
- prompt
- essay
- score

The output is saved as a Hugging Face DatasetDict at datasets/training/ and can be
loaded directly with datasets.load_from_disk().

Provenance is written separately as JSONL files.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from datasets import Dataset, DatasetDict, Features, Value, load_from_disk


@dataclass(frozen=True)
class Example:
    """Training-ready example with required fields only."""

    prompt: str
    essay: str
    score: float


@dataclass
class BuildStats:
    """Pipeline stats for reporting."""

    input_lines: int = 0
    parse_errors: int = 0
    non_object_rows: int = 0
    filtered_missing_split: int = 0
    filtered_invalid_split: int = 0
    filtered_missing_prompt: int = 0
    filtered_missing_essay: int = 0
    filtered_missing_score: int = 0
    filtered_non_numeric_score: int = 0
    kept_before_dedup: int = 0
    dedup_removed: int = 0


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Build final train/validation/test dataset.")
    parser.add_argument(
        "--input-jsonl",
        default="datasets/processed/unified/unified_all.jsonl",
        help="Unified input dataset JSONL.",
    )
    parser.add_argument(
        "--output-dataset-dir",
        default="datasets/training",
        help="Output Hugging Face DatasetDict directory.",
    )
    parser.add_argument(
        "--provenance-dir",
        default="datasets/training_provenance",
        help="Separate provenance JSONL directory.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/training_dataset.md",
        help="Output markdown report path.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    """Normalize whitespace."""
    return " ".join(text.split())


def parse_score(value: Any) -> float | None:
    """Parse numeric score."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
        return None

    raw = str(value).strip()
    if not raw:
        return None
    try:
        numeric = float(raw)
    except ValueError:
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def normalize_split(value: Any) -> str:
    """Normalize split labels."""
    split = str(value or "").strip().lower()
    if split in {"train", "training"}:
        return "train"
    if split in {"validation", "val", "valid", "dev"}:
        return "validation"
    if split in {"test", "testing"}:
        return "test"
    return split


def choose_prompt(row: dict[str, Any]) -> str:
    """Get prompt text/id from common fields."""
    for key in ("prompt", "context", "essay_set", "prompt_id"):
        if key not in row:
            continue
        prompt = normalize_text(str(row.get(key, "")))
        if prompt:
            return prompt
    return ""


def choose_essay(row: dict[str, Any]) -> str:
    """Get essay text from common fields."""
    for key in ("essay", "input", "text", "argument_text", "student_response", "content"):
        if key not in row:
            continue
        essay = normalize_text(str(row.get(key, "")))
        if essay:
            return essay
    return ""


def load_and_filter(
    input_jsonl: Path,
) -> tuple[dict[str, list[Example]], dict[str, list[dict[str, Any]]], BuildStats]:
    """Load unified input, filter valid rows, and build split-wise examples + provenance."""
    stats = BuildStats()

    grouped_examples: dict[str, list[Example]] = {"train": [], "validation": [], "test": []}
    grouped_provenance: dict[str, list[dict[str, Any]]] = {
        "train": [],
        "validation": [],
        "test": [],
    }

    with input_jsonl.open("r", encoding="utf-8", errors="replace") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            stats.input_lines += 1

            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                stats.parse_errors += 1
                continue

            if not isinstance(row, dict):
                stats.non_object_rows += 1
                continue

            if "split" not in row:
                stats.filtered_missing_split += 1
                continue

            split = normalize_split(row.get("split"))
            if split not in {"train", "validation", "test"}:
                stats.filtered_invalid_split += 1
                continue

            prompt = choose_prompt(row)
            if not prompt:
                stats.filtered_missing_prompt += 1
                continue

            essay = choose_essay(row)
            if not essay:
                stats.filtered_missing_essay += 1
                continue

            if "score" not in row and "label" not in row:
                stats.filtered_missing_score += 1
                continue

            score = parse_score(row.get("score", row.get("label")))
            if score is None:
                stats.filtered_non_numeric_score += 1
                continue

            stats.kept_before_dedup += 1
            grouped_examples[split].append(Example(prompt=prompt, essay=essay, score=score))

            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            grouped_provenance[split].append(
                {
                    "source_id": str(row.get("id", "")).strip() or f"line-{line_number}",
                    "split": split,
                    "source": str(row.get("source", "")).strip() or "unknown",
                    "license": str(row.get("license", "")).strip() or "unknown",
                    "source_case": metadata.get("source_case"),
                    "source_ref": metadata.get("source_ref"),
                    "row_index": metadata.get("row_index"),
                }
            )

    return grouped_examples, grouped_provenance, stats


def deduplicate_with_provenance(
    grouped_examples: dict[str, list[Example]],
    grouped_provenance: dict[str, list[dict[str, Any]]],
    stats: BuildStats,
) -> tuple[dict[str, list[Example]], dict[str, list[dict[str, Any]]]]:
    """Deduplicate exact duplicate examples and aggregate provenance lists."""
    dedup_examples: dict[str, list[Example]] = {"train": [], "validation": [], "test": []}
    dedup_provenance: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}

    for split in ("train", "validation", "test"):
        index_by_key: dict[tuple[str, str, float], int] = {}
        prov_buckets: list[list[dict[str, Any]]] = []

        for example, prov in zip(
            grouped_examples[split],
            grouped_provenance[split],
            strict=True,
        ):
            key = (example.prompt, example.essay, round(example.score, 8))
            existing = index_by_key.get(key)
            if existing is None:
                index_by_key[key] = len(dedup_examples[split])
                dedup_examples[split].append(example)
                prov_buckets.append([prov])
            else:
                stats.dedup_removed += 1
                prov_buckets[existing].append(prov)

        for idx, prov_list in enumerate(prov_buckets):
            dedup_provenance[split].append(
                {
                    "example_index": idx,
                    "split": split,
                    "prompt": dedup_examples[split][idx].prompt,
                    "essay_sha256": __import__("hashlib")
                    .sha256(dedup_examples[split][idx].essay.encode("utf-8"))
                    .hexdigest(),
                    "source_records": prov_list,
                }
            )

    return dedup_examples, dedup_provenance


def save_training_dataset(
    output_dir: Path, grouped_examples: dict[str, list[Example]]
) -> DatasetDict:
    """Save split datasets with only prompt/essay/score fields."""
    features = Features(
        {
            "prompt": Value("string"),
            "essay": Value("string"),
            "score": Value("float64"),
        }
    )

    dataset_dict = DatasetDict()
    for split in ("train", "validation", "test"):
        rows = [
            {
                "prompt": ex.prompt,
                "essay": ex.essay,
                "score": ex.score,
            }
            for ex in grouped_examples[split]
        ]
        if rows:
            dataset_dict[split] = Dataset.from_list(rows, features=features)

    if not dataset_dict:
        raise ValueError("No training rows available to build DatasetDict.")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        import shutil

        shutil.rmtree(output_dir)
    dataset_dict.save_to_disk(str(output_dir))
    return dataset_dict


def save_provenance(
    provenance_dir: Path, grouped_provenance: dict[str, list[dict[str, Any]]]
) -> None:
    """Save provenance JSONL files separately by split."""
    provenance_dir.mkdir(parents=True, exist_ok=True)
    for split in ("train", "validation", "test"):
        path = provenance_dir / f"{split}.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for row in grouped_provenance[split]:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize_scores(values: list[float]) -> dict[str, float | None]:
    """Return basic score summary stats."""
    if not values:
        return {"min": None, "max": None, "mean": None}
    return {
        "min": min(values),
        "max": max(values),
        "mean": mean(values),
    }


def render_report(
    *,
    input_jsonl: Path,
    output_dataset_dir: Path,
    provenance_dir: Path,
    stats: BuildStats,
    grouped_examples: dict[str, list[Example]],
    load_ok: bool,
    load_message: str,
) -> str:
    """Render training dataset report."""
    counts = {split: len(grouped_examples[split]) for split in ("train", "validation", "test")}
    total_final = sum(counts.values())

    split_score_stats = {
        split: summarize_scores([ex.score for ex in grouped_examples[split]])
        for split in ("train", "validation", "test")
    }

    lines = [
        "# Training Dataset Build Report",
        "",
        f"- Input unified dataset: `{input_jsonl}`",
        f"- Output dataset dir: `{output_dataset_dir}`",
        f"- Output provenance dir: `{provenance_dir}`",
        "",
        "## Pipeline Summary",
        "",
        f"- Input non-empty lines processed: `{stats.input_lines}`",
        f"- JSON parse errors skipped: `{stats.parse_errors}`",
        f"- Non-object rows skipped: `{stats.non_object_rows}`",
        f"- Filtered missing split: `{stats.filtered_missing_split}`",
        f"- Filtered invalid split: `{stats.filtered_invalid_split}`",
        f"- Filtered missing prompt: `{stats.filtered_missing_prompt}`",
        f"- Filtered missing essay: `{stats.filtered_missing_essay}`",
        f"- Filtered missing score field: `{stats.filtered_missing_score}`",
        f"- Filtered non-numeric score: `{stats.filtered_non_numeric_score}`",
        f"- Kept before deduplication: `{stats.kept_before_dedup}`",
        f"- Exact duplicates removed: `{stats.dedup_removed}`",
        f"- Final examples: `{total_final}`",
        "",
        "## Final Split Counts",
        "",
        "| split | examples | score_min | score_max | score_mean |",
        "|---|---:|---:|---:|---:|",
    ]

    for split in ("train", "validation", "test"):
        summary = split_score_stats[split]

        def fmt(value: float | None) -> str:
            return "N/A" if value is None else f"{value:.4f}"

        lines.append(
            f"| {split} | {counts[split]} | {fmt(summary['min'])} | "
            f"{fmt(summary['max'])} | {fmt(summary['mean'])} |"
        )

    lines.extend(
        [
            "",
            "## Output Schema",
            "",
            "Training dataset fields (only):",
            "- `prompt`",
            "- `essay`",
            "- `score`",
            "",
            "Provenance is stored separately per split in JSONL files and contains source lineage.",
            "",
            "## HF Load Verification",
            "",
            f"- `datasets.load_from_disk()` status: {'PASS' if load_ok else 'FAIL'}",
            f"- Message: {load_message}",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Run final preprocessing build."""
    args = parse_args()
    input_jsonl = Path(args.input_jsonl)
    output_dataset_dir = Path(args.output_dataset_dir)
    provenance_dir = Path(args.provenance_dir)
    report_path = Path(args.report_path)

    report_path.parent.mkdir(parents=True, exist_ok=True)

    grouped_examples_raw, grouped_provenance_raw, stats = load_and_filter(input_jsonl)
    grouped_examples, grouped_provenance = deduplicate_with_provenance(
        grouped_examples_raw,
        grouped_provenance_raw,
        stats,
    )

    save_training_dataset(output_dataset_dir, grouped_examples)
    save_provenance(provenance_dir, grouped_provenance)

    load_ok = False
    load_message = "unknown"
    try:
        loaded = load_from_disk(str(output_dataset_dir))
        required_splits = {"train", "validation", "test"}
        loaded_splits = set(loaded.keys())
        if loaded_splits != required_splits:
            load_message = (
                f"unexpected splits: expected {sorted(required_splits)}, "
                f"got {sorted(loaded_splits)}"
            )
        else:
            for split in sorted(loaded_splits):
                columns = list(loaded[split].column_names)
                if columns != ["prompt", "essay", "score"]:
                    raise ValueError(f"split {split} columns mismatch: {columns}")
            load_ok = True
            load_message = f"load_from_disk succeeded with splits: {sorted(loaded_splits)}"
    except Exception as exc:  # pragma: no cover
        load_ok = False
        load_message = f"{type(exc).__name__}: {exc}"

    report = render_report(
        input_jsonl=input_jsonl,
        output_dataset_dir=output_dataset_dir,
        provenance_dir=provenance_dir,
        stats=stats,
        grouped_examples=grouped_examples,
        load_ok=load_ok,
        load_message=load_message,
    )
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "output_dataset_dir": str(output_dataset_dir),
                "provenance_dir": str(provenance_dir),
                "report_path": str(report_path),
                "train": len(grouped_examples["train"]),
                "validation": len(grouped_examples["validation"]),
                "test": len(grouped_examples["test"]),
                "load_ok": load_ok,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
