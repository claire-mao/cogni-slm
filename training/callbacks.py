"""Custom callbacks for Unsloth training."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from transformers import TrainerCallback, TrainerControl, TrainerState, TrainingArguments


@dataclass
class EvalRecord:
    """One evaluation callback event row."""

    step: int
    epoch: float | None
    metrics: dict[str, Any]
    timestamp_utc: str


class EvalMetricsCallback(TrainerCallback):
    """Persist evaluation metrics to JSONL after each evaluation event."""

    def __init__(self, output_path: str | Path) -> None:
        self.output_path = Path(output_path)

    def on_evaluate(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        metrics: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        del kwargs
        payload = EvalRecord(
            step=int(state.global_step),
            epoch=float(state.epoch) if state.epoch is not None else None,
            metrics=metrics or {},
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload.__dict__, ensure_ascii=False) + "\n")
