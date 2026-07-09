"""Run ensemble aggregation over existing teacher-run outputs.

Supported strategies:
- majority vote
- weighted vote
- score averaging
- teacher + verifier
- teacher + judge

Inputs:
- configs under `configs/teacher/`
- existing responses under `outputs/teacher_runs/<source_run_id>/responses.jsonl`

This module does not call provider APIs and does not execute model inference.
"""

from __future__ import annotations

import argparse
import copy
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

_CRITERIA_ORDER = ("claim", "evidence", "reasoning", "organization", "style")
_JUDGMENT_ORDER = ("meets", "partially_meets", "does_not_meet")
_NONE_FALLACY = {"", "none", "no_fallacy", "no_fallacy_detected"}
_UNSUPPORTED_FEEDBACK_PATTERNS = (
    re.compile(r"\byour teacher said\b", re.IGNORECASE),
    re.compile(r"\baccording to (the )?data table\b", re.IGNORECASE),
)


@dataclass(frozen=True)
class CaseKey:
    """Stable key for one comparable response case."""

    task_id: str
    example_id: str
    seed: int
    temperature: float
    prompt_version: str


@dataclass(frozen=True)
class TeacherResponse:
    """Normalized response row from teacher-runs output."""

    model: str
    task_id: str
    example_id: str
    seed: int
    temperature: float
    prompt_version: str
    confidence: float | None
    latency_ms: float | None
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    output_json: dict[str, Any] | None
    output_parse_error: str | None
    raw: dict[str, Any]

    @property
    def case_key(self) -> CaseKey:
        return CaseKey(
            task_id=self.task_id,
            example_id=self.example_id,
            seed=self.seed,
            temperature=self.temperature,
            prompt_version=self.prompt_version,
        )


@dataclass(frozen=True)
class EnsembleOutput:
    """One ensemble-generated output row."""

    run_id: str
    source_run_id: str
    strategy: str
    ensemble_id: str
    task_id: str
    example_id: str
    seed: int
    temperature: float
    prompt_version: str
    member_models: tuple[str, ...]
    output_json: dict[str, Any] | None
    confidence: float | None
    status: str
    notes: tuple[str, ...]
    latency_ms: float | None
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    member_trace: tuple[dict[str, Any], ...]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("teacher-ensembles-%Y%m%dT%H%M%SZ")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL row is not object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    number = _safe_float(value)
    if number is None:
        return default
    return int(number)


def _normalize_label(value: Any) -> str:
    text = " ".join(str(value or "").strip().lower().replace("-", " ").split())
    return text.replace(" ", "_")


def _normalize_confidence(value: Any) -> float | None:
    score = _safe_float(value)
    if score is None:
        return None
    if score > 1.0:
        score = score / 100.0
    return max(0.0, min(1.0, score))


def _extract_score(output_json: dict[str, Any] | None) -> float | None:
    if not isinstance(output_json, dict):
        return None
    for key in ("score", "predicted_score", "score_prediction"):
        score = _safe_float(output_json.get(key))
        if score is not None:
            return score
    return None


def _extract_fallacy(output_json: dict[str, Any] | None) -> str:
    if not isinstance(output_json, dict):
        return ""

    direct = _normalize_label(output_json.get("fallacy_label"))
    if direct:
        return direct
    nested = output_json.get("fallacies")
    if isinstance(nested, dict):
        return _normalize_label(nested.get("primary"))
    return ""


def _extract_rubric_judgments(output_json: dict[str, Any] | None) -> dict[str, str]:
    if not isinstance(output_json, dict):
        return {}
    rubric = output_json.get("rubric")
    if not isinstance(rubric, dict):
        return {}
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list):
        return {}

    result: dict[str, str] = {}
    for item in criteria:
        if not isinstance(item, dict):
            continue
        criterion = _normalize_label(item.get("criterion"))
        judgment = _normalize_label(item.get("judgment"))
        if criterion and judgment:
            result[criterion] = judgment
    return result


def _extract_task_specific_confidence(
    response: TeacherResponse,
    output_json: dict[str, Any] | None,
) -> float:
    if response.confidence is not None:
        return response.confidence
    if not isinstance(output_json, dict):
        return 0.5
    candidates = (
        output_json.get("confidence"),
        output_json.get("rubric_adherence_confidence"),
    )
    for value in candidates:
        confidence = _normalize_confidence(value)
        if confidence is not None:
            return confidence
    return 0.5


def _weighted_choice(
    items: list[tuple[str, float, float]],
) -> str:
    """Weighted mode with confidence tie-break."""
    if not items:
        return ""

    by_label: dict[str, tuple[float, float]] = {}
    for label, weight, confidence in items:
        current_weight, current_conf = by_label.get(label, (0.0, 0.0))
        by_label[label] = (current_weight + weight, max(current_conf, confidence))

    ranked = sorted(
        by_label.items(),
        key=lambda item: (-item[1][0], -item[1][1], item[0]),
    )
    return ranked[0][0]


def _aggregate_resource_cost(
    responses: list[TeacherResponse],
    *,
    sequential: bool,
) -> tuple[float | None, int, int, float | None]:
    latencies = [item.latency_ms for item in responses if item.latency_ms is not None]
    costs = [item.estimated_cost_usd for item in responses if item.estimated_cost_usd is not None]
    input_tokens = sum(item.input_tokens for item in responses)
    output_tokens = sum(item.output_tokens for item in responses)

    if latencies:
        latency_ms = sum(latencies) if sequential else max(latencies)
    else:
        latency_ms = None
    cost = sum(costs) if costs else None
    return latency_ms, input_tokens, output_tokens, cost


def _member_trace(responses: list[TeacherResponse]) -> tuple[dict[str, Any], ...]:
    trace: list[dict[str, Any]] = []
    for item in responses:
        trace.append(
            {
                "model": item.model,
                "confidence": item.confidence,
                "latency_ms": item.latency_ms,
                "input_tokens": item.input_tokens,
                "output_tokens": item.output_tokens,
                "estimated_cost_usd": item.estimated_cost_usd,
                "score": _extract_score(item.output_json),
                "fallacy": _extract_fallacy(item.output_json),
            }
        )
    return tuple(trace)


def _best_member_index(responses: list[TeacherResponse], weights: dict[str, float]) -> int:
    ranked = []
    for index, item in enumerate(responses):
        weight = weights.get(item.model, 1.0)
        confidence = item.confidence if item.confidence is not None else 0.5
        ranked.append((index, weight, confidence))
    ranked.sort(key=lambda item: (-item[1], -item[2], item[0]))
    return ranked[0][0] if ranked else 0


def _vote_score(
    responses: list[TeacherResponse],
    *,
    weights: dict[str, float] | None = None,
    weighted_average: bool = False,
) -> float | None:
    scores: list[tuple[float, float, float]] = []
    for response in responses:
        score = _extract_score(response.output_json)
        if score is None:
            continue
        confidence = response.confidence if response.confidence is not None else 0.5
        weight = (weights or {}).get(response.model, 1.0)
        scores.append((score, weight, confidence))
    if not scores:
        return None

    if weighted_average:
        numerator = sum(score * weight for score, weight, _ in scores)
        denom = sum(weight for _, weight, _ in scores)
        return numerator / denom if denom > 0 else None

    if weights is not None:
        rounded_items = [(str(int(round(score))), weight, conf) for score, weight, conf in scores]
        label = _weighted_choice(rounded_items)
        return float(int(label)) if label else None

    rounded_scores = [int(round(score)) for score, _weight, _conf in scores]
    counts: dict[int, int] = {}
    for value in rounded_scores:
        counts[value] = counts.get(value, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    top_count = ranked[0][1]
    tied = [value for value, count in ranked if count == top_count]
    if len(tied) == 1:
        return float(tied[0])

    # Tie-breaker: highest-confidence member.
    best = max(scores, key=lambda item: item[2])
    return float(int(round(best[0])))


def _aggregate_rubric(
    responses: list[TeacherResponse],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any] | None:
    criteria_votes: dict[str, list[tuple[str, float, float]]] = {
        criterion: [] for criterion in _CRITERIA_ORDER
    }
    for response in responses:
        judgments = _extract_rubric_judgments(response.output_json)
        confidence = _extract_task_specific_confidence(response, response.output_json)
        weight = (weights or {}).get(response.model, 1.0)
        for criterion in _CRITERIA_ORDER:
            judgment = judgments.get(criterion)
            if judgment:
                criteria_votes[criterion].append((judgment, weight, confidence))

    criteria_payload: list[dict[str, str]] = []
    for criterion in _CRITERIA_ORDER:
        votes = criteria_votes[criterion]
        if not votes:
            continue
        if weights is None:
            counts: dict[str, int] = {}
            best_conf: dict[str, float] = {}
            for label, _weight, conf in votes:
                counts[label] = counts.get(label, 0) + 1
                best_conf[label] = max(best_conf.get(label, 0.0), conf)
            ranked = sorted(
                counts.items(),
                key=lambda item: (
                    -item[1],
                    -best_conf.get(item[0], 0.0),
                    _JUDGMENT_ORDER.index(item[0]) if item[0] in _JUDGMENT_ORDER else 99,
                ),
            )
            chosen = ranked[0][0]
        else:
            chosen = _weighted_choice(votes)

        criteria_payload.append(
            {
                "criterion": criterion,
                "judgment": chosen,
                "evidence": "ensemble_vote",
                "impact": "aggregated_from_member_votes",
            }
        )

    if not criteria_payload:
        return None
    return {
        "criteria": criteria_payload,
        "summary": "ensemble_aggregated_rubric",
    }


def _majority_vote_output(
    responses: list[TeacherResponse],
    *,
    weights: dict[str, float] | None = None,
    weighted_vote: bool = False,
    score_average: bool = False,
) -> tuple[dict[str, Any] | None, float | None, tuple[str, ...]]:
    valid = [item for item in responses if isinstance(item.output_json, dict)]
    if not valid:
        return None, None, ("no_valid_member_outputs",)

    if score_average:
        score = _vote_score(valid, weights=weights, weighted_average=True)
    elif weighted_vote:
        score = _vote_score(valid, weights=weights, weighted_average=False)
    else:
        score = _vote_score(valid, weights=None, weighted_average=False)

    best_index = _best_member_index(valid, weights or {})
    base_output = copy.deepcopy(valid[best_index].output_json)
    if not isinstance(base_output, dict):
        base_output = {}

    confidences = [
        _extract_task_specific_confidence(item, item.output_json)
        for item in valid
    ]
    confidence = mean(confidences) if confidences else None

    if score is not None:
        base_output["score"] = int(round(score))
    if confidence is not None:
        base_output["confidence"] = max(0.0, min(1.0, confidence))

    rubric_payload = _aggregate_rubric(
        valid,
        weights=(weights if weighted_vote else None),
    )
    if rubric_payload is not None:
        base_output["rubric"] = rubric_payload

    fallacy_votes: list[tuple[str, float, float]] = []
    for item in valid:
        label = _extract_fallacy(item.output_json)
        if not label:
            continue
        fallacy_votes.append(
            (
                label,
                (weights or {}).get(item.model, 1.0),
                _extract_task_specific_confidence(item, item.output_json),
            )
        )
    if fallacy_votes:
        if weighted_vote:
            chosen = _weighted_choice(fallacy_votes)
        else:
            mode_items = [(label, 1.0, conf) for label, _weight, conf in fallacy_votes]
            chosen = _weighted_choice(mode_items)
        base_output.setdefault("fallacies", {})
        if isinstance(base_output["fallacies"], dict):
            base_output["fallacies"]["primary"] = chosen
            base_output["fallacies"]["detected"] = chosen not in _NONE_FALLACY

    notes = ("weighted_vote" if weighted_vote else "majority_vote",)
    if score_average:
        notes = ("score_averaging",)
    return base_output, confidence, notes


def _teacher_verifier_output(
    teacher: TeacherResponse,
    verifier: TeacherResponse,
) -> tuple[dict[str, Any] | None, float | None, str, tuple[str, ...]]:
    if not isinstance(teacher.output_json, dict):
        return None, None, "reject", ("teacher_output_invalid",)
    if not isinstance(verifier.output_json, dict):
        return (
            copy.deepcopy(teacher.output_json),
            teacher.confidence,
            "accept",
            ("verifier_invalid",),
        )

    teacher_score = _extract_score(teacher.output_json)
    verifier_score = _extract_score(verifier.output_json)
    score_delta = None
    if teacher_score is not None and verifier_score is not None:
        score_delta = abs(teacher_score - verifier_score)

    teacher_fallacy = _extract_fallacy(teacher.output_json)
    verifier_fallacy = _extract_fallacy(verifier.output_json)
    fallacy_conflict = (
        teacher_fallacy
        and verifier_fallacy
        and teacher_fallacy != verifier_fallacy
    )

    teacher_rubric = _extract_rubric_judgments(teacher.output_json)
    verifier_rubric = _extract_rubric_judgments(verifier.output_json)
    overlapping = set(teacher_rubric) & set(verifier_rubric)
    rubric_mismatch = 0.0
    if overlapping:
        mismatches = sum(
            1 for key in overlapping if teacher_rubric.get(key) != verifier_rubric.get(key)
        )
        rubric_mismatch = mismatches / len(overlapping)

    notes: list[str] = []
    if score_delta is not None and score_delta > 2.0:
        notes.append("score_delta_gt_2")
    if fallacy_conflict:
        notes.append("fallacy_conflict")
    if rubric_mismatch > 0.4:
        notes.append("rubric_mismatch_gt_0.4")

    output = copy.deepcopy(teacher.output_json)
    if not notes:
        status = "accept"
    elif len(notes) == 1 and notes[0] != "score_delta_gt_2":
        status = "minor_fix"
        output.setdefault("verifier_notes", [])
        if isinstance(output.get("verifier_notes"), list):
            output["verifier_notes"].extend(notes)
    else:
        status = "reject"
    return output, teacher.confidence, status, tuple(notes)


def _judge_quality_score(output_json: dict[str, Any] | None) -> float:
    if not isinstance(output_json, dict):
        return 0.0

    score = 0.0
    if _extract_score(output_json) is not None:
        score += 0.25
    rubric = output_json.get("rubric")
    if isinstance(rubric, dict):
        criteria = rubric.get("criteria")
        if isinstance(criteria, list) and len(criteria) >= 3:
            score += 0.25
    reasoning = output_json.get("reasoning")
    if isinstance(reasoning, dict):
        steps = reasoning.get("steps")
        if isinstance(steps, list) and len(steps) >= 3:
            score += 0.25
    if isinstance(output_json.get("feedback"), dict):
        score += 0.25
    return score


def _hallucination_heuristic(output_json: dict[str, Any] | None) -> float:
    if not isinstance(output_json, dict):
        return 1.0
    text = json.dumps(output_json, ensure_ascii=False).lower()
    return 1.0 if any(pattern.search(text) for pattern in _UNSUPPORTED_FEEDBACK_PATTERNS) else 0.0


def _teacher_judge_output(
    teacher: TeacherResponse,
    judge: TeacherResponse,
    gate_thresholds: dict[str, Any],
) -> tuple[dict[str, Any] | None, float | None, str, tuple[str, ...]]:
    teacher_output = teacher.output_json if isinstance(teacher.output_json, dict) else None
    judge_output = judge.output_json if isinstance(judge.output_json, dict) else None
    if teacher_output is None:
        return None, None, "reject", ("teacher_output_invalid",)

    rubric_min = _safe_float(gate_thresholds.get("rubric_adherence_min"))
    if rubric_min is None:
        rubric_min = 0.85
    json_required = bool(gate_thresholds.get("json_validity_required", True))
    hallucination_max = _safe_float(gate_thresholds.get("hallucination_rate_max"))
    if hallucination_max is None:
        hallucination_max = 0.05

    judge_rubric = _judge_quality_score(judge_output)
    judge_hall = _hallucination_heuristic(judge_output)
    judge_json_ok = judge_output is not None

    notes: list[str] = []
    if judge_rubric < rubric_min:
        notes.append("judge_rubric_below_threshold")
    if json_required and not judge_json_ok:
        notes.append("judge_json_invalid")
    if judge_hall > hallucination_max:
        notes.append("judge_hallucination_above_threshold")

    status = "accept" if not notes else "reject"
    output = copy.deepcopy(teacher_output)
    output.setdefault("judge_gate", {})
    if isinstance(output["judge_gate"], dict):
        output["judge_gate"]["judge_rubric_score"] = judge_rubric
        output["judge_gate"]["judge_hallucination_rate"] = judge_hall
        output["judge_gate"]["status"] = status
    return output, teacher.confidence, status, tuple(notes)


def _normalize_response(row: dict[str, Any]) -> TeacherResponse:
    output_json = row.get("raw_json_output")
    if not isinstance(output_json, dict):
        output_json = None
    parse_error = row.get("output_parse_error")
    if not isinstance(parse_error, str):
        parse_error = None

    return TeacherResponse(
        model=str(row.get("model", "")).strip(),
        task_id=str(row.get("task_id", "")).strip(),
        example_id=str(row.get("example_id", "")).strip(),
        seed=_safe_int(row.get("seed"), default=0),
        temperature=float(_safe_float(row.get("temperature")) or 0.0),
        prompt_version=str(row.get("prompt_version", "")).strip(),
        confidence=_normalize_confidence(row.get("confidence")),
        latency_ms=_safe_float(row.get("latency_ms")),
        input_tokens=_safe_int(row.get("input_tokens"), default=0),
        output_tokens=_safe_int(row.get("output_tokens"), default=0),
        estimated_cost_usd=_safe_float(row.get("estimated_cost_usd")),
        output_json=output_json,
        output_parse_error=parse_error,
        raw=dict(row),
    )


def _index_responses(
    responses: list[TeacherResponse],
) -> dict[str, dict[CaseKey, TeacherResponse]]:
    by_model: dict[str, dict[CaseKey, TeacherResponse]] = {}
    for item in responses:
        if not item.model or not item.task_id or not item.example_id:
            continue
        by_model.setdefault(item.model, {})[item.case_key] = item
    return by_model


def _shared_cases(
    by_model: dict[str, dict[CaseKey, TeacherResponse]],
    models: tuple[str, ...],
) -> list[list[TeacherResponse]]:
    model_maps = [by_model.get(model, {}) for model in models]
    if not model_maps or any(not mapping for mapping in model_maps):
        return []
    common = set(model_maps[0].keys())
    for mapping in model_maps[1:]:
        common &= set(mapping.keys())
    grouped: list[list[TeacherResponse]] = []
    for key in sorted(
        common,
        key=lambda item: (item.task_id, item.example_id, item.seed, item.temperature),
    ):
        grouped.append([mapping[key] for mapping in model_maps])
    return grouped


def _load_weights(path: Path | None) -> dict[str, float]:
    if path is None:
        return {}
    payload = _read_json(path)
    weights: dict[str, float] = {}
    for model, value in payload.items():
        if not isinstance(model, str):
            continue
        weight = _safe_float(value)
        if weight is None:
            continue
        weights[model] = max(0.0, weight)
    return weights


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _select_source_run(runs_root: Path, source_run_id: str | None) -> Path:
    if source_run_id:
        run_dir = runs_root / source_run_id
        if not run_dir.exists():
            raise FileNotFoundError(f"Source run not found: {run_dir}")
        return run_dir

    candidates = [
        path
        for path in runs_root.iterdir()
        if path.is_dir() and (path / "responses.jsonl").exists()
    ]
    if not candidates:
        raise FileNotFoundError(f"No run directories with responses.jsonl found under: {runs_root}")
    candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
    return candidates[0]


def run_ensembles(
    *,
    config_root: Path,
    runs_root: Path,
    output_root: Path,
    source_run_id: str | None,
    run_id: str,
    weights: dict[str, float],
) -> dict[str, Any]:
    """Execute ensemble aggregation using config-driven strategies."""
    ensembles_cfg = _read_json(config_root / "teacher_ensembles_v1.json")
    source_run_dir = _select_source_run(runs_root, source_run_id=source_run_id)
    source_id = source_run_dir.name
    responses_rows = _read_jsonl(source_run_dir / "responses.jsonl")
    responses = [_normalize_response(row) for row in responses_rows]
    by_model = _index_responses(responses)

    strategies = ensembles_cfg.get("strategies")
    planned = ensembles_cfg.get("planned_comparisons")
    if not isinstance(strategies, list) or not isinstance(planned, dict):
        raise ValueError("Invalid ensemble config structure.")

    strategy_index = {
        str(item.get("strategy_id")): item
        for item in strategies
        if isinstance(item, dict) and isinstance(item.get("strategy_id"), str)
    }
    judge_thresholds = {}
    judge_strategy = strategy_index.get("teacher_judge_pipeline")
    if isinstance(judge_strategy, dict):
        thresholds = judge_strategy.get("gate_thresholds")
        if isinstance(thresholds, dict):
            judge_thresholds = dict(thresholds)

    outputs: list[EnsembleOutput] = []

    # majority vote and score averaging triplets
    triplets_raw = planned.get("three_teacher_majority_vote_triplets")
    triplets: list[tuple[str, str, str]] = []
    if isinstance(triplets_raw, list):
        for item in triplets_raw:
            if isinstance(item, list) and len(item) == 3 and all(isinstance(v, str) for v in item):
                triplets.append((item[0], item[1], item[2]))

    for models in triplets:
        shared = _shared_cases(by_model, models=models)
        ensemble_label = "+".join(models)
        for group in shared:
            key = group[0].case_key
            latency_ms, in_tokens, out_tokens, cost = _aggregate_resource_cost(
                group,
                sequential=False,
            )

            for strategy_name, is_weighted, is_score_avg in (
                ("majority_vote", False, False),
                ("weighted_vote", True, False),
                ("score_averaging", True, True),
            ):
                output_json, confidence, notes = _majority_vote_output(
                    group,
                    weights=weights,
                    weighted_vote=is_weighted,
                    score_average=is_score_avg,
                )
                outputs.append(
                    EnsembleOutput(
                        run_id=run_id,
                        source_run_id=source_id,
                        strategy=strategy_name,
                        ensemble_id=f"{strategy_name}:{ensemble_label}",
                        task_id=key.task_id,
                        example_id=key.example_id,
                        seed=key.seed,
                        temperature=key.temperature,
                        prompt_version=key.prompt_version,
                        member_models=models,
                        output_json=output_json,
                        confidence=confidence,
                        status="ok" if output_json is not None else "empty",
                        notes=notes,
                        latency_ms=latency_ms,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                        estimated_cost_usd=cost,
                        member_trace=_member_trace(group),
                    )
                )

    # teacher + verifier
    verifier_pairs = planned.get("teacher_verifier_pairs")
    if isinstance(verifier_pairs, list):
        for pair in verifier_pairs:
            if not isinstance(pair, dict):
                continue
            teacher = pair.get("teacher")
            verifier = pair.get("verifier")
            if not isinstance(teacher, str) or not isinstance(verifier, str):
                continue
            models = (teacher, verifier)
            shared = _shared_cases(by_model, models=models)
            ensemble_label = f"{teacher}+{verifier}"
            for group in shared:
                key = group[0].case_key
                output_json, confidence, status, notes = _teacher_verifier_output(
                    teacher=group[0],
                    verifier=group[1],
                )
                latency_ms, in_tokens, out_tokens, cost = _aggregate_resource_cost(
                    group,
                    sequential=True,
                )
                outputs.append(
                    EnsembleOutput(
                        run_id=run_id,
                        source_run_id=source_id,
                        strategy="teacher_plus_verifier",
                        ensemble_id=f"teacher_plus_verifier:{ensemble_label}",
                        task_id=key.task_id,
                        example_id=key.example_id,
                        seed=key.seed,
                        temperature=key.temperature,
                        prompt_version=key.prompt_version,
                        member_models=models,
                        output_json=output_json,
                        confidence=confidence,
                        status=status,
                        notes=notes,
                        latency_ms=latency_ms,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                        estimated_cost_usd=cost,
                        member_trace=_member_trace(group),
                    )
                )

    # teacher + judge
    judge_pairs = planned.get("teacher_judge_pairs")
    if isinstance(judge_pairs, list):
        for pair in judge_pairs:
            if not isinstance(pair, dict):
                continue
            teacher = pair.get("teacher")
            judge = pair.get("judge")
            if not isinstance(teacher, str) or not isinstance(judge, str):
                continue
            models = (teacher, judge)
            shared = _shared_cases(by_model, models=models)
            ensemble_label = f"{teacher}+{judge}"
            for group in shared:
                key = group[0].case_key
                output_json, confidence, status, notes = _teacher_judge_output(
                    teacher=group[0],
                    judge=group[1],
                    gate_thresholds=judge_thresholds,
                )
                latency_ms, in_tokens, out_tokens, cost = _aggregate_resource_cost(
                    group,
                    sequential=True,
                )
                outputs.append(
                    EnsembleOutput(
                        run_id=run_id,
                        source_run_id=source_id,
                        strategy="teacher_plus_judge",
                        ensemble_id=f"teacher_plus_judge:{ensemble_label}",
                        task_id=key.task_id,
                        example_id=key.example_id,
                        seed=key.seed,
                        temperature=key.temperature,
                        prompt_version=key.prompt_version,
                        member_models=models,
                        output_json=output_json,
                        confidence=confidence,
                        status=status,
                        notes=notes,
                        latency_ms=latency_ms,
                        input_tokens=in_tokens,
                        output_tokens=out_tokens,
                        estimated_cost_usd=cost,
                        member_trace=_member_trace(group),
                    )
                )

    out_dir = output_root / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(item) for item in outputs]
    _write_jsonl(out_dir / "ensemble_outputs.jsonl", rows)

    by_strategy: dict[str, int] = {}
    by_status: dict[str, int] = {}
    for item in outputs:
        by_strategy[item.strategy] = by_strategy.get(item.strategy, 0) + 1
        by_status[item.status] = by_status.get(item.status, 0) + 1

    summary = {
        "run_id": run_id,
        "created_at": _utc_now(),
        "source_run_id": source_id,
        "source_responses": len(responses),
        "ensemble_outputs": len(outputs),
        "strategies_emitted": sorted(by_strategy.keys()),
        "counts_by_strategy": by_strategy,
        "counts_by_status": by_status,
        "output_dir": str(out_dir),
        "weights_used": weights,
        "supports": [
            "majority_vote",
            "weighted_vote",
            "score_averaging",
            "teacher_plus_verifier",
            "teacher_plus_judge",
        ],
    }
    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run teacher ensemble aggregations.")
    parser.add_argument("--config-root", default="configs/teacher")
    parser.add_argument("--runs-root", default="outputs/teacher_runs")
    parser.add_argument("--output-root", default="outputs/teacher_runs/ensembles")
    parser.add_argument("--source-run-id", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--weights-json",
        default=None,
        help="Optional JSON object mapping model_id -> weight for weighted strategies.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    run_id = args.run_id or _default_run_id()
    weights = _load_weights(Path(args.weights_json)) if args.weights_json else {}
    summary = run_ensembles(
        config_root=Path(args.config_root),
        runs_root=Path(args.runs_root),
        output_root=Path(args.output_root),
        source_run_id=args.source_run_id,
        run_id=run_id,
        weights=weights,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
