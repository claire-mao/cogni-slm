"""Build versioned gold datasets from approved review examples.

This builder consumes approved review rows and writes a versioned gold dataset
with:
- review metadata
- adjudication history
- deterministic checksums

No model inference is executed in this module.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SUPPORTED_APPROVAL_DECISIONS = {"accept", "edit", "approved"}


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


def _stable_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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


def _is_approved(row: dict[str, Any]) -> bool:
    decision = _normalize_text(row.get("decision")).lower()
    if not decision:
        # Support already-filtered approved-only sources.
        return True
    return decision in SUPPORTED_APPROVAL_DECISIONS


def _detect_label(row: dict[str, Any]) -> dict[str, Any] | None:
    candidate = row.get("merged_label")
    if isinstance(candidate, dict):
        return candidate

    candidate = row.get("edited_output")
    if isinstance(candidate, dict):
        return candidate

    teacher_output = row.get("teacher_output")
    if isinstance(teacher_output, dict):
        nested = teacher_output.get("output_json")
        if isinstance(nested, dict):
            return nested

    for key in ("output_json", "label", "output", "gold_label"):
        candidate = row.get(key)
        if isinstance(candidate, dict):
            return candidate

    return None


def _detect_license(row: dict[str, Any]) -> str:
    for key in ("license", "dataset_license", "source_license"):
        value = _normalize_text(row.get(key))
        if value:
            return value
    return "unspecified"


def _select_example_id(row: dict[str, Any], index: int) -> str:
    for key in ("example_id", "gold_example_id", "id"):
        value = _normalize_text(row.get(key))
        if value:
            return value
    case_id = _normalize_text(row.get("case_id"))
    if case_id:
        return f"case-{case_id}"
    return f"gold-{index:06d}"


def _review_metadata(row: dict[str, Any]) -> dict[str, Any]:
    flags = row.get("flags") if isinstance(row.get("flags"), dict) else {}
    return {
        "review_id": _normalize_text(row.get("review_id")),
        "created_at": _normalize_text(row.get("created_at")),
        "reviewer_id": _normalize_text(row.get("reviewer_id")) or "anonymous",
        "decision": _normalize_text(row.get("decision")).lower(),
        "notes": _normalize_text(row.get("notes")),
        "selected_teacher_model": _normalize_text(row.get("selected_teacher_model")),
        "hallucination_flag": bool(flags.get("hallucination", False)),
        "rubric_error_flag": bool(flags.get("rubric_error", False)),
        "rubric_correction_applied": bool(row.get("rubric_correction_applied", False)),
    }


def _provenance_metadata(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": _normalize_text(row.get("case_id")),
        "run_id": _normalize_text(row.get("run_id")),
        "task_id": _normalize_text(row.get("task_id")),
        "seed": row.get("seed"),
        "temperature": _safe_float(row.get("temperature")),
        "prompt_version": _normalize_text(row.get("prompt_version")),
        "selected_teacher_model": _normalize_text(row.get("selected_teacher_model")),
    }


def _history_event(row: dict[str, Any]) -> dict[str, Any]:
    flags = row.get("flags") if isinstance(row.get("flags"), dict) else {}
    return {
        "review_id": _normalize_text(row.get("review_id")),
        "created_at": _normalize_text(row.get("created_at")),
        "reviewer_id": _normalize_text(row.get("reviewer_id")) or "anonymous",
        "decision": _normalize_text(row.get("decision")).lower(),
        "selected_teacher_model": _normalize_text(row.get("selected_teacher_model")),
        "notes": _normalize_text(row.get("notes")),
        "flags": {
            "hallucination": bool(flags.get("hallucination", False)),
            "rubric_error": bool(flags.get("rubric_error", False)),
        },
        "edited_output_present": isinstance(row.get("edited_output"), dict),
    }


def _load_adjudication_index(adjudication_log: Path) -> dict[str, list[dict[str, Any]]]:
    rows = _read_jsonl(adjudication_log)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        case_id = _normalize_text(row.get("case_id"))
        if not case_id:
            continue
        grouped.setdefault(case_id, []).append(_history_event(row))

    for events in grouped.values():
        events.sort(
            key=lambda event: (
                _parse_iso8601(event.get("created_at")),
                _normalize_text(event.get("review_id")),
            )
        )
    return grouped


def _auto_version(output_root: Path) -> str:
    versions_dir = output_root / "versions"
    if not versions_dir.exists():
        return "gold_v1"

    max_seen = 0
    for path in versions_dir.iterdir():
        if not path.is_dir():
            continue
        match = re.fullmatch(r"gold_v(\d+)", path.name)
        if not match:
            continue
        value = int(match.group(1))
        if value > max_seen:
            max_seen = value
    return f"gold_v{max_seen + 1}"


def _sanitize_version(version: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "_", version).strip("_")
    if not normalized:
        raise ValueError("Version must contain at least one alphanumeric character.")
    if not normalized.startswith("gold_v"):
        normalized = f"gold_v{normalized}"
    return normalized


def _build_gold_record(
    *,
    row: dict[str, Any],
    index: int,
    version: str,
    adjudication_history: list[dict[str, Any]],
) -> dict[str, Any]:
    label = _detect_label(row)
    if label is None:
        case_id = _normalize_text(row.get("case_id"))
        raise ValueError("Approved row is missing label payload " f"for case_id={case_id}")

    gold_answer = row.get("gold_answer") if isinstance(row.get("gold_answer"), dict) else {}
    fallacies = gold_answer.get("expected_fallacies")
    if fallacies is None:
        fallacies = label.get("fallacies")

    record: dict[str, Any] = {
        "example_id": _select_example_id(row, index),
        "version": version,
        "source": _normalize_text(row.get("source")) or "unknown",
        "license": _detect_license(row),
        "difficulty": _normalize_text(row.get("difficulty")) or "unknown",
        "prompt": _normalize_text(row.get("prompt")),
        "essay": _normalize_text(row.get("essay")),
        "gold_score": label.get("score", gold_answer.get("score")),
        "rubric": label.get("rubric", gold_answer.get("rubric")),
        "expected_reasoning_skills": gold_answer.get("expected_reasoning_skills"),
        "expected_fallacies": fallacies,
        "gold_label": label,
        "notes_for_reviewers": _normalize_text(gold_answer.get("notes"))
        or _normalize_text(row.get("notes")),
        "review_metadata": _review_metadata(row),
        "adjudication_history": adjudication_history,
        "provenance": _provenance_metadata(row),
    }
    record["record_checksum_sha256"] = _stable_hash(record)
    return record


def _build_version_index(output_root: Path, latest_version: str) -> dict[str, Any]:
    versions_dir = output_root / "versions"
    versions = [path.name for path in sorted(versions_dir.iterdir()) if path.is_dir()]
    return {
        "latest_version": latest_version,
        "versions": versions,
        "updated_at_utc": _utc_now(),
    }


def build_gold_dataset(
    *,
    approved_path: Path,
    output_root: Path,
    adjudication_log: Path | None,
    version: str | None,
) -> dict[str, Any]:
    """Build one versioned gold dataset from approved review examples."""
    if not approved_path.exists():
        raise FileNotFoundError(f"Approved review examples not found: {approved_path}")

    approved_rows = [row for row in _read_jsonl(approved_path) if _is_approved(row)]
    resolved_version = _sanitize_version(version) if version else _auto_version(output_root)
    version_dir = output_root / "versions" / resolved_version
    version_dir.mkdir(parents=True, exist_ok=True)

    adjudication_index: dict[str, list[dict[str, Any]]] = {}
    if adjudication_log is not None and adjudication_log.exists():
        adjudication_index = _load_adjudication_index(adjudication_log)

    gold_rows: list[dict[str, Any]] = []
    adjudication_rows: list[dict[str, Any]] = []
    skipped_case_ids: list[str] = []
    decision_counts: dict[str, int] = {}
    reviewer_ids: set[str] = set()
    hallucination_count = 0
    rubric_error_count = 0

    stable_rows = sorted(
        approved_rows,
        key=lambda row: (
            _normalize_text(row.get("example_id")),
            _normalize_text(row.get("case_id")),
            _normalize_text(row.get("review_id")),
        ),
    )

    for idx, row in enumerate(stable_rows, start=1):
        decision = _normalize_text(row.get("decision")).lower() or "approved"
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        reviewer = _normalize_text(row.get("reviewer_id"))
        if reviewer:
            reviewer_ids.add(reviewer)

        flags = row.get("flags") if isinstance(row.get("flags"), dict) else {}
        if bool(flags.get("hallucination", False)):
            hallucination_count += 1
        if bool(flags.get("rubric_error", False)):
            rubric_error_count += 1

        case_id = _normalize_text(row.get("case_id"))
        history = adjudication_index.get(case_id, [])
        if case_id and history:
            adjudication_rows.append({"case_id": case_id, "events": history})

        try:
            gold_rows.append(
                _build_gold_record(
                    row=row,
                    index=idx,
                    version=resolved_version,
                    adjudication_history=history,
                )
            )
        except ValueError:
            skipped_case_ids.append(case_id or f"row-{idx}")

    dataset_path = version_dir / "gold_dataset.jsonl"
    adjudication_path = version_dir / "adjudication_history.jsonl"
    checksums_path = version_dir / "checksums.json"
    manifest_path = version_dir / "manifest.json"
    latest_manifest_path = output_root / "manifest.json"
    version_index_path = output_root / "version_index.json"

    _write_jsonl(dataset_path, gold_rows)
    _write_jsonl(adjudication_path, adjudication_rows)

    checksums = {
        "approved_input_sha256": _path_sha256(approved_path),
        "adjudication_log_sha256": (
            _path_sha256(adjudication_log) if adjudication_log is not None else ""
        ),
        "gold_dataset_sha256": _path_sha256(dataset_path),
        "adjudication_history_sha256": _path_sha256(adjudication_path),
        "record_checksums_sha256": hashlib.sha256(
            "\n".join(row.get("record_checksum_sha256", "") for row in gold_rows).encode("utf-8")
        ).hexdigest(),
    }
    _write_json(checksums_path, checksums)

    manifest = {
        "schema_version": "gold_dataset_builder_v1",
        "created_at_utc": _utc_now(),
        "version": resolved_version,
        "inputs": {
            "approved_reviews_path": str(approved_path),
            "adjudication_log_path": str(adjudication_log) if adjudication_log else None,
        },
        "outputs": {
            "version_dir": str(version_dir),
            "gold_dataset_jsonl": str(dataset_path),
            "adjudication_history_jsonl": str(adjudication_path),
            "checksums_json": str(checksums_path),
        },
        "counts": {
            "approved_rows_seen": len(approved_rows),
            "gold_rows_written": len(gold_rows),
            "skipped_rows": len(skipped_case_ids),
            "rows_with_adjudication_history": sum(
                1 for row in gold_rows if row.get("adjudication_history")
            ),
        },
        "review_metadata": {
            "reviewer_count": len(reviewer_ids),
            "reviewers": sorted(reviewer_ids),
            "decision_counts": decision_counts,
            "hallucination_flags_total": hallucination_count,
            "rubric_error_flags_total": rubric_error_count,
        },
        "adjudication": {
            "history_available": bool(adjudication_index),
            "cases_with_history": len(adjudication_rows),
            "max_events_per_case": max(
                (len(row["events"]) for row in adjudication_rows),
                default=0,
            ),
        },
        "checksums": checksums,
        "skipped_case_ids": skipped_case_ids,
    }
    _write_json(manifest_path, manifest)
    _write_json(latest_manifest_path, manifest)

    version_index = _build_version_index(output_root, resolved_version)
    _write_json(version_index_path, version_index)
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build versioned gold dataset artifacts from approved review examples."
    )
    parser.add_argument(
        "--approved-path",
        default="datasets/review/final/review_dataset.jsonl",
        help="JSONL of approved review examples (accept/edit decisions).",
    )
    parser.add_argument(
        "--adjudication-log",
        default="datasets/review/reviews.jsonl",
        help="Optional full review log used to attach adjudication history.",
    )
    parser.add_argument(
        "--output-root",
        default="datasets/gold",
        help="Root directory for gold dataset versions.",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="Optional explicit version (for example: gold_v2). Auto-increments when omitted.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    adjudication_log = Path(args.adjudication_log)
    manifest = build_gold_dataset(
        approved_path=Path(args.approved_path),
        output_root=Path(args.output_root),
        adjudication_log=adjudication_log if adjudication_log.exists() else None,
        version=_normalize_text(args.version) or None,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
