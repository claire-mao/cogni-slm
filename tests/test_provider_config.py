from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.provider_config import load_env_file, validate_provider_configuration


def test_load_env_file_parses_values(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TFY_API_KEY=tfy-key",
                'PRIMARY_TEACHER_MODEL="openai-group/gpt-5"',
                "export TFY_BASE_URL=https://gateway.example/v1",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TFY_API_KEY", raising=False)
    monkeypatch.delenv("PRIMARY_TEACHER_MODEL", raising=False)
    monkeypatch.delenv("TFY_BASE_URL", raising=False)

    loaded = load_env_file(env_path)
    assert loaded["TFY_API_KEY"] == "tfy-key"
    assert loaded["PRIMARY_TEACHER_MODEL"] == "openai-group/gpt-5"
    assert loaded["TFY_BASE_URL"] == "https://gateway.example/v1"


def _write_gateway_provider_config(config_path: Path) -> None:
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "openai": {
                        "required_env_all": [
                            "PRIMARY_TEACHER_MODEL",
                            "VERIFIER_MODEL",
                            "SECONDARY_MODEL",
                        ],
                        "required_env_any": [
                            ["TFY_API_KEY", "TRUEFOUNDRY_API_KEY"],
                            ["TFY_BASE_URL", "TRUEFOUNDRY_BASE_URL"],
                        ],
                        "optional_env": [],
                    }
                }
            }
        ),
        encoding="utf-8",
    )


def test_validate_provider_configuration_with_tfy_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    _write_gateway_provider_config(config_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TFY_API_KEY=tfy-key",
                "TFY_BASE_URL=https://gateway.example/v1",
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TFY_API_KEY", raising=False)
    monkeypatch.delenv("TFY_BASE_URL", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_API_KEY", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_BASE_URL", raising=False)
    monkeypatch.delenv("PRIMARY_TEACHER_MODEL", raising=False)
    monkeypatch.delenv("VERIFIER_MODEL", raising=False)
    monkeypatch.delenv("SECONDARY_MODEL", raising=False)

    report = validate_provider_configuration(
        required_providers=["openai"],
        config_path=config_path,
        env_file=env_path,
        strict=True,
        load_env=True,
    )
    assert report["valid"] is True
    assert report["providers"]["openai"]["valid"] is True


def test_validate_provider_configuration_with_legacy_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    _write_gateway_provider_config(config_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TRUEFOUNDRY_API_KEY=tfy-key",
                "TRUEFOUNDRY_BASE_URL=https://gateway.example/v1",
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TFY_API_KEY", raising=False)
    monkeypatch.delenv("TFY_BASE_URL", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_API_KEY", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_BASE_URL", raising=False)
    monkeypatch.delenv("PRIMARY_TEACHER_MODEL", raising=False)
    monkeypatch.delenv("VERIFIER_MODEL", raising=False)
    monkeypatch.delenv("SECONDARY_MODEL", raising=False)

    report = validate_provider_configuration(
        required_providers=["openai"],
        config_path=config_path,
        env_file=env_path,
        strict=True,
        load_env=True,
    )
    assert report["valid"] is True
    assert report["providers"]["openai"]["valid"] is True


def test_validate_provider_configuration_prefers_tfy_when_both_exist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    _write_gateway_provider_config(config_path)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "TFY_API_KEY=tfy-preferred",
                "TRUEFOUNDRY_API_KEY=tfy-legacy",
                "TFY_BASE_URL=https://gateway-preferred.example/v1",
                "TRUEFOUNDRY_BASE_URL=https://gateway-legacy.example/v1",
                "PRIMARY_TEACHER_MODEL=openai-group/gpt-5",
                "VERIFIER_MODEL=claude-group/claude-opus-4-8",
                "SECONDARY_MODEL=gemini-group/gemini-3.1-pro",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("TFY_API_KEY", raising=False)
    monkeypatch.delenv("TFY_BASE_URL", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_API_KEY", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_BASE_URL", raising=False)
    monkeypatch.delenv("PRIMARY_TEACHER_MODEL", raising=False)
    monkeypatch.delenv("VERIFIER_MODEL", raising=False)
    monkeypatch.delenv("SECONDARY_MODEL", raising=False)

    report = validate_provider_configuration(
        required_providers=["openai"],
        config_path=config_path,
        env_file=env_path,
        strict=True,
        load_env=True,
    )
    assert report["valid"] is True
    assert report["providers"]["openai"]["valid"] is True
    assert "TFY_API_KEY" in report["providers"]["openai"]["present_keys"]
    assert "TFY_BASE_URL" in report["providers"]["openai"]["present_keys"]


def test_validate_provider_configuration_fails_when_both_gateway_names_missing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    _write_gateway_provider_config(config_path)
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
    monkeypatch.delenv("TFY_API_KEY", raising=False)
    monkeypatch.delenv("TFY_BASE_URL", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_API_KEY", raising=False)
    monkeypatch.delenv("TRUEFOUNDRY_BASE_URL", raising=False)
    monkeypatch.delenv("PRIMARY_TEACHER_MODEL", raising=False)
    monkeypatch.delenv("VERIFIER_MODEL", raising=False)
    monkeypatch.delenv("SECONDARY_MODEL", raising=False)

    with pytest.raises(ValueError):
        validate_provider_configuration(
            required_providers=["openai"],
            config_path=config_path,
            env_file=env_path,
            strict=True,
            load_env=True,
        )


def test_validate_provider_configuration_direct_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    _write_gateway_provider_config(config_path)
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
    for key in (
        "TFY_API_KEY",
        "TFY_BASE_URL",
        "TRUEFOUNDRY_API_KEY",
        "TRUEFOUNDRY_BASE_URL",
        "TEACHER_PROVIDER_MODE",
        "TEACHER_API_KEY",
        "TEACHER_BASE_URL",
        "PRIMARY_TEACHER_MODEL",
        "VERIFIER_MODEL",
        "SECONDARY_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)

    report = validate_provider_configuration(
        required_providers=["openai"],
        config_path=config_path,
        env_file=env_path,
        strict=True,
        load_env=True,
    )
    assert report["valid"] is True
    assert report["provider_mode"] == "direct"
    openai_check = report["providers"]["openai"]
    assert openai_check["valid"] is True
    assert ["TEACHER_API_KEY"] in openai_check["required_env_any"]
    assert ["TEACHER_BASE_URL"] in openai_check["required_env_any"]
