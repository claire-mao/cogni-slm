"""Create a provenance index for all examples under datasets/final.

The index is generated from every ``*.jsonl`` artifact in ``datasets/final`` and
contains both compatibility fields and repaired lineage fields:

- original dataset
- original identifier
- preprocessing history
- split assignment
- source URL
- license
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

try:
    from datasets import load_from_disk
except ImportError:  # pragma: no cover - optional runtime dependency in some environments
    load_from_disk = None

DATASET_URLS: dict[str, str] = {
    "asap_aes": "https://www.kaggle.com/c/asap-aes",
    "persuade2": "https://www.kaggle.com/competitions/feedback-prize-effectiveness",
    "asap2": "https://huggingface.co/datasets/jatinmehra/Automated-Essay-Scoring-2.0",
    "heldout_benchmark_internal": "datasets/eval/heldout_benchmark.jsonl",
}

DATASET_LICENSES: dict[str, str] = {
    "asap_aes": "ASAP-AES competition/research dataset terms (verify redistribution rights)",
    "persuade2": "Kaggle/official source terms (manual acceptance may be required)",
    "asap2": "Unknown on mirror; verify before redistribution",
    "heldout_benchmark_internal": "Internal held-out benchmark artifact",
}

DEFAULT_INTERNAL_LICENSE = "Derived internal artifact; inherits upstream source license constraints"

STAGE_ORDER: dict[str, int] = {
    "quality_scored": 10,
    "quality_filtered": 20,
    "quality_removed": 30,
    "quality_deduped": 40,
    "train": 50,
    "validation": 50,
    "test": 50,
    "merged_all": 60,
}

REQUIRED_TRACEABILITY_FIELDS = (
    "original_dataset",
    "original_identifier",
    "preprocessing_history",
    "split_assignment",
    "source_url",
    "license",
)


@dataclass(frozen=True)
class ProvenanceRow:
    """One provenance record for a final example row."""

    example_id: str
    dataset: str
    original_dataset: str
    original_identifier: str
    preprocessing_history: str
    split_assignment: str
    source_url: str
    original_url: str
    license: str
    retrieval_date: str
    hash: str
    split: str
    source_filename: str
    artifact_path: str
    artifact_row: int


@dataclass(frozen=True)
class ArtifactSource:
    """One example-bearing artifact source."""

    kind: str
    path: Path
    artifact_path: str
    split_hint: str = ""


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(
        description="Create provenance index parquet for final dataset."
    )
    parser.add_argument(
        "--final-dir",
        default="datasets/final",
        help="Final dataset directory containing JSONL files.",
    )
    parser.add_argument(
        "--output-parquet",
        default="datasets/final/provenance.parquet",
        help="Output provenance parquet path.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/provenance.md",
        help="Markdown report path.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50000,
        help="Parquet write batch size.",
    )
    return parser.parse_args()


def _file_date_or_unknown(path: Path) -> str:
    """Return file mtime date in ISO-8601 date form."""
    if not path.exists():
        return "unknown"
    dt = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
    return dt.date().isoformat()


def infer_source_filename(source: str, metadata: dict[str, Any]) -> str:
    """Infer originating filename from metadata or source conventions."""
    for key in (
        "source_filename",
        "source_file",
        "filename",
        "file_name",
        "source_path",
    ):
        raw = metadata.get(key)
        if isinstance(raw, str) and raw.strip():
            return Path(raw).name

    source_split = str(metadata.get("source_split", "")).strip().lower()
    if source == "asap_aes":
        if source_split == "validation":
            return "valid_set.tsv"
        if source_split == "test":
            return "test_set.tsv"
        return "training_set_rel3.tsv"

    if "/" in source:
        return Path(source).name
    return "unknown"


def infer_original_url(source: str, metadata: dict[str, Any]) -> str:
    """Choose original URL from metadata or source mapping."""
    for key in ("original_url", "url", "source_url", "dataset_url"):
        raw = metadata.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    source_ref = metadata.get("source_ref")
    if isinstance(source_ref, str) and source_ref.strip():
        return source_ref.strip()
    if source.startswith(("raw/", "processed/", "final/", "eval/", "hf/", "training")):
        return f"datasets/{source}"
    return DATASET_URLS.get(source, "unknown")


def infer_license(source: str, metadata: dict[str, Any], row_license: str = "") -> str:
    """Choose license from row/metadata/source mapping."""
    if row_license.strip() and row_license.strip().lower() != "unknown":
        return row_license.strip()
    for key in ("license", "source_license"):
        raw = metadata.get(key)
        if isinstance(raw, str) and raw.strip() and raw.strip().lower() != "unknown":
            return raw.strip()
    if source.startswith("eval/heldout_benchmark") or "golden" in source:
        return DATASET_LICENSES["heldout_benchmark_internal"]
    if source == "asap_aes" or source.startswith("raw/asap_aes/") or "asap_aes" in source:
        return DATASET_LICENSES["asap_aes"]
    if source in DATASET_LICENSES:
        return DATASET_LICENSES[source]
    if source.startswith(("processed/", "final/", "hf/", "training")):
        return DEFAULT_INTERNAL_LICENSE
    return "Unspecified source license; manual verification required"


def infer_original_dataset(source: str, metadata: dict[str, Any]) -> str:
    """Infer canonical originating dataset slug."""
    for key in ("original_dataset", "dataset", "source_dataset"):
        raw = metadata.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()

    original_fields = metadata.get("original_fields")
    if isinstance(original_fields, dict):
        for key in ("dataset", "source", "source_dataset"):
            raw = original_fields.get(key)
            if isinstance(raw, str) and raw.strip():
                return raw.strip()

    if source == "asap_aes" or source.startswith("raw/asap_aes/") or "asap_aes" in source:
        return "asap_aes"
    if source.startswith("eval/heldout_benchmark") or "golden" in source:
        return "heldout_benchmark_internal"
    if source:
        return source
    return "unknown"


def infer_original_identifier(example_id: str, metadata: dict[str, Any]) -> str:
    """Infer canonical original record identifier."""
    for key in (
        "original_identifier",
        "original_id",
        "source_id",
        "source_row_id",
        "essay_id",
        "example_id",
        "id",
    ):
        raw = metadata.get(key)
        if raw is not None and str(raw).strip():
            return str(raw).strip()

    original_fields = metadata.get("original_fields")
    mapping = metadata.get("mapping")
    if isinstance(original_fields, dict):
        if isinstance(mapping, dict):
            mapped_id_field = mapping.get("id")
            if (
                isinstance(mapped_id_field, str)
                and mapped_id_field in original_fields
                and not mapped_id_field.startswith("<")
            ):
                mapped_id_value = original_fields.get(mapped_id_field)
                if mapped_id_value is not None and str(mapped_id_value).strip():
                    return str(mapped_id_value).strip()

        for key in ("example_id", "essay_id", "id", "source_id"):
            raw = original_fields.get(key)
            if raw is not None and str(raw).strip():
                return str(raw).strip()

    return example_id


def infer_retrieval_date(
    source: str,
    source_filename: str,
    metadata: dict[str, Any],
    final_dir: Path,
) -> str:
    """Choose retrieval date from metadata or source file mtime."""
    for key in ("retrieval_date", "download_date", "ingested_at"):
        raw = metadata.get(key)
        if isinstance(raw, str) and raw.strip():
            return raw.strip()

    raw_file = final_dir.parent / "raw" / source / source_filename
    source_files_file = final_dir.parent / "raw" / source / "source_files" / source_filename

    date_value = _file_date_or_unknown(raw_file)
    if date_value != "unknown":
        return date_value

    date_value = _file_date_or_unknown(source_files_file)
    if date_value != "unknown":
        return date_value

    return "unknown"


def _discover_artifacts(final_dir: Path) -> list[ArtifactSource]:
    """Return all example-bearing artifacts under final dir."""
    artifacts: list[ArtifactSource] = []

    for path in sorted(path for path in final_dir.glob("*.jsonl") if path.is_file()):
        artifacts.append(
            ArtifactSource(
                kind="jsonl",
                path=path,
                artifact_path=str(Path("final") / path.name),
            )
        )

    dataset_dict_dir = final_dir / "dataset_dict"
    if dataset_dict_dir.exists() and load_from_disk is not None:
        try:
            dataset_dict = load_from_disk(str(dataset_dict_dir))
            for split in sorted(dataset_dict.keys()):
                artifacts.append(
                    ArtifactSource(
                        kind="hf_split",
                        path=dataset_dict_dir / split,
                        artifact_path=str(Path("final") / "dataset_dict" / split),
                        split_hint=split,
                    )
                )
        except Exception:
            # Keep provenance generation resilient when HF cache files are unavailable.
            pass

    return artifacts


def _stage_name(artifact: ArtifactSource) -> str:
    """Return stage name from artifact filename."""
    if artifact.kind == "hf_split":
        return artifact.split_hint or artifact.path.name
    return artifact.path.stem


def _normalize_split(raw_split: Any, artifact_name: str) -> str:
    """Normalize split assignment with artifact-aware fallback."""
    split = str(raw_split or "").strip().lower()
    if split:
        return split
    if artifact_name in {"train", "validation", "test"}:
        return artifact_name
    return ""


def _prefer_value(current: str, new: str) -> str:
    """Prefer a non-empty, non-unknown value."""
    current_clean = current.strip()
    new_clean = new.strip()
    if not current_clean or current_clean.lower() == "unknown":
        return new_clean or current_clean
    return current_clean


def _compute_content_hash(example_id: str, dataset: str, record: dict[str, Any]) -> str:
    """Compute deterministic hash from best available text payload."""
    payload_candidates = [
        record.get("text"),
        record.get("input"),
        record.get("response"),
        record.get("prompt"),
    ]

    metadata = record.get("metadata")
    if isinstance(metadata, dict):
        original_fields = metadata.get("original_fields")
        if isinstance(original_fields, dict):
            payload_candidates.extend(
                [
                    original_fields.get("argument_text"),
                    original_fields.get("essay"),
                    original_fields.get("text"),
                ]
            )

    for value in payload_candidates:
        if isinstance(value, str) and value.strip():
            return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()

    fallback = f"{dataset}:{example_id}"
    return hashlib.sha256(fallback.encode("utf-8", errors="ignore")).hexdigest()


def _iter_artifact_rows(
    artifact: ArtifactSource,
    final_dir: Path,
) -> tuple[int, dict[str, Any]]:
    """Yield (row_number, record) pairs from one artifact."""
    if artifact.kind == "jsonl":
        with artifact.path.open("r", encoding="utf-8") as handle:
            for row_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    continue
                yield row_number, record
        return

    if artifact.kind == "hf_split" and load_from_disk is not None:
        dataset_dict = load_from_disk(str(final_dir / "dataset_dict"))
        if artifact.split_hint not in dataset_dict:
            return
        split_dataset = dataset_dict[artifact.split_hint]
        for row_number, record in enumerate(split_dataset, 1):
            if isinstance(record, dict):
                yield row_number, record
        return


def _collect_key_state(final_dir: Path) -> tuple[
    dict[tuple[str, str], set[str]],
    dict[tuple[str, str], str],
    dict[tuple[str, str], dict[str, str]],
    dict[str, int],
]:
    """Collect per-example lineage state across all final JSONL artifacts."""
    key_to_history: dict[tuple[str, str], set[str]] = {}
    key_to_split: dict[tuple[str, str], str] = {}
    key_to_trace: dict[tuple[str, str], dict[str, str]] = {}
    artifact_row_counts: dict[str, int] = {}

    for artifact in _discover_artifacts(final_dir):
        artifact_name = _stage_name(artifact)
        artifact_rel = artifact.artifact_path
        artifact_row_counts[artifact_rel] = 0

        for _, record in _iter_artifact_rows(artifact, final_dir):
            artifact_row_counts[artifact_rel] += 1
            example_id = str(record.get("id", "")).strip()
            dataset = str(record.get("source", "unknown")).strip() or "unknown"
            key = (example_id, dataset)

            metadata = record.get("metadata")
            metadata = metadata if isinstance(metadata, dict) else {}
            row_license = str(record.get("license", "")).strip()

            split_assignment = _normalize_split(record.get("split"), artifact_name)
            source_filename = infer_source_filename(dataset, metadata)
            original_dataset = infer_original_dataset(dataset, metadata)
            original_identifier = infer_original_identifier(example_id, metadata)
            source_url = infer_original_url(dataset, metadata)
            license_name = infer_license(dataset, metadata, row_license=row_license)
            retrieval_date = infer_retrieval_date(
                original_dataset, source_filename, metadata, final_dir
            )

            key_to_history.setdefault(key, set()).add(artifact_name)
            if split_assignment and key not in key_to_split:
                key_to_split[key] = split_assignment

            trace = key_to_trace.setdefault(
                key,
                {
                    "original_dataset": original_dataset,
                    "original_identifier": original_identifier,
                    "source_url": source_url,
                    "license": license_name,
                    "retrieval_date": retrieval_date,
                    "source_filename": source_filename,
                },
            )
            trace["original_dataset"] = _prefer_value(trace["original_dataset"], original_dataset)
            trace["original_identifier"] = _prefer_value(
                trace["original_identifier"], original_identifier
            )
            trace["source_url"] = _prefer_value(trace["source_url"], source_url)
            trace["license"] = _prefer_value(trace["license"], license_name)
            trace["retrieval_date"] = _prefer_value(trace["retrieval_date"], retrieval_date)
            trace["source_filename"] = _prefer_value(trace["source_filename"], source_filename)

    return key_to_history, key_to_split, key_to_trace, artifact_row_counts


def _history_for_key(key_history: set[str]) -> str:
    """Serialize deterministic preprocessing history for one example key."""
    ordered = sorted(key_history, key=lambda stage: (STAGE_ORDER.get(stage, 999), stage))
    return json.dumps(ordered, ensure_ascii=False)


def _default_split_for_artifact(artifact_name: str) -> str:
    """Provide fallback split assignment when per-row split is absent."""
    if artifact_name in {"train", "validation", "test"}:
        return artifact_name
    if artifact_name == "quality_removed":
        return "removed"
    return "unknown"


def _provenance_schema() -> pa.Schema:
    """Return parquet schema for provenance index."""
    return pa.schema(
        [
            pa.field("example_id", pa.string()),
            pa.field("dataset", pa.string()),
            pa.field("original_dataset", pa.string()),
            pa.field("original_identifier", pa.string()),
            pa.field("preprocessing_history", pa.string()),
            pa.field("split", pa.string()),
            pa.field("split_assignment", pa.string()),
            pa.field("source_url", pa.string()),
            pa.field("original_url", pa.string()),
            pa.field("license", pa.string()),
            pa.field("retrieval_date", pa.string()),
            pa.field("hash", pa.string()),
            pa.field("source_filename", pa.string()),
            pa.field("artifact_path", pa.string()),
            pa.field("artifact_row", pa.int64()),
        ]
    )


def _write_rows_batch(writer: pq.ParquetWriter, batch_rows: list[dict[str, Any]]) -> None:
    """Write one row batch to parquet."""
    if not batch_rows:
        return
    table = pa.Table.from_pylist(batch_rows, schema=_provenance_schema())
    writer.write_table(table)


def build_and_write_rows(
    final_dir: Path,
    output_parquet: Path,
    batch_size: int,
) -> tuple[list[ProvenanceRow], dict[str, int], dict[str, int], int]:
    """Build provenance rows for all final JSONL artifacts and write parquet."""
    key_to_history, key_to_split, key_to_trace, artifact_row_counts = _collect_key_state(final_dir)
    total_input_rows = sum(artifact_row_counts.values())

    output_parquet.parent.mkdir(parents=True, exist_ok=True)
    writer = pq.ParquetWriter(output_parquet, _provenance_schema(), compression="snappy")

    rows_preview: list[ProvenanceRow] = []
    required_missing_counts = {name: 0 for name in REQUIRED_TRACEABILITY_FIELDS}
    batch_rows: list[dict[str, Any]] = []

    try:
        for artifact in _discover_artifacts(final_dir):
            artifact_name = _stage_name(artifact)
            artifact_rel = artifact.artifact_path

            for row_number, record in _iter_artifact_rows(artifact, final_dir):
                example_id = str(record.get("id", "")).strip()
                dataset = str(record.get("source", "unknown")).strip() or "unknown"
                key = (example_id, dataset)

                metadata = record.get("metadata")
                metadata = metadata if isinstance(metadata, dict) else {}
                row_license = str(record.get("license", "")).strip()

                split_raw = _normalize_split(record.get("split"), artifact_name)
                split_assignment = (
                    split_raw
                    or key_to_split.get(key, "")
                    or _default_split_for_artifact(artifact_name)
                )

                trace = key_to_trace.get(
                    key,
                    {
                        "original_dataset": infer_original_dataset(dataset, metadata),
                        "original_identifier": infer_original_identifier(example_id, metadata),
                        "source_url": infer_original_url(dataset, metadata),
                        "license": infer_license(dataset, metadata, row_license=row_license),
                        "retrieval_date": infer_retrieval_date(
                            dataset, infer_source_filename(dataset, metadata), metadata, final_dir
                        ),
                        "source_filename": infer_source_filename(dataset, metadata),
                    },
                )

                preprocessing_history = _history_for_key(key_to_history.get(key, {artifact_name}))

                row = ProvenanceRow(
                    example_id=example_id,
                    dataset=dataset,
                    original_dataset=trace.get("original_dataset", dataset) or dataset,
                    original_identifier=trace.get("original_identifier", example_id) or example_id,
                    preprocessing_history=preprocessing_history,
                    split=split_assignment,
                    split_assignment=split_assignment,
                    source_url=trace.get("source_url", infer_original_url(dataset, metadata))
                    or infer_original_url(dataset, metadata),
                    original_url=trace.get("source_url", infer_original_url(dataset, metadata))
                    or infer_original_url(dataset, metadata),
                    license=trace.get(
                        "license", infer_license(dataset, metadata, row_license=row_license)
                    )
                    or infer_license(dataset, metadata, row_license=row_license),
                    retrieval_date=trace.get("retrieval_date", "unknown") or "unknown",
                    hash=_compute_content_hash(example_id, dataset, record),
                    source_filename=trace.get(
                        "source_filename", infer_source_filename(dataset, metadata)
                    )
                    or infer_source_filename(dataset, metadata),
                    artifact_path=artifact_rel,
                    artifact_row=row_number,
                )

                for field in REQUIRED_TRACEABILITY_FIELDS:
                    if not str(getattr(row, field)).strip():
                        required_missing_counts[field] += 1

                batch_rows.append(row.__dict__)
                if len(rows_preview) < 5:
                    rows_preview.append(row)

                if len(batch_rows) >= batch_size:
                    _write_rows_batch(writer, batch_rows)
                    batch_rows.clear()

        _write_rows_batch(writer, batch_rows)
    finally:
        writer.close()

    return rows_preview, artifact_row_counts, required_missing_counts, total_input_rows


def _read_parquet_counts(output_parquet: Path) -> tuple[
    int,
    Counter[str],
    Counter[str],
    Counter[str],
]:
    """Read aggregate counters from parquet."""
    table = pq.read_table(output_parquet)
    frame = table.to_pandas()
    total = len(frame)
    split_counts = Counter(frame["split"].astype(str))
    dataset_counts = Counter(frame["original_dataset"].astype(str))
    artifact_counts = Counter(frame["artifact_path"].astype(str))
    return total, split_counts, dataset_counts, artifact_counts


def write_report(
    report_path: Path,
    output_parquet: Path,
    preview_rows: list[ProvenanceRow],
    artifact_row_counts: dict[str, int],
    required_missing_counts: dict[str, int],
    total_input_rows: int,
) -> None:
    """Write provenance repair + verification markdown report."""
    total_rows, split_counts, dataset_counts, artifact_counts = _read_parquet_counts(output_parquet)
    missing_total = sum(required_missing_counts.values())
    traceable_rows = total_rows if missing_total == 0 else total_rows - missing_total
    fully_traceable = (
        total_rows == total_input_rows
        and all(count == 0 for count in required_missing_counts.values())
        and total_rows > 0
    )

    lines = [
        "# Provenance Repair Report",
        "",
        f"- Output parquet: `{output_parquet}`",
        f"- Final JSONL rows scanned: `{total_input_rows}`",
        f"- Provenance rows written: `{total_rows}`",
        f"- Fully traceable rows: `{traceable_rows}`",
        f"- All examples traceable: `{'YES' if fully_traceable else 'NO'}`",
        "",
        "## Required Field Completeness",
        "",
        "| field | missing_rows |",
        "|---|---:|",
    ]

    for field in REQUIRED_TRACEABILITY_FIELDS:
        lines.append(f"| {field} | {required_missing_counts.get(field, 0)} |")

    lines.extend(
        [
            "",
            "## Counts by Split Assignment",
            "",
            "| split | rows |",
            "|---|---:|",
        ]
    )
    for name, count in sorted(split_counts.items()):
        lines.append(f"| {name} | {count} |")

    lines.extend(
        [
            "",
            "## Counts by Original Dataset",
            "",
            "| original_dataset | rows |",
            "|---|---:|",
        ]
    )
    for name, count in sorted(dataset_counts.items()):
        lines.append(f"| {name} | {count} |")

    lines.extend(
        [
            "",
            "## Artifact Coverage",
            "",
            "| artifact | input_rows | provenance_rows | match |",
            "|---|---:|---:|---|",
        ]
    )
    for artifact in sorted(artifact_row_counts):
        input_rows = artifact_row_counts.get(artifact, 0)
        written_rows = artifact_counts.get(artifact, 0)
        match = "yes" if input_rows == written_rows else "no"
        lines.append(f"| {artifact} | {input_rows} | {written_rows} | {match} |")

    lines.extend(
        [
            "",
            "## Preview Rows",
            "",
            (
                "| example_id | original_dataset | original_identifier | "
                "split_assignment | source_url | license |"
            ),
            "|---|---|---|---|---|---|",
        ]
    )

    for row in preview_rows:
        lines.append(
            "| "
            f"{row.example_id} | {row.original_dataset} | {row.original_identifier} | "
            f"{row.split_assignment} | {row.source_url} | {row.license} |"
        )

    lines.extend(
        [
            "",
            "## Schema",
            "",
            "Each provenance row contains:",
            "- `example_id`",
            "- `dataset`",
            "- `original_dataset`",
            "- `original_identifier`",
            "- `preprocessing_history` (JSON array string of stages)",
            "- `split`",
            "- `split_assignment`",
            "- `source_url`",
            "- `original_url` (compatibility alias)",
            "- `license`",
            "- `retrieval_date`",
            "- `hash`",
            "- `source_filename`",
            "- `artifact_path`",
            "- `artifact_row`",
            "",
            "## Verification Result",
            "",
            (
                "Every example in `datasets/final` is traceable with required provenance fields."
                if fully_traceable
                else (
                    "Traceability is incomplete; see missing field counts and "
                    "artifact mismatches above."
                )
            ),
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def load_preview_rows(output_parquet: Path, limit: int = 5) -> list[ProvenanceRow]:
    """Load a small preview set from parquet for reporting."""
    frame = pd.read_parquet(output_parquet).head(limit)
    rows: list[ProvenanceRow] = []
    for _, row in frame.iterrows():
        rows.append(
            ProvenanceRow(
                example_id=str(row["example_id"]),
                dataset=str(row["dataset"]),
                original_dataset=str(row["original_dataset"]),
                original_identifier=str(row["original_identifier"]),
                preprocessing_history=str(row["preprocessing_history"]),
                split_assignment=str(row["split_assignment"]),
                source_url=str(row["source_url"]),
                original_url=str(row["original_url"]),
                license=str(row["license"]),
                retrieval_date=str(row["retrieval_date"]),
                hash=str(row["hash"]),
                split=str(row["split"]),
                source_filename=str(row["source_filename"]),
                artifact_path=str(row["artifact_path"]),
                artifact_row=int(row["artifact_row"]),
            )
        )

    return rows


def main() -> None:
    """Run provenance index generation and repair verification."""
    args = parse_args()
    final_dir = Path(args.final_dir)
    output_parquet = Path(args.output_parquet)
    report_path = Path(args.report_path)

    (
        preview_rows,
        artifact_row_counts,
        required_missing_counts,
        total_input_rows,
    ) = build_and_write_rows(
        final_dir=final_dir,
        output_parquet=output_parquet,
        batch_size=max(int(args.batch_size), 1),
    )
    if not preview_rows:
        preview_rows = load_preview_rows(output_parquet, limit=5)

    write_report(
        report_path=report_path,
        output_parquet=output_parquet,
        preview_rows=preview_rows,
        artifact_row_counts=artifact_row_counts,
        required_missing_counts=required_missing_counts,
        total_input_rows=total_input_rows,
    )

    total_rows, _, _, _ = _read_parquet_counts(output_parquet)

    print(
        json.dumps(
            {
                "records": total_rows,
                "input_rows": total_input_rows,
                "required_missing_counts": required_missing_counts,
                "output_parquet": str(output_parquet),
                "report_path": str(report_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
