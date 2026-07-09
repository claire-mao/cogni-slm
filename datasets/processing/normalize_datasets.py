"""Normalize raw datasets to a canonical schema.

Canonical schema:
{
    "id": string,
    "source": string,
    "task": string,
    "prompt": string,
    "text": string,
    "label": float,
    "metadata": dict,
}

This module preserves metadata by storing original row payload and source context
under `metadata`.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".txt"}
ENCODING_FALLBACKS = ("utf-8-sig", "cp1252", "latin-1")

ID_FIELDS = ("id", "essay_id", "example_id", "uuid")
TEXT_FIELDS = ("text", "essay", "argument_text", "student_response", "response", "content")
LABEL_FIELDS = (
    "score",
    "label",
    "domain1_score",
    "holistic_essay_score",
    "rubric_score",
)
PROMPT_FIELDS = (
    "prompt",
    "essay_set",
    "prompt_id",
    "assignment",
    "source_text",
    "context",
)
TASK_FIELDS = ("task", "task_mode")


@dataclass
class NormalizeStats:
    """Normalization stats per dataset."""

    dataset: str
    files_seen: int = 0
    files_processed: int = 0
    parse_errors: int = 0
    rows_seen: int = 0
    rows_kept: int = 0
    rows_dropped_missing_text: int = 0
    rows_missing_label: int = 0


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Normalize datasets into canonical schema.")
    parser.add_argument("--raw-root", default="datasets/raw", help="Raw dataset root directory.")
    parser.add_argument(
        "--output-dir",
        default="datasets/processed/normalized",
        help="Output directory for normalized JSONL files.",
    )
    parser.add_argument(
        "--summary-path",
        default="datasets/processed/normalized/summary.json",
        help="Summary JSON output path.",
    )
    return parser.parse_args()


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    """Read a text file with fallback encodings."""
    decode_errors: list[str] = []
    for encoding in ENCODING_FALLBACKS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")

    details = " | ".join(decode_errors) if decode_errors else "unknown"
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Failed to decode {path}: {details}")


def first_non_empty(payload: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    """Return first non-empty string value for given keys."""
    for key in keys:
        if key in payload:
            value = str(payload.get(key, "")).strip()
            if value:
                return value
    return None


def infer_task(payload: dict[str, Any]) -> str:
    """Infer canonical task from row fields."""
    explicit = first_non_empty(payload, TASK_FIELDS)
    if explicit:
        return explicit

    payload_keys = {k.lower() for k in payload.keys()}
    if payload_keys.intersection(
        {"domain1_score", "holistic_essay_score", "rubric_score", "score"}
    ):
        return "essay_scoring"
    if payload_keys.intersection({"primary_fallacy_label", "acceptable_alternative_labels"}):
        return "fallacy_reasoning"
    return "unknown"


def parse_label(payload: dict[str, Any]) -> tuple[float | None, str | None]:
    """Parse canonical label as float when available."""
    raw = first_non_empty(payload, LABEL_FIELDS)
    if raw is None:
        return None, None
    try:
        return float(raw), raw
    except ValueError:
        return None, raw


def normalize_split_from_path(path: Path) -> str | None:
    """Infer split from filename when available."""
    name = path.name.lower()
    if "train" in name:
        return "train"
    if "valid" in name or "val" in name or "dev" in name:
        return "validation"
    if "test" in name:
        return "test"
    return None


def load_csv_or_tsv(path: Path, delimiter: str) -> tuple[list[dict[str, Any]], str]:
    """Load CSV/TSV rows as dicts."""
    text, encoding = read_text_with_fallback(path)
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if not reader.fieldnames:
        return [], encoding

    rows: list[dict[str, Any]] = []
    for row in reader:
        rows.append({k: v for k, v in row.items()})
    return rows, encoding


def load_json(path: Path) -> tuple[list[dict[str, Any]], str]:
    """Load .json rows."""
    text, encoding = read_text_with_fallback(path)
    payload = json.loads(text)

    if isinstance(payload, dict):
        if "records" in payload and isinstance(payload["records"], list):
            rows = [item for item in payload["records"] if isinstance(item, dict)]
        else:
            rows = [payload]
        return rows, encoding

    if isinstance(payload, list):
        rows = [item for item in payload if isinstance(item, dict)]
        return rows, encoding

    return [], encoding


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], str]:
    """Load .jsonl rows."""
    text, encoding = read_text_with_fallback(path)
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        raw = line.strip()
        if not raw:
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows, encoding


def load_txt(path: Path) -> tuple[list[dict[str, Any]], str]:
    """Load .txt as single text record."""
    text, encoding = read_text_with_fallback(path)
    return [{"id": path.stem, "text": text}], encoding


def load_rows(path: Path) -> tuple[list[dict[str, Any]], str]:
    """Load rows from a supported file path."""
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
    return [], "unknown"


def normalize_row(
    *,
    row: dict[str, Any],
    dataset_name: str,
    source_file: Path,
    row_index: int,
    encoding: str,
) -> dict[str, Any] | None:
    """Normalize one row to canonical schema."""
    text = first_non_empty(row, TEXT_FIELDS)
    if text is None:
        return None

    label_value, label_raw = parse_label(row)

    source_value = first_non_empty(row, ("source",)) or dataset_name
    prompt_value = first_non_empty(row, PROMPT_FIELDS) or ""

    raw_id = first_non_empty(row, ID_FIELDS)
    if not raw_id:
        raw_id = f"{dataset_name}:{source_file.stem}:{row_index}"

    task = infer_task(row)

    metadata = {
        "source_file": str(source_file),
        "row_index": row_index,
        "encoding": encoding,
        "split_hint": normalize_split_from_path(source_file),
        "label_raw": label_raw,
        "raw_row": row,
    }

    return {
        "id": str(raw_id),
        "source": str(source_value),
        "task": str(task),
        "prompt": str(prompt_value),
        "text": str(text),
        "label": label_value,
        "metadata": metadata,
    }


def iter_dataset_dirs(raw_root: Path) -> list[Path]:
    """Return top-level dataset directories under raw root."""
    return [
        path
        for path in sorted(raw_root.iterdir())
        if path.is_dir() and not path.name.startswith(".")
    ]


def iter_supported_files(dataset_dir: Path) -> list[Path]:
    """Return supported files within a dataset directory."""
    files: list[Path] = []
    for path in sorted(dataset_dir.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        files.append(path)
    return files


def normalize_dataset(dataset_dir: Path, output_dir: Path) -> tuple[Path, NormalizeStats]:
    """Normalize one dataset directory and write JSONL output."""
    dataset_name = dataset_dir.name
    stats = NormalizeStats(dataset=dataset_name)
    output_path = output_dir / f"{dataset_name}.jsonl"

    files = iter_supported_files(dataset_dir)
    stats.files_seen = len(files)

    with output_path.open("w", encoding="utf-8") as handle:
        for path in files:
            try:
                rows, encoding = load_rows(path)
                stats.files_processed += 1
            except Exception:
                stats.parse_errors += 1
                continue

            for row_index, row in enumerate(rows, start=1):
                stats.rows_seen += 1
                normalized = normalize_row(
                    row=row,
                    dataset_name=dataset_name,
                    source_file=path,
                    row_index=row_index,
                    encoding=encoding,
                )
                if normalized is None:
                    stats.rows_dropped_missing_text += 1
                    continue
                if normalized["label"] is None:
                    stats.rows_missing_label += 1

                handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
                stats.rows_kept += 1

    return output_path, stats


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    raw_root = Path(args.raw_root)
    output_dir = Path(args.output_dir)
    summary_path = Path(args.summary_path)

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    dataset_dirs = iter_dataset_dirs(raw_root)
    per_dataset_outputs: dict[str, str] = {}
    all_stats: list[NormalizeStats] = []

    for dataset_dir in dataset_dirs:
        output_path, stats = normalize_dataset(dataset_dir=dataset_dir, output_dir=output_dir)
        per_dataset_outputs[dataset_dir.name] = str(output_path)
        all_stats.append(stats)

    # Build combined file across all normalized datasets.
    combined_path = output_dir / "all_datasets.jsonl"
    with combined_path.open("w", encoding="utf-8") as out_handle:
        for dataset_name in sorted(per_dataset_outputs.keys()):
            path = Path(per_dataset_outputs[dataset_name])
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    out_handle.write(line + "\n")

    summary = {
        "raw_root": str(raw_root),
        "output_dir": str(output_dir),
        "combined_output": str(combined_path),
        "datasets": [asdict(item) for item in all_stats],
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
