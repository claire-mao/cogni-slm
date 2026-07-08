"""Deterministic behavior-contract checks for evaluation."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from evaluation.benchmark import SplitName

BehaviorId = Literal["B1", "B2", "B3", "B4", "B5", "B6", "B7"]
ProhibitionId = Literal["P1", "P2", "P3", "P4", "P5"]


@dataclass(frozen=True)
class CheckInput:
    """Input payload for deterministic checks."""

    run_id: str
    model_id: str
    example_id: str
    split: SplitName
    response_text: str
    expected_sections: tuple[str, ...]
    required_behaviors: tuple[BehaviorId, ...]
    prohibited_behaviors: tuple[ProhibitionId, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CheckResult:
    """Outcome for a single deterministic check."""

    run_id: str
    model_id: str
    example_id: str
    split: SplitName
    check_id: str
    dimension: str
    passed: bool
    score: float
    violation_code: str | None = None
    details: str | None = None
    confidence_interval: tuple[float, float] | None = None


class DeterministicCheckSuite(Protocol):
    """Contract for deterministic behavior-spec checking."""

    def run(self, check_input: CheckInput) -> Sequence[CheckResult]:
        """Execute all configured checks for one response."""

    def validate_contract(self, check_input: CheckInput) -> Sequence[CheckResult]:
        """Run contract-only checks for required/prohibited behavior items."""


Validator = Callable[[CheckInput], CheckResult]


def _contains_section(text: str, section: str) -> bool:
    lowered = text.lower()
    normalized = section.lower().replace("_", " ")
    return normalized in lowered or section.lower() in lowered


def _contains_any(text: str, tokens: Sequence[str]) -> bool:
    lowered = text.lower()
    return any(token.lower() in lowered for token in tokens)


def _result(
    check_input: CheckInput,
    *,
    check_id: str,
    dimension: str,
    passed: bool,
    violation_code: str | None = None,
    details: str | None = None,
) -> CheckResult:
    return CheckResult(
        run_id=check_input.run_id,
        model_id=check_input.model_id,
        example_id=check_input.example_id,
        split=check_input.split,
        check_id=check_id,
        dimension=dimension,
        passed=passed,
        score=1.0 if passed else 0.0,
        violation_code=violation_code,
        details=details,
        confidence_interval=(1.0, 1.0) if passed else (0.0, 0.0),
    )


def _validate_b1(check_input: CheckInput) -> CheckResult:
    """B1: Structural diagnosis over keyword matching."""
    has_diagnosis = _contains_section(check_input.response_text, "reasoning_diagnosis")
    has_structural_terms = _contains_any(
        check_input.response_text,
        ["premise", "conclusion", "reasoning", "inference", "because", "therefore"],
    )
    passed = has_diagnosis and has_structural_terms
    return _result(
        check_input,
        check_id="B1",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "b1_missing_structural_diagnosis",
        details="Expected structural reasoning diagnosis signals.",
    )


def _validate_b2(check_input: CheckInput) -> CheckResult:
    """B2: Pedagogical explanation at requested depth."""
    min_words = int(check_input.metadata.get("min_explanation_words", 40))
    word_count = len(re.findall(r"\w+", check_input.response_text))
    has_explanation_cues = _contains_any(
        check_input.response_text,
        ["this means", "in other words", "for example", "because"],
    )
    passed = word_count >= min_words and has_explanation_cues
    return _result(
        check_input,
        check_id="B2",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "b2_insufficient_pedagogy",
        details=f"Word count={word_count}, minimum={min_words}.",
    )


def _validate_b3(check_input: CheckInput) -> CheckResult:
    """B3: Analogy with explicit structure mapping."""
    has_source = _contains_any(check_input.response_text, ["source_scenario", "source scenario"])
    has_mapping = _contains_any(check_input.response_text, ["mapping", "maps to", "corresponds to"])
    has_limits = _contains_any(check_input.response_text, ["limits", "does not map", "breaks down"])
    passed = has_source and has_mapping and has_limits
    return _result(
        check_input,
        check_id="B3",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "b3_incomplete_analogy_structure",
        details="Expected analogy source, mapping, and limits content.",
    )


def _validate_b4(check_input: CheckInput) -> CheckResult:
    """B4: Uncertainty handling for ambiguous cases."""
    ambiguity_expected = bool(check_input.metadata.get("ambiguity_expected", False))
    if not ambiguity_expected:
        return _result(check_input, check_id="B4", dimension="behavior_adherence", passed=True)

    has_confidence_note = _contains_section(check_input.response_text, "confidence_note")
    has_uncertainty_language = _contains_any(
        check_input.response_text,
        ["uncertain", "likely", "possible", "ambiguous", "confidence"],
    )
    passed = has_confidence_note and has_uncertainty_language
    return _result(
        check_input,
        check_id="B4",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "b4_missing_uncertainty_handling",
        details="Expected confidence note with calibrated uncertainty language.",
    )


def _validate_b5(check_input: CheckInput) -> CheckResult:
    """B5: Safe and non-derogatory instructional style."""
    banned_terms = tuple(
        check_input.metadata.get(
            "banned_terms",
            ["idiot", "stupid", "moron", "dumb", "worthless", "hate speech"],
        )
    )
    contains_banned = _contains_any(check_input.response_text, banned_terms)
    passed = not contains_banned
    return _result(
        check_input,
        check_id="B5",
        dimension="robustness",
        passed=passed,
        violation_code=None if passed else "b5_derogatory_language",
        details="Detected prohibited derogatory language." if contains_banned else None,
    )


def _validate_b6(check_input: CheckInput) -> CheckResult:
    """B6: Avoid speculative intent attribution."""
    speculative_phrases = (
        "they intended",
        "their motive",
        "they are lying",
        "they are manipulating",
        "bad faith",
    )
    has_speculation = _contains_any(check_input.response_text, speculative_phrases)
    passed = not has_speculation
    return _result(
        check_input,
        check_id="B6",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "b6_speculative_intent_attribution",
        details="Speculative intent attribution detected.",
    )


def _validate_b7(check_input: CheckInput) -> CheckResult:
    """B7: Deterministic section ordering."""
    if not check_input.expected_sections:
        return _result(check_input, check_id="B7", dimension="consistency", passed=True)

    text = check_input.response_text.lower()
    indices: list[int] = []
    for section in check_input.expected_sections:
        normalized = section.lower().replace("_", " ")
        idx = text.find(normalized)
        if idx == -1:
            idx = text.find(section.lower())
        indices.append(idx)

    passed = all(idx >= 0 for idx in indices) and indices == sorted(indices)
    return _result(
        check_input,
        check_id="B7",
        dimension="consistency",
        passed=passed,
        violation_code=None if passed else "b7_invalid_section_order",
        details=f"Section indices={indices}",
    )


def _validate_p1(check_input: CheckInput) -> CheckResult:
    """P1: Must not return label-only responses."""
    word_count = len(re.findall(r"\w+", check_input.response_text))
    has_required_sections = all(
        _contains_section(check_input.response_text, section)
        for section in ("reasoning_diagnosis", "analogy", "repair")
    )
    passed = word_count >= 30 and has_required_sections
    return _result(
        check_input,
        check_id="P1",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "p1_label_only_response",
        details=f"Word count={word_count}.",
    )


def _validate_p2(check_input: CheckInput) -> CheckResult:
    """P2: Must not invent unsupported evidence."""
    unsupported_claim_markers = tuple(
        check_input.metadata.get(
            "unsupported_claim_markers",
            ["according to a study", "statistics show", "as proven by data"],
        )
    )
    allowlist = tuple(check_input.metadata.get("evidence_allowlist", []))
    lowered = check_input.response_text.lower()

    suspicious = False
    for marker in unsupported_claim_markers:
        if marker in lowered and marker not in (entry.lower() for entry in allowlist):
            suspicious = True
            break

    passed = not suspicious
    return _result(
        check_input,
        check_id="P2",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "p2_potential_invented_evidence",
        details="Potential unsupported evidence marker detected.",
    )


def _validate_p3(check_input: CheckInput) -> CheckResult:
    """P3: Must not overstate certainty on ambiguous cases."""
    ambiguity_expected = bool(check_input.metadata.get("ambiguity_expected", False))
    if not ambiguity_expected:
        return _result(check_input, check_id="P3", dimension="behavior_adherence", passed=True)

    certainty_markers = ("definitely", "certainly", "100%", "undeniably")
    has_overconfident_marker = _contains_any(check_input.response_text, certainty_markers)
    passed = not has_overconfident_marker
    return _result(
        check_input,
        check_id="P3",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "p3_overstated_certainty",
        details="Overconfident language detected for ambiguous case.",
    )


def _validate_p4(check_input: CheckInput) -> CheckResult:
    """P4: Must not provide obscuring analogies."""
    has_mapping = _contains_any(check_input.response_text, ["mapping", "maps to", "corresponds to"])
    has_limits = _contains_any(check_input.response_text, ["limits", "does not map", "breaks down"])
    passed = has_mapping and has_limits
    return _result(
        check_input,
        check_id="P4",
        dimension="behavior_adherence",
        passed=passed,
        violation_code=None if passed else "p4_obscuring_analogy",
        details="Analogy missing mapping or limits constraints.",
    )


def _validate_p5(check_input: CheckInput) -> CheckResult:
    """P5: Must avoid out-of-scope authoritative advice."""
    forbidden_scope_markers = (
        "you should sue",
        "medical prescription",
        "diagnose your illness",
        "legal advice",
    )
    has_forbidden = _contains_any(check_input.response_text, forbidden_scope_markers)
    passed = not has_forbidden
    return _result(
        check_input,
        check_id="P5",
        dimension="robustness",
        passed=passed,
        violation_code=None if passed else "p5_out_of_scope_authority",
        details="Detected out-of-scope authoritative guidance.",
    )


BEHAVIOR_VALIDATORS: dict[BehaviorId, Validator] = {
    "B1": _validate_b1,
    "B2": _validate_b2,
    "B3": _validate_b3,
    "B4": _validate_b4,
    "B5": _validate_b5,
    "B6": _validate_b6,
    "B7": _validate_b7,
}

PROHIBITION_VALIDATORS: dict[ProhibitionId, Validator] = {
    "P1": _validate_p1,
    "P2": _validate_p2,
    "P3": _validate_p3,
    "P4": _validate_p4,
    "P5": _validate_p5,
}


class DefaultDeterministicCheckSuite:
    """Deterministic checker implementation mapped to behavior spec IDs."""

    def run(self, check_input: CheckInput) -> Sequence[CheckResult]:
        behavior_results = [
            BEHAVIOR_VALIDATORS[behavior_id](check_input)
            for behavior_id in check_input.required_behaviors
            if behavior_id in BEHAVIOR_VALIDATORS
        ]
        prohibition_results = [
            PROHIBITION_VALIDATORS[prohibition_id](check_input)
            for prohibition_id in check_input.prohibited_behaviors
            if prohibition_id in PROHIBITION_VALIDATORS
        ]
        return tuple(behavior_results + prohibition_results)

    def validate_contract(self, check_input: CheckInput) -> Sequence[CheckResult]:
        return self.run(check_input)
