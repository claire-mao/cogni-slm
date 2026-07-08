"""Public interfaces for the Cogni evaluation package."""

from evaluation.benchmark import BenchmarkLoader, BenchmarkRecord, JSONLBenchmarkLoader, SplitName
from evaluation.deterministic_checks import (
    BehaviorId,
    CheckInput,
    CheckResult,
    DefaultDeterministicCheckSuite,
    DeterministicCheckSuite,
    ProhibitionId,
)
from evaluation.evaluator import ComparisonPayload, EvaluationConfig, EvaluationRunner, ModelAdapter
from evaluation.llm_judge import DefaultLLMJudge, JudgeInput, JudgeResult, JudgeRubric, LLMJudge
from evaluation.metrics import (
    AggregateMetric,
    ComparisonResult,
    GateOutcome,
    PerExampleMetric,
    aggregate_metrics,
    evaluate_gated_composite,
    paired_model_comparison,
)
from evaluation.report import (
    DefaultReportRenderer,
    EvaluationSummary,
    ExampleTrace,
    ReportRenderer,
)

__all__ = [
    "AggregateMetric",
    "BehaviorId",
    "BenchmarkLoader",
    "BenchmarkRecord",
    "CheckInput",
    "CheckResult",
    "ComparisonPayload",
    "ComparisonResult",
    "DefaultDeterministicCheckSuite",
    "DefaultLLMJudge",
    "DefaultReportRenderer",
    "DeterministicCheckSuite",
    "EvaluationConfig",
    "EvaluationRunner",
    "EvaluationSummary",
    "ExampleTrace",
    "GateOutcome",
    "JSONLBenchmarkLoader",
    "JudgeInput",
    "JudgeResult",
    "JudgeRubric",
    "LLMJudge",
    "ModelAdapter",
    "PerExampleMetric",
    "ProhibitionId",
    "ReportRenderer",
    "SplitName",
    "aggregate_metrics",
    "evaluate_gated_composite",
    "paired_model_comparison",
]
