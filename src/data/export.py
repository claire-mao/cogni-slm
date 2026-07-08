"""JSONL export for validated synthetic dataset artifacts."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from data.schemas import DatasetManifest, DatasetRecord


@dataclass(frozen=True)
class ExportConfig:
    """Configuration contract for dataset artifact export."""

    output_root: str
    dataset_filename: str = "dataset.jsonl"
    manifest_filename: str = "manifest.json"
    traces_filename: str = "audit_traces.jsonl"
    include_audit_traces: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


class DatasetExporter(Protocol):
    """Contract for writing dataset export artifacts."""

    def export_jsonl(
        self,
        records: Sequence[DatasetRecord],
        manifest: DatasetManifest,
    ) -> Mapping[str, str]:
        """Write dataset and manifest artifacts and return artifact paths."""


def _stable_json_line(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


class JSONLDatasetExporter:
    """JSONL exporter with deterministic serialization and manifest hashing."""

    def __init__(self, config: ExportConfig) -> None:
        self.config = config

    def export_jsonl(
        self,
        records: Sequence[DatasetRecord],
        manifest: DatasetManifest,
    ) -> Mapping[str, str]:
        output_root = Path(self.config.output_root)
        output_root.mkdir(parents=True, exist_ok=True)

        dataset_path = output_root / self.config.dataset_filename
        manifest_path = output_root / self.config.manifest_filename
        traces_path = output_root / self.config.traces_filename

        serialized_records: list[dict[str, Any]] = [asdict(record) for record in records]
        stable_lines = [_stable_json_line(record) for record in serialized_records]

        with dataset_path.open("w", encoding="utf-8") as handle:
            for line in stable_lines:
                handle.write(line + "\n")

        snapshot_hash = hashlib.sha256("\n".join(stable_lines).encode("utf-8")).hexdigest()

        manifest_payload = asdict(manifest)
        manifest_payload["snapshot_hash"] = snapshot_hash
        manifest_payload["metadata"] = {
            **manifest_payload.get("metadata", {}),
            **self.config.metadata,
        }

        manifest_path.write_text(
            json.dumps(manifest_payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

        if self.config.include_audit_traces:
            with traces_path.open("w", encoding="utf-8") as handle:
                for record in serialized_records:
                    trace = {
                        "example_id": record["example_id"],
                        "primary_fallacy_label": record["primary_fallacy_label"],
                        "is_no_fallacy": record["is_no_fallacy"],
                        "is_adversarial": record["is_adversarial"],
                        "filter_decisions": record["filter_decisions"],
                        "critique_scores": record["critique_scores"],
                        "dedup_cluster_id": record["dedup_cluster_id"],
                        "metadata": record["metadata"],
                    }
                    handle.write(_stable_json_line(trace) + "\n")

        return {
            "dataset_jsonl": str(dataset_path),
            "manifest_json": str(manifest_path),
            "traces_jsonl": str(traces_path),
            "snapshot_hash": snapshot_hash,
        }
