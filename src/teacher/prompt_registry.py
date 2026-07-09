"""Prompt version registry for teacher prompt management.

Features:
- prompt versions
- prompt metadata
- automatic prompt hashes
- deterministic A/B prompt testing

Storage root:
- teacher_prompts/versions/
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_VERSIONS_ROOT = Path("teacher_prompts/versions")
_PROMPTS_DIRNAME = "prompts"
_AB_TESTS_DIRNAME = "ab_tests"
_REGISTRY_FILENAME = "registry.json"


@dataclass(frozen=True)
class PromptVersion:
    """One prompt version metadata record."""

    prompt_id: str
    version: str
    created_at_utc: str
    prompt_hash_sha256: str
    prompt_path: str
    metadata_path: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ABVariant:
    """One A/B variant mapping to a prompt version."""

    label: str
    prompt_id: str
    version: str
    weight: float


@dataclass(frozen=True)
class ABAssignment:
    """Deterministic assignment result for one unit."""

    experiment_id: str
    unit_id: str
    variant_label: str
    prompt_id: str
    version: str
    weight: float
    assignment_hash: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "_", value).strip("_")
    return slug or "prompt"


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _stable_copy(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))


def compute_prompt_hash(prompt_text: str) -> str:
    """Compute SHA-256 hash for prompt text."""
    return hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()


class PromptRegistry:
    """File-backed prompt version and A/B registry."""

    def __init__(self, versions_root: str | Path = DEFAULT_VERSIONS_ROOT) -> None:
        self.versions_root = Path(versions_root)
        self.prompts_root = self.versions_root / _PROMPTS_DIRNAME
        self.ab_tests_root = self.versions_root / _AB_TESTS_DIRNAME
        self.registry_path = self.versions_root / _REGISTRY_FILENAME
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        self.prompts_root.mkdir(parents=True, exist_ok=True)
        self.ab_tests_root.mkdir(parents=True, exist_ok=True)
        if not self.registry_path.exists():
            _write_json(
                self.registry_path,
                {
                    "schema_version": "v1",
                    "created_at_utc": _utc_now(),
                    "updated_at_utc": _utc_now(),
                    "prompts": {},
                    "ab_tests": {},
                },
            )

    def _load_registry(self) -> dict[str, Any]:
        return _read_json(self.registry_path)

    def _save_registry(self, payload: dict[str, Any]) -> None:
        payload["updated_at_utc"] = _utc_now()
        _write_json(self.registry_path, payload)

    def _canonical_prompt_id(self, prompt_id: str) -> str:
        normalized = _normalize_text(prompt_id).lower()
        if not normalized:
            raise ValueError("prompt_id is required")
        return _safe_slug(normalized)

    def _prompt_version_dir(self, prompt_id: str, version: str) -> Path:
        return self.prompts_root / prompt_id / version

    def _next_version(self, prompt_id: str) -> str:
        prompt_dir = self.prompts_root / prompt_id
        if not prompt_dir.exists():
            return "v001"

        highest = 0
        for candidate in prompt_dir.iterdir():
            if not candidate.is_dir():
                continue
            match = re.match(r"^v(\d+)$", candidate.name)
            if not match:
                continue
            highest = max(highest, int(match.group(1)))
        return f"v{highest + 1:03d}"

    def register_prompt(
        self,
        *,
        prompt_id: str,
        prompt_text: str,
        metadata: dict[str, Any] | None = None,
        version: str | None = None,
        overwrite: bool = False,
    ) -> PromptVersion:
        """Register one prompt version and persist metadata + hash."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        version_id = version or self._next_version(canonical_id)
        version_id = _safe_slug(version_id)
        if not version_id:
            raise ValueError("version cannot be empty")

        version_dir = self._prompt_version_dir(canonical_id, version_id)
        if version_dir.exists() and not overwrite:
            raise FileExistsError(
                f"Prompt version already exists: prompt_id={canonical_id}, version={version_id}"
            )

        version_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = version_dir / "prompt.txt"
        metadata_path = version_dir / "metadata.json"

        prompt_hash = compute_prompt_hash(prompt_text)
        user_meta = _stable_copy(metadata or {})

        created_at = _utc_now()
        version_record = PromptVersion(
            prompt_id=canonical_id,
            version=version_id,
            created_at_utc=created_at,
            prompt_hash_sha256=prompt_hash,
            prompt_path=str(prompt_path),
            metadata_path=str(metadata_path),
            metadata=user_meta,
        )

        prompt_path.write_text(prompt_text, encoding="utf-8")
        _write_json(
            metadata_path,
            {
                **asdict(version_record),
                "schema_version": "v1",
            },
        )

        registry = self._load_registry()
        prompts = registry.setdefault("prompts", {})
        prompt_entry = prompts.setdefault(canonical_id, {"latest_version": None, "versions": {}})
        versions = prompt_entry.setdefault("versions", {})
        versions[version_id] = {
            "created_at_utc": created_at,
            "prompt_hash_sha256": prompt_hash,
            "prompt_path": str(prompt_path),
            "metadata_path": str(metadata_path),
            "metadata": user_meta,
        }
        prompt_entry["latest_version"] = version_id
        self._save_registry(registry)

        return version_record

    def register_prompt_file(
        self,
        *,
        prompt_id: str,
        source_path: str | Path,
        metadata: dict[str, Any] | None = None,
        version: str | None = None,
        overwrite: bool = False,
    ) -> PromptVersion:
        """Register a prompt from an existing text file."""
        path = Path(source_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Prompt file not found: {path}")
        prompt_text = path.read_text(encoding="utf-8")

        merged_meta = dict(metadata or {})
        merged_meta.setdefault("source_path", str(path))
        return self.register_prompt(
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            metadata=merged_meta,
            version=version,
            overwrite=overwrite,
        )

    def list_prompt_versions(self, prompt_id: str) -> tuple[PromptVersion, ...]:
        """List all versions for one prompt id."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        registry = self._load_registry()
        prompt_entry = registry.get("prompts", {}).get(canonical_id)
        if not isinstance(prompt_entry, dict):
            return ()

        versions = prompt_entry.get("versions")
        if not isinstance(versions, dict):
            return ()

        rows: list[PromptVersion] = []
        for version_id, payload in sorted(versions.items()):
            if not isinstance(payload, dict):
                continue
            rows.append(
                PromptVersion(
                    prompt_id=canonical_id,
                    version=str(version_id),
                    created_at_utc=str(payload.get("created_at_utc", "")),
                    prompt_hash_sha256=str(payload.get("prompt_hash_sha256", "")),
                    prompt_path=str(payload.get("prompt_path", "")),
                    metadata_path=str(payload.get("metadata_path", "")),
                    metadata=_stable_copy(payload.get("metadata", {})),
                )
            )
        return tuple(rows)

    def get_prompt_version(
        self,
        *,
        prompt_id: str,
        version: str = "latest",
    ) -> PromptVersion:
        """Get one prompt version record."""
        canonical_id = self._canonical_prompt_id(prompt_id)
        registry = self._load_registry()
        prompt_entry = registry.get("prompts", {}).get(canonical_id)
        if not isinstance(prompt_entry, dict):
            raise KeyError(f"Prompt id not found: {canonical_id}")

        resolved_version = version
        if version == "latest":
            latest = prompt_entry.get("latest_version")
            if not isinstance(latest, str) or not latest:
                raise KeyError(f"Prompt id has no versions: {canonical_id}")
            resolved_version = latest

        versions = prompt_entry.get("versions")
        if not isinstance(versions, dict):
            raise KeyError(f"Prompt id has invalid versions index: {canonical_id}")

        payload = versions.get(resolved_version)
        if not isinstance(payload, dict):
            raise KeyError(
                f"Prompt version not found: prompt_id={canonical_id}, version={resolved_version}"
            )

        return PromptVersion(
            prompt_id=canonical_id,
            version=resolved_version,
            created_at_utc=str(payload.get("created_at_utc", "")),
            prompt_hash_sha256=str(payload.get("prompt_hash_sha256", "")),
            prompt_path=str(payload.get("prompt_path", "")),
            metadata_path=str(payload.get("metadata_path", "")),
            metadata=_stable_copy(payload.get("metadata", {})),
        )

    def get_prompt_text(self, *, prompt_id: str, version: str = "latest") -> str:
        """Load prompt text for one prompt version."""
        record = self.get_prompt_version(prompt_id=prompt_id, version=version)
        path = Path(record.prompt_path)
        if not path.exists():
            raise FileNotFoundError(
                "Prompt text file not found for registered version: "
                f"prompt_id={record.prompt_id}, version={record.version}"
            )
        return path.read_text(encoding="utf-8")

    def create_ab_test(
        self,
        *,
        experiment_id: str,
        variants: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create one deterministic A/B test configuration."""
        normalized_id = _safe_slug(_normalize_text(experiment_id).lower())
        if not normalized_id:
            raise ValueError("experiment_id is required")
        if len(variants) < 2:
            raise ValueError("A/B test requires at least two variants")

        prepared: list[ABVariant] = []
        for index, row in enumerate(variants, start=1):
            if not isinstance(row, dict):
                raise ValueError("Each variant must be a JSON object")
            label = _normalize_text(row.get("label")) or chr(ord("A") + index - 1)
            prompt_id = _normalize_text(row.get("prompt_id"))
            version = _normalize_text(row.get("version")) or "latest"
            weight_raw = row.get("weight", 1.0)
            try:
                weight = float(weight_raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid variant weight for label={label}: {weight_raw}"
                ) from exc
            if weight <= 0:
                raise ValueError(f"Variant weight must be > 0 for label={label}")

            prompt_record = self.get_prompt_version(prompt_id=prompt_id, version=version)
            prepared.append(
                ABVariant(
                    label=label,
                    prompt_id=prompt_record.prompt_id,
                    version=prompt_record.version,
                    weight=weight,
                )
            )

        total_weight = sum(item.weight for item in prepared)
        normalized_variants: list[dict[str, Any]] = []
        for item in prepared:
            normalized_variants.append(
                {
                    "label": item.label,
                    "prompt_id": item.prompt_id,
                    "version": item.version,
                    "weight": item.weight,
                    "normalized_weight": item.weight / total_weight,
                }
            )

        config = {
            "schema_version": "v1",
            "experiment_id": normalized_id,
            "created_at_utc": _utc_now(),
            "variants": normalized_variants,
            "metadata": _stable_copy(metadata or {}),
        }

        path = self.ab_tests_root / f"{normalized_id}.json"
        if path.exists() and not overwrite:
            raise FileExistsError(f"A/B config already exists: {path}")
        _write_json(path, config)

        registry = self._load_registry()
        ab_tests = registry.setdefault("ab_tests", {})
        ab_tests[normalized_id] = {
            "path": str(path),
            "created_at_utc": config["created_at_utc"],
            "variant_count": len(normalized_variants),
            "metadata": config["metadata"],
        }
        self._save_registry(registry)

        return config

    def list_ab_tests(self) -> tuple[dict[str, Any], ...]:
        """List registered A/B tests from registry index."""
        registry = self._load_registry()
        ab_tests = registry.get("ab_tests", {})
        if not isinstance(ab_tests, dict):
            return ()

        rows: list[dict[str, Any]] = []
        for experiment_id, payload in sorted(ab_tests.items()):
            if not isinstance(payload, dict):
                continue
            rows.append({"experiment_id": experiment_id, **_stable_copy(payload)})
        return tuple(rows)

    def load_ab_test(self, experiment_id: str) -> dict[str, Any]:
        """Load one A/B config file by experiment id."""
        normalized_id = _safe_slug(_normalize_text(experiment_id).lower())
        path = self.ab_tests_root / f"{normalized_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"A/B test config not found: {path}")
        return _read_json(path)

    def assign_ab_variant(
        self,
        *,
        experiment_id: str,
        unit_id: str,
        salt: str = "",
    ) -> ABAssignment:
        """Deterministically assign one unit to an A/B variant."""
        config = self.load_ab_test(experiment_id)
        variants = config.get("variants")
        if not isinstance(variants, list) or not variants:
            raise ValueError(f"A/B test has no variants: {experiment_id}")

        norm_unit = _normalize_text(unit_id)
        if not norm_unit:
            raise ValueError("unit_id is required")

        seed_text = f"{config.get('experiment_id')}|{norm_unit}|{salt}"
        digest = hashlib.sha256(seed_text.encode("utf-8")).digest()
        value = int.from_bytes(digest[:8], byteorder="big", signed=False) / float(2**64)

        cumulative = 0.0
        selected = None
        for row in variants:
            if not isinstance(row, dict):
                continue
            weight = float(row.get("normalized_weight", 0.0))
            cumulative += weight
            if value <= cumulative:
                selected = row
                break

        if selected is None:
            last = variants[-1]
            if not isinstance(last, dict):
                raise ValueError(f"A/B test variants malformed: {experiment_id}")
            selected = last

        return ABAssignment(
            experiment_id=str(config.get("experiment_id") or experiment_id),
            unit_id=norm_unit,
            variant_label=str(selected.get("label") or "A"),
            prompt_id=str(selected.get("prompt_id") or ""),
            version=str(selected.get("version") or ""),
            weight=float(selected.get("normalized_weight", 0.0)),
            assignment_hash=hashlib.sha256(seed_text.encode("utf-8")).hexdigest(),
        )


def get_default_prompt_registry() -> PromptRegistry:
    """Return default prompt registry rooted at teacher_prompts/versions/."""
    return PromptRegistry(DEFAULT_VERSIONS_ROOT)
