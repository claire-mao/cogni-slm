"""LLM-as-judge interfaces and default scoring adapter."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol

from evaluation.benchmark import BenchmarkRecord, SplitName


@dataclass(frozen=True)
class JudgeRubric:
    """Rubric definition consumed by an LLM judge backend."""

    rubric_id: str
    dimension: str
    description: str
    criteria: tuple[str, ...]
    min_score: float = 0.0
    max_score: float = 1.0


@dataclass(frozen=True)
class JudgeInput:
    """Per-example payload for semantic judge scoring."""

    run_id: str
    model_id: str
    example_id: str
    split: SplitName
    record: BenchmarkRecord
    response_text: str
    deterministic_findings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class JudgeResult:
    """Score output produced by a judge rubric."""

    run_id: str
    model_id: str
    example_id: str
    split: SplitName
    rubric_id: str
    dimension: str
    score: float
    rationale: str
    confidence_interval: tuple[float, float] | None = None


class LLMJudge(Protocol):
    """Contract for LLM-based rubric scoring."""

    def score(
        self,
        judge_input: JudgeInput,
        rubrics: Sequence[JudgeRubric],
    ) -> Sequence[JudgeResult]:
        """Score one example against one or more rubrics."""


class JudgeBackend(Protocol):
    """Minimal backend protocol for external LLM judge providers."""

    def complete(self, prompt: str) -> str:
        """Return model output text for a given judge prompt."""


class DefaultLLMJudge:
    """Default LLM-as-judge implementation with pluggable backend.

    If no backend is supplied, it falls back to a deterministic heuristic to keep
    the pipeline runnable in offline/test environments.
    """

    def __init__(self, backend: JudgeBackend | None = None) -> None:
        self.backend = backend

    def _build_prompt(self, judge_input: JudgeInput, rubric: JudgeRubric) -> str:
        criteria_block = "\n".join(f"- {criterion}" for criterion in rubric.criteria)
        findings_block = "\n".join(judge_input.deterministic_findings) or "(none)"

        return (
            "You are an evaluation judge for a logical-fallacy tutor.\n"
            "Score the response against the rubric and return JSON with keys "
            "`score` (float) and `rationale` (string).\n\n"
            f"Rubric ID: {rubric.rubric_id}\n"
            f"Dimension: {rubric.dimension}\n"
            f"Description: {rubric.description}\n"
            f"Criteria:\n{criteria_block}\n\n"
            f"Argument:\n{judge_input.record.argument_text}\n\n"
            f"Response:\n{judge_input.response_text}\n\n"
            f"Deterministic findings:\n{findings_block}\n"
        )

    def _heuristic_score(self, judge_input: JudgeInput, rubric: JudgeRubric) -> JudgeResult:
        response = judge_input.response_text.strip()
        word_count = len(response.split())
        coverage_hits = sum(
            1 for criterion in rubric.criteria if criterion.lower() in response.lower()
        )
        coverage_ratio = coverage_hits / max(1, len(rubric.criteria))

        base_score = 0.2 + 0.4 * min(1.0, word_count / 120.0) + 0.4 * coverage_ratio
        score = min(rubric.max_score, max(rubric.min_score, base_score))

        rationale = (
            "Heuristic fallback used (no LLM backend configured). "
            f"Word count={word_count}, criteria hits={coverage_hits}/{len(rubric.criteria)}."
        )
        return JudgeResult(
            run_id=judge_input.run_id,
            model_id=judge_input.model_id,
            example_id=judge_input.example_id,
            split=judge_input.split,
            rubric_id=rubric.rubric_id,
            dimension=rubric.dimension,
            score=score,
            rationale=rationale,
            confidence_interval=None,
        )

    def _backend_score(self, judge_input: JudgeInput, rubric: JudgeRubric) -> JudgeResult:
        if self.backend is None:
            return self._heuristic_score(judge_input, rubric)

        raw = self.backend.complete(self._build_prompt(judge_input, rubric))
        score = 0.5
        rationale = "Judge backend response could not be parsed; default score applied."

        try:
            payload = json.loads(raw)
            score = float(payload.get("score", score))
            rationale = str(payload.get("rationale", rationale))
        except json.JSONDecodeError:
            rationale = f"Raw backend response (unparsed): {raw[:300]}"

        score = min(rubric.max_score, max(rubric.min_score, score))
        return JudgeResult(
            run_id=judge_input.run_id,
            model_id=judge_input.model_id,
            example_id=judge_input.example_id,
            split=judge_input.split,
            rubric_id=rubric.rubric_id,
            dimension=rubric.dimension,
            score=score,
            rationale=rationale,
            confidence_interval=None,
        )

    def score(
        self,
        judge_input: JudgeInput,
        rubrics: Sequence[JudgeRubric],
    ) -> Sequence[JudgeResult]:
        return tuple(self._backend_score(judge_input, rubric) for rubric in rubrics)
