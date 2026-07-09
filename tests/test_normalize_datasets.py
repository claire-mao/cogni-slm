from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = (
    Path(__file__).resolve().parents[1] / "datasets" / "processing" / "normalize_datasets.py"
)
SPEC = importlib.util.spec_from_file_location("normalize_datasets_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

normalize_dataset = MODULE.normalize_dataset


def test_normalize_dataset_to_canonical_schema(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    ds_dir = raw_root / "demo"
    ds_dir.mkdir(parents=True)

    (ds_dir / "train.csv").write_text(
        "id,essay,domain1_score,essay_set,source\n"
        "a1,This is essay one.,4,1,asap_aes\n"
        "a2,,5,1,asap_aes\n"
        "a3,This is essay three.,,1,asap_aes\n",
        encoding="utf-8",
    )
    (ds_dir / "validation.jsonl").write_text(
        json.dumps({"essay_id": "v1", "text": "Validation text", "score": 2.5, "prompt": "P"})
        + "\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "normalized"
    output_dir.mkdir(parents=True)

    output_path, stats = normalize_dataset(dataset_dir=ds_dir, output_dir=output_dir)

    rows = [
        json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line
    ]

    assert stats.files_seen == 2
    assert stats.rows_seen == 4
    assert stats.rows_kept == 3
    assert stats.rows_dropped_missing_text == 1
    assert stats.rows_missing_label == 1

    first = rows[0]
    assert set(first.keys()) == {"id", "source", "task", "prompt", "text", "label", "metadata"}
    assert first["id"] == "a1"
    assert isinstance(first["label"], float)
    assert "raw_row" in first["metadata"]
    assert "encoding" in first["metadata"]

    third = rows[2]
    assert third["id"] == "v1"
    assert third["prompt"] == "P"


def test_missing_label_is_graceful(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    ds_dir = raw_root / "nolabel"
    ds_dir.mkdir(parents=True)

    (ds_dir / "test.tsv").write_text(
        "essay_id\tessay_set\tessay\n" "t1\t8\tMissing score example\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "normalized"
    output_dir.mkdir(parents=True)

    output_path, stats = normalize_dataset(dataset_dir=ds_dir, output_dir=output_dir)
    rows = [
        json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines() if line
    ]

    assert stats.rows_kept == 1
    assert stats.rows_missing_label == 1
    assert rows[0]["label"] is None
    assert rows[0]["task"] == "unknown"
