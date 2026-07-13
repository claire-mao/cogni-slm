from __future__ import annotations

import json
import socket
import ssl
import sys
from pathlib import Path
from urllib import error as urllib_error

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.providers.http import ProviderNetworkError  # noqa: E402
from teacher.test_truefoundry_connection import run_smoke_test  # noqa: E402


def _clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "TFY_API_KEY",
        "TFY_BASE_URL",
        "TRUEFOUNDRY_API_KEY",
        "TRUEFOUNDRY_BASE_URL",
        "PRIMARY_TEACHER_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_run_smoke_test_success_with_tfy_vars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-secret")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("PRIMARY_TEACHER_MODEL", "openai-group/gpt-5")

    captured: dict[str, object] = {}

    def _fake_http_json_post(**kwargs: object) -> tuple[int, dict, str]:
        captured.update(kwargs)
        payload = {
            "choices": [{"message": {"content": '{"status":"ok"}'}}],
            "usage": {"prompt_tokens": 12, "completion_tokens": 3, "total_tokens": 15},
        }
        return 200, payload, json.dumps(payload)

    monkeypatch.setattr(
        "teacher.test_truefoundry_connection.http_json_post",
        _fake_http_json_post,
    )

    output_path = tmp_path / "smoke_test.json"
    result = run_smoke_test(output_path=output_path, load_env=False)
    assert result["success"] is True
    assert result["failure_category"] is None
    assert result["http_status"] == 200
    assert result["model_name"] == "openai-group/gpt-5"
    assert result["token_usage"] == {"input_tokens": 12, "output_tokens": 3, "total_tokens": 15}
    assert captured["url"] == "https://gateway.example/v1/chat/completions"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["Content-Type"] == "application/json"
    assert str(headers["Authorization"]).startswith("Bearer ")
    diagnostics = result["request_diagnostics"]
    assert diagnostics["resolved_base_url"] == "https://gateway.example/v1"
    assert diagnostics["final_request_url"] == "https://gateway.example/v1/chat/completions"
    assert diagnostics["chat_completions_appended"] is True
    assert diagnostics["headers"]["authorization_header_is_bearer"] is True
    assert output_path.exists()


def test_run_smoke_test_success_with_legacy_vars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("TRUEFOUNDRY_API_KEY", "legacy-secret")
    monkeypatch.setenv("TRUEFOUNDRY_BASE_URL", "https://legacy-gateway.example/v1")
    monkeypatch.setenv("PRIMARY_TEACHER_MODEL", "openai-group/gpt-5")

    def _fake_http_json_post(**_: object) -> tuple[int, dict, str]:
        payload = {"choices": [{"message": {"content": '{"status":"ok"}'}}]}
        return 200, payload, json.dumps(payload)

    monkeypatch.setattr(
        "teacher.test_truefoundry_connection.http_json_post",
        _fake_http_json_post,
    )

    output_path = tmp_path / "smoke_test.json"
    result = run_smoke_test(output_path=output_path, load_env=False)
    assert result["success"] is True
    assert result["http_status"] == 200
    assert result["token_usage"] == {
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
    }
    assert result["request_diagnostics"]["resolved_base_url"] == "https://legacy-gateway.example/v1"


def test_run_smoke_test_fails_on_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-secret")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("PRIMARY_TEACHER_MODEL", "openai-group/gpt-5")

    def _fake_http_json_post(**_: object) -> tuple[int, dict, str]:
        payload = {"choices": [{"message": {"content": '{"status":"not_ok"}'}}]}
        return 200, payload, json.dumps(payload)

    monkeypatch.setattr(
        "teacher.test_truefoundry_connection.http_json_post",
        _fake_http_json_post,
    )

    output_path = tmp_path / "smoke_test.json"
    result = run_smoke_test(output_path=output_path, load_env=False)
    assert result["success"] is False
    assert result["failure_category"] == "response_mismatch"
    assert "expected exactly" in str(result["error"]).lower()


def test_run_smoke_test_fails_when_env_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _clear_env(monkeypatch)
    output_path = tmp_path / "smoke_test.json"
    result = run_smoke_test(output_path=output_path, load_env=False)
    assert result["success"] is False
    assert result["failure_category"] == "configuration_error"
    assert "missing tfy_api_key/truefoundry_api_key" in str(result["error"]).lower()
    assert output_path.exists()


@pytest.mark.parametrize(
    ("status", "category"),
    [
        (401, "http_401"),
        (403, "http_403"),
        (404, "http_404"),
        (500, "http_5xx"),
    ],
)
def test_run_smoke_test_http_status_categories(
    status: int,
    category: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-secret")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("PRIMARY_TEACHER_MODEL", "openai-group/gpt-5")

    def _fake_http_json_post(**_: object) -> tuple[int, dict, str]:
        payload = {"error": {"message": "blocked"}}
        return status, payload, json.dumps(payload)

    monkeypatch.setattr(
        "teacher.test_truefoundry_connection.http_json_post",
        _fake_http_json_post,
    )

    result = run_smoke_test(output_path=tmp_path / "smoke_test.json", load_env=False)
    assert result["success"] is False
    assert result["http_status"] == status
    assert result["failure_category"] == category
    assert str(result["error"]).startswith(f"{category}:")


def test_run_smoke_test_json_parse_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-secret")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1")
    monkeypatch.setenv("PRIMARY_TEACHER_MODEL", "openai-group/gpt-5")

    def _fake_http_json_post(**_: object) -> tuple[int, dict, str]:
        payload = {"choices": [{"message": {"content": "not-json"}}]}
        return 200, payload, json.dumps(payload)

    monkeypatch.setattr(
        "teacher.test_truefoundry_connection.http_json_post",
        _fake_http_json_post,
    )

    result = run_smoke_test(output_path=tmp_path / "smoke_test.json", load_env=False)
    assert result["success"] is False
    assert result["failure_category"] == "json_parse_failure"


@pytest.mark.parametrize(
    ("network_exc_factory", "expected_category"),
    [
        (
            lambda: urllib_error.URLError(socket.gaierror(-2, "Name or service not known")),
            "dns_resolution_failure",
        ),
        (
            lambda: urllib_error.URLError(TimeoutError("timed out")),
            "connection_timeout",
        ),
        (
            lambda: urllib_error.URLError(ssl.SSLError("certificate verify failed")),
            "tls_ssl_error",
        ),
    ],
)
def test_run_smoke_test_network_failure_categories(
    network_exc_factory,
    expected_category: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_env(monkeypatch)
    monkeypatch.setenv("TFY_API_KEY", "tfy-secret")
    monkeypatch.setenv("TFY_BASE_URL", "https://gateway.example/v1/")
    monkeypatch.setenv("PRIMARY_TEACHER_MODEL", "openai-group/gpt-5")

    def _fake_http_json_post(**_: object) -> tuple[int, dict, str]:
        provider_exc = ProviderNetworkError(
            provider="truefoundry_smoke_test",
            message="truefoundry_smoke_test network_error",
            retriable=True,
            payload={},
        )
        raise provider_exc from network_exc_factory()

    monkeypatch.setattr(
        "teacher.test_truefoundry_connection.http_json_post",
        _fake_http_json_post,
    )

    result = run_smoke_test(output_path=tmp_path / "smoke_test.json", load_env=False)
    assert result["success"] is False
    assert result["failure_category"] == expected_category
    diagnostics = result["request_diagnostics"]
    assert diagnostics["normalized_base_url"] == "https://gateway.example/v1"
    assert diagnostics["final_request_url"] == "https://gateway.example/v1/chat/completions"
