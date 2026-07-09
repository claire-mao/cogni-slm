from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "score_dataset_quality.py"
SPEC = importlib.util.spec_from_file_location("score_dataset_quality_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_quality_helper_functions_cover_key_branches() -> None:
    assert MODULE.clamp(5, 0, 10) == 5
    assert MODULE.clamp(-1, 0, 10) == 0
    assert MODULE.clamp(11, 0, 10) == 10

    assert MODULE.compute_length_score(0, 100, 200) == 0.0
    assert MODULE.compute_length_score(50, 100, 200) < 100
    assert MODULE.compute_length_score(150, 100, 200) == 100.0
    assert MODULE.compute_length_score(300, 100, 200) < 100.0

    text = "This is a simple sentence. Another sentence follows."
    words = MODULE.tokenize_words(text)
    assert len(words) >= 6
    assert MODULE.count_syllables("reading") >= 2

    assert MODULE.compute_language_quality(text, words) > 0
    assert MODULE.compute_ocr_quality(text, words) > 0
    assert MODULE.compute_readability(text, words) >= 0


def test_metadata_and_duplicate_probability_logic() -> None:
    score, missing = MODULE.compute_metadata_score(
        {"source_split": "train"}, ["source_split", "source_row_index"]
    )
    assert score < 100
    assert missing == ["source_row_index"]

    probs = MODULE.compute_duplicate_probabilities(
        ["alpha beta gamma", "alpha beta gamma", "completely different sentence"]
    )
    assert probs[0] == 1.0
    assert probs[1] == 1.0
    assert 0.0 <= probs[2] <= 1.0


def test_score_records_and_reasons() -> None:
    records = [
        {
            "id": "r1",
            "text": "Short text",
            "score": 1,
            "prompt": "P1",
            "source": "demo",
            "metadata": {"source_split": "train"},
        },
        {
            "id": "r2",
            "text": " ".join(["word"] * 200),
            "score": 2,
            "prompt": "P2",
            "source": "demo",
            "metadata": {"source_split": "train", "source_row_index": 2},
        },
    ]

    args = Namespace(
        required_metadata_keys="source_split,source_row_index",
        optimal_min_words=100,
        optimal_max_words=300,
        threshold=70.0,
        sample_removed=10,
    )

    enriched, removed = MODULE.score_records(records, args)

    assert len(enriched) == 2
    assert "quality" in enriched[0]
    assert "overall_quality_score" in enriched[0]["quality"]
    assert all(decision.record_id for decision in removed)


def test_main_writes_scored_filtered_and_report(tmp_path: Path, monkeypatch) -> None:
    input_path = tmp_path / "in.jsonl"
    scored_output = tmp_path / "scored.jsonl"
    filtered_output = tmp_path / "filtered.jsonl"
    removed_output = tmp_path / "removed.jsonl"
    report_path = tmp_path / "report.md"

    rows = [
        {
            "id": "k1",
            "text": " ".join(["good"] * 180),
            "score": 3,
            "prompt": "Prompt",
            "metadata": {"source_split": "train", "source_row_index": 1},
        },
        {
            "id": "k2",
            "text": "bad",
            "score": 1,
            "prompt": "Prompt",
            "metadata": {},
        },
    ]
    input_path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")

    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: Namespace(
            input_jsonl=str(input_path),
            scored_output=str(scored_output),
            filtered_output=str(filtered_output),
            removed_output=str(removed_output),
            report_path=str(report_path),
            threshold=50.0,
            optimal_min_words=100,
            optimal_max_words=250,
            required_metadata_keys="source_split,source_row_index",
            sample_removed=5,
        ),
    )

    MODULE.main()

    scored_rows = [line for line in scored_output.read_text(encoding="utf-8").splitlines() if line]
    filtered_rows = [
        line for line in filtered_output.read_text(encoding="utf-8").splitlines() if line
    ]
    removed_rows = [
        line for line in removed_output.read_text(encoding="utf-8").splitlines() if line
    ]
    report = report_path.read_text(encoding="utf-8")

    assert len(scored_rows) == 2
    assert len(filtered_rows) >= 1
    assert len(removed_rows) >= 0
    assert "# Dataset Quality Scoring Report" in report
