"""Dataset loading and text-formatting helpers for SFT."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from datasets import Dataset, DatasetDict, load_dataset, load_from_disk

from .config import PipelineConfig


def _to_text(prompt: str, essay: str, score: float) -> str:
    """Format one supervised training text sample."""
    return (
        "You are an AP Language instructor. Evaluate the argument quality and score.\n\n"
        f"Prompt:\n{prompt}\n\n"
        f"Essay:\n{essay}\n\n"
        "Target:\n"
        f"Final score: {score:.4f}\n"
    )


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _parse_score(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        score = float(value)
        if score == score and score not in (float("inf"), float("-inf")):
            return score
        return None

    raw = _normalize_text(value)
    if not raw:
        return None

    try:
        score = float(raw)
    except ValueError:
        return None

    if score == score and score not in (float("inf"), float("-inf")):
        return score
    return None


def _datasetdict_from_json(path: Path) -> DatasetDict:
    """Load JSON/JSONL data into a DatasetDict with at least train split."""
    if path.suffix.lower() == ".jsonl":
        data_files = {"train": str(path)}
        loaded = load_dataset("json", data_files=data_files)
        return DatasetDict({"train": loaded["train"]})

    if path.suffix.lower() == ".json":
        data_files = {"train": str(path)}
        loaded = load_dataset("json", data_files=data_files)
        return DatasetDict({"train": loaded["train"]})

    raise ValueError(f"Unsupported file extension for dataset path: {path}")


def load_raw_dataset(config: PipelineConfig) -> DatasetDict:
    """Load source dataset from disk path (DatasetDict dir or json/jsonl file)."""
    dataset_path = Path(config.dataset.dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path not found: {dataset_path}")

    if dataset_path.is_dir():
        try:
            loaded = load_from_disk(str(dataset_path))
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(f"Failed to load dataset directory: {dataset_path}") from exc
        if isinstance(loaded, DatasetDict):
            return loaded
        return DatasetDict({"train": loaded})

    return _datasetdict_from_json(dataset_path)


def _build_text_dataset(dataset: Dataset, config: PipelineConfig) -> Dataset:
    """Ensure dataset has a `text` column for SFT."""
    if config.dataset.text_field in dataset.column_names:
        return dataset

    required = {
        config.dataset.prompt_field,
        config.dataset.essay_field,
        config.dataset.score_field,
    }
    if not required.issubset(set(dataset.column_names)):
        missing = sorted(required - set(dataset.column_names))
        raise ValueError(f"Dataset missing required fields for text build: {missing}")

    def map_fn(example: dict[str, Any]) -> dict[str, str]:
        prompt = _normalize_text(example.get(config.dataset.prompt_field))
        essay = _normalize_text(example.get(config.dataset.essay_field))
        score = _parse_score(example.get(config.dataset.score_field))
        if not prompt or not essay or score is None:
            return {"text": ""}
        return {"text": _to_text(prompt, essay, score)}

    mapped = dataset.map(map_fn, desc="Building SFT text column")
    mapped = mapped.filter(lambda row: _normalize_text(row.get("text")) != "")
    return mapped


def _maybe_limit(dataset: Dataset, limit: int) -> Dataset:
    if limit <= 0 or len(dataset) <= limit:
        return dataset
    return dataset.select(range(limit))


def prepare_train_eval_datasets(config: PipelineConfig) -> tuple[Dataset, Dataset | None]:
    """Load and format training/eval datasets for SFT."""
    dataset_dict = load_raw_dataset(config)

    if config.dataset.train_split not in dataset_dict:
        raise ValueError(f"Train split not found: {config.dataset.train_split}")

    train_ds = _build_text_dataset(dataset_dict[config.dataset.train_split], config)
    train_ds = _maybe_limit(train_ds, config.dataset.max_train_samples)

    eval_ds = None
    if config.dataset.eval_split in dataset_dict:
        eval_ds = _build_text_dataset(dataset_dict[config.dataset.eval_split], config)
        eval_ds = _maybe_limit(eval_ds, config.dataset.max_eval_samples)
        if len(eval_ds) == 0:
            eval_ds = None

    return train_ds, eval_ds
