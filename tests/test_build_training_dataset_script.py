from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

from datasets import load_from_disk

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "build_training_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_training_dataset_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

Example = MODULE.Example
BuildStats = MODULE.BuildStats


def test_parse_and_choice_helpers() -> None:
    assert MODULE.parse_score(1) == 1.0
    assert MODULE.parse_score("2.5") == 2.5
    assert MODULE.parse_score("nan") is None

    assert MODULE.normalize_split("Training") == "train"
    assert MODULE.normalize_split("dev") == "validation"
    assert MODULE.normalize_split("testing") == "test"

    row = {"context": "Prompt", "text": "Essay", "label": 2.0}
    assert MODULE.choose_prompt(row) == "Prompt"
    assert MODULE.choose_essay(row) == "Essay"


def test_load_and_filter_collects_expected_stats(tmp_path: Path) -> None:
    input_jsonl = tmp_path / "unified.jsonl"
    lines = [
        json.dumps({"split": "train", "prompt": "P1", "essay": "E1", "score": 1}),
        json.dumps({"split": "validation", "context": "P2", "text": "E2", "label": 2}),
        json.dumps({"prompt": "P", "essay": "E", "score": 1}),
        json.dumps({"split": "other", "prompt": "P", "essay": "E", "score": 1}),
        json.dumps({"split": "train", "essay": "E", "score": 1}),
        json.dumps({"split": "train", "prompt": "P", "score": 1}),
        json.dumps({"split": "train", "prompt": "P", "essay": "E"}),
        json.dumps({"split": "train", "prompt": "P", "essay": "E", "score": "bad"}),
        "[1,2,3]",
        "not-json",
    ]
    input_jsonl.write_text("\n".join(lines) + "\n", encoding="utf-8")

    grouped_examples, grouped_prov, stats = MODULE.load_and_filter(input_jsonl)

    assert stats.input_lines == 10
    assert stats.parse_errors == 1
    assert stats.non_object_rows == 1
    assert stats.filtered_missing_split == 1
    assert stats.filtered_invalid_split == 1
    assert stats.filtered_missing_prompt == 1
    assert stats.filtered_missing_essay == 1
    assert stats.filtered_missing_score == 1
    assert stats.filtered_non_numeric_score == 1
    assert stats.kept_before_dedup == 2

    assert len(grouped_examples["train"]) == 1
    assert len(grouped_examples["validation"]) == 1
    assert len(grouped_prov["test"]) == 0


def test_deduplicate_with_provenance() -> None:
    stats = BuildStats()
    grouped_examples = {
        "train": [
            Example(prompt="P", essay="E", score=1.0),
            Example(prompt="P", essay="E", score=1.0),
        ],
        "validation": [],
        "test": [],
    }
    grouped_provenance = {
        "train": [
            {"source_id": "a", "split": "train"},
            {"source_id": "b", "split": "train"},
        ],
        "validation": [],
        "test": [],
    }

    dedup_examples, dedup_prov = MODULE.deduplicate_with_provenance(
        grouped_examples, grouped_provenance, stats
    )

    assert len(dedup_examples["train"]) == 1
    assert stats.dedup_removed == 1
    assert len(dedup_prov["train"]) == 1
    assert len(dedup_prov["train"][0]["source_records"]) == 2


def test_save_training_dataset_and_provenance(tmp_path: Path) -> None:
    grouped_examples = {
        "train": [Example(prompt="P1", essay="E1", score=1.0)],
        "validation": [Example(prompt="P2", essay="E2", score=2.0)],
        "test": [Example(prompt="P3", essay="E3", score=3.0)],
    }
    out_dir = tmp_path / "training"
    prov_dir = tmp_path / "prov"

    MODULE.save_training_dataset(out_dir, grouped_examples)
    loaded = load_from_disk(str(out_dir))

    assert set(loaded.keys()) == {"train", "validation", "test"}
    assert loaded["train"].column_names == ["prompt", "essay", "score"]

    MODULE.save_provenance(
        prov_dir,
        {
            "train": [{"id": "a"}],
            "validation": [{"id": "b"}],
            "test": [{"id": "c"}],
        },
    )
    assert (prov_dir / "train.jsonl").exists()


def test_main_builds_dataset_and_report(tmp_path: Path, monkeypatch) -> None:
    input_jsonl = tmp_path / "in.jsonl"
    input_jsonl.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": "a",
                        "split": "train",
                        "prompt": "P",
                        "essay": "E",
                        "score": 1,
                        "metadata": {"source_case": "c", "source_ref": "r", "row_index": 1},
                    }
                ),
                json.dumps(
                    {
                        "id": "b",
                        "split": "validation",
                        "prompt": "P",
                        "essay": "E2",
                        "score": 2,
                        "metadata": {},
                    }
                ),
                json.dumps(
                    {
                        "id": "c",
                        "split": "test",
                        "prompt": "P",
                        "essay": "E3",
                        "score": 3,
                        "metadata": {},
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    output_dataset_dir = tmp_path / "training"
    provenance_dir = tmp_path / "provenance"
    report_path = tmp_path / "report.md"

    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: Namespace(
            input_jsonl=str(input_jsonl),
            output_dataset_dir=str(output_dataset_dir),
            provenance_dir=str(provenance_dir),
            report_path=str(report_path),
        ),
    )

    MODULE.main()

    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "HF Load Verification" in report
    assert "PASS" in report

    loaded = load_from_disk(str(output_dataset_dir))
    assert loaded["train"].num_rows == 1
