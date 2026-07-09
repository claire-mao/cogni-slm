"""Build a normalized Hugging Face DatasetDict from raw essay files.

Output schema for each example:
{
    "id": str,
    "text": str,
    "score": float,
    "source": str,
    "prompt": str,
    "split": str,
}

The builder preserves train/validation/test splits when present and handles missing
fields gracefully by dropping invalid rows (missing text/score) while continuing.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from datasets import Dataset, DatasetDict, Features, Value

SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".txt"}
TEXT_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

ID_FIELDS = ("id", "essay_id", "example_id", "uuid")
TEXT_FIELDS = ("text", "essay", "argument_text", "student_response", "response", "content")
SCORE_FIELDS = (
    "score",
    "domain1_score",
    "holistic_essay_score",
    "label",
    "rubric_score",
)
PROMPT_FIELDS = ("prompt", "essay_set", "prompt_id", "assignment", "source_text", "context")
SPLIT_FIELDS = ("split", "dataset_split")
SOURCE_FIELDS = ("source",)
ALLOWED_SPLITS = ("train", "validation", "test")


@dataclass(frozen=True)
class FileRecord:
    """One loaded record with source context."""

    row: dict[str, Any]
    source_file: str
    row_index: int


@dataclass
class BuildStats:
    """Aggregate build statistics."""

    files_scanned: int = 0
    files_processed: int = 0
    rows_seen: int = 0
    rows_kept: int = 0
    rows_dropped_missing_text: int = 0
    rows_dropped_missing_score: int = 0
    rows_dropped_bad_score: int = 0
    parse_errors: int = 0


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Build arrow datasets from raw essays.")
    parser.add_argument("--raw-root", default="datasets/raw", help="Input raw dataset root.")
    parser.add_argument("--output-dir", default="datasets/hf/dataset_dict", help="Output path.")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output directory if it already exists.",
    )
    parser.add_argument(
        "--summary-path",
        default="datasets/hf/build_summary.json",
        help="Optional summary JSON path.",
    )
    return parser.parse_args()


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    """Read text file with encoding fallback."""
    errors: list[str] = []
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")

    details = " | ".join(errors) if errors else "unknown"
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Could not decode {path}: {details}")


def first_non_empty(mapping: dict[str, Any], keys: Iterable[str]) -> str | None:
    """Get first non-empty string field by key priority."""
    for key in keys:
        if key in mapping:
            value = str(mapping.get(key, "")).strip()
            if value:
                return value
    return None


def normalize_split(split_value: str | None, default_split: str) -> str:
    """Normalize split names to train/validation/test."""
    if not split_value:
        return default_split

    value = split_value.strip().lower()
    if value in {"val", "valid", "dev", "validation"}:
        return "validation"
    if value in {"test", "testing"}:
        return "test"
    if value in {"train", "training"}:
        return "train"
    return default_split


def infer_default_split(path: Path) -> str:
    """Infer split from filename/path when not explicitly present."""
    name = path.name.lower()
    if "valid" in name or "val" in name or "dev" in name:
        return "validation"
    if "test" in name:
        return "test"
    return "train"


def iter_data_files(raw_root: Path) -> list[Path]:
    """Return candidate data files under raw root."""
    files: list[Path] = []
    for path in sorted(raw_root.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        files.append(path)
    return files


def load_csv_or_tsv(path: Path, delimiter: str) -> list[FileRecord]:
    """Load delimited file into FileRecord rows."""
    text, _encoding = read_text_with_fallback(path)
    reader = csv.DictReader(text.splitlines(), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError(f"No header found in {path}")

    records: list[FileRecord] = []
    for row_index, row in enumerate(reader, start=2):
        records.append(FileRecord(row=dict(row), source_file=str(path), row_index=row_index))
    return records


def load_json(path: Path) -> list[FileRecord]:
    """Load .json file as one or many object rows."""
    text, _encoding = read_text_with_fallback(path)
    payload = json.loads(text)

    rows: list[dict[str, Any]] = []
    if isinstance(payload, dict):
        if "records" in payload and isinstance(payload["records"], list):
            rows = [item for item in payload["records"] if isinstance(item, dict)]
        else:
            rows = [payload]
    elif isinstance(payload, list):
        rows = [item for item in payload if isinstance(item, dict)]

    return [
        FileRecord(row=row, source_file=str(path), row_index=index)
        for index, row in enumerate(rows, start=1)
    ]


def load_jsonl(path: Path) -> list[FileRecord]:
    """Load .jsonl file as object rows."""
    text, _encoding = read_text_with_fallback(path)
    records: list[FileRecord] = []
    for line_index, line in enumerate(text.splitlines(), start=1):
        raw = line.strip()
        if not raw:
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict):
            records.append(FileRecord(row=payload, source_file=str(path), row_index=line_index))
    return records


def load_txt(path: Path) -> list[FileRecord]:
    """Load plain text as a single row with essay text."""
    text, _encoding = read_text_with_fallback(path)
    row = {
        "id": path.stem,
        "text": text,
    }
    return [FileRecord(row=row, source_file=str(path), row_index=1)]


def load_file_records(path: Path) -> list[FileRecord]:
    """Load records from a supported file."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv_or_tsv(path, delimiter=",")
    if suffix == ".tsv":
        return load_csv_or_tsv(path, delimiter="\t")
    if suffix == ".json":
        return load_json(path)
    if suffix == ".jsonl":
        return load_jsonl(path)
    if suffix == ".txt":
        return load_txt(path)
    return []


def parse_score(raw_score: str) -> float:
    """Parse score to float."""
    return float(raw_score)


def normalize_example(
    record: FileRecord, raw_root: Path
) -> tuple[dict[str, Any] | None, str | None]:
    """Normalize one record to the target schema."""
    row = record.row
    text_value = first_non_empty(row, TEXT_FIELDS)
    if text_value is None:
        return None, "missing_text"

    score_raw = first_non_empty(row, SCORE_FIELDS)
    if score_raw is None:
        return None, "missing_score"

    try:
        score_value = parse_score(score_raw)
    except ValueError:
        return None, "bad_score"

    source_value = first_non_empty(row, SOURCE_FIELDS)
    if not source_value:
        relative = Path(record.source_file).relative_to(raw_root)
        source_value = relative.parts[0] if relative.parts else "unknown"

    default_split = infer_default_split(Path(record.source_file))
    split_raw = first_non_empty(row, SPLIT_FIELDS)
    split_value = normalize_split(split_raw, default_split)

    id_value = first_non_empty(row, ID_FIELDS)
    if not id_value:
        source_stub = Path(record.source_file).stem
        id_value = f"{source_value}:{source_stub}:{record.row_index}"

    prompt_value = first_non_empty(row, PROMPT_FIELDS) or ""

    return {
        "id": str(id_value),
        "text": str(text_value),
        "score": float(score_value),
        "source": str(source_value),
        "prompt": str(prompt_value),
        "split": str(split_value),
    }, None


def empty_split_dataset(features: Features) -> Dataset:
    """Create empty dataset with fixed schema."""
    return Dataset.from_dict(
        {
            "id": [],
            "text": [],
            "score": [],
            "source": [],
            "prompt": [],
            "split": [],
        },
        features=features,
    )


def build_dataset_dict(raw_root: Path) -> tuple[DatasetDict, BuildStats]:
    """Build DatasetDict from raw_root."""
    stats = BuildStats()
    records_by_split: dict[str, list[dict[str, Any]]] = {s: [] for s in ALLOWED_SPLITS}

    files = iter_data_files(raw_root)
    stats.files_scanned = len(files)

    for path in files:
        try:
            file_records = load_file_records(path)
            stats.files_processed += 1
        except Exception:
            stats.parse_errors += 1
            continue

        for record in file_records:
            stats.rows_seen += 1
            normalized, err = normalize_example(record, raw_root=raw_root)
            if err == "missing_text":
                stats.rows_dropped_missing_text += 1
                continue
            if err == "missing_score":
                stats.rows_dropped_missing_score += 1
                continue
            if err == "bad_score":
                stats.rows_dropped_bad_score += 1
                continue
            assert normalized is not None
            split = normalized["split"] if normalized["split"] in ALLOWED_SPLITS else "train"
            normalized["split"] = split
            records_by_split[split].append(normalized)
            stats.rows_kept += 1

    features = Features(
        {
            "id": Value("string"),
            "text": Value("string"),
            "score": Value("float64"),
            "source": Value("string"),
            "prompt": Value("string"),
            "split": Value("string"),
        }
    )

    split_map = {
        split: Dataset.from_list(items, features=features)
        for split, items in records_by_split.items()
        if items
    }
    if not split_map:
        split_map["train"] = empty_split_dataset(features)

    dataset_dict = DatasetDict(split_map)
    return dataset_dict, stats


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    raw_root = Path(args.raw_root)
    output_dir = Path(args.output_dir)
    summary_path = Path(args.summary_path)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(
            f"Output directory already exists and is not empty: {output_dir}. Use --overwrite."
        )

    dataset_dict, stats = build_dataset_dict(raw_root=raw_root)
    dataset_dict.save_to_disk(str(output_dir))

    split_counts = {
        split: int(dataset_dict[split].num_rows) if split in dataset_dict else 0
        for split in ALLOWED_SPLITS
    }
    summary = {
        "raw_root": str(raw_root),
        "output_dir": str(output_dir),
        "split_counts": split_counts,
        "stats": asdict(stats),
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
