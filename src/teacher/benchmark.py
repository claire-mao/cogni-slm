"""Teacher benchmarking engine for educational-assessment supervision.

This module evaluates configured teacher models on:
- essay scoring
- logical reasoning
- rubric adherence
- fallacy detection
- feedback quality

Outputs include:
- leaderboards
- cost tables
- latency tables
- agreement matrices
- confidence calibration summaries

No model inference is executed in this module.
"""

from __future__ import annotations

import csv
import json
import math
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from .io import GoldExample, PredictionRecord
from .metrics import (
    clamp01,
    f1_precision_recall,
    feedback_usefulness_score,
    mae,
    percentile,
    quadratic_weighted_kappa,
)
from .models import SUPPORTED_MODELS, canonical_model_id

TASK_ESSAY_SCORING = "essay_scoring"
TASK_RUBRIC_ADHERENCE = "rubric_adherence"
TASK_EDUCATIONAL_FEEDBACK = "educational_feedback"
TASK_LOGICAL_REASONING = "logical_reasoning"
TASK_ARGUMENT_QUALITY = "argument_quality"
TASK_FALLACY_IDENTIFICATION = "logical_fallacy_identification"

DEFAULT_TASK_SUITE_PATH = Path("configs/teacher/teacher_task_suite_v1.json")
DEFAULT_MODELS_CONFIG_PATH = Path("configs/teacher/teacher_models_costs_v1.json")


@dataclass(frozen=True)
class PerExampleMetricRow:
    """Per-example benchmark row."""

    model_id: str
    example_id: str
    source: str
    difficulty: str
    score_abs_error: float | None
    rubric_adherence: float
    logical_reasoning: float
    argument_quality: float
    fallacy_precision: float
    fallacy_recall: float
    fallacy_f1: float
    educational_feedback: float
    json_valid: bool
    latency_ms: float | None
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: float | None
    confidence_mean: float | None
    tasks_covered: int
    missing_prediction: bool
    notes: str


@dataclass(frozen=True)
class ModelSummary:
    """Model-level aggregate benchmark scores."""

    model_id: str
    examples_total: int
    examples_with_prediction: int
    coverage: float
    score_prediction_qwk: float
    score_prediction_mae: float
    rubric_adherence: float
    logical_reasoning: float
    argument_quality: float
    fallacy_precision: float
    fallacy_recall: float
    fallacy_f1: float
    educational_feedback: float
    json_validity: float
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    input_tokens_total: int
    output_tokens_total: int
    total_tokens_total: int
    cost_total_usd: float
    cost_per_example_usd: float
    agreement: float
    consistency: float
    calibration_temperature: float
    calibration_ece_before: float | None
    calibration_ece_after: float | None
    calibration_brier_before: float | None
    calibration_brier_after: float | None
    rank_score: float
    rank: int


@dataclass(frozen=True)
class _TaskSpec:
    task_id: str
    required_output_fields: tuple[str, ...]


@dataclass(frozen=True)
class _InternalPrediction:
    model_id: str
    example_id: str
    task_id: str
    run_id: str
    seed: int
    temperature: float
    prompt_version: str
    predicted_score: float | None
    rubric_items: tuple[str, ...]
    rubric_score: float | None
    reasoning_skills: tuple[str, ...]
    reasoning_score: float | None
    argument_quality_score: float | None
    predicted_fallacies: tuple[str, ...]
    feedback_text: str
    confidence: float | None
    json_valid: bool
    latency_ms: float | None
    input_tokens: int
    output_tokens: int
    cost_usd: float | None
    output_payload: dict[str, Any] | None
    raw_payload: dict[str, Any]


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    parsed = _safe_float(value)
    return int(parsed) if parsed is not None else default


def _clamp_probability(value: float, *, eps: float = 1e-6) -> float:
    return min(1.0 - eps, max(eps, value))


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1.0 + exp_pos)


def _logit(value: float) -> float:
    p = _clamp_probability(value)
    return math.log(p / (1.0 - p))


def temperature_scale_confidence(confidence: float, temperature: float) -> float:
    """Apply temperature scaling to one confidence value."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    return _sigmoid(_logit(clamp01(confidence)) / temperature)


def brier_score(confidences: list[float], targets: list[float]) -> float | None:
    """Compute Brier score over paired confidence/target values."""
    if not confidences or len(confidences) != len(targets):
        return None
    return mean(
        (confidence - target) ** 2
        for confidence, target in zip(confidences, targets, strict=True)
    )


def expected_calibration_error(
    confidences: list[float],
    targets: list[float],
    *,
    bins: int = 10,
) -> float | None:
    """Compute expected calibration error (ECE)."""
    if not confidences or len(confidences) != len(targets):
        return None
    if bins < 2:
        raise ValueError("bins must be >= 2")

    bucket_conf: list[list[float]] = [[] for _ in range(bins)]
    bucket_tar: list[list[float]] = [[] for _ in range(bins)]
    for confidence, target in zip(confidences, targets, strict=True):
        index = min(int(clamp01(confidence) * bins), bins - 1)
        bucket_conf[index].append(clamp01(confidence))
        bucket_tar[index].append(clamp01(target))

    total = sum(len(row) for row in bucket_conf)
    if total == 0:
        return None

    ece = 0.0
    for conf_values, target_values in zip(bucket_conf, bucket_tar, strict=True):
        if not conf_values:
            continue
        avg_conf = mean(conf_values)
        avg_target = mean(target_values)
        ece += (len(conf_values) / total) * abs(avg_conf - avg_target)
    return ece


def _binary_nll(probabilities: list[float], targets: list[float]) -> float:
    if not probabilities or len(probabilities) != len(targets):
        raise ValueError("probabilities and targets must be non-empty with equal lengths")
    losses: list[float] = []
    for probability, target in zip(probabilities, targets, strict=True):
        p = _clamp_probability(probability)
        y = clamp01(target)
        losses.append(-(y * math.log(p) + (1.0 - y) * math.log(1.0 - p)))
    return mean(losses)


def fit_temperature_scaling(
    confidences: list[float],
    targets: list[float],
    *,
    grid_min: float = 0.25,
    grid_max: float = 4.0,
    grid_size: int = 200,
) -> tuple[float, float | None, float | None]:
    """Fit temperature by minimizing NLL on a fixed grid."""
    if not confidences or len(confidences) != len(targets):
        return 1.0, None, None
    if grid_min <= 0 or grid_max <= 0:
        raise ValueError("temperature grid bounds must be > 0")
    if grid_min > grid_max:
        raise ValueError("grid_min must be <= grid_max")
    if grid_size < 2:
        raise ValueError("grid_size must be >= 2")

    nll_before = _binary_nll(confidences, targets)
    best_temperature = 1.0
    best_nll = nll_before

    for index in range(grid_size):
        frac = index / (grid_size - 1)
        temperature = grid_min + frac * (grid_max - grid_min)
        scaled = [temperature_scale_confidence(value, temperature) for value in confidences]
        nll = _binary_nll(scaled, targets)
        if nll < best_nll:
            best_nll = nll
            best_temperature = temperature

    return best_temperature, nll_before, best_nll


def _normalize_label(value: Any) -> str:
    text = _normalize_text(value).lower().replace("-", " ")
    normalized = "_".join(text.split())
    if normalized in {"none", "no_fallacy", "n/a", "na", "null"}:
        return ""
    return normalized


def _to_label_set(values: tuple[str, ...]) -> set[str]:
    return {item for item in (_normalize_label(value) for value in values) if item}


def _extract_json_object(text: str) -> dict[str, Any] | None:
    raw = text.strip()
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        return payload

    start = raw.find("{")
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(raw)):
        ch = raw[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                segment = raw[start : index + 1]
                try:
                    candidate = json.loads(segment)
                except json.JSONDecodeError:
                    return None
                return candidate if isinstance(candidate, dict) else None
    return None


def _extract_output_payload(row: dict[str, Any]) -> dict[str, Any] | None:
    payload = row.get("raw_json_output")
    if isinstance(payload, dict):
        return payload

    payload = row.get("output")
    if isinstance(payload, dict):
        return payload

    raw_response = row.get("raw_response_text")
    if isinstance(raw_response, str):
        return _extract_json_object(raw_response)
    return None


def _first_float(payload: dict[str, Any] | None, keys: tuple[str, ...]) -> float | None:
    if not isinstance(payload, dict):
        return None
    for key in keys:
        value = _safe_float(payload.get(key))
        if value is not None:
            return value
    return None


def _first_text(payload: dict[str, Any] | None, keys: tuple[str, ...]) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _to_list(value: Any) -> list[str]:
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
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, dict):
        return [str(key).strip() for key in value if str(key).strip()]
    if value is None:
        return []
    return [str(value).strip()]


def _extract_fallacies(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()

    direct = payload.get("fallacies")
    if isinstance(direct, list):
        values = sorted({label for label in (_normalize_label(v) for v in direct) if label})
        return tuple(values)
    if isinstance(direct, dict):
        primary = _normalize_label(direct.get("primary"))
        alternatives = [
            _normalize_label(item)
            for item in _to_list(direct.get("alternative_labels"))
            if _normalize_label(item)
        ]
        values = sorted({item for item in [primary, *alternatives] if item})
        return tuple(values)

    label = _normalize_label(payload.get("fallacy_label"))
    if label:
        return (label,)
    return ()


def _extract_confidence(row: dict[str, Any], payload: dict[str, Any] | None) -> float | None:
    candidates = [
        _safe_float(row.get("confidence")),
        _first_float(payload, ("confidence", "rubric_adherence_confidence")),
    ]
    for value in candidates:
        if value is None:
            continue
        if value > 1.0 and value <= 100.0:
            value = value / 100.0
        return clamp01(value)
    return None


def _extract_rubric_items(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    items = _to_list(payload.get("rubric"))
    if items:
        return tuple(items)
    items = _to_list(payload.get("rubric_items"))
    if items:
        return tuple(items)
    criterion_scores = payload.get("criterion_scores")
    if isinstance(criterion_scores, dict):
        return tuple(_to_list(criterion_scores))
    return ()


def _extract_reasoning_skills(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    items = _to_list(payload.get("reasoning_skills"))
    if items:
        return tuple(items)
    links = payload.get("claim_evidence_links")
    return tuple(_to_list(links))


def _task_specs(path: Path = DEFAULT_TASK_SUITE_PATH) -> dict[str, _TaskSpec]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return {}
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        return {}
    specs: dict[str, _TaskSpec] = {}
    for row in tasks:
        if not isinstance(row, dict):
            continue
        task_id = _normalize_text(row.get("task_id"))
        if not task_id:
            continue
        required = row.get("required_output_fields")
        if not isinstance(required, list):
            required = []
        specs[task_id] = _TaskSpec(
            task_id=task_id,
            required_output_fields=tuple(_normalize_text(item) for item in required if item),
        )
    return specs


def _canonical_or_none(model_name: str) -> str | None:
    if not model_name.strip():
        return None
    try:
        return canonical_model_id(model_name)
    except Exception:
        pass

    alias = _normalize_text(model_name).lower().replace("-", "_").replace(" ", "_")
    fallback_aliases = {
        "claude_opus_4x": "claude_opus_4",
        "claude_sonnet_4x": "claude_sonnet_4",
        "llama4_maverick": "llama_4_maverick",
    }
    return fallback_aliases.get(alias)


def _configured_models(path: Path = DEFAULT_MODELS_CONFIG_PATH) -> tuple[str, ...]:
    if not path.exists():
        return SUPPORTED_MODELS
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return SUPPORTED_MODELS
    rows = payload.get("models")
    if not isinstance(rows, list):
        return SUPPORTED_MODELS

    models: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _normalize_text(row.get("model_id"))
        resolved = _canonical_or_none(value)
        if resolved and resolved not in models:
            models.append(resolved)
    return tuple(models) if models else SUPPORTED_MODELS


def _prediction_to_internal(record: PredictionRecord) -> _InternalPrediction:
    row = record.raw_payload if isinstance(record.raw_payload, dict) else {}
    payload = _extract_output_payload(row)

    predicted_score = record.predicted_score
    if predicted_score is None:
        predicted_score = _first_float(payload, ("score", "predicted_score", "score_prediction"))

    rubric_score = record.rubric_score
    if rubric_score is None:
        rubric_score = _first_float(payload, ("rubric_score", "rubric_adherence_score"))

    reasoning_score = record.reasoning_score
    if reasoning_score is None:
        reasoning_score = _first_float(payload, ("reasoning_quality_score", "reasoning_score"))

    argument_quality_score = record.argument_quality_score
    if argument_quality_score is None:
        argument_quality_score = _first_float(payload, ("argument_quality_score",))

    feedback_text = record.feedback_text.strip()
    if not feedback_text:
        feedback_text = _first_text(
            payload,
            (
                "feedback",
                "educational_feedback",
                "next_revision_step",
                "revision_plan",
            ),
        )

    task_id = _normalize_text(row.get("task_id")) or TASK_ESSAY_SCORING
    return _InternalPrediction(
        model_id=record.model_id,
        example_id=record.example_id,
        task_id=task_id,
        run_id=_normalize_text(row.get("run_id")),
        seed=_safe_int(row.get("seed"), default=0),
        temperature=_safe_float(row.get("temperature")) or 0.0,
        prompt_version=_normalize_text(row.get("prompt_version")),
        predicted_score=predicted_score,
        rubric_items=record.rubric_items or _extract_rubric_items(payload),
        rubric_score=rubric_score,
        reasoning_skills=record.reasoning_skills or _extract_reasoning_skills(payload),
        reasoning_score=reasoning_score,
        argument_quality_score=argument_quality_score,
        predicted_fallacies=record.predicted_fallacies or _extract_fallacies(payload),
        feedback_text=feedback_text,
        confidence=_extract_confidence(row, payload),
        json_valid=record.json_valid,
        latency_ms=record.latency_ms,
        input_tokens=record.input_tokens,
        output_tokens=record.output_tokens,
        cost_usd=record.cost_usd,
        output_payload=payload,
        raw_payload=row,
    )


def _sort_key_for_primary(item: _InternalPrediction) -> tuple[float, int, str, str]:
    return (
        abs(item.temperature),
        item.seed,
        item.run_id,
        item.prompt_version,
    )


def _select_primary(items: list[_InternalPrediction]) -> _InternalPrediction:
    return sorted(items, key=_sort_key_for_primary)[0]


def _field_present(payload: dict[str, Any] | None, field: str) -> bool:
    if not isinstance(payload, dict):
        return False
    value = payload.get(field)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return True


def _rubric_adherence_score(
    prediction: _InternalPrediction | None,
    gold: GoldExample,
    task_spec: _TaskSpec | None,
) -> float:
    if prediction is None:
        return 0.0
    if prediction.rubric_score is not None:
        return clamp01(prediction.rubric_score)

    field_score = 0.0
    if task_spec and task_spec.required_output_fields:
        required = task_spec.required_output_fields
        present = sum(1 for field in required if _field_present(prediction.output_payload, field))
        field_score = present / len(required)

    overlap_score: float | None = None
    if gold.rubric or prediction.rubric_items:
        _p, _r, overlap_score = f1_precision_recall(gold.rubric, prediction.rubric_items)
    if overlap_score is None:
        return clamp01(field_score)
    return clamp01(mean((field_score, overlap_score)))


def _logical_reasoning_score(prediction: _InternalPrediction | None, gold: GoldExample) -> float:
    if prediction is None:
        return 0.0
    if prediction.reasoning_score is not None:
        return clamp01(prediction.reasoning_score)
    _p, _r, f1 = f1_precision_recall(gold.expected_reasoning_skills, prediction.reasoning_skills)
    return clamp01(f1)


def _normalize_score_distance(predicted: float | None, expected: float | None) -> float:
    if predicted is None or expected is None:
        return 0.0
    return clamp01(1.0 - min(1.0, abs(predicted - expected) / 4.0))


def _argument_quality_score(
    prediction: _InternalPrediction | None,
    gold: GoldExample,
    logical_reasoning: float,
) -> float:
    if prediction is None:
        return logical_reasoning
    raw_score = prediction.argument_quality_score
    if raw_score is None:
        raw_score = prediction.predicted_score
    if raw_score is None:
        return logical_reasoning
    return _normalize_score_distance(raw_score, gold.gold_score)


def _fallacy_metrics(
    prediction: _InternalPrediction | None,
    gold: GoldExample,
) -> tuple[float, float, float]:
    if prediction is None:
        return 0.0, 0.0, 0.0
    return f1_precision_recall(gold.expected_fallacies, prediction.predicted_fallacies)


def _feedback_quality_score(prediction: _InternalPrediction | None, gold: GoldExample) -> float:
    if prediction is None:
        return 0.0
    return feedback_usefulness_score(
        feedback_text=prediction.feedback_text,
        expected_reasoning_skills=gold.expected_reasoning_skills,
        rubric_items=gold.rubric,
        reviewer_notes=gold.notes_for_reviewers,
    )


def _confidence_target(
    *,
    task_id: str,
    prediction: _InternalPrediction,
    gold: GoldExample,
    task_specs: dict[str, _TaskSpec],
) -> float | None:
    if task_id == TASK_ESSAY_SCORING:
        if prediction.predicted_score is None or gold.gold_score is None:
            return None
        return 1.0 if abs(prediction.predicted_score - gold.gold_score) <= 1.0 else 0.0
    if task_id == TASK_RUBRIC_ADHERENCE:
        spec = task_specs.get(task_id)
        return _rubric_adherence_score(prediction, gold, spec)
    if task_id == TASK_LOGICAL_REASONING:
        return _logical_reasoning_score(prediction, gold)
    if task_id == TASK_ARGUMENT_QUALITY:
        logical = _logical_reasoning_score(prediction, gold)
        return _argument_quality_score(prediction, gold, logical)
    if task_id == TASK_FALLACY_IDENTIFICATION:
        _p, _r, f1 = _fallacy_metrics(prediction, gold)
        return f1
    if task_id == TASK_EDUCATIONAL_FEEDBACK:
        return _feedback_quality_score(prediction, gold)
    return None


def _model_consistency(
    *,
    model_buckets: dict[tuple[str, str], list[_InternalPrediction]],
) -> float:
    norm_stds: list[float] = []
    for (_example_id, task_id), rows in model_buckets.items():
        if task_id != TASK_ESSAY_SCORING:
            continue
        numeric = [row.predicted_score for row in rows if row.predicted_score is not None]
        if len(numeric) < 2:
            continue
        std = pstdev(numeric)
        norm_stds.append(clamp01(std / 4.0))
    if not norm_stds:
        return 1.0
    return clamp01(1.0 - mean(norm_stds))


def evaluate_model_against_gold(
    model_id: str,
    gold_examples: list[GoldExample],
    model_buckets: dict[tuple[str, str], list[_InternalPrediction]],
    task_specs: dict[str, _TaskSpec],
) -> tuple[list[PerExampleMetricRow], ModelSummary]:
    """Evaluate one model against full gold set."""
    rows: list[PerExampleMetricRow] = []

    score_true: list[float] = []
    score_pred: list[float] = []
    score_abs_errors: list[float] = []
    rubric_scores: list[float] = []
    reasoning_scores: list[float] = []
    argument_scores: list[float] = []
    fallacy_precisions: list[float] = []
    fallacy_recalls: list[float] = []
    fallacy_f1s: list[float] = []
    feedback_scores: list[float] = []
    latencies: list[float] = []
    json_flags: list[float] = []
    input_tokens_total = 0
    output_tokens_total = 0
    cost_values: list[float] = []
    examples_with_prediction = 0
    calibration_confidences: list[float] = []
    calibration_targets: list[float] = []

    for gold in gold_examples:
        selected_by_task: dict[str, _InternalPrediction] = {}
        per_example_predictions: list[_InternalPrediction] = []
        for task_id in (
            TASK_ESSAY_SCORING,
            TASK_RUBRIC_ADHERENCE,
            TASK_LOGICAL_REASONING,
            TASK_ARGUMENT_QUALITY,
            TASK_FALLACY_IDENTIFICATION,
            TASK_EDUCATIONAL_FEEDBACK,
        ):
            bucket = model_buckets.get((gold.example_id, task_id), [])
            if not bucket:
                continue
            chosen = _select_primary(bucket)
            selected_by_task[task_id] = chosen
            per_example_predictions.append(chosen)

        if per_example_predictions:
            examples_with_prediction += 1

        essay = selected_by_task.get(TASK_ESSAY_SCORING)
        rubric = selected_by_task.get(TASK_RUBRIC_ADHERENCE)
        reasoning = selected_by_task.get(TASK_LOGICAL_REASONING)
        argument = selected_by_task.get(TASK_ARGUMENT_QUALITY)
        fallacy = selected_by_task.get(TASK_FALLACY_IDENTIFICATION)
        feedback = selected_by_task.get(TASK_EDUCATIONAL_FEEDBACK)

        score_abs_error: float | None = None
        if essay and essay.predicted_score is not None and gold.gold_score is not None:
            score_abs_error = abs(gold.gold_score - essay.predicted_score)
            score_true.append(gold.gold_score)
            score_pred.append(essay.predicted_score)
            score_abs_errors.append(score_abs_error)

        rubric_adherence = _rubric_adherence_score(
            rubric,
            gold,
            task_specs.get(TASK_RUBRIC_ADHERENCE),
        )
        logical_reasoning = _logical_reasoning_score(reasoning, gold)
        argument_quality = _argument_quality_score(argument, gold, logical_reasoning)
        fallacy_precision, fallacy_recall, fallacy_f1 = _fallacy_metrics(fallacy, gold)
        feedback_quality = _feedback_quality_score(feedback, gold)

        rubric_scores.append(rubric_adherence)
        reasoning_scores.append(logical_reasoning)
        argument_scores.append(argument_quality)
        fallacy_precisions.append(fallacy_precision)
        fallacy_recalls.append(fallacy_recall)
        fallacy_f1s.append(fallacy_f1)
        feedback_scores.append(feedback_quality)

        if per_example_predictions:
            json_valid = all(item.json_valid for item in per_example_predictions)
            json_flags.extend(1.0 if item.json_valid else 0.0 for item in per_example_predictions)

            task_latencies = [
                item.latency_ms for item in per_example_predictions if item.latency_ms is not None
            ]
            latency_ms = mean(task_latencies) if task_latencies else None
            if latency_ms is not None:
                latencies.extend(task_latencies)
            input_tokens = sum(item.input_tokens for item in per_example_predictions)
            output_tokens = sum(item.output_tokens for item in per_example_predictions)
            cost = sum(item.cost_usd or 0.0 for item in per_example_predictions)
            cost_value: float | None = cost if cost > 0 else None
            confidences = [
                item.confidence for item in per_example_predictions if item.confidence is not None
            ]
            confidence_mean = mean(confidences) if confidences else None
            missing_tasks = [
                task_id
                for task_id in (
                    TASK_ESSAY_SCORING,
                    TASK_RUBRIC_ADHERENCE,
                    TASK_LOGICAL_REASONING,
                    TASK_FALLACY_IDENTIFICATION,
                    TASK_EDUCATIONAL_FEEDBACK,
                )
                if task_id not in selected_by_task
            ]
        else:
            json_valid = False
            latency_ms = None
            input_tokens = 0
            output_tokens = 0
            cost_value = None
            confidence_mean = None
            missing_tasks = [
                TASK_ESSAY_SCORING,
                TASK_RUBRIC_ADHERENCE,
                TASK_LOGICAL_REASONING,
                TASK_FALLACY_IDENTIFICATION,
                TASK_EDUCATIONAL_FEEDBACK,
            ]

        input_tokens_total += input_tokens
        output_tokens_total += output_tokens
        if cost_value is not None:
            cost_values.append(cost_value)

        for task_id, prediction in selected_by_task.items():
            if prediction.confidence is None:
                continue
            target = _confidence_target(
                task_id=task_id,
                prediction=prediction,
                gold=gold,
                task_specs=task_specs,
            )
            if target is None:
                continue
            calibration_confidences.append(prediction.confidence)
            calibration_targets.append(clamp01(target))

        rows.append(
            PerExampleMetricRow(
                model_id=model_id,
                example_id=gold.example_id,
                source=gold.source,
                difficulty=gold.difficulty,
                score_abs_error=score_abs_error,
                rubric_adherence=rubric_adherence,
                logical_reasoning=logical_reasoning,
                argument_quality=argument_quality,
                fallacy_precision=fallacy_precision,
                fallacy_recall=fallacy_recall,
                fallacy_f1=fallacy_f1,
                educational_feedback=feedback_quality,
                json_valid=json_valid,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                cost_usd=cost_value,
                confidence_mean=confidence_mean,
                tasks_covered=len(per_example_predictions),
                missing_prediction=not bool(per_example_predictions),
                notes="missing_tasks:" + ",".join(missing_tasks) if missing_tasks else "",
            )
        )

    total_examples = len(gold_examples)
    coverage = examples_with_prediction / total_examples if total_examples else 0.0

    latencies_sorted = sorted(latencies)
    avg_latency_ms = mean(latencies) if latencies else 0.0
    p50_latency_ms = percentile(latencies_sorted, 50) if latencies else 0.0
    p95_latency_ms = percentile(latencies_sorted, 95) if latencies else 0.0
    cost_total = sum(cost_values)

    temperature, _nll_before, _nll_after = fit_temperature_scaling(
        calibration_confidences,
        calibration_targets,
    )
    calibrated = [
        temperature_scale_confidence(value, temperature) for value in calibration_confidences
    ]
    calibration_ece_before = expected_calibration_error(
        calibration_confidences,
        calibration_targets,
    )
    calibration_ece_after = expected_calibration_error(
        calibrated,
        calibration_targets,
    )
    calibration_brier_before = brier_score(
        calibration_confidences,
        calibration_targets,
    )
    calibration_brier_after = brier_score(
        calibrated,
        calibration_targets,
    )

    summary = ModelSummary(
        model_id=model_id,
        examples_total=total_examples,
        examples_with_prediction=examples_with_prediction,
        coverage=coverage,
        score_prediction_qwk=quadratic_weighted_kappa(score_true, score_pred),
        score_prediction_mae=mae(score_true, score_pred),
        rubric_adherence=mean(rubric_scores) if rubric_scores else 0.0,
        logical_reasoning=mean(reasoning_scores) if reasoning_scores else 0.0,
        argument_quality=mean(argument_scores) if argument_scores else 0.0,
        fallacy_precision=mean(fallacy_precisions) if fallacy_precisions else 0.0,
        fallacy_recall=mean(fallacy_recalls) if fallacy_recalls else 0.0,
        fallacy_f1=mean(fallacy_f1s) if fallacy_f1s else 0.0,
        educational_feedback=mean(feedback_scores) if feedback_scores else 0.0,
        json_validity=mean(json_flags) if json_flags else 0.0,
        avg_latency_ms=avg_latency_ms,
        p50_latency_ms=p50_latency_ms,
        p95_latency_ms=p95_latency_ms,
        input_tokens_total=input_tokens_total,
        output_tokens_total=output_tokens_total,
        total_tokens_total=input_tokens_total + output_tokens_total,
        cost_total_usd=cost_total,
        cost_per_example_usd=(
            cost_total / examples_with_prediction
            if examples_with_prediction
            else 0.0
        ),
        agreement=0.0,
        consistency=_model_consistency(model_buckets=model_buckets),
        calibration_temperature=temperature,
        calibration_ece_before=calibration_ece_before,
        calibration_ece_after=calibration_ece_after,
        calibration_brier_before=calibration_brier_before,
        calibration_brier_after=calibration_brier_after,
        rank_score=0.0,
        rank=0,
    )
    return rows, summary


def _pairwise_agreement(
    left: dict[tuple[str, str], _InternalPrediction],
    right: dict[tuple[str, str], _InternalPrediction],
) -> float | None:
    example_ids = sorted(
        {
            example_id
            for (example_id, task_id) in left.keys() | right.keys()
            if task_id in {TASK_ESSAY_SCORING, TASK_FALLACY_IDENTIFICATION}
        }
    )
    values: list[float] = []
    for example_id in example_ids:
        essay_left = left.get((example_id, TASK_ESSAY_SCORING))
        essay_right = right.get((example_id, TASK_ESSAY_SCORING))
        if essay_left and essay_right:
            if essay_left.predicted_score is not None and essay_right.predicted_score is not None:
                diff = abs(essay_left.predicted_score - essay_right.predicted_score)
                values.append(clamp01(1.0 - min(1.0, diff / 4.0)))

        fallacy_left = left.get((example_id, TASK_FALLACY_IDENTIFICATION))
        fallacy_right = right.get((example_id, TASK_FALLACY_IDENTIFICATION))
        if fallacy_left and fallacy_right:
            _p, _r, f1 = f1_precision_recall(
                fallacy_left.predicted_fallacies,
                fallacy_right.predicted_fallacies,
            )
            values.append(f1)

    if not values:
        return None
    return mean(values)


def _agreement_matrix(
    primary_maps: dict[str, dict[tuple[str, str], _InternalPrediction]],
    model_ids: tuple[str, ...],
) -> tuple[dict[str, dict[str, float | None]], dict[str, float]]:
    matrix: dict[str, dict[str, float | None]] = {}
    per_model: dict[str, float] = {}
    for model in model_ids:
        matrix[model] = {}
        pair_values: list[float] = []
        for other in model_ids:
            if model == other:
                matrix[model][other] = 1.0
                continue
            score = _pairwise_agreement(
                primary_maps.get(model, {}),
                primary_maps.get(other, {}),
            )
            matrix[model][other] = score
            if score is not None:
                pair_values.append(score)
        per_model[model] = mean(pair_values) if pair_values else 0.0
    return matrix, per_model


def _leaderboard_score(row: ModelSummary) -> float:
    qwk_score = clamp01((row.score_prediction_qwk + 1.0) / 2.0)
    mae_score = clamp01(1.0 - min(1.0, row.score_prediction_mae / 4.0))
    calibration_score = (
        clamp01(1.0 - row.calibration_ece_after)
        if row.calibration_ece_after is not None
        else 0.0
    )
    return (
        0.20 * qwk_score
        + 0.10 * mae_score
        + 0.10 * row.rubric_adherence
        + 0.10 * row.logical_reasoning
        + 0.15 * row.fallacy_f1
        + 0.10 * row.educational_feedback
        + 0.10 * row.json_validity
        + 0.05 * row.agreement
        + 0.05 * row.consistency
        + 0.05 * calibration_score
    )


def run_benchmark(
    *,
    gold_examples: list[GoldExample],
    predictions: list[PredictionRecord],
    model_ids: tuple[str, ...],
) -> tuple[list[PerExampleMetricRow], list[ModelSummary], dict[str, Any]]:
    """Run benchmark for selected (or configured) models."""
    if not gold_examples:
        raise ValueError("gold_examples is empty.")

    task_specs = _task_specs()
    internal_predictions = [_prediction_to_internal(item) for item in predictions]

    requested = list(model_ids)
    if not requested:
        requested = list(_configured_models())

    resolved_model_ids: list[str] = []
    for model in requested:
        resolved = _canonical_or_none(model)
        if resolved is None:
            continue
        if resolved not in resolved_model_ids:
            resolved_model_ids.append(resolved)
    if not resolved_model_ids:
        resolved_model_ids = list(_configured_models())

    by_model: dict[str, dict[tuple[str, str], list[_InternalPrediction]]] = {}
    for prediction in internal_predictions:
        if prediction.model_id not in resolved_model_ids:
            continue
        bucket = by_model.setdefault(prediction.model_id, {})
        bucket.setdefault((prediction.example_id, prediction.task_id), []).append(prediction)

    all_rows: list[PerExampleMetricRow] = []
    summaries: list[ModelSummary] = []
    primary_maps: dict[str, dict[tuple[str, str], _InternalPrediction]] = {}

    for model_id in resolved_model_ids:
        model_buckets = by_model.get(model_id, {})
        rows, summary = evaluate_model_against_gold(
            model_id=model_id,
            gold_examples=gold_examples,
            model_buckets=model_buckets,
            task_specs=task_specs,
        )
        all_rows.extend(rows)
        summaries.append(summary)
        primary_maps[model_id] = {
            key: _select_primary(values) for key, values in model_buckets.items() if values
        }

    agreement_matrix, agreement_per_model = _agreement_matrix(
        primary_maps=primary_maps,
        model_ids=tuple(resolved_model_ids),
    )
    summaries = [
        replace(
            item,
            agreement=agreement_per_model.get(item.model_id, 0.0),
            rank_score=_leaderboard_score(
                replace(item, agreement=agreement_per_model.get(item.model_id, 0.0))
            ),
        )
        for item in summaries
    ]

    ranked = sorted(
        summaries,
        key=lambda item: (
            -item.rank_score,
            -item.score_prediction_qwk,
            item.score_prediction_mae,
            item.cost_per_example_usd,
        ),
    )
    ranked = [replace(item, rank=index) for index, item in enumerate(ranked, start=1)]

    cost_table = [
        {
            "model_id": item.model_id,
            "rank": item.rank,
            "cost_total_usd": item.cost_total_usd,
            "cost_per_example_usd": item.cost_per_example_usd,
            "input_tokens_total": item.input_tokens_total,
            "output_tokens_total": item.output_tokens_total,
            "total_tokens_total": item.total_tokens_total,
        }
        for item in ranked
    ]
    latency_table = [
        {
            "model_id": item.model_id,
            "rank": item.rank,
            "avg_latency_ms": item.avg_latency_ms,
            "p50_latency_ms": item.p50_latency_ms,
            "p95_latency_ms": item.p95_latency_ms,
        }
        for item in ranked
    ]
    calibration_table = [
        {
            "model_id": item.model_id,
            "rank": item.rank,
            "temperature": item.calibration_temperature,
            "ece_before": item.calibration_ece_before,
            "ece_after": item.calibration_ece_after,
            "brier_before": item.calibration_brier_before,
            "brier_after": item.calibration_brier_after,
        }
        for item in ranked
    ]

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "gold_examples": len(gold_examples),
        "predictions_loaded": len(predictions),
        "models_evaluated": [item.model_id for item in ranked],
        "summary_count": len(ranked),
        "outputs": {
            "leaderboard": "leaderboard.json",
            "cost_table": "cost_table.json",
            "latency_table": "latency_table.json",
            "agreement_matrix": "agreement_matrix.json",
            "confidence_calibration": "confidence_calibration.json",
        },
        "leaderboard": [asdict(item) for item in ranked],
        "cost_table": cost_table,
        "latency_table": latency_table,
        "agreement_matrix": agreement_matrix,
        "confidence_calibration": calibration_table,
    }
    return all_rows, ranked, manifest


def _json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = sorted({key for row in rows for key in row.keys()})
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _render_markdown_report(run_id: str, manifest: dict[str, Any]) -> str:
    leaderboard = manifest.get("leaderboard", [])
    cost_table = manifest.get("cost_table", [])
    latency_table = manifest.get("latency_table", [])
    calibration_table = manifest.get("confidence_calibration", [])

    lines = [
        "# Teacher Benchmark Report",
        "",
        f"- run_id: `{run_id}`",
        f"- generated_at_utc: `{manifest.get('generated_at_utc', '')}`",
        f"- gold_examples: `{manifest.get('gold_examples', 0)}`",
        f"- predictions_loaded: `{manifest.get('predictions_loaded', 0)}`",
        "",
        "## Leaderboard",
        "",
        (
            "| rank | model | rank_score | qwk | mae | rubric | reasoning | "
            "fallacy_f1 | feedback | agreement | consistency | json_validity |"
        ),
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in leaderboard:
        lines.append(
            f"| {row.get('rank', 0)} | {row.get('model_id', '')} "
            f"| {float(row.get('rank_score', 0.0)):.4f} "
            f"| {float(row.get('score_prediction_qwk', 0.0)):.4f} "
            f"| {float(row.get('score_prediction_mae', 0.0)):.4f} "
            f"| {float(row.get('rubric_adherence', 0.0)):.4f} "
            f"| {float(row.get('logical_reasoning', 0.0)):.4f} "
            f"| {float(row.get('fallacy_f1', 0.0)):.4f} "
            f"| {float(row.get('educational_feedback', 0.0)):.4f} "
            f"| {float(row.get('agreement', 0.0)):.4f} "
            f"| {float(row.get('consistency', 0.0)):.4f} "
            f"| {float(row.get('json_validity', 0.0)):.4f} |"
        )

    lines.extend(
        [
            "",
            "## Cost Table",
            "",
            "| rank | model | total_cost_usd | cost_per_example_usd | total_tokens |",
            "|---:|---|---:|---:|---:|",
        ]
    )
    for row in cost_table:
        lines.append(
            f"| {row.get('rank', 0)} | {row.get('model_id', '')} "
            f"| {float(row.get('cost_total_usd', 0.0)):.6f} "
            f"| {float(row.get('cost_per_example_usd', 0.0)):.6f} "
            f"| {int(row.get('total_tokens_total', 0) or 0)} |"
        )

    lines.extend(
        [
            "",
            "## Latency Table",
            "",
            "| rank | model | avg_latency_ms | p50_latency_ms | p95_latency_ms |",
            "|---:|---|---:|---:|---:|",
        ]
    )
    for row in latency_table:
        lines.append(
            f"| {row.get('rank', 0)} | {row.get('model_id', '')} "
            f"| {float(row.get('avg_latency_ms', 0.0)):.2f} "
            f"| {float(row.get('p50_latency_ms', 0.0)):.2f} "
            f"| {float(row.get('p95_latency_ms', 0.0)):.2f} |"
        )

    lines.extend(
        [
            "",
            "## Confidence Calibration",
            "",
            "| rank | model | temperature | ece_before | ece_after | brier_before | brier_after |",
            "|---:|---|---:|---:|---:|---:|---:|",
        ]
    )
    for row in calibration_table:
        ece_before = row.get("ece_before")
        ece_after = row.get("ece_after")
        brier_before = row.get("brier_before")
        brier_after = row.get("brier_after")
        lines.append(
            f"| {row.get('rank', 0)} | {row.get('model_id', '')} "
            f"| {float(row.get('temperature', 1.0)):.4f} "
            f"| {float(ece_before):.4f} | {float(ece_after):.4f} "
            f"| {float(brier_before):.4f} | {float(brier_after):.4f} |"
            if ece_before is not None
            and ece_after is not None
            and brier_before is not None
            and brier_after is not None
            else (
                f"| {row.get('rank', 0)} | {row.get('model_id', '')} "
                f"| {float(row.get('temperature', 1.0)):.4f} | n/a | n/a | n/a | n/a |"
            )
        )

    lines.extend(
        [
            "",
            "## Agreement Matrix",
            "",
            "See `agreement_matrix.csv` and `agreement_matrix.json` for full pairwise values.",
            "",
        ]
    )
    return "\n".join(lines)


def write_benchmark_outputs(
    *,
    output_dir: Path,
    run_id: str,
    per_example_rows: list[PerExampleMetricRow],
    summaries: list[ModelSummary],
    manifest: dict[str, Any],
) -> None:
    """Write benchmark artifacts to output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)

    leaderboard_rows = [asdict(item) for item in summaries]
    cost_rows = [
        {
            "model_id": item.model_id,
            "rank": item.rank,
            "cost_total_usd": item.cost_total_usd,
            "cost_per_example_usd": item.cost_per_example_usd,
            "input_tokens_total": item.input_tokens_total,
            "output_tokens_total": item.output_tokens_total,
            "total_tokens_total": item.total_tokens_total,
        }
        for item in summaries
    ]
    latency_rows = [
        {
            "model_id": item.model_id,
            "rank": item.rank,
            "avg_latency_ms": item.avg_latency_ms,
            "p50_latency_ms": item.p50_latency_ms,
            "p95_latency_ms": item.p95_latency_ms,
        }
        for item in summaries
    ]
    calibration_rows = [
        {
            "model_id": item.model_id,
            "rank": item.rank,
            "temperature": item.calibration_temperature,
            "ece_before": item.calibration_ece_before,
            "ece_after": item.calibration_ece_after,
            "brier_before": item.calibration_brier_before,
            "brier_after": item.calibration_brier_after,
        }
        for item in summaries
    ]

    agreement_matrix = manifest.get("agreement_matrix", {})
    agreement_csv_rows: list[dict[str, Any]] = []
    if isinstance(agreement_matrix, dict):
        model_ids = sorted(agreement_matrix.keys())
        for model_id in model_ids:
            row: dict[str, Any] = {"model_id": model_id}
            peers = agreement_matrix.get(model_id, {})
            if isinstance(peers, dict):
                for peer_id in model_ids:
                    row[peer_id] = peers.get(peer_id)
            agreement_csv_rows.append(row)

    (output_dir / "manifest.json").write_text(_json_dumps(manifest) + "\n", encoding="utf-8")
    (output_dir / "model_summary.json").write_text(
        _json_dumps(leaderboard_rows) + "\n",
        encoding="utf-8",
    )
    (output_dir / "leaderboard.json").write_text(
        _json_dumps(leaderboard_rows) + "\n",
        encoding="utf-8",
    )
    (output_dir / "cost_table.json").write_text(_json_dumps(cost_rows) + "\n", encoding="utf-8")
    (output_dir / "latency_table.json").write_text(
        _json_dumps(latency_rows) + "\n",
        encoding="utf-8",
    )
    (output_dir / "confidence_calibration.json").write_text(
        _json_dumps(calibration_rows) + "\n",
        encoding="utf-8",
    )
    (output_dir / "agreement_matrix.json").write_text(
        _json_dumps(agreement_matrix) + "\n",
        encoding="utf-8",
    )

    _write_csv(output_dir / "model_summary.csv", leaderboard_rows)
    _write_csv(output_dir / "leaderboard.csv", leaderboard_rows)
    _write_csv(output_dir / "cost_table.csv", cost_rows)
    _write_csv(output_dir / "latency_table.csv", latency_rows)
    _write_csv(output_dir / "confidence_calibration.csv", calibration_rows)
    if agreement_csv_rows:
        _write_csv(output_dir / "agreement_matrix.csv", agreement_csv_rows)

    with (output_dir / "per_example_metrics.jsonl").open("w", encoding="utf-8") as handle:
        for row in per_example_rows:
            handle.write(_json_dumps(asdict(row)) + "\n")

    report_md = _render_markdown_report(run_id=run_id, manifest=manifest)
    (output_dir / "report.md").write_text(report_md, encoding="utf-8")
