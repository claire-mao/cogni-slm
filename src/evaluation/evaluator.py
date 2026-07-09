"""Top-level orchestration for paired base-vs-tuned evaluation runs."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any, Protocol

from .benchmark import BenchmarkLoader, BenchmarkRecord, SplitName
from .deterministic_checks import CheckInput, DeterministicCheckSuite
from .llm_judge import JudgeInput, JudgeRubric, LLMJudge
from .metrics import (
    ComparisonResult,
    GateOutcome,
    PerExampleMetric,
    aggregate_metrics,
    evaluate_gated_composite,
    paired_model_comparison,
)
from .report import EvaluationSummary, ExampleTrace, ReportRenderer


@dataclass(frozen=True)
class EvaluationConfig:
    """Configuration contract for one base-vs-tuned evaluation run."""

    run_id: str
    dataset_version: str
    taxonomy_version: str
    splits: tuple[SplitName, ...]
    dimensions: tuple[str, ...]
    judge_rubrics: tuple[JudgeRubric, ...]
    comparison_method: str = "paired_bootstrap"
    required_improvement_dims: tuple[str, ...] = (
        "behavior_adherence",
        "fallacy_accuracy",
    )
    no_regression_dims: tuple[str, ...] = (
        "robustness",
        "consistency",
    )
    threshold_config: Mapping[str, float] | None = None
    assumptions: Mapping[str, str] = field(default_factory=dict)


class ModelAdapter(Protocol):
    """Abstract model interface used by the evaluation runner."""

    @property
    def model_id(self) -> str:
        """Stable model identifier for reporting and comparison."""

    def generate(self, record: BenchmarkRecord) -> str:
        """Generate one output for a benchmark record."""


@dataclass(frozen=True)
class ComparisonPayload:
    """Standardized comparison payload used by report and downstream consumers."""

    run_id: str
    base_model_id: str
    tuned_model_id: str
    per_example_traces: tuple[ExampleTrace, ...]
    aggregate_comparisons: tuple[ComparisonResult, ...]
    gate_outcomes: tuple[GateOutcome, ...]
    assumptions: Mapping[str, str]


def _extract_predicted_fallacy(response_text: str) -> str | None:
    # Prefer explicit structured field.
    explicit = re.search(r"fallacy[_\s]hypothesis\s*[:\-]\s*([^\n]+)", response_text, re.IGNORECASE)
    if explicit:
        return explicit.group(1).strip().lower().replace(" ", "_")

    fallback = re.search(r"fallacy\s*[:\-]\s*([^\n]+)", response_text, re.IGNORECASE)
    if fallback:
        return fallback.group(1).strip().lower().replace(" ", "_")

    return None


def _score_fallacy_accuracy(record: BenchmarkRecord, response_text: str) -> float:
    predicted = _extract_predicted_fallacy(response_text)
    expected = (record.primary_fallacy_label or "").strip().lower().replace(" ", "_") or None
    alternates = {
        label.strip().lower().replace(" ", "_") for label in record.acceptable_alternative_labels
    }

    if expected is None:
        return (
            1.0
            if predicted in {None, "none", "no_fallacy", "no_fallacy_detected", "valid_reasoning"}
            else 0.0
        )

    if predicted == expected:
        return 1.0
    if predicted in alternates:
        return 0.5
    return 0.0


def _check_input_from_record(
    run_id: str,
    model_id: str,
    record: BenchmarkRecord,
    response_text: str,
) -> CheckInput:
    return CheckInput(
        run_id=run_id,
        model_id=model_id,
        example_id=record.example_id,
        split=record.split,
        response_text=response_text,
        expected_sections=record.expected_sections,
        required_behaviors=tuple(record.required_behaviors),
        prohibited_behaviors=tuple(record.prohibited_behaviors),
        metadata={
            "argument_text": record.argument_text,
            "is_adversarial": record.is_adversarial,
            **record.metadata,
        },
    )


def _scores_to_metrics(
    *,
    run_id: str,
    model_id: str,
    record: BenchmarkRecord,
    deterministic_scores: Sequence[float],
    consistency_score: float,
    robustness_score: float,
    fallacy_accuracy_score: float,
    judge_results: Sequence[Any],
) -> list[PerExampleMetric]:
    metrics: list[PerExampleMetric] = []

    behavior_adherence = mean(deterministic_scores) if deterministic_scores else 0.0
    metrics.append(
        PerExampleMetric(
            run_id=run_id,
            model_id=model_id,
            example_id=record.example_id,
            split=record.split,
            dimension="behavior_adherence",
            score=behavior_adherence,
        )
    )
    metrics.append(
        PerExampleMetric(
            run_id=run_id,
            model_id=model_id,
            example_id=record.example_id,
            split=record.split,
            dimension="fallacy_accuracy",
            score=fallacy_accuracy_score,
        )
    )
    metrics.append(
        PerExampleMetric(
            run_id=run_id,
            model_id=model_id,
            example_id=record.example_id,
            split=record.split,
            dimension="robustness",
            score=robustness_score,
        )
    )
    metrics.append(
        PerExampleMetric(
            run_id=run_id,
            model_id=model_id,
            example_id=record.example_id,
            split=record.split,
            dimension="consistency",
            score=consistency_score,
        )
    )

    for judge_result in judge_results:
        metrics.append(
            PerExampleMetric(
                run_id=run_id,
                model_id=model_id,
                example_id=record.example_id,
                split=record.split,
                dimension=judge_result.dimension,
                score=judge_result.score,
                confidence_interval=judge_result.confidence_interval,
                metadata={"rubric_id": judge_result.rubric_id},
            )
        )

    return metrics


class EvaluationRunner:
    """Evaluation orchestrator for deterministic checks, judging, and reporting."""

    def __init__(
        self,
        config: EvaluationConfig,
        benchmark_loader: BenchmarkLoader,
        deterministic_suite: DeterministicCheckSuite,
        judge: LLMJudge,
        report_renderer: ReportRenderer,
    ) -> None:
        self.config = config
        self.benchmark_loader = benchmark_loader
        self.deterministic_suite = deterministic_suite
        self.judge = judge
        self.report_renderer = report_renderer

    def _score_model_response(
        self,
        model: ModelAdapter,
        record: BenchmarkRecord,
    ) -> tuple[str, tuple[Any, ...], tuple[Any, ...], list[PerExampleMetric]]:
        response_text = model.generate(record)
        check_input = _check_input_from_record(
            self.config.run_id,
            model.model_id,
            record,
            response_text,
        )

        deterministic_results = tuple(self.deterministic_suite.run(check_input))
        findings = tuple(
            f"{result.check_id}:{result.violation_code or 'ok'}"
            for result in deterministic_results
            if not result.passed
        )
        judge_input = JudgeInput(
            run_id=self.config.run_id,
            model_id=model.model_id,
            example_id=record.example_id,
            split=record.split,
            record=record,
            response_text=response_text,
            deterministic_findings=findings,
            metadata=record.metadata,
        )
        judge_results = tuple(self.judge.score(judge_input, self.config.judge_rubrics))

        deterministic_scores = [result.score for result in deterministic_results]
        b7_scores = [result.score for result in deterministic_results if result.check_id == "B7"]
        safety_scores = [
            result.score for result in deterministic_results if result.check_id in {"B5", "P5"}
        ]

        default_score = mean(deterministic_scores) if deterministic_scores else 0.0
        consistency_score = b7_scores[0] if b7_scores else default_score
        robustness_base = mean(safety_scores) if safety_scores else default_score
        robustness_score = (
            robustness_base if record.is_adversarial else min(1.0, robustness_base + 0.1)
        )

        fallacy_accuracy_score = _score_fallacy_accuracy(record, response_text)

        metrics = _scores_to_metrics(
            run_id=self.config.run_id,
            model_id=model.model_id,
            record=record,
            deterministic_scores=deterministic_scores,
            consistency_score=consistency_score,
            robustness_score=robustness_score,
            fallacy_accuracy_score=fallacy_accuracy_score,
            judge_results=judge_results,
        )

        return response_text, deterministic_results, judge_results, metrics

    def run_comparison(
        self,
        base_model: ModelAdapter,
        tuned_model: ModelAdapter,
    ) -> tuple[EvaluationSummary, ComparisonPayload]:
        """Run the complete paired base-vs-tuned evaluation workflow."""
        traces: list[ExampleTrace] = []
        base_metrics: list[PerExampleMetric] = []
        tuned_metrics: list[PerExampleMetric] = []

        for split in self.config.splits:
            for record in self.benchmark_loader.load_split(split):
                if record.split != split:
                    # Keep comparison consistent with requested split routing.
                    continue

                base_output, base_det, base_judge, base_example_metrics = (
                    self._score_model_response(
                        base_model,
                        record,
                    )
                )
                tuned_output, tuned_det, tuned_judge, tuned_example_metrics = (
                    self._score_model_response(
                        tuned_model,
                        record,
                    )
                )

                traces.append(
                    ExampleTrace(
                        run_id=self.config.run_id,
                        example_id=record.example_id,
                        split=record.split,
                        base_model_id=base_model.model_id,
                        tuned_model_id=tuned_model.model_id,
                        base_output=base_output,
                        tuned_output=tuned_output,
                        base_deterministic=tuple(base_det),
                        tuned_deterministic=tuple(tuned_det),
                        base_judge=tuple(base_judge),
                        tuned_judge=tuple(tuned_judge),
                        metadata={
                            "is_adversarial": record.is_adversarial,
                            "adversarial_type": record.adversarial_type,
                            "attack_target": record.attack_target,
                        },
                    )
                )

                base_metrics.extend(base_example_metrics)
                tuned_metrics.extend(tuned_example_metrics)

        all_metrics = tuple(base_metrics + tuned_metrics)
        aggregate = tuple(aggregate_metrics(all_metrics))
        comparisons = tuple(
            paired_model_comparison(
                base=base_metrics,
                tuned=tuned_metrics,
                method=self.config.comparison_method,
            )
        )
        gates = tuple(
            evaluate_gated_composite(
                comparisons,
                required_improvement_dims=self.config.required_improvement_dims,
                no_regression_dims=self.config.no_regression_dims,
                threshold_config=self.config.threshold_config,
            )
        )

        summary = EvaluationSummary(
            run_id=self.config.run_id,
            base_model_id=base_model.model_id,
            tuned_model_id=tuned_model.model_id,
            dataset_version=self.config.dataset_version,
            taxonomy_version=self.config.taxonomy_version,
            comparison_method=self.config.comparison_method,
            aggregate_metrics=aggregate,
            gate_outcomes=gates,
            assumptions=self.config.assumptions,
        )

        payload = ComparisonPayload(
            run_id=self.config.run_id,
            base_model_id=base_model.model_id,
            tuned_model_id=tuned_model.model_id,
            per_example_traces=tuple(traces),
            aggregate_comparisons=comparisons,
            gate_outcomes=gates,
            assumptions=self.config.assumptions,
        )
        return summary, payload

    def export_artifacts(
        self,
        summary: EvaluationSummary,
        payload: ComparisonPayload,
        output_root: str,
    ) -> Mapping[str, Any]:
        """Write markdown/json reports and trace artifacts under outputs/."""
        run_dir = Path(output_root) / summary.run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        report_md = self.report_renderer.render_markdown(summary, payload.per_example_traces)
        report_json = self.report_renderer.render_json(summary, payload.per_example_traces)
        report_json["comparisons"] = [asdict(item) for item in payload.aggregate_comparisons]

        report_path = run_dir / "report.md"
        summary_path = run_dir / "summary.json"
        traces_path = run_dir / "traces.jsonl"

        report_path.write_text(report_md, encoding="utf-8")
        summary_path.write_text(
            json.dumps(report_json, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        with traces_path.open("w", encoding="utf-8") as handle:
            for trace in payload.per_example_traces:
                handle.write(json.dumps(asdict(trace), ensure_ascii=False) + "\n")

        return {
            "run_id": summary.run_id,
            "run_dir": str(run_dir),
            "report_md": str(report_path),
            "summary_json": str(summary_path),
            "traces_jsonl": str(traces_path),
        }
