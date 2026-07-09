"""Automatic validation checks for teacher-model outputs.

This module validates precomputed teacher outputs and does not call provider APIs.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from .io import GoldExample, PredictionRecord

ALLOWED_RUBRIC_CRITERIA: tuple[str, ...] = (
    "claim",
    "evidence",
    "reasoning",
    "organization",
    "style",
)

REQUIRED_STRUCTURE: dict[str, Any] = {
    "score": int,
    "confidence": (int, float),
    "rubric": {
        "criteria": list,
        "summary": str,
    },
    "reasoning": {
        "summary": str,
        "steps": list,
    },
    "logical_analysis": {
        "claim_quality": str,
        "evidence_quality": str,
        "coherence": str,
        "counterargument_handling": str,
        "consistency_checks": list,
    },
    "fallacies": {
        "detected": bool,
        "primary": str,
        "secondary": list,
        "evidence": str,
        "severity": str,
    },
    "feedback": {
        "strengths": list,
        "priorities": list,
        "student_facing_summary": str,
    },
    "revision_plan": {
        "goal": str,
        "actions": list,
        "expected_impact": str,
    },
}

_WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_'-]*")
_UNSUPPORTED_FEEDBACK_PATTERNS = (
    re.compile(r"\byour teacher said\b", re.IGNORECASE),
    re.compile(r"\baccording to (the )?data table\b", re.IGNORECASE),
    re.compile(r"\bas a (?:male|female|student from)\b", re.IGNORECASE),
)
_FALLBACK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "he",
    "in",
    "is",
    "it",
    "its",
    "of",
    "on",
    "that",
    "the",
    "to",
    "was",
    "were",
    "will",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class ValidationFinding:
    """One validation finding."""

    check_id: str
    passed: bool
    message: str
    severity: str = "error"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExampleValidationResult:
    """Validation result for one model/example pair."""

    model_id: str
    example_id: str
    json_validity: bool
    missing_fields: tuple[str, ...]
    score_range_valid: bool
    hallucinated_rubric_items: tuple[str, ...]
    unsupported_feedback: bool
    reasoning_completeness: float
    confidence: float | None
    calibration_target: float | None
    calibration_brier: float | None
    findings: tuple[ValidationFinding, ...]


@dataclass(frozen=True)
class ModelValidationSummary:
    """Aggregated validation summary for one model."""

    model_id: str
    examples_total: int
    json_validity_rate: float
    missing_fields_rate: float
    score_range_valid_rate: float
    hallucinated_rubric_rate: float
    unsupported_feedback_rate: float
    reasoning_completeness_mean: float
    confidence_available_rate: float
    calibration_target_available_rate: float
    brier_mean: float | None
    ece_10bin: float | None
    overconfidence_rate: float | None


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _WORD_RE.findall(text or "")]


def _extract_output_object(payload: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("output", "predicted", "response_json"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value

    raw_output = payload.get("raw_output")
    if isinstance(raw_output, str):
        try:
            parsed = json.loads(raw_output)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed

    response_text = payload.get("response_text")
    if isinstance(response_text, str):
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            return None
        if isinstance(parsed, dict):
            return parsed

    # Allow flat output rows with required keys at top-level.
    if isinstance(payload, dict) and "score" in payload and "confidence" in payload:
        return payload

    return None


def _collect_missing_fields(
    obj: dict[str, Any],
    spec: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    missing: list[str] = []
    for key, expected in spec.items():
        field_path = f"{prefix}.{key}" if prefix else key
        if key not in obj:
            missing.append(field_path)
            continue
        value = obj[key]
        if isinstance(expected, dict):
            if not isinstance(value, dict):
                missing.append(field_path)
                continue
            missing.extend(_collect_missing_fields(value, expected, field_path))
            continue
        if not isinstance(value, expected):
            missing.append(field_path)
    return missing


def _score_range_valid(output_obj: dict[str, Any]) -> bool:
    score = output_obj.get("score")
    return isinstance(score, int) and 0 <= score <= 60


def _validate_rubric_items(
    output_obj: dict[str, Any],
    gold: GoldExample | None,
) -> tuple[tuple[str, ...], list[ValidationFinding]]:
    findings: list[ValidationFinding] = []
    issues: list[str] = []
    rubric = output_obj.get("rubric")
    if not isinstance(rubric, dict):
        issues.append("rubric_missing")
        findings.append(
            ValidationFinding(
                check_id="hallucinated_rubric_items",
                passed=False,
                message="Missing rubric object.",
            )
        )
        return tuple(issues), findings

    criteria = rubric.get("criteria")
    if not isinstance(criteria, list):
        issues.append("rubric.criteria_missing")
        findings.append(
            ValidationFinding(
                check_id="hallucinated_rubric_items",
                passed=False,
                message="Missing rubric.criteria array.",
            )
        )
        return tuple(issues), findings

    seen: set[str] = set()
    for item in criteria:
        if not isinstance(item, dict):
            issues.append("rubric.criteria.non_object_item")
            continue
        criterion = item.get("criterion")
        if not isinstance(criterion, str):
            issues.append("rubric.criteria.criterion_missing")
            continue
        criterion_norm = criterion.strip().lower()
        if criterion_norm not in ALLOWED_RUBRIC_CRITERIA:
            issues.append(f"unknown:{criterion_norm}")
        if criterion_norm in seen:
            issues.append(f"duplicate:{criterion_norm}")
        seen.add(criterion_norm)

    for required in ALLOWED_RUBRIC_CRITERIA:
        if required not in seen:
            issues.append(f"missing:{required}")

    if gold and gold.rubric:
        gold_terms = {item.strip().lower() for item in gold.rubric if item.strip()}
        # If gold rubric uses task-specific labels, warn when no lexical overlap exists.
        if gold_terms and not (seen & gold_terms):
            findings.append(
                ValidationFinding(
                    check_id="hallucinated_rubric_items",
                    passed=False,
                    severity="warning",
                    message="Predicted rubric criteria have zero overlap with gold rubric labels.",
                    metadata={"gold_terms": sorted(gold_terms), "predicted_terms": sorted(seen)},
                )
            )

    if issues:
        findings.append(
            ValidationFinding(
                check_id="hallucinated_rubric_items",
                passed=False,
                message="Rubric criteria contain unsupported or missing items.",
                metadata={"issues": issues},
            )
        )
    else:
        findings.append(
            ValidationFinding(
                check_id="hallucinated_rubric_items",
                passed=True,
                message="Rubric criteria are within allowed set.",
            )
        )
    return tuple(issues), findings


def _feedback_text(output_obj: dict[str, Any]) -> str:
    feedback = output_obj.get("feedback")
    if isinstance(feedback, dict):
        parts: list[str] = []
        for key in ("strengths", "priorities"):
            value = feedback.get(key)
            if isinstance(value, list):
                parts.extend(str(item) for item in value)
        summary = feedback.get("student_facing_summary")
        if isinstance(summary, str):
            parts.append(summary)
        return " ".join(parts).strip()

    # Fallback for flat formats.
    for key in ("feedback", "educational_feedback"):
        value = output_obj.get(key)
        if isinstance(value, str):
            return value.strip()
    return ""


def _is_unsupported_feedback(output_obj: dict[str, Any], gold: GoldExample | None) -> bool:
    text = _feedback_text(output_obj)
    if not text:
        return True

    for pattern in _UNSUPPORTED_FEEDBACK_PATTERNS:
        if pattern.search(text):
            return True

    if gold is None:
        return False

    essay_tokens = {token for token in _tokenize(gold.essay) if token not in _FALLBACK_STOPWORDS}
    feedback_tokens = {
        token for token in _tokenize(text) if token not in _FALLBACK_STOPWORDS and len(token) >= 4
    }
    if not feedback_tokens:
        return True

    overlap = essay_tokens & feedback_tokens
    overlap_ratio = len(overlap) / len(feedback_tokens)
    # Very low overlap is a pragmatic proxy for unsupported feedback claims.
    return overlap_ratio < 0.04


def _reasoning_completeness(output_obj: dict[str, Any]) -> float:
    reasoning = output_obj.get("reasoning")
    logical = output_obj.get("logical_analysis")
    if not isinstance(reasoning, dict) or not isinstance(logical, dict):
        return 0.0

    checks = []
    summary = reasoning.get("summary")
    checks.append(1.0 if isinstance(summary, str) and summary.strip() else 0.0)

    steps = reasoning.get("steps")
    steps_ok = (
        isinstance(steps, list)
        and len(steps) >= 3
        and all(isinstance(item, str) and item.strip() for item in steps[:3])
    )
    checks.append(1.0 if steps_ok else 0.0)

    required_logical = (
        "claim_quality",
        "evidence_quality",
        "coherence",
        "counterargument_handling",
        "consistency_checks",
    )
    logical_ok = True
    for key in required_logical:
        if key not in logical:
            logical_ok = False
            break
    if logical_ok:
        consistency = logical.get("consistency_checks")
        logical_ok = isinstance(consistency, list) and len(consistency) >= 1
    checks.append(1.0 if logical_ok else 0.0)

    return mean(checks) if checks else 0.0


def _confidence_and_target(
    output_obj: dict[str, Any],
    prediction: PredictionRecord,
    gold: GoldExample | None,
) -> tuple[float | None, float | None, float | None]:
    confidence_raw = output_obj.get("confidence")
    confidence: float | None = None
    if isinstance(confidence_raw, int | float):
        confidence = float(confidence_raw)
        confidence = max(0.0, min(1.0, confidence))

    if gold is None:
        return confidence, None, None

    targets: list[float] = []
    if gold.gold_score is not None and prediction.predicted_score is not None:
        targets.append(1.0 if abs(gold.gold_score - prediction.predicted_score) <= 1.0 else 0.0)

    if gold.expected_fallacies and prediction.predicted_fallacies:
        expected = {item.strip().lower() for item in gold.expected_fallacies if item.strip()}
        predicted = {
            item.strip().lower() for item in prediction.predicted_fallacies if item.strip()
        }
        if expected:
            targets.append(1.0 if (expected & predicted) else 0.0)

    target = mean(targets) if targets else None
    if confidence is None or target is None:
        return confidence, target, None
    brier = (confidence - target) ** 2
    return confidence, target, brier


def validate_prediction(
    prediction: PredictionRecord,
    *,
    gold: GoldExample | None = None,
) -> ExampleValidationResult:
    """Run all automatic checks for one prediction."""
    findings: list[ValidationFinding] = []
    output_obj = _extract_output_object(prediction.raw_payload)

    json_validity = output_obj is not None
    findings.append(
        ValidationFinding(
            check_id="json_validity",
            passed=json_validity,
            message=(
                "Output is parseable JSON object." if json_validity else "Output is not valid JSON."
            ),
        )
    )

    missing_fields: tuple[str, ...] = ()
    score_range_valid = False
    hallucinated_rubric_items: tuple[str, ...] = ()
    unsupported_feedback = True
    reasoning_completeness = 0.0
    confidence: float | None = None
    calibration_target: float | None = None
    calibration_brier: float | None = None

    if output_obj is not None:
        missing = _collect_missing_fields(output_obj, REQUIRED_STRUCTURE)
        missing_fields = tuple(sorted(set(missing)))
        findings.append(
            ValidationFinding(
                check_id="missing_fields",
                passed=not missing_fields,
                message=(
                    "All required fields present."
                    if not missing_fields
                    else "Missing required fields."
                ),
                metadata={"missing_fields": list(missing_fields)},
            )
        )

        score_range_valid = _score_range_valid(output_obj)
        findings.append(
            ValidationFinding(
                check_id="score_range",
                passed=score_range_valid,
                message=(
                    "Score within [0,60] integer range."
                    if score_range_valid
                    else "Score missing or out of range."
                ),
            )
        )

        hallucinated_rubric_items, rubric_findings = _validate_rubric_items(output_obj, gold=gold)
        findings.extend(rubric_findings)

        unsupported_feedback = _is_unsupported_feedback(output_obj, gold=gold)
        findings.append(
            ValidationFinding(
                check_id="unsupported_feedback",
                passed=not unsupported_feedback,
                message=(
                    "Feedback appears grounded."
                    if not unsupported_feedback
                    else "Feedback appears weakly grounded or unsupported."
                ),
            )
        )

        reasoning_completeness = _reasoning_completeness(output_obj)
        findings.append(
            ValidationFinding(
                check_id="reasoning_completeness",
                passed=reasoning_completeness >= 0.67,
                message=(
                    "Reasoning sections are complete enough."
                    if reasoning_completeness >= 0.67
                    else "Reasoning sections are incomplete."
                ),
                metadata={"reasoning_completeness": reasoning_completeness},
            )
        )

        confidence, calibration_target, calibration_brier = _confidence_and_target(
            output_obj=output_obj,
            prediction=prediction,
            gold=gold,
        )
        if confidence is None:
            findings.append(
                ValidationFinding(
                    check_id="confidence_calibration",
                    passed=False,
                    severity="warning",
                    message="Confidence value missing; calibration unavailable.",
                )
            )
        elif calibration_brier is None:
            findings.append(
                ValidationFinding(
                    check_id="confidence_calibration",
                    passed=False,
                    severity="warning",
                    message="Calibration target unavailable for this example.",
                )
            )
        else:
            findings.append(
                ValidationFinding(
                    check_id="confidence_calibration",
                    passed=True,
                    message="Calibration computed.",
                    metadata={
                        "confidence": confidence,
                        "target": calibration_target,
                        "brier": calibration_brier,
                    },
                )
            )
    else:
        findings.append(
            ValidationFinding(
                check_id="missing_fields",
                passed=False,
                message="Cannot check required fields because JSON is invalid.",
            )
        )
        findings.append(
            ValidationFinding(
                check_id="score_range",
                passed=False,
                message="Cannot check score range because JSON is invalid.",
            )
        )
        findings.append(
            ValidationFinding(
                check_id="hallucinated_rubric_items",
                passed=False,
                message="Cannot check rubric items because JSON is invalid.",
            )
        )
        findings.append(
            ValidationFinding(
                check_id="unsupported_feedback",
                passed=False,
                message="Cannot check feedback grounding because JSON is invalid.",
            )
        )
        findings.append(
            ValidationFinding(
                check_id="reasoning_completeness",
                passed=False,
                message="Cannot check reasoning completeness because JSON is invalid.",
            )
        )
        findings.append(
            ValidationFinding(
                check_id="confidence_calibration",
                passed=False,
                severity="warning",
                message="Cannot calibrate confidence because JSON is invalid.",
            )
        )

    return ExampleValidationResult(
        model_id=prediction.model_id,
        example_id=prediction.example_id,
        json_validity=json_validity,
        missing_fields=missing_fields,
        score_range_valid=score_range_valid,
        hallucinated_rubric_items=hallucinated_rubric_items,
        unsupported_feedback=unsupported_feedback,
        reasoning_completeness=reasoning_completeness,
        confidence=confidence,
        calibration_target=calibration_target,
        calibration_brier=calibration_brier,
        findings=tuple(findings),
    )


def _compute_ece(
    confidences: list[float],
    targets: list[float],
    *,
    bins: int = 10,
) -> float | None:
    if not confidences or not targets or len(confidences) != len(targets):
        return None

    bucket_conf: list[list[float]] = [[] for _ in range(bins)]
    bucket_tar: list[list[float]] = [[] for _ in range(bins)]
    for confidence, target in zip(confidences, targets, strict=True):
        index = min(int(confidence * bins), bins - 1)
        bucket_conf[index].append(confidence)
        bucket_tar[index].append(target)

    total = len(confidences)
    ece = 0.0
    for conf_bucket, target_bucket in zip(bucket_conf, bucket_tar, strict=True):
        if not conf_bucket:
            continue
        avg_conf = mean(conf_bucket)
        avg_target = mean(target_bucket)
        ece += (len(conf_bucket) / total) * abs(avg_conf - avg_target)
    return ece


def summarize_validation(results: list[ExampleValidationResult]) -> list[ModelValidationSummary]:
    """Aggregate example-level checks into model-level summaries."""
    by_model: dict[str, list[ExampleValidationResult]] = {}
    for result in results:
        by_model.setdefault(result.model_id, []).append(result)

    summaries: list[ModelValidationSummary] = []
    for model_id, rows in sorted(by_model.items()):
        total = len(rows)
        json_validity_rate = (
            mean(1.0 if row.json_validity else 0.0 for row in rows) if rows else 0.0
        )
        missing_fields_rate = (
            mean(1.0 if row.missing_fields else 0.0 for row in rows) if rows else 0.0
        )
        score_range_valid_rate = (
            mean(1.0 if row.score_range_valid else 0.0 for row in rows) if rows else 0.0
        )
        hallucinated_rubric_rate = (
            mean(1.0 if row.hallucinated_rubric_items else 0.0 for row in rows) if rows else 0.0
        )
        unsupported_feedback_rate = (
            mean(1.0 if row.unsupported_feedback else 0.0 for row in rows) if rows else 0.0
        )
        reasoning_mean = mean(row.reasoning_completeness for row in rows) if rows else 0.0

        confidence_values = [row.confidence for row in rows if row.confidence is not None]
        target_values = [
            row.calibration_target for row in rows if row.calibration_target is not None
        ]
        paired: list[tuple[float, float]] = []
        for row in rows:
            if row.confidence is not None and row.calibration_target is not None:
                paired.append((row.confidence, row.calibration_target))
        paired_confidences = [item[0] for item in paired]
        paired_targets = [item[1] for item in paired]
        briers = [row.calibration_brier for row in rows if row.calibration_brier is not None]

        overconfidence = None
        if paired:
            overconfidence = mean(
                1.0 if (confidence >= 0.8 and target <= 0.5) else 0.0
                for confidence, target in paired
            )

        summaries.append(
            ModelValidationSummary(
                model_id=model_id,
                examples_total=total,
                json_validity_rate=json_validity_rate,
                missing_fields_rate=missing_fields_rate,
                score_range_valid_rate=score_range_valid_rate,
                hallucinated_rubric_rate=hallucinated_rubric_rate,
                unsupported_feedback_rate=unsupported_feedback_rate,
                reasoning_completeness_mean=reasoning_mean,
                confidence_available_rate=(len(confidence_values) / total if total else 0.0),
                calibration_target_available_rate=(len(target_values) / total if total else 0.0),
                brier_mean=(mean(briers) if briers else None),
                ece_10bin=_compute_ece(paired_confidences, paired_targets, bins=10),
                overconfidence_rate=overconfidence,
            )
        )

    return summaries


def run_validation(
    *,
    predictions: list[PredictionRecord],
    gold_examples: list[GoldExample] | None = None,
) -> tuple[list[ExampleValidationResult], list[ModelValidationSummary]]:
    """Run full validation suite over prediction rows."""
    gold_index = {item.example_id: item for item in (gold_examples or [])}

    results = [
        validate_prediction(prediction, gold=gold_index.get(prediction.example_id))
        for prediction in predictions
    ]
    summaries = summarize_validation(results)
    return results, summaries


def write_validation_outputs(
    *,
    output_dir: Path,
    results: list[ExampleValidationResult],
    summaries: list[ModelValidationSummary],
) -> None:
    """Persist validation outputs in machine-readable and csv forms."""
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "teacher_validation_results.jsonl").open("w", encoding="utf-8") as handle:
        for row in results:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")

    (output_dir / "teacher_validation_summary.json").write_text(
        json.dumps([asdict(item) for item in summaries], ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with (output_dir / "teacher_validation_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        if summaries:
            fieldnames = list(asdict(summaries[0]).keys())
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for item in summaries:
                writer.writerow(asdict(item))
