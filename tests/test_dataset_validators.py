from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "datasets" / "processing" / "validators.py"
SPEC = importlib.util.spec_from_file_location("validators_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

ValidatorConfig = MODULE.ValidatorConfig
validate_jsonl_file = MODULE.validate_jsonl_file


def test_record_level_checks(tmp_path: Path) -> None:
    path = tmp_path / "sample.jsonl"
    rows = [
        {
            "id": "a",
            "text": " ",
            "label": 1.0,
            "source": "x",
            "task": "essay_scoring",
            "prompt": "p",
            "metadata": {},
        },
        {
            "id": "a",
            "text": "short text",
            "label": "bad",
            "source": "x",
            "task": "essay_scoring",
            "prompt": "p",
            "metadata": {},
        },
        {
            "id": "c",
            "text": "short text",
            "label": 99,
            "source": "x",
            "task": "essay_scoring",
            "prompt": "p",
            "metadata": {},
        },
        {
            "id": "d",
            "text": "valid text with enough words " * 30,
            "label": None,
            "source": "x",
            "task": "essay_scoring",
            "prompt": "p",
            "metadata": {},
        },
    ]
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    cfg = ValidatorConfig(label_min=0, label_max=10, min_word_count=3, max_word_count=50)
    result = validate_jsonl_file(path, cfg)

    assert result.total_records == 4
    assert result.issue_counts.get("whitespace_only_essay", 0) >= 1
    assert result.issue_counts.get("empty_text", 0) >= 0
    assert result.issue_counts.get("duplicate_id", 0) == 1
    assert result.issue_counts.get("duplicate_text", 0) == 1
    assert result.issue_counts.get("invalid_label", 0) >= 2
    assert result.issue_counts.get("label_out_of_range", 0) == 1
    assert result.issue_counts.get("extremely_short_essay", 0) >= 1
    assert result.issue_counts.get("extremely_long_essay", 0) == 1


def test_invalid_utf8_check(tmp_path: Path) -> None:
    path = tmp_path / "bad_utf8.jsonl"
    path.write_bytes(b"\x80\x81\x82")

    cfg = ValidatorConfig()
    result = validate_jsonl_file(path, cfg)

    assert result.encoding_ok is False
    assert result.issue_counts.get("invalid_utf8", 0) == 1
