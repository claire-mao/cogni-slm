"""Confidence calibration utilities for educational-assessment predictions.

This module analyzes precomputed predictions and does not run model inference.
Supported calibration methods:
- Expected Calibration Error (ECE)
- Reliability diagram bins + SVG render
- Brier Score
- Temperature scaling
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean

from teacher.io import GoldExample, PredictionRecord, load_gold_examples, load_predictions

TARGET_MODE_SCORE_ONLY = "score_only"
TARGET_MODE_FALLACY_ONLY = "fallacy_only"
TARGET_MODE_SCORE_AND_FALLACY = "score_and_fallacy"
TARGET_MODES = (
    TARGET_MODE_SCORE_ONLY,
    TARGET_MODE_FALLACY_ONLY,
    TARGET_MODE_SCORE_AND_FALLACY,
)

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
class CalibrationConfig:
    """Runtime configuration for calibration analysis."""

    gold_path: Path
    predictions_path: Path
    output_dir: Path
    bins: int = 10
    target_mode: str = TARGET_MODE_SCORE_AND_FALLACY
    score_tolerance: float = 1.0
    overconfidence_threshold: float = 0.8
    temperature_grid_min: float = 0.25
    temperature_grid_max: float = 4.0
    temperature_grid_size: int = 200


@dataclass(frozen=True)
class CalibrationExampleRecord:
    """Per-example calibration record."""

    model_id: str
    example_id: str
    confidence: float | None
    calibrated_confidence: float | None
    target: float | None
    score_target: float | None
    fallacy_target: float | None
    brier_before: float | None
    brier_after: float | None


@dataclass(frozen=True)
class ReliabilityBin:
    """One reliability-diagram bin."""

    bin_index: int
    lower: float
    upper: float
    count: int
    avg_confidence: float | None
    avg_target: float | None
    abs_gap: float | None


@dataclass(frozen=True)
class ModelReliability:
    """Reliability bins before and after temperature scaling."""

    model_id: str
    bins_before: tuple[ReliabilityBin, ...]
    bins_after: tuple[ReliabilityBin, ...]


@dataclass(frozen=True)
class ModelCalibrationSummary:
    """Model-level calibration summary."""

    model_id: str
    examples_total: int
    confidence_available_rate: float
    target_available_rate: float
    paired_examples: int
    temperature: float
    brier_before: float | None
    brier_after: float | None
    ece_before: float | None
    ece_after: float | None
    nll_before: float | None
    nll_after: float | None
    overconfidence_before: float | None
    overconfidence_after: float | None


@dataclass(frozen=True)
class CalibrationResult:
    """Top-level calibration analysis payload."""

    total_predictions: int
    matched_gold_examples: int
    unmatched_gold_examples: int
    bins: int
    target_mode: str
    score_tolerance: float
    model_summaries: tuple[ModelCalibrationSummary, ...]
    reliability: tuple[ModelReliability, ...]
    records: tuple[CalibrationExampleRecord, ...]


def _extract(path: list[str], payload: dict[str, object]) -> object | None:
    current: object = payload
    for key in path:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _safe_float(value: object) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(parsed):
        return None
    return parsed


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


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


def _extract_confidence(prediction: PredictionRecord) -> float | None:
    payload = prediction.raw_payload
    candidates = [
        ["confidence"],
        ["output", "confidence"],
        ["predicted", "confidence"],
        ["raw_json_output", "confidence"],
        ["response_json", "confidence"],
    ]
    confidence: float | None = None
    for path in candidates:
        value = _safe_float(_extract(path, payload))
        if value is not None:
            confidence = value
            break
    if confidence is None:
        return None
    if confidence > 1.0 and confidence <= 100.0:
        confidence = confidence / 100.0
    return _clamp01(confidence)


def _score_target(
    prediction: PredictionRecord,
    gold: GoldExample | None,
    *,
    score_tolerance: float,
) -> float | None:
    if gold is None or gold.gold_score is None or prediction.predicted_score is None:
        return None
    return 1.0 if abs(gold.gold_score - prediction.predicted_score) <= score_tolerance else 0.0


def _fallacy_target(prediction: PredictionRecord, gold: GoldExample | None) -> float | None:
    if gold is None:
        return None
    expected = _normalize_fallacy_set(gold.expected_fallacies)
    if not expected:
        return None
    predicted = _normalize_fallacy_set(prediction.predicted_fallacies)
    return 1.0 if set(expected) & set(predicted) else 0.0


def _compose_target(
    *,
    score_target: float | None,
    fallacy_target: float | None,
    target_mode: str,
) -> float | None:
    if target_mode == TARGET_MODE_SCORE_ONLY:
        return score_target
    if target_mode == TARGET_MODE_FALLACY_ONLY:
        return fallacy_target
    if target_mode == TARGET_MODE_SCORE_AND_FALLACY:
        parts = [value for value in (score_target, fallacy_target) if value is not None]
        return mean(parts) if parts else None
    raise ValueError(f"Unsupported target_mode: {target_mode}")


def brier_score(confidences: list[float], targets: list[float]) -> float | None:
    """Compute Brier score over paired confidence/target values."""
    if not confidences or len(confidences) != len(targets):
        return None
    return mean(
        (confidence - target) ** 2
        for confidence, target in zip(confidences, targets, strict=True)
    )


def reliability_diagram_bins(
    confidences: list[float],
    targets: list[float],
    *,
    bins: int = 10,
) -> tuple[ReliabilityBin, ...]:
    """Build reliability-diagram bins."""
    if bins < 2:
        raise ValueError("bins must be >= 2")
    if len(confidences) != len(targets):
        raise ValueError("confidences and targets must have the same length")

    bucket_conf: list[list[float]] = [[] for _ in range(bins)]
    bucket_tar: list[list[float]] = [[] for _ in range(bins)]
    for confidence, target in zip(confidences, targets, strict=True):
        index = min(int(_clamp01(confidence) * bins), bins - 1)
        bucket_conf[index].append(_clamp01(confidence))
        bucket_tar[index].append(_clamp01(target))

    rows: list[ReliabilityBin] = []
    width = 1.0 / bins
    for index in range(bins):
        conf_values = bucket_conf[index]
        target_values = bucket_tar[index]
        if conf_values:
            avg_conf = mean(conf_values)
            avg_target = mean(target_values)
            gap = abs(avg_conf - avg_target)
        else:
            avg_conf = None
            avg_target = None
            gap = None
        rows.append(
            ReliabilityBin(
                bin_index=index,
                lower=index * width,
                upper=(index + 1) * width,
                count=len(conf_values),
                avg_confidence=avg_conf,
                avg_target=avg_target,
                abs_gap=gap,
            )
        )
    return tuple(rows)


def expected_calibration_error(
    confidences: list[float],
    targets: list[float],
    *,
    bins: int = 10,
) -> float | None:
    """Compute Expected Calibration Error."""
    reliability = reliability_diagram_bins(confidences, targets, bins=bins)
    total = sum(row.count for row in reliability)
    if total == 0:
        return None
    return sum(
        (row.count / total) * (row.abs_gap or 0.0)
        for row in reliability
        if row.count > 0 and row.abs_gap is not None
    )


def _sigmoid(value: float) -> float:
    if value >= 0:
        exp_neg = math.exp(-value)
        return 1.0 / (1.0 + exp_neg)
    exp_pos = math.exp(value)
    return exp_pos / (1.0 + exp_pos)


def _logit(probability: float, *, eps: float = 1e-6) -> float:
    p = min(1.0 - eps, max(eps, probability))
    return math.log(p / (1.0 - p))


def temperature_scale_confidence(confidence: float, temperature: float) -> float:
    """Apply temperature scaling to one confidence value."""
    if temperature <= 0:
        raise ValueError("temperature must be > 0")
    return _sigmoid(_logit(_clamp01(confidence)) / temperature)


def _binary_nll(probabilities: list[float], targets: list[float], *, eps: float = 1e-6) -> float:
    if not probabilities or len(probabilities) != len(targets):
        raise ValueError("probabilities and targets must be non-empty with equal lengths")
    losses: list[float] = []
    for probability, target in zip(probabilities, targets, strict=True):
        p = min(1.0 - eps, max(eps, probability))
        y = _clamp01(target)
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
    """Fit temperature on a fixed grid by minimizing NLL.

    Returns `(best_temperature, nll_before, nll_after)`.
    """
    if not confidences or len(confidences) != len(targets):
        return 1.0, None, None
    if grid_min <= 0 or grid_max <= 0:
        raise ValueError("temperature grid bounds must be > 0")
    if grid_min > grid_max:
        raise ValueError("temperature_grid_min must be <= temperature_grid_max")
    if grid_size < 2:
        raise ValueError("temperature_grid_size must be >= 2")

    nll_before = _binary_nll(confidences, targets)
    best_temperature = 1.0
    best_nll = nll_before

    for index in range(grid_size):
        if grid_size == 1:
            temperature = grid_min
        else:
            frac = index / (grid_size - 1)
            temperature = grid_min + frac * (grid_max - grid_min)
        scaled = [temperature_scale_confidence(item, temperature) for item in confidences]
        nll = _binary_nll(scaled, targets)
        if nll < best_nll:
            best_nll = nll
            best_temperature = temperature

    return best_temperature, nll_before, best_nll


def _overconfidence_rate(
    confidences: list[float],
    targets: list[float],
    *,
    threshold: float,
) -> float | None:
    if not confidences or len(confidences) != len(targets):
        return None
    return mean(
        1.0 if (confidence >= threshold and target <= 0.5) else 0.0
        for confidence, target in zip(confidences, targets, strict=True)
    )


def _model_records(
    *,
    model_id: str,
    rows: list[PredictionRecord],
    gold_index: dict[str, GoldExample],
    config: CalibrationConfig,
) -> tuple[list[CalibrationExampleRecord], ModelCalibrationSummary, ModelReliability]:
    records: list[CalibrationExampleRecord] = []
    paired_confidences: list[float] = []
    paired_targets: list[float] = []

    for prediction in rows:
        gold = gold_index.get(prediction.example_id)
        confidence = _extract_confidence(prediction)
        score_target = _score_target(prediction, gold, score_tolerance=config.score_tolerance)
        fallacy_target = _fallacy_target(prediction, gold)
        target = _compose_target(
            score_target=score_target,
            fallacy_target=fallacy_target,
            target_mode=config.target_mode,
        )

        if confidence is not None and target is not None:
            paired_confidences.append(confidence)
            paired_targets.append(target)

        records.append(
            CalibrationExampleRecord(
                model_id=model_id,
                example_id=prediction.example_id,
                confidence=confidence,
                calibrated_confidence=None,
                target=target,
                score_target=score_target,
                fallacy_target=fallacy_target,
                brier_before=(
                    (confidence - target) ** 2
                    if confidence is not None and target is not None
                    else None
                ),
                brier_after=None,
            )
        )

    temperature, nll_before, nll_after = fit_temperature_scaling(
        paired_confidences,
        paired_targets,
        grid_min=config.temperature_grid_min,
        grid_max=config.temperature_grid_max,
        grid_size=config.temperature_grid_size,
    )

    calibrated = [temperature_scale_confidence(item, temperature) for item in paired_confidences]
    brier_before = brier_score(paired_confidences, paired_targets)
    brier_after = brier_score(calibrated, paired_targets)
    ece_before = expected_calibration_error(paired_confidences, paired_targets, bins=config.bins)
    ece_after = expected_calibration_error(calibrated, paired_targets, bins=config.bins)
    over_before = _overconfidence_rate(
        paired_confidences,
        paired_targets,
        threshold=config.overconfidence_threshold,
    )
    over_after = _overconfidence_rate(
        calibrated,
        paired_targets,
        threshold=config.overconfidence_threshold,
    )

    # Update per-example rows with calibrated confidence + after-brier for paired examples.
    pair_index = 0
    updated_rows: list[CalibrationExampleRecord] = []
    for row in records:
        if row.confidence is None or row.target is None:
            updated_rows.append(row)
            continue
        calibrated_confidence = calibrated[pair_index]
        pair_index += 1
        updated_rows.append(
            CalibrationExampleRecord(
                model_id=row.model_id,
                example_id=row.example_id,
                confidence=row.confidence,
                calibrated_confidence=calibrated_confidence,
                target=row.target,
                score_target=row.score_target,
                fallacy_target=row.fallacy_target,
                brier_before=row.brier_before,
                brier_after=(calibrated_confidence - row.target) ** 2,
            )
        )

    reliability_before = reliability_diagram_bins(
        paired_confidences,
        paired_targets,
        bins=config.bins,
    )
    reliability_after = reliability_diagram_bins(
        calibrated,
        paired_targets,
        bins=config.bins,
    )

    total = len(rows)
    confidence_available = sum(1 for row in records if row.confidence is not None)
    target_available = sum(1 for row in records if row.target is not None)
    summary = ModelCalibrationSummary(
        model_id=model_id,
        examples_total=total,
        confidence_available_rate=(confidence_available / total if total else 0.0),
        target_available_rate=(target_available / total if total else 0.0),
        paired_examples=len(paired_confidences),
        temperature=temperature,
        brier_before=brier_before,
        brier_after=brier_after,
        ece_before=ece_before,
        ece_after=ece_after,
        nll_before=nll_before,
        nll_after=nll_after,
        overconfidence_before=over_before,
        overconfidence_after=over_after,
    )
    reliability = ModelReliability(
        model_id=model_id,
        bins_before=reliability_before,
        bins_after=reliability_after,
    )
    return updated_rows, summary, reliability


def analyze_calibration(config: CalibrationConfig) -> CalibrationResult:
    """Run confidence calibration analysis for precomputed prediction rows."""
    if config.target_mode not in TARGET_MODES:
        raise ValueError(f"Unsupported target_mode: {config.target_mode}")
    if config.bins < 2:
        raise ValueError("bins must be >= 2")

    gold_examples = load_gold_examples(config.gold_path)
    predictions = load_predictions(config.predictions_path)

    gold_index = {item.example_id: item for item in gold_examples}
    matched = sum(1 for prediction in predictions if prediction.example_id in gold_index)

    by_model: dict[str, list[PredictionRecord]] = {}
    for prediction in predictions:
        by_model.setdefault(prediction.model_id, []).append(prediction)

    all_records: list[CalibrationExampleRecord] = []
    summaries: list[ModelCalibrationSummary] = []
    reliability_rows: list[ModelReliability] = []
    for model_id, rows in sorted(by_model.items()):
        model_records, model_summary, model_reliability = _model_records(
            model_id=model_id,
            rows=rows,
            gold_index=gold_index,
            config=config,
        )
        all_records.extend(model_records)
        summaries.append(model_summary)
        reliability_rows.append(model_reliability)

    summaries = sorted(
        summaries,
        key=lambda item: (
            (item.ece_after if item.ece_after is not None else 1e9),
            (item.brier_after if item.brier_after is not None else 1e9),
            -(item.paired_examples),
        ),
    )
    return CalibrationResult(
        total_predictions=len(predictions),
        matched_gold_examples=matched,
        unmatched_gold_examples=max(0, len(predictions) - matched),
        bins=config.bins,
        target_mode=config.target_mode,
        score_tolerance=config.score_tolerance,
        model_summaries=tuple(summaries),
        reliability=tuple(reliability_rows),
        records=tuple(all_records),
    )


def _sanitize_filename(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", text).strip("_") or "model"


def render_reliability_svg(
    bins: tuple[ReliabilityBin, ...],
    *,
    title: str,
    width: int = 720,
    height: int = 520,
) -> str:
    """Render a lightweight SVG reliability diagram."""
    left = 80
    right = width - 30
    top = 50
    bottom = height - 70
    plot_w = right - left
    plot_h = bottom - top

    rows = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>",
        "<rect width='100%' height='100%' fill='white'/>",
        f"<text x='{left}' y='28' font-size='18' font-family='sans-serif'>{title}</text>",
        (
            f"<line x1='{left}' y1='{bottom}' x2='{right}' y2='{bottom}' "
            "stroke='#222' stroke-width='1.5'/>"
        ),
        (
            f"<line x1='{left}' y1='{bottom}' x2='{left}' y2='{top}' "
            "stroke='#222' stroke-width='1.5'/>"
        ),
    ]

    # Perfect calibration diagonal.
    rows.append(
        f"<line x1='{left}' y1='{bottom}' x2='{right}' y2='{top}' "
        "stroke='#8a8a8a' stroke-width='1.5' stroke-dasharray='6 4'/>"
    )

    total_bins = max(1, len(bins))
    bar_w = plot_w / total_bins
    for item in bins:
        x0 = left + item.bin_index * bar_w
        x_mid = x0 + bar_w / 2.0
        if item.avg_target is not None:
            y_target = bottom - (item.avg_target * plot_h)
            rows.append(
                f"<rect x='{x0 + 2:.2f}' y='{y_target:.2f}' "
                f"width='{max(1.0, bar_w - 4):.2f}' "
                f"height='{max(0.0, bottom - y_target):.2f}' "
                "fill='#7db7e8' opacity='0.7'/>"
            )
        if item.avg_confidence is not None:
            y_conf = bottom - (item.avg_confidence * plot_h)
            rows.append(
                f"<circle cx='{x_mid:.2f}' cy='{y_conf:.2f}' r='4' fill='#b11226'/>"
            )

    # Axes labels and ticks.
    rows.extend(
        [
            (
                f"<text x='{(left + right) / 2:.0f}' y='{height - 22}' "
                "font-size='12'>Confidence</text>"
            ),
            (
                f"<text x='20' y='{(top + bottom) / 2:.0f}' "
                "font-size='12' transform='rotate(-90 20 "
                f"{(top + bottom) / 2:.0f})'>Accuracy</text>"
            ),
        ]
    )
    for tick in range(6):
        frac = tick / 5.0
        x = left + frac * plot_w
        y = bottom - frac * plot_h
        rows.append(
            f"<line x1='{x:.2f}' y1='{bottom}' x2='{x:.2f}' y2='{bottom + 5}' stroke='#222'/>"
        )
        rows.append(
            f"<text x='{x:.2f}' y='{bottom + 20}' font-size='11' "
            f"text-anchor='middle'>{frac:.1f}</text>"
        )
        rows.append(
            f"<line x1='{left - 5}' y1='{y:.2f}' x2='{left}' y2='{y:.2f}' stroke='#222'/>"
        )
        rows.append(
            f"<text x='{left - 10}' y='{y + 4:.2f}' font-size='11' "
            f"text-anchor='end'>{frac:.1f}</text>"
        )

    rows.append("</svg>")
    return "\n".join(rows) + "\n"


def render_markdown_report(result: CalibrationResult) -> str:
    """Render markdown calibration report."""
    lines = [
        "# Confidence Calibration Report",
        "",
        "## Scope",
        "",
        "- Expected Calibration Error (ECE)",
        "- reliability diagram data",
        "- Brier score",
        "- temperature scaling",
        "",
        "## Coverage",
        "",
        f"- total_predictions: `{result.total_predictions}`",
        f"- matched_gold_examples: `{result.matched_gold_examples}`",
        f"- unmatched_gold_examples: `{result.unmatched_gold_examples}`",
        f"- target_mode: `{result.target_mode}`",
        f"- score_tolerance: `{result.score_tolerance}`",
        f"- bins: `{result.bins}`",
        "",
        "## Model Calibration Summary",
        "",
        (
            "| model | paired_n | temp | ece_before | ece_after | brier_before | "
            "brier_after | nll_before | nll_after |"
        ),
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result.model_summaries:
        ece_before = f"{row.ece_before:.4f}" if row.ece_before is not None else "n/a"
        ece_after = f"{row.ece_after:.4f}" if row.ece_after is not None else "n/a"
        brier_before = f"{row.brier_before:.4f}" if row.brier_before is not None else "n/a"
        brier_after = f"{row.brier_after:.4f}" if row.brier_after is not None else "n/a"
        nll_before = f"{row.nll_before:.4f}" if row.nll_before is not None else "n/a"
        nll_after = f"{row.nll_after:.4f}" if row.nll_after is not None else "n/a"
        lines.append(
            "| "
            + " | ".join(
                [
                    row.model_id,
                    str(row.paired_examples),
                    f"{row.temperature:.4f}",
                    ece_before,
                    ece_after,
                    brier_before,
                    brier_after,
                    nll_before,
                    nll_after,
                ]
            )
            + " |"
        )

    lines.extend(["", "## Reliability Diagrams", ""])
    lines.append(
        "Per-model reliability bins are available in JSON and SVG under "
        "`reliability_diagrams/` in the output directory."
    )
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_calibration_outputs(*, output_dir: Path, result: CalibrationResult) -> None:
    """Persist calibration outputs to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / "calibration_records.jsonl").open("w", encoding="utf-8") as handle:
        for row in result.records:
            handle.write(json.dumps(asdict(row), ensure_ascii=False, sort_keys=True) + "\n")

    (output_dir / "calibration_summary.json").write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    with (output_dir / "calibration_model_summary.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        if result.model_summaries:
            fieldnames = list(asdict(result.model_summaries[0]).keys())
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in result.model_summaries:
                writer.writerow(asdict(row))

    reliability_dir = output_dir / "reliability_diagrams"
    reliability_dir.mkdir(parents=True, exist_ok=True)
    for row in result.reliability:
        model_slug = _sanitize_filename(row.model_id)
        json_payload = {
            "model_id": row.model_id,
            "bins_before": [asdict(item) for item in row.bins_before],
            "bins_after": [asdict(item) for item in row.bins_after],
        }
        (reliability_dir / f"{model_slug}.json").write_text(
            json.dumps(json_payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        (reliability_dir / f"{model_slug}_before.svg").write_text(
            render_reliability_svg(row.bins_before, title=f"{row.model_id} (before scaling)"),
            encoding="utf-8",
        )
        (reliability_dir / f"{model_slug}_after.svg").write_text(
            render_reliability_svg(row.bins_after, title=f"{row.model_id} (after scaling)"),
            encoding="utf-8",
        )

    (output_dir / "calibration_report.md").write_text(
        render_markdown_report(result),
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run confidence calibration analysis.")
    parser.add_argument("--gold-path", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--predictions-path", required=True)
    parser.add_argument("--output-dir", default="outputs/calibration")
    parser.add_argument("--bins", type=int, default=10)
    parser.add_argument(
        "--target-mode",
        choices=TARGET_MODES,
        default=TARGET_MODE_SCORE_AND_FALLACY,
    )
    parser.add_argument("--score-tolerance", type=float, default=1.0)
    parser.add_argument("--overconfidence-threshold", type=float, default=0.8)
    parser.add_argument("--temperature-grid-min", type=float, default=0.25)
    parser.add_argument("--temperature-grid-max", type=float, default=4.0)
    parser.add_argument("--temperature-grid-size", type=int, default=200)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    config = CalibrationConfig(
        gold_path=Path(args.gold_path),
        predictions_path=Path(args.predictions_path),
        output_dir=Path(args.output_dir),
        bins=int(args.bins),
        target_mode=str(args.target_mode),
        score_tolerance=float(args.score_tolerance),
        overconfidence_threshold=float(args.overconfidence_threshold),
        temperature_grid_min=float(args.temperature_grid_min),
        temperature_grid_max=float(args.temperature_grid_max),
        temperature_grid_size=int(args.temperature_grid_size),
    )
    result = analyze_calibration(config)
    write_calibration_outputs(output_dir=config.output_dir, result=result)
    print(json.dumps(asdict(result), ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
