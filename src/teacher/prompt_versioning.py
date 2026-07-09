"""Production prompt version management for teacher pipelines.

This module manages prompt assets under ``configs/prompts/`` and supports:
- version IDs
- checksums
- changelogs
- rollback to prior versions
- automatic experiment-tracker logging hooks

The module does not execute model inference.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

DEFAULT_PROMPTS_ROOT = Path("configs/prompts")
_REGISTRY_FILE = "registry.json"
_PROMPTS_DIR = "prompts"
_CHANGELOGS_DIR = "changelogs"
_EVENTS_FILE = "events.jsonl"


class TrackerLike(Protocol):
    """Subset of ExperimentTracker API used by this module."""

    def log_event(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        """Append one event to experiment tracking artifacts."""


@dataclass(frozen=True)
class PromptVersionRecord:
    """Stored metadata for one prompt version."""

    prompt_id: str
    version_id: str
    created_at_utc: str
    checksum_sha256: str
    prompt_path: str
    metadata_path: str
    changelog: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RollbackRecord:
    """One rollback operation recorded in the registry."""

    prompt_id: str
    from_version: str
    to_version: str
    rolled_back_at_utc: str
    reason: str
    actor: str
    metadata: dict[str, Any] = field(default_factory=dict)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_slug(value: str, *, fallback: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return slug or fallback


def _stable_json(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def compute_checksum(prompt_text: str) -> str:
    """Compute SHA-256 checksum for prompt content."""
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


class PromptVersionManager:
    """File-backed prompt version manager under ``configs/prompts/``."""

    def __init__(self, prompts_root: str | Path = DEFAULT_PROMPTS_ROOT) -> None:
        self.prompts_root = Path(prompts_root)
        self.prompt_versions_root = self.prompts_root / _PROMPTS_DIR
        self.changelogs_root = self.prompts_root / _CHANGELOGS_DIR
        self.registry_path = self.prompts_root / _REGISTRY_FILE
        self.events_path = self.prompts_root / _EVENTS_FILE
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        self.prompt_versions_root.mkdir(parents=True, exist_ok=True)
        self.changelogs_root.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            _write_json(
                self.registry_path,
                {
                    "schema_version": "v1",
                    "created_at_utc": _utc_now(),
                    "updated_at_utc": _utc_now(),
                    "prompts": {},
                },
            )
        if not self.events_path.exists():
            self.events_path.write_text("", encoding="utf-8")

    def _load_registry(self) -> dict[str, Any]:
        return _read_json(self.registry_path)

    def _save_registry(self, payload: dict[str, Any]) -> None:
        payload["updated_at_utc"] = _utc_now()
        _write_json(self.registry_path, payload)

    def _append_event(self, event_type: str, payload: dict[str, Any]) -> None:
        row = {
            "timestamp_utc": _utc_now(),
            "event_type": _normalize_text(event_type) or "event",
            "payload": _stable_json(payload),
        }
        with self.events_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    def _canonical_prompt_id(self, prompt_id: str) -> str:
        normalized = _normalize_text(prompt_id).lower()
        if not normalized:
            raise ValueError("prompt_id is required")
        return _safe_slug(normalized, fallback="prompt")

    def _next_version_id(self, prompt_id: str) -> str:
        base = self.prompt_versions_root / prompt_id
        if not base.exists():
            return "v001"

        highest = 0
        for candidate in base.iterdir():
            if not candidate.is_dir():
                continue
            match = re.match(r"^v(\d+)$", candidate.name)
            if not match:
                continue
            highest = max(highest, int(match.group(1)))
        return f"v{highest + 1:03d}"

    def _changelog_path(self, prompt_id: str) -> Path:
        return self.changelogs_root / f"{prompt_id}.md"

    def _append_changelog_line(self, prompt_id: str, line: str) -> None:
        path = self._changelog_path(prompt_id)
        if not path.exists():
            header = [
                f"# Prompt Changelog: {prompt_id}",
                "",
                "This file is auto-maintained by PromptVersionManager.",
                "",
            ]
            path.write_text("\n".join(header), encoding="utf-8")
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line.rstrip() + "\n")

    def _build_record(
        self,
        *,
        prompt_id: str,
        version_id: str,
        payload: dict[str, Any],
    ) -> PromptVersionRecord:
        return PromptVersionRecord(
            prompt_id=prompt_id,
            version_id=version_id,
            created_at_utc=str(payload.get("created_at_utc", "")),
            checksum_sha256=str(payload.get("checksum_sha256", "")),
            prompt_path=str(payload.get("prompt_path", "")),
            metadata_path=str(payload.get("metadata_path", "")),
            changelog=str(payload.get("changelog", "")),
            metadata=_stable_json(payload.get("metadata", {})),
        )

    def register_prompt(
        self,
        *,
        prompt_id: str,
        prompt_text: str,
        changelog: str,
        metadata: dict[str, Any] | None = None,
        version_id: str | None = None,
        make_active: bool = True,
        overwrite: bool = False,
    ) -> PromptVersionRecord:
        """Register and persist one prompt version."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        resolved_version = (
            _safe_slug(_normalize_text(version_id), fallback="") if version_id else ""
        ) or self._next_version_id(canonical_id)

        version_dir = self.prompt_versions_root / canonical_id / resolved_version
        if version_dir.exists() and not overwrite:
            raise FileExistsError(
                f"Prompt version exists: prompt_id={canonical_id}, version_id={resolved_version}"
            )
        version_dir.mkdir(parents=True, exist_ok=True)

        prompt_path = version_dir / "prompt.txt"
        metadata_path = version_dir / "metadata.json"
        checksum = compute_checksum(prompt_text)
        metadata_payload = _stable_json(metadata or {})

        prompt_path.write_text(prompt_text, encoding="utf-8")

        created_at = _utc_now()
        version_payload = {
            "schema_version": "v1",
            "prompt_id": canonical_id,
            "version_id": resolved_version,
            "created_at_utc": created_at,
            "checksum_sha256": checksum,
            "prompt_path": str(prompt_path),
            "metadata_path": str(metadata_path),
            "changelog": _normalize_text(changelog),
            "metadata": metadata_payload,
        }
        _write_json(metadata_path, version_payload)

        registry = self._load_registry()
        prompts = registry.setdefault("prompts", {})
        prompt_entry = prompts.setdefault(
            canonical_id,
            {
                "latest_version": None,
                "active_version": None,
                "versions": {},
                "rollbacks": [],
            },
        )
        versions = prompt_entry.setdefault("versions", {})
        versions[resolved_version] = {
            "created_at_utc": created_at,
            "checksum_sha256": checksum,
            "prompt_path": str(prompt_path),
            "metadata_path": str(metadata_path),
            "changelog": _normalize_text(changelog),
            "metadata": metadata_payload,
        }
        prompt_entry["latest_version"] = resolved_version
        if make_active or not prompt_entry.get("active_version"):
            prompt_entry["active_version"] = resolved_version
        self._save_registry(registry)

        change_line = (
            f"- {created_at} | register | version={resolved_version} | "
            f"checksum={checksum[:12]} | {_normalize_text(changelog)}"
        )
        self._append_changelog_line(canonical_id, change_line)
        self._append_event(
            "prompt_registered",
            {
                "prompt_id": canonical_id,
                "version_id": resolved_version,
                "checksum_sha256": checksum,
                "active_version": prompt_entry.get("active_version"),
            },
        )

        return self._build_record(
            prompt_id=canonical_id,
            version_id=resolved_version,
            payload=versions[resolved_version],
        )

    def register_prompt_file(
        self,
        *,
        prompt_id: str,
        source_path: str | Path,
        changelog: str,
        metadata: dict[str, Any] | None = None,
        version_id: str | None = None,
        make_active: bool = True,
        overwrite: bool = False,
    ) -> PromptVersionRecord:
        """Register one prompt version from a text file."""
        path = Path(source_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        prompt_text = path.read_text(encoding="utf-8")
        merged_meta = dict(metadata or {})
        merged_meta.setdefault("source_path", str(path))
        return self.register_prompt(
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            changelog=changelog,
            metadata=merged_meta,
            version_id=version_id,
            make_active=make_active,
            overwrite=overwrite,
        )

    def list_versions(self, prompt_id: str) -> tuple[PromptVersionRecord, ...]:
        """List all versions for one prompt id."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        registry = self._load_registry()
        prompt_entry = registry.get("prompts", {}).get(canonical_id)
        if not isinstance(prompt_entry, dict):
            return ()
        versions = prompt_entry.get("versions")
        if not isinstance(versions, dict):
            return ()

        rows: list[PromptVersionRecord] = []
        for version_id, payload in sorted(versions.items()):
            if not isinstance(payload, dict):
                continue
            rows.append(
                self._build_record(
                    prompt_id=canonical_id,
                    version_id=str(version_id),
                    payload=payload,
                )
            )
        return tuple(rows)

    def get_version(
        self,
        *,
        prompt_id: str,
        version_id: str = "active",
    ) -> PromptVersionRecord:
        """Get one resolved prompt version record.

        ``version_id`` may be one of:
        - ``active``: current production target
        - ``latest``: most recently registered
        - explicit version id (example: ``v003``)
        """
        canonical_id = self._canonical_prompt_id(prompt_id)
        registry = self._load_registry()
        prompt_entry = registry.get("prompts", {}).get(canonical_id)
        if not isinstance(prompt_entry, dict):
            raise KeyError(f"Prompt id not found: {canonical_id}")

        resolved = _normalize_text(version_id) or "active"
        if resolved == "active":
            resolved = str(prompt_entry.get("active_version") or "")
        elif resolved == "latest":
            resolved = str(prompt_entry.get("latest_version") or "")
        resolved = _safe_slug(resolved, fallback="")
        if not resolved:
            raise KeyError(
                f"No resolved version for prompt_id={canonical_id}, requested={version_id}"
            )

        versions = prompt_entry.get("versions")
        if not isinstance(versions, dict):
            raise KeyError(f"Prompt versions index invalid for prompt_id={canonical_id}")
        payload = versions.get(resolved)
        if not isinstance(payload, dict):
            raise KeyError(
                f"Prompt version not found: prompt_id={canonical_id}, version_id={resolved}"
            )
        return self._build_record(prompt_id=canonical_id, version_id=resolved, payload=payload)

    def get_prompt_text(self, *, prompt_id: str, version_id: str = "active") -> str:
        """Load prompt text for one prompt version."""
        record = self.get_version(prompt_id=prompt_id, version_id=version_id)
        path = Path(record.prompt_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(
                "Prompt text file not found for registered version: "
                f"prompt_id={record.prompt_id}, version_id={record.version_id}"
            )
        return path.read_text(encoding="utf-8")

    def rollback(
        self,
        *,
        prompt_id: str,
        to_version: str,
        reason: str,
        actor: str = "system",
        metadata: dict[str, Any] | None = None,
    ) -> RollbackRecord:
        """Rollback active prompt version to an existing version."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        target_version = _safe_slug(_normalize_text(to_version), fallback="")
        if not target_version:
            raise ValueError("to_version is required")

        registry = self._load_registry()
        prompt_entry = registry.get("prompts", {}).get(canonical_id)
        if not isinstance(prompt_entry, dict):
            raise KeyError(f"Prompt id not found: {canonical_id}")

        versions = prompt_entry.get("versions")
        if not isinstance(versions, dict) or target_version not in versions:
            raise KeyError(
                f"Rollback target not found: prompt_id={canonical_id}, to_version={target_version}"
            )

        from_version = str(prompt_entry.get("active_version") or "")
        prompt_entry["active_version"] = target_version

        rollback = RollbackRecord(
            prompt_id=canonical_id,
            from_version=from_version,
            to_version=target_version,
            rolled_back_at_utc=_utc_now(),
            reason=_normalize_text(reason),
            actor=_normalize_text(actor) or "system",
            metadata=_stable_json(metadata or {}),
        )
        rollbacks = prompt_entry.setdefault("rollbacks", [])
        if not isinstance(rollbacks, list):
            prompt_entry["rollbacks"] = []
            rollbacks = prompt_entry["rollbacks"]
        rollbacks.append(asdict(rollback))

        self._save_registry(registry)

        change_line = (
            f"- {rollback.rolled_back_at_utc} | rollback | "
            f"from={rollback.from_version or 'none'} -> to={rollback.to_version} | "
            f"actor={rollback.actor} | {rollback.reason}"
        )
        self._append_changelog_line(canonical_id, change_line)
        self._append_event("prompt_rolled_back", asdict(rollback))
        return rollback

    def get_state(self, prompt_id: str) -> dict[str, Any]:
        """Return prompt-level registry state (active/latest/versions/rollbacks)."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        registry = self._load_registry()
        prompt_entry = registry.get("prompts", {}).get(canonical_id)
        if not isinstance(prompt_entry, dict):
            raise KeyError(f"Prompt id not found: {canonical_id}")
        return _stable_json(prompt_entry)

    def build_tracking_payload(
        self,
        *,
        prompt_id: str,
        version_id: str = "active",
        include_prompt_text: bool = False,
    ) -> dict[str, Any]:
        """Build experiment-tracking payload for one resolved prompt version."""
        record = self.get_version(prompt_id=prompt_id, version_id=version_id)
        payload: dict[str, Any] = {
            "prompt_id": record.prompt_id,
            "prompt_version": record.version_id,
            "prompt_checksum_sha256": record.checksum_sha256,
            "prompt_path": record.prompt_path,
            "prompt_metadata_path": record.metadata_path,
            "prompt_changelog": record.changelog,
        }
        if include_prompt_text:
            payload["prompt_text"] = Path(record.prompt_path).read_text(encoding="utf-8")
        return payload

    def attach_to_experiment(
        self,
        *,
        tracker: TrackerLike | None,
        prompt_id: str,
        version_id: str = "active",
        experiment_config: dict[str, Any] | None = None,
        include_prompt_text: bool = False,
    ) -> dict[str, Any]:
        """Attach prompt-version metadata to experiment config and tracker events."""
        payload = self.build_tracking_payload(
            prompt_id=prompt_id,
            version_id=version_id,
            include_prompt_text=include_prompt_text,
        )

        if experiment_config is not None:
            slot = experiment_config.setdefault("prompt_versioning", {})
            if isinstance(slot, dict):
                slot.update(payload)
            else:
                experiment_config["prompt_versioning"] = payload

        if tracker is not None:
            tracker.log_event("prompt_version_attached", payload)

        self._append_event(
            "prompt_attached_to_experiment",
            {
                "prompt_id": payload["prompt_id"],
                "prompt_version": payload["prompt_version"],
                "prompt_checksum_sha256": payload["prompt_checksum_sha256"],
            },
        )
        return payload


__all__ = [
    "DEFAULT_PROMPTS_ROOT",
    "PromptVersionManager",
    "PromptVersionRecord",
    "RollbackRecord",
    "compute_checksum",
]
