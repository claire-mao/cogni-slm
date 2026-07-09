"""Teacher benchmarking package."""

from .benchmark import (
    ModelSummary,
    PerExampleMetricRow,
    run_benchmark,
    write_benchmark_outputs,
)
from .io import GoldExample, PredictionRecord, load_gold_examples, load_predictions
from .models import SUPPORTED_MODELS, canonical_model_id
from .prompt_registry import (
    DEFAULT_VERSIONS_ROOT,
    ABAssignment,
    ABVariant,
    PromptRegistry,
    PromptVersion,
    compute_prompt_hash,
    get_default_prompt_registry,
)
from .prompt_versioning import (
    DEFAULT_PROMPTS_ROOT,
    PromptVersionManager,
    PromptVersionRecord,
    RollbackRecord,
    compute_checksum,
)
from .providers import (
    TeacherExample,
    TeacherProvider,
    canonical_provider_name,
    create_teacher_provider,
)
from .validation import (
    ExampleValidationResult,
    ModelValidationSummary,
    ValidationFinding,
    run_validation,
    summarize_validation,
    validate_prediction,
    write_validation_outputs,
)

__all__ = [
    "GoldExample",
    "ModelSummary",
    "PerExampleMetricRow",
    "PredictionRecord",
    "SUPPORTED_MODELS",
    "TeacherExample",
    "TeacherProvider",
    "PromptRegistry",
    "PromptVersion",
    "PromptVersionManager",
    "PromptVersionRecord",
    "ABVariant",
    "ABAssignment",
    "DEFAULT_VERSIONS_ROOT",
    "DEFAULT_PROMPTS_ROOT",
    "RollbackRecord",
    "ValidationFinding",
    "ExampleValidationResult",
    "ModelValidationSummary",
    "canonical_provider_name",
    "canonical_model_id",
    "compute_prompt_hash",
    "compute_checksum",
    "create_teacher_provider",
    "get_default_prompt_registry",
    "load_gold_examples",
    "load_predictions",
    "run_benchmark",
    "run_validation",
    "summarize_validation",
    "validate_prediction",
    "write_benchmark_outputs",
    "write_validation_outputs",
]
