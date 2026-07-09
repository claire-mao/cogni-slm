"""Create candidate prompt-group splits without overwriting existing datasets.

This script:
1. Loads the current training dataset and split-wise provenance sidecar.
2. Groups all examples by prompt.
3. Searches prompt-to-split assignments with no prompt overlap.
4. Selects the assignment that best balances split sizes and score distribution.
5. Writes candidate split JSONL files (prompt, essay, score only).
6. Writes candidate provenance sidecar files preserving source lineage.
7. Writes a markdown report to docs/reports/group_split.md.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import shutil
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from datasets import load_from_disk

SPLITS = ("train", "validation", "test")
SPLIT_INDEX = {name: idx for idx, name in enumerate(SPLITS)}


@dataclass(frozen=True)
class ExampleRecord:
    """One candidate example with provenance linkage."""

    prompt: str
    essay: str
    score: float
    original_split: str
    original_example_index: int
    provenance: dict[str, Any]


@dataclass(frozen=True)
class AssignmentScore:
    """Objective components for one prompt assignment."""

    objective: float
    size_error: float
    dist_error: float


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(
        description="Create candidate train/validation/test split by prompt groups."
    )
    parser.add_argument(
        "--input-dataset-dir",
        default="datasets/training",
        help="Existing HF training dataset directory.",
    )
    parser.add_argument(
        "--input-provenance-dir",
        default="datasets/training_provenance",
        help="Existing split-wise provenance JSONL directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/training_candidates/prompt_group_split",
        help="Output candidate split directory.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/group_split.md",
        help="Output markdown report path.",
    )
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--validation-ratio", type=float, default=0.1)
    parser.add_argument("--test-ratio", type=float, default=0.1)
    parser.add_argument(
        "--size-weight",
        type=float,
        default=1.0,
        help="Objective weight for split-size deviation.",
    )
    parser.add_argument(
        "--distribution-weight",
        type=float,
        default=2.0,
        help="Objective weight for score-distribution deviation.",
    )
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL rows from disk."""
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    """Write JSONL rows to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def score_histogram(scores: list[float], bins: list[float]) -> list[float]:
    """Return normalized histogram over explicit score bins."""
    if not scores:
        return [0.0 for _ in bins]
    counts = Counter(scores)
    total = float(len(scores))
    return [counts.get(bin_value, 0) / total for bin_value in bins]


def l1_distance(a: list[float], b: list[float]) -> float:
    """Return L1 distance between two same-length vectors."""
    return sum(abs(x - y) for x, y in zip(a, b, strict=True))


def validate_ratios(train: float, validation: float, test: float) -> None:
    """Validate split ratios."""
    total = train + validation + test
    if not math.isfinite(total) or total <= 0:
        raise ValueError("Split ratios must sum to a positive finite value.")


def load_records(
    dataset_dir: Path,
    provenance_dir: Path,
) -> tuple[list[ExampleRecord], int, int]:
    """Load examples and align each with provenance entries."""
    dataset = load_from_disk(str(dataset_dir))

    records: list[ExampleRecord] = []
    missing_provenance_rows = 0
    sha_mismatch_rows = 0

    for split in SPLITS:
        if split not in dataset:
            continue

        split_rows = dataset[split]
        provenance_rows = load_jsonl(provenance_dir / f"{split}.jsonl")

        for idx, row in enumerate(split_rows):
            prompt = str(row.get("prompt", "")).strip()
            essay = str(row.get("essay", "")).strip()
            score = float(row.get("score"))

            provenance = provenance_rows[idx] if idx < len(provenance_rows) else {}
            if idx >= len(provenance_rows):
                missing_provenance_rows += 1

            essay_sha256 = hashlib.sha256(essay.encode("utf-8")).hexdigest()
            prov_sha = provenance.get("essay_sha256")
            if isinstance(prov_sha, str) and prov_sha and prov_sha != essay_sha256:
                sha_mismatch_rows += 1

            records.append(
                ExampleRecord(
                    prompt=prompt,
                    essay=essay,
                    score=score,
                    original_split=split,
                    original_example_index=idx,
                    provenance=provenance,
                )
            )

    if not records:
        raise ValueError("No records loaded from dataset.")

    return records, missing_provenance_rows, sha_mismatch_rows


def assignment_objective(
    assignment: tuple[int, ...],
    prompts: list[str],
    grouped: dict[str, list[ExampleRecord]],
    target_counts: dict[str, float],
    global_hist: list[float],
    bins: list[float],
    size_weight: float,
    distribution_weight: float,
) -> AssignmentScore | None:
    """Compute objective for one prompt->split assignment."""
    split_records: dict[str, list[ExampleRecord]] = {split: [] for split in SPLITS}

    for prompt, split_idx in zip(prompts, assignment, strict=True):
        split = SPLITS[split_idx]
        split_records[split].extend(grouped[prompt])

    if any(len(split_records[split]) == 0 for split in SPLITS):
        return None

    total = float(sum(len(split_records[split]) for split in SPLITS))
    if total <= 0:
        return None

    size_error = 0.0
    dist_error = 0.0
    for split in SPLITS:
        split_count = len(split_records[split])
        target = target_counts[split]
        size_error += abs(split_count - target) / total

        split_scores = [record.score for record in split_records[split]]
        split_hist = score_histogram(split_scores, bins)
        dist_error += l1_distance(split_hist, global_hist)

    objective = size_weight * size_error + distribution_weight * dist_error
    return AssignmentScore(objective=objective, size_error=size_error, dist_error=dist_error)


def find_best_assignment(
    grouped: dict[str, list[ExampleRecord]],
    train_ratio: float,
    validation_ratio: float,
    test_ratio: float,
    size_weight: float,
    distribution_weight: float,
) -> tuple[dict[str, str], AssignmentScore]:
    """Exhaustively search prompt assignments to minimize objective."""
    prompts = sorted(grouped.keys())
    all_scores = [record.score for records in grouped.values() for record in records]
    bins = sorted(set(all_scores))

    total = float(len(all_scores))
    ratio_total = train_ratio + validation_ratio + test_ratio
    target_counts = {
        "train": total * (train_ratio / ratio_total),
        "validation": total * (validation_ratio / ratio_total),
        "test": total * (test_ratio / ratio_total),
    }

    global_hist = score_histogram(all_scores, bins)

    best: AssignmentScore | None = None
    best_assignment: tuple[int, ...] | None = None

    for assignment in itertools.product(range(3), repeat=len(prompts)):
        metric = assignment_objective(
            assignment=assignment,
            prompts=prompts,
            grouped=grouped,
            target_counts=target_counts,
            global_hist=global_hist,
            bins=bins,
            size_weight=size_weight,
            distribution_weight=distribution_weight,
        )
        if metric is None:
            continue

        if best is None or metric.objective < best.objective:
            best = metric
            best_assignment = assignment

    if best is None or best_assignment is None:
        raise ValueError("Unable to find a valid prompt-group assignment.")

    mapping = {
        prompt: SPLITS[split_idx]
        for prompt, split_idx in zip(prompts, best_assignment, strict=True)
    }
    return mapping, best


def summarize_scores(scores: list[float]) -> dict[str, float | None]:
    """Compute basic score summary stats."""
    if not scores:
        return {"min": None, "max": None, "mean": None, "std": None}
    return {
        "min": min(scores),
        "max": max(scores),
        "mean": mean(scores),
        "std": pstdev(scores),
    }


def render_report(
    *,
    records: list[ExampleRecord],
    prompt_to_split: dict[str, str],
    candidate_examples: dict[str, list[dict[str, Any]]],
    candidate_provenance: dict[str, list[dict[str, Any]]],
    assignment_score: AssignmentScore,
    output_dir: Path,
    missing_provenance_rows: int,
    sha_mismatch_rows: int,
) -> str:
    """Build markdown split report."""
    all_scores = [record.score for record in records]
    global_summary = summarize_scores(all_scores)

    prompts_by_split: dict[str, list[str]] = {split: [] for split in SPLITS}
    for prompt, split in sorted(prompt_to_split.items()):
        prompts_by_split[split].append(prompt)

    # Verify no prompt overlap.
    overlap_tv = set(prompts_by_split["train"]) & set(prompts_by_split["validation"])
    overlap_tt = set(prompts_by_split["train"]) & set(prompts_by_split["test"])
    overlap_vt = set(prompts_by_split["validation"]) & set(prompts_by_split["test"])

    lines = [
        "# Prompt-Group Candidate Split Report",
        "",
        "## Objective",
        "",
        "Create a candidate split where each prompt appears in exactly one split, while balancing",
        "split sizes and score distributions as much as possible.",
        "",
        "## Candidate Output",
        "",
        f"- Candidate directory: `{output_dir}`",
        "- Data files: `train.jsonl`, `validation.jsonl`, `test.jsonl`",
        "- Data schema: `prompt`, `essay`, `score`",
        "- Provenance sidecar: `provenance/{train,validation,test}.jsonl`",
        "",
        "## Search Method",
        "",
        f"- Prompt groups searched: `{len(prompt_to_split)}`",
        f"- Exhaustive assignments evaluated: `{3 ** len(prompt_to_split)}`",
        "- Constraint: each prompt assigned to one split only",
        "- Objective: `size_weight * size_error + distribution_weight * distribution_error`",
        f"- Best objective: `{assignment_score.objective:.6f}`",
        f"- Size error component: `{assignment_score.size_error:.6f}`",
        f"- Distribution error component: `{assignment_score.dist_error:.6f}`",
        "",
        "## Prompt Assignment",
        "",
        "| split | prompts |",
        "|---|---|",
    ]

    for split in SPLITS:
        lines.append(f"| {split} | {', '.join(prompts_by_split[split])} |")

    lines.extend(
        [
            "",
            "## Prompt Overlap Check",
            "",
            f"- train ∩ validation: `{len(overlap_tv)}`",
            f"- train ∩ test: `{len(overlap_tt)}`",
            f"- validation ∩ test: `{len(overlap_vt)}`",
            "",
            "## Split Summary",
            "",
            "| split | examples | prompts | score_min | score_max | score_mean | score_std |",
            "|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for split in SPLITS:
        split_scores = [row["score"] for row in candidate_examples[split]]
        summary = summarize_scores(split_scores)

        def fmt(value: float | None) -> str:
            return "N/A" if value is None else f"{value:.4f}"

        lines.append(
            f"| {split} | {len(candidate_examples[split])} | {len(prompts_by_split[split])} "
            f"| {fmt(summary['min'])} | {fmt(summary['max'])} "
            f"| {fmt(summary['mean'])} | {fmt(summary['std'])} |"
        )

    lines.extend(
        [
            "",
            "## Global Score Summary",
            "",
            f"- Total examples: `{len(records)}`",
            f"- Min: `{global_summary['min']:.4f}`",
            f"- Max: `{global_summary['max']:.4f}`",
            f"- Mean: `{global_summary['mean']:.4f}`",
            f"- Std: `{global_summary['std']:.4f}`",
            "",
            "## Provenance Preservation",
            "",
            f"- Candidate provenance rows: `{sum(len(candidate_provenance[s]) for s in SPLITS)}`",
            f"- Missing provenance rows during load: `{missing_provenance_rows}`",
            f"- Essay hash mismatches vs provenance: `{sha_mismatch_rows}`",
            "- Each candidate provenance row includes:",
            "  - `candidate_example_index`",
            "  - `candidate_split`",
            "  - `original_split`",
            "  - `original_example_index`",
            "  - `prompt`",
            "  - `essay_sha256`",
            "  - `source_records`",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    """Create prompt-group candidate split and report."""
    args = parse_args()
    validate_ratios(args.train_ratio, args.validation_ratio, args.test_ratio)

    input_dataset_dir = Path(args.input_dataset_dir)
    input_provenance_dir = Path(args.input_provenance_dir)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)

    records, missing_provenance_rows, sha_mismatch_rows = load_records(
        dataset_dir=input_dataset_dir,
        provenance_dir=input_provenance_dir,
    )

    grouped: dict[str, list[ExampleRecord]] = defaultdict(list)
    for record in records:
        grouped[record.prompt].append(record)

    if not grouped:
        raise ValueError("No records found for prompt-group splitting.")

    prompt_to_split, assignment_score = find_best_assignment(
        grouped=grouped,
        train_ratio=args.train_ratio,
        validation_ratio=args.validation_ratio,
        test_ratio=args.test_ratio,
        size_weight=args.size_weight,
        distribution_weight=args.distribution_weight,
    )

    candidate_examples: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}
    candidate_provenance: dict[str, list[dict[str, Any]]] = {split: [] for split in SPLITS}

    for prompt in sorted(grouped.keys()):
        target_split = prompt_to_split[prompt]
        for record in grouped[prompt]:
            row_index = len(candidate_examples[target_split])
            candidate_examples[target_split].append(
                {
                    "prompt": record.prompt,
                    "essay": record.essay,
                    "score": record.score,
                }
            )
            candidate_provenance[target_split].append(
                {
                    "candidate_example_index": row_index,
                    "candidate_split": target_split,
                    "original_split": record.original_split,
                    "original_example_index": record.original_example_index,
                    "prompt": record.prompt,
                    "essay_sha256": hashlib.sha256(record.essay.encode("utf-8")).hexdigest(),
                    "source_records": record.provenance.get("source_records", []),
                }
            )

    data_dir = output_dir / "data"
    prov_dir = output_dir / "provenance"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for split in SPLITS:
        write_jsonl(data_dir / f"{split}.jsonl", candidate_examples[split])
        write_jsonl(prov_dir / f"{split}.jsonl", candidate_provenance[split])

    summary = {
        "input_dataset_dir": str(input_dataset_dir),
        "input_provenance_dir": str(input_provenance_dir),
        "output_dir": str(output_dir),
        "prompt_to_split": prompt_to_split,
        "assignment_score": {
            "objective": assignment_score.objective,
            "size_error": assignment_score.size_error,
            "distribution_error": assignment_score.dist_error,
        },
        "counts": {split: len(candidate_examples[split]) for split in SPLITS},
        "missing_provenance_rows": missing_provenance_rows,
        "sha_mismatch_rows": sha_mismatch_rows,
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        render_report(
            records=records,
            prompt_to_split=prompt_to_split,
            candidate_examples=candidate_examples,
            candidate_provenance=candidate_provenance,
            assignment_score=assignment_score,
            output_dir=output_dir,
            missing_provenance_rows=missing_provenance_rows,
            sha_mismatch_rows=sha_mismatch_rows,
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "output_dir": str(output_dir),
                "report_path": str(report_path),
                "counts": {split: len(candidate_examples[split]) for split in SPLITS},
                "prompt_to_split": prompt_to_split,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
