"""Approved scraping policies for openly reusable sources.

Only add sources that explicitly permit redistribution or educational reuse.
"""

from __future__ import annotations

from .types import SourcePolicy

EXAMPLE_OPEN_POLICY = SourcePolicy(
    name="Example Open Education Source",
    base_url="https://example.org",
    license_name="CC BY 4.0",
    terms_url="https://example.org/terms",
    allows_redistribution=True,
    allowed_path_prefixes=("/education/", "/resources/"),
)


__all__ = ["EXAMPLE_OPEN_POLICY"]
