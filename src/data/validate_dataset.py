"""Validate generated dataset examples and emit a markdown report."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = (
    "id",
    "essay",
    "rubric_score",
    "score_explanation",
    "strongest_evidence",
    "weakest_reasoning",
    "revision",
    "teacher_reasoning",
    "metadata",
)
TEXT_REQUIRED_FIELDS = (
    "essay",
    "score_explanation",
    "strongest_evidence",
    "weakest_reasoning",
    "revision",
    "teacher_reasoning",
)


@dataclass(frozen=True)
class ValidationIssue:
    """One validation issue linked to a file."""

    path: str
    code: str
    message: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate generated AP Lang dataset examples.")
    parser.add_argument(
        "--input-dir",
        default="datasets/processed/training_examples",
        help="Directory of generated JSON example files.",
    )
    parser.add_argument(
        "--report-path",
        default="outputs/dataset_validation/report.md",
        help="Markdown validation report output path.",
    )
    parser.add_argument("--min-score", type=int, default=0)
    parser.add_argument("--max-score", type=int, default=6)
    parser.add_argument("--min-essay-words", type=int, default=80)
    parser.add_argument("--min-feedback-words", type=int, default=12)
    return parser.parse_args()


def count_words(text: str) -> int:
    return len(text.split())


def validate_record(
    payload: dict[str, Any],
    *,
    path: Path,
    min_score: int,
    max_score: int,
    min_essay_words: int,
    min_feedback_words: int,
) -> list[ValidationIssue]:
    """Validate one dataset record."""
    issues: list[ValidationIssue] = []
    path_str = str(path)

    for field in REQUIRED_FIELDS:
        if field not in payload:
            issues.append(
                ValidationIssue(
                    path=path_str,
                    code="missing_field",
                    message=f"Missing field: {field}",
                )
            )

    for field in TEXT_REQUIRED_FIELDS:
        value = str(payload.get(field, "")).strip()
        if not value:
            issues.append(
                ValidationIssue(
                    path=path_str,
                    code="empty_field",
                    message=f"Empty required field: {field}",
                )
            )

    score = payload.get("rubric_score")
    if not isinstance(score, int):
        issues.append(
            ValidationIssue(
                path=path_str,
                code="invalid_score_type",
                message="rubric_score must be an integer.",
            )
        )
    elif score < min_score or score > max_score:
        issues.append(
            ValidationIssue(
                path=path_str,
                code="invalid_score_range",
                message=f"rubric_score must be in [{min_score}, {max_score}].",
            )
        )

    essay_words = count_words(str(payload.get("essay", "")))
    if essay_words < min_essay_words:
        issues.append(
            ValidationIssue(
                path=path_str,
                code="essay_too_short",
                message=f"Essay words {essay_words} < minimum {min_essay_words}.",
            )
        )

    feedback_fields = (
        str(payload.get("score_explanation", "")),
        str(payload.get("strongest_evidence", "")),
        str(payload.get("weakest_reasoning", "")),
        str(payload.get("revision", "")),
        str(payload.get("teacher_reasoning", "")),
    )
    feedback_words = sum(count_words(item) for item in feedback_fields)
    if feedback_words < min_feedback_words:
        issues.append(
            ValidationIssue(
                path=path_str,
                code="feedback_too_short",
                message=f"Feedback words {feedback_words} < minimum {min_feedback_words}.",
            )
        )

    return issues


def render_report(
    *,
    input_dir: Path,
    checked_files: int,
    valid_files: int,
    issues: list[ValidationIssue],
) -> str:
    """Render markdown validation report."""
    lines = [
        "# Dataset Validation Report",
        "",
        f"- Input directory: `{input_dir}`",
        f"- Files checked: `{checked_files}`",
        f"- Valid files: `{valid_files}`",
        f"- Invalid files: `{checked_files - valid_files}`",
        f"- Total issues: `{len(issues)}`",
        "",
        "## Issues",
        "",
    ]

    if not issues:
        lines.append("- No validation issues found.")
        return "\n".join(lines)

    for issue in issues[:200]:
        lines.append(f"- `{issue.path}` [{issue.code}]: {issue.message}")

    if len(issues) > 200:
        lines.append(f"- ... {len(issues) - 200} additional issues omitted.")

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    report_path = Path(args.report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    json_files = sorted(path for path in input_dir.glob("*.json") if path.is_file())
    issues: list[ValidationIssue] = []
    valid_files = 0

    for path in json_files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(
                ValidationIssue(
                    path=str(path),
                    code="invalid_json",
                    message=f"JSON parse error: {exc.msg}",
                )
            )
            continue

        record_issues = validate_record(
            payload,
            path=path,
            min_score=args.min_score,
            max_score=args.max_score,
            min_essay_words=args.min_essay_words,
            min_feedback_words=args.min_feedback_words,
        )
        if record_issues:
            issues.extend(record_issues)
        else:
            valid_files += 1

    report_text = render_report(
        input_dir=input_dir,
        checked_files=len(json_files),
        valid_files=valid_files,
        issues=issues,
    )
    report_path.write_text(report_text, encoding="utf-8")

    print(f"report={report_path}")
    print(f"checked={len(json_files)} valid={valid_files} issues={len(issues)}")


if __name__ == "__main__":
    main()
