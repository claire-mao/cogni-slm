"""Heuristic feedback-quality scoring for essay-evaluation outputs."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

ACTIONABLE_MARKERS = (
    "revise",
    "add",
    "clarify",
    "explain",
    "support",
    "evidence",
    "counterargument",
    "thesis",
    "commentary",
)

GENERIC_PHRASES = (
    "good job",
    "nice work",
    "needs improvement",
    "keep it up",
    "well done",
)

TOKEN_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")


@dataclass(frozen=True)
class FeedbackQualityResult:
    """Feedback-quality scalar with component diagnostics."""

    score: float
    length_score: float
    actionable_score: float
    specificity_score: float
    generic_penalty: float


def _normalize(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def score_feedback_quality(feedback: str, essay: str) -> FeedbackQualityResult:
    """Score feedback quality on a 0..1 scale."""
    feedback_norm = _normalize(feedback)
    essay_norm = _normalize(essay)

    if not feedback_norm:
        return FeedbackQualityResult(
            score=0.0,
            length_score=0.0,
            actionable_score=0.0,
            specificity_score=0.0,
            generic_penalty=0.0,
        )

    feedback_tokens = _tokens(feedback_norm)
    essay_tokens = _tokens(essay_norm)

    token_count = len(feedback_tokens)
    if token_count <= 5:
        length_score = token_count / 5.0
    elif token_count <= 40:
        length_score = 1.0
    elif token_count <= 120:
        length_score = max(0.4, 1.0 - (token_count - 40) / 200.0)
    else:
        length_score = max(0.1, 0.4 - (token_count - 120) / 600.0)

    actionable_hits = sum(1 for marker in ACTIONABLE_MARKERS if marker in feedback_norm)
    actionable_score = min(1.0, actionable_hits / 3.0)

    essay_content = [tok for tok in essay_tokens if len(tok) >= 5]
    feedback_content = [tok for tok in feedback_tokens if len(tok) >= 5]
    if not essay_content or not feedback_content:
        specificity_score = 0.0
    else:
        essay_counts = Counter(essay_content)
        overlap = sum(1 for tok in set(feedback_content) if tok in essay_counts)
        specificity_score = min(1.0, overlap / max(1, len(set(feedback_content)) * 0.6))

    generic_hits = sum(1 for phrase in GENERIC_PHRASES if phrase in feedback_norm)
    generic_penalty = min(0.35, generic_hits * 0.12)

    score = 0.35 * length_score + 0.35 * actionable_score + 0.30 * specificity_score
    score = max(0.0, min(1.0, score - generic_penalty))

    return FeedbackQualityResult(
        score=score,
        length_score=length_score,
        actionable_score=actionable_score,
        specificity_score=specificity_score,
        generic_penalty=generic_penalty,
    )
