"""Path helpers shared by pipeline modules."""

from __future__ import annotations

from pathlib import Path


def repo_root(start: str | Path | None = None) -> Path:
    """Infer repository root by walking up to the directory containing pyproject.toml."""
    current = Path(start) if start is not None else Path(__file__)
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists():
            return candidate
    return Path.cwd()


def reports_root(start: str | Path | None = None) -> Path:
    """Return canonical reports root path."""
    return repo_root(start) / "docs" / "reports"


def outputs_root(start: str | Path | None = None) -> Path:
    """Return outputs root path."""
    return repo_root(start) / "outputs"
