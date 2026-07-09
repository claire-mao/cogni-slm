"""Storage helpers for scraped records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TextIO

from .types import ScrapedRecord


def write_jsonl(records: list[ScrapedRecord], output_path: Path) -> None:
    """Write records to JSONL with required provenance fields."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            _write_record(handle, record)


def _write_record(handle: TextIO, record: ScrapedRecord) -> None:
    payload = {
        "id": record.id,
        "text": record.text,
        "source_url": record.source_url,
        "license": record.license,
        "retrieval_date": record.retrieval_date,
        "metadata": record.metadata,
    }
    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
