"""Base-vs-tuned evaluation harness for essay-scoring + feedback outputs."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .harness_data import EvalRecord, load_records_from_hf_dataset, load_records_from_jsonl
    from .harness_feedback import FeedbackQualityResult, score_feedback_quality
    from .harness_metrics import ModelMetricSummary, summarize_model_metrics
    from .harness_model import LocalModelRunner, ParsedModelOutput
except ImportError:  # pragma: no cover - script-mode import fallback
    from harness_data import EvalRecord, load_records_from_hf_dataset, load_records_from_jsonl
    from harness_feedback import FeedbackQualityResult, score_feedback_quality
    from harness_metrics import ModelMetricSummary, summarize_model_metrics
    from harness_model import LocalModelRunner, ParsedModelOutput


@dataclass(frozen=True)
class ExampleResult:
    """Per-example result row for one model."""

    id: str
    split: str
    gold_score: float
    predicted_score: float | None
    confidence: float | None
    reasoning: str
    feedback: str
    feedback_quality: float
    parse_error: str | None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Compare base vs fine-tuned model outputs.")
    parser.add_argument("--base-model-id", required=True)
    parser.add_argument("--tuned-model-id", required=True)
    parser.add_argument("--dataset-path", default="datasets/training")
    parser.add_argument("--dataset-split", default="validation")
    parser.add_argument("--input-jsonl", default="")
    parser.add_argument("--output-dir", default="outputs/evaluation/harness")
    parser.add_argument(
        "--prompt-template-path",
        default="teacher_prompts/local_teacher_inference_template.txt",
    )
    parser.add_argument("--system-role-path", default="teacher_prompts/system_role.txt")
    parser.add_argument("--max-examples", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=320)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def _load_text(path: str | Path) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Missing file: {p}")
    return p.read_text(encoding="utf-8").strip()


def _load_records(args: argparse.Namespace) -> list[EvalRecord]:
    if args.input_jsonl:
        return load_records_from_jsonl(args.input_jsonl, max_examples=args.max_examples)
    return load_records_from_hf_dataset(
        args.dataset_path,
        args.dataset_split,
        max_examples=args.max_examples,
    )


def _evaluate_model(
    *,
    model_runner: LocalModelRunner,
    records: list[EvalRecord],
) -> tuple[list[ExampleResult], ModelMetricSummary]:
    results: list[ExampleResult] = []

    gold_scores: list[float] = []
    predicted_scores: list[float | None] = []
    quality_rows: list[FeedbackQualityResult] = []

    for record in records:
        output: ParsedModelOutput = model_runner.generate(record)
        quality = score_feedback_quality(output.feedback, record.essay)

        result = ExampleResult(
            id=record.example_id,
            split=record.split,
            gold_score=record.score,
            predicted_score=output.predicted_score,
            confidence=output.confidence,
            reasoning=output.reasoning,
            feedback=output.feedback,
            feedback_quality=quality.score,
            parse_error=output.parse_error,
        )
        results.append(result)

        gold_scores.append(record.score)
        predicted_scores.append(output.predicted_score)
        quality_rows.append(quality)

    summary = summarize_model_metrics(
        gold_scores=gold_scores,
        predicted_scores=predicted_scores,
        feedback_quality=quality_rows,
    )
    return results, summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _render_report(
    *,
    run_id: str,
    base_model_id: str,
    tuned_model_id: str,
    total_examples: int,
    base_summary: ModelMetricSummary,
    tuned_summary: ModelMetricSummary,
) -> str:
    deltas = {
        "score_accuracy": tuned_summary.score_accuracy - base_summary.score_accuracy,
        "quadratic_weighted_kappa": (
            tuned_summary.quadratic_weighted_kappa - base_summary.quadratic_weighted_kappa
        ),
        "mae": tuned_summary.mae - base_summary.mae,
        "feedback_quality": tuned_summary.feedback_quality - base_summary.feedback_quality,
    }

    def fmt(value: float) -> str:
        return f"{value:.6f}"

    lines = [
        "# Evaluation Harness Report",
        "",
        f"- run_id: `{run_id}`",
        f"- total_examples: `{total_examples}`",
        "",
        "## Model Metrics",
        "",
        "| model | score_accuracy | quadratic_weighted_kappa | MAE | feedback_quality | "
        "valid_score_predictions |",
        "|---|---:|---:|---:|---:|---:|",
        (
            f"| {base_model_id} | {fmt(base_summary.score_accuracy)} | "
            f"{fmt(base_summary.quadratic_weighted_kappa)} | {fmt(base_summary.mae)} | "
            f"{fmt(base_summary.feedback_quality)} | {base_summary.valid_score_predictions} |"
        ),
        (
            f"| {tuned_model_id} | {fmt(tuned_summary.score_accuracy)} | "
            f"{fmt(tuned_summary.quadratic_weighted_kappa)} | {fmt(tuned_summary.mae)} | "
            f"{fmt(tuned_summary.feedback_quality)} | {tuned_summary.valid_score_predictions} |"
        ),
        "",
        "## Tuned - Base Delta",
        "",
        f"- score_accuracy: `{fmt(deltas['score_accuracy'])}`",
        f"- quadratic_weighted_kappa: `{fmt(deltas['quadratic_weighted_kappa'])}`",
        f"- MAE: `{fmt(deltas['mae'])}` (negative is better)",
        f"- feedback_quality: `{fmt(deltas['feedback_quality'])}`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    """Run base-vs-tuned evaluation harness."""
    args = parse_args()

    records = _load_records(args)
    if not records:
        raise ValueError("No evaluation records found with prompt/essay/score fields.")

    prompt_template = _load_text(args.prompt_template_path)
    system_role = _load_text(args.system_role_path)

    run_id = datetime.now(timezone.utc).strftime("eval-%Y%m%dT%H%M%SZ")
    run_dir = Path(args.output_dir) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    base_runner = LocalModelRunner(
        model_id=args.base_model_id,
        system_role=system_role,
        prompt_template=prompt_template,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        local_files_only=args.local_files_only,
        dry_run=args.dry_run,
    )
    tuned_runner = LocalModelRunner(
        model_id=args.tuned_model_id,
        system_role=system_role,
        prompt_template=prompt_template,
        max_new_tokens=args.max_new_tokens,
        temperature=args.temperature,
        local_files_only=args.local_files_only,
        dry_run=args.dry_run,
    )

    base_rows, base_summary = _evaluate_model(model_runner=base_runner, records=records)
    tuned_rows, tuned_summary = _evaluate_model(model_runner=tuned_runner, records=records)

    base_path = run_dir / "base_predictions.jsonl"
    tuned_path = run_dir / "tuned_predictions.jsonl"
    summary_path = run_dir / "summary.json"
    report_path = run_dir / "report.md"

    _write_jsonl(base_path, [asdict(item) for item in base_rows])
    _write_jsonl(tuned_path, [asdict(item) for item in tuned_rows])

    summary_payload = {
        "run_id": run_id,
        "dataset_path": args.dataset_path,
        "dataset_split": args.dataset_split,
        "input_jsonl": args.input_jsonl,
        "total_examples": len(records),
        "base_model": {
            "model_id": args.base_model_id,
            **asdict(base_summary),
        },
        "tuned_model": {
            "model_id": args.tuned_model_id,
            **asdict(tuned_summary),
        },
        "comparison": {
            "score_accuracy_delta": tuned_summary.score_accuracy - base_summary.score_accuracy,
            "qwk_delta": (
                tuned_summary.quadratic_weighted_kappa - base_summary.quadratic_weighted_kappa
            ),
            "mae_delta": tuned_summary.mae - base_summary.mae,
            "feedback_quality_delta": (
                tuned_summary.feedback_quality - base_summary.feedback_quality
            ),
        },
        "artifacts": {
            "base_predictions": str(base_path),
            "tuned_predictions": str(tuned_path),
            "summary": str(summary_path),
            "report": str(report_path),
        },
    }

    summary_path.write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    report_path.write_text(
        _render_report(
            run_id=run_id,
            base_model_id=args.base_model_id,
            tuned_model_id=args.tuned_model_id,
            total_examples=len(records),
            base_summary=base_summary,
            tuned_summary=tuned_summary,
        ),
        encoding="utf-8",
    )

    print(json.dumps(summary_payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
