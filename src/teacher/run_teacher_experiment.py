"""Run one teacher experiment end-to-end with tracking and validation.

Inputs:
- dataset
- teacher model
- prompt version
- task suite

Automatically:
- run teacher provider
- store outputs
- validate outputs
- track cost
- track latency
- track confidence
- track experiment metadata via src.utils.experiment_tracker

This runner does not generate production labels.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from utils.experiment_tracker import ExperimentTracker

from .io import GoldExample, PredictionRecord, load_gold_examples
from .models import canonical_model_id, estimate_cost_usd
from .prompt_registry import PromptRegistry
from .provider_config import validate_provider_configuration
from .providers import TeacherExample, create_teacher_provider
from .validation import ExampleValidationResult, validate_prediction


@dataclass(frozen=True)
class TaskSpec:
    """One teacher task from task suite config."""

    task_id: str
    description: str
    required_output_fields: tuple[str, ...]
    scoring_mode: str


@dataclass(frozen=True)
class DatasetExample:
    """Minimal runtime dataset row for teacher generation."""

    example_id: str
    prompt: str
    essay: str
    score: float | None
    source: str
    difficulty: str
    raw: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("teacher-exp-%Y%m%dT%H%M%SZ")


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


def _is_simulated_example(row: dict[str, Any]) -> bool:
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    context = row.get("context") if isinstance(row.get("context"), dict) else {}
    source_id = _normalize_text(row.get("source_id")).lower()
    dataset_version = _normalize_text(row.get("dataset_version")).lower()
    example_id = _normalize_text(row.get("example_id") or row.get("id")).lower()
    return (
        metadata.get("placeholder") is True
        or context.get("placeholder") is True
        or source_id.startswith("placeholder::synthetic")
        or "placeholder" in dataset_version
        or example_id.startswith("heldout-placeholder-")
    )


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


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


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _parse_dataset_examples(path: Path) -> tuple[DatasetExample, ...]:
    rows = _read_jsonl(path)
    items: list[DatasetExample] = []
    for index, row in enumerate(rows, start=1):
        if _is_simulated_example(row):
            raise ValueError(
                "Simulated/placeholder dataset row detected at "
                f"{path}:{index}. Provide real reviewed examples."
            )
        example_id = _normalize_text(row.get("example_id") or row.get("id"))
        if not example_id:
            example_id = f"example-{index:06d}"

        prompt = _normalize_text(row.get("prompt") or row.get("prompt_text"))
        essay = _normalize_text(
            row.get("essay") or row.get("essay_text") or row.get("text") or row.get("input")
        )
        if not prompt or not essay:
            continue

        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        source = _normalize_text(row.get("source") or metadata.get("source")) or "unknown"
        difficulty = (
            _normalize_text(row.get("difficulty") or metadata.get("difficulty")) or "unknown"
        )
        score = _safe_float(row.get("gold_score", row.get("score")))

        items.append(
            DatasetExample(
                example_id=example_id,
                prompt=prompt,
                essay=essay,
                score=score,
                source=source,
                difficulty=difficulty,
                raw=row,
            )
        )
    return tuple(items)


def _load_task_suite(path: Path) -> tuple[TaskSpec, ...]:
    payload = _read_json(path)
    task_rows = payload.get("tasks")
    if not isinstance(task_rows, list):
        raise ValueError(f"Task suite missing tasks list: {path}")

    tasks: list[TaskSpec] = []
    for row in task_rows:
        if not isinstance(row, dict):
            continue
        task_id = row.get("task_id")
        description = row.get("description")
        fields = row.get("required_output_fields")
        scoring_mode = row.get("scoring_mode")
        if not isinstance(task_id, str) or not isinstance(description, str):
            continue
        if not isinstance(fields, list):
            fields = []
        if not isinstance(scoring_mode, str):
            scoring_mode = "unknown"

        tasks.append(
            TaskSpec(
                task_id=task_id,
                description=description,
                required_output_fields=tuple(str(item) for item in fields),
                scoring_mode=scoring_mode,
            )
        )

    if not tasks:
        raise ValueError(f"No valid tasks found in suite: {path}")
    return tuple(tasks)


def _infer_provider_from_model(teacher_model: str) -> str:
    value = teacher_model.lower()
    if "claude" in value:
        return "anthropic"
    if "gemini" in value:
        return "gemini"
    if "deepseek" in value:
        return "deepseek"
    if "openrouter" in value:
        return "openrouter"
    if "local" in value or "transformers" in value or "hf:" in value:
        return "local_transformers"
    return "openai"


def _resolve_provider_and_model(
    *,
    provider: str | None,
    teacher_model: str,
) -> tuple[str, str]:
    raw = teacher_model.strip()
    if not raw:
        raise ValueError("teacher_model is required")

    if ":" in raw:
        maybe_provider, maybe_model = raw.split(":", maxsplit=1)
        left = maybe_provider.strip().lower()
        right = maybe_model.strip()
        known = {
            "openai",
            "anthropic",
            "gemini",
            "deepseek",
            "openrouter",
            "openrouter_compatible",
            "local",
            "local_transformers",
            "transformers",
        }
        if left in known and right:
            return left, right

    resolved_provider = provider.strip().lower() if provider else _infer_provider_from_model(raw)
    return resolved_provider, raw


def _canonical_model_or_none(teacher_model: str) -> str | None:
    try:
        return canonical_model_id(teacher_model)
    except Exception:
        return None


def _estimate_call_cost(
    *,
    teacher_model: str,
    output: dict[str, Any],
) -> float | None:
    metadata = output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
    explicit = _safe_float(metadata.get("estimated_cost_usd") or metadata.get("cost_usd"))
    if explicit is not None:
        return explicit

    canonical = _canonical_model_or_none(teacher_model)
    if canonical is None:
        return None

    input_tokens = _safe_int(metadata.get("input_tokens"), default=0)
    output_tokens = _safe_int(metadata.get("output_tokens"), default=0)
    return estimate_cost_usd(canonical, input_tokens, output_tokens)


def _structured_output(output: dict[str, Any]) -> dict[str, Any] | None:
    metadata = output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
    raw = metadata.get("raw_json_output")
    if isinstance(raw, dict):
        return raw
    return None


def _extract_rubric_items(output_obj: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(output_obj, dict):
        return tuple()
    rubric = output_obj.get("rubric")
    if not isinstance(rubric, dict):
        return tuple()
    criteria = rubric.get("criteria")
    if not isinstance(criteria, list):
        return tuple()
    labels: list[str] = []
    for row in criteria:
        if not isinstance(row, dict):
            continue
        criterion = row.get("criterion")
        if isinstance(criterion, str) and criterion.strip():
            labels.append(criterion.strip().lower())
    return tuple(dict.fromkeys(labels))


def _extract_fallacies(output_obj: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(output_obj, dict):
        return tuple()
    fallacies = output_obj.get("fallacies")
    if not isinstance(fallacies, dict):
        return tuple()
    labels: list[str] = []
    primary = fallacies.get("primary")
    if isinstance(primary, str) and primary.strip():
        labels.append(primary.strip().lower())
    secondary = fallacies.get("secondary")
    if isinstance(secondary, list):
        for row in secondary:
            if isinstance(row, str) and row.strip():
                labels.append(row.strip().lower())
    return tuple(dict.fromkeys(labels))


def _extract_feedback_text(output: dict[str, Any], output_obj: dict[str, Any] | None) -> str:
    if isinstance(output_obj, dict):
        feedback = output_obj.get("feedback")
        if isinstance(feedback, dict):
            summary = feedback.get("student_facing_summary")
            if isinstance(summary, str) and summary.strip():
                return summary.strip()
        if isinstance(feedback, str) and feedback.strip():
            return feedback.strip()
    return _normalize_text(output.get("feedback"))


def _to_prediction_record(
    *,
    teacher_model: str,
    example: DatasetExample,
    output: dict[str, Any],
    cost_usd: float | None,
) -> PredictionRecord:
    metadata = output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
    output_obj = _structured_output(output)
    parse_error = metadata.get("parse_error")

    return PredictionRecord(
        model_id=_canonical_model_or_none(teacher_model) or teacher_model,
        example_id=example.example_id,
        predicted_score=_safe_float(output.get("score")),
        rubric_items=_extract_rubric_items(output_obj),
        rubric_score=None,
        reasoning_skills=tuple(),
        reasoning_score=None,
        argument_quality_score=None,
        predicted_fallacies=_extract_fallacies(output_obj),
        feedback_text=_extract_feedback_text(output, output_obj),
        json_valid=parse_error in (None, "") and isinstance(output_obj, dict),
        latency_ms=_safe_float(metadata.get("latency_ms")),
        input_tokens=_safe_int(metadata.get("input_tokens"), default=0),
        output_tokens=_safe_int(metadata.get("output_tokens"), default=0),
        cost_usd=cost_usd,
        raw_payload={
            "output": output_obj if isinstance(output_obj, dict) else {},
            "response_text": metadata.get("raw_response_text"),
            "raw_json_output": output_obj,
            "provider_normalized_output": output,
        },
    )


def _validation_to_json(result: ExampleValidationResult) -> dict[str, Any]:
    return {
        "model_id": result.model_id,
        "example_id": result.example_id,
        "json_validity": result.json_validity,
        "missing_fields": list(result.missing_fields),
        "score_range_valid": result.score_range_valid,
        "hallucinated_rubric_items": list(result.hallucinated_rubric_items),
        "unsupported_feedback": result.unsupported_feedback,
        "reasoning_completeness": result.reasoning_completeness,
        "confidence": result.confidence,
        "calibration_target": result.calibration_target,
        "calibration_brier": result.calibration_brier,
        "findings": [
            {
                "check_id": finding.check_id,
                "passed": finding.passed,
                "message": finding.message,
                "severity": finding.severity,
                "metadata": finding.metadata,
            }
            for finding in result.findings
        ],
    }


def _load_gold_index(path: Path) -> dict[str, GoldExample]:
    try:
        examples = load_gold_examples(path)
    except Exception:
        return {}
    return {item.example_id: item for item in examples}


def run_teacher_experiment(
    *,
    dataset_path: Path,
    teacher_model: str,
    provider: str | None,
    prompt_id: str,
    prompt_version: str,
    task_suite_path: Path,
    versions_root: Path,
    output_root: Path,
    run_id: str,
    max_examples: int,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> dict[str, Any]:
    """Run one teacher experiment with tracking and validation."""
    provider_name, model_name = _resolve_provider_and_model(
        provider=provider,
        teacher_model=teacher_model,
    )

    registry = PromptRegistry(versions_root)
    prompt_record = registry.get_prompt_version(prompt_id=prompt_id, version=prompt_version)
    prompt_text = Path(prompt_record.prompt_path).read_text(encoding="utf-8")

    tasks = _load_task_suite(task_suite_path)
    examples = list(_parse_dataset_examples(dataset_path))
    if max_examples > 0:
        examples = examples[:max_examples]

    if not examples:
        raise ValueError(f"No valid dataset examples found in: {dataset_path}")

    output_dir = output_root / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    responses_path = output_dir / "responses.jsonl"
    validation_path = output_dir / "validation_results.jsonl"
    failures_path = output_dir / "failures.jsonl"

    tracker = ExperimentTracker(
        experiment_name=run_id,
        dataset_path=dataset_path,
        teacher_version=f"{model_name}:{prompt_record.prompt_id}:{prompt_record.version}",
        training_config={
            "runner": "teacher_experiment",
            "provider": provider_name,
            "teacher_model": model_name,
            "prompt_id": prompt_record.prompt_id,
            "prompt_version": prompt_record.version,
            "prompt_hash_sha256": prompt_record.prompt_hash_sha256,
            "task_suite_path": str(task_suite_path),
            "task_count": len(tasks),
            "temperature": temperature,
            "seed": seed,
            "timeout_seconds": timeout_seconds,
            "max_output_tokens": max_output_tokens,
        },
        seed=seed,
    )

    tracker.log_event(
        "experiment_started",
        {
            "run_id": run_id,
            "output_dir": str(output_dir),
            "dataset_examples": len(examples),
            "task_count": len(tasks),
            "provider": provider_name,
            "model_name": model_name,
        },
    )

    provider_adapter = create_teacher_provider(
        provider=provider_name,
        model_name=model_name,
        prompt_template=prompt_text,
        temperature=temperature,
        seed=seed,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )

    gold_index = _load_gold_index(dataset_path)

    total_requests = 0
    successful_requests = 0
    failed_requests = 0

    cost_values: list[float] = []
    latency_values: list[float] = []
    confidence_values: list[float] = []
    validation_json_valid: list[float] = []

    for task in tasks:
        for example in examples:
            total_requests += 1
            started = time.perf_counter()
            try:
                output = provider_adapter.generate(
                    TeacherExample(
                        example_id=example.example_id,
                        prompt=example.prompt,
                        essay=example.essay,
                        score=example.score,
                        task_id=task.task_id,
                        metadata={
                            "source": example.source,
                            "difficulty": example.difficulty,
                            "task_description": task.description,
                        },
                    )
                )
                call_latency_ms = (time.perf_counter() - started) * 1000.0

                metadata = (
                    output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
                )
                if _safe_float(metadata.get("latency_ms")) is None:
                    metadata["latency_ms"] = call_latency_ms
                    output["metadata"] = metadata

                cost_usd = _estimate_call_cost(teacher_model=model_name, output=output)
                if cost_usd is not None:
                    cost_values.append(cost_usd)

                latency_value = _safe_float(metadata.get("latency_ms"))
                if latency_value is not None:
                    latency_values.append(latency_value)

                confidence = _safe_float(output.get("confidence"))
                if confidence is not None:
                    if confidence > 1.0:
                        confidence = confidence / 100.0
                    confidence = max(0.0, min(1.0, confidence))
                    confidence_values.append(confidence)

                prediction = _to_prediction_record(
                    teacher_model=model_name,
                    example=example,
                    output=output,
                    cost_usd=cost_usd,
                )
                validation = validate_prediction(
                    prediction,
                    gold=gold_index.get(example.example_id),
                )
                validation_json_valid.append(1.0 if validation.json_validity else 0.0)

                response_row = {
                    "run_id": run_id,
                    "timestamp_utc": _utc_now(),
                    "provider": provider_name,
                    "model": model_name,
                    "prompt_id": prompt_record.prompt_id,
                    "prompt_version": prompt_record.version,
                    "prompt_hash_sha256": prompt_record.prompt_hash_sha256,
                    "task_id": task.task_id,
                    "example_id": example.example_id,
                    "temperature": temperature,
                    "seed": seed,
                    "estimated_cost_usd": cost_usd,
                    "latency_ms": latency_value,
                    "confidence": confidence,
                    "input_tokens": _safe_int(metadata.get("input_tokens"), default=0),
                    "output_tokens": _safe_int(metadata.get("output_tokens"), default=0),
                    "output": output,
                }
                _append_jsonl(responses_path, response_row)
                _append_jsonl(
                    validation_path,
                    {
                        "run_id": run_id,
                        "timestamp_utc": _utc_now(),
                        "task_id": task.task_id,
                        "example_id": example.example_id,
                        "validation": _validation_to_json(validation),
                    },
                )
                successful_requests += 1
            except Exception as exc:  # pragma: no cover - runtime/provider variability
                failed_requests += 1
                failure_row = {
                    "run_id": run_id,
                    "timestamp_utc": _utc_now(),
                    "provider": provider_name,
                    "model": model_name,
                    "task_id": task.task_id,
                    "example_id": example.example_id,
                    "temperature": temperature,
                    "seed": seed,
                    "latency_ms": (time.perf_counter() - started) * 1000.0,
                    "error": f"{type(exc).__name__}: {exc}",
                }
                _append_jsonl(failures_path, failure_row)

    summary = {
        "run_id": run_id,
        "created_at": _utc_now(),
        "output_dir": str(output_dir),
        "dataset_path": str(dataset_path),
        "task_suite_path": str(task_suite_path),
        "provider": provider_name,
        "model": model_name,
        "prompt_id": prompt_record.prompt_id,
        "prompt_version": prompt_record.version,
        "prompt_hash_sha256": prompt_record.prompt_hash_sha256,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "example_count": len(examples),
        "task_count": len(tasks),
        "temperature": temperature,
        "seed": seed,
        "metrics": {
            "total_cost_usd": sum(cost_values) if cost_values else 0.0,
            "avg_cost_usd": mean(cost_values) if cost_values else None,
            "avg_latency_ms": mean(latency_values) if latency_values else None,
            "p95_latency_ms": (
                sorted(latency_values)[max(0, int(len(latency_values) * 0.95) - 1)]
                if latency_values
                else None
            ),
            "avg_confidence": mean(confidence_values) if confidence_values else None,
            "json_validity_rate": (mean(validation_json_valid) if validation_json_valid else None),
        },
        "artifacts": {
            "responses_path": str(responses_path),
            "validation_path": str(validation_path),
            "failures_path": str(failures_path),
        },
        "experiment_tracker": {
            "experiment_id": tracker.experiment_id,
            "run_dir": str(tracker.run_dir),
            "manifest_path": str(tracker.manifest_path),
        },
    }

    _write_json(output_dir / "summary.json", summary)
    _write_json(
        output_dir / "manifest.json",
        {
            "run_id": run_id,
            "created_at": summary["created_at"],
            "dataset_path": str(dataset_path),
            "provider": provider_name,
            "model": model_name,
            "prompt_id": prompt_record.prompt_id,
            "prompt_version": prompt_record.version,
            "prompt_hash_sha256": prompt_record.prompt_hash_sha256,
            "task_ids": [task.task_id for task in tasks],
            "example_count": len(examples),
            "temperature": temperature,
            "seed": seed,
            "responses_path": str(responses_path),
            "validation_path": str(validation_path),
            "failures_path": str(failures_path),
            "summary_path": str(output_dir / "summary.json"),
            "experiment_tracker_manifest": str(tracker.manifest_path),
        },
    )

    tracker.set_metrics(summary["metrics"], section="teacher_experiment")
    tracker.set_metrics(
        {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "json_validity_rate": summary["metrics"].get("json_validity_rate"),
        },
        section="validation",
    )

    final_status = "completed" if failed_requests == 0 else "completed_with_failures"
    tracker.finalize(
        status=final_status,
        notes=(
            f"run_id={run_id}; provider={provider_name}; model={model_name}; "
            f"requests={total_requests}; success={successful_requests}; failed={failed_requests}"
        ),
    )

    return summary


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run one tracked teacher experiment.")
    parser.add_argument("--dataset", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--teacher-model", required=True)
    parser.add_argument("--provider", default="")
    parser.add_argument("--providers-config", default="configs/providers/providers_v1.json")
    parser.add_argument("--env-file", default=".env")

    parser.add_argument("--prompt-id", required=True)
    parser.add_argument("--prompt-version", default="latest")
    parser.add_argument("--versions-root", default="teacher_prompts/versions")

    parser.add_argument("--task-suite", default="configs/teacher/teacher_task_suite_v1.json")

    parser.add_argument("--output-root", default="outputs/teacher_runs")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--max-examples", type=int, default=0)

    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    run_id = _normalize_text(args.run_id) or _default_run_id()
    provider_name, _ = _resolve_provider_and_model(
        provider=(_normalize_text(args.provider) or None),
        teacher_model=str(args.teacher_model),
    )
    validate_provider_configuration(
        required_providers=[provider_name],
        config_path=Path(args.providers_config),
        env_file=Path(args.env_file),
        strict=True,
        load_env=True,
        override_env=False,
    )

    summary = run_teacher_experiment(
        dataset_path=Path(args.dataset),
        teacher_model=str(args.teacher_model),
        provider=(_normalize_text(args.provider) or None),
        prompt_id=str(args.prompt_id),
        prompt_version=str(args.prompt_version),
        task_suite_path=Path(args.task_suite),
        versions_root=Path(args.versions_root),
        output_root=Path(args.output_root),
        run_id=run_id,
        max_examples=max(0, int(args.max_examples)),
        temperature=float(args.temperature),
        seed=int(args.seed),
        timeout_seconds=float(args.timeout_seconds),
        max_output_tokens=int(args.max_output_tokens),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
