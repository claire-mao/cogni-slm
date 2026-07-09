"""Build a project experiment dashboard from existing artifacts.

This module summarizes:
- teacher experiments
- training runs
- evaluation metrics
- error analysis
- cost
- runtime

It does not execute experiments.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from utils.paths import repo_root


@dataclass(frozen=True)
class TeacherRunSummary:
    run_id: str
    round_id: str
    dry_run: bool
    model_count: int
    task_count: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_cost_usd: float
    avg_latency_ms: float | None
    duration_seconds: float | None


@dataclass(frozen=True)
class TrainingAggregate:
    plans_found: int
    runs_total: int
    runs_completed: int
    runs_failed: int
    runs_planned: int
    total_runtime_seconds: float


@dataclass(frozen=True)
class EvaluationRunSummary:
    run_id: str
    source: str
    total_examples: int
    base_model: str | None
    tuned_model: str | None
    base_qwk: float | None
    tuned_qwk: float | None
    qwk_delta: float | None
    mae_delta: float | None


@dataclass(frozen=True)
class ErrorAnalysisSummary:
    available: bool
    total_predictions: int
    matched_gold_examples: int
    unmatched_gold_examples: int
    model_count: int


@dataclass(frozen=True)
class DashboardPayload:
    generated_at_utc: str
    teacher_runs: tuple[TeacherRunSummary, ...]
    training: TrainingAggregate
    evaluations: tuple[EvaluationRunSummary, ...]
    error_analysis: ErrorAnalysisSummary
    teacher_leaderboard_top: tuple[dict[str, Any], ...]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    parsed = _safe_float(value)
    return int(parsed) if parsed is not None else default


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"Expected JSON object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _parse_iso_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _collect_teacher_runs(teacher_runs_root: Path) -> tuple[TeacherRunSummary, ...]:
    if not teacher_runs_root.exists() or not teacher_runs_root.is_dir():
        return ()

    summaries: list[TeacherRunSummary] = []
    for run_dir in sorted(teacher_runs_root.iterdir()):
        if not run_dir.is_dir():
            continue

        summary_path = run_dir / "summary.json"
        manifest_path = run_dir / "manifest.json"
        responses_path = run_dir / "responses.jsonl"

        if not summary_path.exists() and not responses_path.exists():
            continue

        summary: dict[str, Any] = _read_json(summary_path) if summary_path.exists() else {}
        manifest: dict[str, Any] = _read_json(manifest_path) if manifest_path.exists() else {}

        responses = _read_jsonl(responses_path) if responses_path.exists() else []
        costs = [
            value
            for value in (_safe_float(row.get("estimated_cost_usd")) for row in responses)
            if value is not None
        ]
        latencies = [
            value
            for value in (_safe_float(row.get("latency_ms")) for row in responses)
            if value is not None
        ]
        timestamps = [
            value
            for value in (_parse_iso_datetime(row.get("timestamp_utc")) for row in responses)
            if value is not None
        ]

        duration_seconds: float | None = None
        if len(timestamps) >= 2:
            duration_seconds = (max(timestamps) - min(timestamps)).total_seconds()

        run_id = str(summary.get("run_id") or manifest.get("run_id") or run_dir.name)
        summaries.append(
            TeacherRunSummary(
                run_id=run_id,
                round_id=str(summary.get("round_id") or manifest.get("round_id") or "unknown"),
                dry_run=bool(summary.get("dry_run") or manifest.get("dry_run")),
                model_count=_safe_int(
                    summary.get("model_count", len(manifest.get("model_ids", []))),
                    default=0,
                ),
                task_count=_safe_int(
                    summary.get("task_count", len(manifest.get("task_ids", []))),
                    default=0,
                ),
                total_requests=_safe_int(
                    summary.get("total_requests", len(responses)),
                    default=len(responses),
                ),
                successful_requests=_safe_int(
                    summary.get("successful_requests", len(responses)),
                    default=len(responses),
                ),
                failed_requests=_safe_int(summary.get("failed_requests", 0), default=0),
                total_cost_usd=sum(costs),
                avg_latency_ms=(mean(latencies) if latencies else None),
                duration_seconds=duration_seconds,
            )
        )

    return tuple(summaries)


def _collect_teacher_leaderboard_top(
    leaderboard_json_path: Path,
    *,
    limit: int = 5,
) -> tuple[dict[str, Any], ...]:
    if not leaderboard_json_path.exists():
        return ()
    payload = _read_json(leaderboard_json_path)
    rows: Any
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict):
        rows = payload.get("leaderboard")
    else:
        return ()
    if not isinstance(rows, list):
        return ()

    items: list[dict[str, Any]] = []
    for row in rows[:limit]:
        if isinstance(row, dict):
            items.append(row)
    return tuple(items)


def _collect_training_aggregate(
    training_experiments_root: Path,
    experiments_root: Path,
) -> TrainingAggregate:
    plans_found = 0
    runs_total = 0
    runs_completed = 0
    runs_failed = 0
    runs_planned = 0
    total_runtime_seconds = 0.0

    if training_experiments_root.exists() and training_experiments_root.is_dir():
        for summary_path in sorted(training_experiments_root.rglob("run_summary.json")):
            try:
                payload = _read_json(summary_path)
            except Exception:
                continue
            plans_found += 1
            runs_total += _safe_int(payload.get("runs_requested", 0), default=0)
            runs_completed += _safe_int(payload.get("runs_completed", 0), default=0)
            runs_failed += _safe_int(payload.get("runs_failed", 0), default=0)
            runs_planned += _safe_int(payload.get("runs_planned", 0), default=0)

            results = payload.get("results")
            if isinstance(results, list):
                for row in results:
                    if not isinstance(row, dict):
                        continue
                    duration = _safe_float(row.get("train_seconds"))
                    if duration is not None:
                        total_runtime_seconds += duration

    if experiments_root.exists() and experiments_root.is_dir():
        for manifest_path in sorted(experiments_root.rglob("manifest.json")):
            try:
                payload = _read_json(manifest_path)
            except Exception:
                continue
            runtime = payload.get("runtime")
            if isinstance(runtime, dict):
                duration = _safe_float(runtime.get("duration_seconds"))
                if duration is not None:
                    total_runtime_seconds += duration

    return TrainingAggregate(
        plans_found=plans_found,
        runs_total=runs_total,
        runs_completed=runs_completed,
        runs_failed=runs_failed,
        runs_planned=runs_planned,
        total_runtime_seconds=total_runtime_seconds,
    )


def _collect_evaluations(evaluation_roots: tuple[Path, ...]) -> tuple[EvaluationRunSummary, ...]:
    summaries: list[EvaluationRunSummary] = []
    seen: set[str] = set()

    for root in evaluation_roots:
        if root.is_file() and root.name == "summary.json":
            candidates = [root]
        elif root.exists() and root.is_dir():
            candidates = sorted(root.rglob("summary.json"))
        else:
            candidates = []

        for path in candidates:
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)

            try:
                payload = _read_json(path)
            except Exception:
                continue

            run_id = str(payload.get("run_id") or path.parent.name)
            total_examples = _safe_int(payload.get("total_examples", 0), default=0)

            base_model = payload.get("base_model")
            tuned_model = payload.get("tuned_model")
            comparison = payload.get("comparison")

            base_model_id = None
            tuned_model_id = None
            base_qwk = None
            tuned_qwk = None
            qwk_delta = None
            mae_delta = None

            if isinstance(base_model, dict):
                base_model_value = base_model.get("model_id")
                base_model_id = str(base_model_value) if base_model_value else None
                base_qwk = _safe_float(base_model.get("quadratic_weighted_kappa"))

            if isinstance(tuned_model, dict):
                tuned_model_id = (
                    str(tuned_model.get("model_id")) if tuned_model.get("model_id") else None
                )
                tuned_qwk = _safe_float(tuned_model.get("quadratic_weighted_kappa"))

            if isinstance(comparison, dict):
                qwk_delta = _safe_float(comparison.get("qwk_delta"))
                mae_delta = _safe_float(comparison.get("mae_delta"))

            # Baseline summary compatibility.
            metrics = payload.get("metrics")
            if isinstance(metrics, dict) and qwk_delta is None:
                qwk_delta = _safe_float(metrics.get("behavior_spec_adherence"))

            summaries.append(
                EvaluationRunSummary(
                    run_id=run_id,
                    source=str(path.parent),
                    total_examples=total_examples,
                    base_model=base_model_id,
                    tuned_model=tuned_model_id,
                    base_qwk=base_qwk,
                    tuned_qwk=tuned_qwk,
                    qwk_delta=qwk_delta,
                    mae_delta=mae_delta,
                )
            )

    summaries = sorted(summaries, key=lambda item: item.run_id, reverse=True)
    return tuple(summaries)


def _collect_error_analysis(error_analysis_root: Path) -> ErrorAnalysisSummary:
    summary_path = error_analysis_root / "error_analysis_summary.json"
    if not summary_path.exists():
        return ErrorAnalysisSummary(
            available=False,
            total_predictions=0,
            matched_gold_examples=0,
            unmatched_gold_examples=0,
            model_count=0,
        )

    payload = _read_json(summary_path)
    model_summaries = payload.get("model_summaries")
    model_count = len(model_summaries) if isinstance(model_summaries, list) else 0

    return ErrorAnalysisSummary(
        available=True,
        total_predictions=_safe_int(payload.get("total_predictions", 0), default=0),
        matched_gold_examples=_safe_int(payload.get("matched_gold_examples", 0), default=0),
        unmatched_gold_examples=_safe_int(payload.get("unmatched_gold_examples", 0), default=0),
        model_count=model_count,
    )


def build_dashboard_payload(
    *,
    teacher_runs_root: Path,
    leaderboard_json_path: Path,
    training_experiments_root: Path,
    experiments_root: Path,
    evaluation_roots: tuple[Path, ...],
    error_analysis_root: Path,
) -> DashboardPayload:
    teacher_runs = _collect_teacher_runs(teacher_runs_root)
    leaderboard_top = _collect_teacher_leaderboard_top(leaderboard_json_path)
    training = _collect_training_aggregate(training_experiments_root, experiments_root)
    evaluations = _collect_evaluations(evaluation_roots)
    error_analysis = _collect_error_analysis(error_analysis_root)

    return DashboardPayload(
        generated_at_utc=_utc_now(),
        teacher_runs=teacher_runs,
        training=training,
        evaluations=evaluations,
        error_analysis=error_analysis,
        teacher_leaderboard_top=leaderboard_top,
    )


def _fmt_float(value: float | None, *, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def _render_teacher_section(payload: DashboardPayload) -> list[str]:
    rows = [
        "## Teacher Experiments",
        "",
        f"- runs_found: `{len(payload.teacher_runs)}`",
    ]

    if not payload.teacher_runs:
        rows.extend(["- No teacher run artifacts found.", ""])
        return rows

    total_requests = sum(item.total_requests for item in payload.teacher_runs)
    total_successful = sum(item.successful_requests for item in payload.teacher_runs)
    total_failed = sum(item.failed_requests for item in payload.teacher_runs)
    total_cost = sum(item.total_cost_usd for item in payload.teacher_runs)
    duration_values = [
        item.duration_seconds for item in payload.teacher_runs if item.duration_seconds is not None
    ]

    rows.extend(
        [
            f"- total_requests: `{total_requests}`",
            f"- successful_requests: `{total_successful}`",
            f"- failed_requests: `{total_failed}`",
            f"- total_estimated_cost_usd: `{total_cost:.6f}`",
            (
                "- total_runtime_seconds: "
                + (
                    f"`{sum(duration_values):.2f}`"
                    if duration_values
                    else "`n/a`"
                )
            ),
            "",
            (
                "| run_id | round_id | dry_run | models | tasks | requests | "
                "avg_latency_ms | cost_usd |"
            ),
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for item in payload.teacher_runs:
        rows.append(
            "| "
            + " | ".join(
                [
                    item.run_id,
                    item.round_id,
                    "yes" if item.dry_run else "no",
                    str(item.model_count),
                    str(item.task_count),
                    str(item.total_requests),
                    _fmt_float(item.avg_latency_ms, digits=3),
                    f"{item.total_cost_usd:.6f}",
                ]
            )
            + " |"
        )

    rows.append("")
    return rows


def _render_training_section(payload: DashboardPayload) -> list[str]:
    training = payload.training
    rows = [
        "## Training Runs",
        "",
        f"- plans_found: `{training.plans_found}`",
        f"- runs_total: `{training.runs_total}`",
        f"- runs_completed: `{training.runs_completed}`",
        f"- runs_failed: `{training.runs_failed}`",
        f"- runs_planned: `{training.runs_planned}`",
        f"- total_runtime_seconds: `{training.total_runtime_seconds:.2f}`",
        "",
    ]
    return rows


def _render_evaluation_section(payload: DashboardPayload) -> list[str]:
    rows = [
        "## Evaluation Metrics",
        "",
        f"- evaluation_runs_found: `{len(payload.evaluations)}`",
    ]

    if not payload.evaluations:
        rows.extend(["- No evaluation summary artifacts found.", ""])
        return rows

    rows.extend(
        [
            "",
            (
                "| run_id | total_examples | base_model | tuned_model | base_qwk | "
                "tuned_qwk | qwk_delta | mae_delta |"
            ),
            "|---|---:|---|---|---:|---:|---:|---:|",
        ]
    )

    for item in payload.evaluations[:20]:
        rows.append(
            "| "
            + " | ".join(
                [
                    item.run_id,
                    str(item.total_examples),
                    item.base_model or "n/a",
                    item.tuned_model or "n/a",
                    _fmt_float(item.base_qwk),
                    _fmt_float(item.tuned_qwk),
                    _fmt_float(item.qwk_delta),
                    _fmt_float(item.mae_delta),
                ]
            )
            + " |"
        )

    rows.append("")
    return rows


def _render_error_analysis_section(payload: DashboardPayload) -> list[str]:
    item = payload.error_analysis
    rows = ["## Error Analysis", ""]

    if not item.available:
        rows.extend(["- available: `false`", "- No error analysis summary found.", ""])
        return rows

    rows.extend(
        [
            "- available: `true`",
            f"- total_predictions: `{item.total_predictions}`",
            f"- matched_gold_examples: `{item.matched_gold_examples}`",
            f"- unmatched_gold_examples: `{item.unmatched_gold_examples}`",
            f"- model_count: `{item.model_count}`",
            "",
        ]
    )
    return rows


def _render_cost_runtime_section(payload: DashboardPayload) -> list[str]:
    teacher_cost = sum(item.total_cost_usd for item in payload.teacher_runs)
    teacher_runtime_values = [
        item.duration_seconds for item in payload.teacher_runs if item.duration_seconds is not None
    ]
    teacher_runtime = sum(teacher_runtime_values) if teacher_runtime_values else None

    training_runtime = payload.training.total_runtime_seconds
    combined_runtime = (teacher_runtime or 0.0) + training_runtime

    rows = [
        "## Cost and Runtime",
        "",
        f"- teacher_cost_usd: `{teacher_cost:.6f}`",
        (
            "- teacher_runtime_seconds: "
            + (f"`{teacher_runtime:.2f}`" if teacher_runtime is not None else "`n/a`")
        ),
        f"- training_runtime_seconds: `{training_runtime:.2f}`",
        f"- combined_runtime_seconds: `{combined_runtime:.2f}`",
        "",
    ]
    return rows


def _render_leaderboard_section(payload: DashboardPayload) -> list[str]:
    rows = [
        "## Teacher Leaderboard Snapshot",
        "",
        f"- models_listed: `{len(payload.teacher_leaderboard_top)}`",
    ]

    if not payload.teacher_leaderboard_top:
        rows.extend(["- No leaderboard snapshot found.", ""])
        return rows

    rows.extend(
        [
            "",
            "| rank | model | qwk | mae | json_validity | latency_ms | cost_usd | rank_score |",
            "|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for row in payload.teacher_leaderboard_top:
        model_name = row.get("model") or row.get("model_id") or "n/a"
        qwk = _safe_float(row.get("qwk"))
        if qwk is None:
            qwk = _safe_float(row.get("score_prediction_qwk"))
        mae = _safe_float(row.get("mae"))
        if mae is None:
            mae = _safe_float(row.get("score_prediction_mae"))
        latency_ms = _safe_float(row.get("latency_ms"))
        if latency_ms is None:
            latency_ms = _safe_float(row.get("avg_latency_ms"))
        cost_usd = _safe_float(row.get("cost_usd"))
        if cost_usd is None:
            cost_usd = _safe_float(row.get("cost_total_usd"))
        rows.append(
            "| "
            + " | ".join(
                [
                    str(_safe_int(row.get("rank"), default=0)),
                    str(model_name),
                    _fmt_float(qwk),
                    _fmt_float(mae),
                    _fmt_float(_safe_float(row.get("json_validity"))),
                    _fmt_float(latency_ms),
                    _fmt_float(cost_usd, digits=6),
                    _fmt_float(_safe_float(row.get("rank_score"))),
                ]
            )
            + " |"
        )

    rows.append("")
    return rows


def render_dashboard_markdown(payload: DashboardPayload) -> str:
    lines = [
        "# Experiment Dashboard",
        "",
        f"- generated_at_utc: `{payload.generated_at_utc}`",
        "",
    ]

    lines.extend(_render_teacher_section(payload))
    lines.extend(_render_training_section(payload))
    lines.extend(_render_evaluation_section(payload))
    lines.extend(_render_error_analysis_section(payload))
    lines.extend(_render_cost_runtime_section(payload))
    lines.extend(_render_leaderboard_section(payload))

    lines.extend(
        [
            "## Notes",
            "",
            "- This dashboard summarizes existing artifacts only.",
            "- No experiments or training jobs were executed by this report builder.",
            "",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def write_dashboard_report(report_path: Path, markdown: str) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(markdown, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build project experiment dashboard report.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--teacher-runs-root", default="outputs/teacher_runs")
    parser.add_argument(
        "--teacher-leaderboard-json",
        default="docs/reports/teacher_leaderboard.json",
    )
    parser.add_argument("--training-experiments-root", default="outputs/training_experiments")
    parser.add_argument("--experiments-root", default="outputs/experiments")
    parser.add_argument("--evaluation-root", action="append", default=[])
    parser.add_argument("--error-analysis-root", default="outputs/error_analysis")
    parser.add_argument("--report-path", default="docs/reports/dashboard.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = repo_root(args.repo_root) if args.repo_root else repo_root()

    evaluation_roots = tuple(
        [
            root / "outputs" / "evaluation" / "harness",
            root / "outputs" / "evaluation_harness",
            root / "outputs" / "baseline" / "summary.json",
        ]
        + [
            Path(path) if Path(path).is_absolute() else (root / path)
            for path in args.evaluation_root
        ]
    )

    payload = build_dashboard_payload(
        teacher_runs_root=(
            Path(args.teacher_runs_root)
            if Path(args.teacher_runs_root).is_absolute()
            else (root / args.teacher_runs_root)
        ),
        leaderboard_json_path=(
            Path(args.teacher_leaderboard_json)
            if Path(args.teacher_leaderboard_json).is_absolute()
            else (root / args.teacher_leaderboard_json)
        ),
        training_experiments_root=(
            Path(args.training_experiments_root)
            if Path(args.training_experiments_root).is_absolute()
            else (root / args.training_experiments_root)
        ),
        experiments_root=(
            Path(args.experiments_root)
            if Path(args.experiments_root).is_absolute()
            else (root / args.experiments_root)
        ),
        evaluation_roots=evaluation_roots,
        error_analysis_root=(
            Path(args.error_analysis_root)
            if Path(args.error_analysis_root).is_absolute()
            else (root / args.error_analysis_root)
        ),
    )

    markdown = render_dashboard_markdown(payload)
    report_path = (
        Path(args.report_path)
        if Path(args.report_path).is_absolute()
        else (root / args.report_path)
    )
    write_dashboard_report(report_path, markdown)

    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "teacher_runs": len(payload.teacher_runs),
                "training_plans": payload.training.plans_found,
                "evaluation_runs": len(payload.evaluations),
                "error_analysis_available": payload.error_analysis.available,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
