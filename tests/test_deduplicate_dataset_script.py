from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "deduplicate_dataset.py"
SPEC = importlib.util.spec_from_file_location("deduplicate_dataset_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

DuplicatePair = MODULE.DuplicatePair


def test_detect_exact_duplicates() -> None:
    records = [
        {"id": "a", "essay": "Same text"},
        {"id": "b", "essay": "Same   text"},
        {"id": "c", "essay": "Different"},
    ]

    duplicate_ids, groups = MODULE.detect_exact_duplicates(records)

    assert duplicate_ids == {"b"}
    assert len(groups) == 1
    assert sorted(next(iter(groups.values()))) == ["a", "b"]


def test_near_duplicate_pairs_with_text() -> None:
    records = [
        {"id": "a", "essay": "This is a sentence about logic and argumentation."},
        {"id": "b", "essay": "This is a sentence about logic and argument."},
        {"id": "c", "essay": "Completely unrelated content."},
    ]

    pairs = MODULE.near_duplicate_pairs_with_text(records, threshold=0.8)

    assert any(pair.left_id == "a" and pair.right_id == "b" for pair in pairs)
    assert all(isinstance(pair, DuplicatePair) for pair in pairs)


def test_main_handles_empty_input(tmp_path: Path, monkeypatch) -> None:
    input_jsonl = tmp_path / "missing.jsonl"
    output_jsonl = tmp_path / "deduped.jsonl"
    report_json = tmp_path / "duplicate_report.json"

    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: Namespace(
            input_jsonl=str(input_jsonl),
            output_jsonl=str(output_jsonl),
            duplicate_report=str(report_json),
            near_threshold=0.95,
        ),
    )

    MODULE.main()

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["total_records"] == 0
    assert output_jsonl.read_text(encoding="utf-8") == ""


def test_main_deduplicates_and_writes_report(tmp_path: Path, monkeypatch) -> None:
    input_jsonl = tmp_path / "in.jsonl"
    output_jsonl = tmp_path / "out.jsonl"
    report_json = tmp_path / "duplicate_report.json"

    rows = [
        {"id": "a", "essay": "Alpha beta gamma"},
        {"id": "b", "essay": "Alpha beta gamma"},
        {"id": "c", "essay": "Nearly same sentence here"},
        {"id": "d", "essay": "Nearly same sentence her"},
    ]
    input_jsonl.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        MODULE,
        "near_duplicate_pairs_with_embeddings",
        lambda records, threshold: ([], False),
    )
    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: Namespace(
            input_jsonl=str(input_jsonl),
            output_jsonl=str(output_jsonl),
            duplicate_report=str(report_json),
            near_threshold=0.95,
        ),
    )

    MODULE.main()

    output_rows = [
        json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines()
    ]
    output_ids = {row["id"] for row in output_rows}
    report = json.loads(report_json.read_text(encoding="utf-8"))

    assert "b" not in output_ids
    assert report["removed_records"] >= 1
    assert report["embedding_available"] is False
