from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.validate_environment import REQUIRED_KEYS, validate_environment  # noqa: E402


def _clear_required_env(monkeypatch) -> None:
    for key in REQUIRED_KEYS:
        monkeypatch.delenv(key, raising=False)


def test_validate_environment_missing_file(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    report = validate_environment(env_file=tmp_path / ".env")
    assert report["valid"] is False
    assert report["format_valid"] is False
    assert "not found" in str(report["format_error"]).lower()


def test_validate_environment_valid_file(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text(
        "\n".join(
            [
                "OPENAI_API_KEY=sk-openai",
                "ANTHROPIC_API_KEY=sk-anthropic",
                "DEEPSEEK_API_KEY=sk-deepseek",
                "GOOGLE_API_KEY=sk-google",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = validate_environment(env_file=env_path)
    assert report["valid"] is True
    assert report["missing_keys"] == []
    assert report["empty_keys"] == []
    assert sorted(report["present_keys"]) == sorted(REQUIRED_KEYS)


def test_validate_environment_invalid_format(tmp_path: Path, monkeypatch) -> None:
    _clear_required_env(monkeypatch)
    env_path = tmp_path / ".env"
    env_path.write_text("OPENAI_API_KEY=ok\nINVALID LINE\n", encoding="utf-8")

    report = validate_environment(env_file=env_path)
    assert report["valid"] is False
    assert report["format_valid"] is False
    assert "invalid" in str(report["format_error"]).lower()
