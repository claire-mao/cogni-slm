"""Provider-agnostic LLM-as-judge interfaces for baseline evaluation."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Protocol

from .benchmark import BenchmarkRecord


@dataclass(frozen=True)
class JudgeInputRecord:
    """Input payload for one judged model response."""

    run_id: str
    model_id: str
    example_id: str
    prompt: str
    response: str
    benchmark_record: BenchmarkRecord
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JudgeDimensionScore:
    """Score details for one evaluation dimension."""

    score: float
    rationale: str


@dataclass(frozen=True)
class JudgeOutputRecord:
    """Structured judge output contract."""

    run_id: str
    model_id: str
    example_id: str
    instruction_following: JudgeDimensionScore
    correctness: JudgeDimensionScore
    reasoning_quality: JudgeDimensionScore
    completeness: JudgeDimensionScore
    hallucination: JudgeDimensionScore
    overall_score: float
    passed: bool
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "model_id": self.model_id,
            "example_id": self.example_id,
            "instruction_following": {
                "score": self.instruction_following.score,
                "rationale": self.instruction_following.rationale,
            },
            "correctness": {
                "score": self.correctness.score,
                "rationale": self.correctness.rationale,
            },
            "reasoning_quality": {
                "score": self.reasoning_quality.score,
                "rationale": self.reasoning_quality.rationale,
            },
            "completeness": {
                "score": self.completeness.score,
                "rationale": self.completeness.rationale,
            },
            "hallucination": {
                "score": self.hallucination.score,
                "rationale": self.hallucination.rationale,
            },
            "overall_score": self.overall_score,
            "passed": self.passed,
            "metadata": self.metadata,
        }


class JudgeBackend(Protocol):
    """Backend protocol for provider-specific judge execution."""

    def complete_json(self, prompt: str) -> Mapping[str, Any] | str:
        """Return structured or JSON-string output for a judge prompt."""


class ResponseJudge(Protocol):
    """Judge contract used by baseline evaluation."""

    def evaluate(self, record: JudgeInputRecord) -> JudgeOutputRecord:
        """Evaluate one model response and return structured scores."""


def _extract_predicted_label(text: str) -> str | None:
    explicit = re.search(r"fallacy[_\s]hypothesis\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
    if explicit:
        return explicit.group(1).strip().lower().replace(" ", "_")

    fallback = re.search(r"fallacy\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
    if fallback:
        return fallback.group(1).strip().lower().replace(" ", "_")

    return None


def _contains_section(text: str, section: str) -> bool:
    lowered = text.lower()
    normalized = section.lower().replace("_", " ")
    return normalized in lowered or section.lower() in lowered


class DefaultBehaviorJudge:
    """Default judge implementation with optional pluggable backend.

    If no backend is provided, this class uses deterministic heuristics so the
    baseline pipeline remains runnable in offline environments.
    """

    def __init__(self, backend: JudgeBackend | None = None, pass_threshold: float = 0.70) -> None:
        self.backend = backend
        self.pass_threshold = pass_threshold

    def _backend_or_none(self, prompt: str) -> Mapping[str, Any] | None:
        if self.backend is None:
            return None

        raw = self.backend.complete_json(prompt)
        if isinstance(raw, Mapping):
            return raw
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                return None
            if isinstance(parsed, Mapping):
                return parsed
        return None

    def _heuristic_evaluate(self, record: JudgeInputRecord) -> JudgeOutputRecord:
        response = record.response
        expected = record.benchmark_record
        response_lower = response.lower()

        expected_sections = expected.expected_sections or (
            "fallacy_hypothesis",
            "reasoning_diagnosis",
            "analogy",
            "repair",
            "confidence_note",
        )
        present_sections = [
            section for section in expected_sections if _contains_section(response, section)
        ]
        completeness_score = len(present_sections) / max(1, len(expected_sections))

        instruction_following_score = completeness_score
        if expected_sections:
            indices: list[int] = []
            for section in expected_sections:
                idx = response_lower.find(section.lower())
                if idx == -1:
                    idx = response_lower.find(section.lower().replace("_", " "))
                indices.append(idx)
            if all(idx >= 0 for idx in indices) and indices == sorted(indices):
                instruction_following_score = min(1.0, instruction_following_score + 0.1)

        predicted = _extract_predicted_label(response)
        target = (
            expected.primary_fallacy_label.strip().lower().replace(" ", "_")
            if expected.primary_fallacy_label
            else None
        )
        alternatives = {
            label.strip().lower().replace(" ", "_")
            for label in expected.acceptable_alternative_labels
        }
        if target is None:
            correctness_score = (
                1.0
                if predicted
                in {
                    None,
                    "none",
                    "no_fallacy",
                    "no_fallacy_detected",
                    "valid_reasoning",
                }
                else 0.0
            )
        elif predicted == target:
            correctness_score = 1.0
        elif predicted in alternatives:
            correctness_score = 0.5
        else:
            correctness_score = 0.0

        reasoning_tokens = ["because", "therefore", "premise", "conclusion", "inference"]
        reasoning_hits = sum(token in response_lower for token in reasoning_tokens)
        reasoning_quality_score = min(1.0, reasoning_hits / 3.0)

        hallucination_markers = ("according to a study", "statistics show", "proven by data")
        hallucination_found = any(marker in response_lower for marker in hallucination_markers)
        hallucination_score = 0.0 if hallucination_found else 1.0

        overall = (
            0.25 * instruction_following_score
            + 0.25 * correctness_score
            + 0.20 * reasoning_quality_score
            + 0.20 * completeness_score
            + 0.10 * hallucination_score
        )
        overall = max(0.0, min(1.0, overall))

        return JudgeOutputRecord(
            run_id=record.run_id,
            model_id=record.model_id,
            example_id=record.example_id,
            instruction_following=JudgeDimensionScore(
                score=instruction_following_score,
                rationale="Section coverage and ordering against expected output contract.",
            ),
            correctness=JudgeDimensionScore(
                score=correctness_score,
                rationale=(
                    "Primary/alternative fallacy label consistency " "with benchmark label policy."
                ),
            ),
            reasoning_quality=JudgeDimensionScore(
                score=reasoning_quality_score,
                rationale="Presence of explicit structural reasoning signals.",
            ),
            completeness=JudgeDimensionScore(
                score=completeness_score,
                rationale=f"Present sections: {len(present_sections)}/{len(expected_sections)}.",
            ),
            hallucination=JudgeDimensionScore(
                score=hallucination_score,
                rationale=(
                    "No obvious unsupported-evidence markers found."
                    if not hallucination_found
                    else "Potential unsupported evidence marker detected."
                ),
            ),
            overall_score=overall,
            passed=overall >= self.pass_threshold,
            metadata={
                "judge_mode": "heuristic",
                "predicted_label": predicted,
                "target_label": target,
            },
        )

    def evaluate(self, record: JudgeInputRecord) -> JudgeOutputRecord:
        # Provider-backed scoring can be added without changing this interface.
        # For now, use deterministic heuristics when backend output is absent.
        backend_payload = self._backend_or_none(
            "Evaluate this response and return JSON with keys: "
            "instruction_following, correctness, reasoning_quality, "
            "completeness, hallucination, overall_score.\n\n"
            f"Prompt:\n{record.prompt}\n\nResponse:\n{record.response}"
        )
        if backend_payload is None:
            return self._heuristic_evaluate(record)

        try:

            def _dim(name: str) -> JudgeDimensionScore:
                item = backend_payload[name]
                return JudgeDimensionScore(
                    score=float(item["score"]),
                    rationale=str(item["rationale"]),
                )

            overall = float(backend_payload["overall_score"])
            overall = max(0.0, min(1.0, overall))

            return JudgeOutputRecord(
                run_id=record.run_id,
                model_id=record.model_id,
                example_id=record.example_id,
                instruction_following=_dim("instruction_following"),
                correctness=_dim("correctness"),
                reasoning_quality=_dim("reasoning_quality"),
                completeness=_dim("completeness"),
                hallucination=_dim("hallucination"),
                overall_score=overall,
                passed=overall >= self.pass_threshold,
                metadata={"judge_mode": "backend"},
            )
        except Exception:
            return self._heuristic_evaluate(record)
