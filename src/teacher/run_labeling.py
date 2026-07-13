"""Production labeling runner.

Responsibilities:
- load dataset
- load teacher provider
- run inference
- resume interrupted runs
- execute parallel requests
- retry failed requests
- validate outputs
- save checkpoints
- track costs/latency
- record experiment metadata

This script prepares and executes teacher inference for labeling workflows.
"""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from utils.environment import get_teacher_provider_mode
from utils.experiment_tracker import ExperimentTracker

from .models import canonical_model_id, estimate_cost_usd
from .prompt_registry import compute_prompt_hash
from .prompt_versioning import PromptVersionManager
from .provider_config import validate_provider_configuration
from .providers import TeacherExample, canonical_provider_name, create_teacher_provider
from .providers.common import validate_normalized_output
from .validate_environment import validate_environment


@dataclass(frozen=True)
class DatasetExample:
    """One dataset row for teacher labeling."""

    example_id: str
    prompt: str
    essay: str
    score: float | None
    metadata: dict[str, Any]


@dataclass(frozen=True)
class WorkerResult:
    """Result of one labeling request."""

    example_id: str
    success: bool
    attempts: int
    output: dict[str, Any] | None
    validation_errors: tuple[str, ...]
    latency_ms: float | None
    input_tokens: int | None
    output_tokens: int | None
    estimated_cost_usd: float | None
    error: str | None


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


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temp.replace(path)


def _resolve_repo_relative_path(path: Path) -> Path:
    """Resolve a relative path from repo root when not found in current cwd."""
    if path.is_absolute() or path.exists():
        return path
    repo_root = Path(__file__).resolve().parents[2]
    candidate = repo_root / path
    if candidate.exists():
        return candidate
    return path


def _infer_provider(model_name: str) -> str:
    lowered = model_name.strip().lower()
    if "claude" in lowered:
        return "anthropic"
    if "gemini" in lowered:
        return "gemini"
    if "deepseek" in lowered:
        return "deepseek"
    if "openrouter" in lowered:
        return "openrouter"
    if lowered.startswith("local/") or "transformers" in lowered or lowered.startswith("hf:"):
        return "local_transformers"
    return "openai"


def _normalize_runtime_provider(value: str) -> str:
    normalized = _normalize_text(value).lower()
    if normalized == "google":
        return "gemini"
    return canonical_provider_name(normalized)


def _canonical_model_or_none(model_name: str) -> str | None:
    try:
        return canonical_model_id(model_name)
    except Exception:
        return None


def _is_simulated_row(row: dict[str, Any]) -> bool:
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


def _extract_dataset(path: Path) -> list[DatasetExample]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    rows = _read_jsonl(path)
    parsed: list[DatasetExample] = []
    seen_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if _is_simulated_row(row):
            raise ValueError(
                "Simulated/placeholder dataset row detected at "
                f"{path}:{index}. Provide real examples before production labeling."
            )

        example_id = _normalize_text(row.get("example_id") or row.get("id"))
        if not example_id:
            example_id = f"example-{index:06d}"
        if example_id in seen_ids:
            raise ValueError(f"Duplicate example_id detected: {example_id}")
        seen_ids.add(example_id)

        prompt = _normalize_text(row.get("prompt") or row.get("prompt_text"))
        essay = _normalize_text(
            row.get("essay") or row.get("essay_text") or row.get("text") or row.get("input")
        )
        if not prompt or not essay:
            raise ValueError(
                "Dataset row missing prompt/essay at " f"{path}:{index} (example_id={example_id})"
            )

        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        parsed.append(
            DatasetExample(
                example_id=example_id,
                prompt=prompt,
                essay=essay,
                score=_safe_float(row.get("score", row.get("gold_score"))),
                metadata=dict(metadata),
            )
        )
    return parsed


def _load_prompt(
    *,
    prompt_template_path: Path | None,
    prompts_root: Path,
    prompt_id: str | None,
    prompt_version: str,
) -> tuple[str, dict[str, Any]]:
    if prompt_id:
        manager = PromptVersionManager(prompts_root)
        record = manager.get_version(prompt_id=prompt_id, version_id=prompt_version)
        text = Path(record.prompt_path).read_text(encoding="utf-8")
        return text, {
            "prompt_source": "registry",
            "prompts_root": str(prompts_root),
            "prompt_id": record.prompt_id,
            "prompt_version": record.version_id,
            "prompt_checksum_sha256": record.checksum_sha256,
            "prompt_path": record.prompt_path,
        }

    if prompt_template_path is None:
        raise ValueError("Either --prompt-id or --prompt-template is required")
    if not prompt_template_path.exists() or not prompt_template_path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {prompt_template_path}")

    text = prompt_template_path.read_text(encoding="utf-8")
    return text, {
        "prompt_source": "template_file",
        "prompt_id": "inline_template",
        "prompt_version": _normalize_text(prompt_version) or "v1",
        "prompt_checksum_sha256": compute_prompt_hash(text),
        "prompt_path": str(prompt_template_path),
    }


def _load_completed_ids(responses_path: Path) -> set[str]:
    if not responses_path.exists():
        return set()
    completed: set[str] = set()
    for row in _read_jsonl(responses_path):
        example_id = _normalize_text(row.get("example_id"))
        if example_id:
            completed.add(example_id)
    return completed


def _estimate_cost(
    *,
    model_name: str,
    input_tokens: int | None,
    output_tokens: int | None,
    explicit_cost: float | None,
) -> float | None:
    if explicit_cost is not None:
        return explicit_cost
    in_tokens = _safe_int(input_tokens)
    out_tokens = _safe_int(output_tokens)
    if in_tokens is None or out_tokens is None:
        return None
    canonical = _canonical_model_or_none(model_name)
    if canonical is None:
        return None
    return estimate_cost_usd(canonical, input_tokens=in_tokens, output_tokens=out_tokens)


def _validate_output(
    output: dict[str, Any],
    *,
    schema_path: Path | None,
) -> tuple[bool, tuple[str, ...]]:
    metadata = output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
    parsed_output = metadata.get("raw_json_output")
    if not isinstance(parsed_output, dict):
        parsed_output = None

    errors = validate_normalized_output(
        parsed_output=parsed_output,
        normalized_output=output,
        schema_path=str(schema_path) if schema_path is not None else None,
    )

    metadata_errors = metadata.get("validation_errors")
    if isinstance(metadata_errors, list):
        for item in metadata_errors:
            if isinstance(item, str):
                errors.append(item)

    unique = tuple(sorted(set(errors)))
    return len(unique) == 0, unique


def _build_checkpoint(
    *,
    run_id: str,
    dataset_path: Path,
    output_dir: Path,
    config: dict[str, Any],
    total_examples: int,
    completed_examples: int,
    succeeded_examples: int,
    failed_examples: int,
    validated_examples: int,
    invalid_examples: int,
    total_input_tokens: int,
    total_output_tokens: int,
    total_cost_usd: float,
    latency_values_ms: list[float],
    resumed_from: bool,
) -> dict[str, Any]:
    avg_latency = sum(latency_values_ms) / len(latency_values_ms) if latency_values_ms else None
    return {
        "run_id": run_id,
        "updated_at_utc": _utc_now(),
        "dataset_path": str(dataset_path),
        "output_dir": str(output_dir),
        "resumed": resumed_from,
        "config": config,
        "counts": {
            "total_examples": total_examples,
            "completed_examples": completed_examples,
            "pending_examples": max(0, total_examples - completed_examples),
            "succeeded_examples": succeeded_examples,
            "failed_examples": failed_examples,
            "validated_examples": validated_examples,
            "invalid_examples": invalid_examples,
        },
        "usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "estimated_cost_usd": round(total_cost_usd, 8),
        },
        "latency": {
            "average_ms": avg_latency,
            "max_ms": max(latency_values_ms) if latency_values_ms else None,
            "min_ms": min(latency_values_ms) if latency_values_ms else None,
        },
    }


def run_labeling(
    *,
    dataset_path: Path,
    output_dir: Path,
    teacher_model: str,
    provider: str | None,
    prompt_template_path: Path | None,
    prompts_root: Path,
    prompt_id: str | None,
    prompt_version: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
    max_workers: int,
    request_max_attempts: int,
    request_retry_backoff_seconds: float,
    checkpoint_every: int,
    schema_path: Path | None,
    strict_validation: bool,
    run_id: str,
    resume: bool,
    providers_config_path: Path,
    env_file: Path,
) -> dict[str, Any]:
    """Run production teacher labeling and return final summary payload."""
    if max_workers < 1:
        raise ValueError("max_workers must be >= 1")
    if request_max_attempts < 1:
        raise ValueError("request_max_attempts must be >= 1")

    raw_provider = _normalize_text(provider).lower() if provider else _infer_provider(teacher_model)
    resolved_provider = _normalize_runtime_provider(raw_provider)
    if resolved_provider != "local_transformers":
        env_report = validate_environment(env_file=env_file)
        if not bool(env_report.get("valid")):
            issues: list[str] = []
            if env_report.get("format_error"):
                issues.append(str(env_report["format_error"]))
            missing = env_report.get("missing_keys") or []
            empty = env_report.get("empty_keys") or []
            invalid = env_report.get("invalid_format_keys") or []
            if missing:
                issues.append("missing_keys=" + ",".join(str(item) for item in missing))
            if empty:
                issues.append("empty_keys=" + ",".join(str(item) for item in empty))
            if invalid:
                issues.append("invalid_format_keys=" + ",".join(str(item) for item in invalid))
            detail_text = "; ".join(issues) if issues else "unknown_environment_error"
            raise ValueError(f"Environment validation failed: {detail_text}")

        provider_report = validate_provider_configuration(
            required_providers=[resolved_provider],
            config_path=providers_config_path,
            env_file=env_file,
            strict=False,
            load_env=False,
            override_env=False,
        )
        normalized = provider_report.get("required_providers_normalized") or []
        provider_key = str(normalized[0]) if normalized else resolved_provider
        provider_check = (
            provider_report.get("providers", {}).get(provider_key, {})
            if isinstance(provider_report.get("providers"), dict)
            else {}
        )
        if not bool(provider_report.get("valid")):
            missing_all = provider_check.get("missing_env_all") or []
            missing_any = provider_check.get("missing_env_any_groups") or []
            raise ValueError(
                "Provider configuration validation failed for "
                f"{provider_key}: missing_env_all={missing_all}; "
                f"missing_env_any_groups={missing_any}; config_path={providers_config_path}"
            )

        if get_teacher_provider_mode() == "truefoundry":
            required_all = {str(item) for item in provider_check.get("required_env_all", [])}
            required_any_groups = [
                {str(item) for item in group}
                for group in provider_check.get("required_env_any", [])
                if isinstance(group, list)
            ]
            expected_all = {"PRIMARY_TEACHER_MODEL", "VERIFIER_MODEL", "SECONDARY_MODEL"}
            expected_any = [
                {"TFY_API_KEY", "TRUEFOUNDRY_API_KEY"},
                {"TFY_BASE_URL", "TRUEFOUNDRY_BASE_URL"},
            ]
            has_expected_any = all(
                any(expected_group.issubset(actual_group) for actual_group in required_any_groups)
                for expected_group in expected_any
            )
            if not expected_all.issubset(required_all) or not has_expected_any:
                expected_alias_groups = sorted(map(sorted, expected_any))
                raise ValueError(
                    "Provider configuration is not aligned with TrueFoundry gateway requirements. "
                    f"Expected env keys {sorted(expected_all)} and alias groups "
                    f"{expected_alias_groups} "
                    f"for provider '{provider_key}' in {providers_config_path}."
                )

    prompt_template, prompt_meta = _load_prompt(
        prompt_template_path=prompt_template_path,
        prompts_root=prompts_root,
        prompt_id=prompt_id,
        prompt_version=prompt_version,
    )

    examples = _extract_dataset(dataset_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    responses_path = output_dir / "responses.jsonl"
    failures_path = output_dir / "failures.jsonl"
    checkpoints_dir = output_dir / "checkpoints"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoints_dir / "progress.json"
    metadata_path = output_dir / "metadata.json"
    summary_path = output_dir / "summary.json"

    if not resume and (responses_path.exists() or failures_path.exists()):
        raise FileExistsError(
            "Output artifacts already exist. Use --resume to continue an interrupted run "
            "or choose a new --output-dir."
        )

    completed_ids = _load_completed_ids(responses_path) if resume else set()
    resumed_completed_count = len(completed_ids)
    pending = [row for row in examples if row.example_id not in completed_ids]

    tracker = ExperimentTracker(
        experiment_name=run_id,
        dataset_path=dataset_path,
        teacher_version=f"{teacher_model}:{prompt_meta.get('prompt_id')}:{prompt_meta.get('prompt_version')}",
        training_config={
            "runner": "run_labeling",
            "provider": resolved_provider,
            "teacher_model": teacher_model,
            "prompt": prompt_meta,
            "temperature": temperature,
            "seed": seed,
            "timeout_seconds": timeout_seconds,
            "max_output_tokens": max_output_tokens,
            "max_workers": max_workers,
            "request_max_attempts": request_max_attempts,
            "request_retry_backoff_seconds": request_retry_backoff_seconds,
            "checkpoint_every": checkpoint_every,
            "schema_path": str(schema_path) if schema_path else None,
            "strict_validation": strict_validation,
            "resume": resume,
            "output_dir": str(output_dir),
        },
        seed=seed,
    )

    run_metadata = {
        "run_id": run_id,
        "created_at_utc": _utc_now(),
        "dataset_path": str(dataset_path),
        "output_dir": str(output_dir),
        "provider": resolved_provider,
        "teacher_model": teacher_model,
        "prompt": prompt_meta,
        "resume": resume,
        "resume_completed_count": resumed_completed_count,
        "total_examples": len(examples),
        "pending_examples": len(pending),
        "artifact_paths": {
            "responses_jsonl": str(responses_path),
            "failures_jsonl": str(failures_path),
            "checkpoint_json": str(checkpoint_path),
            "summary_json": str(summary_path),
            "experiment_tracker_dir": str(tracker.run_dir),
        },
    }
    _atomic_write_json(metadata_path, run_metadata)
    tracker.log_event("labeling_started", run_metadata)

    provider_kwargs = {
        "provider": resolved_provider,
        "model_name": teacher_model,
        "prompt_template": prompt_template,
        "temperature": float(temperature),
        "seed": int(seed),
        "timeout_seconds": float(timeout_seconds),
        "max_output_tokens": int(max_output_tokens),
    }

    thread_local = threading.local()

    def get_provider() -> Any:
        instance = getattr(thread_local, "provider", None)
        if instance is None:
            instance = create_teacher_provider(**provider_kwargs)
            thread_local.provider = instance
        return instance

    def run_one(example: DatasetExample) -> WorkerResult:
        last_error: str | None = None
        for attempt in range(1, request_max_attempts + 1):
            try:
                adapter = get_provider()
                output = adapter.generate(
                    TeacherExample(
                        example_id=example.example_id,
                        prompt=example.prompt,
                        essay=example.essay,
                        score=example.score,
                        metadata=example.metadata,
                    )
                )
                if not isinstance(output, dict):
                    raise ValueError("Provider returned non-object output")

                is_valid, validation_errors = _validate_output(
                    output,
                    schema_path=schema_path,
                )
                metadata = (
                    output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
                )
                latency_ms = _safe_float(metadata.get("latency_ms"))
                in_tokens = _safe_int(metadata.get("input_tokens"))
                out_tokens = _safe_int(metadata.get("output_tokens"))
                explicit_cost = _safe_float(metadata.get("estimated_cost_usd"))
                cost_usd = _estimate_cost(
                    model_name=teacher_model,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    explicit_cost=explicit_cost,
                )

                if strict_validation and not is_valid:
                    raise ValueError("Validation failed: " + ", ".join(validation_errors))

                return WorkerResult(
                    example_id=example.example_id,
                    success=True,
                    attempts=attempt,
                    output=output,
                    validation_errors=validation_errors,
                    latency_ms=latency_ms,
                    input_tokens=in_tokens,
                    output_tokens=out_tokens,
                    estimated_cost_usd=cost_usd,
                    error=None,
                )
            except Exception as exc:  # pragma: no cover - provider runtime variability
                last_error = f"{type(exc).__name__}: {exc}"
                if attempt >= request_max_attempts:
                    break
                if request_retry_backoff_seconds > 0:
                    sleep_seconds = request_retry_backoff_seconds * (2 ** (attempt - 1))
                    time.sleep(sleep_seconds)

        return WorkerResult(
            example_id=example.example_id,
            success=False,
            attempts=request_max_attempts,
            output=None,
            validation_errors=tuple(),
            latency_ms=None,
            input_tokens=None,
            output_tokens=None,
            estimated_cost_usd=None,
            error=last_error,
        )

    total_examples = len(examples)
    succeeded_examples = resumed_completed_count
    failed_examples = 0
    validated_examples = 0
    invalid_examples = 0
    total_input_tokens = 0
    total_output_tokens = 0
    total_cost_usd = 0.0
    latency_values_ms: list[float] = []

    processed_since_checkpoint = 0
    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_example: dict[Future[WorkerResult], DatasetExample] = {
            executor.submit(run_one, example): example for example in pending
        }

        for future in as_completed(future_to_example):
            example = future_to_example[future]
            result = future.result()

            base_row = {
                "run_id": run_id,
                "timestamp_utc": _utc_now(),
                "provider": resolved_provider,
                "model": teacher_model,
                "example_id": example.example_id,
                "attempts": result.attempts,
                "prompt_id": prompt_meta.get("prompt_id"),
                "prompt_version": prompt_meta.get("prompt_version"),
                "prompt_checksum_sha256": prompt_meta.get("prompt_checksum_sha256"),
                "temperature": temperature,
                "seed": seed,
            }

            if result.success:
                succeeded_examples += 1
                completed_ids.add(example.example_id)

                if result.input_tokens is not None:
                    total_input_tokens += result.input_tokens
                if result.output_tokens is not None:
                    total_output_tokens += result.output_tokens
                if result.estimated_cost_usd is not None:
                    total_cost_usd += float(result.estimated_cost_usd)
                if result.latency_ms is not None:
                    latency_values_ms.append(float(result.latency_ms))

                validation_passed = len(result.validation_errors) == 0
                if validation_passed:
                    validated_examples += 1
                else:
                    invalid_examples += 1

                row = {
                    **base_row,
                    "status": "success",
                    "validation_passed": validation_passed,
                    "validation_errors": list(result.validation_errors),
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "estimated_cost_usd": result.estimated_cost_usd,
                    "output": result.output,
                }
                _append_jsonl(responses_path, row)
            else:
                failed_examples += 1
                _append_jsonl(
                    failures_path,
                    {
                        **base_row,
                        "status": "failed",
                        "error": result.error,
                    },
                )

            processed_since_checkpoint += 1
            if processed_since_checkpoint >= checkpoint_every:
                processed_since_checkpoint = 0
                checkpoint = _build_checkpoint(
                    run_id=run_id,
                    dataset_path=dataset_path,
                    output_dir=output_dir,
                    config={
                        "provider": resolved_provider,
                        "teacher_model": teacher_model,
                        "prompt_id": prompt_meta.get("prompt_id"),
                        "prompt_version": prompt_meta.get("prompt_version"),
                        "max_workers": max_workers,
                        "request_max_attempts": request_max_attempts,
                        "strict_validation": strict_validation,
                    },
                    total_examples=total_examples,
                    completed_examples=succeeded_examples + failed_examples,
                    succeeded_examples=succeeded_examples,
                    failed_examples=failed_examples,
                    validated_examples=validated_examples,
                    invalid_examples=invalid_examples,
                    total_input_tokens=total_input_tokens,
                    total_output_tokens=total_output_tokens,
                    total_cost_usd=total_cost_usd,
                    latency_values_ms=latency_values_ms,
                    resumed_from=resume,
                )
                _atomic_write_json(checkpoint_path, checkpoint)
                tracker.log_event(
                    "checkpoint_saved",
                    {
                        "completed": checkpoint["counts"]["completed_examples"],
                        "pending": checkpoint["counts"]["pending_examples"],
                    },
                )

    elapsed_seconds = max(0.0, time.perf_counter() - start)
    avg_latency_ms = sum(latency_values_ms) / len(latency_values_ms) if latency_values_ms else None

    summary = {
        "run_id": run_id,
        "finished_at_utc": _utc_now(),
        "elapsed_seconds": elapsed_seconds,
        "dataset_path": str(dataset_path),
        "output_dir": str(output_dir),
        "provider": resolved_provider,
        "teacher_model": teacher_model,
        "prompt": prompt_meta,
        "resume": resume,
        "counts": {
            "total_examples": total_examples,
            "attempted_examples": len(pending),
            "resumed_already_completed": resumed_completed_count,
            "succeeded_in_run": max(0, succeeded_examples - resumed_completed_count),
            "succeeded_examples": succeeded_examples,
            "failed_examples": failed_examples,
            "completed_examples": succeeded_examples + failed_examples,
            "pending_examples": max(0, total_examples - (succeeded_examples + failed_examples)),
            "validated_examples": validated_examples,
            "invalid_examples": invalid_examples,
        },
        "usage": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_tokens": total_input_tokens + total_output_tokens,
            "estimated_cost_usd": round(total_cost_usd, 8),
        },
        "latency": {
            "average_ms": avg_latency_ms,
            "max_ms": max(latency_values_ms) if latency_values_ms else None,
            "min_ms": min(latency_values_ms) if latency_values_ms else None,
        },
        "artifacts": {
            "responses_jsonl": str(responses_path),
            "failures_jsonl": str(failures_path),
            "checkpoint_json": str(checkpoint_path),
            "metadata_json": str(metadata_path),
            "summary_json": str(summary_path),
            "experiment_tracker_dir": str(tracker.run_dir),
        },
    }

    checkpoint = _build_checkpoint(
        run_id=run_id,
        dataset_path=dataset_path,
        output_dir=output_dir,
        config={
            "provider": resolved_provider,
            "teacher_model": teacher_model,
            "prompt_id": prompt_meta.get("prompt_id"),
            "prompt_version": prompt_meta.get("prompt_version"),
            "max_workers": max_workers,
            "request_max_attempts": request_max_attempts,
            "strict_validation": strict_validation,
        },
        total_examples=total_examples,
        completed_examples=succeeded_examples + failed_examples,
        succeeded_examples=succeeded_examples,
        failed_examples=failed_examples,
        validated_examples=validated_examples,
        invalid_examples=invalid_examples,
        total_input_tokens=total_input_tokens,
        total_output_tokens=total_output_tokens,
        total_cost_usd=total_cost_usd,
        latency_values_ms=latency_values_ms,
        resumed_from=resume,
    )
    _atomic_write_json(checkpoint_path, checkpoint)
    _atomic_write_json(summary_path, summary)

    tracker.set_metrics(
        {
            "elapsed_seconds": elapsed_seconds,
            "counts": summary["counts"],
            "usage": summary["usage"],
            "latency": summary["latency"],
            "strict_validation": strict_validation,
            "resume": resume,
        },
        section="labeling",
    )
    tracker.log_event("labeling_finished", summary)
    tracker.finalize(status="completed")

    return summary


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for production labeling runner."""
    parser = argparse.ArgumentParser(description="Run production teacher labeling inference.")
    parser.add_argument("--dataset", default="datasets/final/merged_all.jsonl")
    parser.add_argument("--output-dir", default="outputs/teacher_runs/run_v1")
    parser.add_argument("--teacher-model", required=True)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--prompt-template", default="teacher_prompts/production_teacher.txt")
    parser.add_argument("--prompts-root", default="configs/prompts")
    parser.add_argument("--prompt-id", default=None)
    parser.add_argument("--prompt-version", default="active")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--max-workers", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    parser.add_argument("--request-max-attempts", type=int, default=3)
    parser.add_argument("--request-retry-backoff-seconds", type=float, default=1.0)
    parser.add_argument("--checkpoint-every", type=int, default=20)
    parser.add_argument("--schema-path", default="teacher_prompts/output_schema.json")
    parser.add_argument("--no-strict-validation", action="store_true")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--providers-config", default="configs/providers/providers_v1.json")
    parser.add_argument("--env-file", default=".env")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    run_id = _normalize_text(args.run_id)
    if not run_id:
        run_id = datetime.now(timezone.utc).strftime("labeling-%Y%m%dT%H%M%SZ")

    schema_path = Path(args.schema_path) if _normalize_text(args.schema_path) else None
    providers_config_path = _resolve_repo_relative_path(Path(args.providers_config))
    env_file_path = _resolve_repo_relative_path(Path(args.env_file))
    summary = run_labeling(
        dataset_path=Path(args.dataset),
        output_dir=Path(args.output_dir),
        teacher_model=str(args.teacher_model),
        provider=str(args.provider) if args.provider else None,
        prompt_template_path=Path(args.prompt_template) if args.prompt_template else None,
        prompts_root=Path(args.prompts_root),
        prompt_id=str(args.prompt_id) if args.prompt_id else None,
        prompt_version=str(args.prompt_version),
        temperature=float(args.temperature),
        seed=int(args.seed),
        timeout_seconds=float(args.timeout_seconds),
        max_output_tokens=int(args.max_output_tokens),
        max_workers=int(args.max_workers),
        request_max_attempts=int(args.request_max_attempts),
        request_retry_backoff_seconds=float(args.request_retry_backoff_seconds),
        checkpoint_every=max(1, int(args.checkpoint_every)),
        schema_path=schema_path,
        strict_validation=not bool(args.no_strict_validation),
        run_id=run_id,
        resume=bool(args.resume),
        providers_config_path=providers_config_path,
        env_file=env_file_path,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
