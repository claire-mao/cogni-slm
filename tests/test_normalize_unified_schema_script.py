from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "normalize_unified_schema.py"
SPEC = importlib.util.spec_from_file_location("normalize_unified_schema_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

MappingTracker = MODULE.MappingTracker
SourceCase = MODULE.SourceCase


def test_discovery_split_inference_and_safe_filename(tmp_path: Path) -> None:
    root = tmp_path / "datasets"
    case_dir = root / "processed" / "normalized" / "demo"
    case_dir.mkdir(parents=True)
    (case_dir / "train.jsonl").write_text("{}\n", encoding="utf-8")
    (case_dir / "validation.jsonl").write_text("{}\n", encoding="utf-8")
    (case_dir / "test.jsonl").write_text("{}\n", encoding="utf-8")

    structured = root / "raw" / "a.csv"
    structured.parent.mkdir(parents=True)
    structured.write_text("id,essay\na1,text\n", encoding="utf-8")

    excluded = root / "processed" / "unified" / "skip.jsonl"
    excluded.parent.mkdir(parents=True)
    excluded.write_text("{}\n", encoding="utf-8")

    jsonl_cases = MODULE.discover_jsonl_cases(root)
    structured_cases = MODULE.discover_structured_file_cases(root)

    assert any(case.kind == "jsonl" and len(case.split_files) == 3 for case in jsonl_cases)
    assert any(case.file_path == structured for case in structured_cases)
    assert not any("processed/unified" in case.name for case in jsonl_cases)

    assert MODULE.infer_split_from_name(Path("my_valid_set.tsv")) == "validation"
    assert MODULE.infer_split_from_name(Path("my_test_set.tsv")) == "test"
    assert MODULE.safe_case_filename("raw/asap/train.jsonl", "jsonl") == "raw__asap__train.jsonl"


def test_read_text_with_fallback_and_loaders(tmp_path: Path) -> None:
    cp_file = tmp_path / "cp.csv"
    cp_file.write_bytes(b"id,essay\n1,\x93quoted\x94\n")

    text, encoding = MODULE.read_text_with_fallback(cp_file)
    assert encoding == "cp1252"
    assert "quoted" in text

    csv_rows, csv_encoding, csv_errors = MODULE.load_structured_rows(cp_file)
    assert csv_encoding == "cp1252"
    assert csv_errors == []
    assert csv_rows[0]["id"] == "1"

    txt_path = tmp_path / "one.txt"
    txt_path.write_text("essay text", encoding="utf-8")
    rows, txt_encoding, txt_errors = MODULE.load_structured_rows(txt_path)
    assert txt_encoding == "utf-8-sig"
    assert txt_errors == []
    assert rows[0]["text"] == "essay text"

    json_path = tmp_path / "bad.json"
    json_path.write_text("{bad", encoding="utf-8")
    bad_rows, _enc, parse_errors = MODULE.load_structured_rows(json_path)
    assert parse_errors
    assert "parse_error" in bad_rows[0]


def test_normalize_row_inference_and_metadata() -> None:
    tracker = MappingTracker()
    row = {
        "essay": "Essay text",
        "primary_fallacy_label": "strawman",
        "domain1_score": "bad-score",
        "custom_field": "x",
    }

    normalized = MODULE.normalize_row(
        row=row,
        tracker=tracker,
        case_name="case/demo",
        source_ref="src/file.jsonl",
        row_index=7,
        split_hint="test",
        encoding="utf-8",
    )

    assert normalized["id"] == "case/demo:00000007"
    assert normalized["task"] == "fallacy_reasoning"
    assert normalized["score"] is None
    assert normalized["source"] == "case/demo"
    assert normalized["license"] == "unknown"
    assert normalized["split"] == "test"
    assert normalized["metadata"]["score_raw"] == "bad-score"
    assert "custom_field" in normalized["metadata"]["unmapped_fields"]


def test_jsonl_case_and_combined_report(tmp_path: Path) -> None:
    source = tmp_path / "source"
    output_root = tmp_path / "out"
    source.mkdir(parents=True)

    train_path = source / "train.jsonl"
    train_path.write_text(
        json.dumps({"id": "a", "essay": "Essay", "score": 1, "split": "train"})
        + "\n"
        + "not-json\n",
        encoding="utf-8",
    )
    test_path = source / "test.jsonl"
    test_path.write_text(
        json.dumps({"id": "b", "essay": "Essay2", "score": 2, "split": "test"}) + "\n",
        encoding="utf-8",
    )

    case = SourceCase(
        name="demo/case",
        kind="jsonl",
        split_files={"train": train_path, "test": test_path},
    )
    case_output = MODULE.normalize_jsonl_case(case, output_root)

    assert case_output.output_path.exists()
    normalized_rows = [
        json.loads(line)
        for line in case_output.output_path.read_text(encoding="utf-8").splitlines()
        if line
    ]
    assert len(normalized_rows) == 3

    combined_path = tmp_path / "combined.jsonl"
    combined_count = MODULE.write_combined([case_output], combined_path)
    assert combined_count == 3

    report = MODULE.render_mapping_report(
        case_outputs=[case_output],
        output_root=output_root,
        combined_path=combined_path,
        combined_rows=combined_count,
    )
    assert "Schema Mapping Report" in report
    assert "demo/case" in report
