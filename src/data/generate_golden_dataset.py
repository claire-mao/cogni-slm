"""Generate a golden synthetic dataset (~50 examples) for manual review."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from data import (
    DedupConfig,
    DefaultCandidateFilter,
    DefaultDatasetValidator,
    DefaultDeduplicator,
    DefaultPromptRegistry,
    DefaultPromptRenderer,
    GenerationConfig,
    GenerationPipeline,
    GenerationPlan,
    HeuristicTeacherCritic,
    JSONLDatasetExporter,
    QualityFilterConfig,
    RuleBasedTeacherRefiner,
    TeacherEnsembleConfig,
    TeacherModelConfig,
    TeacherStack,
    TemplateTeacherGenerator,
    ValidationConfig,
)
from data.export import ExportConfig
from data.prompts import SUPPORTED_FALLACIES, build_default_prompt_bundle


def build_pipeline(output_root: str, run_id: str) -> GenerationPipeline:
    bundle = build_default_prompt_bundle(bundle_version="v1")
    prompt_registry = DefaultPromptRegistry(bundle)
    prompt_renderer = DefaultPromptRenderer()

    teacher_stack = TeacherStack(
        config=TeacherEnsembleConfig(
            version="teacher-v1",
            generator=TeacherModelConfig(
                model_id="rule-based-golden-generator-v1",
                model_role="generator",
                provider="internal",
                temperature=0.0,
                max_tokens=1024,
                decoding_config={"strategy": "deterministic_templates"},
            ),
            critic=TeacherModelConfig(
                model_id="rule-based-golden-critic-v1",
                model_role="critic",
                provider="internal",
                temperature=0.0,
                max_tokens=512,
                decoding_config={"strategy": "heuristic_scoring"},
            ),
            refiner=TeacherModelConfig(
                model_id="rule-based-golden-refiner-v1",
                model_role="refiner",
                provider="internal",
                temperature=0.0,
                max_tokens=512,
                decoding_config={"strategy": "rule_rewrite"},
            ),
        ),
        generator=TemplateTeacherGenerator(),
        critic=HeuristicTeacherCritic(),
        refiner=RuleBasedTeacherRefiner(),
    )

    candidate_filter = DefaultCandidateFilter(
        QualityFilterConfig(
            hard_gate_codes=(
                "missing_behavior_output",
                "missing_required_behavior_fields",
                "invalid_expected_section_order",
                "no_fallacy_has_label",
                "fallacy_missing_primary_label",
                "adversarial_metadata_missing",
                "derogatory_language",
            ),
            soft_score_thresholds={"overall": 0.65},
            allow_revision_on_soft_fail=True,
        )
    )

    deduplicator = DefaultDeduplicator(
        DedupConfig(
            lexical_similarity_threshold=0.995,
            semantic_similarity_threshold=0.995,
            structural_similarity_threshold=0.999,
        )
    )

    validator = DefaultDatasetValidator(
        ValidationConfig(
            metadata={
                "required_fallacies": SUPPORTED_FALLACIES,
                "min_no_fallacy": 5,
                "min_adversarial": 8,
                "min_ambiguous": 6,
            }
        )
    )

    exporter = JSONLDatasetExporter(
        ExportConfig(
            output_root=output_root,
            include_audit_traces=True,
            metadata={"artifact": "golden_dataset"},
        )
    )

    config = GenerationConfig(
        generation_run_id=run_id,
        dataset_version="0.1.0-golden",
        taxonomy_version="v0",
        prompt_bundle_version=bundle.bundle_version,
        teacher_config_version=teacher_stack.config.version,
        enable_deduplication=False,
        metadata={"dataset_name": "cogni_golden_dataset"},
    )

    return GenerationPipeline(
        config=config,
        prompt_registry=prompt_registry,
        prompt_renderer=prompt_renderer,
        teacher_stack=teacher_stack,
        candidate_filter=candidate_filter,
        deduplicator=deduplicator,
        validator=validator,
        exporter=exporter,
    )


def build_plan() -> GenerationPlan:
    # 11 fallacies * 4 = 44, plus 6 no-fallacy => 50 total.
    fallacy_targets = {fallacy: 4 for fallacy in SUPPORTED_FALLACIES}

    return GenerationPlan(
        total_target_examples=50,
        fallacy_targets=fallacy_targets,
        no_fallacy_target=6,
        adversarial_target=10,
        domain_targets={
            "education": 2,
            "health": 2,
            "policy": 2,
            "finance": 2,
            "technology": 2,
            "environment": 2,
        },
        reflection_style_targets={
            "concise_diagnostic": 2,
            "stepwise_pedagogical": 2,
            "counterexample_driven": 2,
            "misconception_correction": 2,
        },
        metadata={"ambiguous_target": 8},
    )


def main() -> None:
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"golden-{run_stamp}"
    output_root = str(Path("datasets/processed/golden") / run_id)

    pipeline = build_pipeline(output_root=output_root, run_id=run_id)
    plan = build_plan()
    artifacts = pipeline.run(plan)

    print("Golden dataset generation complete")
    print(f"run_id={run_id}")
    print(f"records={len(artifacts.validated_records)}")
    print(f"dataset={artifacts.export_paths.get('dataset_jsonl')}")
    print(f"manifest={artifacts.export_paths.get('manifest_json')}")
    print(f"traces={artifacts.export_paths.get('traces_jsonl')}")


if __name__ == "__main__":
    main()
