#!/usr/bin/env python3
"""Evaluate prompt-test outputs against the strict AP 7-step behavior spec."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.llm_judge import DefaultLLMJudge, JudgeInput, JudgeRubric  # noqa: E402

FALLACY_LABELS = {
    "ad_hominem",
    "ad_populum",
    "appeal_to_emotion",
    "appeal_to_false_authority",
    "appeal_to_fear",
    "appeal_to_nature",
    "appeal_to_pity",
    "appeal_to_tradition",
    "circular_reasoning",
    "equivocation",
    "false_analogy",
    "false_causality",
    "false_dilemma",
    "faulty_generalization",
    "hasty_generalization",
    "irrelevant_authority",
    "red_herring",
    "slippery_slope",
    "straw_man",
    "tu_quoque",
    "none",
}


@dataclass(frozen=True)
class MiniRecord:
    argument_text: str


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _strip_think(text: str) -> str:
    if "</think>" in text:
        return text.split("</think>", maxsplit=1)[1].strip()
    return text.strip()


def _norm(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def _extract_predicted_fallacy(text: str) -> str | None:
    lowered = _norm(text)
    for label in sorted(FALLACY_LABELS, key=len, reverse=True):
        phrase = label.replace("_", " ")
        if re.search(rf"\b{re.escape(phrase)}\b", lowered):
            return label
    if "no clear fallacy" in lowered or "no fallacy" in lowered:
        return "none"
    return None


def _count_question_marks(text: str) -> int:
    return text.count("?")


def _step_checks(response_text: str, argument_text: str) -> tuple[dict[str, bool], str | None]:
    text = _strip_think(response_text)
    lowered = _norm(text)

    s1 = ("argument summary" in lowered) or ("summary" in lowered and "argument" in lowered)
    s2 = "assumption" in lowered

    predicted = _extract_predicted_fallacy(text)
    s3 = ("primary fallacy" in lowered) and (predicted is not None)

    s4 = (("why this applies" in lowered) or ("because" in lowered)) and (
        "fallacy" in lowered or predicted == "none"
    )

    argument_terms = {token for token in re.findall(r"[a-zA-Z]{5,}", argument_text.lower())}
    analogy_terms = {token for token in re.findall(r"[a-zA-Z]{5,}", text.lower())}
    overlap_ratio = 0.0
    if analogy_terms:
        overlap_ratio = len(argument_terms & analogy_terms) / max(1, len(analogy_terms))

    s5 = (
        ("cross-domain" in lowered or "cross domain" in lowered or "analogy" in lowered)
        and ("map" in lowered or "mapping" in lowered or "correspond" in lowered)
        and overlap_ratio < 0.55
    )

    s6 = (
        ("transfer" in lowered or "new example" in lowered)
        and _count_question_marks(text) >= 1
        and ("the answer is" not in lowered)
    )

    reflective_idx = lowered.rfind("reflective question")
    reflective_text = lowered[reflective_idx:] if reflective_idx >= 0 else ""
    s7 = reflective_idx >= 0 and reflective_text.endswith("?") and reflective_text.count("?") == 1

    return {
        "S1_summary": s1,
        "S2_assumptions": s2,
        "S3_primary_fallacy": s3,
        "S4_explanation": s4,
        "S5_analogy": s5,
        "S6_transfer": s6,
        "S7_reflective_question": s7,
    }, predicted


def _load_rubrics(path: Path) -> list[JudgeRubric]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    dims = payload.get("dimensions") if isinstance(payload, dict) else None
    rubrics: list[JudgeRubric] = []
    if not isinstance(dims, list):
        return rubrics
    for dim in dims:
        if not isinstance(dim, dict):
            continue
        rubrics.append(
            JudgeRubric(
                rubric_id=str(dim.get("rubric_id", "rubric")),
                dimension=str(dim.get("dimension", "behavior_adherence")),
                description=str(dim.get("description", "")),
                criteria=tuple(str(c) for c in dim.get("criteria", []) if str(c).strip()),
                min_score=float(dim.get("min_score", 0.0)),
                max_score=float(dim.get("max_score", 1.0)),
            )
        )
    return rubrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate AP prompt-test outputs.")
    parser.add_argument(
        "--raw-predictions",
        default="outputs/evaluation/prompt_test_public_v1/raw_predictions.jsonl",
    )
    parser.add_argument(
        "--benchmark",
        default="datasets/eval/heldout_benchmark_public_v1.jsonl",
    )
    parser.add_argument(
        "--rubric-config",
        default="configs/evaluation/ap_tutor_judge_rubric_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/evaluation/ap_prompt_test_public_v1",
    )
    args = parser.parse_args()

    raw_rows = _read_jsonl(Path(args.raw_predictions))
    benchmark_rows = _read_jsonl(Path(args.benchmark))
    benchmark_by_id = {str(row.get("example_id")): row for row in benchmark_rows}

    # Keep one prediction per example for deterministic scoring.
    by_example: dict[str, dict[str, Any]] = {}
    for row in raw_rows:
        example_id = str(row.get("example_id", "")).strip()
        if not example_id or example_id in by_example:
            continue
        by_example[example_id] = row

    rubrics = _load_rubrics(Path(args.rubric_config))
    judge = DefaultLLMJudge(backend=None)

    results: list[dict[str, Any]] = []
    pass_flags: list[bool] = []
    step_values: dict[str, list[float]] = {
        "S1_summary": [],
        "S2_assumptions": [],
        "S3_primary_fallacy": [],
        "S4_explanation": [],
        "S5_analogy": [],
        "S6_transfer": [],
        "S7_reflective_question": [],
    }
    fallacy_accuracy_values: list[float] = []
    judge_scores: dict[str, list[float]] = {}

    for example_id, pred in sorted(by_example.items()):
        benchmark = benchmark_by_id.get(example_id, {})
        argument_text = str(benchmark.get("argument_text", ""))
        response = str(pred.get("response", ""))
        checks, predicted_label = _step_checks(response, argument_text)
        passed = all(checks.values())
        pass_flags.append(passed)

        for key, value in checks.items():
            step_values[key].append(1.0 if value else 0.0)

        expected_label = str(benchmark.get("primary_fallacy_label", "")).strip().lower()
        acceptable = benchmark.get("acceptable_alternative_labels")
        alt_labels = {
            str(item).strip().lower()
            for item in acceptable
            if isinstance(acceptable, list) and str(item).strip()
        }
        fallacy_ok = 0.0
        if predicted_label is not None:
            normalized_pred = predicted_label.strip().lower()
            if normalized_pred == expected_label or normalized_pred in alt_labels:
                fallacy_ok = 1.0
        fallacy_accuracy_values.append(fallacy_ok)

        deterministic_findings = tuple(key for key, value in checks.items() if not value)

        if rubrics:
            judge_input = JudgeInput(
                run_id=str(pred.get("run_id", "ap-prompt-test")),
                model_id=str(pred.get("model_id", "unknown")),
                example_id=example_id,
                split="heldout_benchmark",
                record=MiniRecord(argument_text=argument_text),
                response_text=response,
                deterministic_findings=deterministic_findings,
                metadata={},
            )
            judge_results = judge.score(judge_input, rubrics)
            for jr in judge_results:
                judge_scores.setdefault(jr.dimension, []).append(float(jr.score))

        results.append(
            {
                "example_id": example_id,
                "passed": passed,
                "step_checks": checks,
                "predicted_fallacy_label": predicted_label,
                "expected_fallacy_label": expected_label,
                "fallacy_accuracy": fallacy_ok,
            }
        )

    summary = {
        "run_id": "ap-prompt-test-eval-v1",
        "example_count": len(results),
        "metrics": {
            "overall_pass_rate": mean(pass_flags) if pass_flags else 0.0,
            "behavior_spec_adherence": (
                mean(mean(item["step_checks"].values()) for item in results) if results else 0.0
            ),
            "fallacy_accuracy": mean(fallacy_accuracy_values) if fallacy_accuracy_values else 0.0,
            "per_step_adherence": {
                key: (mean(values) if values else 0.0) for key, values in step_values.items()
            },
        },
        "judge_dimension_means": {
            key: mean(values) if values else 0.0 for key, values in sorted(judge_scores.items())
        },
        "artifacts": {
            "results": str(Path(args.output_dir) / "results.json"),
            "summary": str(Path(args.output_dir) / "summary.json"),
            "report": str(Path(args.output_dir) / "report.md"),
        },
    }

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    report_lines = [
        "# AP Prompt Test Evaluation Report",
        "",
        f"- Examples: `{summary['example_count']}`",
        f"- Overall pass rate: `{summary['metrics']['overall_pass_rate']:.4f}`",
        f"- Behavior adherence: `{summary['metrics']['behavior_spec_adherence']:.4f}`",
        f"- Fallacy accuracy: `{summary['metrics']['fallacy_accuracy']:.4f}`",
        "",
        "## Per-Step Adherence",
        "",
        "| Step | Adherence |",
        "|---|---:|",
    ]
    for step, value in summary["metrics"]["per_step_adherence"].items():
        report_lines.append(f"| {step} | {value:.4f} |")

    report_lines.extend(["", "## Judge Dimension Means", "", "| Dimension | Score |", "|---|---:|"])
    for dim, value in summary["judge_dimension_means"].items():
        report_lines.append(f"| {dim} | {value:.4f} |")

    (output_dir / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
