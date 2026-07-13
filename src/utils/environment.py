"""Environment resolution helpers with backward-compatible aliases."""

from __future__ import annotations

import os
from typing import Final

TFY_API_KEY_VAR: Final[str] = "TFY_API_KEY"
TFY_BASE_URL_VAR: Final[str] = "TFY_BASE_URL"
TRUEFOUNDRY_API_KEY_VAR: Final[str] = "TRUEFOUNDRY_API_KEY"
TRUEFOUNDRY_BASE_URL_VAR: Final[str] = "TRUEFOUNDRY_BASE_URL"
TEACHER_PROVIDER_MODE_VAR: Final[str] = "TEACHER_PROVIDER_MODE"
TEACHER_API_KEY_VAR: Final[str] = "TEACHER_API_KEY"
TEACHER_BASE_URL_VAR: Final[str] = "TEACHER_BASE_URL"


def _resolve_preferred_with_alias(*, preferred: str, alias: str) -> tuple[str | None, str | None]:
    """Resolve preferred env var with fallback alias.

    Precedence is presence-based:
    - if preferred key exists in env (including empty), it is selected
    - else if alias exists, alias is selected
    - else unresolved
    """
    if preferred in os.environ:
        return os.environ.get(preferred), preferred
    if alias in os.environ:
        return os.environ.get(alias), alias
    return None, None


def resolve_truefoundry_api_key() -> tuple[str | None, str | None]:
    """Return (api_key_value, resolved_variable_name)."""
    value, variable = _resolve_preferred_with_alias(
        preferred=TFY_API_KEY_VAR,
        alias=TRUEFOUNDRY_API_KEY_VAR,
    )
    if value is None:
        return None, None
    return value.strip(), variable


def resolve_truefoundry_base_url() -> tuple[str | None, str | None]:
    """Return (base_url_value, resolved_variable_name)."""
    value, variable = _resolve_preferred_with_alias(
        preferred=TFY_BASE_URL_VAR,
        alias=TRUEFOUNDRY_BASE_URL_VAR,
    )
    if value is None:
        return None, None
    return value.strip(), variable


def get_truefoundry_api_key() -> str | None:
    """Return resolved TFY API key value or None."""
    value, _ = resolve_truefoundry_api_key()
    return value


def get_truefoundry_base_url() -> str | None:
    """Return resolved TFY base URL value or None."""
    value, _ = resolve_truefoundry_base_url()
    return value


def get_truefoundry_api_key_variable_name() -> str | None:
    """Return resolved env var name for TFY API key."""
    _, variable = resolve_truefoundry_api_key()
    return variable


def get_truefoundry_base_url_variable_name() -> str | None:
    """Return resolved env var name for TFY base URL."""
    _, variable = resolve_truefoundry_base_url()
    return variable


def get_teacher_provider_mode() -> str:
    """Return provider routing mode.

    Supported values:
    - ``truefoundry`` (default): route via TFY gateway env vars.
    - ``direct``: route via TEACHER_API_KEY/TEACHER_BASE_URL.
    """
    raw = str(os.getenv(TEACHER_PROVIDER_MODE_VAR, "truefoundry")).strip().lower()
    if raw in {"direct", "openai_compatible", "openai-compatible", "openai_compat"}:
        return "direct"
    return "truefoundry"


def resolve_teacher_api_key() -> tuple[str | None, str | None]:
    """Return (api_key_value, resolved_variable_name) for active provider mode."""
    if get_teacher_provider_mode() == "direct":
        if TEACHER_API_KEY_VAR not in os.environ:
            return None, None
        value = os.environ.get(TEACHER_API_KEY_VAR)
        if value is None:
            return None, TEACHER_API_KEY_VAR
        return value.strip(), TEACHER_API_KEY_VAR
    return resolve_truefoundry_api_key()


def resolve_teacher_base_url() -> tuple[str | None, str | None]:
    """Return (base_url_value, resolved_variable_name) for active provider mode."""
    if get_teacher_provider_mode() == "direct":
        if TEACHER_BASE_URL_VAR not in os.environ:
            return None, None
        value = os.environ.get(TEACHER_BASE_URL_VAR)
        if value is None:
            return None, TEACHER_BASE_URL_VAR
        return value.strip(), TEACHER_BASE_URL_VAR
    return resolve_truefoundry_base_url()


def get_teacher_api_key() -> str | None:
    """Return resolved API key for active provider mode."""
    value, _ = resolve_teacher_api_key()
    return value


def get_teacher_base_url() -> str | None:
    """Return resolved base URL for active provider mode."""
    value, _ = resolve_teacher_base_url()
    return value


def get_teacher_api_key_variable_name() -> str | None:
    """Return resolved API key variable name for active provider mode."""
    _, variable = resolve_teacher_api_key()
    return variable


def get_teacher_base_url_variable_name() -> str | None:
    """Return resolved base URL variable name for active provider mode."""
    _, variable = resolve_teacher_base_url()
    return variable
