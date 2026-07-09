"""Task metrics for teacher benchmark evaluation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from math import ceil
from statistics import mean


def _to_tokens(items: Iterable[str]) -> set[str]:
    return {item.strip().lower() for item in items if item and item.strip()}


def clamp01(value: float) -> float:
    """Clamp metric to [0, 1]."""
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return value


def f1_precision_recall(
    expected: Iterable[str],
    predicted: Iterable[str],
) -> tuple[float, float, float]:
    """Set-based precision, recall, F1."""
    expected_set = _to_tokens(expected)
    predicted_set = _to_tokens(predicted)

    if not expected_set and not predicted_set:
        return 1.0, 1.0, 1.0
    if not predicted_set:
        return 0.0, 0.0, 0.0

    true_positive = len(expected_set & predicted_set)
    precision = true_positive / len(predicted_set) if predicted_set else 0.0
    recall = true_positive / len(expected_set) if expected_set else 0.0
    if precision + recall == 0:
        f1 = 0.0
    else:
        f1 = (2 * precision * recall) / (precision + recall)
    return precision, recall, f1


def _to_ordinal(values: list[float]) -> list[int]:
    return [int(round(value)) for value in values]


def quadratic_weighted_kappa(y_true: list[float], y_pred: list[float]) -> float:
    """Compute quadratic weighted kappa for ordinal scores."""
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
    for truth, pred in zip(true_shifted, pred_shifted, strict=True):
        observed[truth][pred] += 1.0

    true_hist = Counter(true_shifted)
    pred_hist = Counter(pred_shifted)
    n = float(len(true_shifted))

    expected = [[0.0 for _ in range(num_ratings)] for _ in range(num_ratings)]
    for i in range(num_ratings):
        for j in range(num_ratings):
            expected[i][j] = (true_hist.get(i, 0) * pred_hist.get(j, 0)) / n

    denominator = float((num_ratings - 1) ** 2)
    weighted_observed = 0.0
    weighted_expected = 0.0
    for i in range(num_ratings):
        for j in range(num_ratings):
            weight = ((i - j) ** 2) / denominator
            weighted_observed += weight * observed[i][j]
            weighted_expected += weight * expected[i][j]

    if weighted_expected == 0.0:
        return 1.0 if weighted_observed == 0.0 else 0.0
    return 1.0 - (weighted_observed / weighted_expected)


def mae(y_true: list[float], y_pred: list[float]) -> float:
    """Mean absolute error."""
    if not y_true or not y_pred or len(y_true) != len(y_pred):
        return 0.0
    return mean(abs(truth - pred) for truth, pred in zip(y_true, y_pred, strict=True))


def percentile(sorted_values: list[float], p: float) -> float:
    """Simple percentile calculation with linear index rounding."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return sorted_values[0]
    index = ceil((p / 100.0) * len(sorted_values)) - 1
    index = max(0, min(index, len(sorted_values) - 1))
    return sorted_values[index]


def feedback_usefulness_score(
    feedback_text: str,
    expected_reasoning_skills: Iterable[str],
    rubric_items: Iterable[str],
    reviewer_notes: str,
) -> float:
    """Deterministic feedback usefulness proxy in [0,1]."""
    text = feedback_text.strip().lower()
    if not text:
        return 0.0

    words = [token for token in text.replace("\n", " ").split(" ") if token]
    length_score = 1.0 if 20 <= len(words) <= 280 else 0.5

    action_keywords = {
        "revise",
        "clarify",
        "support",
        "explain",
        "add",
        "remove",
        "organize",
        "strengthen",
        "counterargument",
        "evidence",
    }
    action_hits = sum(1 for token in words if token.strip(".,!?;:") in action_keywords)
    actionability_score = 1.0 if action_hits >= 2 else (0.5 if action_hits == 1 else 0.0)

    expected_terms = _to_tokens(list(expected_reasoning_skills) + list(rubric_items))
    note_terms = _to_tokens([reviewer_notes])
    overlap_basis = expected_terms | note_terms
    if not overlap_basis:
        relevance_score = 0.5
    else:
        feedback_terms = _to_tokens(words)
        overlap = len(feedback_terms & overlap_basis)
        relevance_score = clamp01(overlap / max(1, min(8, len(overlap_basis))))

    return clamp01((length_score + actionability_score + relevance_score) / 3.0)
