"""Reusable base classes for compliant scraping."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

from .types import ScrapedRecord, SourcePolicy

BLOCKED_DOMAINS = {
    "collegeboard.org",
    "www.collegeboard.org",
    "apcentral.collegeboard.org",
}


@dataclass
class ScrapeRunSummary:
    """Summarizes scrape outcomes for traceability."""

    source_name: str
    attempted_urls: int = 0
    fetched_urls: int = 0
    skipped_urls: int = 0
    records_emitted: int = 0
    errors: list[str] = field(default_factory=list)


class BaseScraper(ABC):
    """Abstract scraper with compliance checks.

    This class enforces:
    - explicit redistribution permission (`SourcePolicy.allows_redistribution`)
    - robots.txt checks before requesting content
    - explicit block on College Board domains
    """

    def __init__(
        self,
        policy: SourcePolicy,
        user_agent: str = "CogniDatasetBot/1.0 (+educational-research)",
        timeout_seconds: int = 20,
    ) -> None:
        self.policy = policy
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self._robots_cache: dict[str, RobotFileParser] = {}

    @abstractmethod
    def discover_urls(self) -> Iterable[str]:
        """Return candidate URLs to scrape."""

    @abstractmethod
    def parse(self, url: str, payload: str) -> Iterable[ScrapedRecord]:
        """Parse a fetched payload into normalized records."""

    def run(self) -> tuple[list[ScrapedRecord], ScrapeRunSummary]:
        """Execute the scraper and return records plus run summary."""
        summary = ScrapeRunSummary(source_name=self.policy.name)

        if not self.policy.allows_redistribution:
            raise PermissionError(
                f"Source '{self.policy.name}' is not approved for redistribution. "
                f"Review terms: {self.policy.terms_url}"
            )

        records: list[ScrapedRecord] = []
        for candidate_url in self.discover_urls():
            summary.attempted_urls += 1
            normalized_url = self._normalize_url(candidate_url)
            if not self._is_url_allowed(normalized_url):
                summary.skipped_urls += 1
                continue
            try:
                payload = self._fetch_text(normalized_url)
                summary.fetched_urls += 1
                parsed = list(self.parse(normalized_url, payload))
                records.extend(self._enrich_record(record, normalized_url) for record in parsed)
                summary.records_emitted += len(parsed)
            except (HTTPError, URLError, ValueError) as exc:
                summary.errors.append(f"{normalized_url}: {exc}")

        return records, summary

    def _normalize_url(self, url: str) -> str:
        return urljoin(self.policy.base_url, url)

    def _fetch_text(self, url: str) -> str:
        request = Request(url=url, headers={"User-Agent": self.user_agent})
        with urlopen(request, timeout=self.timeout_seconds) as response:
            content_type = response.headers.get("Content-Type", "")
            charset = self._extract_charset(content_type)
            return response.read().decode(charset)

    @staticmethod
    def _extract_charset(content_type: str) -> str:
        parts = [part.strip() for part in content_type.split(";")]
        for part in parts:
            if part.lower().startswith("charset="):
                return part.split("=", maxsplit=1)[1].strip() or "utf-8"
        return "utf-8"

    def _is_url_allowed(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.hostname in BLOCKED_DOMAINS:
            return False

        base_domain = urlparse(self.policy.base_url).hostname
        if parsed.hostname != base_domain:
            return False

        if not any(parsed.path.startswith(prefix) for prefix in self.policy.allowed_path_prefixes):
            return False

        parser = self._robots_for(parsed.scheme, parsed.netloc)
        return parser.can_fetch(self.user_agent, url)

    def _robots_for(self, scheme: str, netloc: str) -> RobotFileParser:
        robots_url = f"{scheme}://{netloc}/robots.txt"
        parser = self._robots_cache.get(robots_url)
        if parser is not None:
            return parser

        parser = RobotFileParser()
        parser.set_url(robots_url)
        try:
            parser.read()
        except (HTTPError, URLError):
            # Conservative default: deny crawling when robots.txt cannot be read.
            parser.parse(["User-agent: *", "Disallow: /"])
        self._robots_cache[robots_url] = parser
        return parser

    def _enrich_record(self, record: ScrapedRecord, source_url: str) -> ScrapedRecord:
        """Ensure required compliance metadata fields are always populated."""
        if not record.source_url:
            record.source_url = source_url
        if not record.license:
            record.license = self.policy.license_name
        if "terms_url" not in record.metadata:
            record.metadata["terms_url"] = self.policy.terms_url
        return record
