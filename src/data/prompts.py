"""Prompt template definitions and rendering for synthetic data generation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from string import Formatter
from typing import Any, Literal, Protocol

from data.schemas import PromptContext

PromptTemplateType = Literal[
    "generation",
    "no_fallacy_generation",
    "adversarial_generation",
    "critique",
    "revision",
]

SUPPORTED_FALLACIES: tuple[str, ...] = (
    "ad_hominem",
    "straw_man",
    "false_dilemma",
    "slippery_slope",
    "hasty_generalization",
    "appeal_to_authority",
    "post_hoc",
    "circular_reasoning",
    "red_herring",
    "equivocation",
    "bandwagon",
)

DEFAULT_EXPECTED_SECTIONS: tuple[str, ...] = (
    "fallacy_hypothesis",
    "reasoning_diagnosis",
    "analogy",
    "repair",
    "confidence_note",
)
DEFAULT_REQUIRED_BEHAVIORS: tuple[str, ...] = (
    "B1",
    "B2",
    "B3",
    "B4",
    "B5",
    "B6",
    "B7",
)
DEFAULT_PROHIBITED_BEHAVIORS: tuple[str, ...] = ("P1", "P2", "P3", "P4", "P5")
DEFAULT_RUBRIC_HOOKS: tuple[str, ...] = (
    "rubric.diagnosis",
    "rubric.analogy_mapping",
    "rubric.repair_quality",
    "rubric.confidence_calibration",
)


@dataclass(frozen=True)
class PromptTemplate:
    """Versioned prompt template definition."""

    template_id: str
    template_type: PromptTemplateType
    template_version: str
    body: str
    required_placeholders: tuple[str, ...] = ()
    output_schema_hints: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptBundle:
    """Collection of templates pinned to one bundle version."""

    bundle_version: str
    templates: tuple[PromptTemplate, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class PromptRegistry(Protocol):
    """Contract for retrieving prompt templates by type and version."""

    def get_template(
        self,
        template_type: PromptTemplateType,
        *,
        template_id: str | None = None,
    ) -> PromptTemplate:
        """Fetch a matching template."""

    def list_templates(
        self,
        template_type: PromptTemplateType | None = None,
    ) -> tuple[PromptTemplate, ...]:
        """List available templates."""


class PromptRenderer(Protocol):
    """Contract for rendering prompt text from templates and context."""

    def render(self, template: PromptTemplate, context: PromptContext) -> str:
        """Render one prompt string."""


def build_default_prompt_bundle(bundle_version: str = "v1") -> PromptBundle:
    """Create the default prompt bundle used by the generation pipeline."""
    templates = (
        PromptTemplate(
            template_id="teacher.generation.default",
            template_type="generation",
            template_version=bundle_version,
            body=(
                "You are a logic tutor generating one training example for {fallacy_label}.\n"
                "Domain: {domain_tag}. Difficulty: {difficulty_level}. "
                "Reflection style: {reflection_style_tag}.\n"
                "Generate: argument_text + structured behavior output fields with "
                "explicit analogy mapping and limits.\n"
                "Return pedagogically clear, non-derogatory content only."
            ),
            required_placeholders=(
                "fallacy_label",
                "domain_tag",
                "difficulty_level",
                "reflection_style_tag",
            ),
            output_schema_hints=DEFAULT_EXPECTED_SECTIONS,
        ),
        PromptTemplate(
            template_id="teacher.generation.no_fallacy",
            template_type="no_fallacy_generation",
            template_version=bundle_version,
            body=(
                "You are a logic tutor generating a NO-FALLACY example.\n"
                "Domain: {domain_tag}. Difficulty: {difficulty_level}.\n"
                "Ensure reasoning is valid or uncertainty is appropriate; "
                "do not force a fallacy label."
            ),
            required_placeholders=("domain_tag", "difficulty_level"),
            output_schema_hints=DEFAULT_EXPECTED_SECTIONS,
        ),
        PromptTemplate(
            template_id="teacher.generation.adversarial",
            template_type="adversarial_generation",
            template_version=bundle_version,
            body=(
                "You are generating an adversarial robustness example.\n"
                "Attack type: {adversarial_type}. Attack target: {attack_target}.\n"
                "Keep educational intent while including adversarial pressure in the input prompt."
            ),
            required_placeholders=("adversarial_type", "attack_target"),
            output_schema_hints=DEFAULT_EXPECTED_SECTIONS,
        ),
        PromptTemplate(
            template_id="teacher.critique.default",
            template_type="critique",
            template_version=bundle_version,
            body=(
                "Critique candidate quality across: structure, diagnosis, "
                "analogy, repair, confidence, safety.\n"
                "Flag behavior-spec violations and propose concrete revision instructions."
            ),
            output_schema_hints=(
                "score_by_dimension",
                "findings",
                "revision_instructions",
            ),
        ),
        PromptTemplate(
            template_id="teacher.revision.default",
            template_type="revision",
            template_version=bundle_version,
            body=(
                "Revise candidate to resolve critique findings while preserving "
                "label/domain intent.\n"
                "Maintain required sections and deterministic section order."
            ),
            output_schema_hints=DEFAULT_EXPECTED_SECTIONS,
        ),
    )
    return PromptBundle(bundle_version=bundle_version, templates=templates)


class DefaultPromptRegistry:
    """Default in-memory prompt registry implementation."""

    def __init__(self, bundle: PromptBundle) -> None:
        self.bundle = bundle

    def get_template(
        self,
        template_type: PromptTemplateType,
        *,
        template_id: str | None = None,
    ) -> PromptTemplate:
        matches = [
            template
            for template in self.bundle.templates
            if template.template_type == template_type
        ]
        if template_id is not None:
            matches = [template for template in matches if template.template_id == template_id]

        if not matches:
            raise KeyError(
                f"No prompt template found for type={template_type!r}, template_id={template_id!r}"
            )

        # Deterministic default to first matching template.
        return matches[0]

    def list_templates(
        self,
        template_type: PromptTemplateType | None = None,
    ) -> tuple[PromptTemplate, ...]:
        if template_type is None:
            return self.bundle.templates
        return tuple(
            template
            for template in self.bundle.templates
            if template.template_type == template_type
        )


class DefaultPromptRenderer:
    """Prompt renderer with strict placeholder validation."""

    def render(self, template: PromptTemplate, context: PromptContext) -> str:
        context_payload = asdict(context)
        flat_values: dict[str, Any] = {
            **context_payload,
            **context_payload.get("metadata", {}),
        }

        missing_required = [
            key for key in template.required_placeholders if flat_values.get(key) in {None, ""}
        ]
        if missing_required:
            raise ValueError(
                f"Missing required placeholders for {template.template_id}: {missing_required}"
            )

        # Validate all placeholders referenced in body are present.
        formatter = Formatter()
        for _, field_name, _, _ in formatter.parse(template.body):
            if not field_name:
                continue
            if field_name not in flat_values:
                raise ValueError(
                    "Template "
                    f"{template.template_id} references unknown placeholder {field_name!r}."
                )

        return template.body.format(**flat_values)
