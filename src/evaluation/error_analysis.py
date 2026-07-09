"""Post-training error analysis framework for educational-assessment predictions.

This module analyzes precomputed model predictions against gold examples and produces:
- score-error analysis
- rubric-failure analysis
- hallucination analysis
- fallacy-miss analysis
- reasoning-failure analysis

No model inference is executed in this module.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from math import sqrt
from pathlib import Path
from statistics import mean

from teacher.io import GoldExample, PredictionRecord, load_gold_examples, load_predictions
from teacher.validation import ExampleValidationResult, run_validation

_NONE_FALLACY_MARKERS = {
    "",
    "none",
    "no_fallacy",
    "no_fallacy_detected",
    "valid_reasoning",
    "n/a",
    "na",
    "null",
}


@dataclass(frozen=True)
class ErrorAnalysisConfig:
    """Runtime configuration for error analysis."""

    gold_path: Path
    predictions_path: Path
    output_dir: Path
    reasoning_failure_threshold: float = 0.67
    severe_score_error_threshold: float = 2.0
    top_k_examples: int = 20


@dataclass(frozen=True)
class ErrorExampleRecord:
    """Per-example error taxonomy record."""

    model_id: str
    example_id: str
    source: str
    difficulty: str
    split: str
    gold_score: float | None
    predicted_score: float | None
    score_error: float | None
    score_error_bucket: str
    rubric_failure: bool
    hallucination: bool
    hallucination_types: tuple[str, ...]
    fallacy_miss: bool
    expected_fallacies: tuple[str, ...]
    predicted_fallacies: tuple[str, ...]
    reasoning_failure: bool
    reasoning_completeness: float
    validation_missing_fields: tuple[str, ...]
    validation_notes: tuple[str, ...]


@dataclass(frozen=True)
class ModelErrorSummary:
    """Aggregated error summary for one model."""

    model_id: str
    examples_total: int
    examples_with_gold: int
    scored_examples: int
    score_mae: float | None
    score_rmse: float | None
    score_exact_match_rate: float
    score_severe_error_rate: float
    rubric_failure_rate: float
    hallucination_rate: float
    fallacy_miss_rate: float
    reasoning_failure_rate: float
    score_error_bucket_counts: dict[str, int]
    top_score_error_example_ids: tuple[str, ...]
    top_hallucination_example_ids: tuple[str, ...]
    top_fallacy_miss_example_ids: tuple[str, ...]
    top_reasoning_failure_example_ids: tuple[str, ...]


@dataclass(frozen=True)
class ErrorAnalysisResult:
    """Top-level analysis payload."""

    total_predictions: int
    matched_gold_examples: int
    unmatched_gold_examples: int
    reasoning_failure_threshold: float
    severe_score_error_threshold: float
    model_summaries: tuple[ModelErrorSummary, ...]
    records: tuple[ErrorExampleRecord, ...]


def _normalize_fallacy_label(value: str) -> str:
    return "_".join(value.strip().lower().replace("-", " ").split())


def _normalize_fallacy_set(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: set[str] = set()
    for value in values:
        label = _normalize_fallacy_label(value)
        if label in _NONE_FALLACY_MARKERS:
            continue
        if label:
            normalized.add(label)
    return tuple(sorted(normalized))


def _safe_split(prediction: PredictionRecord) -> str:
    payload = prediction.raw_payload
    split = payload.get("split")
    if isinstance(split, str) and split.strip():
        return split.strip().lower()

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        meta_split = metadata.get("split")
        if isinstance(meta_split, str) and meta_split.strip():
            return meta_split.strip().lower()
    return "unknown"


def _score_error_bucket(
    score_error: float | None,
    *,
    severe_threshold: float,
) -> str:
    if score_error is None:
        return "unavailable"
    if score_error == 0.0:
        return "exact"
    if score_error <= 1.0:
        return "off_by_1"
    if score_error < severe_threshold:
        return "off_by_2_to_threshold"
    return "severe"


def _validation_note_ids(result: ExampleValidationResult) -> tuple[str, ...]:
    notes: set[str] = set()
    for finding in result.findings:
        if not finding.passed:
            notes.add(finding.check_id)
    return tuple(sorted(notes))


def _hallucination_types(result: ExampleValidationResult) -> tuple[str, ...]:
    kinds: list[str] = []
    if result.hallucinated_rubric_items:
        kinds.append("hallucinated_rubric_items")
    if result.unsupported_feedback:
        kinds.append("unsupported_feedback")
    return tuple(kinds)


def _build_record(
    *,
    prediction: PredictionRecord,
    gold: GoldExample | None,
    validation: ExampleValidationResult,
    config: ErrorAnalysisConfig,
) -> ErrorExampleRecord:
    gold_score = gold.gold_score if gold is not None else None
    predicted_score = prediction.predicted_score
    score_error = None
    if gold_score is not None and predicted_score is not None:
        score_error = abs(predicted_score - gold_score)

    expected = _normalize_fallacy_set(gold.expected_fallacies if gold else ())
    predicted = _normalize_fallacy_set(prediction.predicted_fallacies)
    fallacy_miss = bool(expected) and not (set(expected) & set(predicted))
    hallucination_types = _hallucination_types(validation)

    return ErrorExampleRecord(
        model_id=prediction.model_id,
        example_id=prediction.example_id,
        source=gold.source if gold else "unknown",
        difficulty=gold.difficulty if gold else "unknown",
        split=_safe_split(prediction),
        gold_score=gold_score,
        predicted_score=predicted_score,
        score_error=score_error,
        score_error_bucket=_score_error_bucket(
            score_error,
            severe_threshold=config.severe_score_error_threshold,
        ),
        rubric_failure=bool(validation.hallucinated_rubric_items),
        hallucination=bool(hallucination_types),
        hallucination_types=hallucination_types,
        fallacy_miss=fallacy_miss,
        expected_fallacies=expected,
        predicted_fallacies=predicted,
        reasoning_failure=validation.reasoning_completeness < config.reasoning_failure_threshold,
        reasoning_completeness=validation.reasoning_completeness,
        validation_missing_fields=validation.missing_fields,
        validation_notes=_validation_note_ids(validation),
    )


def _empty_score_bucket_counts() -> dict[str, int]:
    return {
        "exact": 0,
        "off_by_1": 0,
        "off_by_2_to_threshold": 0,
        "severe": 0,
        "unavailable": 0,
    }


def _summarize_model(
    *,
    model_id: str,
    rows: list[ErrorExampleRecord],
    severe_threshold: float,
    top_k: int,
) -> ModelErrorSummary:
    total = len(rows)
    with_gold = [row for row in rows if row.gold_score is not None]
    scored = [row for row in rows if row.score_error is not None]
    score_errors = [row.score_error for row in scored if row.score_error is not None]

    bucket_counts = _empty_score_bucket_counts()
    for row in rows:
        bucket_counts[row.score_error_bucket] = bucket_counts.get(row.score_error_bucket, 0) + 1

    top_score_rows = sorted(
        [row for row in scored if row.score_error is not None],
        key=lambda item: item.score_error if item.score_error is not None else -1.0,
        reverse=True,
    )[:top_k]
    top_hallucination_rows = [row for row in rows if row.hallucination][:top_k]
    top_fallacy_rows = [row for row in rows if row.fallacy_miss][:top_k]
    top_reasoning_rows = sorted(
        [row for row in rows if row.reasoning_failure],
        key=lambda item: item.reasoning_completeness,
    )[:top_k]

    return ModelErrorSummary(
        model_id=model_id,
        examples_total=total,
        examples_with_gold=len(with_gold),
        scored_examples=len(scored),
        score_mae=(mean(score_errors) if score_errors else None),
        score_rmse=(sqrt(mean(error**2 for error in score_errors)) if score_errors else None),
        score_exact_match_rate=(
            mean(1.0 if row.score_error == 0.0 else 0.0 for row in scored) if scored else 0.0
        ),
        score_severe_error_rate=(
            mean(
                1.0
                if row.score_error is not None and row.score_error >= severe_threshold
                else 0.0
                for row in scored
            )
            if scored
            else 0.0
        ),
        rubric_failure_rate=(
            mean(1.0 if row.rubric_failure else 0.0 for row in rows) if rows else 0.0
        ),
        hallucination_rate=(
            mean(1.0 if row.hallucination else 0.0 for row in rows) if rows else 0.0
        ),
        fallacy_miss_rate=(
            mean(1.0 if row.fallacy_miss else 0.0 for row in rows) if rows else 0.0
        ),
        reasoning_failure_rate=(
            mean(1.0 if row.reasoning_failure else 0.0 for row in rows) if rows else 0.0
        ),
        score_error_bucket_counts=bucket_counts,
        top_score_error_example_ids=tuple(row.example_id for row in top_score_rows),
        top_hallucination_example_ids=tuple(row.example_id for row in top_hallucination_rows),
        top_fallacy_miss_example_ids=tuple(row.example_id for row in top_fallacy_rows),
        top_reasoning_failure_example_ids=tuple(row.example_id for row in top_reasoning_rows),
    )


def analyze_errors(config: ErrorAnalysisConfig) -> ErrorAnalysisResult:
    """Run post-training error analysis on precomputed predictions."""
    gold_examples = load_gold_examples(config.gold_path)
    predictions = load_predictions(config.predictions_path)
    validation_results, _ = run_validation(predictions=predictions, gold_examples=gold_examples)

    gold_index = {item.example_id: item for item in gold_examples}
    validation_index = {(item.model_id, item.example_id): item for item in validation_results}

    records: list[ErrorExampleRecord] = []
    matched = 0
    for prediction in predictions:
        gold = gold_index.get(prediction.example_id)
        if gold is not None:
            matched += 1
        validation = validation_index[(prediction.model_id, prediction.example_id)]
        records.append(
            _build_record(
                prediction=prediction,
                gold=gold,
                validation=validation,
                config=config,
            )
        )

    by_model: dict[str, list[ErrorExampleRecord]] = {}
    for row in records:
        by_model.setdefault(row.model_id, []).append(row)

    summaries = [
        _summarize_model(
            model_id=model_id,
            rows=rows,
            severe_threshold=config.severe_score_error_threshold,
            top_k=config.top_k_examples,
        )
        for model_id, rows in sorted(by_model.items())
    ]

    return ErrorAnalysisResult(
        total_predictions=len(predictions),
        matched_gold_examples=matched,
        unmatched_gold_examples=max(0, len(predictions) - matched),
        reasoning_failure_threshold=config.reasoning_failure_threshold,
        severe_score_error_threshold=config.severe_score_error_threshold,
        model_summaries=tuple(summaries),
        records=tuple(records),
    )


def render_markdown_report(result: ErrorAnalysisResult) -> str:
    """Render a markdown summary report."""
    lines = [
        "# Post-Training Error Analysis",
        "",
        "## Scope",
        "",
        "- score errors",
        "- rubric failures",
        "- hallucinations",
        "- fallacy misses",
        "- reasoning failures",
        "",
        "## Dataset Coverage",
        "",
        f"- total_predictions: `{result.total_predictions}`",
        f"- matched_gold_examples: `{result.matched_gold_examples}`",
        f"- unmatched_gold_examples: `{result.unmatched_gold_examples}`",
        (
            f"- reasoning_failure_threshold: `{result.reasoning_failure_threshold}` "
            "(reasoning completeness below this threshold is a failure)"
        ),
        f"- severe_score_error_threshold: `{result.severe_score_error_threshold}`",
        "",
        "## Model Summaries",
        "",
        (
            "| model | n | scored | mae | rmse | exact_rate | severe_score_rate | "
            "rubric_fail | hallucination | fallacy_miss | reasoning_fail |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for item in result.model_summaries:
        mae = f"{item.score_mae:.4f}" if item.score_mae is not None else "n/a"
        rmse = f"{item.score_rmse:.4f}" if item.score_rmse is not None else "n/a"
        lines.append("| " + " | ".join(
            [
                item.model_id,
                str(item.examples_total),
                str(item.scored_examples),
                mae,
                rmse,
                f"{item.score_exact_match_rate:.4f}",
                f"{item.score_severe_error_rate:.4f}",
                f"{item.rubric_failure_rate:.4f}",
                f"{item.hallucination_rate:.4f}",
                f"{item.fallacy_miss_rate:.4f}",
                f"{item.reasoning_failure_rate:.4f}",
            ]
        ) + " |")

    lines.extend(["", "## Score Error Buckets", ""])
    for item in result.model_summaries:
        lines.append(f"### {item.model_id}")
        lines.append("")
        lines.append(
            "- counts: "
            + ", ".join(
                f"{bucket}={count}"
                for bucket, count in sorted(item.score_error_bucket_counts.items())
            )
        )
        lines.append(
            "- top_score_error_example_ids: "
            + ", ".join(item.top_score_error_example_ids)
        )
        lines.append(
            "- top_hallucination_example_ids: "
            + ", ".join(item.top_hallucination_example_ids)
        )
        lines.append(
            "- top_fallacy_miss_example_ids: "
            + ", ".join(item.top_fallacy_miss_example_ids)
        )
        lines.append(
            "- top_reasoning_failure_example_ids: "
            + ", ".join(item.top_reasoning_failure_example_ids)
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_analysis_outputs(*, output_dir: Path, result: ErrorAnalysisResult) -> None:
    """Persist machine-readable and markdown analysis artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "error_analysis_records.jsonl").open("w", encoding="utf-8") as handle:
        for row in result.records:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")

    (output_dir / "error_analysis_summary.json").write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    with (output_dir / "error_analysis_model_summary.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        if result.model_summaries:
            fieldnames = list(asdict(result.model_summaries[0]).keys())
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in result.model_summaries:
                writer.writerow(asdict(row))

    (output_dir / "error_analysis_report.md").write_text(
        render_markdown_report(result),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run post-training error analysis framework.")
    parser.add_argument("--gold-path", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--predictions-path", required=True)
    parser.add_argument("--output-dir", default="outputs/error_analysis")
    parser.add_argument("--reasoning-failure-threshold", type=float, default=0.67)
    parser.add_argument("--severe-score-error-threshold", type=float, default=2.0)
    parser.add_argument("--top-k-examples", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    config = ErrorAnalysisConfig(
        gold_path=Path(args.gold_path),
        predictions_path=Path(args.predictions_path),
        output_dir=Path(args.output_dir),
        reasoning_failure_threshold=float(args.reasoning_failure_threshold),
        severe_score_error_threshold=float(args.severe_score_error_threshold),
        top_k_examples=int(args.top_k_examples),
    )
    result = analyze_errors(config)
    write_analysis_outputs(output_dir=config.output_dir, result=result)
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
