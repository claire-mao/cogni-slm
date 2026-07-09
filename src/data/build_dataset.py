"""Run a reproducible end-to-end dataset build pipeline.

Pipeline order:
1. verify raw datasets
2. ingest Hugging Face datasets
3. normalize schemas
4. compute quality scores
5. deduplicate
6. verify licenses
7. generate provenance
8. build training dataset
9. verify final dataset
10. generate reports

Usage:
    python scripts/build_dataset.py

One-command execution is exposed via the Makefile target `dataset-build`.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

ENCODING_CANDIDATES = ("utf-8-sig", "cp1252", "latin-1")
VALID_SPLITS = {"train", "validation", "test"}
TEXT_FIELDS = ("input", "text", "essay", "argument_text", "student_response", "content")
SCORE_FIELDS = ("score", "label", "rubric_score", "domain1_score", "holistic_essay_score")
DEFAULT_TRAIN_RATIO = 0.8
DEFAULT_VALIDATION_RATIO = 0.1
DEFAULT_TEST_RATIO = 0.1

LICENSE_FALLBACKS = {
    "asap_aes": "Public competition/research dataset terms (verify official terms)",
    "asap2": "Unknown on mirror; verify before redistribution",
    "persuade2": "Kaggle/official source terms (manual acceptance may be required)",
}

OPEN_LICENSE_TOKENS = (
    "cc0",
    "cc by",
    "cc-by",
    "mit",
    "apache",
    "bsd",
    "gpl",
    "public domain",
    "u.s. government",
    "open data",
)


@dataclass
class StepResult:
    """Result of one pipeline step."""

    index: int
    name: str
    status: str
    duration_seconds: float
    details: str
    artifacts: list[str]


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Build full dataset pipeline reproducibly.")
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Repository root path.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned execution without running the pipeline.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip remote acquisition and use local raw files only.",
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=60.0,
        help="Quality score threshold for filtering.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/reproducibility.md",
        help="Output reproducibility report path.",
    )
    return parser.parse_args()


def run_command(
    command: list[str],
    cwd: Path,
    *,
    allow_failure: bool = False,
) -> tuple[bool, str]:
    """Run a subprocess command and return (success, details)."""
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )

    output = "\n".join(
        part.strip() for part in [proc.stdout.strip(), proc.stderr.strip()] if part.strip()
    )
    if not output:
        output = "(no output)"
    output = " ".join(output.replace("\r", " ").replace("\n", " ").split())

    if proc.returncode != 0 and not allow_failure:
        return False, f"returncode={proc.returncode}; output={output[:2000]}"

    status = "warning" if proc.returncode != 0 else "ok"
    return True, f"status={status}; output={output[:2000]}"


def normalize_text(text: str) -> str:
    """Collapse whitespace for stable hashing."""
    return " ".join(text.split())


def choose_field(row: dict[str, Any], candidates: tuple[str, ...]) -> str:
    """Choose the first non-empty field by priority."""
    for key in candidates:
        value = str(row.get(key, "")).strip()
        if value:
            return value
    return ""


def parse_score(value: Any) -> float | None:
    """Parse score as finite float or return None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        parsed = float(value)
        return parsed if parsed == parsed and parsed not in (float("inf"), float("-inf")) else None
    raw = str(value).strip()
    if not raw:
        return None
    try:
        parsed = float(raw)
    except ValueError:
        return None
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return None
    return parsed


def verify_raw_datasets(raw_root: Path, report_path: Path) -> tuple[bool, str, list[str]]:
    """Verify parseability and basic integrity of raw dataset files."""
    supported = {".csv", ".tsv", ".json", ".jsonl", ".txt"}
    files = sorted(
        path for path in raw_root.rglob("*") if path.is_file() and path.suffix.lower() in supported
    )

    artifact_paths: list[str] = [str(report_path)]
    if not files:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            "# Raw Dataset Verification\n\n- Status: FAIL\n- No supported raw files found.\n",
            encoding="utf-8",
        )
        return False, "No supported raw dataset files found.", artifact_paths

    parse_failures: list[str] = []
    malformed_rows = 0
    total_rows = 0
    encoding_hits: dict[str, int] = {enc: 0 for enc in ENCODING_CANDIDATES}

    for path in files:
        suffix = path.suffix.lower()
        decoded: str | None = None
        decode_error = ""

        for encoding in ENCODING_CANDIDATES:
            try:
                decoded = path.read_text(encoding=encoding)
                encoding_hits[encoding] += 1
                break
            except UnicodeDecodeError as exc:
                decode_error = f"{type(exc).__name__}: {exc}"

        if decoded is None:
            parse_failures.append(f"{path}: decode failed ({decode_error})")
            continue

        try:
            if suffix in {".csv", ".tsv"}:
                delimiter = "," if suffix == ".csv" else "\t"
                reader = csv.reader(io.StringIO(decoded, newline=""), delimiter=delimiter)
                rows = list(reader)
                if not rows:
                    parse_failures.append(f"{path}: empty delimited file")
                    continue
                expected_cols = len(rows[0])
                for idx, row in enumerate(rows[1:], start=2):
                    total_rows += 1
                    if len(row) != expected_cols:
                        malformed_rows += 1
                        parse_failures.append(
                            f"{path}: row {idx} has {len(row)} columns, expected {expected_cols}"
                        )
            elif suffix == ".json":
                payload = json.loads(decoded)
                if isinstance(payload, list):
                    total_rows += len(payload)
                elif isinstance(payload, dict):
                    total_rows += 1
                else:
                    parse_failures.append(
                        f"{path}: unsupported JSON root type {type(payload).__name__}"
                    )
            elif suffix == ".jsonl":
                for idx, line in enumerate(decoded.splitlines(), start=1):
                    raw = line.strip()
                    if not raw:
                        continue
                    total_rows += 1
                    try:
                        json.loads(raw)
                    except json.JSONDecodeError as exc:
                        malformed_rows += 1
                        parse_failures.append(f"{path}: line {idx} invalid JSON ({exc.msg})")
            elif suffix == ".txt":
                total_rows += 1
                if not decoded.strip():
                    malformed_rows += 1
                    parse_failures.append(f"{path}: empty text file")
        except Exception as exc:
            parse_failures.append(f"{path}: parse exception {type(exc).__name__}: {exc}")

    report_lines = [
        "# Raw Dataset Verification",
        "",
        f"- Raw root: `{raw_root}`",
        f"- Supported files scanned: `{len(files)}`",
        f"- Approximate rows observed: `{total_rows}`",
        f"- Malformed rows: `{malformed_rows}`",
        "",
        "## Encoding Detection",
        "",
        "| encoding | files decoded |",
        "|---|---:|",
    ]
    for encoding in ENCODING_CANDIDATES:
        report_lines.append(f"| {encoding} | {encoding_hits.get(encoding, 0)} |")

    report_lines.extend(["", "## Parse Failures", ""])
    if parse_failures:
        for item in parse_failures[:200]:
            report_lines.append(f"- {item}")
        if len(parse_failures) > 200:
            report_lines.append(f"- ... and {len(parse_failures) - 200} more")
    else:
        report_lines.append("- None")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    success = len(parse_failures) == 0
    details = (
        f"files={len(files)}, rows={total_rows}, malformed={malformed_rows}, "
        f"failures={len(parse_failures)}"
    )
    return success, details, artifact_paths


def deduplicate_quality_filtered(
    input_jsonl: Path,
    deduped_output: Path,
    final_dir: Path,
    report_path: Path,
) -> tuple[bool, str, list[str]]:
    """Deduplicate quality-filtered records and materialize final split files."""
    artifacts = [str(deduped_output), str(report_path)]
    if not input_jsonl.exists():
        return False, f"Missing input: {input_jsonl}", artifacts

    records: list[dict[str, Any]] = []
    with input_jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if isinstance(payload, dict):
                records.append(payload)

    seen_ids: set[str] = set()
    seen_text_hashes: set[str] = set()

    deduped_records: list[dict[str, Any]] = []
    removed_dup_id = 0
    removed_dup_text = 0
    skipped_invalid = 0

    for idx, row in enumerate(records, start=1):
        record_id = str(row.get("id", f"row-{idx}")).strip() or f"row-{idx}"
        text_value = choose_field(row, TEXT_FIELDS)
        score_value = parse_score(row.get("score", row.get("label")))

        if not text_value or score_value is None:
            skipped_invalid += 1
            continue

        text_hash = hashlib.sha256(normalize_text(text_value).lower().encode("utf-8")).hexdigest()

        if record_id in seen_ids:
            removed_dup_id += 1
            continue
        if text_hash in seen_text_hashes:
            removed_dup_text += 1
            continue

        seen_ids.add(record_id)
        seen_text_hashes.add(text_hash)
        row["id"] = record_id
        row["_normalized_text"] = text_value
        row["_normalized_score"] = score_value
        row["_original_split"] = str(row.get("split", "train")).strip().lower()
        row["_split_hash"] = hashlib.sha256(
            f"{record_id}\n{normalize_text(text_value).lower()}".encode()
        ).hexdigest()
        deduped_records.append(row)

    # Deterministically assign train/validation/test on the deduplicated set.
    # This prevents split collapse caused by cross-split duplicate removal order.
    ordered_indices = sorted(
        range(len(deduped_records)),
        key=lambda i: (
            str(deduped_records[i].get("_split_hash", "")),
            str(deduped_records[i].get("id", "")),
        ),
    )
    n = len(ordered_indices)
    train_count = int(n * DEFAULT_TRAIN_RATIO)
    validation_count = int(n * DEFAULT_VALIDATION_RATIO)
    test_count = n - train_count - validation_count

    if n >= 3:
        train_count = max(train_count, 1)
        validation_count = max(validation_count, 1)
        test_count = max(test_count, 1)
        while train_count + validation_count + test_count > n:
            if train_count >= validation_count and train_count >= test_count and train_count > 1:
                train_count -= 1
            elif validation_count >= test_count and validation_count > 1:
                validation_count -= 1
            elif test_count > 1:
                test_count -= 1
            else:
                break

    for rank, row_index in enumerate(ordered_indices):
        if rank < train_count:
            assigned_split = "train"
        elif rank < train_count + validation_count:
            assigned_split = "validation"
        else:
            assigned_split = "test"
        deduped_records[row_index]["split"] = assigned_split

    deduped_output.parent.mkdir(parents=True, exist_ok=True)
    with deduped_output.open("w", encoding="utf-8") as handle:
        for row in deduped_records:
            row_copy = dict(row)
            row_copy.pop("_normalized_text", None)
            row_copy.pop("_normalized_score", None)
            row_copy.pop("_split_hash", None)
            handle.write(json.dumps(row_copy, ensure_ascii=False) + "\n")

    final_dir.mkdir(parents=True, exist_ok=True)
    split_files = {
        "train": final_dir / "train.jsonl",
        "validation": final_dir / "validation.jsonl",
        "test": final_dir / "test.jsonl",
    }

    split_handles = {split: path.open("w", encoding="utf-8") for split, path in split_files.items()}
    artifacts.extend(str(path) for path in split_files.values())

    merged_all = final_dir / "merged_all.jsonl"
    artifacts.append(str(merged_all))

    final_count = 0
    label_values: list[float] = []

    try:
        with merged_all.open("w", encoding="utf-8") as merged:
            for row in deduped_records:
                split = str(row.get("split", "train")).strip().lower()
                if split not in VALID_SPLITS:
                    split = "train"

                text = row.get("_normalized_text") or choose_field(row, TEXT_FIELDS)
                score = row.get("_normalized_score")
                if score is None:
                    score = parse_score(row.get("score", row.get("label")))
                if not text or score is None:
                    continue

                metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
                metadata = dict(metadata)
                original_split = str(row.get("_original_split", "")).strip().lower()
                if original_split:
                    metadata.setdefault("original_split", original_split)

                if "license" in row and str(row.get("license", "")).strip():
                    metadata.setdefault("license", str(row.get("license")).strip())

                final_record = {
                    "id": str(row.get("id", "")).strip() or f"missing-id-{final_count + 1}",
                    "source": str(row.get("source", "unknown")).strip() or "unknown",
                    "task": str(row.get("task", "essay_scoring")).strip() or "essay_scoring",
                    "prompt": str(row.get("prompt", "")).strip(),
                    "text": str(text),
                    "label": float(score),
                    "metadata": metadata,
                    "split": split,
                }

                split_handles[split].write(json.dumps(final_record, ensure_ascii=False) + "\n")
                merged.write(json.dumps(final_record, ensure_ascii=False) + "\n")
                label_values.append(float(score))
                final_count += 1
    finally:
        for handle in split_handles.values():
            handle.close()

    split_counts = {}
    for split, path in split_files.items():
        with path.open("r", encoding="utf-8") as handle:
            split_counts[split] = sum(1 for _ in handle)

    report_lines = [
        "# Deduplication Report",
        "",
        f"- Input records: `{len(records)}`",
        f"- Kept after deduplication: `{len(deduped_records)}`",
        f"- Removed duplicate IDs: `{removed_dup_id}`",
        f"- Removed duplicate text: `{removed_dup_text}`",
        f"- Skipped invalid rows: `{skipped_invalid}`",
        f"- Final records materialized: `{final_count}`",
        (
            "- Split assignment: deterministic hash partition "
            f"({DEFAULT_TRAIN_RATIO:.1f}/{DEFAULT_VALIDATION_RATIO:.1f}/{DEFAULT_TEST_RATIO:.1f})"
        ),
        "",
        "## Final Split Counts",
        "",
        "| split | records |",
        "|---|---:|",
        f"| train | {split_counts.get('train', 0)} |",
        f"| validation | {split_counts.get('validation', 0)} |",
        f"| test | {split_counts.get('test', 0)} |",
        "",
    ]

    if label_values:
        report_lines.extend(
            [
                "## Label Summary",
                "",
                f"- Min label: `{min(label_values):.4f}`",
                f"- Max label: `{max(label_values):.4f}`",
                f"- Mean label: `{mean(label_values):.4f}`",
            ]
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    details = (
        f"input={len(records)}, deduped={len(deduped_records)}, final={final_count}, "
        f"split_counts={split_counts}"
    )
    return True, details, artifacts


def sanitize_jsonl(
    input_path: Path,
    output_path: Path,
    report_path: Path,
) -> tuple[bool, str, list[str]]:
    """Write a sanitized JSONL with malformed rows removed."""
    artifacts = [str(output_path), str(report_path)]
    if not input_path.exists():
        return False, f"Missing input JSONL: {input_path}", artifacts

    output_path.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    skipped = 0
    total = 0

    with (
        input_path.open("r", encoding="utf-8", errors="replace") as source,
        output_path.open("w", encoding="utf-8") as sink,
    ):
        for _line_number, line in enumerate(source, start=1):
            raw = line.strip()
            if not raw:
                continue
            total += 1
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(payload, dict):
                skipped += 1
                continue
            sink.write(json.dumps(payload, ensure_ascii=False) + "\n")
            kept += 1

    report_lines = [
        "# Unified JSONL Sanitization",
        "",
        f"- Input: `{input_path}`",
        f"- Output: `{output_path}`",
        f"- Total non-empty lines: `{total}`",
        f"- Kept valid JSON object rows: `{kept}`",
        f"- Skipped malformed/non-object rows: `{skipped}`",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    return True, f"total={total}, kept={kept}, skipped={skipped}", artifacts


def compute_quality_scores_fast(
    *,
    input_jsonl: Path,
    scored_output: Path,
    filtered_output: Path,
    removed_output: Path,
    report_path: Path,
    threshold: float,
) -> tuple[bool, str, list[str]]:
    """Compute lightweight quality scores and filter records quickly."""
    artifacts = [
        str(scored_output),
        str(filtered_output),
        str(removed_output),
        str(report_path),
    ]
    if not input_jsonl.exists():
        return False, f"Missing sanitized input: {input_jsonl}", artifacts

    scored_output.parent.mkdir(parents=True, exist_ok=True)
    filtered_output.parent.mkdir(parents=True, exist_ok=True)
    removed_output.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    kept = 0
    removed = 0
    score_values: list[float] = []

    def length_score(words: int) -> float:
        if words <= 0:
            return 0.0
        if words < 80:
            return min(100.0, (words / 80.0) * 100.0)
        if words <= 1200:
            return 100.0
        return max(0.0, 100.0 - ((words - 1200) / 1200.0) * 80.0)

    with (
        input_jsonl.open("r", encoding="utf-8") as source,
        scored_output.open("w", encoding="utf-8") as scored,
        filtered_output.open("w", encoding="utf-8") as filtered,
        removed_output.open("w", encoding="utf-8") as removed_sink,
    ):
        for line in source:
            raw = line.strip()
            if not raw:
                continue
            row = json.loads(raw)
            if not isinstance(row, dict):
                continue
            total += 1

            text = choose_field(row, TEXT_FIELDS)
            words = len(text.split())
            base = length_score(words)

            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            metadata_bonus = 10.0 if metadata else 0.0
            prompt_bonus = 5.0 if str(row.get("prompt", "")).strip() else 0.0
            parsed_score = parse_score(row.get("score", row.get("label")))
            label_bonus = 10.0 if parsed_score is not None else 0.0

            quality = max(
                0.0,
                min(100.0, base + metadata_bonus + prompt_bonus + label_bonus - 15.0),
            )
            score_values.append(quality)

            scored_row = dict(row)
            scored_row["quality"] = {
                "length_score": base,
                "metadata_bonus": metadata_bonus,
                "prompt_bonus": prompt_bonus,
                "label_bonus": label_bonus,
                "overall_quality_score": quality,
            }
            scored.write(json.dumps(scored_row, ensure_ascii=False) + "\n")

            if quality >= threshold:
                filtered.write(json.dumps(scored_row, ensure_ascii=False) + "\n")
                kept += 1
            else:
                removed_row = {
                    "id": str(row.get("id", "")),
                    "source": str(row.get("source", "unknown")),
                    "overall_quality_score": quality,
                    "reason": "below_threshold",
                }
                removed_sink.write(json.dumps(removed_row, ensure_ascii=False) + "\n")
                removed += 1

    report_lines = [
        "# Final Dataset Quality (Fast Pipeline)",
        "",
        f"- Input: `{input_jsonl}`",
        f"- Threshold: `{threshold}`",
        f"- Total examples: `{total}`",
        f"- Kept: `{kept}`",
        f"- Removed: `{removed}`",
    ]
    if score_values:
        report_lines.extend(
            [
                f"- Min quality: `{min(score_values):.4f}`",
                f"- Max quality: `{max(score_values):.4f}`",
                f"- Mean quality: `{mean(score_values):.4f}`",
            ]
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    details = f"total={total}, kept={kept}, removed={removed}, threshold={threshold}"
    return True, details, artifacts


def verify_licenses(final_merged_jsonl: Path, report_path: Path) -> tuple[bool, str, list[str]]:
    """Verify dataset license coverage from final merged records."""
    artifacts = [str(report_path)]
    if not final_merged_jsonl.exists():
        return False, f"Missing merged final dataset: {final_merged_jsonl}", artifacts

    by_source: dict[str, dict[str, Any]] = {}
    total_rows = 0

    with final_merged_jsonl.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            row = json.loads(raw)
            if not isinstance(row, dict):
                continue
            total_rows += 1
            source = str(row.get("source", "unknown")).strip() or "unknown"
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            license_value = str(metadata.get("license", "")).strip() or LICENSE_FALLBACKS.get(
                source, "unknown"
            )

            source_state = by_source.setdefault(
                source,
                {
                    "count": 0,
                    "licenses": set(),
                },
            )
            source_state["count"] += 1
            if license_value:
                source_state["licenses"].add(license_value)

    open_ok = True
    lines = [
        "# License Verification",
        "",
        f"- Input records: `{total_rows}`",
        "",
        "| source | records | observed license(s) | status |",
        "|---|---:|---|---|",
    ]

    for source in sorted(by_source):
        row = by_source[source]
        licenses = sorted(row["licenses"]) if row["licenses"] else ["unknown"]
        license_text = "; ".join(licenses)
        lowered = license_text.lower()
        status = "PASS"
        if "unknown" in lowered or not any(token in lowered for token in OPEN_LICENSE_TOKENS):
            status = "WARN"
            open_ok = False
        if "college board" in lowered or "leaked" in lowered:
            status = "FAIL"
            open_ok = False
        lines.append(f"| {source} | {row['count']} | {license_text} | {status} |")

    lines.extend(
        [
            "",
            "## Policy Checks",
            "",
            "- No College Board leaked exam datasets should be included.",
            "- Unknown licenses require manual legal verification before redistribution.",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    details = f"sources={len(by_source)}, open_or_verified={open_ok}"
    return True, details, artifacts


def write_reproducibility_report(
    report_path: Path,
    step_results: list[StepResult],
    command_hint: str,
) -> None:
    """Write a reproducibility summary report."""
    total_seconds = sum(item.duration_seconds for item in step_results)
    success_count = sum(1 for item in step_results if item.status == "PASS")
    warn_count = sum(1 for item in step_results if item.status == "WARN")
    fail_count = sum(1 for item in step_results if item.status == "FAIL")

    lines = [
        "# Dataset Reproducibility Report",
        "",
        f"- Generated: `{time.strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- One-command entry point: `{command_hint}`",
        f"- Total runtime (seconds): `{total_seconds:.2f}`",
        f"- Step results: PASS={success_count}, WARN={warn_count}, FAIL={fail_count}",
        "",
        "## Step Execution",
        "",
        "| # | step | status | duration_s | details |",
        "|---:|---|---|---:|---|",
    ]

    for result in step_results:
        lines.append(
            f"| {result.index} | {result.name} | {result.status} | "
            f"{result.duration_seconds:.2f} | "
            f"{result.details.replace('|', '/').replace(chr(10), '<br>')} |"
        )

    lines.extend(["", "## Artifacts", ""])
    for result in step_results:
        if not result.artifacts:
            continue
        lines.append(f"### {result.index}. {result.name}")
        for artifact in result.artifacts:
            lines.append(f"- `{artifact}`")
        lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    """Run full dataset build pipeline."""
    args = parse_args()
    root = Path(args.workspace_root).resolve()

    raw_root = root / "datasets" / "raw"
    final_dir = root / "datasets" / "final"

    step_results: list[StepResult] = []

    pipeline_plan = [
        "verify raw datasets",
        "ingest Hugging Face datasets",
        "normalize schemas",
        "compute quality scores",
        "deduplicate",
        "verify licenses",
        "generate provenance",
        "build training dataset",
        "verify final dataset",
        "generate reports",
    ]

    if args.dry_run:
        for idx, step_name in enumerate(pipeline_plan, start=1):
            print(f"{idx}. {step_name}")
        return

    def record_step(
        idx: int,
        name: str,
        fn,
    ) -> bool:
        started = time.perf_counter()
        ok, details, artifacts = fn()
        duration = time.perf_counter() - started
        status = "PASS" if ok else "FAIL"
        step_results.append(
            StepResult(
                index=idx,
                name=name,
                status=status,
                duration_seconds=duration,
                details=details,
                artifacts=artifacts,
            )
        )
        return ok

    def run_script_step(
        idx: int,
        name: str,
        command: list[str],
        artifacts: list[Path],
        *,
        allow_failure: bool = False,
    ) -> bool:
        started = time.perf_counter()
        ok, details = run_command(command, cwd=root, allow_failure=allow_failure)
        duration = time.perf_counter() - started
        if allow_failure and not ok:
            status = "WARN"
            ok = True
        elif allow_failure and "status=warning" in details:
            status = "WARN"
        else:
            status = "PASS" if ok else "FAIL"

        step_results.append(
            StepResult(
                index=idx,
                name=name,
                status=status,
                duration_seconds=duration,
                details=details,
                artifacts=[str(path) for path in artifacts],
            )
        )
        return ok

    # 1) verify raw datasets
    if not record_step(
        1,
        pipeline_plan[0],
        lambda: verify_raw_datasets(
            raw_root=raw_root,
            report_path=root / "docs" / "reports" / "raw_verification.md",
        ),
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 2) ingest Hugging Face datasets
    step2_started = time.perf_counter()
    step2_artifacts = [
        str(root / "outputs" / "data_ingestion" / "download_summary.json"),
        str(root / "datasets" / "hf" / "dataset_dict"),
        str(root / "datasets" / "hf" / "build_summary.json"),
    ]
    step2_status = "PASS"
    step2_detail_parts: list[str] = []

    if args.skip_download:
        step2_status = "WARN"
        step2_detail_parts.append("download=skipped (--skip-download)")
    else:
        dl_ok, dl_details = run_command(
            [sys.executable, "scripts/download_datasets.py"],
            cwd=root,
            allow_failure=True,
        )
        if not dl_ok or "status=warning" in dl_details:
            step2_status = "WARN"
        step2_detail_parts.append(f"download: {dl_details}")

    ingest_ok, ingest_details = run_command(
        [sys.executable, "datasets/build_dataset.py", "--overwrite"],
        cwd=root,
    )
    if not ingest_ok:
        step2_status = "FAIL"
    step2_detail_parts.append(f"build: {ingest_details}")

    step2_duration = time.perf_counter() - step2_started
    step_results.append(
        StepResult(
            index=2,
            name=pipeline_plan[1],
            status=step2_status,
            duration_seconds=step2_duration,
            details=" | ".join(step2_detail_parts),
            artifacts=step2_artifacts,
        )
    )

    if step2_status == "FAIL":
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 3) normalize schemas
    if not run_script_step(
        3,
        pipeline_plan[2],
        [sys.executable, "scripts/normalize_unified_schema.py"],
        [
            root / "datasets" / "processed" / "unified" / "unified_all.jsonl",
            root / "docs" / "reports" / "schema_mapping.md",
        ],
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 4) compute quality scores
    sanitize_ok, _sanitize_details, sanitize_artifacts = sanitize_jsonl(
        input_path=root / "datasets" / "processed" / "unified" / "unified_all.jsonl",
        output_path=root / "datasets" / "processed" / "unified" / "unified_all.sanitized.jsonl",
        report_path=root / "docs" / "reports" / "unified_sanitization.md",
    )
    if not sanitize_ok:
        step_results.append(
            StepResult(
                index=4,
                name=pipeline_plan[3],
                status="FAIL",
                duration_seconds=0.0,
                details="sanitize failed",
                artifacts=sanitize_artifacts,
            )
        )
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    if not record_step(
        4,
        pipeline_plan[3],
        lambda: compute_quality_scores_fast(
            input_jsonl=root / "datasets" / "processed" / "unified" / "unified_all.sanitized.jsonl",
            scored_output=root / "datasets" / "final" / "quality_scored.jsonl",
            filtered_output=root / "datasets" / "final" / "quality_filtered.jsonl",
            removed_output=root / "datasets" / "final" / "quality_removed.jsonl",
            report_path=root / "docs" / "reports" / "final_dataset_quality.md",
            threshold=args.quality_threshold,
        ),
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 5) deduplicate
    if not record_step(
        5,
        pipeline_plan[4],
        lambda: deduplicate_quality_filtered(
            input_jsonl=root / "datasets" / "final" / "quality_filtered.jsonl",
            deduped_output=root / "datasets" / "final" / "quality_deduped.jsonl",
            final_dir=final_dir,
            report_path=root / "docs" / "reports" / "deduplication.md",
        ),
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 6) verify licenses
    license_ok = record_step(
        6,
        pipeline_plan[5],
        lambda: verify_licenses(
            final_merged_jsonl=root / "datasets" / "final" / "merged_all.jsonl",
            report_path=root / "docs" / "reports" / "license_verification.md",
        ),
    )
    if not license_ok:
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 7) generate provenance
    if not run_script_step(
        7,
        pipeline_plan[6],
        [
            sys.executable,
            "scripts/create_provenance_index.py",
            "--final-dir",
            "datasets/final",
            "--output-parquet",
            "datasets/final/provenance.parquet",
            "--report-path",
            "docs/reports/provenance.md",
        ],
        [
            root / "datasets" / "final" / "provenance.parquet",
            root / "docs" / "reports" / "provenance.md",
        ],
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 8) build training dataset
    if not run_script_step(
        8,
        pipeline_plan[7],
        [
            sys.executable,
            "scripts/build_training_dataset.py",
            "--input-jsonl",
            "datasets/final/quality_deduped.jsonl",
            "--output-dataset-dir",
            "datasets/training",
            "--provenance-dir",
            "datasets/training_provenance",
            "--report-path",
            "docs/reports/training_dataset.md",
        ],
        [
            root / "datasets" / "training",
            root / "datasets" / "training_provenance",
            root / "docs" / "reports" / "training_dataset.md",
        ],
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 9) verify final dataset
    if not run_script_step(
        9,
        pipeline_plan[8],
        [
            sys.executable,
            "scripts/verify_final_dataset.py",
            "--dataset-dir",
            "datasets/final",
            "--report-path",
            "docs/reports/final_verification.md",
            "--hf-disk-path",
            "datasets/final/dataset_dict",
        ],
        [
            root / "docs" / "reports" / "final_verification.md",
            root / "datasets" / "final" / "dataset_dict",
        ],
    ):
        write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")
        sys.exit(1)

    # 10) generate reports
    reports_ok = run_script_step(
        10,
        "generate reports (dataset cards)",
        [sys.executable, "scripts/generate_dataset_cards.py", "--repo-root", str(root)],
        [root / "docs" / "datasets" / "dataset_cards"],
        allow_failure=True,
    )

    if not reports_ok:
        for idx, item in enumerate(step_results):
            if item.index == 10:
                step_results[idx].status = "WARN"
                break

    write_reproducibility_report(Path(args.report_path), step_results, "make dataset-build")

    has_failures = any(item.status == "FAIL" for item in step_results)
    if has_failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
