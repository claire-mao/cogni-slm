"""Automatic quality filtering for generated candidates."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from statistics import mean
from typing import Any, Protocol

from data.prompts import DEFAULT_EXPECTED_SECTIONS
from data.schemas import CandidateExample, CritiqueResult, FilterDecision


@dataclass(frozen=True)
class QualityFilterConfig:
    """Configuration contract for hard and soft quality gates."""

    hard_gate_codes: tuple[str, ...]
    soft_score_thresholds: dict[str, float]
    allow_revision_on_soft_fail: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class CandidateFilter(Protocol):
    """Contract for automated candidate filtering."""

    def evaluate(
        self,
        candidate: CandidateExample,
        critiques: Sequence[CritiqueResult] = (),
    ) -> FilterDecision:
        """Return pass/reject/revision decision for one candidate."""


class DefaultCandidateFilter:
    """Candidate filter with hard/soft gate decisions."""

    def __init__(self, config: QualityFilterConfig) -> None:
        self.config = config

    def _hard_gate_failures(self, candidate: CandidateExample) -> list[str]:
        failures: list[str] = []

        behavior = candidate.behavior_output
        if behavior is None:
            failures.append("missing_behavior_output")
            return failures

        required_behavior_fields = [
            behavior.fallacy_hypothesis,
            behavior.reasoning_diagnosis,
            behavior.analogy_source_scenario,
            behavior.analogy_mapping,
            behavior.analogy_limits,
            behavior.repair,
            behavior.confidence_note,
        ]
        if any(not field.strip() for field in required_behavior_fields):
            failures.append("missing_required_behavior_fields")

        if candidate.expected_sections != DEFAULT_EXPECTED_SECTIONS:
            failures.append("invalid_expected_section_order")

        if candidate.is_no_fallacy and candidate.primary_fallacy_label is not None:
            failures.append("no_fallacy_has_label")
        if (not candidate.is_no_fallacy) and candidate.primary_fallacy_label is None:
            failures.append("fallacy_missing_primary_label")

        if candidate.is_adversarial and (
            not candidate.adversarial_type or not candidate.attack_target
        ):
            failures.append("adversarial_metadata_missing")

        banned_tokens = tuple(
            self.config.metadata.get("banned_tokens", ("idiot", "moron", "stupid"))
        )
        lowered_argument = candidate.argument_text.lower()
        if any(token in lowered_argument for token in banned_tokens):
            failures.append("derogatory_language")

        if (
            candidate.metadata.get("ambiguity_expected")
            and not candidate.acceptable_alternative_labels
        ):
            failures.append("ambiguous_without_alternatives")

        allowed = set(self.config.hard_gate_codes)
        return [failure for failure in failures if failure in allowed]

    def _soft_scores(
        self,
        candidate: CandidateExample,
        critiques: Sequence[CritiqueResult],
    ) -> dict[str, float]:
        behavior = candidate.behavior_output
        if behavior is None:
            return {
                "critique_overall": 0.0,
                "structure": 0.0,
                "content_length": 0.0,
                "overall": 0.0,
            }

        critique_overall = (
            mean(critique.score_by_dimension.get("overall", 0.0) for critique in critiques)
            if critiques
            else 0.8
        )
        structure_score = 1.0 if candidate.expected_sections == DEFAULT_EXPECTED_SECTIONS else 0.5
        content_length_score = min(1.0, len(candidate.argument_text.split()) / 20.0)
        overall = 0.5 * critique_overall + 0.25 * structure_score + 0.25 * content_length_score

        return {
            "critique_overall": critique_overall,
            "structure": structure_score,
            "content_length": content_length_score,
            "overall": overall,
        }

    def evaluate(
        self,
        candidate: CandidateExample,
        critiques: Sequence[CritiqueResult] = (),
    ) -> FilterDecision:
        hard_failures = self._hard_gate_failures(candidate)
        scores = self._soft_scores(candidate, critiques)

        if hard_failures:
            return FilterDecision(
                example_id=candidate.example_id,
                decision="reject",
                reason_codes=tuple(hard_failures),
                scores=scores,
                metadata={"gate": "hard"},
            )

        threshold = float(self.config.soft_score_thresholds.get("overall", 0.75))
        if scores["overall"] < threshold:
            decision = "needs_revision" if self.config.allow_revision_on_soft_fail else "reject"
            reason = "soft_score_below_threshold"
            return FilterDecision(
                example_id=candidate.example_id,
                decision=decision,
                reason_codes=(reason,),
                scores=scores,
                metadata={"gate": "soft", "threshold": threshold},
            )

        return FilterDecision(
            example_id=candidate.example_id,
            decision="pass",
            reason_codes=("quality_pass",),
            scores=scores,
            metadata={"gate": "soft", "threshold": threshold},
        )
