"""Dataset loading utilities for model-comparison evaluation harness."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

try:
    from .harness_common import normalize_text, parse_finite_float
except ImportError:  # pragma: no cover - script-mode import fallback
    from harness_common import normalize_text, parse_finite_float


@dataclass(frozen=True)
class EvalRecord:
    """Single evaluation record."""

    example_id: str
    split: str
    prompt: str
    essay: str
    score: float


def load_records_from_hf_dataset(
    dataset_path: str | Path,
    split: str,
    *,
    max_examples: int = 0,
    prompt_field: str = "prompt",
    essay_field: str = "essay",
    score_field: str = "score",
) -> list[EvalRecord]:
    """Load records from a Hugging Face DatasetDict saved to disk."""
    from datasets import load_from_disk

    path = Path(dataset_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset path not found: {path}")

    dataset = load_from_disk(str(path))
    if split not in dataset:
        raise ValueError(f"Split '{split}' not found in dataset: {sorted(dataset.keys())}")

    records: list[EvalRecord] = []
    for idx, row in enumerate(dataset[split]):
        prompt = normalize_text(row.get(prompt_field))
        essay = normalize_text(row.get(essay_field))
        score = parse_finite_float(row.get(score_field))

        if not prompt or not essay or score is None:
            continue

        record_id = normalize_text(row.get("id")) or f"{split}:{idx:07d}"
        records.append(
            EvalRecord(
                example_id=record_id,
                split=split,
                prompt=prompt,
                essay=essay,
                score=score,
            )
        )

        if max_examples > 0 and len(records) >= max_examples:
            break

    return records


def load_records_from_jsonl(
    jsonl_path: str | Path,
    *,
    max_examples: int = 0,
    prompt_field: str = "prompt",
    essay_field: str = "essay",
    score_field: str = "score",
) -> list[EvalRecord]:
    """Load records from a JSONL file."""
    path = Path(jsonl_path)
    if not path.exists():
        raise FileNotFoundError(f"JSONL path not found: {path}")

    records: list[EvalRecord] = []
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue

            payload = json.loads(raw)
            if not isinstance(payload, dict):
                continue

            prompt = normalize_text(payload.get(prompt_field))
            essay = normalize_text(payload.get(essay_field))
            score = parse_finite_float(payload.get(score_field))

            if not prompt or not essay or score is None:
                continue

            record_id = normalize_text(payload.get("id")) or f"jsonl:{idx:07d}"
            split = normalize_text(payload.get("split")) or "unknown"

            records.append(
                EvalRecord(
                    example_id=record_id,
                    split=split,
                    prompt=prompt,
                    essay=essay,
                    score=score,
                )
            )

            if max_examples > 0 and len(records) >= max_examples:
                break

    return records
