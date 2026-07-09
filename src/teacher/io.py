"""IO and normalization helpers for teacher benchmarking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import canonical_model_id, estimate_cost_usd


def _as_str(value: Any, *, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if "|" in text:
            parts = text.split("|")
        elif ";" in text:
            parts = text.split(";")
        elif "\n" in text:
            parts = text.splitlines()
        else:
            parts = [text]
        return [item.strip() for item in parts if item.strip()]
    if isinstance(value, dict):
        # Keep keys as rubric/skill labels.
        return [str(key).strip() for key in value.keys() if str(key).strip()]
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_number}: {exc.msg}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"Invalid JSONL object at {path}:{line_number}; expected object.")
            rows.append(payload)
    return rows


def _extract(path: list[str], payload: dict[str, Any]) -> Any:
    current: Any = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _first_value(payload: dict[str, Any], candidates: list[list[str]]) -> Any:
    for path in candidates:
        value = _extract(path, payload)
        if value is not None:
            return value
    return None


@dataclass(frozen=True)
class GoldExample:
    """Gold benchmark example."""

    example_id: str
    source: str
    license: str
    prompt: str
    essay: str
    gold_score: float | None
    rubric: tuple[str, ...]
    difficulty: str
    expected_reasoning_skills: tuple[str, ...]
    expected_fallacies: tuple[str, ...]
    notes_for_reviewers: str


@dataclass(frozen=True)
class PredictionRecord:
    """One model prediction row for a gold example."""

    model_id: str
    example_id: str
    predicted_score: float | None
    rubric_items: tuple[str, ...]
    rubric_score: float | None
    reasoning_skills: tuple[str, ...]
    reasoning_score: float | None
    argument_quality_score: float | None
    predicted_fallacies: tuple[str, ...]
    feedback_text: str
    json_valid: bool
    latency_ms: float | None
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    raw_payload: dict[str, Any]


def load_gold_examples(path: Path) -> list[GoldExample]:
    """Load gold set rows from JSONL."""
    if not path.exists():
        raise FileNotFoundError(f"Gold dataset not found: {path}")

    rows = _read_jsonl(path)
    examples: list[GoldExample] = []
    for payload in rows:
        example_id = _as_str(payload.get("example_id")).strip()
        if not example_id:
            raise ValueError("Gold dataset row missing 'example_id'.")

        notes = _first_value(
            payload,
            candidates=[
                ["notes_for_reviewers"],
                ["notes for reviewers"],
                ["reviewer_notes"],
            ],
        )
        examples.append(
            GoldExample(
                example_id=example_id,
                source=_as_str(payload.get("source"), default="unknown"),
                license=_as_str(payload.get("license"), default="unknown"),
                prompt=_as_str(payload.get("prompt")),
                essay=_as_str(payload.get("essay")),
                gold_score=_float_or_none(
                    _first_value(payload, candidates=[["gold_score"], ["score"], ["label"]])
                ),
                rubric=tuple(
                    _listify(_first_value(payload, candidates=[["rubric"], ["gold_rubric_items"]]))
                ),
                difficulty=_as_str(payload.get("difficulty"), default="unknown"),
                expected_reasoning_skills=tuple(
                    _listify(
                        _first_value(
                            payload,
                            candidates=[
                                ["expected_reasoning_skills"],
                                ["expected reasoning skills"],
                            ],
                        )
                    )
                ),
                expected_fallacies=tuple(
                    _listify(
                        _first_value(
                            payload,
                            candidates=[
                                ["expected_fallacies"],
                                ["expected fallacies"],
                            ],
                        )
                    )
                ),
                notes_for_reviewers=_as_str(notes),
            )
        )
    return examples


def _parse_json_valid(payload: dict[str, Any]) -> bool:
    explicit = _first_value(payload, candidates=[["json_valid"], ["json_validity"]])
    if isinstance(explicit, bool):
        return explicit

    output_payload = _first_value(
        payload,
        candidates=[["output"], ["predicted"], ["response_json"]],
    )
    if isinstance(output_payload, dict):
        return True

    raw_output = _first_value(payload, candidates=[["raw_output"], ["response_text"]])
    if isinstance(raw_output, str):
        try:
            parsed = json.loads(raw_output)
            return isinstance(parsed, dict)
        except json.JSONDecodeError:
            return False

    return False


def _parse_tokens(payload: dict[str, Any]) -> tuple[int, int]:
    input_tokens = _first_value(
        payload,
        candidates=[
            ["input_tokens"],
            ["token_usage", "input"],
            ["token_usage", "prompt_tokens"],
            ["usage", "prompt_tokens"],
        ],
    )
    output_tokens = _first_value(
        payload,
        candidates=[
            ["output_tokens"],
            ["token_usage", "output"],
            ["token_usage", "completion_tokens"],
            ["usage", "completion_tokens"],
        ],
    )
    return _int_or_none(input_tokens) or 0, _int_or_none(output_tokens) or 0


def _extract_prediction_fields(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "predicted_score": _first_value(
            payload,
            candidates=[
                ["score_prediction"],
                ["predicted_score"],
                ["output", "score"],
                ["predicted", "score"],
            ],
        ),
        "rubric_items": _first_value(
            payload,
            candidates=[
                ["rubric_items"],
                ["rubric_adherence", "covered"],
                ["output", "criterion_scores"],
                ["output", "rubric_items"],
            ],
        ),
        "rubric_score": _first_value(
            payload,
            candidates=[
                ["rubric_adherence_score"],
                ["rubric_score"],
                ["output", "rubric_adherence_score"],
            ],
        ),
        "reasoning_skills": _first_value(
            payload,
            candidates=[
                ["reasoning_skills"],
                ["logical_reasoning_skills"],
                ["output", "reasoning_skills"],
            ],
        ),
        "reasoning_score": _first_value(
            payload,
            candidates=[
                ["logical_reasoning_score"],
                ["reasoning_score"],
                ["output", "reasoning_quality_score"],
            ],
        ),
        "argument_quality_score": _first_value(
            payload,
            candidates=[
                ["argument_quality_score"],
                ["output", "argument_quality_score"],
                ["output", "argument", "score"],
            ],
        ),
        "predicted_fallacies": _first_value(
            payload,
            candidates=[
                ["fallacy_label"],
                ["predicted_fallacies"],
                ["fallacy_identification", "labels"],
                ["output", "fallacy_label"],
                ["output", "fallacy_labels"],
            ],
        ),
        "feedback_text": _first_value(
            payload,
            candidates=[
                ["educational_feedback"],
                ["feedback"],
                ["output", "feedback"],
                ["output", "next_revision_step"],
                ["revision_suggestions"],
            ],
        ),
    }


def load_predictions(path: Path) -> list[PredictionRecord]:
    """Load prediction rows from one jsonl file or a directory of jsonl files."""
    if not path.exists():
        raise FileNotFoundError(f"Prediction path not found: {path}")

    files: list[Path]
    if path.is_dir():
        files = sorted(path.rglob("*.jsonl"))
        if not files:
            raise FileNotFoundError(f"No JSONL prediction files found under: {path}")
    else:
        files = [path]

    records: list[PredictionRecord] = []
    for file_path in files:
        for payload in _read_jsonl(file_path):
            raw_model = _as_str(_first_value(payload, candidates=[["model_id"], ["model"]])).strip()
            if not raw_model:
                raise ValueError(f"Prediction row missing model_id/model in {file_path}")
            model_id = canonical_model_id(raw_model)

            example_id = _as_str(payload.get("example_id")).strip()
            if not example_id:
                raise ValueError(f"Prediction row missing example_id in {file_path}")

            parsed = _extract_prediction_fields(payload)
            input_tokens, output_tokens = _parse_tokens(payload)
            raw_cost = _first_value(payload, candidates=[["cost_usd"], ["cost"]])
            cost_usd = _float_or_none(raw_cost)
            if cost_usd is None:
                cost_usd = estimate_cost_usd(
                    model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

            records.append(
                PredictionRecord(
                    model_id=model_id,
                    example_id=example_id,
                    predicted_score=_float_or_none(parsed["predicted_score"]),
                    rubric_items=tuple(_listify(parsed["rubric_items"])),
                    rubric_score=_float_or_none(parsed["rubric_score"]),
                    reasoning_skills=tuple(_listify(parsed["reasoning_skills"])),
                    reasoning_score=_float_or_none(parsed["reasoning_score"]),
                    argument_quality_score=_float_or_none(parsed["argument_quality_score"]),
                    predicted_fallacies=tuple(_listify(parsed["predicted_fallacies"])),
                    feedback_text=_as_str(parsed["feedback_text"]),
                    json_valid=_parse_json_valid(payload),
                    latency_ms=_float_or_none(
                        _first_value(
                            payload,
                            candidates=[
                                ["latency_ms"],
                                ["latency"],
                                ["timing", "latency_ms"],
                            ],
                        )
                    ),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=cost_usd,
                    raw_payload=payload,
                )
            )

    return records
