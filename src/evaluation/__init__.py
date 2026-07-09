"""Public interfaces for the Cogni evaluation package."""

from .benchmark import BenchmarkLoader, BenchmarkRecord, JSONLBenchmarkLoader, SplitName
from .deterministic_checks import (
    BehaviorId,
    CheckInput,
    CheckResult,
    DefaultDeterministicCheckSuite,
    DeterministicCheckSuite,
    ProhibitionId,
)
from .evaluator import ComparisonPayload, EvaluationConfig, EvaluationRunner, ModelAdapter
from .judge import (
    DefaultBehaviorJudge,
    JudgeBackend,
    JudgeDimensionScore,
    JudgeInputRecord,
    JudgeOutputRecord,
    ResponseJudge,
)
from .llm_judge import DefaultLLMJudge, JudgeInput, JudgeResult, JudgeRubric, LLMJudge
from .metrics import (
    AggregateMetric,
    ComparisonResult,
    GateOutcome,
    PerExampleMetric,
    aggregate_metrics,
    evaluate_gated_composite,
    paired_model_comparison,
)
from .report import (
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
    "JudgeBackend",
    "JudgeDimensionScore",
    "JudgeInputRecord",
    "JudgeOutputRecord",
    "JudgeInput",
    "JudgeResult",
    "JudgeRubric",
    "LLMJudge",
    "DefaultBehaviorJudge",
    "ModelAdapter",
    "PerExampleMetric",
    "ProhibitionId",
    "ResponseJudge",
    "ReportRenderer",
    "SplitName",
    "aggregate_metrics",
    "evaluate_gated_composite",
    "paired_model_comparison",
]
