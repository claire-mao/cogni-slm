"""Deduplication for synthetic dataset candidates."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Any, Protocol

from data.schemas import CandidateExample, DedupDecision


@dataclass(frozen=True)
class DedupConfig:
    """Configuration for lexical/semantic/structural dedup behavior."""

    lexical_similarity_threshold: float
    semantic_similarity_threshold: float
    structural_similarity_threshold: float
    cross_split_dedup: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class DuplicateCluster:
    """Grouped duplicate candidates for winner selection."""

    cluster_id: str
    member_example_ids: tuple[str, ...]
    representative_example_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class Deduplicator(Protocol):
    """Contract for deduplicating candidate examples."""

    def cluster(self, candidates: Sequence[CandidateExample]) -> Sequence[DuplicateCluster]:
        """Identify duplicate clusters for a candidate set."""

    def decide(self, clusters: Sequence[DuplicateCluster]) -> Sequence[DedupDecision]:
        """Select kept/rejected examples from duplicate clusters."""


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", "", text.lower())).strip()


def _token_jaccard(left: str, right: str) -> float:
    left_tokens = set(_normalize(left).split())
    right_tokens = set(_normalize(right).split())
    if not left_tokens and not right_tokens:
        return 1.0
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = left_tokens & right_tokens
    union = left_tokens | right_tokens
    return len(intersection) / len(union)


class DefaultDeduplicator:
    """Pairwise deduplicator using lexical, token, and structural similarity."""

    def __init__(self, config: DedupConfig) -> None:
        self.config = config
        self._candidates_by_id: dict[str, CandidateExample] = {}

    def _similar(self, left: CandidateExample, right: CandidateExample) -> tuple[bool, float, str]:
        lexical = SequenceMatcher(
            None, _normalize(left.argument_text), _normalize(right.argument_text)
        ).ratio()
        semantic = _token_jaccard(left.argument_text, right.argument_text)

        left_struct = (
            (left.behavior_output.reasoning_diagnosis if left.behavior_output else "")
            + " "
            + str(left.primary_fallacy_label)
        )
        right_struct = (
            (right.behavior_output.reasoning_diagnosis if right.behavior_output else "")
            + " "
            + str(right.primary_fallacy_label)
        )
        structural = SequenceMatcher(
            None, _normalize(left_struct), _normalize(right_struct)
        ).ratio()

        if lexical >= self.config.lexical_similarity_threshold:
            return True, lexical, "lexical"
        if semantic >= self.config.semantic_similarity_threshold:
            return True, semantic, "semantic"
        if (
            left.primary_fallacy_label == right.primary_fallacy_label
            and structural >= self.config.structural_similarity_threshold
        ):
            return True, structural, "structural"

        return False, max(lexical, semantic, structural), "none"

    def cluster(self, candidates: Sequence[CandidateExample]) -> Sequence[DuplicateCluster]:
        self._candidates_by_id = {candidate.example_id: candidate for candidate in candidates}
        n = len(candidates)
        parent = list(range(n))

        def find(index: int) -> int:
            while parent[index] != index:
                parent[index] = parent[parent[index]]
                index = parent[index]
            return index

        def union(left: int, right: int) -> None:
            root_left = find(left)
            root_right = find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        for left in range(n):
            for right in range(left + 1, n):
                is_dup, _, _ = self._similar(candidates[left], candidates[right])
                if is_dup:
                    union(left, right)

        groups: dict[int, list[CandidateExample]] = {}
        for idx, candidate in enumerate(candidates):
            groups.setdefault(find(idx), []).append(candidate)

        clusters: list[DuplicateCluster] = []
        for cluster_index, members in enumerate(groups.values(), start=1):
            representative = max(
                members,
                key=lambda candidate: (
                    float(candidate.metadata.get("critique_overall", 0.0)),
                    len(candidate.argument_text),
                    candidate.example_id,
                ),
            )
            clusters.append(
                DuplicateCluster(
                    cluster_id=f"cluster-{cluster_index:04d}",
                    member_example_ids=tuple(member.example_id for member in members),
                    representative_example_id=representative.example_id,
                    metadata={"size": len(members)},
                )
            )

        return tuple(clusters)

    def decide(self, clusters: Sequence[DuplicateCluster]) -> Sequence[DedupDecision]:
        decisions: list[DedupDecision] = []
        for cluster in clusters:
            representative = cluster.representative_example_id
            for member_id in cluster.member_example_ids:
                kept = member_id == representative
                reason = "representative" if kept else "duplicate_removed"
                candidate = self._candidates_by_id.get(member_id)
                score = None
                if (
                    candidate is not None
                    and representative is not None
                    and member_id != representative
                ):
                    _, score, _ = self._similar(candidate, self._candidates_by_id[representative])

                decisions.append(
                    DedupDecision(
                        example_id=member_id,
                        kept=kept,
                        dedup_cluster_id=cluster.cluster_id,
                        similarity_score=score,
                        reason=reason,
                        metadata=cluster.metadata,
                    )
                )

        return tuple(decisions)
