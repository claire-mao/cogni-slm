"""Shared data models for compliant dataset scraping."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SourcePolicy:
    """Policy contract for a single source domain.

    Attributes:
        name: Human-readable source name.
        base_url: Canonical base URL for the source.
        license_name: License attached to collected material.
        terms_url: Terms of service URL reviewed for this source.
        allows_redistribution: Whether source terms explicitly allow redistribution or
            educational reuse for this project.
        allowed_path_prefixes: Optional URL prefixes further constraining crawl scope.
    """

    name: str
    base_url: str
    license_name: str
    terms_url: str
    allows_redistribution: bool
    allowed_path_prefixes: tuple[str, ...] = ("/",)


@dataclass
class ScrapedRecord:
    """Normalized output from a scraper."""

    id: str
    text: str
    source_url: str
    license: str
    retrieval_date: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    metadata: dict[str, Any] = field(default_factory=dict)
