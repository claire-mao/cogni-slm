"""Offline ingestion pipeline for private educational documents.

This script only reads local files from datasets/private and writes local outputs.
It does not perform any network activity, uploads, or remote sync.

Supported input formats:
- .pdf
- text files: .txt, .md, .text

Normalized output schema:
{
  "id": "...",
  "essay": "...",
  "source": "private_local",
  "metadata": {
    "filename": "...",
    "page_number": 1,
    ...
  }
}
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TEXT_SUFFIXES = {".txt", ".md", ".text"}
PDF_SUFFIXES = {".pdf"}
SUPPORTED_SUFFIXES = TEXT_SUFFIXES | PDF_SUFFIXES
TEXT_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")

try:
    from pypdf import PdfReader  # type: ignore
except ImportError:
    try:
        from PyPDF2 import PdfReader  # type: ignore
    except ImportError:
        PdfReader = None


class MalformedFileError(ValueError):
    """Raised when a local document cannot be parsed."""


@dataclass(frozen=True)
class DocumentChunk:
    """One normalized text chunk with provenance."""

    record_id: str
    essay: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class Rejection:
    """One rejected file/chunk with reason and message."""

    reason: str
    source: str
    message: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Ingest private local documents offline.")
    parser.add_argument(
        "--input-dir",
        default="datasets/private",
        help="Directory containing private local documents.",
    )
    parser.add_argument(
        "--output-jsonl",
        default="datasets/processed/private_documents.jsonl",
        help="Output JSONL path for normalized private documents.",
    )
    parser.add_argument(
        "--report-path",
        default="outputs/data_ingestion/private_ingestion_report.md",
        help="Output markdown report path.",
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=1,
        help="Minimum word count per accepted record.",
    )
    return parser.parse_args()


def safe_id(value: str) -> str:
    """Build a stable, filesystem-safe identifier."""
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())
    return cleaned.strip("_")


def normalize_text(text: str) -> str:
    """Normalize whitespace in text while preserving content."""
    return " ".join(text.split())


def count_words(text: str) -> int:
    """Count whitespace-delimited words."""
    return len(text.split())


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    """Read text file with explicit encoding fallback chain."""
    decode_errors: list[str] = []
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            decode_errors.append(f"{encoding}: {exc}")
        except OSError as exc:
            raise MalformedFileError(f"Failed reading {path}: {exc}") from exc

    details = " | ".join(decode_errors) if decode_errors else "Unknown decoding failure."
    raise MalformedFileError(
        f"Could not decode text file {path} with utf-8-sig/cp1252/latin-1. Details: {details}"
    )


def chunk_id(relative_path: Path, page_number: int) -> str:
    """Create a deterministic chunk id from relative path and page index."""
    return safe_id(f"{relative_path.as_posix()}-p{page_number:05d}")


def parse_text_file(path: Path, input_dir: Path) -> list[DocumentChunk]:
    """Parse one text document into a single chunk with page_number=1."""
    text, encoding = read_text_with_fallback(path)
    relative = path.relative_to(input_dir)

    chunk = DocumentChunk(
        record_id=chunk_id(relative, page_number=1),
        essay=normalize_text(text),
        metadata={
            "filename": path.name,
            "relative_path": relative.as_posix(),
            "source_format": path.suffix.lower().lstrip("."),
            "encoding": encoding,
            "page_number": 1,
        },
    )
    return [chunk]


def parse_pdf_file(path: Path, input_dir: Path) -> list[DocumentChunk]:
    """Parse one PDF into one chunk per page with explicit page provenance."""
    if PdfReader is None:
        raise MalformedFileError(
            "PDF parsing requires `pypdf` or `PyPDF2` to be installed in this local environment."
        )

    try:
        reader = PdfReader(str(path))
    except Exception as exc:  # pragma: no cover - parser errors vary by backend
        raise MalformedFileError(f"Unable to parse PDF {path}: {exc}") from exc

    if getattr(reader, "is_encrypted", False):
        try:
            reader.decrypt("")
        except Exception as exc:  # pragma: no cover - backend specific
            raise MalformedFileError(f"Encrypted PDF is not readable {path}: {exc}") from exc

    relative = path.relative_to(input_dir)
    chunks: list[DocumentChunk] = []
    total_pages = len(reader.pages)

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover - backend specific
            raise MalformedFileError(
                f"Failed extracting page {page_number} from {path}: {exc}"
            ) from exc

        chunks.append(
            DocumentChunk(
                record_id=chunk_id(relative, page_number=page_number),
                essay=normalize_text(page_text),
                metadata={
                    "filename": path.name,
                    "relative_path": relative.as_posix(),
                    "source_format": "pdf",
                    "encoding": "pdf_text_extraction",
                    "page_number": page_number,
                    "total_pages": total_pages,
                },
            )
        )

    return chunks


def load_chunks(path: Path, input_dir: Path) -> list[DocumentChunk]:
    """Load normalized chunks from one supported file."""
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return parse_text_file(path, input_dir)
    if suffix in PDF_SUFFIXES:
        return parse_pdf_file(path, input_dir)
    return []


def render_report(
    *,
    input_dir: Path,
    output_jsonl: Path,
    files_scanned: int,
    files_supported: int,
    chunks_discovered: int,
    accepted: int,
    rejected: list[Rejection],
    malformed_files: list[Rejection],
    min_words: int,
) -> str:
    """Render ingestion summary report."""
    reason_counts: dict[str, int] = {}
    for item in rejected:
        reason_counts[item.reason] = reason_counts.get(item.reason, 0) + 1

    lines = [
        "# Private Data Ingestion Report",
        "",
        "All processing was local/offline only. No files were uploaded or synced.",
        "",
        f"- Input directory: `{input_dir}`",
        f"- Output JSONL: `{output_jsonl}`",
        f"- Files scanned: `{files_scanned}`",
        f"- Supported files processed: `{files_supported}`",
        f"- Candidate chunks discovered: `{chunks_discovered}`",
        f"- Accepted chunks: `{accepted}`",
        f"- Rejected chunks: `{len(rejected)}`",
        f"- Malformed files: `{len(malformed_files)}`",
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

    lines.extend(["", "## Rejected Chunks (first 50)", ""])
    if rejected:
        for issue in rejected[:50]:
            lines.append(f"- `{issue.source}` [{issue.reason}]: {issue.message}")
        if len(rejected) > 50:
            lines.append(f"- ... {len(rejected) - 50} additional rejected chunks omitted.")
    else:
        lines.append("- None")

    return "\n".join(lines)


def main() -> None:
    """Run offline private document ingestion."""
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_jsonl = Path(args.output_jsonl)
    report_path = Path(args.report_path)

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    all_files = sorted(
        path for path in input_dir.rglob("*") if path.is_file() and not path.name.startswith(".")
    )
    supported_files = [path for path in all_files if path.suffix.lower() in SUPPORTED_SUFFIXES]

    seen_ids: set[str] = set()
    accepted_records: list[dict[str, Any]] = []
    malformed_files: list[Rejection] = []
    rejected: list[Rejection] = []
    chunks_discovered = 0

    for path in supported_files:
        try:
            chunks = load_chunks(path, input_dir)
        except MalformedFileError as exc:
            malformed_files.append(
                Rejection(reason="malformed_file", source=str(path), message=str(exc))
            )
            continue

        chunks_discovered += len(chunks)
        for chunk in chunks:
            if not chunk.essay:
                rejected.append(
                    Rejection(
                        reason="empty_text",
                        source=f"{path}",
                        message="Extracted text is empty after normalization.",
                    )
                )
                continue

            word_count = count_words(chunk.essay)
            if word_count < args.min_words:
                rejected.append(
                    Rejection(
                        reason="text_too_short",
                        source=f"{path}",
                        message=(
                            f"Extracted text has {word_count} words; minimum is {args.min_words}."
                        ),
                    )
                )
                continue

            if chunk.record_id in seen_ids:
                rejected.append(
                    Rejection(
                        reason="duplicate_id",
                        source=f"{path}",
                        message=f"Duplicate chunk ID: {chunk.record_id}",
                    )
                )
                continue

            seen_ids.add(chunk.record_id)
            metadata = dict(chunk.metadata)
            metadata["word_count"] = word_count
            accepted_records.append(
                {
                    "id": chunk.record_id,
                    "essay": chunk.essay,
                    "source": "private_local",
                    "metadata": metadata,
                }
            )

    with output_jsonl.open("w", encoding="utf-8") as handle:
        for record in accepted_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    report_text = render_report(
        input_dir=input_dir,
        output_jsonl=output_jsonl,
        files_scanned=len(all_files),
        files_supported=len(supported_files),
        chunks_discovered=chunks_discovered,
        accepted=len(accepted_records),
        rejected=rejected,
        malformed_files=malformed_files,
        min_words=args.min_words,
    )
    report_path.write_text(report_text, encoding="utf-8")

    print(
        json.dumps(
            {
                "files_scanned": len(all_files),
                "files_supported": len(supported_files),
                "malformed_files": len(malformed_files),
                "chunks_discovered": chunks_discovered,
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
