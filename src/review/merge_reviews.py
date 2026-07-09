"""Merge human review decisions into a final reviewed dataset.

This module:
- reads review decisions from datasets/review
- reconstructs review cases from teacher outputs
- applies latest decisions (accept/reject/edit)
- merges accepted edits into datasets/review/final

No model inference is executed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return payload


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


def _parse_iso8601(value: Any) -> datetime:
    raw = _normalize_text(value)
    if not raw:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


@dataclass(frozen=True)
class TeacherOutput:
    """One teacher output row resolved for review merging."""

    model: str
    run_id: str
    task_id: str
    example_id: str
    seed: int
    temperature: float
    prompt_version: str
    output_json: dict[str, Any] | None
    raw_row: dict[str, Any]


def _build_gold_index(gold_path: Path) -> dict[str, dict[str, Any]]:
    rows = _read_jsonl(gold_path)
    index: dict[str, dict[str, Any]] = {}
    for i, row in enumerate(rows, start=1):
        example_id = _normalize_text(row.get("example_id") or row.get("id")) or f"gold-{i:06d}"
        index[example_id] = {
            "example_id": example_id,
            "source": _normalize_text(row.get("source")) or "unknown",
            "difficulty": _normalize_text(row.get("difficulty")) or "unknown",
            "prompt": _normalize_text(row.get("prompt") or row.get("prompt_text")),
            "essay": _normalize_text(
                row.get("essay") or row.get("essay_text") or row.get("text") or row.get("input")
            ),
            "gold_answer": {
                "score": row.get("gold_score", row.get("score")),
                "rubric": row.get("rubric", row.get("gold_rubric_items")),
                "expected_fallacies": row.get(
                    "expected_fallacies",
                    row.get("gold_fallacy_label"),
                ),
                "notes": row.get("notes_for_reviewers", row.get("reviewer_notes")),
            },
        }
    return index


def _load_teacher_outputs(
    *,
    runs_root: Path,
    source_run_id: str | None,
) -> list[TeacherOutput]:
    run_dirs: list[Path] = []
    if source_run_id:
        selected = runs_root / source_run_id
        if selected.exists() and selected.is_dir():
            run_dirs = [selected]
    else:
        if runs_root.exists() and runs_root.is_dir():
            run_dirs = [
                path
                for path in sorted(runs_root.iterdir())
                if path.is_dir() and (path / "responses.jsonl").exists()
            ]

    rows: list[TeacherOutput] = []
    for run_dir in run_dirs:
        for raw in _read_jsonl(run_dir / "responses.jsonl"):
            model = _normalize_text(raw.get("model"))
            task_id = _normalize_text(raw.get("task_id"))
            example_id = _normalize_text(raw.get("example_id"))
            if not model or not task_id or not example_id:
                continue

            output_json = raw.get("raw_json_output")
            if not isinstance(output_json, dict):
                output_json = None

            rows.append(
                TeacherOutput(
                    model=model,
                    run_id=run_dir.name,
                    task_id=task_id,
                    example_id=example_id,
                    seed=_safe_int(raw.get("seed"), default=0),
                    temperature=float(_safe_float(raw.get("temperature")) or 0.0),
                    prompt_version=_normalize_text(raw.get("prompt_version")) or "unknown",
                    output_json=output_json,
                    raw_row=dict(raw),
                )
            )
    return rows


def _case_id(
    *,
    run_id: str,
    task_id: str,
    example_id: str,
    seed: int,
    temperature: float,
    prompt_version: str,
) -> str:
    hash_key = "|".join(
        [
            run_id,
            task_id,
            example_id,
            str(seed),
            f"{temperature:.4f}",
            prompt_version,
        ]
    )
    return hashlib.sha1(hash_key.encode("utf-8")).hexdigest()[:16]


def _build_case_index(
    *,
    outputs: list[TeacherOutput],
    gold_index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[tuple[str, str, str, int, float, str], list[TeacherOutput]] = {}
    for row in outputs:
        key = (
            row.run_id,
            row.task_id,
            row.example_id,
            row.seed,
            row.temperature,
            row.prompt_version,
        )
        grouped.setdefault(key, []).append(row)

    cases: dict[str, dict[str, Any]] = {}
    for key, rows in grouped.items():
        run_id, task_id, example_id, seed, temperature, prompt_version = key
        resolved_rows = sorted(rows, key=lambda item: item.model)
        case_id = _case_id(
            run_id=run_id,
            task_id=task_id,
            example_id=example_id,
            seed=seed,
            temperature=temperature,
            prompt_version=prompt_version,
        )
        gold = gold_index.get(example_id, {})
        cases[case_id] = {
            "case_id": case_id,
            "run_id": run_id,
            "task_id": task_id,
            "example_id": example_id,
            "seed": seed,
            "temperature": temperature,
            "prompt_version": prompt_version,
            "prompt": gold.get("prompt", ""),
            "essay": gold.get("essay", ""),
            "source": gold.get("source", "unknown"),
            "difficulty": gold.get("difficulty", "unknown"),
            "gold_answer": gold.get("gold_answer", {}),
            "teacher_outputs": [
                {
                    "model": item.model,
                    "output_json": item.output_json,
                    "raw_row": item.raw_row,
                }
                for item in resolved_rows
            ],
        }
    return cases


def _load_latest_reviews(reviews_root: Path) -> dict[str, dict[str, Any]]:
    latest_path = reviews_root / "latest_reviews.json"
    reviews_path = reviews_root / "reviews.jsonl"

    if latest_path.exists():
        payload = _read_json(latest_path)
        latest: dict[str, dict[str, Any]] = {}
        for case_id, row in payload.items():
            if isinstance(case_id, str) and isinstance(row, dict):
                latest[case_id] = row
        if latest:
            return latest

    # Fallback to deterministic latest-by-created_at reduction.
    latest: dict[str, dict[str, Any]] = {}
    for row in _read_jsonl(reviews_path):
        case_id = _normalize_text(row.get("case_id"))
        if not case_id:
            continue
        prev = latest.get(case_id)
        if prev is None:
            latest[case_id] = row
            continue
        prev_time = _parse_iso8601(prev.get("created_at"))
        curr_time = _parse_iso8601(row.get("created_at"))
        if curr_time >= prev_time:
            latest[case_id] = row
    return latest


def _select_teacher_output(
    case: dict[str, Any],
    selected_model: str | None,
) -> dict[str, Any] | None:
    outputs = case.get("teacher_outputs")
    if not isinstance(outputs, list) or not outputs:
        return None
    if selected_model:
        for row in outputs:
            if isinstance(row, dict) and _normalize_text(row.get("model")) == selected_model:
                return row
    first = outputs[0]
    return first if isinstance(first, dict) else None


def _rubric_correction_applied(
    *,
    decision: str,
    flags: dict[str, Any],
    merged_label: dict[str, Any] | None,
    original_label: dict[str, Any] | None,
) -> bool:
    if bool(flags.get("rubric_error", False)):
        return True
    if decision != "edit":
        return False
    if not isinstance(merged_label, dict):
        return False
    if not isinstance(original_label, dict):
        return False
    return merged_label.get("rubric") != original_label.get("rubric")


def merge_reviews(
    *,
    gold_path: Path,
    runs_root: Path,
    reviews_root: Path,
    output_root: Path,
    source_run_id: str | None,
) -> dict[str, Any]:
    """Merge latest review decisions into review/final dataset artifacts."""
    output_root.mkdir(parents=True, exist_ok=True)

    gold_index = _build_gold_index(gold_path)
    outputs = _load_teacher_outputs(runs_root=runs_root, source_run_id=source_run_id)
    cases = _build_case_index(outputs=outputs, gold_index=gold_index)
    latest_reviews = _load_latest_reviews(reviews_root)

    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    unresolved_rows: list[dict[str, Any]] = []

    hallucination_count = 0
    rubric_error_count = 0

    for case_id, review in sorted(latest_reviews.items()):
        case = cases.get(case_id)
        if case is None:
            unresolved_rows.append(
                {
                    "case_id": case_id,
                    "reason": "case_not_found",
                    "review": review,
                }
            )
            continue

        decision = _normalize_text(review.get("decision")).lower()
        flags = review.get("flags") if isinstance(review.get("flags"), dict) else {}
        selected_model = _normalize_text(review.get("selected_teacher_model")) or None

        selected = _select_teacher_output(case, selected_model)
        original_label = selected.get("output_json") if isinstance(selected, dict) else None
        edited_output = review.get("edited_output")
        if decision == "edit" and isinstance(edited_output, dict):
            merged_label = edited_output
        else:
            merged_label = original_label

        if bool(flags.get("hallucination", False)):
            hallucination_count += 1
        if bool(flags.get("rubric_error", False)):
            rubric_error_count += 1

        row = {
            "case_id": case_id,
            "review_id": _normalize_text(review.get("review_id")),
            "created_at": _normalize_text(review.get("created_at")),
            "decision": decision,
            "reviewer_id": _normalize_text(review.get("reviewer_id")) or "anonymous",
            "run_id": case.get("run_id"),
            "task_id": case.get("task_id"),
            "example_id": case.get("example_id"),
            "seed": case.get("seed"),
            "temperature": case.get("temperature"),
            "prompt_version": case.get("prompt_version"),
            "source": case.get("source"),
            "difficulty": case.get("difficulty"),
            "prompt": case.get("prompt"),
            "essay": case.get("essay"),
            "gold_answer": case.get("gold_answer"),
            "selected_teacher_model": selected_model,
            "teacher_output": selected,
            "merged_label": merged_label,
            "flags": {
                "hallucination": bool(flags.get("hallucination", False)),
                "rubric_error": bool(flags.get("rubric_error", False)),
            },
            "rubric_correction_applied": _rubric_correction_applied(
                decision=decision,
                flags=flags,
                merged_label=merged_label if isinstance(merged_label, dict) else None,
                original_label=original_label if isinstance(original_label, dict) else None,
            ),
            "notes": _normalize_text(review.get("notes")),
        }

        if decision in {"accept", "edit"}:
            # Only accepted rows are merged into final review dataset.
            accepted_rows.append(row)
        elif decision == "reject":
            rejected_rows.append(row)
        else:
            unresolved_rows.append(
                {
                    "case_id": case_id,
                    "reason": f"unknown_decision:{decision}",
                    "review": review,
                }
            )

    accepted_path = output_root / "merged_accepted.jsonl"
    rejected_path = output_root / "rejected.jsonl"
    unresolved_path = output_root / "unresolved.jsonl"
    final_dataset_path = output_root / "review_dataset.jsonl"
    summary_path = output_root / "summary.json"
    manifest_path = output_root / "manifest.json"

    _write_jsonl(accepted_path, accepted_rows)
    _write_jsonl(rejected_path, rejected_rows)
    _write_jsonl(unresolved_path, unresolved_rows)
    _write_jsonl(final_dataset_path, accepted_rows)

    summary = {
        "created_at_utc": _utc_now(),
        "source_run_id": source_run_id,
        "reviews_total": len(latest_reviews),
        "cases_resolved": len(cases),
        "accepted_or_edited_total": len(accepted_rows),
        "rejected_total": len(rejected_rows),
        "unresolved_total": len(unresolved_rows),
        "hallucination_flags_total": hallucination_count,
        "rubric_error_flags_total": rubric_error_count,
    }
    _write_json(summary_path, summary)

    manifest = {
        "schema_version": "v1",
        "stage": "review_merge",
        "created_at_utc": summary["created_at_utc"],
        "inputs": {
            "gold_path": str(gold_path),
            "runs_root": str(runs_root),
            "reviews_root": str(reviews_root),
            "source_run_id": source_run_id,
        },
        "outputs": {
            "merged_accepted_jsonl": str(accepted_path),
            "review_dataset_jsonl": str(final_dataset_path),
            "rejected_jsonl": str(rejected_path),
            "unresolved_jsonl": str(unresolved_path),
            "summary_json": str(summary_path),
        },
        "counts": {
            "reviews_total": summary["reviews_total"],
            "accepted_or_edited_total": summary["accepted_or_edited_total"],
            "rejected_total": summary["rejected_total"],
            "unresolved_total": summary["unresolved_total"],
        },
        "flags": {
            "hallucination_flags_total": summary["hallucination_flags_total"],
            "rubric_error_flags_total": summary["rubric_error_flags_total"],
        },
    }
    _write_json(manifest_path, manifest)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge review decisions into final review dataset."
    )
    parser.add_argument("--gold-path", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--runs-root", default="outputs/teacher_runs")
    parser.add_argument("--reviews-root", default="datasets/review")
    parser.add_argument("--output-root", default="datasets/review/final")
    parser.add_argument("--source-run-id", default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = merge_reviews(
        gold_path=Path(args.gold_path),
        runs_root=Path(args.runs_root),
        reviews_root=Path(args.reviews_root),
        output_root=Path(args.output_root),
        source_run_id=_normalize_text(args.source_run_id) or None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
