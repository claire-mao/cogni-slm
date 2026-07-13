from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.validate_environment import REQUIRED_KEYS, validate_environment  # noqa: E402


def _clear_required_env(monkeypatch) -> None:
    for key in REQUIRED_KEYS + (
        "TRUEFOUNDRY_API_KEY",
        "TRUEFOUNDRY_BASE_URL",
        "TEACHER_PROVIDER_MODE",
        "TEACHER_API_KEY",
        "TEACHER_BASE_URL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_validate_environment_missing_file(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    report = validate_environment(env_file=tmp_path / ".env")
    assert report["valid"] is False
    assert report["format_valid"] is False
    assert "not found" in str(report["format_error"]).lower()


def test_validate_environment_with_tfy_only(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TFY_API_KEY=tfy-secret",
                "TFY_BASE_URL=https://gateway.truefoundry.example/v1",
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["valid"] is True
    assert report["missing_keys"] == []
    assert report["empty_keys"] == []
    assert "TFY_API_KEY" in report["present_keys"]
    assert "TFY_BASE_URL" in report["present_keys"]
    assert report["resolved_api_key_variable"] == "TFY_API_KEY"
    assert report["resolved_base_url_variable"] == "TFY_BASE_URL"


def test_validate_environment_invalid_format(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text("TFY_API_KEY=ok\nINVALID LINE\n", encoding="utf-8")

    report = validate_environment(env_file=env_path)
    assert report["valid"] is False
    assert report["format_valid"] is False
    assert "invalid" in str(report["format_error"]).lower()


def test_validate_environment_with_legacy_alias_only(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TRUEFOUNDRY_API_KEY=tfy-secret",
                "TRUEFOUNDRY_BASE_URL=https://gateway.truefoundry.example/v1",
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["valid"] is True
    assert report["missing_keys"] == []
    assert report["empty_keys"] == []
    assert "TRUEFOUNDRY_API_KEY" in report["present_keys"]
    assert "TRUEFOUNDRY_BASE_URL" in report["present_keys"]
    assert report["resolved_api_key_variable"] == "TRUEFOUNDRY_API_KEY"
    assert report["resolved_base_url_variable"] == "TRUEFOUNDRY_BASE_URL"


def test_validate_environment_prefers_tfy_when_both_exist(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TFY_API_KEY=tfy-secret-preferred",
                "TRUEFOUNDRY_API_KEY=tfy-secret-legacy",
                "TFY_BASE_URL=https://gateway-preferred.truefoundry.example/v1",
                "TRUEFOUNDRY_BASE_URL=https://gateway-legacy.truefoundry.example/v1",
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["valid"] is True
    assert report["resolved_api_key_variable"] == "TFY_API_KEY"
    assert report["resolved_base_url_variable"] == "TFY_BASE_URL"


def test_validate_environment_fails_when_both_gateway_names_missing(
    tmp_path: Path, monkeypatch
) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["valid"] is False
    assert "TFY_API_KEY" in report["missing_keys"]
    assert "TFY_BASE_URL" in report["missing_keys"]
    assert report["resolved_api_key_variable"] is None
    assert report["resolved_base_url_variable"] is None


def test_validate_environment_invalid_key_format(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TFY_API_KEY=tfy-secret",
                "TFY_BASE_URL=not-a-url",
                "PRIMARY_TEACHER_MODEL=gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["valid"] is False
    assert sorted(report["invalid_format_keys"]) == sorted(
        ["TFY_BASE_URL", "PRIMARY_TEACHER_MODEL"]
    )


def test_validate_environment_direct_mode(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TEACHER_PROVIDER_MODE=direct",
                "TEACHER_API_KEY=direct-key",
                "TEACHER_BASE_URL=https://openai-compatible.example/v1",
                "PRIMARY_TEACHER_MODEL=gpt-5",
                "VERIFIER_MODEL=claude-opus-4-8",
                "SECONDARY_MODEL=gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["provider_mode"] == "direct"
    assert report["valid"] is True
    assert report["resolved_api_key_variable"] == "TEACHER_API_KEY"
    assert report["resolved_base_url_variable"] == "TEACHER_BASE_URL"
    assert report["invalid_format_keys"] == []
