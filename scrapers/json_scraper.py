"""JSON endpoint scraper utilities."""

from __future__ import annotations

import json
from collections.abc import Iterable

from .base import BaseScraper
from .types import ScrapedRecord, SourcePolicy


class JSONListScraper(BaseScraper):
    """Reusable scraper for endpoints returning a JSON list of objects."""

    def __init__(
        self,
        policy: SourcePolicy,
        urls: list[str],
        text_field: str,
        id_field: str,
        user_agent: str = "CogniDatasetBot/1.0 (+educational-research)",
        timeout_seconds: int = 20,
    ) -> None:
        super().__init__(policy=policy, user_agent=user_agent, timeout_seconds=timeout_seconds)
        self.urls = urls
        self.text_field = text_field
        self.id_field = id_field

    def discover_urls(self) -> Iterable[str]:
        return list(self.urls)

    def parse(self, url: str, payload: str) -> Iterable[ScrapedRecord]:
        parsed = json.loads(payload)
        if not isinstance(parsed, list):
            raise ValueError(f"Expected JSON list at {url}, got: {type(parsed).__name__}")

        records: list[ScrapedRecord] = []
        for idx, row in enumerate(parsed):
            if not isinstance(row, dict):
                continue

            text = row.get(self.text_field)
            identifier = row.get(self.id_field, f"{url}::{idx}")
            if not isinstance(text, str) or not text.strip():
                continue

            records.append(
                ScrapedRecord(
                    id=str(identifier),
                    text=text.strip(),
                    source_url=url,
                    license=self.policy.license_name,
                    metadata={"source_type": "json", "row_index": idx},
                )
            )

        return records
