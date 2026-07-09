"""Build final supervised fine-tuning datasets from teacher outputs.

This builder composes two deterministic stages:
1) canonical SFT generation via `src.teacher.generate_labels`
2) format exports for Alpaca, ShareGPT, ChatML, and Hugging Face JSONL

No provider API inference is performed in this module.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from teacher.generate_labels import PipelineConfig, run_pipeline

VALID_SPLITS: tuple[str, ...] = ("train", "validation", "test")
SUPPORTED_EXPORT_FORMATS: tuple[str, ...] = ("alpaca", "sharegpt", "chatml", "huggingface")
DEFAULT_INSTRUCTION_TEXT = (
    "Evaluate the student essay using rubric-grounded educational reasoning and return "
    "strict JSON following the production output schema."
)


@dataclass(frozen=True)
class SFTBuildConfig:
    """Runtime configuration for SFT dataset build."""

    input_jsonl: Path
    teacher_outputs_path: Path | None
    output_root: Path
    teacher_model_id: str
    inference_mode: str
    schema_path: Path
    quality_threshold: float
    confidence_threshold: float
    strict_source_split: bool
    instruction_text: str
    export_formats: tuple[str, ...]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"Expected object JSONL row at {path}:{line_number}")
            rows.append(payload)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


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
            deduped.append(part)
            seen.add(part)
    return tuple(deduped)


def _load_canonical_rows(output_root: Path) -> dict[str, list[dict[str, Any]]]:
    rows_by_split: dict[str, list[dict[str, Any]]] = {}
    for split in VALID_SPLITS:
        split_path = output_root / split / "data.jsonl"
        rows_by_split[split] = _read_jsonl(split_path)
    return rows_by_split


def _safe_metadata(row: dict[str, Any]) -> dict[str, Any]:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _example_id(row: dict[str, Any], index: int) -> str:
    metadata = _safe_metadata(row)
    value = metadata.get("example_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"row-{index:06d}"


def _build_user_text(instruction: str, input_payload: str) -> str:
    return f"Instruction:\n{instruction}\n\nInput:\n{input_payload}"


def _chatml_messages(row: dict[str, Any]) -> list[dict[str, str]]:
    instruction = str(row.get("instruction", ""))
    input_payload = str(row.get("input", ""))
    output_payload = str(row.get("output", ""))
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": input_payload},
        {"role": "assistant", "content": output_payload},
    ]


def _chatml_text(messages: list[dict[str, str]]) -> str:
    blocks = [
        f"<|{message['role']}|>\n{message['content']}"
        for message in messages
        if message.get("role") and message.get("content")
    ]
    return "\n\n".join(blocks)


def _to_alpaca(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    return {
        "id": _example_id(row, row_index),
        "instruction": str(row.get("instruction", "")),
        "input": str(row.get("input", "")),
        "output": str(row.get("output", "")),
        "metadata": _safe_metadata(row),
    }


def _to_sharegpt(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    instruction = str(row.get("instruction", ""))
    input_payload = str(row.get("input", ""))
    output_payload = str(row.get("output", ""))
    return {
        "id": _example_id(row, row_index),
        "conversations": [
            {"from": "human", "value": _build_user_text(instruction, input_payload)},
            {"from": "gpt", "value": output_payload},
        ],
        "metadata": _safe_metadata(row),
    }


def _to_chatml(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    return {
        "id": _example_id(row, row_index),
        "messages": _chatml_messages(row),
        "metadata": _safe_metadata(row),
    }


def _to_huggingface(row: dict[str, Any], row_index: int) -> dict[str, Any]:
    messages = _chatml_messages(row)
    return {
        "id": _example_id(row, row_index),
        "instruction": str(row.get("instruction", "")),
        "input": str(row.get("input", "")),
        "output": str(row.get("output", "")),
        "messages": messages,
        "text": _chatml_text(messages),
        "metadata": _safe_metadata(row),
    }


def _convert_rows(
    rows: list[dict[str, Any]],
    *,
    export_format: str,
) -> list[dict[str, Any]]:
    converted: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        if export_format == "alpaca":
            converted.append(_to_alpaca(row, index))
            continue
        if export_format == "sharegpt":
            converted.append(_to_sharegpt(row, index))
            continue
        if export_format == "chatml":
            converted.append(_to_chatml(row, index))
            continue
        if export_format == "huggingface":
            converted.append(_to_huggingface(row, index))
            continue
        raise ValueError(f"Unsupported export format: {export_format}")
    return converted


def export_sft_formats(
    *,
    output_root: Path,
    export_formats: tuple[str, ...],
) -> dict[str, Any]:
    """Export canonical SFT rows to requested SFT training formats."""
    rows_by_split = _load_canonical_rows(output_root)
    summary: dict[str, Any] = {"formats": {}}

    for export_format in export_formats:
        split_counts: dict[str, int] = {}
        split_paths: dict[str, str] = {}
        for split in VALID_SPLITS:
            converted = _convert_rows(rows_by_split.get(split, []), export_format=export_format)
            path = output_root / "formats" / export_format / f"{split}.jsonl"
            _write_jsonl(path, converted)
            split_counts[split] = len(converted)
            split_paths[split] = str(path)

        summary["formats"][export_format] = {
            "split_counts": split_counts,
            "paths": split_paths,
        }
    return summary


def build_sft_dataset(config: SFTBuildConfig) -> dict[str, Any]:
    """Build canonical and multi-format SFT datasets from teacher outputs."""
    if config.inference_mode != "precomputed":
        raise ValueError(
            "Unsupported inference_mode. build_sft_dataset only supports "
            "'precomputed' teacher outputs."
        )
    if config.teacher_outputs_path is None:
        raise ValueError("--teacher-outputs-path is required when inference_mode=precomputed")

    pipeline_manifest = run_pipeline(
        PipelineConfig(
            input_jsonl=config.input_jsonl,
            output_root=config.output_root,
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

    export_summary = export_sft_formats(
        output_root=config.output_root,
        export_formats=config.export_formats,
    )

    manifest = {
        "stage": "build_sft_dataset",
        "input_jsonl": str(config.input_jsonl),
        "teacher_outputs_path": (
            str(config.teacher_outputs_path) if config.teacher_outputs_path else None
        ),
        "output_root": str(config.output_root),
        "teacher_model_id": config.teacher_model_id,
        "inference_mode": config.inference_mode,
        "schema_path": str(config.schema_path),
        "quality_threshold": config.quality_threshold,
        "confidence_threshold": config.confidence_threshold,
        "strict_source_split": config.strict_source_split,
        "export_formats": list(config.export_formats),
        "canonical_manifest": pipeline_manifest,
        "export_summary": export_summary,
    }
    manifest_path = config.output_root / "sft_build_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    """Parse CLI args for SFT build."""
    parser = argparse.ArgumentParser(description="Build final SFT datasets from teacher outputs.")
    parser.add_argument("--input-jsonl", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument(
        "--teacher-outputs-path",
        default=None,
        help="Path to precomputed teacher outputs (JSONL file or directory).",
    )
    parser.add_argument("--output-root", default="datasets/sft")
    parser.add_argument("--teacher-model-id", default="gpt-5")
    parser.add_argument(
        "--inference-mode",
        default="precomputed",
        choices=("precomputed",),
        help="Use precomputed teacher outputs.",
    )
    parser.add_argument("--schema-path", default="teacher_prompts/output_schema.json")
    parser.add_argument("--quality-threshold", type=float, default=0.80)
    parser.add_argument("--confidence-threshold", type=float, default=0.60)
    parser.add_argument(
        "--strict-source-split",
        action="store_true",
        help="Keep provided source split labels where valid.",
    )
    parser.add_argument(
        "--instruction-text",
        default=DEFAULT_INSTRUCTION_TEXT,
        help="Instruction prompt stored in SFT training rows.",
    )
    parser.add_argument(
        "--export-formats",
        default="alpaca,sharegpt,chatml,huggingface",
        help="Comma-separated export formats.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    config = SFTBuildConfig(
        input_jsonl=Path(args.input_jsonl),
        teacher_outputs_path=(
            Path(args.teacher_outputs_path) if args.teacher_outputs_path is not None else None
        ),
        output_root=Path(args.output_root),
        teacher_model_id=str(args.teacher_model_id),
        inference_mode=str(args.inference_mode),
        schema_path=Path(args.schema_path),
        quality_threshold=float(args.quality_threshold),
        confidence_threshold=float(args.confidence_threshold),
        strict_source_split=bool(args.strict_source_split),
        instruction_text=str(args.instruction_text),
        export_formats=_parse_export_formats(str(args.export_formats)),
    )
    manifest = build_sft_dataset(config)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
