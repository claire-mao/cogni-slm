"""Validation checks for generated dataset records."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from data.prompts import (
    DEFAULT_EXPECTED_SECTIONS,
    DEFAULT_PROHIBITED_BEHAVIORS,
    DEFAULT_REQUIRED_BEHAVIORS,
)
from data.schemas import DatasetRecord, ValidationIssue, ValidationReport


@dataclass(frozen=True)
class ValidationConfig:
    """Configuration for schema and policy validation checks."""

    require_behavior_sections: bool = True
    require_metadata_completeness: bool = True
    enforce_no_fallacy_policy: bool = True
    enforce_adversarial_metadata: bool = True
    enforce_split_constraints: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class DatasetValidator(Protocol):
    """Contract for validating dataset records prior to export."""

    def validate(self, records: Sequence[DatasetRecord]) -> ValidationReport:
        """Run all configured validation checks."""


class DefaultDatasetValidator:
    """Rule-based validator for dataset records."""

    ALLOWED_SPLITS = {"train", "validation", "test", "heldout_benchmark", None}

    def __init__(self, config: ValidationConfig) -> None:
        self.config = config

    def _issue(
        self,
        *,
        example_id: str | None,
        severity: str,
        code: str,
        message: str,
        field: str | None = None,
    ) -> ValidationIssue:
        return ValidationIssue(
            example_id=example_id,
            severity=severity,
            code=code,
            message=message,
            field=field,
        )

    def validate(self, records: Sequence[DatasetRecord]) -> ValidationReport:
        issues: list[ValidationIssue] = []
        failed_ids: set[str] = set()

        required_fallacies = set(self.config.metadata.get("required_fallacies", []))
        min_no_fallacy = int(self.config.metadata.get("min_no_fallacy", 0))
        min_adversarial = int(self.config.metadata.get("min_adversarial", 0))
        min_ambiguous = int(self.config.metadata.get("min_ambiguous", 0))

        no_fallacy_count = 0
        adversarial_count = 0
        ambiguous_count = 0
        fallacy_counts: Counter[str] = Counter()

        for record in records:
            if record.validation_status != "passed":
                issues.append(
                    self._issue(
                        example_id=record.example_id,
                        severity="error",
                        code="record_not_marked_passed",
                        message="Record validation_status must be 'passed' before export.",
                        field="validation_status",
                    )
                )
                failed_ids.add(record.example_id)

            if self.config.require_behavior_sections:
                if tuple(record.expected_sections) != DEFAULT_EXPECTED_SECTIONS:
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="invalid_expected_sections",
                            message="expected_sections must match behavior spec section order.",
                            field="expected_sections",
                        )
                    )
                    failed_ids.add(record.example_id)

                if tuple(record.required_behaviors) != DEFAULT_REQUIRED_BEHAVIORS:
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="invalid_required_behaviors",
                            message="required_behaviors must match behavior spec B1-B7.",
                            field="required_behaviors",
                        )
                    )
                    failed_ids.add(record.example_id)

                if tuple(record.prohibited_behaviors) != DEFAULT_PROHIBITED_BEHAVIORS:
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="invalid_prohibited_behaviors",
                            message="prohibited_behaviors must match behavior spec P1-P5.",
                            field="prohibited_behaviors",
                        )
                    )
                    failed_ids.add(record.example_id)

                behavior_output = record.metadata.get("behavior_output")
                if not isinstance(behavior_output, dict):
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="missing_behavior_output_metadata",
                            message="metadata.behavior_output is required for reviewable targets.",
                            field="metadata.behavior_output",
                        )
                    )
                    failed_ids.add(record.example_id)
                else:
                    required_output_fields = (
                        "fallacy_hypothesis",
                        "reasoning_diagnosis",
                        "analogy_source_scenario",
                        "analogy_mapping",
                        "analogy_limits",
                        "repair",
                        "confidence_note",
                    )
                    for field_name in required_output_fields:
                        value = str(behavior_output.get(field_name, "")).strip()
                        if not value:
                            issues.append(
                                self._issue(
                                    example_id=record.example_id,
                                    severity="error",
                                    code="missing_behavior_output_field",
                                    message=f"behavior_output.{field_name} is missing or empty.",
                                    field=f"metadata.behavior_output.{field_name}",
                                )
                            )
                            failed_ids.add(record.example_id)

            if self.config.require_metadata_completeness:
                required_metadata_keys = (
                    "template_type",
                    "manual_review_required",
                )
                for metadata_key in required_metadata_keys:
                    if metadata_key not in record.metadata:
                        issues.append(
                            self._issue(
                                example_id=record.example_id,
                                severity="error",
                                code="missing_metadata_key",
                                message=f"metadata.{metadata_key} is required.",
                                field=f"metadata.{metadata_key}",
                            )
                        )
                        failed_ids.add(record.example_id)

            if self.config.enforce_no_fallacy_policy:
                if record.is_no_fallacy and record.primary_fallacy_label is not None:
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="no_fallacy_with_label",
                            message="is_no_fallacy records must have primary_fallacy_label=None.",
                            field="primary_fallacy_label",
                        )
                    )
                    failed_ids.add(record.example_id)

                if (not record.is_no_fallacy) and record.primary_fallacy_label is None:
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="fallacy_missing_label",
                            message="Fallacy records must provide primary_fallacy_label.",
                            field="primary_fallacy_label",
                        )
                    )
                    failed_ids.add(record.example_id)

            if self.config.enforce_adversarial_metadata:
                if record.is_adversarial and (
                    not record.adversarial_type or not record.attack_target
                ):
                    issues.append(
                        self._issue(
                            example_id=record.example_id,
                            severity="error",
                            code="adversarial_metadata_missing",
                            message=(
                                "Adversarial records require adversarial_type " "and attack_target."
                            ),
                            field="adversarial_type",
                        )
                    )
                    failed_ids.add(record.example_id)

            if (
                self.config.enforce_split_constraints
                and record.split_hint not in self.ALLOWED_SPLITS
            ):
                issues.append(
                    self._issue(
                        example_id=record.example_id,
                        severity="error",
                        code="invalid_split_hint",
                        message=f"split_hint must be one of {sorted(self.ALLOWED_SPLITS)}.",
                        field="split_hint",
                    )
                )
                failed_ids.add(record.example_id)

            if record.is_no_fallacy:
                no_fallacy_count += 1
            else:
                if record.primary_fallacy_label is not None:
                    fallacy_counts[record.primary_fallacy_label] += 1
            if record.is_adversarial:
                adversarial_count += 1
            if bool(record.metadata.get("ambiguity_expected", False)):
                ambiguous_count += 1

        covered_fallacies = set(fallacy_counts.keys())
        missing_fallacies = sorted(required_fallacies - covered_fallacies)
        if missing_fallacies:
            issues.append(
                self._issue(
                    example_id=None,
                    severity="error",
                    code="missing_required_fallacy_coverage",
                    message=f"Missing fallacy coverage for: {missing_fallacies}",
                    field="primary_fallacy_label",
                )
            )

        if no_fallacy_count < min_no_fallacy:
            issues.append(
                self._issue(
                    example_id=None,
                    severity="error",
                    code="insufficient_no_fallacy_examples",
                    message=(
                        f"Expected at least {min_no_fallacy} no-fallacy examples, "
                        f"got {no_fallacy_count}."
                    ),
                    field="is_no_fallacy",
                )
            )

        if adversarial_count < min_adversarial:
            issues.append(
                self._issue(
                    example_id=None,
                    severity="error",
                    code="insufficient_adversarial_examples",
                    message=(
                        f"Expected at least {min_adversarial} adversarial "
                        f"examples, got {adversarial_count}."
                    ),
                    field="is_adversarial",
                )
            )

        if ambiguous_count < min_ambiguous:
            issues.append(
                self._issue(
                    example_id=None,
                    severity="error",
                    code="insufficient_ambiguous_examples",
                    message=(
                        f"Expected at least {min_ambiguous} ambiguous examples, "
                        f"got {ambiguous_count}."
                    ),
                    field="metadata.ambiguity_expected",
                )
            )

        total_examples = len(records)
        failed_examples = len(failed_ids)
        passed_examples = max(0, total_examples - failed_examples)

        return ValidationReport(
            total_examples=total_examples,
            passed_examples=passed_examples,
            failed_examples=failed_examples,
            issues=tuple(issues),
        )
