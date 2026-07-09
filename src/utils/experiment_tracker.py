"""Lightweight file-based experiment tracking utilities.

Tracks:
- git commit metadata
- dataset checksum
- teacher version
- training config
- evaluation metrics
- runtime
- GPU metadata
- seed

This module only records metadata and does not execute experiments.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .paths import repo_root

DEFAULT_EXPERIMENTS_ROOT = "outputs/experiments"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return slug or "experiment"


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _run_command(
    args: list[str],
    *,
    cwd: Path,
    timeout_seconds: int = 10,
) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except Exception as exc:  # pragma: no cover - subprocess variance
        return 1, "", f"{type(exc).__name__}: {exc}"
    return completed.returncode, completed.stdout.strip(), completed.stderr.strip()


@dataclass(frozen=True)
class GitMetadata:
    """Git metadata for one experiment run."""

    commit: str
    short_commit: str
    branch: str
    is_dirty: bool
    remote_url: str | None


@dataclass(frozen=True)
class DatasetChecksum:
    """Dataset checksum metadata for a tracked dataset path."""

    dataset_path: str
    checksum_sha256: str
    file_count: int
    total_bytes: int


@dataclass(frozen=True)
class RuntimeMetadata:
    """Runtime metadata recorded over an experiment lifecycle."""

    started_at_utc: str
    finished_at_utc: str | None = None
    duration_seconds: float | None = None
    hostname: str | None = None
    pid: int | None = None


@dataclass(frozen=True)
class GPUMetadata:
    """GPU metadata captured from torch and/or nvidia-smi."""

    available: bool
    count: int
    devices: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    backend: str = "none"


@dataclass(frozen=True)
class ExperimentManifest:
    """Top-level experiment manifest."""

    experiment_id: str
    experiment_name: str
    run_dir: str
    created_at_utc: str
    status: str
    git: GitMetadata
    dataset: DatasetChecksum
    teacher_version: str
    seed: int | None
    training_config: dict[str, Any]
    evaluation_metrics: dict[str, Any]
    runtime: RuntimeMetadata
    gpu: GPUMetadata
    notes: str = ""


def collect_git_metadata(*, root: Path | None = None) -> GitMetadata:
    """Collect git metadata from repository root."""
    resolved_root = repo_root(root)
    commit_code, commit_out, _ = _run_command(
        ["git", "rev-parse", "HEAD"],
        cwd=resolved_root,
    )
    short_code, short_out, _ = _run_command(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=resolved_root,
    )
    branch_code, branch_out, _ = _run_command(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=resolved_root,
    )
    status_code, status_out, _ = _run_command(
        ["git", "status", "--porcelain"],
        cwd=resolved_root,
    )
    remote_code, remote_out, _ = _run_command(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=resolved_root,
    )

    commit = commit_out if commit_code == 0 and commit_out else "unknown"
    short_commit = short_out if short_code == 0 and short_out else commit[:8]
    branch = branch_out if branch_code == 0 and branch_out else "unknown"
    is_dirty = bool(status_out) if status_code == 0 else False
    remote_url = remote_out if remote_code == 0 and remote_out else None

    return GitMetadata(
        commit=commit,
        short_commit=short_commit,
        branch=branch,
        is_dirty=is_dirty,
        remote_url=remote_url,
    )


def compute_dataset_checksum(dataset_path: Path) -> DatasetChecksum:
    """Compute content checksum for a dataset file or directory."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset path not found: {dataset_path}")

    hasher = hashlib.sha256()
    file_count = 0
    total_bytes = 0

    def digest_file(path: Path, rel: str) -> None:
        nonlocal file_count, total_bytes
        file_count += 1
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\x00")
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                hasher.update(chunk)
        hasher.update(b"\x00")

    if dataset_path.is_file():
        digest_file(dataset_path, dataset_path.name)
    else:
        for candidate in sorted(dataset_path.rglob("*")):
            if not candidate.is_file():
                continue
            rel = str(candidate.relative_to(dataset_path)).replace("\\", "/")
            digest_file(candidate, rel)

    return DatasetChecksum(
        dataset_path=str(dataset_path),
        checksum_sha256=hasher.hexdigest(),
        file_count=file_count,
        total_bytes=total_bytes,
    )


def detect_gpu_metadata() -> GPUMetadata:
    """Collect GPU metadata from torch and fallback to nvidia-smi."""
    # Try torch first for consistent training-runtime view.
    try:
        import torch
    except Exception:
        torch = None  # type: ignore[assignment]

    if torch is not None:
        try:
            if torch.cuda.is_available():
                count = int(torch.cuda.device_count())
                devices: list[dict[str, Any]] = []
                for index in range(count):
                    props = torch.cuda.get_device_properties(index)
                    devices.append(
                        {
                            "index": index,
                            "name": str(getattr(props, "name", "")),
                            "total_memory_bytes": int(getattr(props, "total_memory", 0)),
                            "multi_processor_count": int(
                                getattr(props, "multi_processor_count", 0)
                            ),
                            "compute_capability": (
                                int(getattr(props, "major", 0)),
                                int(getattr(props, "minor", 0)),
                            ),
                        }
                    )
                return GPUMetadata(
                    available=True,
                    count=count,
                    devices=tuple(devices),
                    backend="torch",
                )
        except Exception:
            pass

    # Fallback: nvidia-smi query.
    code, stdout, _ = _run_command(
        [
            "nvidia-smi",
            "--query-gpu=name,memory.total,driver_version",
            "--format=csv,noheader,nounits",
        ],
        cwd=Path.cwd(),
    )
    if code != 0 or not stdout:
        return GPUMetadata(available=False, count=0, devices=tuple(), backend="none")

    devices = []
    for index, row in enumerate(stdout.splitlines()):
        parts = [item.strip() for item in row.split(",")]
        if len(parts) < 3:
            continue
        memory_mb = _safe_float(parts[1])
        devices.append(
            {
                "index": index,
                "name": parts[0],
                "total_memory_mb": memory_mb,
                "driver_version": parts[2],
            }
        )
    return GPUMetadata(
        available=bool(devices),
        count=len(devices),
        devices=tuple(devices),
        backend="nvidia-smi",
    )


class ExperimentTracker:
    """Tracks and persists experiment metadata and metrics."""

    def __init__(
        self,
        *,
        experiment_name: str,
        dataset_path: str | Path,
        teacher_version: str,
        training_config: dict[str, Any],
        seed: int | None = None,
        experiments_root: str | Path = DEFAULT_EXPERIMENTS_ROOT,
        repo_root_path: str | Path | None = None,
        notes: str = "",
    ) -> None:
        name = _normalize_text(experiment_name)
        if not name:
            raise ValueError("experiment_name is required")
        teacher = _normalize_text(teacher_version)
        if not teacher:
            raise ValueError("teacher_version is required")

        self.repo_root = repo_root(repo_root_path)
        self.experiments_root = (self.repo_root / Path(experiments_root)).resolve()
        self.experiments_root.mkdir(parents=True, exist_ok=True)

        self.experiment_id = f"{_timestamp_id()}-{_safe_slug(name)}"
        self.run_dir = self.experiments_root / self.experiment_id
        self.run_dir.mkdir(parents=True, exist_ok=False)

        self.events_path = self.run_dir / "events.jsonl"
        self.metrics_path = self.run_dir / "evaluation_metrics.json"
        self.training_config_path = self.run_dir / "training_config.json"
        self.manifest_path = self.run_dir / "manifest.json"

        self._start_perf = time.perf_counter()
        self._started_at = _utc_now()
        self._finished_at: str | None = None
        self._status = "initialized"

        self._git = collect_git_metadata(root=self.repo_root)
        self._dataset = compute_dataset_checksum(Path(dataset_path))
        self._runtime = RuntimeMetadata(
            started_at_utc=self._started_at,
            hostname=_run_command(["hostname"], cwd=self.repo_root)[1] or None,
            pid=os.getpid(),
        )
        self._gpu = detect_gpu_metadata()

        self._teacher_version = teacher
        self._training_config = copy_jsonable(training_config)
        self._seed = int(seed) if seed is not None else None
        self._notes = notes
        self._evaluation_metrics: dict[str, Any] = {}

        self._write_training_config()
        self._write_manifest()
        self.log_event(
            "initialized",
            {
                "experiment_name": name,
                "dataset_path": self._dataset.dataset_path,
                "teacher_version": self._teacher_version,
                "seed": self._seed,
            },
        )

    def _manifest(self) -> ExperimentManifest:
        duration = None
        if self._finished_at is not None:
            duration = max(0.0, time.perf_counter() - self._start_perf)
        runtime = RuntimeMetadata(
            started_at_utc=self._runtime.started_at_utc,
            finished_at_utc=self._finished_at,
            duration_seconds=duration,
            hostname=self._runtime.hostname,
            pid=self._runtime.pid,
        )
        return ExperimentManifest(
            experiment_id=self.experiment_id,
            experiment_name=self.experiment_id.split("-", maxsplit=1)[1],
            run_dir=str(self.run_dir),
            created_at_utc=self._started_at,
            status=self._status,
            git=self._git,
            dataset=self._dataset,
            teacher_version=self._teacher_version,
            seed=self._seed,
            training_config=self._training_config,
            evaluation_metrics=self._evaluation_metrics,
            runtime=runtime,
            gpu=self._gpu,
            notes=self._notes,
        )

    def _write_manifest(self) -> None:
        payload = asdict(self._manifest())
        self.manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def _write_training_config(self) -> None:
        self.training_config_path.write_text(
            json.dumps(self._training_config, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def log_event(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Append one tracker event row."""
        row = {
            "timestamp_utc": _utc_now(),
            "event_type": _normalize_text(event_type) or "event",
            "payload": copy_jsonable(payload or {}),
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def set_metrics(self, metrics: dict[str, Any], *, section: str = "evaluation") -> None:
        """Set metrics for one section and persist manifest/metrics files."""
        key = _safe_slug(section)
        self._evaluation_metrics[key] = copy_jsonable(metrics)
        self.metrics_path.write_text(
            json.dumps(self._evaluation_metrics, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        self.log_event("metrics_updated", {"section": key})
        self._write_manifest()

    def finalize(self, *, status: str = "completed", notes: str = "") -> None:
        """Finalize tracker state and persist final manifest."""
        normalized_status = _normalize_text(status).lower() or "completed"
        self._status = normalized_status
        self._finished_at = _utc_now()
        if notes:
            merged = _normalize_text(f"{self._notes} {notes}")
            self._notes = merged
        self.log_event("finalized", {"status": self._status})
        self._write_manifest()

    def as_dict(self) -> dict[str, Any]:
        """Return current manifest payload as dictionary."""
        return asdict(self._manifest())


def copy_jsonable(value: Any) -> Any:
    """Deep-copy JSON-serializable data with stable conversion."""
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def create_experiment_tracker(
    *,
    experiment_name: str,
    dataset_path: str | Path,
    teacher_version: str,
    training_config: dict[str, Any],
    seed: int | None = None,
    experiments_root: str | Path = DEFAULT_EXPERIMENTS_ROOT,
    repo_root_path: str | Path | None = None,
    notes: str = "",
) -> ExperimentTracker:
    """Factory helper that returns initialized tracker and created folder."""
    return ExperimentTracker(
        experiment_name=experiment_name,
        dataset_path=dataset_path,
        teacher_version=teacher_version,
        training_config=training_config,
        seed=seed,
        experiments_root=experiments_root,
        repo_root_path=repo_root_path,
        notes=notes,
    )
