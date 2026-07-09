"""Analyze prompt leakage across train/validation/test and recommend split strategy.

This script does not rewrite datasets. It produces only an analysis report.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

PROMPT_NUMERIC_RE = re.compile(r"^\s*[-+]?\d+(?:\.\d+)?\s*$")
TOKEN_RE = re.compile(r"[A-Za-z0-9']+")


@dataclass(frozen=True)
class Example:
    """One dataset row used in leakage analysis."""

    split: str
    prompt: str
    text: str
    score: float | None


@dataclass(frozen=True)
class AssignmentScore:
    """Candidate prompt-group assignment and objective values."""

    assignment: dict[str, str]
    size_cost: float
    dist_cost: float
    overall_cost: float
    split_counts: dict[str, int]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Analyze prompt leakage across dataset splits.")
    parser.add_argument(
        "--dataset-dir",
        default="datasets/final",
        help="Directory containing train.jsonl / validation.jsonl / test.jsonl.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/prompt_leakage_analysis.md",
        help="Output markdown report path.",
    )
    parser.add_argument(
        "--min-train-prompts",
        type=int,
        default=4,
        help="Minimum number of prompt groups assigned to train in recommendation search.",
    )
    return parser.parse_args()


def parse_score(value: Any) -> float | None:
    """Parse numeric score if available."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None

    raw = str(value).strip()
    if not raw:
        return None
    try:
        numeric = float(raw)
    except ValueError:
        return None
    return numeric if math.isfinite(numeric) else None


def normalize_prompt(value: Any) -> str:
    """Normalize prompt text/id value."""
    return " ".join(str(value or "").split()).strip()


def normalize_text(value: Any) -> str:
    """Normalize essay text for coarse duplicate checks."""
    return " ".join(str(value or "").split()).strip()


def load_examples(dataset_dir: Path) -> list[Example]:
    """Load examples from train/validation/test JSONL files."""
    examples: list[Example] = []

    for split in ("train", "validation", "test"):
        path = dataset_dir / f"{split}.jsonl"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue

                prompt = normalize_prompt(row.get("prompt"))
                text = normalize_text(row.get("text", row.get("essay")))
                score = parse_score(row.get("label", row.get("score")))
                if not prompt:
                    prompt = "<missing_prompt>"

                examples.append(Example(split=split, prompt=prompt, text=text, score=score))

    return examples


def prompt_overlap(examples: list[Example]) -> dict[str, set[str]]:
    """Return prompt sets per split."""
    by_split: dict[str, set[str]] = {"train": set(), "validation": set(), "test": set()}
    for ex in examples:
        by_split.setdefault(ex.split, set()).add(ex.prompt)
    return by_split


def is_prompt_textual(prompts: set[str]) -> bool:
    """Return True if prompts appear textual (not just numeric IDs)."""
    if not prompts:
        return False
    non_numeric = [prompt for prompt in prompts if not PROMPT_NUMERIC_RE.match(prompt)]
    return len(non_numeric) >= max(1, int(len(prompts) * 0.25))


def tokenize_prompt(prompt: str) -> set[str]:
    """Tokenize prompt for paraphrase heuristics."""
    return set(TOKEN_RE.findall(prompt.lower()))


def prompt_jaccard(left: str, right: str) -> float:
    """Jaccard similarity between prompt token sets."""
    left_tokens = tokenize_prompt(left)
    right_tokens = tokenize_prompt(right)
    if not left_tokens or not right_tokens:
        return 0.0
    inter = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    return inter / union if union else 0.0


def prompt_char_similarity(left: str, right: str) -> float:
    """Character trigram overlap as a fallback paraphrase heuristic."""

    def grams(text: str) -> set[str]:
        compact = re.sub(r"\s+", " ", text.lower()).strip()
        if len(compact) < 3:
            return {compact} if compact else set()
        return {compact[idx : idx + 3] for idx in range(len(compact) - 2)}

    lg = grams(left)
    rg = grams(right)
    if not lg or not rg:
        return 0.0
    inter = len(lg & rg)
    union = len(lg | rg)
    return inter / union if union else 0.0


def find_paraphrased_prompt_pairs(
    by_split: dict[str, set[str]],
) -> list[tuple[str, str, str, str, float, float]]:
    """Identify likely paraphrased prompts across splits.

    Returns tuples:
    (left_split, left_prompt, right_split, right_prompt, jaccard, trigram)
    """
    pairs: list[tuple[str, str, str, str, float, float]] = []
    split_pairs = (("train", "validation"), ("train", "test"), ("validation", "test"))

    for left_split, right_split in split_pairs:
        left_prompts = by_split.get(left_split, set())
        right_prompts = by_split.get(right_split, set())
        for left_prompt in sorted(left_prompts):
            for right_prompt in sorted(right_prompts):
                if left_prompt == right_prompt:
                    continue
                jacc = prompt_jaccard(left_prompt, right_prompt)
                tri = prompt_char_similarity(left_prompt, right_prompt)
                if jacc >= 0.75 or tri >= 0.85:
                    pairs.append((left_split, left_prompt, right_split, right_prompt, jacc, tri))

    pairs.sort(key=lambda item: (max(item[4], item[5]), item[0], item[2]), reverse=True)
    return pairs


def score_hist(scores: list[float], bins: int = 61) -> list[float]:
    """Build normalized integer score histogram over [0, 60]."""
    counts = [0.0] * bins
    valid = 0
    for score in scores:
        idx = int(round(score))
        if idx < 0:
            idx = 0
        if idx >= bins:
            idx = bins - 1
        counts[idx] += 1.0
        valid += 1
    if valid == 0:
        return counts
    return [count / valid for count in counts]


def js_divergence(p: list[float], q: list[float]) -> float:
    """Jensen-Shannon divergence between probability vectors."""
    m = [(pi + qi) / 2.0 for pi, qi in zip(p, q, strict=True)]

    def kl(a: list[float], b: list[float]) -> float:
        total = 0.0
        for ai, bi in zip(a, b, strict=True):
            if ai <= 0:
                continue
            if bi <= 0:
                continue
            total += ai * math.log(ai / bi, 2)
        return total

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def candidate_assignments(
    prompts: list[str],
    min_train_prompts: int,
) -> list[dict[str, str]]:
    """Enumerate prompt->split assignments with basic constraints."""
    assignments: list[dict[str, str]] = []
    split_labels = ("train", "validation", "test")

    for combo in itertools.product(split_labels, repeat=len(prompts)):
        mapping = {prompt: split for prompt, split in zip(prompts, combo, strict=True)}
        split_counts = Counter(mapping.values())

        if split_counts["train"] < min_train_prompts:
            continue
        if split_counts["validation"] < 1 or split_counts["test"] < 1:
            continue

        assignments.append(mapping)

    return assignments


def evaluate_assignment(
    mapping: dict[str, str],
    examples: list[Example],
    target_ratios: dict[str, float],
) -> AssignmentScore:
    """Compute objective score for one prompt-group assignment."""
    split_scores: dict[str, list[float]] = {"train": [], "validation": [], "test": []}
    split_counts: dict[str, int] = {"train": 0, "validation": 0, "test": 0}

    all_scores: list[float] = []
    for ex in examples:
        assigned = mapping.get(ex.prompt)
        if assigned is None:
            continue
        split_counts[assigned] += 1
        if ex.score is not None:
            split_scores[assigned].append(ex.score)
            all_scores.append(ex.score)

    total = sum(split_counts.values())
    if total == 0:
        return AssignmentScore(mapping, 999.0, 999.0, 999.0, split_counts)

    observed_ratios = {split: split_counts[split] / total for split in split_counts}
    size_cost = sum(abs(observed_ratios[split] - target_ratios[split]) for split in split_counts)

    global_hist = score_hist(all_scores)
    dist_terms: list[float] = []
    for split in ("train", "validation", "test"):
        if not split_scores[split]:
            dist_terms.append(1.0)
            continue
        split_hist = score_hist(split_scores[split])
        dist_terms.append(js_divergence(split_hist, global_hist))

    dist_cost = mean(dist_terms)
    overall = size_cost + 3.0 * dist_cost

    return AssignmentScore(
        assignment=mapping,
        size_cost=size_cost,
        dist_cost=dist_cost,
        overall_cost=overall,
        split_counts=split_counts,
    )


def recommend_prompt_disjoint_strategy(
    examples: list[Example],
    min_train_prompts: int,
) -> AssignmentScore | None:
    """Find best prompt-group disjoint assignment preserving score distributions."""
    prompts = sorted({ex.prompt for ex in examples})
    if len(prompts) < 3:
        return None

    observed = Counter(ex.split for ex in examples)
    total = sum(observed.values())
    target = {
        "train": observed["train"] / total if total else 0.8,
        "validation": observed["validation"] / total if total else 0.1,
        "test": observed["test"] / total if total else 0.1,
    }

    best: AssignmentScore | None = None
    for mapping in candidate_assignments(prompts, min_train_prompts=min_train_prompts):
        scored = evaluate_assignment(mapping, examples, target_ratios=target)
        if best is None or scored.overall_cost < best.overall_cost:
            best = scored

    return best


def render_report(
    *,
    dataset_dir: Path,
    examples: list[Example],
    by_split_prompts: dict[str, set[str]],
    paraphrase_pairs: list[tuple[str, str, str, str, float, float]],
    recommendation: AssignmentScore | None,
) -> str:
    """Render markdown prompt leakage report."""
    overlaps = {
        "train_validation": by_split_prompts["train"] & by_split_prompts["validation"],
        "train_test": by_split_prompts["train"] & by_split_prompts["test"],
        "validation_test": by_split_prompts["validation"] & by_split_prompts["test"],
    }

    prompt_split_presence: dict[str, set[str]] = defaultdict(set)
    prompt_split_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ex in examples:
        prompt_split_presence[ex.prompt].add(ex.split)
        prompt_split_counts[ex.prompt][ex.split] += 1

    leaking_prompts = {
        prompt: sorted(list(splits))
        for prompt, splits in prompt_split_presence.items()
        if len(splits) > 1
    }

    lines = [
        "# Prompt Leakage Analysis",
        "",
        f"- Dataset directory: `{dataset_dir}`",
        f"- Total examples analyzed: `{len(examples)}`",
        f"- Unique prompts: `{len(prompt_split_presence)}`",
        "",
        "## Exact Prompt Overlap",
        "",
        f"- `train ∩ validation`: `{len(overlaps['train_validation'])}` prompts",
        f"- `train ∩ test`: `{len(overlaps['train_test'])}` prompts",
        f"- `validation ∩ test`: `{len(overlaps['validation_test'])}` prompts",
        "",
        "| prompt | train | validation | test | split_count |",
        "|---|---:|---:|---:|---:|",
    ]

    for prompt in sorted(prompt_split_counts):
        counts = prompt_split_counts[prompt]
        lines.append(
            "| "
            f"`{prompt}` | "
            f"{counts.get('train', 0)} | "
            f"{counts.get('validation', 0)} | "
            f"{counts.get('test', 0)} | "
            f"{len(prompt_split_presence[prompt])} |"
        )

    lines.extend(["", "## Paraphrased Prompt Overlap", ""])

    all_prompts = set().union(*by_split_prompts.values())
    if not is_prompt_textual(all_prompts):
        lines.append(
            "Prompt values are ID-like (mostly numeric), so paraphrase detection on prompt text "
            "is not meaningful with the current split files."
        )
    elif paraphrase_pairs:
        lines.append("Likely paraphrased prompt pairs across splits:")
        lines.append("")
        lines.append(
            "| left_split | left_prompt | right_split | right_prompt | jaccard | trigram |"
        )
        lines.append("|---|---|---|---|---:|---:|")
        for left_split, left_prompt, right_split, right_prompt, jacc, tri in paraphrase_pairs[:50]:
            lines.append(
                "| "
                f"`{left_split}` | `{left_prompt}` | `{right_split}` | `{right_prompt}` | "
                f"{jacc:.3f} | {tri:.3f} |"
            )
        if len(paraphrase_pairs) > 50:
            lines.append(f"| ... | ... | ... | ... | ... | ... ({len(paraphrase_pairs)-50} more) |")
    else:
        lines.append("No likely paraphrased prompts detected across splits.")

    lines.extend(["", "## Prompt-Family Leakage Into Evaluation", ""])
    if leaking_prompts:
        lines.append(
            "Prompts appearing in multiple splits: "
            f"`{len(leaking_prompts)}/{len(prompt_split_presence)}`."
        )
        lines.append(
            "This indicates essays from the same prompt family are present in both training and "
            "evaluation splits."
        )
    else:
        lines.append("No cross-split prompt-family leakage detected.")

    lines.extend(["", "## Recommendation", ""])
    if recommendation is None:
        lines.append("Insufficient prompt groups to compute a prompt-disjoint recommendation.")
    else:
        split_to_prompts: dict[str, list[str]] = {"train": [], "validation": [], "test": []}
        for prompt, split in recommendation.assignment.items():
            split_to_prompts[split].append(prompt)
        for split in split_to_prompts:
            split_to_prompts[split].sort()

        lines.append(
            "Recommended strategy: **prompt-group disjoint split** "
            "(no prompt appears in more than one split)."
        )
        lines.append("")
        lines.append("Suggested assignment (optimized for size + score-distribution preservation):")
        lines.append("")
        lines.append(f"- train prompts: `{split_to_prompts['train']}`")
        lines.append(f"- validation prompts: `{split_to_prompts['validation']}`")
        lines.append(f"- test prompts: `{split_to_prompts['test']}`")
        lines.append("")
        lines.append(
            f"- Expected counts: train=`{recommendation.split_counts['train']}`, "
            f"validation=`{recommendation.split_counts['validation']}`, "
            f"test=`{recommendation.split_counts['test']}`"
        )
        lines.append(f"- Size deviation objective: `{recommendation.size_cost:.6f}`")
        lines.append(f"- Score-distribution divergence objective: `{recommendation.dist_cost:.6f}`")
        lines.append(f"- Combined objective: `{recommendation.overall_cost:.6f}`")
        lines.append("")
        lines.append("Why this strategy:")
        lines.append("- Prevents exact and prompt-family leakage by construction.")
        lines.append(
            "- Preserves score distributions better than arbitrary prompt holdout "
            "by optimizing divergence."
        )
        lines.append(
            "- Keeps evaluation prompts unseen during training, "
            "which is the correct generalization test."
        )

    lines.extend(["", "## Operational Guidance (No Rewrite Performed)", ""])
    lines.append("- Keep current files unchanged for now (this report is analysis only).")
    lines.append(
        "- If you proceed, rebuild splits by grouping on prompt ID first, "
        "then assigning prompt groups "
        "to train/validation/test using the recommended partition."
    )
    lines.append(
        "- After re-splitting, rerun leakage and score-distribution checks "
        "to confirm zero prompt overlap."
    )

    return "\n".join(lines)


def main() -> None:
    """Run prompt leakage analysis and write report."""
    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    report_path = Path(args.report_path)

    report_path.parent.mkdir(parents=True, exist_ok=True)

    examples = load_examples(dataset_dir)
    by_split_prompts = prompt_overlap(examples)
    paraphrase_pairs = find_paraphrased_prompt_pairs(by_split_prompts)
    recommendation = recommend_prompt_disjoint_strategy(
        examples,
        min_train_prompts=args.min_train_prompts,
    )

    report = render_report(
        dataset_dir=dataset_dir,
        examples=examples,
        by_split_prompts=by_split_prompts,
        paraphrase_pairs=paraphrase_pairs,
        recommendation=recommendation,
    )
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "examples": len(examples),
                "unique_prompts": len({ex.prompt for ex in examples}),
                "paraphrase_pairs": len(paraphrase_pairs),
                "report_path": str(report_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
