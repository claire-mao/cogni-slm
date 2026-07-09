"""Reusable validators for canonical dataset records.

Canonical record shape expected:
{
    "id": string,
    "source": string,
    "task": string,
    "prompt": string,
    "text": string,
    "label": float,
    "metadata": dict,
}
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ValidatorConfig:
    """Configuration for validation checks."""

    label_min: float = 0.0
    label_max: float = 60.0
    min_word_count: int = 20
    max_word_count: int = 1500
    max_examples_per_check: int = 25


@dataclass(frozen=True)
class ValidationIssue:
    """Single validation issue."""

    check: str
    file_path: str
    line: int | None
    record_id: str | None
    message: str


@dataclass
class DatasetValidationResult:
    """Validation outcome for one dataset file."""

    file_path: str
    total_records: int = 0
    issues: list[ValidationIssue] = field(default_factory=list)
    issue_counts: dict[str, int] = field(default_factory=dict)
    encoding_ok: bool = True
    utf8_error: str | None = None

    def add_issue(self, issue: ValidationIssue) -> None:
        """Add one issue and update count."""
        self.issues.append(issue)
        self.issue_counts[issue.check] = self.issue_counts.get(issue.check, 0) + 1


def _word_count(text: str) -> int:
    return len(text.split())


def verify_utf8(path: Path) -> tuple[bool, str | None]:
    """Validate file is valid UTF-8 bytes."""
    raw = path.read_bytes()
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def _parse_records(path: Path, result: DatasetValidationResult) -> list[tuple[int, dict[str, Any]]]:
    """Parse JSONL file into (line, record) tuples and log parse issues."""
    parsed: list[tuple[int, dict[str, Any]]] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    for line_no, line in enumerate(text.splitlines(), start=1):
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            result.add_issue(
                ValidationIssue(
                    check="invalid_json",
                    file_path=str(path),
                    line=line_no,
                    record_id=None,
                    message=f"JSON parse error: {exc}",
                )
            )
            continue
        if not isinstance(payload, dict):
            result.add_issue(
                ValidationIssue(
                    check="invalid_record_type",
                    file_path=str(path),
                    line=line_no,
                    record_id=None,
                    message="Record is not a JSON object.",
                )
            )
            continue
        parsed.append((line_no, payload))
    return parsed


def validate_jsonl_file(path: Path, config: ValidatorConfig) -> DatasetValidationResult:
    """Run all checks on one JSONL file."""
    result = DatasetValidationResult(file_path=str(path))

    ok, utf8_error = verify_utf8(path)
    result.encoding_ok = ok
    result.utf8_error = utf8_error
    if not ok and utf8_error is not None:
        result.add_issue(
            ValidationIssue(
                check="invalid_utf8",
                file_path=str(path),
                line=None,
                record_id=None,
                message=utf8_error,
            )
        )

    parsed = _parse_records(path, result)
    result.total_records = len(parsed)

    id_counts: Counter[str] = Counter()
    text_counts: Counter[str] = Counter()

    for line_no, row in parsed:
        rid = row.get("id")
        rid_str = str(rid) if rid is not None else None

        text_value_raw = row.get("text")
        text_value = "" if text_value_raw is None else str(text_value_raw)

        # empty text / whitespace-only checks
        if text_value_raw is None or text_value == "":
            result.add_issue(
                ValidationIssue(
                    check="empty_text",
                    file_path=str(path),
                    line=line_no,
                    record_id=rid_str,
                    message="`text` is empty or missing.",
                )
            )
        if text_value.strip() == "":
            result.add_issue(
                ValidationIssue(
                    check="whitespace_only_essay",
                    file_path=str(path),
                    line=line_no,
                    record_id=rid_str,
                    message="Essay text is whitespace only.",
                )
            )

        wc = _word_count(text_value)
        if text_value.strip() and wc < config.min_word_count:
            result.add_issue(
                ValidationIssue(
                    check="extremely_short_essay",
                    file_path=str(path),
                    line=line_no,
                    record_id=rid_str,
                    message=f"Word count {wc} < minimum {config.min_word_count}.",
                )
            )
        if wc > config.max_word_count:
            result.add_issue(
                ValidationIssue(
                    check="extremely_long_essay",
                    file_path=str(path),
                    line=line_no,
                    record_id=rid_str,
                    message=f"Word count {wc} > maximum {config.max_word_count}.",
                )
            )

        # label checks
        label = row.get("label")
        numeric_label: float | None = None
        if label is None:
            result.add_issue(
                ValidationIssue(
                    check="invalid_label",
                    file_path=str(path),
                    line=line_no,
                    record_id=rid_str,
                    message="Label is missing.",
                )
            )
        else:
            try:
                numeric_label = float(label)
                if math.isnan(numeric_label) or math.isinf(numeric_label):
                    raise ValueError("Label is NaN/Inf.")
            except (TypeError, ValueError):
                result.add_issue(
                    ValidationIssue(
                        check="invalid_label",
                        file_path=str(path),
                        line=line_no,
                        record_id=rid_str,
                        message=f"Non-numeric label: {label}",
                    )
                )

        if numeric_label is not None and (
            numeric_label < config.label_min or numeric_label > config.label_max
        ):
            result.add_issue(
                ValidationIssue(
                    check="label_out_of_range",
                    file_path=str(path),
                    line=line_no,
                    record_id=rid_str,
                    message=(
                        f"Label {numeric_label} outside "
                        f"[{config.label_min}, {config.label_max}]."
                    ),
                )
            )

        if rid_str:
            id_counts[rid_str] += 1
        if text_value:
            text_counts[text_value] += 1

    for rid, count in id_counts.items():
        if count > 1:
            result.add_issue(
                ValidationIssue(
                    check="duplicate_id",
                    file_path=str(path),
                    line=None,
                    record_id=rid,
                    message=f"ID appears {count} times.",
                )
            )

    for text, count in text_counts.items():
        if count > 1:
            preview = text[:80].replace("\n", " ")
            result.add_issue(
                ValidationIssue(
                    check="duplicate_text",
                    file_path=str(path),
                    line=None,
                    record_id=None,
                    message=f"Text appears {count} times. Preview: {preview}",
                )
            )

    return result


def validate_directory(
    input_dir: Path,
    config: ValidatorConfig,
    *,
    include_combined: bool = False,
) -> list[DatasetValidationResult]:
    """Validate all JSONL files in a directory."""
    results: list[DatasetValidationResult] = []
    for path in sorted(input_dir.glob("*.jsonl")):
        if not include_combined and path.name == "all_datasets.jsonl":
            continue
        results.append(validate_jsonl_file(path, config))
    return results


def render_markdown_report(
    results: list[DatasetValidationResult],
    config: ValidatorConfig,
) -> str:
    """Render markdown report for validation results."""
    all_checks = [
        "empty_text",
        "duplicate_id",
        "duplicate_text",
        "invalid_label",
        "label_out_of_range",
        "invalid_utf8",
        "whitespace_only_essay",
        "extremely_short_essay",
        "extremely_long_essay",
    ]

    lines: list[str] = []
    lines.append("# Dataset Validation Report")
    lines.append("")
    lines.append(
        f"Configured thresholds: label in [{config.label_min}, {config.label_max}], "
        f"min_words={config.min_word_count}, max_words={config.max_word_count}"
    )
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append(
        "| File | Records | UTF-8 | empty_text | duplicate_id | duplicate_text | "
        "invalid_label | label_out_of_range | invalid_utf8 | whitespace_only | "
        "extremely_short | extremely_long |"
    )
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")

    for result in results:
        counts = result.issue_counts
        lines.append(
            f"| `{Path(result.file_path).name}` | {result.total_records} | "
            f"{'OK' if result.encoding_ok else 'FAIL'} | "
            f"{counts.get('empty_text', 0)} | {counts.get('duplicate_id', 0)} | "
            f"{counts.get('duplicate_text', 0)} | {counts.get('invalid_label', 0)} | "
            f"{counts.get('label_out_of_range', 0)} | {counts.get('invalid_utf8', 0)} | "
            f"{counts.get('whitespace_only_essay', 0)} | "
            f"{counts.get('extremely_short_essay', 0)} | "
            f"{counts.get('extremely_long_essay', 0)} |"
        )

    lines.append("")
    lines.append("## Detailed Findings")
    lines.append("")

    for result in results:
        lines.append(f"### `{Path(result.file_path).name}`")
        if not result.issues:
            lines.append("- No issues found.")
            lines.append("")
            continue

        grouped: dict[str, list[ValidationIssue]] = {check: [] for check in all_checks}
        for issue in result.issues:
            grouped.setdefault(issue.check, []).append(issue)

        for check in all_checks:
            issues = grouped.get(check, [])
            if not issues:
                continue
            lines.append(f"- `{check}`: {len(issues)}")
            for issue in issues[: config.max_examples_per_check]:
                where = f"line {issue.line}" if issue.line is not None else "dataset-level"
                rid = f", id={issue.record_id}" if issue.record_id else ""
                lines.append(f"  - {where}{rid}: {issue.message}")

        lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    lines.append("1. Drop or repair records flagged for `empty_text`/`whitespace_only_essay`.")
    lines.append("2. Resolve `duplicate_id` and consider deduplicating `duplicate_text` entries.")
    lines.append("3. Enforce numeric labels and clamp to expected range before model training.")
    lines.append(
        "4. Route files with `invalid_utf8` through encoding normalization "
        "prior to downstream processing."
    )
    lines.append(
        "5. Review extreme length outliers to avoid truncated supervision "
        "and unstable training dynamics."
    )

    return "\n".join(lines)
