from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from datasets import DatasetDict, load_from_disk

MODULE_PATH = Path(__file__).resolve().parents[1] / "datasets" / "build_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_dataset_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


build_dataset_dict = MODULE.build_dataset_dict
ALLOWED_SPLITS = MODULE.ALLOWED_SPLITS


def test_build_dataset_dict_preserves_splits_and_schema(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    (raw_root / "asap_aes").mkdir(parents=True)
    (raw_root / "persuade2").mkdir(parents=True)

    (raw_root / "asap_aes" / "training_set.csv").write_text(
        "essay_id,essay,domain1_score,essay_set\n"
        "e1,This is a valid training essay.,3,1\n"
        "e2,,4,1\n"
        "e3,This has a bad score,bad,1\n",
        encoding="utf-8",
    )
    (raw_root / "asap_aes" / "valid_set.tsv").write_text(
        "id\ttext\tscore\tprompt\n" "v1\tThis is validation text\t2.5\tPrompt A\n",
        encoding="utf-8",
    )
    (raw_root / "persuade2" / "test.jsonl").write_text(
        json.dumps(
            {
                "id": "t1",
                "text": "This is a held-out test response.",
                "score": 1,
                "source": "persuade2",
                "prompt": "Prompt T",
            }
        )
        + "\n"
        + json.dumps({"id": "t2", "text": "Missing score row"})
        + "\n",
        encoding="utf-8",
    )

    dataset_dict, stats = build_dataset_dict(raw_root)

    assert isinstance(dataset_dict, DatasetDict)
    assert tuple(dataset_dict.keys()) == ALLOWED_SPLITS

    assert dataset_dict["train"].num_rows == 1
    assert dataset_dict["validation"].num_rows == 1
    assert dataset_dict["test"].num_rows == 1

    train_example = dataset_dict["train"][0]
    assert set(train_example.keys()) == {"id", "text", "score", "source", "prompt", "split"}
    assert train_example["id"] == "e1"
    assert train_example["split"] == "train"
    assert isinstance(train_example["score"], float)

    valid_example = dataset_dict["validation"][0]
    assert valid_example["split"] == "validation"
    assert valid_example["prompt"] == "Prompt A"

    test_example = dataset_dict["test"][0]
    assert test_example["split"] == "test"
    assert test_example["source"] == "persuade2"

    assert stats.rows_kept == 3
    assert stats.rows_dropped_missing_text == 1
    assert stats.rows_dropped_missing_score == 1
    assert stats.rows_dropped_bad_score == 1


def test_save_and_reload_arrow_dataset(tmp_path: Path) -> None:
    raw_root = tmp_path / "raw"
    (raw_root / "asap2").mkdir(parents=True)

    (raw_root / "asap2" / "train.json").write_text(
        json.dumps(
            [
                {
                    "essay_id": "a1",
                    "essay": "Arrow persistence sample essay.",
                    "domain1_score": 4,
                    "prompt": "Prompt 1",
                }
            ]
        ),
        encoding="utf-8",
    )

    dataset_dict, _stats = build_dataset_dict(raw_root)
    out_dir = tmp_path / "hf" / "dataset_dict"
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    dataset_dict.save_to_disk(str(out_dir))

    reloaded = load_from_disk(str(out_dir))
    assert isinstance(reloaded, DatasetDict)
    assert reloaded["train"].num_rows == 1
    assert reloaded["train"][0]["id"] == "a1"
    assert reloaded["train"][0]["split"] == "train"
