"""Provider configuration loading and validation utilities.

This module reads provider credentials from `.env` (or another env file),
validates required keys for selected providers, and returns a structured
validation report without making network calls.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

_ENV_PATTERN = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")

_PROVIDER_ALIASES: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "google",
    "gemini": "google",
    "deepseek": "deepseek",
    "openrouter": "openrouter",
    "openrouter_compatible": "openrouter",
}


def _normalize_provider_name(value: str) -> str:
    key = value.strip().lower()
    if key in _PROVIDER_ALIASES:
        return _PROVIDER_ALIASES[key]
    raise ValueError(
        f"Unsupported provider '{value}'. "
        "Expected one of: openai, anthropic, google, gemini, deepseek, openrouter."
    )


def _parse_env_value(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.startswith("'") and text.endswith("'") and len(text) >= 2:
        return text[1:-1]
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        inner = text[1:-1]
        inner = inner.replace(r"\n", "\n").replace(r"\t", "\t").replace(r"\\", "\\")
        return inner
    if " #" in text:
        text = text.split(" #", maxsplit=1)[0].strip()
    return text


def load_env_file(
    path: Path,
    *,
    override: bool = False,
) -> dict[str, str]:
    """Load KEY=VALUE pairs from an env file into os.environ."""
    if not path.exists():
        return {}

    loaded: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            match = _ENV_PATTERN.match(raw)
            if not match:
                raise ValueError(f"Invalid env line at {path}:{line_number}")
            key, value = match.group(1), _parse_env_value(match.group(2))
            loaded[key] = value
            if override:
                os.environ[key] = value
            else:
                os.environ.setdefault(key, value)
    return loaded


def _read_provider_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Provider config must be JSON object: {path}")
    return payload


def _collect_missing(
    *,
    provider_cfg: dict[str, Any],
) -> tuple[list[str], list[list[str]], list[str]]:
    required_all = provider_cfg.get("required_env_all")
    required_any = provider_cfg.get("required_env_any")
    optional_env = provider_cfg.get("optional_env")

    all_keys = [str(item) for item in required_all] if isinstance(required_all, list) else []
    any_groups: list[list[str]] = []
    if isinstance(required_any, list):
        for group in required_any:
            if isinstance(group, list):
                keys = [str(item) for item in group if str(item).strip()]
                if keys:
                    any_groups.append(keys)
    optional_keys = [str(item) for item in optional_env] if isinstance(optional_env, list) else []
    return all_keys, any_groups, optional_keys


def validate_provider_configuration(
    *,
    required_providers: list[str],
    config_path: Path = Path("configs/providers/providers_v1.json"),
    env_file: Path = Path(".env"),
    strict: bool = False,
    load_env: bool = True,
    override_env: bool = False,
) -> dict[str, Any]:
    """Validate provider credentials for a set of providers."""
    if not config_path.exists():
        raise FileNotFoundError(f"Provider config not found: {config_path}")

    loaded_env: dict[str, str] = {}
    if load_env:
        loaded_env = load_env_file(env_file, override=override_env)

    payload = _read_provider_config(config_path)
    providers = payload.get("providers")
    if not isinstance(providers, dict):
        raise ValueError(f"Provider config missing providers map: {config_path}")

    normalized_required: list[str] = []
    for provider in required_providers:
        normalized = _normalize_provider_name(provider)
        if normalized not in normalized_required:
            normalized_required.append(normalized)

    checks: dict[str, Any] = {}
    invalid: list[str] = []

    for provider_name in normalized_required:
        raw_cfg = providers.get(provider_name)
        if not isinstance(raw_cfg, dict):
            checks[provider_name] = {
                "valid": False,
                "error": "missing_provider_config",
                "required_env_all": [],
                "required_env_any": [],
                "optional_env": [],
                "present_keys": [],
                "missing_env_all": [],
                "missing_env_any_groups": [],
            }
            invalid.append(provider_name)
            continue

        required_all, required_any, optional_env = _collect_missing(provider_cfg=raw_cfg)
        present_keys: list[str] = []
        for key in required_all + [item for group in required_any for item in group] + optional_env:
            if os.getenv(key):
                present_keys.append(key)
        present_keys = sorted(set(present_keys))

        missing_all = [key for key in required_all if not os.getenv(key)]
        missing_any_groups = [
            group for group in required_any if not any(os.getenv(k) for k in group)
        ]
        is_valid = not missing_all and not missing_any_groups
        if not is_valid:
            invalid.append(provider_name)

        checks[provider_name] = {
            "valid": is_valid,
            "required_env_all": required_all,
            "required_env_any": required_any,
            "optional_env": optional_env,
            "present_keys": present_keys,
            "missing_env_all": missing_all,
            "missing_env_any_groups": missing_any_groups,
        }

    report = {
        "config_path": str(config_path),
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "env_keys_loaded_count": len(loaded_env),
        "required_providers_input": required_providers,
        "required_providers_normalized": normalized_required,
        "providers": checks,
        "valid": len(invalid) == 0,
        "invalid_providers": invalid,
    }

    if strict and invalid:
        details = ", ".join(sorted(invalid))
        raise ValueError(
            "Provider configuration validation failed for: "
            f"{details}. Populate required keys in {env_file}."
        )
    return report


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for provider-config validation."""
    parser = argparse.ArgumentParser(description="Validate provider configuration from .env.")
    parser.add_argument(
        "--providers",
        default="openai,anthropic,google,deepseek,openrouter",
        help="Comma-separated provider list.",
    )
    parser.add_argument("--config-path", default="configs/providers/providers_v1.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--override-env", action="store_true")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    required = [item.strip() for item in str(args.providers).split(",") if item.strip()]
    report = validate_provider_configuration(
        required_providers=required,
        config_path=Path(args.config_path),
        env_file=Path(args.env_file),
        strict=bool(args.strict),
        load_env=True,
        override_env=bool(args.override_env),
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
