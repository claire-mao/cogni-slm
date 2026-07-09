"""HTML scraper utilities built on top of BaseScraper."""

from __future__ import annotations

from collections.abc import Iterable
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

from .base import BaseScraper
from .types import ScrapedRecord, SourcePolicy


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        normalized = " ".join(data.split())
        if normalized:
            self._parts.append(normalized)

    def text(self) -> str:
        return " ".join(self._parts).strip()


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr_map = {key: value for key, value in attrs}
        href = attr_map.get("href")
        if href:
            self.hrefs.append(href)


class StaticHTMLScraper(BaseScraper):
    """Scraper for static index pages with article links.

    This implementation:
    - fetches one or more index pages
    - extracts links
    - keeps only in-domain links under policy path prefixes
    - fetches each article page and emits one text record per URL
    """

    def __init__(
        self,
        policy: SourcePolicy,
        index_urls: list[str],
        user_agent: str = "CogniDatasetBot/1.0 (+educational-research)",
        timeout_seconds: int = 20,
    ) -> None:
        super().__init__(policy=policy, user_agent=user_agent, timeout_seconds=timeout_seconds)
        self.index_urls = index_urls

    def discover_urls(self) -> Iterable[str]:
        seen: set[str] = set()
        discovered: list[str] = []

        for index_url in self.index_urls:
            normalized_index = self._normalize_url(index_url)
            if not self._is_url_allowed(normalized_index):
                continue

            payload = self._fetch_text(normalized_index)
            parser = _LinkExtractor()
            parser.feed(payload)
            for href in parser.hrefs:
                absolute = urljoin(normalized_index, href)
                parsed = urlparse(absolute)
                if parsed.fragment:
                    absolute = absolute.split("#", maxsplit=1)[0]
                if absolute in seen:
                    continue
                if self._is_url_allowed(absolute):
                    seen.add(absolute)
                    discovered.append(absolute)

        return discovered

    def parse(self, url: str, payload: str) -> Iterable[ScrapedRecord]:
        extractor = _TextExtractor()
        extractor.feed(payload)
        text = extractor.text()
        if not text:
            return []

        record_id = f"{self.policy.name.lower().replace(' ', '_')}::{url}"
        return [
            ScrapedRecord(
                id=record_id,
                text=text,
                source_url=url,
                license=self.policy.license_name,
                metadata={"source_type": "html"},
            )
        ]
