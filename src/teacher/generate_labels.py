"""Production label generation pipeline for SFT data export.

Pipeline stages:
dataset -> teacher inference -> validation -> quality filter ->
JSON schema validation -> confidence filter -> dataset export

This module does not call provider APIs directly. Inference is sourced from
precomputed teacher outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean
from typing import Any

from .io import GoldExample, PredictionRecord, load_predictions
from .models import canonical_model_id
from .validation import validate_prediction

_VALID_SPLITS = ("train", "validation", "test")
_DEFAULT_INSTRUCTION = (
    "Evaluate the student essay using rubric-grounded educational reasoning and return "
    "strict JSON following the production output schema."
)


@dataclass(frozen=True)
class InputExample:
    """Input record for label generation."""

    example_id: str
    prompt: str
    essay: str
    score: float | None
    split: str | None
    source: str
    license: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PipelineCandidate:
    """Candidate item flowing through the label generation pipeline."""

    input_example: InputExample
    prediction: PredictionRecord
    output_object: dict[str, Any] | None
    validation_score: float
    validation_notes: list[str]
    schema_valid: bool
    schema_errors: list[str]
    confidence: float | None


@dataclass(frozen=True)
class PipelineConfig:
    """Runtime configuration for generation pipeline."""

    input_jsonl: Path
    output_root: Path
    teacher_model_id: str
    inference_mode: str
    predictions_path: Path | None
    schema_path: Path
    quality_threshold: float
    confidence_threshold: float
    strict_source_split: bool
    instruction_text: str


def _normalize_split(value: Any) -> str | None:
    if value is None:
        return None
    split = str(value).strip().lower()
    if split in {"train", "training"}:
        return "train"
    if split in {"validation", "valid", "val", "dev"}:
        return "validation"
    if split in {"test", "testing"}:
        return "test"
    return None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:  # NaN guard
        return None
    return numeric


def _is_simulated_example(payload: dict[str, Any]) -> bool:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    source_id = str(payload.get("source_id", "")).strip().lower()
    dataset_version = str(payload.get("dataset_version", "")).strip().lower()
    example_id = str(payload.get("example_id") or payload.get("id") or "").strip().lower()
    return (
        metadata.get("placeholder") is True
        or context.get("placeholder") is True
        or source_id.startswith("placeholder::synthetic")
        or "placeholder" in dataset_version
        or example_id.startswith("heldout-placeholder-")
    )


def _extract_input_examples(path: Path) -> list[InputExample]:
    if not path.exists():
        raise FileNotFoundError(f"Input dataset not found: {path}")

    rows: list[InputExample] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"Input row must be object at {path}:{line_number}")
            if _is_simulated_example(payload):
                raise ValueError(
                    "Simulated/placeholder dataset row detected at "
                    f"{path}:{line_number}. Replace with real reviewed data before labeling."
                )

            example_id = str(payload.get("example_id") or payload.get("id") or "").strip()
            if not example_id:
                example_id = f"row-{line_number:06d}"
            prompt = str(payload.get("prompt") or "").strip()
            essay = str(
                payload.get("essay") or payload.get("text") or payload.get("input") or ""
            ).strip()
            if not prompt or not essay:
                raise ValueError(
                    "Input row missing prompt/essay at "
                    f"{path}:{line_number} (example_id={example_id})"
                )

            metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
            rows.append(
                InputExample(
                    example_id=example_id,
                    prompt=prompt,
                    essay=essay,
                    score=_safe_float(payload.get("score", payload.get("gold_score"))),
                    split=_normalize_split(payload.get("split")),
                    source=str(payload.get("source", "unknown")),
                    license=str(payload.get("license", "unknown")),
                    metadata=dict(metadata),
                )
            )
    return rows


def _extract_output_object(payload: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("output", "predicted", "response_json", "raw_json_output"):
        value = payload.get(key)
        if isinstance(value, dict):
            return value

    for key in ("raw_output", "response_text", "raw_response_text"):
        value = payload.get(key)
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

    if "score" in payload and "confidence" in payload and isinstance(payload, dict):
        return payload
    return None


def _build_prediction_records(
    *,
    examples: list[InputExample],
    config: PipelineConfig,
) -> tuple[list[PredictionRecord], dict[str, dict[str, Any] | None]]:
    teacher_model_id = canonical_model_id(config.teacher_model_id)

    if config.inference_mode == "precomputed":
        if config.predictions_path is None:
            raise ValueError("--predictions-path is required when inference_mode=precomputed")
        raw_predictions = load_predictions(config.predictions_path)
        filtered = [row for row in raw_predictions if row.model_id == teacher_model_id]
        if not filtered:
            raise ValueError(
                f"No predictions found for model '{teacher_model_id}' in {config.predictions_path}"
            )
        by_id = {row.example_id: row for row in filtered}
        missing_ids = [item.example_id for item in examples if item.example_id not in by_id]
        if missing_ids:
            missing_preview = ", ".join(missing_ids[:10])
            raise ValueError(
                f"Missing predictions for {len(missing_ids)} input examples. "
                f"First missing ids: {missing_preview}"
            )
        ordered = [by_id[item.example_id] for item in examples]
        output_objects = {
            row.example_id: _extract_output_object(row.raw_payload) for row in ordered
        }
        return ordered, output_objects

    raise ValueError(
        "Unsupported inference_mode. This pipeline only supports "
        "'precomputed' teacher outputs. Run teacher inference first and pass "
        "--predictions-path."
    )


def _quality_score(result: Any) -> float:
    components = [
        1.0 if result.json_validity else 0.0,
        1.0 if not result.missing_fields else 0.0,
        1.0 if result.score_range_valid else 0.0,
        1.0 if not result.hallucinated_rubric_items else 0.0,
        1.0 if not result.unsupported_feedback else 0.0,
        float(result.reasoning_completeness),
    ]
    return mean(components)


def _load_schema(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Schema file must contain a JSON object.")
    return payload


def _type_matches(value: Any, schema_type: str) -> bool:
    if schema_type == "object":
        return isinstance(value, dict)
    if schema_type == "array":
        return isinstance(value, list)
    if schema_type == "string":
        return isinstance(value, str)
    if schema_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if schema_type == "number":
        return isinstance(value, int | float) and not isinstance(value, bool)
    if schema_type == "boolean":
        return isinstance(value, bool)
    if schema_type == "null":
        return value is None
    return True


def _validate_schema_node(payload: Any, schema: dict[str, Any], path: str = "$") -> list[str]:
    errors: list[str] = []
    schema_type = schema.get("type")
    if isinstance(schema_type, str) and not _type_matches(payload, schema_type):
        return [f"{path}: expected type '{schema_type}'"]

    if "enum" in schema and payload not in schema["enum"]:
        errors.append(f"{path}: value not in enum")

    if isinstance(payload, int | float) and not isinstance(payload, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and payload < minimum:
            errors.append(f"{path}: value {payload} < minimum {minimum}")
        if maximum is not None and payload > maximum:
            errors.append(f"{path}: value {payload} > maximum {maximum}")

    if isinstance(payload, str):
        min_length = schema.get("minLength")
        if min_length is not None and len(payload) < int(min_length):
            errors.append(f"{path}: string shorter than minLength {min_length}")

    if isinstance(payload, list):
        min_items = schema.get("minItems")
        max_items = schema.get("maxItems")
        if min_items is not None and len(payload) < int(min_items):
            errors.append(f"{path}: array shorter than minItems {min_items}")
        if max_items is not None and len(payload) > int(max_items):
            errors.append(f"{path}: array longer than maxItems {max_items}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(payload):
                errors.extend(_validate_schema_node(item, item_schema, f"{path}[{index}]"))

    if isinstance(payload, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for key in required:
                if key not in payload:
                    errors.append(f"{path}: missing required key '{key}'")

        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for key, node_schema in properties.items():
                if key in payload and isinstance(node_schema, dict):
                    errors.extend(_validate_schema_node(payload[key], node_schema, f"{path}.{key}"))

        if schema.get("additionalProperties") is False and isinstance(properties, dict):
            extra_keys = sorted(set(payload.keys()) - set(properties.keys()))
            for key in extra_keys:
                errors.append(f"{path}: additional property '{key}' not allowed")

    return errors


def _json_schema_validate(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except Exception:
        return _validate_schema_node(payload, schema, "$")

    validator = Draft202012Validator(schema)
    return sorted(error.message for error in validator.iter_errors(payload))


def _confidence_from_output(output_object: dict[str, Any] | None) -> float | None:
    if not isinstance(output_object, dict):
        return None
    confidence = output_object.get("confidence")
    if isinstance(confidence, int | float) and not isinstance(confidence, bool):
        value = float(confidence)
        return max(0.0, min(1.0, value))
    return None


def _gold_examples_for_validation(examples: list[InputExample]) -> list[GoldExample]:
    gold_rows: list[GoldExample] = []
    for item in examples:
        expected_skills = item.metadata.get("expected_reasoning_skills")
        if not isinstance(expected_skills, list):
            expected_skills = []
        expected_fallacies = item.metadata.get("expected_fallacies")
        if not isinstance(expected_fallacies, list):
            expected_fallacies = []
        rubric = item.metadata.get("rubric")
        if not isinstance(rubric, list):
            rubric = []
        notes = item.metadata.get("notes_for_reviewers")
        gold_rows.append(
            GoldExample(
                example_id=item.example_id,
                source=item.source,
                license=item.license,
                prompt=item.prompt,
                essay=item.essay,
                gold_score=item.score,
                rubric=tuple(str(value) for value in rubric),
                difficulty=str(item.metadata.get("difficulty", "unknown")),
                expected_reasoning_skills=tuple(str(value) for value in expected_skills),
                expected_fallacies=tuple(str(value) for value in expected_fallacies),
                notes_for_reviewers=str(notes) if notes is not None else "",
            )
        )
    return gold_rows


def _split_for_export(example: InputExample, *, strict_source_split: bool) -> str:
    if strict_source_split and example.split in _VALID_SPLITS:
        return str(example.split)
    if example.split in _VALID_SPLITS:
        return str(example.split)

    digest = hashlib.sha256(example.example_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _ensure_clean_split_dirs(output_root: Path) -> None:
    for split in _VALID_SPLITS:
        split_dir = output_root / split
        split_dir.mkdir(parents=True, exist_ok=True)
        data_path = split_dir / "data.jsonl"
        if data_path.exists():
            data_path.unlink()


def run_pipeline(config: PipelineConfig) -> dict[str, Any]:
    """Run full label generation pipeline and return manifest stats."""
    input_examples = _extract_input_examples(config.input_jsonl)
    schema = _load_schema(config.schema_path)
    predictions, output_map = _build_prediction_records(examples=input_examples, config=config)

    by_prediction_id = {(item.model_id, item.example_id): item for item in predictions}
    teacher_model_id = canonical_model_id(config.teacher_model_id)
    gold_index = {item.example_id: item for item in _gold_examples_for_validation(input_examples)}

    candidates: list[PipelineCandidate] = []
    for example in input_examples:
        prediction = by_prediction_id[(teacher_model_id, example.example_id)]
        output_obj = output_map.get(example.example_id)
        validation_result = validate_prediction(
            prediction,
            gold=gold_index.get(example.example_id),
        )

        quality = _quality_score(validation_result)
        notes: list[str] = []
        if validation_result.missing_fields:
            notes.append("missing_fields")
        if validation_result.hallucinated_rubric_items:
            notes.append("hallucinated_rubric_items")
        if validation_result.unsupported_feedback:
            notes.append("unsupported_feedback")

        schema_errors: list[str] = []
        schema_valid = False
        if output_obj is not None:
            schema_errors = _json_schema_validate(output_obj, schema)
            schema_valid = len(schema_errors) == 0

        confidence = _confidence_from_output(output_obj)
        candidates.append(
            PipelineCandidate(
                input_example=example,
                prediction=prediction,
                output_object=output_obj,
                validation_score=quality,
                validation_notes=notes,
                schema_valid=schema_valid,
                schema_errors=schema_errors,
                confidence=confidence,
            )
        )

    after_quality = [
        item for item in candidates if item.validation_score >= config.quality_threshold
    ]
    after_schema = [item for item in after_quality if item.schema_valid]
    after_confidence = [
        item
        for item in after_schema
        if item.confidence is not None and item.confidence >= config.confidence_threshold
    ]

    _ensure_clean_split_dirs(config.output_root)
    split_counts = {split: 0 for split in _VALID_SPLITS}
    for item in after_confidence:
        split = _split_for_export(
            item.input_example,
            strict_source_split=config.strict_source_split,
        )
        split_counts[split] += 1
        export_row = {
            "instruction": config.instruction_text,
            "input": _canonical_json(
                {
                    "prompt": item.input_example.prompt,
                    "essay": item.input_example.essay,
                    "score": item.input_example.score,
                }
            ),
            "output": _canonical_json(item.output_object or {}),
            "metadata": {
                "example_id": item.input_example.example_id,
                "teacher_model_id": item.prediction.model_id,
                "source": item.input_example.source,
                "license": item.input_example.license,
                "split": split,
                "validation_score": item.validation_score,
                "validation_notes": item.validation_notes,
                "schema_valid": item.schema_valid,
                "confidence": item.confidence,
                "latency_ms": item.prediction.latency_ms,
                "input_tokens": item.prediction.input_tokens,
                "output_tokens": item.prediction.output_tokens,
                "cost_usd": item.prediction.cost_usd,
            },
        }
        split_path = config.output_root / split / "data.jsonl"
        with split_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(export_row, ensure_ascii=False, sort_keys=True) + "\n")

    manifest = {
        "input_jsonl": str(config.input_jsonl),
        "teacher_model_id": teacher_model_id,
        "inference_mode": config.inference_mode,
        "predictions_path": str(config.predictions_path) if config.predictions_path else None,
        "schema_path": str(config.schema_path),
        "quality_threshold": config.quality_threshold,
        "confidence_threshold": config.confidence_threshold,
        "counts": {
            "input_examples": len(input_examples),
            "predictions_available": len(predictions),
            "after_validation": len(candidates),
            "after_quality_filter": len(after_quality),
            "after_schema_validation": len(after_schema),
            "after_confidence_filter": len(after_confidence),
            "export_train": split_counts["train"],
            "export_validation": split_counts["validation"],
            "export_test": split_counts["test"],
        },
        "pipeline_order": [
            "dataset",
            "teacher_inference",
            "validation",
            "quality_filter",
            "json_schema_validation",
            "confidence_filter",
            "dataset_export",
        ],
    }
    (config.output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Run production SFT label generation pipeline.")
    parser.add_argument("--input-jsonl", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--output-root", default="datasets/sft")
    parser.add_argument("--teacher-model-id", default="gpt-5")
    parser.add_argument(
        "--inference-mode",
        default="precomputed",
        choices=("precomputed",),
        help="Inference source. This script requires precomputed teacher outputs.",
    )
    parser.add_argument(
        "--predictions-path",
        default=None,
        help="JSONL file or directory of JSONL predictions (required for precomputed mode).",
    )
    parser.add_argument("--schema-path", default="teacher_prompts/output_schema.json")
    parser.add_argument("--quality-threshold", type=float, default=0.80)
    parser.add_argument("--confidence-threshold", type=float, default=0.60)
    parser.add_argument(
        "--strict-source-split",
        action="store_true",
        help="Require valid input split labels; otherwise deterministic hash split is used.",
    )
    parser.add_argument(
        "--instruction-text",
        default=_DEFAULT_INSTRUCTION,
        help="Instruction string written to every exported SFT example.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    config = PipelineConfig(
        input_jsonl=Path(args.input_jsonl),
        output_root=Path(args.output_root),
        teacher_model_id=args.teacher_model_id,
        inference_mode=args.inference_mode,
        predictions_path=Path(args.predictions_path) if args.predictions_path else None,
        schema_path=Path(args.schema_path),
        quality_threshold=float(args.quality_threshold),
        confidence_threshold=float(args.confidence_threshold),
        strict_source_split=bool(args.strict_source_split),
        instruction_text=str(args.instruction_text),
    )
    manifest = run_pipeline(config)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
