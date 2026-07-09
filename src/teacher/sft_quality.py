"""Post-label quality checks for SFT exports.

Checks:
- duplicate labels
- identical reasoning
- identical feedback
- low-confidence outputs
- hallucinations (heuristic via teacher validation rules)
- schema validity
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .io import GoldExample, PredictionRecord
from .validation import validate_prediction

_SPLITS: tuple[str, ...] = ("train", "validation", "test")


@dataclass(frozen=True)
class SFTExample:
    """One SFT row loaded from split files."""

    split: str
    line_number: int
    instruction: str
    input_raw: str
    output_raw: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class SFTQualitySummary:
    """Aggregated post-label quality summary."""

    dataset_found: bool
    examples_total: int
    duplicates_count: int
    duplicate_example_ids: tuple[str, ...]
    identical_reasoning_count: int
    identical_feedback_count: int
    low_confidence_count: int
    low_confidence_rate: float
    hallucination_count: int
    hallucination_rate: float
    schema_invalid_count: int
    schema_valid_rate: float
    avg_confidence: float | None
    confidence_threshold: float
    notes: str


def _json_schema_validate(payload: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except Exception:
        # Minimal fallback: check required fields only.
        required = schema.get("required", [])
        errors = []
        if isinstance(required, list):
            for key in required:
                if key not in payload:
                    errors.append(f"missing required key '{key}'")
        return errors

    validator = Draft202012Validator(schema)
    return sorted(error.message for error in validator.iter_errors(payload))


def load_sft_examples(sft_root: Path) -> list[SFTExample]:
    """Load SFT rows from datasets/sft/{split}/data.jsonl."""
    examples: list[SFTExample] = []
    for split in _SPLITS:
        split_path = sft_root / split / "data.jsonl"
        if not split_path.exists():
            continue
        with split_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                raw = line.strip()
                if not raw:
                    continue
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise ValueError(f"Invalid row at {split_path}:{line_number}, expected object.")
                examples.append(
                    SFTExample(
                        split=split,
                        line_number=line_number,
                        instruction=str(payload.get("instruction", "")),
                        input_raw=str(payload.get("input", "")),
                        output_raw=str(payload.get("output", "")),
                        metadata=(
                            payload.get("metadata")
                            if isinstance(payload.get("metadata"), dict)
                            else {}
                        ),
                    )
                )
    return examples


def _parse_json_object(raw: str) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _extract_example_id(item: SFTExample) -> str:
    value = item.metadata.get("example_id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"{item.split}:{item.line_number}"


def _reasoning_blob(output_obj: dict[str, Any]) -> str:
    value = output_obj.get("reasoning")
    if isinstance(value, dict):
        return _canonical(value)
    return ""


def _feedback_blob(output_obj: dict[str, Any]) -> str:
    value = output_obj.get("feedback")
    if isinstance(value, dict):
        return _canonical(value)
    return ""


def _build_validation_pair(
    item: SFTExample, output_obj: dict[str, Any]
) -> tuple[PredictionRecord, GoldExample]:
    example_id = _extract_example_id(item)
    input_obj = _parse_json_object(item.input_raw) or {}
    prompt = str(input_obj.get("prompt", ""))
    essay = str(input_obj.get("essay", ""))
    score_raw = input_obj.get("score")
    score = None
    if isinstance(score_raw, int | float) and not isinstance(score_raw, bool):
        score = float(score_raw)

    prediction = PredictionRecord(
        model_id=str(item.metadata.get("teacher_model_id", "unknown")),
        example_id=example_id,
        predicted_score=(
            float(output_obj["score"]) if isinstance(output_obj.get("score"), int | float) else None
        ),
        rubric_items=tuple(),
        rubric_score=None,
        reasoning_skills=tuple(),
        reasoning_score=None,
        argument_quality_score=None,
        predicted_fallacies=tuple(),
        feedback_text=json.dumps(output_obj.get("feedback", {}), ensure_ascii=False),
        json_valid=True,
        latency_ms=None,
        input_tokens=0,
        output_tokens=0,
        cost_usd=None,
        raw_payload={"output": output_obj},
    )
    gold = GoldExample(
        example_id=example_id,
        source=str(item.metadata.get("source", "unknown")),
        license=str(item.metadata.get("license", "unknown")),
        prompt=prompt,
        essay=essay,
        gold_score=score,
        rubric=tuple(),
        difficulty=str(item.metadata.get("difficulty", "unknown")),
        expected_reasoning_skills=tuple(),
        expected_fallacies=tuple(),
        notes_for_reviewers="",
    )
    return prediction, gold


def analyze_sft_quality(
    *,
    sft_root: Path,
    schema_path: Path,
    confidence_threshold: float = 0.6,
) -> SFTQualitySummary:
    """Compute post-label quality checks over SFT export rows."""
    if not sft_root.exists():
        return SFTQualitySummary(
            dataset_found=False,
            examples_total=0,
            duplicates_count=0,
            duplicate_example_ids=(),
            identical_reasoning_count=0,
            identical_feedback_count=0,
            low_confidence_count=0,
            low_confidence_rate=0.0,
            hallucination_count=0,
            hallucination_rate=0.0,
            schema_invalid_count=0,
            schema_valid_rate=0.0,
            avg_confidence=None,
            confidence_threshold=confidence_threshold,
            notes="datasets/sft not found; checks were not executed.",
        )

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError(f"Invalid schema file: {schema_path}")

    examples = load_sft_examples(sft_root)
    if not examples:
        return SFTQualitySummary(
            dataset_found=True,
            examples_total=0,
            duplicates_count=0,
            duplicate_example_ids=(),
            identical_reasoning_count=0,
            identical_feedback_count=0,
            low_confidence_count=0,
            low_confidence_rate=0.0,
            hallucination_count=0,
            hallucination_rate=0.0,
            schema_invalid_count=0,
            schema_valid_rate=0.0,
            avg_confidence=None,
            confidence_threshold=confidence_threshold,
            notes="No rows found under datasets/sft/*/data.jsonl.",
        )

    by_output: dict[str, list[str]] = {}
    by_reasoning: dict[str, list[str]] = {}
    by_feedback: dict[str, list[str]] = {}
    confidence_values: list[float] = []
    low_confidence_count = 0
    schema_invalid_count = 0
    hallucination_count = 0

    for item in examples:
        example_id = _extract_example_id(item)
        output_obj = _parse_json_object(item.output_raw)
        if output_obj is None:
            schema_invalid_count += 1
            low_confidence_count += 1
            continue

        by_output.setdefault(_canonical(output_obj), []).append(example_id)

        reasoning_blob = _reasoning_blob(output_obj)
        if reasoning_blob:
            by_reasoning.setdefault(reasoning_blob, []).append(example_id)

        feedback_blob = _feedback_blob(output_obj)
        if feedback_blob:
            by_feedback.setdefault(feedback_blob, []).append(example_id)

        schema_errors = _json_schema_validate(output_obj, schema)
        if schema_errors:
            schema_invalid_count += 1

        confidence = output_obj.get("confidence")
        if isinstance(confidence, int | float) and not isinstance(confidence, bool):
            value = max(0.0, min(1.0, float(confidence)))
            confidence_values.append(value)
            if value < confidence_threshold:
                low_confidence_count += 1
        else:
            low_confidence_count += 1

        prediction, gold = _build_validation_pair(item, output_obj)
        validation_result = validate_prediction(prediction, gold=gold)
        if validation_result.hallucinated_rubric_items or validation_result.unsupported_feedback:
            hallucination_count += 1

    duplicate_ids: list[str] = []
    duplicates_count = 0
    for ids in by_output.values():
        if len(ids) > 1:
            duplicates_count += len(ids)
            duplicate_ids.extend(ids)

    identical_reasoning_count = sum(len(ids) for ids in by_reasoning.values() if len(ids) > 1)
    identical_feedback_count = sum(len(ids) for ids in by_feedback.values() if len(ids) > 1)

    total = len(examples)
    schema_valid_rate = (total - schema_invalid_count) / total if total else 0.0
    low_confidence_rate = low_confidence_count / total if total else 0.0
    hallucination_rate = hallucination_count / total if total else 0.0

    return SFTQualitySummary(
        dataset_found=True,
        examples_total=total,
        duplicates_count=duplicates_count,
        duplicate_example_ids=tuple(sorted(set(duplicate_ids))),
        identical_reasoning_count=identical_reasoning_count,
        identical_feedback_count=identical_feedback_count,
        low_confidence_count=low_confidence_count,
        low_confidence_rate=low_confidence_rate,
        hallucination_count=hallucination_count,
        hallucination_rate=hallucination_rate,
        schema_invalid_count=schema_invalid_count,
        schema_valid_rate=schema_valid_rate,
        avg_confidence=(mean(confidence_values) if confidence_values else None),
        confidence_threshold=confidence_threshold,
        notes="Checks executed successfully.",
    )


def render_markdown_report(summary: SFTQualitySummary) -> str:
    """Render markdown report for SFT quality checks."""
    lines = [
        "# SFT Post-Label Quality Report",
        "",
        "## Scope",
        "",
        "- duplicate labels",
        "- identical reasoning",
        "- identical feedback",
        "- low-confidence outputs",
        "- hallucinations (heuristic)",
        "- schema validity",
        "",
        "## Status",
        "",
        f"- dataset_found: `{summary.dataset_found}`",
        f"- notes: {summary.notes}",
        "",
        "## Summary Metrics",
        "",
        f"- examples_total: `{summary.examples_total}`",
        f"- duplicates_count: `{summary.duplicates_count}`",
        f"- identical_reasoning_count: `{summary.identical_reasoning_count}`",
        f"- identical_feedback_count: `{summary.identical_feedback_count}`",
        f"- low_confidence_count: `{summary.low_confidence_count}`",
        f"- low_confidence_rate: `{summary.low_confidence_rate:.4f}`",
        f"- hallucination_count: `{summary.hallucination_count}`",
        f"- hallucination_rate: `{summary.hallucination_rate:.4f}`",
        f"- schema_invalid_count: `{summary.schema_invalid_count}`",
        f"- schema_valid_rate: `{summary.schema_valid_rate:.4f}`",
        f"- avg_confidence: `{summary.avg_confidence}`",
        f"- confidence_threshold: `{summary.confidence_threshold}`",
    ]

    if summary.duplicate_example_ids:
        lines.extend(
            [
                "",
                "## Duplicate Example IDs",
                "",
                ", ".join(summary.duplicate_example_ids),
            ]
        )

    return "\n".join(lines) + "\n"


def write_report(path: Path, summary: SFTQualitySummary) -> None:
    """Write markdown report and adjacent json summary."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown_report(summary), encoding="utf-8")
    json_path = path.with_suffix(".json")
    json_payload = json.dumps(asdict(summary), ensure_ascii=False, indent=2)
    json_path.write_text(json_payload, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Post-label SFT quality checks.")
    parser.add_argument("--sft-root", default="datasets/sft")
    parser.add_argument("--schema-path", default="teacher_prompts/output_schema.json")
    parser.add_argument("--confidence-threshold", type=float, default=0.6)
    parser.add_argument("--report-path", default="docs/reports/sft_quality.md")
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    summary = analyze_sft_quality(
        sft_root=Path(args.sft_root),
        schema_path=Path(args.schema_path),
        confidence_threshold=float(args.confidence_threshold),
    )
    report_path = Path(args.report_path)
    write_report(report_path, summary)
    print(json.dumps(asdict(summary), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
