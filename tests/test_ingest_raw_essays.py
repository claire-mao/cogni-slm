from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "ingest_raw_essays.py"
SPEC = importlib.util.spec_from_file_location("ingest_raw_essays_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

CandidateRecord = MODULE.CandidateRecord
MalformedFileError = MODULE.MalformedFileError


def _long_essay(words: int = 320) -> str:
    return " ".join(f"word{i}" for i in range(words))


def test_safe_id_and_text_helpers() -> None:
    assert MODULE.safe_id(" essay id / 01 ") == "essay_id___01"
    assert MODULE.normalize_essay_text("a\n\tb   c") == "a b c"
    assert MODULE.count_words("a b c") == 3


def test_read_text_with_fallback_cp1252(tmp_path: Path) -> None:
    path = tmp_path / "cp1252.txt"
    path.write_bytes(b"\x93Quoted text\x94")

    text, encoding = MODULE.read_text_with_fallback(path)

    assert encoding == "cp1252"
    assert "Quoted text" in text


def test_candidate_from_mapping_asap_aes_schema() -> None:
    payload = {
        "essay_id": "A-1",
        "essay": "This is an essay.",
        "essay_set": "2",
        "domain1_score": "4",
    }

    candidate = MODULE.candidate_from_mapping(
        payload,
        fallback_id="fallback",
        source="source.csv:2",
        source_file="source.csv",
        source_format="csv",
        row_number=2,
        encoding="utf-8-sig",
    )

    assert isinstance(candidate, CandidateRecord)
    assert candidate.record_id == "A-1"
    assert candidate.source == "ASAP-AES"
    assert candidate.metadata["essay_set"] == "2"
    assert candidate.metadata["score"] == 4
    assert candidate.metadata["encoding"] == "utf-8-sig"


def test_load_csv_and_tsv(tmp_path: Path) -> None:
    csv_path = tmp_path / "rows.csv"
    csv_path.write_text(
        "id,essay\n" f"c1,{_long_essay()}\n",
        encoding="utf-8",
    )

    tsv_path = tmp_path / "asap.tsv"
    tsv_path.write_text(
        "essay_id\tessay\tessay_set\tdomain1_score\n" f"t1\t{_long_essay()}\t1\t3\n",
        encoding="utf-8",
    )

    csv_rows = MODULE.load_csv(csv_path)
    tsv_rows = MODULE.load_csv(tsv_path)

    assert len(csv_rows) == 1
    assert csv_rows[0].record_id == "c1"
    assert csv_rows[0].metadata["source_format"] == "csv"

    assert len(tsv_rows) == 1
    assert tsv_rows[0].source == "ASAP-AES"
    assert tsv_rows[0].metadata["source_format"] == "tsv"


def test_load_json_variants(tmp_path: Path) -> None:
    object_path = tmp_path / "one.json"
    object_path.write_text(json.dumps({"id": "j1", "essay": _long_essay()}), encoding="utf-8")

    list_path = tmp_path / "many.json"
    list_path.write_text(
        json.dumps(
            [
                {"id": "l1", "essay": _long_essay()},
                {"id": "l2", "essay": _long_essay()},
            ]
        ),
        encoding="utf-8",
    )

    records_path = tmp_path / "records.json"
    records_path.write_text(
        json.dumps({"records": [{"id": "r1", "essay": _long_essay()}]}),
        encoding="utf-8",
    )

    assert len(MODULE.load_json(object_path)) == 1
    assert len(MODULE.load_json(list_path)) == 2
    assert len(MODULE.load_json(records_path)) == 1


def test_load_jsonl_malformed_row_raises(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"id":"ok","essay":"text"}\nnot-json\n', encoding="utf-8")

    try:
        MODULE.load_jsonl(path)
    except MalformedFileError as exc:
        assert "JSONL parse error" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("Expected MalformedFileError for invalid JSONL")


def test_main_applies_validation_and_writes_report(tmp_path: Path, monkeypatch) -> None:
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    (raw_dir / "essay_a.txt").write_text(_long_essay(), encoding="utf-8")
    (raw_dir / "rows.csv").write_text(
        "id,essay\n" f"essay_a,{_long_essay()}\n" "short1,too short\n",
        encoding="utf-8",
    )
    (raw_dir / "broken.json").write_text("{not valid json", encoding="utf-8")

    output_jsonl = tmp_path / "processed" / "raw_essays.jsonl"
    report_path = tmp_path / "outputs" / "report.md"

    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: Namespace(
            raw_dir=str(raw_dir),
            output_jsonl=str(output_jsonl),
            report_path=str(report_path),
            min_words=300,
        ),
    )

    MODULE.main()

    rows = [
        json.loads(line) for line in output_jsonl.read_text(encoding="utf-8").splitlines() if line
    ]
    report = report_path.read_text(encoding="utf-8")

    assert len(rows) == 1
    assert rows[0]["id"] == "essay_a"
    assert rows[0]["metadata"]["word_count"] >= 300

    assert "Malformed files rejected: `1`" in report
    assert "`duplicate_id`: `1`" in report
    assert "`essay_too_short`: `1`" in report
