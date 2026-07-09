"""Metrics for base-vs-tuned essay-evaluation comparison harness."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from statistics import mean

try:
    from .harness_feedback import FeedbackQualityResult
except ImportError:  # pragma: no cover - script-mode import fallback
    from harness_feedback import FeedbackQualityResult


@dataclass(frozen=True)
class ModelMetricSummary:
    """Aggregate metrics for one model."""

    total_examples: int
    valid_score_predictions: int
    score_accuracy: float
    mae: float
    quadratic_weighted_kappa: float
    feedback_quality: float


def _to_ordinal(values: list[float]) -> list[int]:
    return [int(round(item)) for item in values]


def quadratic_weighted_kappa(y_true: list[float], y_pred: list[float]) -> float:
    """Compute quadratic weighted kappa on rounded ordinal scores."""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0

    true_int = _to_ordinal(y_true)
    pred_int = _to_ordinal(y_pred)

    min_rating = min(min(true_int), min(pred_int))
    max_rating = max(max(true_int), max(pred_int))
    num_ratings = max_rating - min_rating + 1

    if num_ratings <= 1:
        return 1.0

    true_shifted = [value - min_rating for value in true_int]
    pred_shifted = [value - min_rating for value in pred_int]

    observed = [[0.0 for _ in range(num_ratings)] for _ in range(num_ratings)]
    for t, p in zip(true_shifted, pred_shifted, strict=True):
        observed[t][p] += 1.0

    true_hist = Counter(true_shifted)
    pred_hist = Counter(pred_shifted)
    n = float(len(true_shifted))

    expected = [[0.0 for _ in range(num_ratings)] for _ in range(num_ratings)]
    for i in range(num_ratings):
        for j in range(num_ratings):
            expected[i][j] = (true_hist.get(i, 0) * pred_hist.get(j, 0)) / n

    denominator_scale = float((num_ratings - 1) ** 2)

    weighted_observed = 0.0
    weighted_expected = 0.0

    for i in range(num_ratings):
        for j in range(num_ratings):
            weight = ((i - j) ** 2) / denominator_scale
            weighted_observed += weight * observed[i][j]
            weighted_expected += weight * expected[i][j]

    if weighted_expected == 0.0:
        return 1.0 if weighted_observed == 0.0 else 0.0

    return 1.0 - (weighted_observed / weighted_expected)


def summarize_model_metrics(
    gold_scores: list[float],
    predicted_scores: list[float | None],
    feedback_quality: list[FeedbackQualityResult],
) -> ModelMetricSummary:
    """Aggregate score metrics and feedback quality for one model."""
    total_examples = len(gold_scores)

    paired = [
        (gold, pred)
        for gold, pred in zip(gold_scores, predicted_scores, strict=True)
        if pred is not None
    ]

    valid_score_predictions = len(paired)

    if not paired:
        accuracy = 0.0
        mae = 0.0
        qwk = 0.0
    else:
        accuracy = mean(
            1.0 if int(round(gold)) == int(round(pred)) else 0.0 for gold, pred in paired
        )
        mae = mean(abs(gold - pred) for gold, pred in paired)
        qwk = quadratic_weighted_kappa(
            [gold for gold, _ in paired],
            [pred for _, pred in paired],
        )

    feedback_quality_mean = (
        mean(item.score for item in feedback_quality) if feedback_quality else 0.0
    )

    return ModelMetricSummary(
        total_examples=total_examples,
        valid_score_predictions=valid_score_predictions,
        score_accuracy=accuracy,
        mae=mae,
        quadratic_weighted_kappa=qwk,
        feedback_quality=feedback_quality_mean,
    )
