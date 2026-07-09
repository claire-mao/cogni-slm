"""Metrics aggregation and paired base-vs-tuned comparison utilities."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import comb, sqrt
from statistics import mean, pstdev
from typing import Any

from .benchmark import SplitName


@dataclass(frozen=True)
class PerExampleMetric:
    """Standardized per-example metric payload."""

    run_id: str
    model_id: str
    example_id: str
    split: SplitName
    dimension: str
    score: float
    confidence_interval: tuple[float, float] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AggregateMetric:
    """Aggregated metric result for one split and dimension."""

    run_id: str
    model_id: str
    split: SplitName
    dimension: str
    score: float
    sample_size: int
    confidence_interval: tuple[float, float] | None = None


@dataclass(frozen=True)
class ComparisonResult:
    """Paired base-vs-tuned comparison outcome."""

    run_id: str
    dimension: str
    split: SplitName
    base_model_id: str
    tuned_model_id: str
    delta: float
    confidence_interval: tuple[float, float] | None
    p_value: float | None = None
    method: str = "paired_bootstrap"


@dataclass(frozen=True)
class GateOutcome:
    """Pass/fail decision for one composite gate dimension."""

    run_id: str
    dimension: str
    passed: bool
    reason: str


def _normal_ci(samples: Sequence[float]) -> tuple[float, float] | None:
    if not samples:
        return None
    if len(samples) == 1:
        return (samples[0], samples[0])

    mu = mean(samples)
    sigma = pstdev(samples)
    margin = 1.96 * sigma / sqrt(len(samples)) if sigma > 0 else 0.0
    return (mu - margin, mu + margin)


def aggregate_metrics(
    per_example: Sequence[PerExampleMetric],
) -> Sequence[AggregateMetric]:
    """Aggregate per-example metric values into split/dimension summaries."""
    grouped: dict[tuple[str, str, SplitName, str], list[float]] = {}

    for metric in per_example:
        key = (metric.run_id, metric.model_id, metric.split, metric.dimension)
        grouped.setdefault(key, []).append(metric.score)

    aggregates: list[AggregateMetric] = []
    for (run_id, model_id, split, dimension), values in sorted(grouped.items()):
        aggregates.append(
            AggregateMetric(
                run_id=run_id,
                model_id=model_id,
                split=split,
                dimension=dimension,
                score=mean(values),
                sample_size=len(values),
                confidence_interval=_normal_ci(values),
            )
        )

    return tuple(aggregates)


def _binomial_two_sided_pvalue(num_positive: int, total: int) -> float | None:
    if total <= 0:
        return None

    # Exact two-sided sign-test p-value under p=0.5.
    tail = min(num_positive, total - num_positive)
    cumulative = sum(comb(total, k) for k in range(tail + 1))
    p_one_tail = cumulative / (2**total)
    return min(1.0, 2 * p_one_tail)


def paired_model_comparison(
    base: Sequence[PerExampleMetric],
    tuned: Sequence[PerExampleMetric],
    *,
    method: str = "paired_bootstrap",
) -> Sequence[ComparisonResult]:
    """Compute paired base-vs-tuned comparison statistics."""
    base_index = {(m.example_id, m.split, m.dimension): m for m in base}
    tuned_index = {(m.example_id, m.split, m.dimension): m for m in tuned}

    shared_keys = sorted(set(base_index) & set(tuned_index))
    grouped_deltas: dict[tuple[str, SplitName], list[float]] = {}

    run_id = ""
    base_model_id = ""
    tuned_model_id = ""

    for key in shared_keys:
        base_metric = base_index[key]
        tuned_metric = tuned_index[key]
        run_id = run_id or base_metric.run_id
        base_model_id = base_model_id or base_metric.model_id
        tuned_model_id = tuned_model_id or tuned_metric.model_id
        _, split, dimension = key
        grouped_deltas.setdefault((dimension, split), []).append(
            tuned_metric.score - base_metric.score
        )

    comparisons: list[ComparisonResult] = []
    for (dimension, split), deltas in sorted(grouped_deltas.items()):
        ci = _normal_ci(deltas)
        positives = sum(1 for delta in deltas if delta > 0)
        p_value = _binomial_two_sided_pvalue(positives, len(deltas))
        comparisons.append(
            ComparisonResult(
                run_id=run_id,
                dimension=dimension,
                split=split,
                base_model_id=base_model_id,
                tuned_model_id=tuned_model_id,
                delta=mean(deltas) if deltas else 0.0,
                confidence_interval=ci,
                p_value=p_value,
                method=method,
            )
        )

    return tuple(comparisons)


def evaluate_gated_composite(
    comparisons: Sequence[ComparisonResult],
    *,
    required_improvement_dims: Sequence[str],
    no_regression_dims: Sequence[str],
    threshold_config: Mapping[str, float] | None = None,
) -> Sequence[GateOutcome]:
    """Evaluate pass/fail gates for the tuned model."""
    threshold_config = dict(threshold_config or {})
    improvement_min = float(threshold_config.get("improvement_min", 0.0))
    no_regression_min = float(threshold_config.get("no_regression_min", 0.0))

    by_dimension: dict[str, list[ComparisonResult]] = {}
    for comparison in comparisons:
        by_dimension.setdefault(comparison.dimension, []).append(comparison)

    outcomes: list[GateOutcome] = []

    for dimension in required_improvement_dims:
        rows = by_dimension.get(dimension, [])
        if not rows:
            outcomes.append(
                GateOutcome(
                    run_id=comparisons[0].run_id if comparisons else "",
                    dimension=dimension,
                    passed=False,
                    reason="No comparison rows available for required improvement dimension.",
                )
            )
            continue

        avg_delta = mean(row.delta for row in rows)
        passed = avg_delta > improvement_min
        outcomes.append(
            GateOutcome(
                run_id=rows[0].run_id,
                dimension=dimension,
                passed=passed,
                reason=(
                    f"Average delta {avg_delta:.4f} exceeds improvement threshold "
                    f"{improvement_min:.4f}."
                    if passed
                    else f"Average delta {avg_delta:.4f} does not exceed {improvement_min:.4f}."
                ),
            )
        )

    for dimension in no_regression_dims:
        rows = by_dimension.get(dimension, [])
        if not rows:
            outcomes.append(
                GateOutcome(
                    run_id=comparisons[0].run_id if comparisons else "",
                    dimension=dimension,
                    passed=False,
                    reason="No comparison rows available for no-regression dimension.",
                )
            )
            continue

        avg_delta = mean(row.delta for row in rows)
        passed = avg_delta >= no_regression_min
        outcomes.append(
            GateOutcome(
                run_id=rows[0].run_id,
                dimension=dimension,
                passed=passed,
                reason=(
                    f"Average delta {avg_delta:.4f} meets no-regression floor "
                    f"{no_regression_min:.4f}."
                    if passed
                    else f"Average delta {avg_delta:.4f} is below {no_regression_min:.4f}."
                ),
            )
        )

    return tuple(outcomes)
