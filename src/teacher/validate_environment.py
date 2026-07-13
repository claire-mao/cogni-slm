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
from urllib.parse import urlparse

from utils.environment import (
    TEACHER_API_KEY_VAR,
    TEACHER_BASE_URL_VAR,
    TFY_API_KEY_VAR,
    TFY_BASE_URL_VAR,
    get_teacher_api_key,
    get_teacher_api_key_variable_name,
    get_teacher_base_url,
    get_teacher_base_url_variable_name,
    get_teacher_provider_mode,
)

from .provider_config import load_env_file

REQUIRED_KEYS: tuple[str, ...] = (
    TFY_API_KEY_VAR,
    TFY_BASE_URL_VAR,
    "PRIMARY_TEACHER_MODEL",
    "VERIFIER_MODEL",
    "SECONDARY_MODEL",
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
        "required_keys": [],
        "provider_mode": "truefoundry",
        "missing_keys": [],
        "empty_keys": [],
        "present_keys": [],
        "invalid_format_keys": [],
        "resolved_api_key_variable": None,
        "resolved_base_url_variable": None,
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

    provider_mode = get_teacher_provider_mode()
    report["provider_mode"] = provider_mode

    provider_mode = str(report["provider_mode"])
    gateway_key_name = TEACHER_API_KEY_VAR if provider_mode == "direct" else TFY_API_KEY_VAR
    gateway_url_name = TEACHER_BASE_URL_VAR if provider_mode == "direct" else TFY_BASE_URL_VAR
    report["required_keys"] = [
        gateway_key_name,
        gateway_url_name,
        *[key for key in required_keys if key not in {TFY_API_KEY_VAR, TFY_BASE_URL_VAR}],
    ]

    missing_keys: list[str] = []
    empty_keys: list[str] = []
    present_keys: list[str] = []

    api_key = get_teacher_api_key()
    api_key_variable = get_teacher_api_key_variable_name()
    base_url = get_teacher_base_url()
    base_url_variable = get_teacher_base_url_variable_name()

    report["resolved_api_key_variable"] = api_key_variable
    report["resolved_base_url_variable"] = base_url_variable

    if api_key_variable is None:
        missing_keys.append(gateway_key_name)
    elif not api_key:
        empty_keys.append(api_key_variable)
    else:
        present_keys.append(api_key_variable)

    if base_url_variable is None:
        missing_keys.append(gateway_url_name)
    elif not base_url:
        empty_keys.append(base_url_variable)
    else:
        present_keys.append(base_url_variable)

    for key in required_keys:
        if key in {TFY_API_KEY_VAR, TFY_BASE_URL_VAR, TEACHER_API_KEY_VAR, TEACHER_BASE_URL_VAR}:
            continue
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
    invalid_format_keys: list[str] = []

    if base_url:
        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            invalid_format_keys.append(base_url_variable or TFY_BASE_URL_VAR)

    for model_key in ("PRIMARY_TEACHER_MODEL", "VERIFIER_MODEL", "SECONDARY_MODEL"):
        value = os.getenv(model_key, "").strip()
        if not value:
            continue
        if provider_mode == "truefoundry":
            # Gateway routes are expected to use namespaced virtual model IDs.
            if "/" not in value or value.startswith("/") or value.endswith("/"):
                invalid_format_keys.append(model_key)

    report["invalid_format_keys"] = sorted(set(invalid_format_keys))
    report["valid"] = bool(
        report["format_valid"]
        and not missing_keys
        and not empty_keys
        and not report["invalid_format_keys"]
    )
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
        invalid = report.get("invalid_format_keys") or []
        if invalid:
            lines.append("Invalid key format: " + ", ".join(str(item) for item in invalid))
        sys.stderr.write("\n".join(lines) + "\n")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
