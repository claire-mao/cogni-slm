"""Validate provider environment configuration for live teacher runs.

Checks:
- `.env` presence
- `.env` parse format
- required key presence for pilot providers

This validator never prints secret values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .provider_config import load_env_file

REQUIRED_KEYS: tuple[str, ...] = (
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "GOOGLE_API_KEY",
)


def validate_environment(
    *,
    env_file: Path,
    required_keys: tuple[str, ...] = REQUIRED_KEYS,
) -> dict[str, Any]:
    """Validate `.env` file and required key presence."""
    report: dict[str, Any] = {
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "required_keys": list(required_keys),
        "missing_keys": [],
        "empty_keys": [],
        "present_keys": [],
        "format_valid": True,
        "format_error": None,
        "valid": False,
    }

    if not env_file.exists() or not env_file.is_file():
        report["format_valid"] = False
        report["format_error"] = f"Environment file not found: {env_file}"
        return report

    try:
        load_env_file(env_file, override=False)
    except Exception as exc:
        report["format_valid"] = False
        report["format_error"] = f"Invalid .env format: {type(exc).__name__}: {exc}"
        return report

    missing_keys: list[str] = []
    empty_keys: list[str] = []
    present_keys: list[str] = []
    for key in required_keys:
        value = os.getenv(key)
        if value is None:
            missing_keys.append(key)
            continue
        if not str(value).strip():
            empty_keys.append(key)
            continue
        present_keys.append(key)

    report["missing_keys"] = missing_keys
    report["empty_keys"] = empty_keys
    report["present_keys"] = sorted(present_keys)
    report["valid"] = bool(report["format_valid"] and not missing_keys and not empty_keys)
    return report


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Validate live-pilot environment configuration.")
    parser.add_argument("--env-file", default=".env", help="Path to env file to validate.")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    report = validate_environment(env_file=Path(args.env_file))
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))

    if not report["valid"]:
        lines: list[str] = ["Environment validation failed."]
        if report.get("format_error"):
            lines.append(str(report["format_error"]))
        missing = report.get("missing_keys") or []
        empty = report.get("empty_keys") or []
        if missing:
            lines.append("Missing required keys: " + ", ".join(str(item) for item in missing))
        if empty:
            lines.append("Empty required keys: " + ", ".join(str(item) for item in empty))
        sys.stderr.write("\n".join(lines) + "\n")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
