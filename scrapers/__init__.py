"""Compliant scraping framework for openly reusable educational sources."""

from .base import BaseScraper, ScrapeRunSummary
from .html_scraper import StaticHTMLScraper
from .json_scraper import JSONListScraper
from .storage import write_jsonl
from .types import ScrapedRecord, SourcePolicy

__all__ = [
    "BaseScraper",
    "JSONListScraper",
    "ScrapeRunSummary",
    "ScrapedRecord",
    "SourcePolicy",
    "StaticHTMLScraper",
    "write_jsonl",
]
