"""Ingest and normalize raw AP Language essays into one JSONL file.

Supported input formats under datasets/raw/:
- .txt
- .csv
- .tsv
- .json
- .jsonl

Normalized output record schema:
{
  "id": "...",
  "essay": "...",
  "source": "...",
  "metadata": {...}
}
"""

from __future__ import annotations

import argparse
import csv
import io
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_SUFFIXES = {".txt", ".csv", ".tsv", ".json", ".jsonl"}
ID_FIELD_CANDIDATES = ("id", "essay_id", "example_id", "uuid")
ESSAY_FIELD_CANDIDATES = ("essay", "text", "student_response", "response", "argument", "content")
TEXT_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")


class MalformedFileError(ValueError):
    """Raised when a file cannot be parsed according to its declared format."""


@dataclass(frozen=True)
class CandidateRecord:
    """Candidate normalized record extracted from one source file."""

    record_id: str
    essay: str
    source: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Rejection:
    """One rejected candidate with reason and source."""

    reason: str
    source: str
    message: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for ingestion."""
    parser = argparse.ArgumentParser(description="Ingest and normalize raw essay sources.")
    parser.add_argument(
        "--raw-dir",
        default="datasets/raw",
        help="Directory containing raw source files.",
    )
    parser.add_argument(
        "--output-jsonl",
        default="datasets/processed/raw_essays.jsonl",
        help="Normalized output JSONL path.",
    )
    parser.add_argument(
        "--report-path",
        default="outputs/data_ingestion/report.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=300,
        help="Minimum word count required for accepted essays.",
    )
    return parser.parse_args()


def safe_id(value: str) -> str:
    """Create a stable ID string safe for use across files."""
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return cleaned.strip("_")


def normalize_essay_text(text: str) -> str:
    """Collapse essay whitespace for consistent downstream processing."""
    return " ".join(text.split())


def count_words(text: str) -> int:
    """Count whitespace-delimited words."""
    return len(text.split())


def first_present(payload: dict[str, Any], candidates: tuple[str, ...]) -> str | None:
    """Return the first non-empty string value among candidate keys."""
    for key in candidates:
        if key in payload:
            value = str(payload.get(key, "")).strip()
            if value:
                return value
    return None


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    """Read text using ordered encoding fallbacks."""
    decode_errors: list[str] = []
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")
            continue
        except OSError as exc:
            raise MalformedFileError(f"File read error in {path}: {exc}") from exc

    details = " | ".join(decode_errors) if decode_errors else "Unknown decode failure."
    raise MalformedFileError(
        f"Could not decode {path} using utf-8-sig, cp1252, or latin-1. Details: {details}"
    )


def parse_score(value: str) -> int | float | str:
    """Parse score into int/float when possible, else keep raw string."""
    raw = value.strip()
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def is_asap_aes_row(payload: dict[str, Any]) -> bool:
    """Return True when row matches ASAP-AES core schema."""
    return "essay_id" in payload and "essay" in payload


def candidate_from_mapping(
    payload: dict[str, Any],
    *,
    fallback_id: str,
    source: str,
    source_file: str,
    source_format: str,
    row_number: int | None = None,
    encoding: str | None = None,
) -> CandidateRecord:
    """Build one candidate record from a mapping-like payload."""
    if is_asap_aes_row(payload):
        essay_raw = str(payload.get("essay", "")).strip()
        if not essay_raw:
            raise MalformedFileError(f"Missing essay field in {source}.")

        record_id_raw = str(payload.get("essay_id", "")).strip() or fallback_id
        record_id = safe_id(record_id_raw)
        if not record_id:
            raise MalformedFileError(f"Could not derive non-empty ID for {source}.")

        metadata: dict[str, Any] = {
            "source_format": source_format,
            "source_file": source_file,
        }
        if encoding is not None:
            metadata["encoding"] = encoding
        if row_number is not None:
            metadata["row_number"] = row_number

        essay_set_value = str(payload.get("essay_set", "")).strip()
        if essay_set_value:
            metadata["essay_set"] = essay_set_value

        domain1_score = str(payload.get("domain1_score", "")).strip()
        if domain1_score:
            metadata["score"] = parse_score(domain1_score)

        return CandidateRecord(
            record_id=record_id,
            essay=normalize_essay_text(essay_raw),
            source="ASAP-AES",
            metadata=metadata,
        )

    essay_raw = first_present(payload, ESSAY_FIELD_CANDIDATES)
    if essay_raw is None:
        raise MalformedFileError(f"Missing essay field in {source}.")

    record_id_raw = first_present(payload, ID_FIELD_CANDIDATES) or fallback_id
    record_id = safe_id(record_id_raw)
    if not record_id:
        raise MalformedFileError(f"Could not derive non-empty ID for {source}.")

    essay = normalize_essay_text(essay_raw)
    metadata: dict[str, Any] = {
        "source_format": source_format,
        "source_file": source_file,
    }
    if encoding is not None:
        metadata["encoding"] = encoding
    if row_number is not None:
        metadata["row_number"] = row_number
    return CandidateRecord(record_id=record_id, essay=essay, source=source, metadata=metadata)


def load_txt(path: Path) -> list[CandidateRecord]:
    """Load one essay per .txt file."""
    text, encoding = read_text_with_fallback(path)

    candidate = candidate_from_mapping(
        {"id": safe_id(path.stem), "essay": text},
        fallback_id=safe_id(path.stem),
        source=str(path),
        source_file=str(path),
        source_format="txt",
        encoding=encoding,
    )
    return [candidate]


def load_csv(path: Path) -> list[CandidateRecord]:
    """Load candidate essays from delimited rows."""
    suffix = path.suffix.lower()
    if suffix == ".csv":
        delimiter = ","
        source_format = "csv"
        label = "CSV"
    elif suffix == ".tsv":
        delimiter = "\t"
        source_format = "tsv"
        label = "TSV"
    else:
        raise MalformedFileError(f"Unsupported delimited file extension for {path}.")

    candidates: list[CandidateRecord] = []
    text, encoding = read_text_with_fallback(path)
    try:
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            raise MalformedFileError(f"No {label} header detected in {path}.")

        for row_index, row in enumerate(reader, start=2):
            if row is None:
                raise MalformedFileError(f"Malformed {label} row in {path} at line {row_index}.")
            candidate = candidate_from_mapping(
                row,
                fallback_id=f"{safe_id(path.stem)}-{row_index:05d}",
                source=f"{path}:{row_index}",
                source_file=str(path),
                source_format=source_format,
                row_number=row_index,
                encoding=encoding,
            )
            candidates.append(candidate)
    except csv.Error as exc:
        raise MalformedFileError(f"{label} parse error in {path}: {exc}") from exc

    return candidates


def load_json(path: Path) -> list[CandidateRecord]:
    """Load candidates from .json object or list of objects."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise MalformedFileError(f"JSON parse error in {path}: {exc}") from exc

    candidates: list[CandidateRecord] = []
    if isinstance(payload, dict):
        if "essay" in payload or any(key in payload for key in ESSAY_FIELD_CANDIDATES):
            candidate = candidate_from_mapping(
                payload,
                fallback_id=safe_id(path.stem),
                source=str(path),
                source_file=str(path),
                source_format="json",
            )
            candidates.append(candidate)
            return candidates

        if "records" in payload and isinstance(payload["records"], list):
            for index, item in enumerate(payload["records"], start=1):
                if not isinstance(item, dict):
                    raise MalformedFileError(f"Non-object record in {path} records[{index - 1}].")
                candidate = candidate_from_mapping(
                    item,
                    fallback_id=f"{safe_id(path.stem)}-{index:05d}",
                    source=f"{path}#records[{index - 1}]",
                    source_file=str(path),
                    source_format="json",
                    row_number=index,
                )
                candidates.append(candidate)
            return candidates

        raise MalformedFileError(f"Unsupported JSON object shape in {path}.")

    if isinstance(payload, list):
        for index, item in enumerate(payload, start=1):
            if not isinstance(item, dict):
                raise MalformedFileError(f"Non-object list entry in {path} at index {index - 1}.")
            candidate = candidate_from_mapping(
                item,
                fallback_id=f"{safe_id(path.stem)}-{index:05d}",
                source=f"{path}#{index - 1}",
                source_file=str(path),
                source_format="json",
                row_number=index,
            )
            candidates.append(candidate)
        return candidates

    raise MalformedFileError(f"Unsupported JSON root type in {path}.")


def load_jsonl(path: Path) -> list[CandidateRecord]:
    """Load candidates from .jsonl where each line is a JSON object."""
    candidates: list[CandidateRecord] = []
    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, line in enumerate(lines, start=1):
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise MalformedFileError(
                f"JSONL parse error in {path} at line {line_number}: {exc}"
            ) from exc

        if not isinstance(payload, dict):
            raise MalformedFileError(f"Non-object JSONL row in {path} at line {line_number}.")
        candidate = candidate_from_mapping(
            payload,
            fallback_id=f"{safe_id(path.stem)}-{line_number:05d}",
            source=f"{path}:{line_number}",
            source_file=str(path),
            source_format="jsonl",
            row_number=line_number,
        )
        candidates.append(candidate)
    return candidates


def load_candidates_for_file(path: Path) -> list[CandidateRecord]:
    """Load candidates from one file based on extension."""
    suffix = path.suffix.lower()
    if suffix == ".txt":
        return load_txt(path)
    if suffix == ".csv":
        return load_csv(path)
    if suffix == ".tsv":
        return load_csv(path)
    if suffix == ".json":
        return load_json(path)
    if suffix == ".jsonl":
        return load_jsonl(path)
    return []


def render_report(
    *,
    raw_dir: Path,
    output_jsonl: Path,
    files_scanned: int,
    files_supported: int,
    malformed_files: list[Rejection],
    total_candidates: int,
    accepted: int,
    rejected: list[Rejection],
    min_words: int,
) -> str:
    """Render ingestion report as markdown."""
    reason_counts: dict[str, int] = {}
    for item in rejected:
        reason_counts[item.reason] = reason_counts.get(item.reason, 0) + 1

    lines = [
        "# Data Ingestion Report",
        "",
        f"- Raw directory: `{raw_dir}`",
        f"- Output JSONL: `{output_jsonl}`",
        f"- Files scanned: `{files_scanned}`",
        f"- Supported files processed: `{files_supported}`",
        f"- Malformed files rejected: `{len(malformed_files)}`",
        f"- Candidate records discovered: `{total_candidates}`",
        f"- Accepted records: `{accepted}`",
        f"- Rejected records: `{len(rejected)}`",
        f"- Minimum word threshold: `{min_words}`",
        "",
        "## Rejections by Reason",
        "",
    ]

    if reason_counts:
        for reason, count in sorted(reason_counts.items()):
            lines.append(f"- `{reason}`: `{count}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Malformed Files", ""])
    if malformed_files:
        for issue in malformed_files:
            lines.append(f"- `{issue.source}`: {issue.message}")
    else:
        lines.append("- None")

    lines.extend(["", "## Rejected Examples (first 50)", ""])
    if rejected:
        for issue in rejected[:50]:
            lines.append(f"- `{issue.source}` [{issue.reason}]: {issue.message}")
        if len(rejected) > 50:
            lines.append(f"- ... {len(rejected) - 50} additional rejected records omitted.")
    else:
        lines.append("- None")

    return "\n".join(lines)


def main() -> None:
    """Run raw essay ingestion and normalization."""
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    output_jsonl = Path(args.output_jsonl)
    report_path = Path(args.report_path)

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    all_files = sorted(
        path for path in raw_dir.rglob("*") if path.is_file() and not path.name.startswith(".")
    )
    supported_files = [path for path in all_files if path.suffix.lower() in SUPPORTED_SUFFIXES]

    seen_ids: set[str] = set()
    accepted_records: list[dict[str, Any]] = []
    malformed_files: list[Rejection] = []
    rejected: list[Rejection] = []
    total_candidates = 0

    for path in supported_files:
        try:
            candidates = load_candidates_for_file(path)
        except MalformedFileError as exc:
            malformed_files.append(
                Rejection(
                    reason="malformed_file",
                    source=str(path),
                    message=str(exc),
                )
            )
            continue

        total_candidates += len(candidates)
        for candidate in candidates:
            if not candidate.essay:
                rejected.append(
                    Rejection(
                        reason="empty_essay",
                        source=candidate.source,
                        message="Essay text is empty after normalization.",
                    )
                )
                continue

            word_count = count_words(candidate.essay)
            if word_count < args.min_words:
                rejected.append(
                    Rejection(
                        reason="essay_too_short",
                        source=candidate.source,
                        message=(
                            f"Essay has {word_count} words; minimum required is {args.min_words}."
                        ),
                    )
                )
                continue

            if candidate.record_id in seen_ids:
                rejected.append(
                    Rejection(
                        reason="duplicate_id",
                        source=candidate.source,
                        message=f"Duplicate ID encountered: {candidate.record_id}",
                    )
                )
                continue

            seen_ids.add(candidate.record_id)
            metadata = dict(candidate.metadata)
            metadata["word_count"] = word_count
            accepted_records.append(
                {
                    "id": candidate.record_id,
                    "essay": candidate.essay,
                    "source": candidate.source,
                    "metadata": metadata,
                }
            )

    with output_jsonl.open("w", encoding="utf-8") as handle:
        for record in accepted_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    report_text = render_report(
        raw_dir=raw_dir,
        output_jsonl=output_jsonl,
        files_scanned=len(all_files),
        files_supported=len(supported_files),
        malformed_files=malformed_files,
        total_candidates=total_candidates,
        accepted=len(accepted_records),
        rejected=rejected,
        min_words=args.min_words,
    )
    report_path.write_text(report_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "files_scanned": len(all_files),
                "files_supported": len(supported_files),
                "malformed_files": len(malformed_files),
                "total_candidates": total_candidates,
                "accepted": len(accepted_records),
                "rejected": len(rejected),
                "output_jsonl": str(output_jsonl),
                "report_path": str(report_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
