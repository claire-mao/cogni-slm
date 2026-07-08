"""Benchmark dataset loading utilities for evaluation workflows."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Protocol

SplitName = Literal["train", "validation", "test", "heldout_benchmark"]


@dataclass(frozen=True)
class BenchmarkRecord:
    """Single benchmark example used by the evaluation pipeline."""

    example_id: str
    split: SplitName
    dataset_version: str
    taxonomy_version: str
    source_id: str
    argument_text: str
    task_mode: Literal["diagnose", "teach", "quiz_feedback"] = "teach"
    difficulty_level: Literal["beginner", "intermediate", "advanced"] | None = None
    context: dict[str, Any] | None = None
    primary_fallacy_label: str | None = None
    acceptable_alternative_labels: tuple[str, ...] = ()
    expected_sections: tuple[str, ...] = ()
    required_behaviors: tuple[str, ...] = ()
    prohibited_behaviors: tuple[str, ...] = ()
    rubric_hooks: tuple[str, ...] = ()
    is_adversarial: bool = False
    adversarial_type: str | None = None
    attack_target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BenchmarkLoader(Protocol):
    """Contract for loading benchmark records from any backing store."""

    def load_split(self, split: SplitName) -> Iterable[BenchmarkRecord]:
        """Load examples for a single split."""

    def iter_all(self) -> Iterator[BenchmarkRecord]:
        """Iterate through all configured splits."""

    def get_by_id(self, example_id: str) -> BenchmarkRecord | None:
        """Fetch one benchmark example by stable identifier."""


class JSONLBenchmarkLoader:
    """JSONL benchmark loader using one file per split."""

    DEFAULT_SPLIT_FILES: dict[SplitName, str] = {
        "train": "train.jsonl",
        "validation": "validation.jsonl",
        "test": "test.jsonl",
        "heldout_benchmark": "heldout_benchmark.jsonl",
    }

    def __init__(
        self,
        dataset_root: str,
        *,
        split_files: dict[SplitName, str] | None = None,
    ) -> None:
        self.dataset_root = Path(dataset_root)
        self.split_files = split_files or self.DEFAULT_SPLIT_FILES
        self._records_by_split: dict[SplitName, tuple[BenchmarkRecord, ...]] = {}
        self._records_by_id: dict[str, BenchmarkRecord] = {}

    def _split_path(self, split: SplitName) -> Path:
        return self.dataset_root / self.split_files[split]

    def _deserialize_record(self, payload: dict[str, Any], split: SplitName) -> BenchmarkRecord:
        required = [
            "example_id",
            "dataset_version",
            "taxonomy_version",
            "source_id",
            "argument_text",
        ]
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError(f"Missing required fields for split={split}: {missing}")

        return BenchmarkRecord(
            example_id=str(payload["example_id"]),
            split=split,
            dataset_version=str(payload["dataset_version"]),
            taxonomy_version=str(payload["taxonomy_version"]),
            source_id=str(payload["source_id"]),
            argument_text=str(payload["argument_text"]),
            task_mode=payload.get("task_mode", "teach"),
            difficulty_level=payload.get("difficulty_level"),
            context=payload.get("context"),
            primary_fallacy_label=payload.get("primary_fallacy_label"),
            acceptable_alternative_labels=tuple(payload.get("acceptable_alternative_labels", ())),
            expected_sections=tuple(payload.get("expected_sections", ())),
            required_behaviors=tuple(payload.get("required_behaviors", ())),
            prohibited_behaviors=tuple(payload.get("prohibited_behaviors", ())),
            rubric_hooks=tuple(payload.get("rubric_hooks", ())),
            is_adversarial=bool(payload.get("is_adversarial", False)),
            adversarial_type=payload.get("adversarial_type"),
            attack_target=payload.get("attack_target"),
            metadata=dict(payload.get("metadata", {})),
        )

    def _load_split_records(self, split: SplitName) -> tuple[BenchmarkRecord, ...]:
        if split in self._records_by_split:
            return self._records_by_split[split]

        split_path = self._split_path(split)
        if not split_path.exists():
            self._records_by_split[split] = ()
            return ()

        records: list[BenchmarkRecord] = []
        with split_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    payload = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(
                        f"Invalid JSONL at {split_path}:{line_number}: {exc.msg}"
                    ) from exc

                record = self._deserialize_record(payload, split)
                records.append(record)
                self._records_by_id[record.example_id] = record

        self._records_by_split[split] = tuple(records)
        return self._records_by_split[split]

    def load_split(self, split: SplitName) -> Iterable[BenchmarkRecord]:
        return self._load_split_records(split)

    def iter_all(self) -> Iterator[BenchmarkRecord]:
        seen: set[str] = set()
        for split in self.split_files:
            for record in self._load_split_records(split):
                if record.example_id in seen:
                    continue
                seen.add(record.example_id)
                yield record

    def get_by_id(self, example_id: str) -> BenchmarkRecord | None:
        if example_id in self._records_by_id:
            return self._records_by_id[example_id]

        for split in self.split_files:
            _ = self._load_split_records(split)
            if example_id in self._records_by_id:
                return self._records_by_id[example_id]

        return None
