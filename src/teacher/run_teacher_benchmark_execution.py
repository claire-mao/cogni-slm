"""Prepare and optionally execute config-driven teacher benchmark runs.

This runner is designed for benchmarking teacher providers against examples in
`datasets/gold/` and writing run artifacts to `outputs/teacher_benchmark/`.

By default, this command only prepares the execution package (manifests and
output directories). Provider inference is executed only when `--execute` is
explicitly passed.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SUPPORTED_MODELS, canonical_model_id, estimate_cost_usd
from .provider_config import validate_provider_configuration
from .providers import TeacherExample, create_teacher_provider

REQUIRED_TEACHER_MODELS: tuple[str, ...] = (
    "gpt-5",
    "o3",
    "claude_sonnet_4",
    "claude_opus_4",
    "gemini_2_5_pro",
    "deepseek_r1",
    "qwen3",
    "llama_4_maverick",
)


@dataclass(frozen=True)
class TaskSpec:
    """Task specification loaded from teacher task-suite config."""

    task_id: str
    description: str
    required_output_fields: tuple[str, ...]
    scoring_mode: str


@dataclass(frozen=True)
class ModelSpec:
    """Teacher model specification loaded from teacher model-costs config."""

    canonical_id: str
    config_model_id: str
    display_name: str
    provider: str
    api_model_name: str
    api_availability: str
    pricing: dict[str, Any]
    raw: dict[str, Any]


@dataclass(frozen=True)
class ExampleSpec:
    """One benchmark example resolved from datasets/gold/*."""

    example_id: str
    prompt: str
    essay: str
    score: float | None
    source: str
    difficulty: str
    raw: dict[str, Any]


@dataclass(frozen=True)
class ExecutionPlan:
    """Fully resolved execution plan for one benchmark run."""

    run_id: str
    prompt_version: str
    dataset_path: Path
    prompt_template_path: Path
    models: tuple[ModelSpec, ...]
    tasks: tuple[TaskSpec, ...]
    examples: tuple[ExampleSpec, ...]
    temperatures: tuple[float, ...]
    seeds: tuple[int, ...]
    execute: bool
    timeout_seconds: float
    max_output_tokens: int


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("teacher-benchmark-%Y%m%dT%H%M%SZ")


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


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


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


def _provider_env_key(model_id: str) -> str:
    normalized = model_id.replace("-", "_").replace(".", "_").upper()
    return f"TEACHER_PROVIDER_{normalized}"


def _api_model_env_key(model_id: str) -> str:
    normalized = model_id.replace("-", "_").replace(".", "_").upper()
    return f"TEACHER_API_MODEL_{normalized}"


def _infer_provider(*, canonical_id: str, api_availability: str) -> str:
    env_override = os.getenv(_provider_env_key(canonical_id))
    if env_override:
        return env_override.strip().lower()

    lower = api_availability.lower()
    if "openai_api" in lower:
        return "openai"
    if "anthropic" in lower:
        return "anthropic"
    if "gemini" in lower or "vertex" in lower:
        return "gemini"
    if "deepseek" in lower:
        return "deepseek"
    if canonical_id in {"qwen3", "llama_4_maverick"}:
        return "openrouter"
    return "openrouter"


def _resolve_api_model_name(*, canonical_id: str, raw: dict[str, Any]) -> str:
    env_override = os.getenv(_api_model_env_key(canonical_id))
    if env_override and env_override.strip():
        return env_override.strip()

    for key in ("api_model_name", "model_name", "provider_model_name"):
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return canonical_id


def _resolve_config_path(master_path: Path, configured: str) -> Path:
    configured_path = Path(configured)
    if configured_path.is_absolute():
        return configured_path
    return (master_path.parent.parent.parent / configured_path).resolve()


def _resolve_dataset_jsonl(dataset_root: Path) -> Path:
    if dataset_root.is_file():
        return dataset_root

    candidates = [
        dataset_root / "gold_v1.jsonl",
        dataset_root / "gold.jsonl",
        dataset_root / "candidates" / "candidate_gold.jsonl",
        dataset_root / "review_package" / "review_forms.jsonl",
    ]
    for path in candidates:
        if path.exists():
            return path

    discovered = sorted(dataset_root.rglob("*.jsonl"))
    if discovered:
        return discovered[0]
    raise FileNotFoundError(f"No JSONL dataset found under {dataset_root}")


def _parse_original_id(value: str) -> tuple[str, int] | None:
    raw = value.strip()
    if ":" not in raw:
        return None
    split, idx_text = raw.split(":", maxsplit=1)
    if not split:
        return None
    try:
        idx = int(idx_text)
    except ValueError:
        return None
    if idx < 0:
        return None
    return split, idx


def _read_training_example(original_id: str) -> tuple[str, str] | None:
    parsed = _parse_original_id(original_id)
    if parsed is None:
        return None

    split, index = parsed
    try:
        from datasets import load_from_disk  # pragma: no cover - dependency environment variability
    except Exception:
        return None

    training_path = Path("datasets/training")
    if not training_path.exists():
        return None
    try:
        ds = load_from_disk(str(training_path))
    except Exception:
        return None
    if split not in ds:
        return None
    if index >= len(ds[split]):
        return None
    row = ds[split][index]
    prompt = _normalize_text(row.get("prompt"))
    essay = _normalize_text(row.get("essay"))
    if not prompt or not essay:
        return None
    return prompt, essay


def _load_examples(path: Path) -> tuple[tuple[ExampleSpec, ...], dict[str, int]]:
    rows = _read_jsonl(path)
    items: list[ExampleSpec] = []
    skipped_missing_text = 0
    filled_from_training = 0

    for index, row in enumerate(rows, start=1):
        if _is_simulated_example(row):
            raise ValueError(
                "Simulated/placeholder benchmark row detected at "
                f"{path}:{index}. Provide a real benchmark dataset before execution."
            )
        example_id = _normalize_text(row.get("example_id") or row.get("id"))
        if not example_id:
            example_id = f"example-{index:06d}"

        prompt = _normalize_text(row.get("prompt") or row.get("prompt_text"))
        essay = _normalize_text(row.get("essay") or row.get("essay_text"))

        if not prompt or not essay:
            original_id = _normalize_text(row.get("original_id"))
            if original_id:
                resolved = _read_training_example(original_id)
                if resolved is not None:
                    prompt, essay = resolved
                    filled_from_training += 1

        if not prompt or not essay:
            skipped_missing_text += 1
            continue

        score = _safe_float(row.get("gold_score", row.get("score")))
        source = _normalize_text(row.get("source")) or _normalize_text(row.get("original_dataset"))
        if not source:
            source = "unknown"
        difficulty = _normalize_text(row.get("difficulty")) or "unknown"

        items.append(
            ExampleSpec(
                example_id=example_id,
                prompt=prompt,
                essay=essay,
                score=score,
                source=source,
                difficulty=difficulty,
                raw=row,
            )
        )

    return tuple(items), {
        "input_rows": len(rows),
        "selected_rows": len(items),
        "skipped_missing_prompt_or_essay": skipped_missing_text,
        "filled_from_training_lookup": filled_from_training,
    }


def _load_tasks(task_suite_path: Path) -> tuple[TaskSpec, ...]:
    payload = _read_json(task_suite_path)
    rows = payload.get("tasks")
    if not isinstance(rows, list):
        raise ValueError(f"Task suite missing tasks list: {task_suite_path}")

    tasks: list[TaskSpec] = []
    for row in rows:
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
                required_output_fields=tuple(_normalize_text(item) for item in fields),
                scoring_mode=scoring_mode,
            )
        )
    if not tasks:
        raise ValueError(f"No valid tasks in: {task_suite_path}")
    return tuple(tasks)


def _load_models(models_path: Path) -> tuple[ModelSpec, ...]:
    payload = _read_json(models_path)
    rows = payload.get("models")
    if not isinstance(rows, list):
        raise ValueError(f"Model config missing models list: {models_path}")

    models: list[ModelSpec] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        model_id = row.get("model_id")
        if not isinstance(model_id, str) or not model_id.strip():
            continue

        canonical = canonical_model_id(model_id)
        pricing = row.get("pricing_usd_per_million_tokens")
        if not isinstance(pricing, dict):
            pricing = {}

        api_availability = _normalize_text(row.get("api_availability"))
        provider = _infer_provider(canonical_id=canonical, api_availability=api_availability)
        api_model_name = _resolve_api_model_name(canonical_id=canonical, raw=row)

        models.append(
            ModelSpec(
                canonical_id=canonical,
                config_model_id=model_id,
                display_name=_normalize_text(row.get("display_name")) or canonical,
                provider=provider,
                api_model_name=api_model_name,
                api_availability=api_availability,
                pricing=dict(pricing),
                raw=dict(row),
            )
        )

    dedup: dict[str, ModelSpec] = {}
    for model in models:
        dedup[model.canonical_id] = model

    missing = sorted(set(REQUIRED_TEACHER_MODELS) - set(dedup.keys()))
    if missing:
        raise ValueError(
            "Missing required teacher model(s) in config: " + ", ".join(missing)
        )

    ordered: list[ModelSpec] = []
    for model_id in REQUIRED_TEACHER_MODELS:
        ordered.append(dedup[model_id])
    return tuple(ordered)


def _build_task_prompt_template(base_template: str, task: TaskSpec) -> str:
    task_lines = [
        "",
        "[BENCHMARK TASK CONTEXT]",
        f"task_id: {task.task_id}",
        f"description: {task.description}",
        f"required_output_fields: {', '.join(task.required_output_fields)}",
        f"scoring_mode: {task.scoring_mode}",
        "",
        "[OUTPUT CONTRACT]",
        "Return strict JSON only and include task-grounded reasoning.",
    ]
    return base_template.rstrip() + "\n" + "\n".join(task_lines) + "\n"


def _extract_confidence(output: dict[str, Any]) -> float | None:
    raw = _safe_float(output.get("confidence"))
    if raw is None:
        return None
    if raw > 1.0:
        raw = raw / 100.0
    return max(0.0, min(1.0, raw))


def _estimate_cost(
    *,
    model_id: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    if input_tokens is None or output_tokens is None:
        return None
    return estimate_cost_usd(model_id, input_tokens=input_tokens, output_tokens=output_tokens)


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = int(round((len(ordered) - 1) * fraction))
    index = max(0, min(len(ordered) - 1, index))
    return ordered[index]


def _aggregate_metrics(
    responses: list[dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    by_model_cost: dict[str, list[float]] = {}
    by_model_latency: dict[str, list[float]] = {}
    by_model_confidence: dict[str, list[float]] = {}

    for row in responses:
        model = _normalize_text(row.get("model"))
        if not model:
            continue
        cost = _safe_float(row.get("estimated_cost_usd"))
        if cost is not None:
            by_model_cost.setdefault(model, []).append(cost)
        latency = _safe_float(row.get("latency_ms"))
        if latency is not None:
            by_model_latency.setdefault(model, []).append(latency)
        confidence = _safe_float(row.get("confidence"))
        if confidence is not None:
            by_model_confidence.setdefault(model, []).append(confidence)

    cost_summary = {
        "models": {
            model: {
                "calls_with_cost": len(values),
                "total_estimated_cost_usd": sum(values),
                "avg_estimated_cost_usd": (sum(values) / len(values)) if values else None,
            }
            for model, values in sorted(by_model_cost.items())
        },
        "total_estimated_cost_usd": sum(sum(values) for values in by_model_cost.values()),
    }

    latency_summary = {
        "models": {
            model: {
                "calls_with_latency": len(values),
                "avg_latency_ms": statistics.mean(values) if values else None,
                "p50_latency_ms": _percentile(values, 0.50),
                "p95_latency_ms": _percentile(values, 0.95),
            }
            for model, values in sorted(by_model_latency.items())
        },
    }

    confidence_summary = {
        "models": {
            model: {
                "calls_with_confidence": len(values),
                "avg_confidence": statistics.mean(values) if values else None,
                "min_confidence": min(values) if values else None,
                "max_confidence": max(values) if values else None,
                "low_confidence_rate_below_0_5": (
                    sum(1 for value in values if value < 0.5) / len(values)
                    if values
                    else None
                ),
            }
            for model, values in sorted(by_model_confidence.items())
        },
    }
    return cost_summary, latency_summary, confidence_summary


def _prepare_output_scaffold(run_dir: Path) -> dict[str, Path]:
    responses_dir = run_dir / "responses"
    cost_dir = run_dir / "cost"
    latency_dir = run_dir / "latency"
    confidence_dir = run_dir / "confidence"
    metadata_dir = run_dir / "metadata"
    for path in (responses_dir, cost_dir, latency_dir, confidence_dir, metadata_dir):
        path.mkdir(parents=True, exist_ok=True)
    return {
        "responses_jsonl": responses_dir / "responses.jsonl",
        "failures_jsonl": responses_dir / "failures.jsonl",
        "cost_json": cost_dir / "summary.json",
        "latency_json": latency_dir / "summary.json",
        "confidence_json": confidence_dir / "summary.json",
        "metadata_json": metadata_dir / "manifest.json",
        "models_json": metadata_dir / "models.json",
        "tasks_json": metadata_dir / "tasks.json",
        "dataset_json": metadata_dir / "dataset.json",
    }


def _build_plan(args: argparse.Namespace) -> tuple[ExecutionPlan, dict[str, Any]]:
    config_root = Path(args.config_root)
    master_path = config_root / "teacher_validation_master.json"
    master = _read_json(master_path)
    configs = master.get("configs")
    if not isinstance(configs, dict):
        raise ValueError(f"Missing configs object in {master_path}")

    task_suite_path = (
        Path(args.task_suite)
        if args.task_suite
        else _resolve_config_path(master_path, str(configs["task_suite"]))
    )
    models_path = (
        Path(args.models_costs)
        if args.models_costs
        else _resolve_config_path(master_path, str(configs["models_costs"]))
    )

    dataset_path = _resolve_dataset_jsonl(Path(args.dataset_root))
    examples, dataset_stats = _load_examples(dataset_path)
    if not examples:
        raise ValueError(f"No valid benchmark examples loaded from {dataset_path}")

    max_examples = int(args.max_examples)
    if max_examples > 0:
        examples = examples[:max_examples]

    tasks = _load_tasks(task_suite_path)
    models = _load_models(models_path)

    temperatures = tuple(
        float(item.strip()) for item in str(args.temperatures).split(",") if item.strip()
    )
    if not temperatures:
        raise ValueError("At least one temperature is required.")

    seeds = tuple(int(item.strip()) for item in str(args.seeds).split(",") if item.strip())
    if not seeds:
        raise ValueError("At least one seed is required.")

    plan = ExecutionPlan(
        run_id=str(args.run_id).strip() or _default_run_id(),
        prompt_version=str(args.prompt_version).strip() or "production_teacher_v1",
        dataset_path=dataset_path,
        prompt_template_path=Path(args.prompt_template),
        models=models,
        tasks=tasks,
        examples=tuple(examples),
        temperatures=temperatures,
        seeds=seeds,
        execute=bool(args.execute),
        timeout_seconds=float(args.timeout_seconds),
        max_output_tokens=int(args.max_output_tokens),
    )
    return plan, dataset_stats


def run_execution_pipeline(
    plan: ExecutionPlan,
    *,
    output_root: Path,
    dataset_stats: dict[str, Any],
    provider_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare benchmark run artifacts and optionally execute provider calls."""
    run_dir = output_root / plan.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = _prepare_output_scaffold(run_dir)

    prompt_template = plan.prompt_template_path.read_text(encoding="utf-8")

    planned_requests = (
        len(plan.models)
        * len(plan.tasks)
        * len(plan.examples)
        * len(plan.temperatures)
        * len(plan.seeds)
    )

    _write_json(
        paths["models_json"],
        {
            "supported_models": list(SUPPORTED_MODELS),
            "required_models": list(REQUIRED_TEACHER_MODELS),
            "models": [
                {
                    "canonical_id": model.canonical_id,
                    "config_model_id": model.config_model_id,
                    "display_name": model.display_name,
                    "provider": model.provider,
                    "api_model_name": model.api_model_name,
                    "api_availability": model.api_availability,
                    "pricing_usd_per_million_tokens": model.pricing,
                }
                for model in plan.models
            ],
            "provider_override_env_vars": {
                model.canonical_id: _provider_env_key(model.canonical_id) for model in plan.models
            },
            "api_model_override_env_vars": {
                model.canonical_id: _api_model_env_key(model.canonical_id) for model in plan.models
            },
        },
    )
    _write_json(
        paths["tasks_json"],
        {
            "tasks": [
                {
                    "task_id": task.task_id,
                    "description": task.description,
                    "required_output_fields": list(task.required_output_fields),
                    "scoring_mode": task.scoring_mode,
                }
                for task in plan.tasks
            ]
        },
    )
    _write_json(
        paths["dataset_json"],
        {
            "dataset_path": str(plan.dataset_path),
            "example_count": len(plan.examples),
            "dataset_stats": dataset_stats,
            "example_ids_preview": [example.example_id for example in plan.examples[:10]],
        },
    )

    if not paths["responses_jsonl"].exists():
        paths["responses_jsonl"].write_text("", encoding="utf-8")
    if not paths["failures_jsonl"].exists():
        paths["failures_jsonl"].write_text("", encoding="utf-8")

    total_requests = 0
    successful_requests = 0
    failed_requests = 0
    response_rows: list[dict[str, Any]] = []

    if plan.execute:
        for model in plan.models:
            for task in plan.tasks:
                task_prompt_template = _build_task_prompt_template(prompt_template, task)
                for temperature in plan.temperatures:
                    for seed in plan.seeds:
                        provider = create_teacher_provider(
                            provider=model.provider,
                            model_name=model.api_model_name,
                            prompt_template=task_prompt_template,
                            temperature=temperature,
                            seed=seed,
                            timeout_seconds=plan.timeout_seconds,
                            max_output_tokens=plan.max_output_tokens,
                        )
                        for example in plan.examples:
                            total_requests += 1
                            try:
                                output = provider.generate(
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
                                metadata = (
                                    output.get("metadata")
                                    if isinstance(output.get("metadata"), dict)
                                    else {}
                                )
                                latency_ms = _safe_float(metadata.get("latency_ms"))
                                input_tokens = _safe_int(metadata.get("input_tokens"), default=0)
                                output_tokens = _safe_int(metadata.get("output_tokens"), default=0)
                                confidence = _extract_confidence(output)
                                cost = _estimate_cost(
                                    model_id=model.canonical_id,
                                    input_tokens=input_tokens,
                                    output_tokens=output_tokens,
                                )
                                row = {
                                    "run_id": plan.run_id,
                                    "timestamp_utc": _utc_now(),
                                    "model": model.canonical_id,
                                    "model_display_name": model.display_name,
                                    "provider": model.provider,
                                    "api_model_name": model.api_model_name,
                                    "prompt_version": plan.prompt_version,
                                    "task_id": task.task_id,
                                    "example_id": example.example_id,
                                    "temperature": temperature,
                                    "seed": seed,
                                    "latency_ms": latency_ms,
                                    "input_tokens": input_tokens,
                                    "output_tokens": output_tokens,
                                    "estimated_cost_usd": cost,
                                    "confidence": confidence,
                                    "output": output,
                                }
                                response_rows.append(row)
                                _append_jsonl(paths["responses_jsonl"], row)
                                successful_requests += 1
                            except Exception as exc:  # pragma: no cover - provider variability
                                failed_requests += 1
                                _append_jsonl(
                                    paths["failures_jsonl"],
                                    {
                                        "run_id": plan.run_id,
                                        "timestamp_utc": _utc_now(),
                                        "model": model.canonical_id,
                                        "provider": model.provider,
                                        "api_model_name": model.api_model_name,
                                        "prompt_version": plan.prompt_version,
                                        "task_id": task.task_id,
                                        "example_id": example.example_id,
                                        "temperature": temperature,
                                        "seed": seed,
                                        "error": f"{type(exc).__name__}: {exc}",
                                    },
                                )
    else:
        total_requests = planned_requests

    cost_summary, latency_summary, confidence_summary = _aggregate_metrics(response_rows)

    _write_json(
        paths["cost_json"],
        {
            "run_id": plan.run_id,
            "execute_mode": plan.execute,
            "generated_at_utc": _utc_now(),
            "planned_requests": planned_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "summary": cost_summary,
        },
    )
    _write_json(
        paths["latency_json"],
        {
            "run_id": plan.run_id,
            "execute_mode": plan.execute,
            "generated_at_utc": _utc_now(),
            "planned_requests": planned_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "summary": latency_summary,
        },
    )
    _write_json(
        paths["confidence_json"],
        {
            "run_id": plan.run_id,
            "execute_mode": plan.execute,
            "generated_at_utc": _utc_now(),
            "planned_requests": planned_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "summary": confidence_summary,
        },
    )

    metadata = {
        "run_id": plan.run_id,
        "created_at_utc": _utc_now(),
        "status": "executed" if plan.execute else "prepared",
        "execution_enabled": plan.execute,
        "output_root": str(output_root),
        "run_dir": str(run_dir),
        "dataset_path": str(plan.dataset_path),
        "prompt_template_path": str(plan.prompt_template_path),
        "prompt_version": plan.prompt_version,
        "models": [model.canonical_id for model in plan.models],
        "providers": sorted({model.provider for model in plan.models}),
        "task_ids": [task.task_id for task in plan.tasks],
        "example_count": len(plan.examples),
        "temperature_values": list(plan.temperatures),
        "seed_values": list(plan.seeds),
        "planned_requests": planned_requests,
        "total_requests": total_requests,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "timeout_seconds": plan.timeout_seconds,
        "max_output_tokens": plan.max_output_tokens,
        "artifact_paths": {key: str(path) for key, path in paths.items()},
        "provider_validation": provider_validation or {},
        "notes": (
            "Run prepared only; provider inference was not executed."
            if not plan.execute
            else "Provider inference executed."
        ),
    }
    _write_json(paths["metadata_json"], metadata)

    return metadata


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Prepare and optionally execute teacher benchmark runs. "
            "Default mode prepares artifacts only (no inference)."
        )
    )
    parser.add_argument("--config-root", default="configs/teacher")
    parser.add_argument("--dataset-root", default="datasets/gold")
    parser.add_argument("--prompt-template", default="teacher_prompts/production_teacher.txt")
    parser.add_argument("--prompt-version", default="production_teacher_v1")
    parser.add_argument("--models-costs", default="")
    parser.add_argument("--task-suite", default="")
    parser.add_argument("--providers-config", default="configs/providers/providers_v1.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--output-root", default="outputs/teacher_benchmark")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--temperatures", default="0.0")
    parser.add_argument("--seeds", default="42")
    parser.add_argument("--max-examples", type=int, default=0)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Execute provider inference. If omitted, command only prepares "
            "execution artifacts and metadata (no model calls)."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    plan, dataset_stats = _build_plan(args)
    required_providers = [model.provider for model in plan.models]
    provider_validation = validate_provider_configuration(
        required_providers=required_providers,
        config_path=Path(args.providers_config),
        env_file=Path(args.env_file),
        strict=bool(plan.execute),
        load_env=True,
        override_env=False,
    )
    summary = run_execution_pipeline(
        plan=plan,
        output_root=Path(args.output_root),
        dataset_stats=dataset_stats,
        provider_validation=provider_validation,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
