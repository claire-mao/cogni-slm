"""Merge reviewed teacher outputs into a validated gold dataset package.

Pipeline:
teacher outputs -> human edits -> gold corrections -> quality validation -> gold dataset

This module does not call external model APIs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.teacher.io import GoldExample, PredictionRecord, load_gold_examples
from src.teacher.validation import validate_prediction

APPROVED_DECISIONS = {"accept", "edit", "approved"}


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


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    parsed = _safe_float(value)
    return int(parsed) if parsed is not None else default


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
                raise ValueError(f"Expected JSON object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def _path_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def _record_sha256(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_approved_reviews(path: Path) -> list[dict[str, Any]]:
    rows = _read_jsonl(path)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        decision = _normalize_text(row.get("decision")).lower()
        if decision and decision not in APPROVED_DECISIONS:
            continue
        filtered.append(row)
    return filtered


def _load_corrections(path: Path) -> dict[str, dict[str, Any]]:
    rows = _read_jsonl(path)
    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        case_id = _normalize_text(row.get("case_id"))
        example_id = _normalize_text(row.get("example_id"))
        key = case_id or example_id
        if not key:
            continue
        indexed[key] = row
    return indexed


def _resolve_label(row: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("merged_label", "edited_output", "gold_label", "output_json"):
        candidate = row.get(key)
        if isinstance(candidate, dict):
            return dict(candidate)
    teacher_output = row.get("teacher_output")
    if isinstance(teacher_output, dict):
        output_json = teacher_output.get("output_json")
        if isinstance(output_json, dict):
            return dict(output_json)
    return None


def _apply_correction(
    *,
    row: dict[str, Any],
    label: dict[str, Any],
    corrections: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    case_id = _normalize_text(row.get("case_id"))
    example_id = _normalize_text(row.get("example_id"))
    correction = corrections.get(case_id) or corrections.get(example_id)
    if not correction:
        return label, False

    patched = dict(label)
    patch_obj = correction.get("gold_label_patch")
    if isinstance(patch_obj, dict):
        patched.update(patch_obj)

    override_obj = correction.get("gold_label")
    if isinstance(override_obj, dict):
        patched = dict(override_obj)
    return patched, True


def _fallback_example_id(row: dict[str, Any], index: int) -> str:
    for key in ("example_id", "gold_example_id", "id"):
        value = _normalize_text(row.get(key))
        if value:
            return value
    return f"gold-v1-{index:06d}"


def _to_prediction(
    *,
    row: dict[str, Any],
    label: dict[str, Any],
    example_id: str,
) -> PredictionRecord:
    feedback = label.get("feedback")
    feedback_text = ""
    if isinstance(feedback, dict):
        text_parts: list[str] = []
        strengths = feedback.get("strengths")
        if isinstance(strengths, list):
            text_parts.extend(_normalize_text(item) for item in strengths)
        priorities = feedback.get("priorities")
        if isinstance(priorities, list):
            text_parts.extend(_normalize_text(item) for item in priorities)
        summary = feedback.get("student_facing_summary")
        if isinstance(summary, str):
            text_parts.append(_normalize_text(summary))
        feedback_text = " ".join(item for item in text_parts if item)
    else:
        feedback_text = _normalize_text(feedback)

    predicted_fallacies: list[str] = []
    fallacies = label.get("fallacies")
    if isinstance(fallacies, dict):
        primary = _normalize_text(fallacies.get("primary"))
        if primary:
            predicted_fallacies.append(primary)
        secondary = fallacies.get("secondary")
        if isinstance(secondary, list):
            predicted_fallacies.extend(
                _normalize_text(item) for item in secondary if _normalize_text(item)
            )

    return PredictionRecord(
        model_id=_normalize_text(row.get("selected_teacher_model"))
        or _normalize_text(row.get("model"))
        or "unknown",
        example_id=example_id,
        predicted_score=_safe_float(label.get("score")),
        rubric_items=tuple(),
        rubric_score=None,
        reasoning_skills=tuple(),
        reasoning_score=None,
        argument_quality_score=None,
        predicted_fallacies=tuple(predicted_fallacies),
        feedback_text=feedback_text,
        json_valid=True,
        latency_ms=_safe_float(row.get("latency_ms")),
        input_tokens=_safe_int(row.get("input_tokens"), default=0),
        output_tokens=_safe_int(row.get("output_tokens"), default=0),
        cost_usd=_safe_float(row.get("estimated_cost_usd")),
        raw_payload={
            "output": label,
            "response_text": json.dumps(label, ensure_ascii=False),
        },
    )


def _validate_row(
    *,
    row: dict[str, Any],
    label: dict[str, Any],
    example_id: str,
    gold_index: dict[str, GoldExample],
) -> dict[str, Any]:
    prediction = _to_prediction(row=row, label=label, example_id=example_id)
    result = validate_prediction(prediction, gold=gold_index.get(example_id))
    passed = (
        result.json_validity
        and not result.missing_fields
        and result.score_range_valid
        and not result.hallucinated_rubric_items
        and not result.unsupported_feedback
        and result.reasoning_completeness >= 0.67
    )
    return {
        "passed": passed,
        "result": asdict(result),
        "quality_flags": {
            "json_validity": result.json_validity,
            "missing_fields": list(result.missing_fields),
            "score_range_valid": result.score_range_valid,
            "hallucinated_rubric_items": list(result.hallucinated_rubric_items),
            "unsupported_feedback": result.unsupported_feedback,
            "reasoning_completeness": result.reasoning_completeness,
        },
    }


def _build_gold_record(
    *,
    row: dict[str, Any],
    label: dict[str, Any],
    example_id: str,
    corrected: bool,
    index: int,
) -> dict[str, Any]:
    gold_answer = row.get("gold_answer") if isinstance(row.get("gold_answer"), dict) else {}
    notes = _normalize_text(gold_answer.get("notes")) or _normalize_text(row.get("notes"))

    review_meta = {
        "review_id": _normalize_text(row.get("review_id")),
        "reviewer_id": _normalize_text(row.get("reviewer_id")) or "anonymous",
        "created_at": _normalize_text(row.get("created_at")),
        "decision": _normalize_text(row.get("decision")).lower() or "approved",
        "selected_teacher_model": _normalize_text(row.get("selected_teacher_model")),
        "correction_applied": corrected,
    }

    record = {
        "example_id": example_id or f"gold-v1-{index:06d}",
        "source": _normalize_text(row.get("source")) or "unknown",
        "license": _normalize_text(row.get("license")) or "unspecified",
        "difficulty": _normalize_text(row.get("difficulty")) or "unknown",
        "prompt": _normalize_text(row.get("prompt")),
        "essay": _normalize_text(row.get("essay")),
        "gold_score": label.get("score", gold_answer.get("score")),
        "rubric": label.get("rubric", gold_answer.get("rubric")),
        "expected_reasoning_skills": gold_answer.get("expected_reasoning_skills"),
        "expected_fallacies": gold_answer.get("expected_fallacies", label.get("fallacies")),
        "notes_for_reviewers": notes,
        "gold_label": label,
        "review_metadata": review_meta,
        "provenance": {
            "case_id": _normalize_text(row.get("case_id")),
            "run_id": _normalize_text(row.get("run_id")),
            "task_id": _normalize_text(row.get("task_id")),
            "seed": row.get("seed"),
            "temperature": _safe_float(row.get("temperature")),
            "prompt_version": _normalize_text(row.get("prompt_version")),
        },
    }
    record["record_checksum_sha256"] = _record_sha256(record)
    return record


def run_merge_pipeline(
    *,
    approved_reviews_path: Path,
    gold_source_path: Path,
    corrections_path: Path | None,
    output_dir: Path,
) -> dict[str, Any]:
    approved_rows = _load_approved_reviews(approved_reviews_path)
    gold_examples = load_gold_examples(gold_source_path) if gold_source_path.exists() else []
    gold_index = {row.example_id: row for row in gold_examples}
    corrections = _load_corrections(corrections_path) if corrections_path else {}

    validated_rows: list[dict[str, Any]] = []
    accepted_gold_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []

    corrected_count = 0
    missing_label_count = 0

    stable_rows = sorted(
        approved_rows,
        key=lambda row: (
            _normalize_text(row.get("example_id")),
            _normalize_text(row.get("case_id")),
            _normalize_text(row.get("review_id")),
        ),
    )

    for index, row in enumerate(stable_rows, start=1):
        example_id = _fallback_example_id(row, index)
        label = _resolve_label(row)
        if label is None:
            missing_label_count += 1
            rejected_rows.append(
                {
                    "example_id": example_id,
                    "case_id": _normalize_text(row.get("case_id")),
                    "reason": "missing_label",
                    "row": row,
                }
            )
            continue

        corrected_label, corrected = _apply_correction(
            row=row,
            label=label,
            corrections=corrections,
        )
        if corrected:
            corrected_count += 1

        validation = _validate_row(
            row=row,
            label=corrected_label,
            example_id=example_id,
            gold_index=gold_index,
        )
        validated_rows.append(
            {
                "example_id": example_id,
                "case_id": _normalize_text(row.get("case_id")),
                "review_id": _normalize_text(row.get("review_id")),
                "passed": validation["passed"],
                "quality_flags": validation["quality_flags"],
                "validation": validation["result"],
                "correction_applied": corrected,
            }
        )

        if not validation["passed"]:
            rejected_rows.append(
                {
                    "example_id": example_id,
                    "case_id": _normalize_text(row.get("case_id")),
                    "reason": "failed_quality_validation",
                    "quality_flags": validation["quality_flags"],
                    "row": row,
                }
            )
            continue

        accepted_gold_rows.append(
            _build_gold_record(
                row=row,
                label=corrected_label,
                example_id=example_id,
                corrected=corrected,
                index=index,
            )
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    gold_dataset_path = output_dir / "gold_dataset.jsonl"
    validation_path = output_dir / "quality_validation.jsonl"
    rejected_path = output_dir / "rejected_after_validation.jsonl"
    checksums_path = output_dir / "checksums.json"
    manifest_path = output_dir / "manifest.json"
    summary_path = output_dir / "summary.md"

    _write_jsonl(gold_dataset_path, accepted_gold_rows)
    _write_jsonl(validation_path, validated_rows)
    _write_jsonl(rejected_path, rejected_rows)

    checksums = {
        "approved_reviews_sha256": _path_sha256(approved_reviews_path),
        "gold_source_sha256": _path_sha256(gold_source_path),
        "corrections_sha256": _path_sha256(corrections_path) if corrections_path else "",
        "gold_dataset_sha256": _path_sha256(gold_dataset_path),
        "quality_validation_sha256": _path_sha256(validation_path),
        "rejected_after_validation_sha256": _path_sha256(rejected_path),
        "record_checksums_sha256": hashlib.sha256(
            "\n".join(row["record_checksum_sha256"] for row in accepted_gold_rows).encode("utf-8")
        ).hexdigest(),
    }
    _write_json(checksums_path, checksums)

    validation_passed = sum(1 for row in validated_rows if row["passed"])
    manifest = {
        "schema_version": "gold_merge_v1",
        "created_at_utc": _utc_now(),
        "pipeline": [
            "teacher_outputs",
            "human_edits",
            "gold_corrections",
            "quality_validation",
            "gold_dataset",
        ],
        "inputs": {
            "approved_reviews_path": str(approved_reviews_path),
            "gold_source_path": str(gold_source_path),
            "corrections_path": str(corrections_path) if corrections_path else None,
        },
        "outputs": {
            "output_dir": str(output_dir),
            "gold_dataset_jsonl": str(gold_dataset_path),
            "quality_validation_jsonl": str(validation_path),
            "rejected_after_validation_jsonl": str(rejected_path),
            "checksums_json": str(checksums_path),
            "summary_md": str(summary_path),
        },
        "counts": {
            "approved_rows_seen": len(approved_rows),
            "rows_missing_label": missing_label_count,
            "rows_validated": len(validated_rows),
            "rows_passed_validation": validation_passed,
            "rows_failed_validation": len(validated_rows) - validation_passed,
            "rows_rejected_total": len(rejected_rows),
            "gold_rows_written": len(accepted_gold_rows),
            "rows_corrected": corrected_count,
        },
        "checksums": checksums,
    }
    _write_json(manifest_path, manifest)

    summary_lines = [
        "# Gold Dataset v1 Summary",
        "",
        f"- created_at_utc: `{manifest['created_at_utc']}`",
        f"- approved_reviews_path: `{approved_reviews_path}`",
        f"- gold_source_path: `{gold_source_path}`",
        f"- corrections_path: `{corrections_path if corrections_path else ''}`",
        "",
        "## Counts",
        "",
        f"- approved_rows_seen: `{len(approved_rows)}`",
        f"- rows_validated: `{len(validated_rows)}`",
        f"- rows_passed_validation: `{validation_passed}`",
        f"- rows_failed_validation: `{len(validated_rows) - validation_passed}`",
        f"- gold_rows_written: `{len(accepted_gold_rows)}`",
        f"- rows_corrected: `{corrected_count}`",
        "",
        "## Artifacts",
        "",
        "- `gold_dataset.jsonl`",
        "- `quality_validation.jsonl`",
        "- `rejected_after_validation.jsonl`",
        "- `manifest.json`",
        "- `checksums.json`",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge reviewed teacher outputs into datasets/gold/v1 package."
    )
    parser.add_argument(
        "--approved-reviews-path",
        default="datasets/review/final/review_dataset.jsonl",
    )
    parser.add_argument(
        "--gold-source-path",
        default="datasets/gold/review_package/review_forms.jsonl",
    )
    parser.add_argument(
        "--corrections-path",
        default="datasets/review/final/gold_corrections.jsonl",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/gold/v1",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    corrections_path = Path(args.corrections_path)
    manifest = run_merge_pipeline(
        approved_reviews_path=Path(args.approved_reviews_path),
        gold_source_path=Path(args.gold_source_path),
        corrections_path=corrections_path if corrections_path.exists() else None,
        output_dir=Path(args.output_dir),
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
