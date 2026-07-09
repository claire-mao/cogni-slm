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
                "OPENAI_API_KEY=abc123",
                'GOOGLE_API_KEY="g-key"',
                "export OPENROUTER_HTTP_REFERER=https://example.org",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_HTTP_REFERER", raising=False)

    loaded = load_env_file(env_path)
    assert loaded["OPENAI_API_KEY"] == "abc123"
    assert loaded["GOOGLE_API_KEY"] == "g-key"
    assert loaded["OPENROUTER_HTTP_REFERER"] == "https://example.org"


def test_validate_provider_configuration_any_of(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "google": {
                        "required_env_all": [],
                        "required_env_any": [["GEMINI_API_KEY", "GOOGLE_API_KEY"]],
                        "optional_env": [],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    env_path = tmp_path / ".env"
    env_path.write_text("GOOGLE_API_KEY=test-google-key\n", encoding="utf-8")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    report = validate_provider_configuration(
        required_providers=["google"],
        config_path=config_path,
        env_file=env_path,
        strict=True,
        load_env=True,
    )
    assert report["valid"] is True
    assert report["providers"]["google"]["valid"] is True


def test_validate_provider_configuration_strict_raises(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "providers_v1.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "openai": {
                        "required_env_all": ["OPENAI_API_KEY"],
                        "required_env_any": [],
                        "optional_env": [],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    env_path = tmp_path / ".env"
    env_path.write_text("", encoding="utf-8")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError):
        validate_provider_configuration(
            required_providers=["openai"],
            config_path=config_path,
            env_file=env_path,
            strict=True,
            load_env=True,
        )
