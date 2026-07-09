"""Production dataset generation workflow orchestrator.

Pipeline:
teacher -> validation -> optional human review -> gold merge -> SFT export

This module composes existing deterministic stages and automatically versions
dataset outputs for validation, review, gold, and SFT artifacts.

No provider API inference is executed in this module unless explicitly enabled
through downstream stage configs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from data.build_gold_dataset import build_gold_dataset
from data.build_sft_dataset import SFTBuildConfig, build_sft_dataset
from review.merge_reviews import merge_reviews
from teacher.generate_labels import PipelineConfig, run_pipeline

DEFAULT_INSTRUCTION_TEXT = (
    "Evaluate the student essay using rubric-grounded educational reasoning and return "
    "strict JSON following the production output schema."
)
SUPPORTED_EXPORT_FORMATS: tuple[str, ...] = ("alpaca", "sharegpt", "chatml", "huggingface")


@dataclass(frozen=True)
class WorkflowConfig:
    """Runtime configuration for production dataset generation workflow."""

    run_id: str | None
    workflow_root: Path
    input_jsonl: Path
    teacher_outputs_path: Path | None
    teacher_model_id: str
    inference_mode: str
    schema_path: Path
    quality_threshold: float
    confidence_threshold: float
    strict_source_split: bool
    instruction_text: str
    export_formats: tuple[str, ...]
    validation_root: Path
    validation_version: str | None
    enable_human_review: bool
    review_final_root: Path
    review_version: str | None
    review_runs_root: Path
    review_reviews_root: Path
    review_source_run_id: str | None
    approved_reviews_path: Path
    adjudication_log: Path | None
    gold_root: Path
    gold_version: str | None
    sft_root: Path
    sft_version: str | None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("dataset-gen-%Y%m%dT%H%M%SZ")


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _parse_export_formats(raw: str) -> tuple[str, ...]:
    parts = [part.strip().lower() for part in raw.split(",") if part.strip()]
    if not parts:
        raise ValueError("At least one export format is required.")
    deduped: list[str] = []
    seen: set[str] = set()
    for part in parts:
        if part not in SUPPORTED_EXPORT_FORMATS:
            allowed = ", ".join(SUPPORTED_EXPORT_FORMATS)
            raise ValueError(f"Unsupported export format '{part}'. Allowed values: {allowed}")
        if part not in seen:
            seen.add(part)
            deduped.append(part)
    return tuple(deduped)


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


def _path_sha256(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    hasher = hashlib.sha256()

    if path.is_file():
        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    for candidate in sorted(path.rglob("*")):
        if not candidate.is_file():
            continue
        rel = str(candidate.relative_to(path)).replace("\\", "/")
        hasher.update(rel.encode("utf-8"))
        hasher.update(b"\x00")
        with candidate.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
        hasher.update(b"\x00")
    return hasher.hexdigest()


def _sanitize_version(prefix: str, version: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", version).strip("_")
    if not normalized:
        raise ValueError("Version must include alphanumeric characters.")
    if not normalized.startswith(f"{prefix}_v"):
        if normalized.startswith("v") and normalized[1:].isdigit():
            normalized = f"{prefix}_{normalized}"
        elif normalized.isdigit():
            normalized = f"{prefix}_v{normalized}"
        else:
            normalized = f"{prefix}_v{normalized}"
    return normalized


def _auto_version(root: Path, prefix: str) -> str:
    versions_dir = root / "versions"
    if not versions_dir.exists():
        return f"{prefix}_v1"

    max_seen = 0
    pattern = re.compile(rf"{re.escape(prefix)}_v(\d+)$")
    for entry in versions_dir.iterdir():
        if not entry.is_dir():
            continue
        match = pattern.fullmatch(entry.name)
        if not match:
            continue
        value = int(match.group(1))
        if value > max_seen:
            max_seen = value
    return f"{prefix}_v{max_seen + 1}"


def _resolve_version_dir(
    *,
    root: Path,
    prefix: str,
    version: str | None,
) -> tuple[str, Path]:
    resolved = _sanitize_version(prefix, version) if version else _auto_version(root, prefix)
    version_dir = root / "versions" / resolved
    version_dir.mkdir(parents=True, exist_ok=True)
    return resolved, version_dir


def _write_version_index(root: Path, *, latest_version: str) -> dict[str, Any]:
    versions_dir = root / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    versions = [path.name for path in sorted(versions_dir.iterdir()) if path.is_dir()]
    payload = {
        "latest_version": latest_version,
        "versions": versions,
        "updated_at_utc": _utc_now(),
    }
    _write_json(root / "version_index.json", payload)
    return payload


def _line_count_jsonl(path: Path | None) -> int | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def _validation_stage(config: WorkflowConfig, *, output_dir: Path) -> dict[str, Any]:
    manifest = run_pipeline(
        PipelineConfig(
            input_jsonl=config.input_jsonl,
            output_root=output_dir,
            teacher_model_id=config.teacher_model_id,
            inference_mode=config.inference_mode,
            predictions_path=config.teacher_outputs_path,
            schema_path=config.schema_path,
            quality_threshold=config.quality_threshold,
            confidence_threshold=config.confidence_threshold,
            strict_source_split=config.strict_source_split,
            instruction_text=config.instruction_text,
        )
    )
    return manifest


def _review_stage(config: WorkflowConfig, *, output_dir: Path) -> dict[str, Any]:
    return merge_reviews(
        gold_path=config.input_jsonl,
        runs_root=config.review_runs_root,
        reviews_root=config.review_reviews_root,
        output_root=output_dir,
        source_run_id=config.review_source_run_id,
    )


def run_workflow(config: WorkflowConfig) -> dict[str, Any]:
    """Run end-to-end production dataset generation workflow."""
    if config.inference_mode != "precomputed":
        raise ValueError(
            "Unsupported inference_mode. Workflow requires "
            "'precomputed' teacher outputs."
        )
    if config.teacher_outputs_path is None:
        raise ValueError("--teacher-outputs-path is required when inference_mode=precomputed")
    if not config.input_jsonl.exists():
        raise FileNotFoundError(f"Input dataset not found: {config.input_jsonl}")

    run_id = _normalize_text(config.run_id) or _default_run_id()
    run_dir = config.workflow_root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    teacher_stage = {
        "stage": "teacher",
        "mode": config.inference_mode,
        "teacher_model_id": config.teacher_model_id,
        "teacher_outputs_path": (
            str(config.teacher_outputs_path) if config.teacher_outputs_path else None
        ),
        "teacher_outputs_checksum_sha256": _path_sha256(config.teacher_outputs_path),
        "teacher_outputs_row_count": _line_count_jsonl(config.teacher_outputs_path),
    }

    validation_version, validation_dir = _resolve_version_dir(
        root=config.validation_root,
        prefix="validation",
        version=config.validation_version,
    )
    validation_manifest = _validation_stage(config, output_dir=validation_dir)
    _write_version_index(config.validation_root, latest_version=validation_version)

    review_manifest: dict[str, Any]
    review_version: str | None = None
    approved_reviews_path = config.approved_reviews_path
    if config.enable_human_review:
        review_version, review_dir = _resolve_version_dir(
            root=config.review_final_root,
            prefix="review_final",
            version=config.review_version,
        )
        review_summary = _review_stage(config, output_dir=review_dir)
        _write_version_index(config.review_final_root, latest_version=review_version)
        approved_reviews_path = review_dir / "review_dataset.jsonl"

        review_manifest_path = review_dir / "manifest.json"
        review_manifest = (
            _read_json(review_manifest_path)
            if review_manifest_path.exists()
            else {
                "schema_version": "review_merge_v1",
                "summary": review_summary,
                "outputs": {"review_dataset_jsonl": str(approved_reviews_path)},
            }
        )
    else:
        review_manifest = {
            "status": "skipped",
            "reason": "human_review_disabled",
            "approved_reviews_path": str(approved_reviews_path),
        }

    if not approved_reviews_path.exists():
        raise FileNotFoundError(
            "Approved review dataset not found for gold merge: "
            f"{approved_reviews_path}"
        )

    gold_manifest = build_gold_dataset(
        approved_path=approved_reviews_path,
        output_root=config.gold_root,
        adjudication_log=config.adjudication_log if config.adjudication_log else None,
        version=config.gold_version,
    )
    gold_dataset_path = Path(str(gold_manifest["outputs"]["gold_dataset_jsonl"]))

    sft_version, sft_dir = _resolve_version_dir(
        root=config.sft_root,
        prefix="sft",
        version=config.sft_version,
    )
    sft_manifest = build_sft_dataset(
        SFTBuildConfig(
            input_jsonl=gold_dataset_path,
            teacher_outputs_path=config.teacher_outputs_path,
            output_root=sft_dir,
            teacher_model_id=config.teacher_model_id,
            inference_mode=config.inference_mode,
            schema_path=config.schema_path,
            quality_threshold=config.quality_threshold,
            confidence_threshold=config.confidence_threshold,
            strict_source_split=config.strict_source_split,
            instruction_text=config.instruction_text,
            export_formats=config.export_formats,
        )
    )
    _write_version_index(config.sft_root, latest_version=sft_version)

    workflow_manifest = {
        "schema_version": "dataset_generation_workflow_v1",
        "run_id": run_id,
        "created_at_utc": _utc_now(),
        "pipeline_order": [
            "teacher",
            "validation",
            "human_review_optional",
            "gold_merge",
            "sft_export",
        ],
        "versions": {
            "validation": validation_version,
            "review_final": review_version,
            "gold": gold_manifest.get("version"),
            "sft": sft_version,
        },
        "inputs": {
            "input_jsonl": str(config.input_jsonl),
            "teacher_outputs_path": (
                str(config.teacher_outputs_path) if config.teacher_outputs_path else None
            ),
            "approved_reviews_path": str(approved_reviews_path),
            "adjudication_log": str(config.adjudication_log) if config.adjudication_log else None,
        },
        "stage_manifests": {
            "teacher": teacher_stage,
            "validation": validation_manifest,
            "human_review": review_manifest,
            "gold_merge": gold_manifest,
            "sft_export": sft_manifest,
        },
        "checksums": {
            "input_jsonl_sha256": _path_sha256(config.input_jsonl),
            "teacher_outputs_sha256": _path_sha256(config.teacher_outputs_path),
            "approved_reviews_sha256": _path_sha256(approved_reviews_path),
            "gold_dataset_sha256": _path_sha256(gold_dataset_path),
            "sft_root_sha256": _path_sha256(sft_dir),
        },
        "outputs": {
            "run_dir": str(run_dir),
            "validation_dir": str(validation_dir),
            "review_final_dir": (
                str(config.review_final_root / "versions" / review_version)
                if review_version
                else None
            ),
            "gold_dataset_jsonl": str(gold_dataset_path),
            "sft_dir": str(sft_dir),
        },
    }

    _write_json(run_dir / "manifest.json", workflow_manifest)
    _write_json(config.workflow_root / "manifest.json", workflow_manifest)
    return workflow_manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run production dataset generation workflow with automatic dataset versioning."
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--workflow-root", default="outputs/dataset_generation")

    parser.add_argument("--input-jsonl", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--teacher-outputs-path", default=None)
    parser.add_argument("--teacher-model-id", default="gpt-5")
    parser.add_argument(
        "--inference-mode",
        default="precomputed",
        choices=("precomputed",),
    )
    parser.add_argument("--schema-path", default="teacher_prompts/output_schema.json")
    parser.add_argument("--quality-threshold", type=float, default=0.80)
    parser.add_argument("--confidence-threshold", type=float, default=0.60)
    parser.add_argument("--strict-source-split", action="store_true")
    parser.add_argument("--instruction-text", default=DEFAULT_INSTRUCTION_TEXT)
    parser.add_argument(
        "--export-formats",
        default="alpaca,sharegpt,chatml,huggingface",
        help="Comma-separated list of SFT export formats.",
    )

    parser.add_argument("--validation-root", default="datasets/validation")
    parser.add_argument("--validation-version", default=None)

    parser.add_argument("--enable-human-review", action="store_true")
    parser.add_argument("--review-final-root", default="datasets/review/final")
    parser.add_argument("--review-version", default=None)
    parser.add_argument("--review-runs-root", default="outputs/teacher_runs")
    parser.add_argument("--review-reviews-root", default="datasets/review")
    parser.add_argument("--review-source-run-id", default=None)
    parser.add_argument(
        "--approved-reviews-path",
        default="datasets/review/final/review_dataset.jsonl",
    )
    parser.add_argument("--adjudication-log", default="datasets/review/reviews.jsonl")

    parser.add_argument("--gold-root", default="datasets/gold")
    parser.add_argument("--gold-version", default=None)
    parser.add_argument("--sft-root", default="datasets/sft")
    parser.add_argument("--sft-version", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    adjudication_log = Path(args.adjudication_log)
    config = WorkflowConfig(
        run_id=_normalize_text(args.run_id) or None,
        workflow_root=Path(args.workflow_root),
        input_jsonl=Path(args.input_jsonl),
        teacher_outputs_path=(
            Path(args.teacher_outputs_path) if args.teacher_outputs_path else None
        ),
        teacher_model_id=str(args.teacher_model_id),
        inference_mode=str(args.inference_mode),
        schema_path=Path(args.schema_path),
        quality_threshold=float(args.quality_threshold),
        confidence_threshold=float(args.confidence_threshold),
        strict_source_split=bool(args.strict_source_split),
        instruction_text=str(args.instruction_text),
        export_formats=_parse_export_formats(str(args.export_formats)),
        validation_root=Path(args.validation_root),
        validation_version=_normalize_text(args.validation_version) or None,
        enable_human_review=bool(args.enable_human_review),
        review_final_root=Path(args.review_final_root),
        review_version=_normalize_text(args.review_version) or None,
        review_runs_root=Path(args.review_runs_root),
        review_reviews_root=Path(args.review_reviews_root),
        review_source_run_id=_normalize_text(args.review_source_run_id) or None,
        approved_reviews_path=Path(args.approved_reviews_path),
        adjudication_log=adjudication_log if adjudication_log.exists() else None,
        gold_root=Path(args.gold_root),
        gold_version=_normalize_text(args.gold_version) or None,
        sft_root=Path(args.sft_root),
        sft_version=_normalize_text(args.sft_version) or None,
    )
    manifest = run_workflow(config)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
