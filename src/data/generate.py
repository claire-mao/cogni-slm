"""End-to-end synthetic data generation pipeline."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from data.deduplicate import Deduplicator
from data.export import DatasetExporter
from data.filter import CandidateFilter
from data.prompts import (
    DEFAULT_EXPECTED_SECTIONS,
    DEFAULT_PROHIBITED_BEHAVIORS,
    DEFAULT_REQUIRED_BEHAVIORS,
    DEFAULT_RUBRIC_HOOKS,
    PromptRegistry,
    PromptRenderer,
)
from data.schemas import (
    CandidateExample,
    CritiqueResult,
    DatasetManifest,
    DatasetRecord,
    PromptContext,
)
from data.teacher import TeacherStack
from data.validate import DatasetValidator


@dataclass(frozen=True)
class GenerationConfig:
    """Top-level generation pipeline configuration contract."""

    generation_run_id: str
    dataset_version: str
    taxonomy_version: str
    prompt_bundle_version: str
    teacher_config_version: str
    enable_self_critique: bool = True
    enable_revision: bool = True
    enable_filtering: bool = True
    enable_deduplication: bool = True
    enable_validation: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationPlan:
    """Plan describing desired coverage for one generation run."""

    total_target_examples: int
    fallacy_targets: dict[str, int]
    no_fallacy_target: int
    adversarial_target: int
    domain_targets: dict[str, int]
    reflection_style_targets: dict[str, int]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GenerationArtifacts:
    """Result container for pipeline stage outputs."""

    candidates: tuple[CandidateExample, ...]
    validated_records: tuple[DatasetRecord, ...]
    manifest: DatasetManifest | None = None
    export_paths: dict[str, str] = field(default_factory=dict)


def _weighted_cycle(weights: dict[str, int]) -> list[str]:
    values: list[str] = []
    for key, count in weights.items():
        values.extend([key] * max(1, int(count)))
    return values or ["general"]


class GenerationPipeline:
    """Multi-stage generation pipeline implementation."""

    ADVERSARIAL_TYPES: tuple[tuple[str, str], ...] = (
        ("prompt_injection", "format_override"),
        ("lexical_misdirection", "label_confusion"),
        ("contradiction", "reasoning_consistency"),
        ("style_pressure", "section_ordering"),
    )

    def __init__(
        self,
        config: GenerationConfig,
        prompt_registry: PromptRegistry,
        prompt_renderer: PromptRenderer,
        teacher_stack: TeacherStack,
        candidate_filter: CandidateFilter,
        deduplicator: Deduplicator,
        validator: DatasetValidator,
        exporter: DatasetExporter,
    ) -> None:
        self.config = config
        self.prompt_registry = prompt_registry
        self.prompt_renderer = prompt_renderer
        self.teacher_stack = teacher_stack
        self.candidate_filter = candidate_filter
        self.deduplicator = deduplicator
        self.validator = validator
        self.exporter = exporter

    def build_prompt_contexts(self, plan: GenerationPlan) -> Sequence[PromptContext]:
        """Create context workload for generation from coverage targets."""
        contexts: list[PromptContext] = []

        domain_cycle = _weighted_cycle(plan.domain_targets)
        reflection_cycle = _weighted_cycle(plan.reflection_style_targets)
        difficulty_cycle = ["beginner", "intermediate", "advanced"]
        task_cycle = ["teach", "diagnose", "quiz_feedback"]

        index = 0
        for fallacy_label, target_count in plan.fallacy_targets.items():
            for _ in range(target_count):
                contexts.append(
                    PromptContext(
                        fallacy_label=fallacy_label,
                        is_no_fallacy=False,
                        task_mode=task_cycle[index % len(task_cycle)],
                        difficulty_level=difficulty_cycle[index % len(difficulty_cycle)],
                        domain_tag=domain_cycle[index % len(domain_cycle)],
                        analogy_source_domain=domain_cycle[(index + 1) % len(domain_cycle)],
                        analogy_target_domain=domain_cycle[index % len(domain_cycle)],
                        reflection_style_tag=reflection_cycle[index % len(reflection_cycle)],
                        metadata={
                            "index": index,
                            "generation_run_id": self.config.generation_run_id,
                            "split_hint": "validation",
                            "template_type": "generation",
                        },
                    )
                )
                index += 1

        for _ in range(plan.no_fallacy_target):
            contexts.append(
                PromptContext(
                    fallacy_label=None,
                    is_no_fallacy=True,
                    task_mode=task_cycle[index % len(task_cycle)],
                    difficulty_level=difficulty_cycle[index % len(difficulty_cycle)],
                    domain_tag=domain_cycle[index % len(domain_cycle)],
                    analogy_source_domain=domain_cycle[(index + 2) % len(domain_cycle)],
                    analogy_target_domain=domain_cycle[index % len(domain_cycle)],
                    reflection_style_tag=reflection_cycle[index % len(reflection_cycle)],
                    metadata={
                        "index": index,
                        "generation_run_id": self.config.generation_run_id,
                        "split_hint": "validation",
                        "template_type": "no_fallacy_generation",
                    },
                )
            )
            index += 1

        contexts = contexts[: plan.total_target_examples]
        while len(contexts) < plan.total_target_examples:
            contexts.append(
                PromptContext(
                    fallacy_label=None,
                    is_no_fallacy=True,
                    task_mode="teach",
                    difficulty_level="beginner",
                    domain_tag=domain_cycle[len(contexts) % len(domain_cycle)],
                    analogy_source_domain=domain_cycle[(len(contexts) + 1) % len(domain_cycle)],
                    analogy_target_domain=domain_cycle[len(contexts) % len(domain_cycle)],
                    reflection_style_tag=reflection_cycle[len(contexts) % len(reflection_cycle)],
                    metadata={
                        "index": len(contexts),
                        "generation_run_id": self.config.generation_run_id,
                        "split_hint": "validation",
                        "template_type": "no_fallacy_generation",
                    },
                )
            )

        adversarial_target = min(plan.adversarial_target, len(contexts))
        for idx in range(adversarial_target):
            adversarial_type, attack_target = self.ADVERSARIAL_TYPES[
                idx % len(self.ADVERSARIAL_TYPES)
            ]
            context = contexts[idx]
            contexts[idx] = replace(
                context,
                is_adversarial=True,
                adversarial_type=adversarial_type,
                attack_target=attack_target,
                metadata={
                    **context.metadata,
                    "template_type": "adversarial_generation",
                    "adversarial_instruction": (
                        f"[{adversarial_type}] Attempt to bypass structure via {attack_target}."
                    ),
                },
            )

        ambiguous_target = int(plan.metadata.get("ambiguous_target", 0))
        marked = 0
        for idx, context in enumerate(contexts):
            if marked >= ambiguous_target:
                break
            if context.is_no_fallacy:
                continue
            contexts[idx] = replace(
                context,
                metadata={
                    **context.metadata,
                    "ambiguity_expected": True,
                },
            )
            marked += 1

        for idx, context in enumerate(contexts):
            contexts[idx] = replace(
                context,
                metadata={
                    **context.metadata,
                    "example_id": f"golden-{idx + 1:04d}",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                },
            )

        return tuple(contexts)

    def _render_prompt(self, context: PromptContext) -> tuple[str, str]:
        template_type = str(context.metadata.get("template_type", "generation"))
        template = self.prompt_registry.get_template(template_type)  # type: ignore[arg-type]
        return template.template_id, self.prompt_renderer.render(template, context)

    def _run_critique_and_revision(
        self,
        candidate: CandidateExample,
        context: PromptContext,
    ) -> tuple[CandidateExample, tuple[CritiqueResult, ...]]:
        critiques: list[CritiqueResult] = []
        if not self.config.enable_self_critique or self.teacher_stack.critic is None:
            return candidate, ()

        critique_template = self.prompt_registry.get_template("critique")
        critique_prompt = self.prompt_renderer.render(critique_template, context)
        critique = self.teacher_stack.run_self_critique(candidate, critique_prompt)
        critiques.append(critique)

        decision = self.candidate_filter.evaluate(candidate, critiques)
        if (
            decision.decision == "needs_revision"
            and self.config.enable_revision
            and self.teacher_stack.refiner is not None
        ):
            revision_template = self.prompt_registry.get_template("revision")
            revision_prompt = self.prompt_renderer.render(revision_template, context)
            candidate = self.teacher_stack.run_revision(candidate, critique, revision_prompt)
            followup_critique = self.teacher_stack.run_self_critique(candidate, critique_prompt)
            critiques.append(followup_critique)

        return candidate, tuple(critiques)

    def generate_candidates(self, contexts: Sequence[PromptContext]) -> Sequence[CandidateExample]:
        """Generate initial candidate examples from planned contexts."""
        generated: list[CandidateExample] = []

        for context in contexts:
            template_id, prompt_text = self._render_prompt(context)
            candidate = self.teacher_stack.run_generation(prompt_text, context)
            candidate, critiques = self._run_critique_and_revision(candidate, context)

            filter_decision = self.candidate_filter.evaluate(candidate, critiques)
            critique_overall = (
                mean(critique.score_by_dimension.get("overall", 0.0) for critique in critiques)
                if critiques
                else 1.0
            )

            candidate = replace(
                candidate,
                metadata={
                    **candidate.metadata,
                    "template_id": template_id,
                    "template_version": self.config.prompt_bundle_version,
                    "template_type": context.metadata.get("template_type", "generation"),
                    "prompt_seed": int(context.metadata.get("index", 0)),
                    "critiques": [asdict(critique) for critique in critiques],
                    "critique_overall": critique_overall,
                    "filter_decision": asdict(filter_decision),
                },
            )

            if self.config.enable_filtering and filter_decision.decision == "reject":
                continue

            generated.append(candidate)

        return tuple(generated)

    def _to_record(self, candidate: CandidateExample) -> DatasetRecord:
        behavior_output = asdict(candidate.behavior_output) if candidate.behavior_output else {}
        filter_decision_payload = candidate.metadata.get("filter_decision", {})
        filter_reason_codes = tuple(filter_decision_payload.get("reason_codes", ()))

        critique_scores = {
            "overall": float(candidate.metadata.get("critique_overall", 1.0)),
        }

        return DatasetRecord(
            example_id=candidate.example_id,
            split_hint=candidate.metadata.get("split_hint", "validation"),
            dataset_version=self.config.dataset_version,
            taxonomy_version=self.config.taxonomy_version,
            source_id=candidate.source_id,
            argument_text=candidate.argument_text,
            task_mode=candidate.task_mode,
            difficulty_level=candidate.difficulty_level,
            primary_fallacy_label=candidate.primary_fallacy_label,
            acceptable_alternative_labels=candidate.acceptable_alternative_labels,
            is_no_fallacy=candidate.is_no_fallacy,
            expected_sections=DEFAULT_EXPECTED_SECTIONS,
            required_behaviors=DEFAULT_REQUIRED_BEHAVIORS,
            prohibited_behaviors=DEFAULT_PROHIBITED_BEHAVIORS,
            rubric_hooks=DEFAULT_RUBRIC_HOOKS,
            domain_tag=candidate.domain_tag,
            analogy_source_domain=candidate.analogy_source_domain,
            analogy_target_domain=candidate.analogy_target_domain,
            reflection_style_tag=candidate.reflection_style_tag,
            is_adversarial=candidate.is_adversarial,
            adversarial_type=candidate.adversarial_type,
            attack_target=candidate.attack_target,
            generator_model_id=self.teacher_stack.config.generator.model_id,
            critic_model_id=(
                self.teacher_stack.config.critic.model_id
                if self.teacher_stack.config.critic
                else None
            ),
            template_id=str(candidate.metadata.get("template_id", "unknown")),
            template_version=str(candidate.metadata.get("template_version", "unknown")),
            prompt_seed=int(candidate.metadata.get("prompt_seed", 0)),
            decoding_config=dict(self.teacher_stack.config.generator.decoding_config),
            critique_scores=critique_scores,
            filter_decisions=filter_reason_codes,
            dedup_cluster_id=str(candidate.metadata.get("dedup_cluster_id", "")) or None,
            validation_status="passed",
            created_at=candidate.created_at,
            updated_at=datetime.now(timezone.utc).isoformat(),
            metadata={
                **candidate.metadata,
                "behavior_output": behavior_output,
            },
        )

    def _build_manifest(self, records: Sequence[DatasetRecord]) -> DatasetManifest:
        fallacy_counts: Counter[str] = Counter(
            record.primary_fallacy_label for record in records if record.primary_fallacy_label
        )
        domain_counts: Counter[str] = Counter(
            record.domain_tag for record in records if record.domain_tag
        )
        reflection_counts: Counter[str] = Counter(
            record.reflection_style_tag for record in records if record.reflection_style_tag
        )

        return DatasetManifest(
            dataset_name=str(self.config.metadata.get("dataset_name", "cogni_golden_dataset")),
            dataset_version=self.config.dataset_version,
            snapshot_hash="pending",
            taxonomy_version=self.config.taxonomy_version,
            prompt_bundle_version=self.config.prompt_bundle_version,
            teacher_config_version=self.config.teacher_config_version,
            generation_run_id=self.config.generation_run_id,
            total_examples=len(records),
            no_fallacy_examples=sum(1 for record in records if record.is_no_fallacy),
            adversarial_examples=sum(1 for record in records if record.is_adversarial),
            fallacy_counts=dict(fallacy_counts),
            domain_counts=dict(domain_counts),
            reflection_style_counts=dict(reflection_counts),
            created_at=datetime.now(timezone.utc).isoformat(),
            metadata=dict(self.config.metadata),
        )

    def run(self, plan: GenerationPlan) -> GenerationArtifacts:
        """Execute the full generation pipeline stages."""
        contexts = self.build_prompt_contexts(plan)
        candidates = list(self.generate_candidates(contexts))

        if self.config.enable_deduplication:
            clusters = self.deduplicator.cluster(candidates)
            decisions = self.deduplicator.decide(clusters)
            decision_by_id = {decision.example_id: decision for decision in decisions}
        else:
            decision_by_id = {}

        kept_candidates: list[CandidateExample] = []
        for candidate in candidates:
            decision = decision_by_id.get(candidate.example_id)
            if decision is not None:
                candidate = replace(
                    candidate,
                    metadata={
                        **candidate.metadata,
                        "dedup_cluster_id": decision.dedup_cluster_id,
                        "dedup_similarity_score": decision.similarity_score,
                        "dedup_reason": decision.reason,
                    },
                )
                if not decision.kept:
                    continue
            kept_candidates.append(candidate)

        records = [self._to_record(candidate) for candidate in kept_candidates]

        if self.config.enable_validation:
            validation_report = self.validator.validate(records)
            if validation_report.failed_examples > 0 or any(
                issue.severity == "error" for issue in validation_report.issues
            ):
                messages = ", ".join(
                    f"{issue.code}:{issue.example_id or 'global'}"
                    for issue in validation_report.issues
                    if issue.severity == "error"
                )
                raise ValueError(f"Validation failed: {messages}")

        manifest = self._build_manifest(records)
        export_paths = dict(self.exporter.export_jsonl(records, manifest))

        return GenerationArtifacts(
            candidates=tuple(kept_candidates),
            validated_records=tuple(records),
            manifest=manifest,
            export_paths=export_paths,
        )
