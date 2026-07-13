"""Rebuild dataset artifacts from datasets/raw in an isolated workspace.

This script fixes repository reproducibility by enforcing a raw-only rebuild flow:
- It copies only `datasets/raw/` and required build scripts into a clean workspace.
- It runs the canonical dataset pipeline there.
- It regenerates post-build artifacts (provenance repair, metadata leakage check,
  prompt-group candidate split).
- It syncs rebuilt artifacts back to the repository.
- It writes a step-by-step report to `docs/reports/rebuild.md`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from datasets import load_from_disk

SUPPORTED_RAW_EXTENSIONS = {".csv", ".tsv", ".json", ".jsonl", ".txt"}

SYNC_DIRS = (
    "datasets/hf",
    "datasets/processed/unified",
    "datasets/final",
    "datasets/training",
    "datasets/training_provenance",
    "datasets/training_candidates/prompt_group_split",
)

SYNC_FILES = (
    "docs/reports/raw_verification.md",
    "docs/reports/schema_mapping.md",
    "docs/reports/unified_sanitization.md",
    "docs/reports/final_dataset_quality.md",
    "docs/reports/deduplication.md",
    "outputs/reports/license_verification.md",
    "docs/reports/provenance.md",
    "docs/reports/provenance_repair.md",
    "docs/reports/training_dataset.md",
    "docs/reports/final_verification.md",
    "docs/reports/reproducibility.md",
    "docs/reports/metadata_leakage.md",
    "docs/reports/group_split.md",
)


@dataclass
class StepResult:
    """One rebuild step result."""

    name: str
    status: str
    duration_seconds: float
    details: str


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(
        description="Rebuild all dataset artifacts from datasets/raw in isolation."
    )
    parser.add_argument("--repo-root", default=".", help="Repository root path.")
    parser.add_argument(
        "--raw-root",
        default="datasets/raw",
        help="Raw dataset directory (relative to repo root).",
    )
    parser.add_argument(
        "--work-dir",
        default=".rebuild_workspace",
        help="Temporary isolated workspace directory.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/rebuild.md",
        help="Output rebuild report path.",
    )
    parser.add_argument(
        "--quality-threshold",
        type=float,
        default=60.0,
        help="Quality threshold passed to scripts/build_dataset.py.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan and report steps without running commands.",
    )
    parser.add_argument(
        "--keep-workspace",
        action="store_true",
        help="Keep isolated workspace after completion.",
    )
    return parser.parse_args()


def run_command(command: list[str], cwd: Path) -> tuple[bool, str]:
    """Run subprocess command and return (ok, compact_output)."""
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    output = "\n".join(
        part.strip() for part in (proc.stdout.strip(), proc.stderr.strip()) if part.strip()
    )
    output = " ".join(output.replace("\r", " ").replace("\n", " ").split())
    if not output:
        output = "(no output)"

    if proc.returncode != 0:
        return False, f"returncode={proc.returncode}; output={output[:2400]}"
    return True, output[:2400]


def list_raw_files(raw_root: Path) -> list[Path]:
    """List supported raw files."""
    return sorted(
        path
        for path in raw_root.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_RAW_EXTENSIONS
    )


def prepare_workspace(repo_root: Path, raw_root: Path, work_root: Path) -> None:
    """Create clean isolated workspace with only raw data + required scripts."""
    if work_root.exists():
        shutil.rmtree(work_root)

    (work_root / "datasets").mkdir(parents=True, exist_ok=True)
    (work_root / "docs" / "reports").mkdir(parents=True, exist_ok=True)

    shutil.copytree(raw_root, work_root / "datasets" / "raw")
    shutil.copytree(repo_root / "scripts", work_root / "scripts")
    shutil.copytree(repo_root / "src", work_root / "src")
    shutil.copytree(repo_root / "evaluation", work_root / "evaluation")
    shutil.copytree(repo_root / "training", work_root / "training")
    shutil.copy2(repo_root / "pyproject.toml", work_root / "pyproject.toml")
    shutil.copy2(
        repo_root / "datasets" / "build_dataset.py",
        work_root / "datasets" / "build_dataset.py",
    )


def sanitize_provenance_scores(provenance_dir: Path) -> tuple[int, int]:
    """Remove score/label-like keys from provenance JSONL sidecar."""

    def scrub(obj: Any) -> Any:
        if isinstance(obj, dict):
            cleaned: dict[str, Any] = {}
            for key, value in obj.items():
                key_lower = str(key).lower()
                if "score" in key_lower or "label" in key_lower:
                    continue
                cleaned[key] = scrub(value)
            return cleaned
        if isinstance(obj, list):
            return [scrub(item) for item in obj]
        return obj

    files_touched = 0
    rows_touched = 0

    for split in ("train", "validation", "test"):
        path = provenance_dir / f"{split}.jsonl"
        if not path.exists():
            continue

        cleaned_lines: list[str] = []
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                payload = json.loads(raw)
                cleaned_lines.append(json.dumps(scrub(payload), ensure_ascii=False))
                rows_touched += 1

        path.write_text(
            "\n".join(cleaned_lines) + ("\n" if cleaned_lines else ""),
            encoding="utf-8",
        )
        files_touched += 1

    return files_touched, rows_touched


def generate_metadata_leakage_report(work_root: Path) -> tuple[bool, str]:
    """Generate docs/reports/metadata_leakage.md inside workspace."""
    training_dir = work_root / "datasets" / "training"
    provenance_dir = work_root / "datasets" / "training_provenance"
    report_path = work_root / "docs" / "reports" / "metadata_leakage.md"

    lines = [
        "# Metadata Leakage Report",
        "",
        "## Scope",
        "",
        "- Training dataset: `datasets/training`",
        "- Provenance sidecar: `datasets/training_provenance`",
        "",
    ]
    failures: list[str] = []
    warnings: list[str] = []

    expected_columns = ["prompt", "essay", "score"]
    if not training_dir.exists():
        failures.append("Missing datasets/training")
        lines.append("Training dataset directory missing.")
    else:
        dataset = load_from_disk(str(training_dir))
        lines.extend(
            [
                "## Training Dataset Schema",
                "",
                "| split | rows | columns | only_prompt_essay_score |",
                "|---|---:|---|---|",
            ]
        )

        for split in ("train", "validation", "test"):
            if split not in dataset:
                warnings.append(f"Missing split: {split}")
                lines.append(f"| {split} | 0 | missing | SKIP |")
                continue
            cols = list(dataset[split].column_names)
            ok = cols == expected_columns
            if not ok:
                failures.append(f"Unexpected columns in {split}: {cols}")
            lines.append(
                f"| {split} | {len(dataset[split])} | `{cols}` | {'PASS' if ok else 'FAIL'} |"
            )

    score_like_key_hits: dict[str, int] = {}
    rows_scanned = 0
    for split in ("train", "validation", "test"):
        path = provenance_dir / f"{split}.jsonl"
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                rows_scanned += 1
                payload = json.loads(raw)
                stack: list[Any] = [payload]
                while stack:
                    value = stack.pop()
                    if isinstance(value, dict):
                        for key, item in value.items():
                            key_lower = str(key).lower()
                            if "score" in key_lower or "label" in key_lower:
                                score_like_key_hits[key] = score_like_key_hits.get(key, 0) + 1
                            stack.append(item)
                    elif isinstance(value, list):
                        stack.extend(value)

    lines.extend(["", "## Provenance Key Audit", "", f"- Rows scanned: `{rows_scanned}`"])
    if score_like_key_hits:
        failures.append("Score/label keys still present in provenance sidecar")
        lines.append("- Result: FAIL")
        lines.append("| key | occurrences |")
        lines.append("|---|---:|")
        for key, count in sorted(score_like_key_hits.items()):
            lines.append(f"| {key} | {count} |")
    else:
        lines.append("- Result: PASS (no score/label keys found in provenance sidecar)")

    status = "PASS" if not failures else "FAIL"
    lines.extend(["", "## Verdict", "", f"- Status: **{status}**"])
    if failures:
        lines.append("- Failures:")
        for item in failures:
            lines.append(f"  - {item}")
    if warnings:
        lines.append("- Warnings:")
        for item in warnings:
            lines.append(f"  - {item}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return not failures, f"status={status}; rows_scanned={rows_scanned}"


def sync_artifacts(work_root: Path, repo_root: Path) -> tuple[int, int, list[str]]:
    """Copy rebuilt artifacts from workspace back into repository."""
    copied = 0
    missing = 0
    missing_paths: list[str] = []

    for rel in SYNC_DIRS:
        src = work_root / rel
        dst = repo_root / rel
        if not src.exists():
            missing += 1
            missing_paths.append(rel)
            continue

        if dst.exists():
            if dst.is_dir():
                shutil.rmtree(dst)
            else:
                dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)
        copied += 1

    for rel in SYNC_FILES:
        src = work_root / rel
        dst = repo_root / rel
        if not src.exists():
            missing += 1
            missing_paths.append(rel)
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += 1

    return copied, missing, missing_paths


def write_rebuild_report(
    report_path: Path,
    *,
    repo_root: Path,
    raw_root: Path,
    work_root: Path,
    dry_run: bool,
    steps: list[StepResult],
    copied_count: int,
    missing_count: int,
    missing_paths: list[str],
) -> None:
    """Write docs/reports/rebuild.md with full preprocessing documentation."""
    total_seconds = sum(step.duration_seconds for step in steps)

    lines = [
        "# Rebuild Pipeline Report",
        "",
        "## Goal",
        "",
        "Rebuild dataset artifacts reproducibly starting only from `datasets/raw/`.",
        "",
        "## Isolation Strategy",
        "",
        f"- Repository root: `{repo_root}`",
        f"- Raw input root: `{raw_root}`",
        f"- Isolated workspace: `{work_root}`",
        "- Workspace includes only:",
        "  - `datasets/raw/`",
        "  - `scripts/` (thin wrappers)",
        "  - `src/`",
        "  - `evaluation/`",
        "  - `training/`",
        "  - `datasets/build_dataset.py`",
        "- All rebuild commands run inside this isolated workspace.",
        "",
        "## Preprocessing Steps",
        "",
        "1. Validate raw files (`csv/tsv/json/jsonl/txt`) exist under `datasets/raw/`.",
        "2. Build Hugging Face staging dataset from raw files (`datasets/build_dataset.py`).",
        "3. Normalize to unified schema (`scripts/normalize_unified_schema.py`).",
        "4. Sanitize unified JSONL (drop malformed rows).",
        "5. Compute quality scores and filter low-quality rows.",
        (
            "6. Deduplicate and materialize canonical "
            "`datasets/final/{train,validation,test}.jsonl` + merged file."
        ),
        "7. Verify licenses and write license report.",
        "8. Build provenance index (`datasets/final/provenance.parquet`).",
        "9. Build training dataset (`datasets/training`) and provenance sidecar.",
        "10. Verify final dataset integrity and HF loadability.",
        "11. Regenerate provenance repair report (`docs/reports/provenance_repair.md`).",
        "12. Remove score/label keys from training provenance sidecar.",
        "13. Generate metadata leakage report (`docs/reports/metadata_leakage.md`).",
        "14. Generate prompt-group candidate split (`docs/reports/group_split.md`).",
        "15. Sync rebuilt artifacts back to repository.",
        "",
        "## Execution",
        "",
        f"- Mode: `{'dry-run' if dry_run else 'execute'}`",
        f"- Total step runtime: `{total_seconds:.2f}` seconds",
        "",
        "| step | status | duration_s | details |",
        "|---|---|---:|---|",
    ]

    for step in steps:
        details = step.details.replace("|", "/").replace("\n", " ")
        lines.append(f"| {step.name} | {step.status} | {step.duration_seconds:.2f} | {details} |")

    lines.extend(
        [
            "",
            "## Artifact Sync",
            "",
            f"- Paths copied: `{copied_count}`",
            f"- Missing paths: `{missing_count}`",
        ]
    )

    if missing_paths:
        lines.append("- Missing path list:")
        for rel in missing_paths:
            lines.append(f"  - `{rel}`")

    lines.extend(
        [
            "",
            "## Rebuild Command",
            "",
            "```bash",
            "python3 scripts/rebuild_all.py",
            "```",
            "",
            "Use `--dry-run` to preview without executing.",
        ]
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """Entrypoint."""
    args = parse_args()

    repo_root = Path(args.repo_root).resolve()
    raw_root = (repo_root / args.raw_root).resolve()
    work_root = (repo_root / args.work_dir).resolve()
    report_path = (repo_root / args.report_path).resolve()

    steps: list[StepResult] = []

    raw_files = list_raw_files(raw_root)
    if not raw_files:
        write_rebuild_report(
            report_path,
            repo_root=repo_root,
            raw_root=raw_root,
            work_root=work_root,
            dry_run=args.dry_run,
            steps=[
                StepResult(
                    name="validate_raw",
                    status="FAIL",
                    duration_seconds=0.0,
                    details="No supported raw files found.",
                )
            ],
            copied_count=0,
            missing_count=0,
            missing_paths=[],
        )
        raise SystemExit("No supported raw files found under datasets/raw.")

    t0 = time.perf_counter()
    prepare_workspace(repo_root=repo_root, raw_root=raw_root, work_root=work_root)
    steps.append(
        StepResult(
            name="prepare_workspace",
            status="PASS",
            duration_seconds=time.perf_counter() - t0,
            details=f"raw_files={len(raw_files)}",
        )
    )

    if args.dry_run:
        planned = [
            "scripts/build_dataset.py --workspace-root . --skip-download",
            "scripts/create_provenance_index.py --final-dir datasets/final",
            "scripts/build_training_dataset.py --input-jsonl datasets/final/quality_deduped.jsonl",
            "scripts/create_prompt_group_split_candidate.py",
            "sync artifacts back to repository",
        ]
        for cmd in planned:
            steps.append(
                StepResult(
                    name="planned",
                    status="PLANNED",
                    duration_seconds=0.0,
                    details=cmd,
                )
            )
        write_rebuild_report(
            report_path,
            repo_root=repo_root,
            raw_root=raw_root,
            work_root=work_root,
            dry_run=True,
            steps=steps,
            copied_count=0,
            missing_count=0,
            missing_paths=[],
        )
        if not args.keep_workspace and work_root.exists():
            shutil.rmtree(work_root)
        return

    command_steps: list[tuple[str, list[str]]] = [
        (
            "build_dataset_pipeline",
            [
                sys.executable,
                "scripts/build_dataset.py",
                "--workspace-root",
                ".",
                "--skip-download",
                "--quality-threshold",
                str(args.quality_threshold),
                "--report-path",
                "docs/reports/reproducibility.md",
            ],
        ),
        (
            "rebuild_provenance_index",
            [
                sys.executable,
                "scripts/create_provenance_index.py",
                "--final-dir",
                "datasets/final",
                "--output-parquet",
                "datasets/final/provenance.parquet",
                "--report-path",
                "docs/reports/provenance_repair.md",
            ],
        ),
        (
            "rebuild_training_dataset",
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
        ),
        (
            "build_prompt_group_candidate",
            [
                sys.executable,
                "scripts/create_prompt_group_split_candidate.py",
                "--input-dataset-dir",
                "datasets/training",
                "--input-provenance-dir",
                "datasets/training_provenance",
                "--output-dir",
                "datasets/training_candidates/prompt_group_split",
                "--report-path",
                "docs/reports/group_split.md",
            ],
        ),
    ]

    failed = False
    for step_name, command in command_steps:
        started = time.perf_counter()
        ok, details = run_command(command, cwd=work_root)
        steps.append(
            StepResult(
                name=step_name,
                status="PASS" if ok else "FAIL",
                duration_seconds=time.perf_counter() - started,
                details=details,
            )
        )
        if not ok:
            failed = True
            break

    if not failed:
        started = time.perf_counter()
        files_touched, rows_touched = sanitize_provenance_scores(
            work_root / "datasets" / "training_provenance"
        )
        steps.append(
            StepResult(
                name="sanitize_training_provenance",
                status="PASS",
                duration_seconds=time.perf_counter() - started,
                details=f"files={files_touched}, rows={rows_touched}",
            )
        )

        started = time.perf_counter()
        leak_ok, leak_details = generate_metadata_leakage_report(work_root)
        steps.append(
            StepResult(
                name="metadata_leakage_report",
                status="PASS" if leak_ok else "FAIL",
                duration_seconds=time.perf_counter() - started,
                details=leak_details,
            )
        )
        if not leak_ok:
            failed = True

    copied_count = 0
    missing_count = 0
    missing_paths: list[str] = []

    if not failed:
        started = time.perf_counter()
        copied_count, missing_count, missing_paths = sync_artifacts(work_root, repo_root)
        steps.append(
            StepResult(
                name="sync_artifacts",
                status="PASS",
                duration_seconds=time.perf_counter() - started,
                details=f"copied={copied_count}, missing={missing_count}",
            )
        )

    write_rebuild_report(
        report_path,
        repo_root=repo_root,
        raw_root=raw_root,
        work_root=work_root,
        dry_run=False,
        steps=steps,
        copied_count=copied_count,
        missing_count=missing_count,
        missing_paths=missing_paths,
    )

    if not args.keep_workspace and work_root.exists():
        shutil.rmtree(work_root)

    if failed:
        raise SystemExit("rebuild_all failed; see docs/reports/rebuild.md")


if __name__ == "__main__":
    main()
