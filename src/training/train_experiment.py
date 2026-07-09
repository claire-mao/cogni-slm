"""Production experiment runner for QLoRA SFT training.

This module loads experiment configs from ``configs/training/experiments/`` and
runs each resolved experiment against ``datasets/sft/``.

Execution behavior:
- default mode plans runs and writes manifests only
- pass ``--do-train`` to execute training

When training is enabled, each run performs:
- train
- checkpoint save
- adapter save
- model merge (best-effort)
- evaluation
- metrics/log persistence
"""

from __future__ import annotations

import argparse
import copy
import itertools
import json
import os
import re
import traceback
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

try:
    from utils.experiment_tracker import ExperimentTracker, create_experiment_tracker
except ModuleNotFoundError:  # pragma: no cover - runtime import layout variance
    from src.utils.experiment_tracker import ExperimentTracker, create_experiment_tracker

DEFAULT_DATASET_ROOT = Path("datasets/sft")
DEFAULT_EXPERIMENTS_DIR = Path("configs/training/experiments")
DEFAULT_EXPERIMENT_MANIFEST = DEFAULT_EXPERIMENTS_DIR / "manifest.json"
DEFAULT_BASE_CONFIG = Path("configs/training/qlora_default.json")
DEFAULT_OUTPUT_ROOT = Path("outputs/training_experiments")
DEFAULT_TRACKING_ROOT = Path("outputs/experiments")

DEFAULT_BATCH_PROFILE_MAP: dict[str, dict[str, int]] = {
    "bsz16": {
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,
        "per_device_eval_batch_size": 2,
        "effective_batch_size": 16,
    },
    "bsz32": {
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 8,
        "per_device_eval_batch_size": 4,
        "effective_batch_size": 32,
    },
    "bsz64": {
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 16,
        "per_device_eval_batch_size": 4,
        "effective_batch_size": 64,
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return slug or "run"


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


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        payload = _read_json(path)
    except Exception:
        return None
    return payload


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _get_nested(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _dataset_version_from_path(path: Path) -> str | None:
    parts = list(path.parts)
    for index, item in enumerate(parts):
        if item != "versions":
            continue
        if index + 1 < len(parts):
            value = _normalize_text(parts[index + 1])
            if value:
                return value
    return None


def _manifest_candidates(dataset_path: Path) -> list[Path]:
    roots: list[Path] = []
    if dataset_path.is_dir():
        roots.extend([dataset_path, dataset_path.parent, dataset_path.parent.parent])
    else:
        roots.extend([dataset_path.parent, dataset_path.parent.parent])
    dedup: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        key = str(root.resolve())
        if key in seen:
            continue
        seen.add(key)
        dedup.append(root)
    manifests: list[Path] = []
    for root in dedup:
        manifests.extend(
            [
                root / "manifest.json",
                root / "sft_build_manifest.json",
                root / "run_manifest.json",
            ]
        )
    return manifests


def _extract_prediction_paths_from_manifests(manifests: list[dict[str, Any]]) -> list[Path]:
    candidates: list[str] = []
    for payload in manifests:
        if not isinstance(payload, dict):
            continue
        for keys in (
            ("teacher_outputs_path",),
            ("predictions_path",),
            ("canonical_manifest", "predictions_path"),
            ("canonical_manifest", "teacher_outputs_path"),
            ("inputs", "teacher_outputs_path"),
        ):
            value = _get_nested(payload, keys)
            if isinstance(value, str) and value.strip():
                candidates.append(value.strip())

    paths: list[Path] = []
    seen: set[str] = set()
    for raw in candidates:
        path = Path(raw)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        paths.append(path)
    return paths


def _extract_prompt_versions_from_predictions(path: Path, *, max_rows: int = 2000) -> list[str]:
    files: list[Path] = []
    if path.is_file():
        files = [path]
    elif path.is_dir():
        response_files = sorted(path.rglob("responses.jsonl"))
        if response_files:
            files = response_files
        else:
            files = sorted(path.rglob("*.jsonl"))
    versions: set[str] = set()
    rows_seen = 0
    for file_path in files:
        try:
            with file_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    if rows_seen >= max_rows:
                        break
                    raw = line.strip()
                    if not raw:
                        continue
                    rows_seen += 1
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(payload, dict):
                        continue
                    prompt_version = _normalize_text(payload.get("prompt_version"))
                    if prompt_version:
                        versions.add(prompt_version)
                if rows_seen >= max_rows:
                    break
        except OSError:
            continue
    return sorted(versions)


def _infer_tracking_context(
    config: ResolvedRunConfig,
) -> dict[str, str | None]:
    manifests = [
        payload
        for path in _manifest_candidates(config.dataset_path)
        for payload in [_read_json_if_exists(path)]
        if isinstance(payload, dict)
    ]

    dataset_version = _dataset_version_from_path(config.dataset_path)
    if not dataset_version:
        for payload in manifests:
            for keys in (
                ("version",),
                ("dataset_version",),
                ("sft_version",),
                ("canonical_manifest", "dataset_version"),
                ("canonical_manifest", "version"),
            ):
                value = _get_nested(payload, keys)
                normalized = _normalize_text(value)
                if normalized:
                    dataset_version = normalized
                    break
            if dataset_version:
                break

    teacher_version = _normalize_text(
        config.parameters.get("teacher_version")
        or config.parameters.get("teacher_model_id")
    )
    if not teacher_version:
        for payload in manifests:
            for keys in (
                ("teacher_version",),
                ("teacher_model_id",),
                ("canonical_manifest", "teacher_model_id"),
                ("stage_manifests", "teacher", "teacher_model_id"),
                ("stage_manifests", "teacher", "teacher_version"),
            ):
                value = _get_nested(payload, keys)
                normalized = _normalize_text(value)
                if normalized:
                    teacher_version = normalized
                    break
            if teacher_version:
                break
    if not teacher_version:
        teacher_version = "unknown"

    prompt_version = _normalize_text(
        config.parameters.get("prompt_version")
        or config.parameters.get("prompt_version_id")
    )
    if not prompt_version:
        for payload in manifests:
            for keys in (
                ("prompt_version",),
                ("prompt_version_id",),
                ("canonical_manifest", "prompt_version"),
                ("stage_manifests", "teacher", "prompt_version"),
            ):
                value = _get_nested(payload, keys)
                normalized = _normalize_text(value)
                if normalized:
                    prompt_version = normalized
                    break
            if prompt_version:
                break

    if not prompt_version:
        prediction_paths = _extract_prediction_paths_from_manifests(manifests)
        for prediction_path in prediction_paths:
            versions = _extract_prompt_versions_from_predictions(prediction_path)
            if not versions:
                continue
            if len(versions) == 1:
                prompt_version = versions[0]
            else:
                prompt_version = ",".join(versions[:5])
            break
    if not prompt_version:
        prompt_version = "unknown"

    return {
        "dataset_version": dataset_version or "unknown",
        "teacher_version": teacher_version,
        "prompt_version": prompt_version,
    }


def _deep_update(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            base[key] = _deep_update(base[key], value)
        else:
            base[key] = value
    return base


@dataclass(frozen=True)
class RunnerConfig:
    """Top-level runtime options for experiment orchestration."""

    dataset_root: Path
    experiments_dir: Path
    manifest_path: Path | None
    base_config_path: Path
    output_root: Path
    tracking_root: Path
    plan_id: str
    do_train: bool
    skip_merge: bool
    phase_ids: tuple[str, ...]
    run_filter: str | None
    max_runs: int
    seed_mode: str
    seed_values: tuple[int, ...]
    phase3_shard_id: str | None
    train_split: str
    eval_split: str
    test_split: str
    max_train_samples: int
    max_eval_samples: int
    max_test_samples: int
    resume_from_checkpoint: str | None


@dataclass(frozen=True)
class ExperimentRun:
    """One expanded run from an experiment config file."""

    source_file: str
    phase_id: str
    run_id: str
    parameters: dict[str, Any]
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ResolvedRunConfig:
    """Fully resolved one-run training configuration."""

    run_id: str
    source_file: str
    phase_id: str
    parameters: dict[str, Any]

    model_id: str
    dataset_path: Path
    train_split: str
    eval_split: str
    test_split: str
    max_train_samples: int
    max_eval_samples: int
    max_test_samples: int

    qlora: dict[str, Any]
    trainer: dict[str, Any]
    packing: bool
    optimizer: str

    run_dir: Path
    checkpoints_dir: Path
    adapters_dir: Path
    merged_model_dir: Path
    logs_dir: Path
    metrics_dir: Path
    manifest_path: Path
    resolved_config_path: Path


@dataclass(frozen=True)
class RunResult:
    """Per-run execution result and summary."""

    run_id: str
    source_file: str
    phase_id: str
    status: str
    training_started: bool
    train_seconds: float
    train_rows: int
    eval_rows: int
    test_rows: int
    train_metrics: dict[str, Any]
    eval_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    merge_status: str
    run_dir: str
    tracker_experiment_id: str | None
    tracker_run_dir: str | None
    dataset_version: str | None
    teacher_version: str | None
    prompt_version: str | None
    error: str | None


def _cartesian_axes(axes: dict[str, list[Any]]) -> list[dict[str, Any]]:
    axis_items = list(axes.items())
    if not axis_items:
        return [{}]
    keys = [item[0] for item in axis_items]
    values = [item[1] if isinstance(item[1], list) else [item[1]] for item in axis_items]
    rows: list[dict[str, Any]] = []
    for combo in itertools.product(*values):
        rows.append(dict(zip(keys, combo, strict=True)))
    return rows


def _discover_batch_profiles(
    payloads: list[tuple[Path, dict[str, Any]]],
) -> dict[str, dict[str, int]]:
    profiles: dict[str, dict[str, int]] = copy.deepcopy(DEFAULT_BATCH_PROFILE_MAP)

    for _path, payload in payloads:
        phase3_map = payload.get("batch_profile_map")
        if isinstance(phase3_map, dict):
            for profile_id, profile_data in phase3_map.items():
                if isinstance(profile_id, str) and isinstance(profile_data, dict):
                    profiles[profile_id] = {
                        key: _safe_int(value)
                        for key, value in profile_data.items()
                        if key
                    }

        comparison_axes = payload.get("comparison_axes")
        if isinstance(comparison_axes, dict):
            raw_profiles = comparison_axes.get("batch_profiles")
            if isinstance(raw_profiles, list):
                for row in raw_profiles:
                    if not isinstance(row, dict):
                        continue
                    profile_id = _normalize_text(row.get("batch_profile_id"))
                    if not profile_id:
                        continue
                    profiles[profile_id] = {
                        key: _safe_int(value)
                        for key, value in row.items()
                        if isinstance(key, str)
                    }
    return profiles


def _filter_phase(phase_id: str, phase_filters: tuple[str, ...]) -> bool:
    if not phase_filters:
        return True
    return phase_id in set(phase_filters)


def _expand_phase1_runs(
    *,
    file_path: Path,
    payload: dict[str, Any],
    phase_filters: tuple[str, ...],
) -> list[ExperimentRun]:
    phase_id = _normalize_text(payload.get("phase_id")) or "phase1"
    if not _filter_phase(phase_id, phase_filters):
        return []

    baseline = payload.get("baseline")
    runs = payload.get("runs")
    if not isinstance(baseline, dict) or not isinstance(runs, list):
        return []

    rows: list[ExperimentRun] = []
    for index, run in enumerate(runs, start=1):
        if not isinstance(run, dict):
            continue
        run_id = _normalize_text(run.get("run_id")) or f"{phase_id}_{index:04d}"
        overrides = run.get("overrides")
        if not isinstance(overrides, dict):
            overrides = {}
        params = copy.deepcopy(baseline)
        params.update(overrides)
        rows.append(
            ExperimentRun(
                source_file=str(file_path),
                phase_id=phase_id,
                run_id=run_id,
                parameters=params,
                metadata={"index": index, "kind": "phase1"},
            )
        )
    return rows


def _expand_phase2_runs(
    *,
    file_path: Path,
    payload: dict[str, Any],
    phase_filters: tuple[str, ...],
) -> list[ExperimentRun]:
    phase_id = _normalize_text(payload.get("phase_id")) or "phase2"
    if not _filter_phase(phase_id, phase_filters):
        return []

    blocks = payload.get("blocks")
    if not isinstance(blocks, list):
        return []

    rows: list[ExperimentRun] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_id = _normalize_text(block.get("block_id")) or "block"
        axes = block.get("axes")
        fixed = block.get("fixed")
        if not isinstance(axes, dict):
            continue
        if not isinstance(fixed, dict):
            fixed = {}

        combos = _cartesian_axes(axes)
        for index, combo in enumerate(combos, start=1):
            params = copy.deepcopy(fixed)
            params.update(combo)
            run_id = f"{phase_id}_{block_id}_{index:04d}"
            rows.append(
                ExperimentRun(
                    source_file=str(file_path),
                    phase_id=phase_id,
                    run_id=run_id,
                    parameters=params,
                    metadata={
                        "block_id": block_id,
                        "index": index,
                        "kind": "phase2",
                    },
                )
            )
    return rows


def _apply_phase3_shard(
    axes: dict[str, list[Any]],
    payload: dict[str, Any],
    shard_id: str | None,
) -> dict[str, list[Any]]:
    resolved = copy.deepcopy(axes)
    if not shard_id:
        return resolved

    sharding_plan = payload.get("sharding_plan")
    if not isinstance(sharding_plan, list):
        raise ValueError("phase3 shard requested but sharding_plan not found")

    shard = None
    for row in sharding_plan:
        if isinstance(row, dict) and _normalize_text(row.get("shard_id")) == shard_id:
            shard = row
            break
    if shard is None:
        raise ValueError(f"phase3 shard_id not found: {shard_id}")

    for key in ("max_seq_length", "packing"):
        if key in shard:
            resolved[key] = [shard[key]]
    return resolved


def _expand_phase3_runs(
    *,
    file_path: Path,
    payload: dict[str, Any],
    phase_filters: tuple[str, ...],
    phase3_shard_id: str | None,
) -> list[ExperimentRun]:
    phase_id = _normalize_text(payload.get("phase_id")) or "phase3"
    if not _filter_phase(phase_id, phase_filters):
        return []

    axes = payload.get("axes")
    if not isinstance(axes, dict):
        return []

    resolved_axes = _apply_phase3_shard(axes, payload, phase3_shard_id)
    combos = _cartesian_axes(resolved_axes)

    rows: list[ExperimentRun] = []
    for index, combo in enumerate(combos, start=1):
        run_id = f"{phase_id}_{index:06d}"
        rows.append(
            ExperimentRun(
                source_file=str(file_path),
                phase_id=phase_id,
                run_id=run_id,
                parameters=combo,
                metadata={"index": index, "kind": "phase3"},
            )
        )
    return rows


def _expand_matrix_runs(
    *,
    file_path: Path,
    payload: dict[str, Any],
    phase_filters: tuple[str, ...],
) -> list[ExperimentRun]:
    matrix_id = _normalize_text(payload.get("matrix_id")) or "matrix"
    phase_id = f"matrix:{matrix_id}"
    if not _filter_phase(phase_id, phase_filters):
        return []

    comparison_axes = payload.get("comparison_axes")
    if not isinstance(comparison_axes, dict):
        return []

    axes: dict[str, list[Any]] = {}
    for key, value in comparison_axes.items():
        if key == "batch_profiles":
            if not isinstance(value, list):
                continue
            batch_ids = []
            for row in value:
                if isinstance(row, dict):
                    profile_id = _normalize_text(row.get("batch_profile_id"))
                    if profile_id:
                        batch_ids.append(profile_id)
            axes["batch_profile_id"] = batch_ids
            continue
        if isinstance(value, list):
            axes[key] = value

    combos = _cartesian_axes(axes)
    rows: list[ExperimentRun] = []
    for index, combo in enumerate(combos, start=1):
        run_id = f"{matrix_id}_{index:06d}"
        rows.append(
            ExperimentRun(
                source_file=str(file_path),
                phase_id=phase_id,
                run_id=run_id,
                parameters=combo,
                metadata={"index": index, "kind": "matrix"},
            )
        )
    return rows


def _expand_runs_from_payload(
    *,
    file_path: Path,
    payload: dict[str, Any],
    phase_filters: tuple[str, ...],
    phase3_shard_id: str | None,
) -> list[ExperimentRun]:
    rows: list[ExperimentRun] = []
    rows.extend(
        _expand_phase1_runs(
            file_path=file_path,
            payload=payload,
            phase_filters=phase_filters,
        )
    )
    rows.extend(
        _expand_phase2_runs(
            file_path=file_path,
            payload=payload,
            phase_filters=phase_filters,
        )
    )
    rows.extend(
        _expand_phase3_runs(
            file_path=file_path,
            payload=payload,
            phase_filters=phase_filters,
            phase3_shard_id=phase3_shard_id,
        )
    )
    rows.extend(
        _expand_matrix_runs(
            file_path=file_path,
            payload=payload,
            phase_filters=phase_filters,
        )
    )
    return rows


def _list_experiment_files(
    experiments_dir: Path,
    manifest_path: Path | None,
) -> list[Path]:
    files: list[Path] = []
    if manifest_path and manifest_path.exists():
        payload = _read_json(manifest_path)
        rows = payload.get("files")
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                raw_path = _normalize_text(row.get("path"))
                if not raw_path:
                    continue
                path = Path(raw_path)
                if not path.is_absolute():
                    path = Path.cwd() / path
                if path.exists() and path.is_file():
                    files.append(path)

    if not files:
        for candidate in sorted(experiments_dir.glob("*.json")):
            if candidate.name == "manifest.json":
                continue
            files.append(candidate)

    dedup: list[Path] = []
    seen: set[str] = set()
    for path in files:
        key = str(path.resolve())
        if key in seen:
            continue
        dedup.append(path)
        seen.add(key)
    return dedup


def _seed_values_from_payload(payload: dict[str, Any]) -> tuple[int, ...]:
    policies = payload.get("policies")
    if isinstance(policies, dict):
        seeds = policies.get("seed_candidates")
        if isinstance(seeds, list):
            parsed = [
                _safe_int(seed)
                for seed in seeds
                if _safe_float(seed) is not None
            ]
            if parsed:
                return tuple(parsed)

    counts = payload.get("counts")
    if isinstance(counts, dict):
        seeds = counts.get("seed_repeats")
        if isinstance(seeds, list):
            parsed = [
                _safe_int(seed)
                for seed in seeds
                if _safe_float(seed) is not None
            ]
            if parsed:
                return tuple(parsed)
    return ()


def _expand_seed_runs(
    runs: list[ExperimentRun],
    *,
    seed_mode: str,
    override_seeds: tuple[int, ...],
    payload_by_file: dict[str, dict[str, Any]],
) -> list[ExperimentRun]:
    if seed_mode != "expand":
        return runs

    expanded: list[ExperimentRun] = []
    for run in runs:
        payload = payload_by_file.get(run.source_file, {})
        seeds = override_seeds or _seed_values_from_payload(payload)
        if not seeds:
            seeds = (42,)

        for seed in seeds:
            params = copy.deepcopy(run.parameters)
            params["seed"] = int(seed)
            expanded.append(
                ExperimentRun(
                    source_file=run.source_file,
                    phase_id=run.phase_id,
                    run_id=f"{run.run_id}_seed{seed}",
                    parameters=params,
                    metadata={**run.metadata, "seed": int(seed)},
                )
            )
    return expanded


def _pick_value(parameters: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in parameters:
            return parameters[key]
    return None


def _resolve_run_config(
    *,
    base_config: dict[str, Any],
    run: ExperimentRun,
    run_index: int,
    runner: RunnerConfig,
    batch_profiles: dict[str, dict[str, int]],
) -> ResolvedRunConfig:
    payload = copy.deepcopy(base_config)
    payload = _deep_update(payload, {})

    qlora = copy.deepcopy(payload.get("qlora", {}))
    trainer = copy.deepcopy(payload.get("trainer", {}))
    dataset = copy.deepcopy(payload.get("dataset", {}))

    params = copy.deepcopy(run.parameters)

    lora_r = _pick_value(params, "lora_rank", "lora_r")
    if lora_r is not None:
        qlora["lora_r"] = _safe_int(lora_r, default=_safe_int(qlora.get("lora_r"), default=16))

    lora_alpha = _pick_value(params, "lora_alpha")
    if lora_alpha is not None:
        qlora["lora_alpha"] = _safe_int(
            lora_alpha,
            default=_safe_int(qlora.get("lora_alpha"), default=16),
        )

    lora_alpha_policy = _normalize_text(_pick_value(params, "lora_alpha_policy") or "")
    if not lora_alpha_policy and isinstance(params.get("policies"), dict):
        lora_alpha_policy = _normalize_text(params["policies"].get("lora_alpha_policy"))
    if lora_alpha_policy == "match_rank":
        qlora["lora_alpha"] = _safe_int(qlora.get("lora_r"), default=16)

    max_seq_length = _pick_value(params, "max_seq_length")
    if max_seq_length is not None:
        qlora["max_seq_length"] = _safe_int(
            max_seq_length,
            default=_safe_int(qlora.get("max_seq_length"), default=2048),
        )

    learning_rate = _pick_value(params, "learning_rate")
    if learning_rate is not None:
        trainer["learning_rate"] = float(learning_rate)

    epochs = _pick_value(params, "num_train_epochs", "epochs")
    if epochs is not None:
        trainer["num_train_epochs"] = float(epochs)

    warmup_ratio = _pick_value(params, "warmup_ratio")
    if warmup_ratio is not None:
        trainer["warmup_ratio"] = float(warmup_ratio)

    seed = _pick_value(params, "seed")
    if seed is not None:
        trainer["seed"] = _safe_int(seed, default=_safe_int(trainer.get("seed"), default=42))
        qlora["random_state"] = _safe_int(seed, default=_safe_int(qlora.get("random_state"), 42))

    batch_profile_id = _normalize_text(_pick_value(params, "batch_profile_id") or "")
    if batch_profile_id:
        profile = batch_profiles.get(batch_profile_id)
        if profile is None:
            raise ValueError(f"Unknown batch_profile_id '{batch_profile_id}' in run '{run.run_id}'")
        trainer["per_device_train_batch_size"] = _safe_int(
            profile.get("per_device_train_batch_size"),
            default=_safe_int(trainer.get("per_device_train_batch_size"), default=2),
        )
        trainer["gradient_accumulation_steps"] = _safe_int(
            profile.get("gradient_accumulation_steps"),
            default=_safe_int(trainer.get("gradient_accumulation_steps"), default=8),
        )
        trainer["per_device_eval_batch_size"] = _safe_int(
            profile.get("per_device_eval_batch_size"),
            default=_safe_int(trainer.get("per_device_eval_batch_size"), default=2),
        )

    for key in (
        "per_device_train_batch_size",
        "per_device_eval_batch_size",
        "gradient_accumulation_steps",
        "eval_steps",
        "save_steps",
        "logging_steps",
        "save_total_limit",
    ):
        if key in params:
            trainer[key] = _safe_int(params[key], default=_safe_int(trainer.get(key), default=0))

    model_id = _normalize_text(_pick_value(params, "model_id") or payload.get("model_id"))
    if not model_id:
        model_id = "Qwen/Qwen3-1.7B-Instruct"

    packing = bool(_pick_value(params, "packing") or False)
    optimizer = _normalize_text(_pick_value(params, "optimizer") or "adamw_torch")

    run_slug = _safe_slug(run.run_id)
    run_dir = runner.output_root / runner.plan_id / f"{run_index:05d}_{run_slug}"
    checkpoints_dir = run_dir / "checkpoints"
    adapters_dir = run_dir / "adapters"
    merged_model_dir = run_dir / "merged_model"
    logs_dir = run_dir / "logs"
    metrics_dir = run_dir / "metrics"

    dataset_path = Path(runner.dataset_root)
    dataset["dataset_path"] = str(dataset_path)
    dataset["train_split"] = runner.train_split
    dataset["eval_split"] = runner.eval_split

    max_train_samples = runner.max_train_samples
    if max_train_samples <= 0:
        max_train_samples = _safe_int(dataset.get("max_train_samples"), default=0)

    max_eval_samples = runner.max_eval_samples
    if max_eval_samples <= 0:
        max_eval_samples = _safe_int(dataset.get("max_eval_samples"), default=0)

    return ResolvedRunConfig(
        run_id=run.run_id,
        source_file=run.source_file,
        phase_id=run.phase_id,
        parameters=params,
        model_id=model_id,
        dataset_path=dataset_path,
        train_split=runner.train_split,
        eval_split=runner.eval_split,
        test_split=runner.test_split,
        max_train_samples=max_train_samples,
        max_eval_samples=max_eval_samples,
        max_test_samples=runner.max_test_samples,
        qlora=qlora,
        trainer=trainer,
        packing=packing,
        optimizer=optimizer,
        run_dir=run_dir,
        checkpoints_dir=checkpoints_dir,
        adapters_dir=adapters_dir,
        merged_model_dir=merged_model_dir,
        logs_dir=logs_dir,
        metrics_dir=metrics_dir,
        manifest_path=run_dir / "run_manifest.json",
        resolved_config_path=run_dir / "resolved_config.json",
    )


def _format_example_to_text(example: dict[str, Any]) -> str:
    text_value = example.get("text")
    if isinstance(text_value, str) and text_value.strip():
        return text_value.strip()

    instruction = _normalize_text(example.get("instruction"))
    input_text = _normalize_text(example.get("input"))
    output_text = _normalize_text(example.get("output"))
    if instruction or input_text or output_text:
        return (
            f"Instruction:\n{instruction}\n\n"
            f"Input:\n{input_text}\n\n"
            f"Output:\n{output_text}"
        ).strip()

    prompt = _normalize_text(example.get("prompt"))
    essay = _normalize_text(example.get("essay"))
    score = _safe_float(example.get("score"))
    if prompt or essay or score is not None:
        score_text = f"{score:.4f}" if score is not None else "unknown"
        return (
            "You are an educational assessment teacher.\n\n"
            f"Prompt:\n{prompt}\n\n"
            f"Essay:\n{essay}\n\n"
            f"Target Score:\n{score_text}"
        ).strip()

    messages = example.get("messages")
    if isinstance(messages, list):
        blocks: list[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = _normalize_text(message.get("role") or message.get("from"))
            content = _normalize_text(message.get("content") or message.get("value"))
            if role and content:
                blocks.append(f"<{role}>\n{content}")
        if blocks:
            return "\n\n".join(blocks)

    return ""


def _load_jsonl_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL row must be an object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _load_sft_dataset_dict(config: ResolvedRunConfig) -> Any:
    """Load datasets DatasetDict from datasets/sft with flexible layouts."""
    try:
        from datasets import Dataset, DatasetDict, load_dataset, load_from_disk
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("datasets is required. Install with: pip install datasets") from exc

    root = config.dataset_path
    if not root.exists():
        raise FileNotFoundError(f"SFT dataset root not found: {root}")

    if root.is_dir():
        try:
            loaded = load_from_disk(str(root))
            if isinstance(loaded, DatasetDict):
                return loaded
            if isinstance(loaded, Dataset):
                return DatasetDict({config.train_split: loaded})
        except Exception:
            pass

        split_files: dict[str, str] = {}
        for split_name in (config.train_split, config.eval_split, config.test_split):
            direct_path = root / split_name / "data.jsonl"
            hf_path = root / "formats" / "huggingface" / f"{split_name}.jsonl"
            flat_path = root / f"{split_name}.jsonl"
            candidate = None
            for item in (direct_path, hf_path, flat_path):
                if item.exists() and item.is_file():
                    candidate = item
                    break
            if candidate is not None:
                split_files[split_name] = str(candidate)

        if split_files:
            loaded = load_dataset("json", data_files=split_files)
            return loaded

        rows = _load_jsonl_rows(root / "data.jsonl") if (root / "data.jsonl").exists() else []
        if rows:
            dataset = Dataset.from_list(rows)
            return DatasetDict({config.train_split: dataset})

    if root.is_file() and root.suffix.lower() in {".json", ".jsonl"}:
        loaded = load_dataset("json", data_files={config.train_split: str(root)})
        return loaded

    raise ValueError(f"Unsupported SFT dataset layout at {root}")


def _prepare_split(
    *,
    dataset_dict: Any,
    split_name: str,
    max_samples: int,
) -> Any | None:
    if split_name not in dataset_dict:
        return None

    dataset = dataset_dict[split_name]

    def map_text(example: dict[str, Any]) -> dict[str, Any]:
        return {"text": _format_example_to_text(example)}

    if "text" not in dataset.column_names:
        dataset = dataset.map(map_text, desc=f"build_text:{split_name}")

    dataset = dataset.filter(lambda row: _normalize_text(row.get("text")) != "")
    if max_samples > 0 and len(dataset) > max_samples:
        dataset = dataset.select(range(max_samples))

    if len(dataset) == 0:
        return None
    return dataset


def _training_dependencies() -> tuple[Any, Any, Any, Any]:
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("torch is required. Install with: pip install torch") from exc

    try:
        from transformers import TrainingArguments
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "transformers is required. Install with: pip install transformers"
        ) from exc

    try:
        from trl import SFTTrainer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("trl is required. Install with: pip install trl") from exc

    try:
        from unsloth import FastLanguageModel
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "unsloth is required. Install with: "
            "pip install 'unsloth[colab-new]' peft bitsandbytes accelerate"
        ) from exc

    return torch, TrainingArguments, SFTTrainer, FastLanguageModel


def _build_training_arguments(
    *,
    config: ResolvedRunConfig,
    has_eval: bool,
    resume_from_checkpoint: str | None,
    torch: Any,
    TrainingArguments: Any,
) -> Any:
    trainer = config.trainer

    bf16_available = bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported())
    fp16_available = bool(torch.cuda.is_available() and not bf16_available)
    evaluation_strategy = trainer.get("evaluation_strategy", "steps") if has_eval else "no"

    checkpoint_arg = resume_from_checkpoint or None

    return TrainingArguments(
        output_dir=str(config.checkpoints_dir),
        logging_dir=str(config.logs_dir),
        run_name=config.run_id,
        num_train_epochs=float(trainer.get("num_train_epochs", 1.0)),
        learning_rate=float(trainer.get("learning_rate", 2e-4)),
        weight_decay=float(trainer.get("weight_decay", 0.0)),
        warmup_ratio=float(trainer.get("warmup_ratio", 0.03)),
        lr_scheduler_type=str(trainer.get("lr_scheduler_type", "cosine")),
        seed=_safe_int(trainer.get("seed"), default=42),
        per_device_train_batch_size=_safe_int(
            trainer.get("per_device_train_batch_size"),
            default=2,
        ),
        per_device_eval_batch_size=_safe_int(
            trainer.get("per_device_eval_batch_size"),
            default=2,
        ),
        gradient_accumulation_steps=_safe_int(
            trainer.get("gradient_accumulation_steps"),
            default=8,
        ),
        evaluation_strategy=evaluation_strategy,
        eval_steps=_safe_int(trainer.get("eval_steps"), default=50),
        save_strategy=str(trainer.get("save_strategy", "steps")),
        save_steps=_safe_int(trainer.get("save_steps"), default=50),
        save_total_limit=_safe_int(trainer.get("save_total_limit"), default=3),
        logging_strategy=str(trainer.get("logging_strategy", "steps")),
        logging_steps=_safe_int(trainer.get("logging_steps"), default=10),
        report_to=trainer.get("report_to", []),
        fp16=fp16_available,
        bf16=bf16_available,
        remove_unused_columns=False,
        optim=config.optimizer,
        save_safetensors=True,
        resume_from_checkpoint=checkpoint_arg,
    )


def _save_log_history(path: Path, history: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in history:
            if isinstance(row, dict):
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _mean_from_log_history(history: list[dict[str, Any]], key: str) -> float | None:
    values: list[float] = []
    for row in history:
        if not isinstance(row, dict):
            continue
        value = _safe_float(row.get(key))
        if value is not None:
            values.append(value)
    if not values:
        return None
    return mean(values)


def _init_tracker(
    *,
    config: ResolvedRunConfig,
    resolved_payload: dict[str, Any],
    tracking_root: Path,
    tracking_context: dict[str, str | None],
) -> tuple[ExperimentTracker | None, str | None]:
    seed = _safe_int(config.trainer.get("seed"), default=42)
    notes = (
        f"dataset_version={tracking_context.get('dataset_version')}; "
        f"prompt_version={tracking_context.get('prompt_version')}"
    )
    try:
        tracker = create_experiment_tracker(
            experiment_name=config.run_id,
            dataset_path=config.dataset_path,
            teacher_version=_normalize_text(tracking_context.get("teacher_version")) or "unknown",
            training_config=resolved_payload,
            seed=seed,
            experiments_root=tracking_root,
            notes=notes,
        )
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

    tracker.log_event("tracking_context", copy.deepcopy(tracking_context))
    return tracker, None


def _execute_training_run(
    *,
    config: ResolvedRunConfig,
    do_train: bool,
    skip_merge: bool,
    tracking_root: Path,
    resume_from_checkpoint: str | None,
) -> RunResult:
    config.run_dir.mkdir(parents=True, exist_ok=True)
    tracking_context = _infer_tracking_context(config)

    resolved_payload = {
        "run_id": config.run_id,
        "source_file": config.source_file,
        "phase_id": config.phase_id,
        "parameters": config.parameters,
        "model_id": config.model_id,
        "dataset": {
            "dataset_path": str(config.dataset_path),
            "train_split": config.train_split,
            "eval_split": config.eval_split,
            "test_split": config.test_split,
            "max_train_samples": config.max_train_samples,
            "max_eval_samples": config.max_eval_samples,
            "max_test_samples": config.max_test_samples,
        },
        "qlora": config.qlora,
        "trainer": config.trainer,
        "runtime": {
            "packing": config.packing,
            "optimizer": config.optimizer,
            "do_train": bool(do_train),
            "skip_merge": bool(skip_merge),
            "resume_from_checkpoint": resume_from_checkpoint,
        },
        "paths": {
            "run_dir": str(config.run_dir),
            "checkpoints_dir": str(config.checkpoints_dir),
            "adapters_dir": str(config.adapters_dir),
            "merged_model_dir": str(config.merged_model_dir),
            "logs_dir": str(config.logs_dir),
            "metrics_dir": str(config.metrics_dir),
        },
        "lineage": tracking_context,
    }
    _write_json(config.resolved_config_path, resolved_payload)

    tracker, tracker_error = _init_tracker(
        config=config,
        resolved_payload=resolved_payload,
        tracking_root=tracking_root,
        tracking_context=tracking_context,
    )
    tracker_experiment_id = tracker.experiment_id if tracker else None
    tracker_run_dir = str(tracker.run_dir) if tracker else None

    if not do_train:
        if tracker:
            tracker.set_metrics(
                {
                    "status": "planned",
                    "training_started": False,
                    "rows": {"train": 0, "eval": 0, "test": 0},
                    "lineage": tracking_context,
                },
                section="evaluation",
            )
            tracker.finalize(status="planned", notes="training_started=False")

        manifest = {
            "run_id": config.run_id,
            "status": "planned",
            "training_started": False,
            "timestamp_utc": _utc_now(),
            "resolved_config_path": str(config.resolved_config_path),
            "tracking": {
                "experiment_id": tracker_experiment_id,
                "run_dir": tracker_run_dir,
                "error": tracker_error,
            },
            "lineage": tracking_context,
        }
        _write_json(config.manifest_path, manifest)
        return RunResult(
            run_id=config.run_id,
            source_file=config.source_file,
            phase_id=config.phase_id,
            status="planned",
            training_started=False,
            train_seconds=0.0,
            train_rows=0,
            eval_rows=0,
            test_rows=0,
            train_metrics={},
            eval_metrics={},
            test_metrics={},
            merge_status="not_started",
            run_dir=str(config.run_dir),
            tracker_experiment_id=tracker_experiment_id,
            tracker_run_dir=tracker_run_dir,
            dataset_version=tracking_context.get("dataset_version"),
            teacher_version=tracking_context.get("teacher_version"),
            prompt_version=tracking_context.get("prompt_version"),
            error=None,
        )

    start_time = datetime.now(timezone.utc)
    try:
        torch, TrainingArguments, SFTTrainer, FastLanguageModel = _training_dependencies()

        dataset_dict = _load_sft_dataset_dict(config)
        train_dataset = _prepare_split(
            dataset_dict=dataset_dict,
            split_name=config.train_split,
            max_samples=config.max_train_samples,
        )
        if train_dataset is None:
            raise ValueError(f"Training split '{config.train_split}' is empty or unavailable")

        eval_dataset = _prepare_split(
            dataset_dict=dataset_dict,
            split_name=config.eval_split,
            max_samples=config.max_eval_samples,
        )
        test_dataset = _prepare_split(
            dataset_dict=dataset_dict,
            split_name=config.test_split,
            max_samples=config.max_test_samples,
        )

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=config.model_id,
            max_seq_length=_safe_int(config.qlora.get("max_seq_length"), default=2048),
            dtype=None,
            load_in_4bit=bool(config.qlora.get("load_in_4bit", True)),
        )

        model = FastLanguageModel.get_peft_model(
            model,
            r=_safe_int(config.qlora.get("lora_r"), default=16),
            target_modules=config.qlora.get(
                "target_modules",
                [
                    "q_proj",
                    "k_proj",
                    "v_proj",
                    "o_proj",
                    "gate_proj",
                    "up_proj",
                    "down_proj",
                ],
            ),
            lora_alpha=_safe_int(config.qlora.get("lora_alpha"), default=16),
            lora_dropout=float(config.qlora.get("lora_dropout", 0.0)),
            bias=str(config.qlora.get("bias", "none")),
            use_gradient_checkpointing=config.qlora.get(
                "use_gradient_checkpointing",
                "unsloth",
            ),
            random_state=_safe_int(config.qlora.get("random_state"), default=42),
        )

        training_args = _build_training_arguments(
            config=config,
            has_eval=eval_dataset is not None,
            resume_from_checkpoint=resume_from_checkpoint,
            torch=torch,
            TrainingArguments=TrainingArguments,
        )

        trainer = SFTTrainer(
            model=model,
            tokenizer=tokenizer,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            dataset_text_field="text",
            max_seq_length=_safe_int(config.qlora.get("max_seq_length"), default=2048),
            packing=bool(config.packing),
            args=training_args,
        )

        train_output = trainer.train(
            resume_from_checkpoint=resume_from_checkpoint if resume_from_checkpoint else None
        )

        config.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        trainer.save_model(str(config.checkpoints_dir))
        trainer.save_state()
        tokenizer.save_pretrained(str(config.checkpoints_dir))

        config.adapters_dir.mkdir(parents=True, exist_ok=True)
        trainer.model.save_pretrained(str(config.adapters_dir))
        tokenizer.save_pretrained(str(config.adapters_dir))

        eval_metrics: dict[str, Any] = {}
        if eval_dataset is not None:
            eval_metrics = dict(trainer.evaluate())

        test_metrics: dict[str, Any] = {}
        if test_dataset is not None:
            test_metrics = dict(
                trainer.evaluate(
                    eval_dataset=test_dataset,
                    metric_key_prefix="test",
                )
            )

        merge_status = "skipped"
        if not skip_merge:
            merge_status = "unsupported"
            try:
                if hasattr(trainer.model, "merge_and_unload"):
                    merged = trainer.model.merge_and_unload()
                    config.merged_model_dir.mkdir(parents=True, exist_ok=True)
                    merged.save_pretrained(str(config.merged_model_dir), safe_serialization=True)
                    tokenizer.save_pretrained(str(config.merged_model_dir))
                    merge_status = "ok"
            except Exception as merge_exc:  # pragma: no cover - runtime variability
                merge_status = f"failed:{type(merge_exc).__name__}"

        train_metrics = dict(train_output.metrics or {})

        history = trainer.state.log_history if trainer.state and trainer.state.log_history else []
        _save_log_history(config.logs_dir / "trainer_log_history.jsonl", history)

        runtime_seconds = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()

        train_metrics.setdefault("runtime_seconds_wall", runtime_seconds)
        train_metrics.setdefault("train_loss_mean", _mean_from_log_history(history, "loss"))

        _write_json(config.metrics_dir / "train_metrics.json", train_metrics)
        _write_json(config.metrics_dir / "eval_metrics.json", eval_metrics)
        _write_json(config.metrics_dir / "test_metrics.json", test_metrics)

        manifest = {
            "run_id": config.run_id,
            "source_file": config.source_file,
            "phase_id": config.phase_id,
            "status": "completed",
            "training_started": True,
            "timestamp_utc": _utc_now(),
            "runtime_seconds": runtime_seconds,
            "rows": {
                "train": int(len(train_dataset)),
                "eval": int(len(eval_dataset)) if eval_dataset is not None else 0,
                "test": int(len(test_dataset)) if test_dataset is not None else 0,
            },
            "merge_status": merge_status,
            "paths": {
                "resolved_config": str(config.resolved_config_path),
                "checkpoints_dir": str(config.checkpoints_dir),
                "adapters_dir": str(config.adapters_dir),
                "merged_model_dir": str(config.merged_model_dir),
                "train_metrics": str(config.metrics_dir / "train_metrics.json"),
                "eval_metrics": str(config.metrics_dir / "eval_metrics.json"),
                "test_metrics": str(config.metrics_dir / "test_metrics.json"),
                "trainer_log_history": str(config.logs_dir / "trainer_log_history.jsonl"),
            },
            "tracking": {
                "experiment_id": tracker_experiment_id,
                "run_dir": tracker_run_dir,
                "error": tracker_error,
            },
            "lineage": tracking_context,
        }
        _write_json(config.manifest_path, manifest)

        if tracker:
            tracker.set_metrics(
                {
                    "status": "completed",
                    "runtime_seconds": runtime_seconds,
                    "rows": {
                        "train": int(len(train_dataset)),
                        "eval": int(len(eval_dataset)) if eval_dataset is not None else 0,
                        "test": int(len(test_dataset)) if test_dataset is not None else 0,
                    },
                    "merge_status": merge_status,
                    "train_metrics": train_metrics,
                    "eval_metrics": eval_metrics,
                    "test_metrics": test_metrics,
                    "lineage": tracking_context,
                },
                section="evaluation",
            )
            tracker.finalize(status="completed")

        # Opportunistic cleanup between long runs.
        del trainer
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return RunResult(
            run_id=config.run_id,
            source_file=config.source_file,
            phase_id=config.phase_id,
            status="completed",
            training_started=True,
            train_seconds=runtime_seconds,
            train_rows=int(len(train_dataset)),
            eval_rows=int(len(eval_dataset)) if eval_dataset is not None else 0,
            test_rows=int(len(test_dataset)) if test_dataset is not None else 0,
            train_metrics=train_metrics,
            eval_metrics=eval_metrics,
            test_metrics=test_metrics,
            merge_status=merge_status,
            run_dir=str(config.run_dir),
            tracker_experiment_id=tracker_experiment_id,
            tracker_run_dir=tracker_run_dir,
            dataset_version=tracking_context.get("dataset_version"),
            teacher_version=tracking_context.get("teacher_version"),
            prompt_version=tracking_context.get("prompt_version"),
            error=None,
        )
    except Exception as exc:  # pragma: no cover - runtime variability
        runtime_seconds = (
            datetime.now(timezone.utc) - start_time
        ).total_seconds()
        error_text = f"{type(exc).__name__}: {exc}"
        _write_json(
            config.manifest_path,
            {
                "run_id": config.run_id,
                "status": "failed",
                "training_started": True,
                "timestamp_utc": _utc_now(),
                "runtime_seconds": runtime_seconds,
                "error": error_text,
                "traceback": traceback.format_exc(),
                "tracking": {
                    "experiment_id": tracker_experiment_id,
                    "run_dir": tracker_run_dir,
                    "error": tracker_error,
                },
                "lineage": tracking_context,
            },
        )
        if tracker:
            tracker.set_metrics(
                {
                    "status": "failed",
                    "runtime_seconds": runtime_seconds,
                    "error": error_text,
                    "lineage": tracking_context,
                },
                section="evaluation",
            )
            tracker.finalize(status="failed", notes=error_text)
        return RunResult(
            run_id=config.run_id,
            source_file=config.source_file,
            phase_id=config.phase_id,
            status="failed",
            training_started=True,
            train_seconds=runtime_seconds,
            train_rows=0,
            eval_rows=0,
            test_rows=0,
            train_metrics={},
            eval_metrics={},
            test_metrics={},
            merge_status="failed",
            run_dir=str(config.run_dir),
            tracker_experiment_id=tracker_experiment_id,
            tracker_run_dir=tracker_run_dir,
            dataset_version=tracking_context.get("dataset_version"),
            teacher_version=tracking_context.get("teacher_version"),
            prompt_version=tracking_context.get("prompt_version"),
            error=error_text,
        )


def _resolve_runs(runner: RunnerConfig) -> tuple[list[ResolvedRunConfig], dict[str, Any]]:
    base_config = _read_json(runner.base_config_path)

    files = _list_experiment_files(
        experiments_dir=runner.experiments_dir,
        manifest_path=runner.manifest_path,
    )
    if not files:
        raise FileNotFoundError("No experiment config files found")

    payloads: list[tuple[Path, dict[str, Any]]] = []
    payload_by_file: dict[str, dict[str, Any]] = {}
    for path in files:
        payload = _read_json(path)
        payloads.append((path, payload))
        payload_by_file[str(path)] = payload

    batch_profiles = _discover_batch_profiles(payloads)

    raw_runs: list[ExperimentRun] = []
    for path, payload in payloads:
        raw_runs.extend(
            _expand_runs_from_payload(
                file_path=path,
                payload=payload,
                phase_filters=runner.phase_ids,
                phase3_shard_id=runner.phase3_shard_id,
            )
        )

    raw_runs = _expand_seed_runs(
        raw_runs,
        seed_mode=runner.seed_mode,
        override_seeds=runner.seed_values,
        payload_by_file=payload_by_file,
    )

    if runner.run_filter:
        needle = runner.run_filter.lower()
        raw_runs = [row for row in raw_runs if needle in row.run_id.lower()]

    if runner.max_runs > 0:
        raw_runs = raw_runs[: runner.max_runs]

    resolved: list[ResolvedRunConfig] = []
    for index, run in enumerate(raw_runs, start=1):
        resolved.append(
            _resolve_run_config(
                base_config=base_config,
                run=run,
                run_index=index,
                runner=runner,
                batch_profiles=batch_profiles,
            )
        )

    plan = {
        "plan_id": runner.plan_id,
        "created_at_utc": _utc_now(),
        "dataset_root": str(runner.dataset_root),
        "tracking_root": str(runner.tracking_root),
        "experiments_dir": str(runner.experiments_dir),
        "manifest_path": str(runner.manifest_path) if runner.manifest_path else None,
        "base_config_path": str(runner.base_config_path),
        "output_root": str(runner.output_root),
        "do_train": runner.do_train,
        "skip_merge": runner.skip_merge,
        "phase_ids": list(runner.phase_ids),
        "run_filter": runner.run_filter,
        "max_runs": runner.max_runs,
        "seed_mode": runner.seed_mode,
        "seed_values": list(runner.seed_values),
        "phase3_shard_id": runner.phase3_shard_id,
        "runs_total": len(resolved),
        "runs": [
            {
                "run_id": row.run_id,
                "phase_id": row.phase_id,
                "source_file": row.source_file,
                "run_dir": str(row.run_dir),
            }
            for row in resolved
        ],
    }
    return resolved, plan


def run_experiments(runner: RunnerConfig) -> dict[str, Any]:
    """Resolve and execute training experiments."""
    resolved_runs, plan = _resolve_runs(runner)

    plan_dir = runner.output_root / runner.plan_id
    plan_dir.mkdir(parents=True, exist_ok=True)
    _write_json(plan_dir / "plan_manifest.json", plan)

    results: list[RunResult] = []
    for row in resolved_runs:
        result = _execute_training_run(
            config=row,
            do_train=runner.do_train,
            skip_merge=runner.skip_merge,
            tracking_root=runner.tracking_root,
            resume_from_checkpoint=runner.resume_from_checkpoint,
        )
        results.append(result)

    summary = {
        "plan_id": runner.plan_id,
        "created_at_utc": _utc_now(),
        "do_train": runner.do_train,
        "tracking_root": str(runner.tracking_root),
        "runs_requested": len(resolved_runs),
        "runs_completed": sum(1 for row in results if row.status == "completed"),
        "runs_planned": sum(1 for row in results if row.status == "planned"),
        "runs_failed": sum(1 for row in results if row.status == "failed"),
        "runs_with_tracking": sum(1 for row in results if row.tracker_experiment_id),
        "output_dir": str(plan_dir),
        "results": [asdict(row) for row in results],
    }

    _write_json(plan_dir / "run_summary.json", summary)
    _write_jsonl(plan_dir / "run_results.jsonl", [asdict(row) for row in results])
    return summary


def _parse_csv_ints(raw: str) -> tuple[int, ...]:
    parts = [_normalize_text(part) for part in raw.split(",") if _normalize_text(part)]
    if not parts:
        return ()
    return tuple(_safe_int(part) for part in parts)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run production QLoRA experiment runner.")
    parser.add_argument("--dataset-root", default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument("--experiments-dir", default=str(DEFAULT_EXPERIMENTS_DIR))
    parser.add_argument("--manifest-path", default=str(DEFAULT_EXPERIMENT_MANIFEST))
    parser.add_argument("--base-config", default=str(DEFAULT_BASE_CONFIG))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--tracking-root", default=str(DEFAULT_TRACKING_ROOT))
    parser.add_argument("--plan-id", default="")

    parser.add_argument("--do-train", action="store_true")
    parser.add_argument("--skip-merge", action="store_true")
    parser.add_argument("--resume-from-checkpoint", default="")

    parser.add_argument(
        "--phase-id",
        action="append",
        default=[],
        help="Repeatable filter. Examples: phase1_ofat_screening, phase2_interactions",
    )
    parser.add_argument("--phase3-shard-id", default="")
    parser.add_argument("--run-filter", default="")
    parser.add_argument("--max-runs", type=int, default=0)

    parser.add_argument("--seed-mode", choices=("base", "expand"), default="base")
    parser.add_argument("--seed-values", default="")

    parser.add_argument("--train-split", default="train")
    parser.add_argument("--eval-split", default="validation")
    parser.add_argument("--test-split", default="test")
    parser.add_argument("--max-train-samples", type=int, default=0)
    parser.add_argument("--max-eval-samples", type=int, default=0)
    parser.add_argument("--max-test-samples", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()

    plan_id = _normalize_text(args.plan_id)
    if not plan_id:
        plan_id = f"train-exp-{_timestamp_id()}"

    manifest_path = Path(args.manifest_path)
    if _normalize_text(args.manifest_path) == "":
        manifest_path = Path("")

    runner = RunnerConfig(
        dataset_root=Path(args.dataset_root),
        experiments_dir=Path(args.experiments_dir),
        manifest_path=(manifest_path if manifest_path.as_posix() else None),
        base_config_path=Path(args.base_config),
        output_root=Path(args.output_root),
        tracking_root=Path(args.tracking_root),
        plan_id=plan_id,
        do_train=bool(args.do_train),
        skip_merge=bool(args.skip_merge),
        phase_ids=tuple(_normalize_text(item) for item in args.phase_id if _normalize_text(item)),
        run_filter=_normalize_text(args.run_filter) or None,
        max_runs=max(0, int(args.max_runs)),
        seed_mode=str(args.seed_mode),
        seed_values=_parse_csv_ints(args.seed_values),
        phase3_shard_id=_normalize_text(args.phase3_shard_id) or None,
        train_split=_normalize_text(args.train_split) or "train",
        eval_split=_normalize_text(args.eval_split) or "validation",
        test_split=_normalize_text(args.test_split) or "test",
        max_train_samples=max(0, int(args.max_train_samples)),
        max_eval_samples=max(0, int(args.max_eval_samples)),
        max_test_samples=max(0, int(args.max_test_samples)),
        resume_from_checkpoint=(
            _normalize_text(args.resume_from_checkpoint)
            if _normalize_text(args.resume_from_checkpoint)
            else None
        ),
    )

    summary = run_experiments(runner)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))

    if not runner.do_train:
        print("training_started=False")


if __name__ == "__main__":
    # Keep tokenizer parallelism predictable in multi-run environments.
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    main()
