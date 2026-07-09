"""Shared utility helpers for the evaluation harness."""

from __future__ import annotations

from typing import Any


def normalize_text(value: Any) -> str:
    """Normalize value into a single-space stripped string."""
    return " ".join(str(value or "").split()).strip()


def parse_finite_float(value: Any) -> float | None:
    """Parse a finite float from mixed input values."""
    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        parsed = float(value)
        if parsed == parsed and parsed not in (float("inf"), float("-inf")):
            return parsed
        return None

    raw = normalize_text(value)
    if not raw:
        return None

    try:
        parsed = float(raw)
    except ValueError:
        return None

    if parsed == parsed and parsed not in (float("inf"), float("-inf")):
        return parsed
    return None
