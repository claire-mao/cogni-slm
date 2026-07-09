from __future__ import annotations

import importlib.util
import json
import sys
from argparse import Namespace
from pathlib import Path

import pandas as pd

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "create_provenance_index.py"
SPEC = importlib.util.spec_from_file_location("create_provenance_index_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

ProvenanceRow = MODULE.ProvenanceRow


def test_infer_helpers_prefer_metadata_then_defaults(tmp_path: Path) -> None:
    metadata = {
        "source_file": "nested/path/file.tsv",
        "original_url": "https://example.com/data",
        "license": "CC-BY-4.0",
        "retrieval_date": "2026-01-01",
        "mapping": {"id": "essay_id"},
        "original_fields": {"essay_id": "orig-123"},
    }

    assert MODULE.infer_source_filename("asap_aes", metadata) == "file.tsv"
    assert MODULE.infer_original_url("asap_aes", metadata) == "https://example.com/data"
    assert MODULE.infer_license("asap_aes", metadata) == "CC-BY-4.0"
    assert MODULE.infer_original_dataset("asap_aes", metadata) == "asap_aes"
    assert MODULE.infer_original_identifier("row-1", metadata) == "orig-123"
    assert (
        MODULE.infer_retrieval_date("asap_aes", "training_set_rel3.tsv", metadata, tmp_path)
        == "2026-01-01"
    )


def test_build_and_write_rows_covers_all_jsonl_artifacts(tmp_path: Path) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir(parents=True)

    quality_scored_row = {
        "id": "a-1",
        "source": "asap_aes",
        "split": "train",
        "text": "Essay A",
        "metadata": {
            "mapping": {"id": "essay_id"},
            "original_fields": {"essay_id": "orig-a1"},
            "source_ref": "datasets/raw/asap_aes/training_set_rel3.tsv",
            "license": "CC-BY-4.0",
        },
    }
    quality_removed_row = {
        "id": "a-1",
        "source": "asap_aes",
        "overall_quality_score": 5.0,
        "reason": "below_threshold",
    }

    (final_dir / "quality_scored.jsonl").write_text(
        json.dumps(quality_scored_row) + "\n", encoding="utf-8"
    )
    (final_dir / "quality_removed.jsonl").write_text(
        json.dumps(quality_removed_row) + "\n", encoding="utf-8"
    )

    output_parquet = tmp_path / "out" / "provenance.parquet"
    (
        preview_rows,
        artifact_counts,
        missing_counts,
        total_rows,
    ) = MODULE.build_and_write_rows(final_dir, output_parquet, batch_size=10)

    assert total_rows == 2
    assert artifact_counts["final/quality_scored.jsonl"] == 1
    assert artifact_counts["final/quality_removed.jsonl"] == 1
    assert all(v == 0 for v in missing_counts.values())
    assert len(preview_rows) >= 1

    frame = pd.read_parquet(output_parquet)
    assert len(frame) == 2
    assert set(frame["artifact_path"].tolist()) == {
        "final/quality_scored.jsonl",
        "final/quality_removed.jsonl",
    }
    assert set(frame["split_assignment"].tolist()) == {"train"}


def test_write_report_outputs_expected_sections(tmp_path: Path) -> None:
    output_parquet = tmp_path / "provenance.parquet"
    frame = pd.DataFrame(
        [
            {
                "example_id": "a",
                "dataset": "asap_aes",
                "original_dataset": "asap_aes",
                "original_identifier": "orig-a",
                "preprocessing_history": '["quality_scored","train"]',
                "split": "train",
                "split_assignment": "train",
                "source_url": "https://example.com",
                "original_url": "https://example.com",
                "license": "CC-BY-4.0",
                "retrieval_date": "2026-01-01",
                "hash": "0" * 64,
                "source_filename": "training.tsv",
                "artifact_path": "final/train.jsonl",
                "artifact_row": 1,
            }
        ]
    )
    frame.to_parquet(output_parquet, index=False)
    report_path = tmp_path / "provenance_repair.md"
    preview_rows = [
        ProvenanceRow(
            example_id="a",
            dataset="asap_aes",
            original_dataset="asap_aes",
            original_identifier="orig-a",
            preprocessing_history='["quality_scored","train"]',
            split_assignment="train",
            source_url="https://example.com",
            original_url="https://example.com",
            license="CC-BY-4.0",
            retrieval_date="2026-01-01",
            hash="0" * 64,
            split="train",
            source_filename="training.tsv",
            artifact_path="final/train.jsonl",
            artifact_row=1,
        )
    ]

    MODULE.write_report(
        report_path=report_path,
        output_parquet=output_parquet,
        preview_rows=preview_rows,
        artifact_row_counts={"final/train.jsonl": 1},
        required_missing_counts={name: 0 for name in MODULE.REQUIRED_TRACEABILITY_FIELDS},
        total_input_rows=1,
    )

    report = report_path.read_text(encoding="utf-8")
    assert "# Provenance Repair Report" in report
    assert "All examples traceable" in report


def test_main_runs(tmp_path: Path, monkeypatch) -> None:
    final_dir = tmp_path / "final"
    final_dir.mkdir(parents=True)
    for split in ("train", "validation", "test"):
        (final_dir / f"{split}.jsonl").write_text(
            json.dumps(
                {
                    "id": f"{split}-1",
                    "source": "asap_aes",
                    "split": split,
                    "text": "essay",
                    "metadata": {},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    output_parquet = tmp_path / "out" / "provenance.parquet"
    report_path = tmp_path / "out" / "provenance_repair.md"

    monkeypatch.setattr(
        MODULE,
        "parse_args",
        lambda: Namespace(
            final_dir=str(final_dir),
            output_parquet=str(output_parquet),
            report_path=str(report_path),
            batch_size=10,
        ),
    )

    MODULE.main()

    assert output_parquet.exists()
    assert report_path.exists()
