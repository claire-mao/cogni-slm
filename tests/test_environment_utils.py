from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from utils.environment import (  # noqa: E402
    get_teacher_api_key,
    get_teacher_api_key_variable_name,
    get_teacher_base_url,
    get_teacher_base_url_variable_name,
    get_teacher_provider_mode,
    get_truefoundry_api_key,
    get_truefoundry_api_key_variable_name,
    get_truefoundry_base_url,
    get_truefoundry_base_url_variable_name,
)


def _clear_gateway_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "TFY_API_KEY",
        "TFY_BASE_URL",
        "TRUEFOUNDRY_API_KEY",
        "TRUEFOUNDRY_BASE_URL",
        "TEACHER_PROVIDER_MODE",
        "TEACHER_API_KEY",
        "TEACHER_BASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_env_utils_tfy_only(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_gateway_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-key")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1")

    assert get_truefoundry_api_key() == "tfy-key"
    assert get_truefoundry_base_url() == "https://gateway.example/v1"
    assert get_truefoundry_api_key_variable_name() == "TFY_API_KEY"
    assert get_truefoundry_base_url_variable_name() == "TFY_BASE_URL"


def test_env_utils_legacy_only(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_gateway_env(monkeypatch)
    monkeypatch.setenv("TRUEFOUNDRY_API_KEY", "legacy-key")
    monkeypatch.setenv("TRUEFOUNDRY_BASE_URL", "https://legacy-gateway.example/v1")

    assert get_truefoundry_api_key() == "legacy-key"
    assert get_truefoundry_base_url() == "https://legacy-gateway.example/v1"
    assert get_truefoundry_api_key_variable_name() == "TRUEFOUNDRY_API_KEY"
    assert get_truefoundry_base_url_variable_name() == "TRUEFOUNDRY_BASE_URL"


def test_env_utils_prefers_tfy_when_both_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_gateway_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-key")
    monkeypatch.setenv("TRUEFOUNDRY_API_KEY", "legacy-key")
    monkeypatch.setenv("TFY_BASE_URL", "https://preferred-gateway.example/v1")
    monkeypatch.setenv("TRUEFOUNDRY_BASE_URL", "https://legacy-gateway.example/v1")

    assert get_truefoundry_api_key() == "tfy-key"
    assert get_truefoundry_base_url() == "https://preferred-gateway.example/v1"
    assert get_truefoundry_api_key_variable_name() == "TFY_API_KEY"
    assert get_truefoundry_base_url_variable_name() == "TFY_BASE_URL"


def test_env_utils_unset_when_neither_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_gateway_env(monkeypatch)
    assert get_truefoundry_api_key() is None
    assert get_truefoundry_base_url() is None
    assert get_truefoundry_api_key_variable_name() is None
    assert get_truefoundry_base_url_variable_name() is None
    assert get_teacher_provider_mode() == "truefoundry"
    assert get_teacher_api_key() is None
    assert get_teacher_base_url() is None
    assert get_teacher_api_key_variable_name() is None
    assert get_teacher_base_url_variable_name() is None


def test_env_utils_direct_mode_uses_teacher_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_gateway_env(monkeypatch)
    monkeypatch.setenv("TEACHER_PROVIDER_MODE", "direct")
    monkeypatch.setenv("TEACHER_API_KEY", "direct-key")
    monkeypatch.setenv("TEACHER_BASE_URL", "https://openai-compatible.example/v1")
    # Ensure TFY vars do not leak into direct mode resolution.
    monkeypatch.setenv("TFY_API_KEY", "tfy-key")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1")

    assert get_teacher_provider_mode() == "direct"
    assert get_teacher_api_key() == "direct-key"
    assert get_teacher_base_url() == "https://openai-compatible.example/v1"
    assert get_teacher_api_key_variable_name() == "TEACHER_API_KEY"
    assert get_teacher_base_url_variable_name() == "TEACHER_BASE_URL"
