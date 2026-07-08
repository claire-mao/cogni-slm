"""Report rendering for evaluation summaries and traces."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from evaluation.benchmark import SplitName
from evaluation.deterministic_checks import CheckResult
from evaluation.llm_judge import JudgeResult
from evaluation.metrics import AggregateMetric, GateOutcome


@dataclass(frozen=True)
class ExampleTrace:
    """Paired per-example trace used for auditability."""

    run_id: str
    example_id: str
    split: SplitName
    base_model_id: str
    tuned_model_id: str
    base_output: str
    tuned_output: str
    base_deterministic: tuple[CheckResult, ...] = ()
    tuned_deterministic: tuple[CheckResult, ...] = ()
    base_judge: tuple[JudgeResult, ...] = ()
    tuned_judge: tuple[JudgeResult, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EvaluationSummary:
    """Top-level summary payload for one evaluation run."""

    run_id: str
    base_model_id: str
    tuned_model_id: str
    dataset_version: str
    taxonomy_version: str
    comparison_method: str
    aggregate_metrics: tuple[AggregateMetric, ...]
    gate_outcomes: tuple[GateOutcome, ...]
    assumptions: Mapping[str, str]


class ReportRenderer(Protocol):
    """Contract for report rendering and machine-readable outputs."""

    def render_markdown(
        self,
        summary: EvaluationSummary,
        traces: Sequence[ExampleTrace],
    ) -> str:
        """Render a human-readable markdown report."""

    def render_json(
        self,
        summary: EvaluationSummary,
        traces: Sequence[ExampleTrace],
    ) -> dict[str, Any]:
        """Render a machine-readable JSON payload."""


class DefaultReportRenderer:
    """Default markdown/json report renderer."""

    def _render_metrics_table(self, metrics: Sequence[AggregateMetric]) -> str:
        lines = [
            "| Model | Split | Dimension | Score | Sample Size | 95% CI |",
            "|---|---|---|---:|---:|---|",
        ]
        for metric in sorted(metrics, key=lambda row: (row.model_id, row.split, row.dimension)):
            ci = (
                f"[{metric.confidence_interval[0]:.4f}, {metric.confidence_interval[1]:.4f}]"
                if metric.confidence_interval
                else "n/a"
            )
            lines.append(
                f"| {metric.model_id} | {metric.split} | {metric.dimension} "
                f"| {metric.score:.4f} | {metric.sample_size} | {ci} |"
            )
        return "\n".join(lines)

    def _render_gates_table(self, gates: Sequence[GateOutcome]) -> str:
        lines = [
            "| Dimension | Status | Reason |",
            "|---|---|---|",
        ]
        for gate in gates:
            status = "pass" if gate.passed else "fail"
            lines.append(f"| {gate.dimension} | {status} | {gate.reason} |")
        return "\n".join(lines)

    def render_markdown(
        self,
        summary: EvaluationSummary,
        traces: Sequence[ExampleTrace],
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        trace_count = len(traces)

        return "\n\n".join(
            [
                "# Evaluation Report",
                (
                    f"Generated: {now}\n"
                    f"Run ID: `{summary.run_id}`\n"
                    f"Base model: `{summary.base_model_id}`\n"
                    f"Tuned model: `{summary.tuned_model_id}`\n"
                    f"Dataset version: `{summary.dataset_version}`\n"
                    f"Taxonomy version: `{summary.taxonomy_version}`\n"
                    f"Comparison method: `{summary.comparison_method}`\n"
                    f"Trace count: `{trace_count}`"
                ),
                "## Aggregate Metrics\n" + self._render_metrics_table(summary.aggregate_metrics),
                "## Gate Outcomes\n" + self._render_gates_table(summary.gate_outcomes),
                "## Assumptions\n"
                + "\n".join(f"- **{key}**: {value}" for key, value in summary.assumptions.items()),
            ]
        )

    def render_json(
        self,
        summary: EvaluationSummary,
        traces: Sequence[ExampleTrace],
    ) -> dict[str, Any]:
        return {
            "run_id": summary.run_id,
            "base_model_id": summary.base_model_id,
            "tuned_model_id": summary.tuned_model_id,
            "dataset_version": summary.dataset_version,
            "taxonomy_version": summary.taxonomy_version,
            "comparison_method": summary.comparison_method,
            "metrics": [asdict(metric) for metric in summary.aggregate_metrics],
            "gate_outcomes": [asdict(gate) for gate in summary.gate_outcomes],
            "assumptions": dict(summary.assumptions),
            "trace_count": len(traces),
            "traces": [asdict(trace) for trace in traces],
        }
