"""Build prioritized human-review queues from teacher benchmark outputs.

Priority signals:
- low confidence
- teacher disagreement
- hallucination flags
- score uncertainty
- reasoning variance
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from src.teacher.io import GoldExample, PredictionRecord, load_gold_examples
from src.teacher.validation import validate_prediction


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


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


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _stddev(values: list[float]) -> float:
    if len(values) <= 1:
        return 0.0
    avg = mean(values)
    return math.sqrt(sum((value - avg) ** 2 for value in values) / len(values))


def _normalize_confidence(raw: Any) -> float | None:
    parsed = _safe_float(raw)
    if parsed is None:
        return None
    if parsed > 1.0:
        parsed = parsed / 100.0
    return max(0.0, min(1.0, parsed))


def _primary_fallacy(output_obj: dict[str, Any]) -> str:
    fallacies = output_obj.get("fallacy_detection")
    if isinstance(fallacies, dict):
        value = fallacies.get("primary")
        if isinstance(value, str):
            return value.strip().lower()

    fallacies = output_obj.get("fallacies")
    if isinstance(fallacies, dict):
        value = fallacies.get("primary")
        if isinstance(value, str):
            return value.strip().lower()
    return ""


def _rubric_signature(output_obj: dict[str, Any]) -> tuple[str, ...]:
    rubric = output_obj.get("rubric")
    if isinstance(rubric, dict):
        criteria = rubric.get("criteria")
        if isinstance(criteria, list):
            labels: list[str] = []
            for row in criteria:
                if not isinstance(row, dict):
                    continue
                label = _normalize_text(row.get("criterion")).lower()
                if label:
                    labels.append(label)
            if labels:
                return tuple(sorted(labels))
    return ()


def _reasoning_signature(output_obj: dict[str, Any]) -> str:
    reasoning = output_obj.get("reasoning")
    if isinstance(reasoning, dict):
        summary = _normalize_text(reasoning.get("summary"))
        if summary:
            return summary.lower()
    return _normalize_text(reasoning).lower()


@dataclass(frozen=True)
class QueueConfig:
    min_priority_score: float
    max_queue_size: int
    per_example_cap: int
    per_task_cap: int


def _case_id(
    *,
    run_id: str,
    task_id: str,
    example_id: str,
    seed: int,
    temperature: float,
    prompt_version: str,
) -> str:
    hash_key = "|".join(
        [
            run_id,
            task_id,
            example_id,
            str(seed),
            f"{temperature:.4f}",
            prompt_version,
        ]
    )
    return hashlib.sha1(hash_key.encode("utf-8")).hexdigest()[:16]


def _prediction_for_validation(row: dict[str, Any], output_obj: dict[str, Any]) -> PredictionRecord:
    model = _normalize_text(row.get("model")) or "unknown"
    example_id = _normalize_text(row.get("example_id"))
    raw_payload = {
        "output": output_obj,
        "response_text": json.dumps(output_obj, ensure_ascii=False),
    }

    feedback = output_obj.get("feedback")
    if isinstance(feedback, dict):
        text_parts = []
        strengths = feedback.get("strengths")
        if isinstance(strengths, list):
            text_parts.extend(_normalize_text(item) for item in strengths)
        priorities = feedback.get("priorities")
        if isinstance(priorities, list):
            text_parts.extend(_normalize_text(item) for item in priorities)
        summary = feedback.get("student_facing_summary")
        if isinstance(summary, str):
            text_parts.append(_normalize_text(summary))
        feedback_text = " ".join(item for item in text_parts if item)
    else:
        feedback_text = _normalize_text(feedback)

    score_raw = output_obj.get("score")
    score = _safe_float(score_raw)

    fallacies = output_obj.get("fallacies")
    predicted_fallacies: tuple[str, ...] = ()
    if isinstance(fallacies, dict):
        labels: list[str] = []
        primary = _normalize_text(fallacies.get("primary"))
        if primary:
            labels.append(primary)
        secondary = fallacies.get("secondary")
        if isinstance(secondary, list):
            labels.extend(_normalize_text(item) for item in secondary if _normalize_text(item))
        predicted_fallacies = tuple(labels)

    return PredictionRecord(
        model_id=model,
        example_id=example_id,
        predicted_score=score,
        rubric_items=tuple(),
        rubric_score=None,
        reasoning_skills=tuple(),
        reasoning_score=None,
        argument_quality_score=None,
        predicted_fallacies=predicted_fallacies,
        feedback_text=feedback_text,
        json_valid=True,
        latency_ms=_safe_float(row.get("latency_ms")),
        input_tokens=_safe_int(row.get("input_tokens"), default=0),
        output_tokens=_safe_int(row.get("output_tokens"), default=0),
        cost_usd=_safe_float(row.get("estimated_cost_usd")),
        raw_payload=raw_payload,
    )


def _priority_components(
    *,
    confidences: list[float],
    scores: list[float],
    fallacy_labels: list[str],
    rubric_signatures: list[tuple[str, ...]],
    reasoning_signatures: list[str],
    hallucination_rate: float,
) -> dict[str, float]:
    mean_confidence = mean(confidences) if confidences else 0.0
    low_confidence = max(0.0, min(1.0, (0.75 - mean_confidence) / 0.75))

    score_std = _stddev(scores) if scores else 0.0
    score_uncertainty = max(0.0, min(1.0, score_std / 6.0))

    fallacy_disagreement = 0.0
    if fallacy_labels:
        unique = len(set(fallacy_labels))
        fallacy_disagreement = (unique - 1) / max(1, len(fallacy_labels) - 1)

    rubric_disagreement = 0.0
    if rubric_signatures:
        unique = len(set(rubric_signatures))
        rubric_disagreement = (unique - 1) / max(1, len(rubric_signatures) - 1)

    disagreement = mean([score_uncertainty, fallacy_disagreement, rubric_disagreement])

    reasoning_variance = 0.0
    non_empty_reasoning = [value for value in reasoning_signatures if value]
    if non_empty_reasoning:
        unique = len(set(non_empty_reasoning))
        reasoning_variance = (unique - 1) / max(1, len(non_empty_reasoning) - 1)

    return {
        "low_confidence": low_confidence,
        "teacher_disagreement": disagreement,
        "hallucination_flags": max(0.0, min(1.0, hallucination_rate)),
        "score_uncertainty": score_uncertainty,
        "reasoning_variance": reasoning_variance,
    }


def build_review_queue(
    *,
    outputs_path: Path,
    gold_path: Path,
    output_dir: Path,
    config: QueueConfig,
) -> dict[str, Any]:
    rows = _read_jsonl(outputs_path)
    gold_rows = load_gold_examples(gold_path)
    gold_index: dict[str, GoldExample] = {row.example_id: row for row in gold_rows}

    grouped: dict[tuple[str, str, str, int, float, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        run_id = _normalize_text(row.get("run_id")) or "unknown_run"
        task_id = _normalize_text(row.get("task_id")) or "unknown_task"
        example_id = _normalize_text(row.get("example_id")) or "unknown_example"
        seed = _safe_int(row.get("seed"), default=0)
        temperature = float(_safe_float(row.get("temperature")) or 0.0)
        prompt_version = _normalize_text(row.get("prompt_version")) or "unknown"
        grouped[(run_id, task_id, example_id, seed, temperature, prompt_version)].append(row)

    scored_rows: list[dict[str, Any]] = []
    for key, group_rows in grouped.items():
        run_id, task_id, example_id, seed, temperature, prompt_version = key
        case_id = _case_id(
            run_id=run_id,
            task_id=task_id,
            example_id=example_id,
            seed=seed,
            temperature=temperature,
            prompt_version=prompt_version,
        )
        gold = gold_index.get(example_id)

        confidences: list[float] = []
        scores: list[float] = []
        fallacy_labels: list[str] = []
        rubric_signatures: list[tuple[str, ...]] = []
        reasoning_signatures: list[str] = []
        hallucination_flags = 0
        invalid_flags = 0
        model_summaries: list[dict[str, Any]] = []

        for row in sorted(group_rows, key=lambda item: _normalize_text(item.get("model"))):
            output_obj = row.get("raw_json_output")
            if not isinstance(output_obj, dict):
                invalid_flags += 1
                continue

            confidence = _normalize_confidence(output_obj.get("confidence"))
            if confidence is not None:
                confidences.append(confidence)

            score = _safe_float(output_obj.get("score"))
            if score is not None:
                scores.append(score)

            fallacy_labels.append(_primary_fallacy(output_obj))
            rubric_signatures.append(_rubric_signature(output_obj))
            reasoning_signatures.append(_reasoning_signature(output_obj))

            prediction = _prediction_for_validation(row, output_obj)
            result = validate_prediction(prediction, gold=gold)
            has_hallucination_flag = (
                result.unsupported_feedback
                or bool(result.hallucinated_rubric_items)
                or not result.json_validity
            )
            if has_hallucination_flag:
                hallucination_flags += 1

            model_summaries.append(
                {
                    "model": _normalize_text(row.get("model")) or "unknown",
                    "score": score,
                    "confidence": confidence,
                    "fallacy_primary": _primary_fallacy(output_obj),
                    "hallucination_flag": has_hallucination_flag,
                    "json_validity": result.json_validity,
                }
            )

        total_outputs = len(group_rows)
        hallucination_rate = hallucination_flags / total_outputs if total_outputs else 0.0
        invalid_rate = invalid_flags / total_outputs if total_outputs else 0.0
        components = _priority_components(
            confidences=confidences,
            scores=scores,
            fallacy_labels=fallacy_labels,
            rubric_signatures=rubric_signatures,
            reasoning_signatures=reasoning_signatures,
            hallucination_rate=hallucination_rate,
        )
        if gold:
            essay_excerpt = gold.essay if len(gold.essay) <= 600 else f"{gold.essay[:600]}..."
        else:
            essay_excerpt = ""
        non_empty_reasoning = [value for value in reasoning_signatures if value]
        reasoning_unique_ratio = (
            len(set(non_empty_reasoning)) / len(non_empty_reasoning) if non_empty_reasoning else 0.0
        )

        priority_score = (
            0.30 * components["low_confidence"]
            + 0.25 * components["teacher_disagreement"]
            + 0.20 * components["hallucination_flags"]
            + 0.15 * components["score_uncertainty"]
            + 0.10 * components["reasoning_variance"]
        )
        priority_score = max(0.0, min(1.0, priority_score))

        reasons: list[str] = []
        if components["low_confidence"] >= 0.25:
            reasons.append("low_confidence")
        if components["teacher_disagreement"] >= 0.25:
            reasons.append("teacher_disagreement")
        if components["hallucination_flags"] > 0.0:
            reasons.append("hallucination_flags")
        if components["score_uncertainty"] >= 0.20:
            reasons.append("score_uncertainty")
        if components["reasoning_variance"] >= 0.25:
            reasons.append("reasoning_variance")
        if invalid_rate > 0.0:
            reasons.append("invalid_outputs")

        requires_review = bool(reasons) or priority_score >= config.min_priority_score
        scored_rows.append(
            {
                "case_id": case_id,
                "run_id": run_id,
                "task_id": task_id,
                "example_id": example_id,
                "seed": seed,
                "temperature": temperature,
                "prompt_version": prompt_version,
                "source": gold.source if gold else "unknown",
                "difficulty": gold.difficulty if gold else "unknown",
                "prompt": gold.prompt if gold else "",
                "essay_excerpt": essay_excerpt,
                "teacher_count": total_outputs,
                "priority_score": priority_score,
                "requires_review": requires_review,
                "priority_reasons": reasons,
                "priority_components": components,
                "metrics": {
                    "mean_confidence": (mean(confidences) if confidences else None),
                    "min_confidence": (min(confidences) if confidences else None),
                    "max_confidence": (max(confidences) if confidences else None),
                    "score_mean": (mean(scores) if scores else None),
                    "score_stddev": _stddev(scores) if scores else 0.0,
                    "score_min": (min(scores) if scores else None),
                    "score_max": (max(scores) if scores else None),
                    "hallucination_rate": hallucination_rate,
                    "invalid_output_rate": invalid_rate,
                    "reasoning_unique_ratio": reasoning_unique_ratio,
                },
                "teacher_summaries": model_summaries,
            }
        )

    scored_rows.sort(
        key=lambda row: (
            -float(row["priority_score"]),
            row["example_id"],
            row["task_id"],
            int(row["seed"]),
        )
    )

    candidates = [row for row in scored_rows if row["requires_review"]]

    selected: list[dict[str, Any]] = []
    per_example_counts: dict[str, int] = defaultdict(int)
    per_task_counts: dict[str, int] = defaultdict(int)

    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_task[str(row.get("task_id") or "unknown")].append(row)

    task_ids = sorted(by_task.keys())
    task_pointers: dict[str, int] = {task_id: 0 for task_id in task_ids}

    while True:
        if config.max_queue_size > 0 and len(selected) >= config.max_queue_size:
            break
        progressed = False
        for task_id in task_ids:
            if config.max_queue_size > 0 and len(selected) >= config.max_queue_size:
                break

            if config.per_task_cap > 0 and per_task_counts[task_id] >= config.per_task_cap:
                continue

            bucket = by_task[task_id]
            pointer = task_pointers[task_id]
            chosen: dict[str, Any] | None = None
            while pointer < len(bucket):
                row = bucket[pointer]
                pointer += 1
                example_id = str(row.get("example_id") or "")
                if (
                    config.per_example_cap > 0
                    and per_example_counts[example_id] >= config.per_example_cap
                ):
                    continue
                chosen = row
                break
            task_pointers[task_id] = pointer
            if chosen is None:
                continue

            selected.append(chosen)
            per_example_counts[str(chosen.get("example_id") or "")] += 1
            per_task_counts[task_id] += 1
            progressed = True
        if not progressed:
            break

    for rank, row in enumerate(selected, start=1):
        row["priority_rank"] = rank

    output_dir.mkdir(parents=True, exist_ok=True)
    queue_all_path = output_dir / "queue_all_scored.jsonl"
    queue_path = output_dir / "review_queue.jsonl"
    manifest_path = output_dir / "manifest.json"
    summary_path = output_dir / "summary.md"

    _write_jsonl(queue_all_path, scored_rows)
    _write_jsonl(queue_path, selected)

    reason_counts: dict[str, int] = defaultdict(int)
    for row in selected:
        for reason in row["priority_reasons"]:
            reason_counts[reason] += 1

    manifest = {
        "generated_at_utc": _utc_now(),
        "inputs": {
            "teacher_outputs_path": str(outputs_path),
            "gold_path": str(gold_path),
        },
        "config": {
            "min_priority_score": config.min_priority_score,
            "max_queue_size": config.max_queue_size,
            "per_example_cap": config.per_example_cap,
            "per_task_cap": config.per_task_cap,
        },
        "counts": {
            "cases_scored": len(scored_rows),
            "cases_candidate": len(candidates),
            "cases_selected": len(selected),
            "examples_selected": len(per_example_counts),
            "tasks_selected": len([key for key, value in per_task_counts.items() if value > 0]),
        },
        "priority_reason_counts": dict(sorted(reason_counts.items())),
        "outputs": {
            "queue_all_scored": str(queue_all_path),
            "review_queue": str(queue_path),
            "summary": str(summary_path),
        },
    }
    _write_json(manifest_path, manifest)

    summary_lines = [
        "# Review Queue Summary",
        "",
        f"- generated_at_utc: `{manifest['generated_at_utc']}`",
        f"- teacher_outputs_path: `{outputs_path}`",
        f"- gold_path: `{gold_path}`",
        f"- cases_scored: `{len(scored_rows)}`",
        f"- cases_selected: `{len(selected)}`",
        f"- min_priority_score: `{config.min_priority_score:.3f}`",
        f"- max_queue_size: `{config.max_queue_size}`",
        f"- per_example_cap: `{config.per_example_cap}`",
        f"- per_task_cap: `{config.per_task_cap}`",
        "",
        "## Priority Reasons",
        "",
    ]
    if reason_counts:
        for reason, count in sorted(reason_counts.items()):
            summary_lines.append(f"- `{reason}`: `{count}`")
    else:
        summary_lines.append("- none")

    summary_lines.extend(
        [
            "",
            "## Top 20 Queue Cases",
            "",
            "| rank | case_id | example_id | task_id | priority_score | reasons |",
            "|---:|---|---|---|---:|---|",
        ]
    )
    for row in selected[:20]:
        summary_lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("priority_rank", "")),
                    str(row.get("case_id", "")),
                    str(row.get("example_id", "")),
                    str(row.get("task_id", "")),
                    f"{float(row.get('priority_score', 0.0)):.4f}",
                    ", ".join(row.get("priority_reasons", [])),
                ]
            )
            + " |"
        )
    summary_lines.append("")
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build prioritized human review queue.")
    parser.add_argument(
        "--teacher-outputs",
        default="outputs/teacher_runs/production_labeling_v1/responses.jsonl",
    )
    parser.add_argument(
        "--gold-path",
        default="datasets/final/merged_all.jsonl",
    )
    parser.add_argument("--output-dir", default="datasets/review/queue")
    parser.add_argument("--min-priority-score", type=float, default=0.35)
    parser.add_argument("--max-queue-size", type=int, default=300)
    parser.add_argument("--per-example-cap", type=int, default=12)
    parser.add_argument("--per-task-cap", type=int, default=80)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_review_queue(
        outputs_path=Path(args.teacher_outputs),
        gold_path=Path(args.gold_path),
        output_dir=Path(args.output_dir),
        config=QueueConfig(
            min_priority_score=float(args.min_priority_score),
            max_queue_size=max(0, int(args.max_queue_size)),
            per_example_cap=max(0, int(args.per_example_cap)),
            per_task_cap=max(0, int(args.per_task_cap)),
        ),
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
