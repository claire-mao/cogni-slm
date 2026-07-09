"""Acquire essay datasets into datasets/raw with reproducible metadata.

This script attempts to download:
- ASAP-AES
- PERSUADE 2.0
- ASAP 2.0

Design goals:
- Use the Hugging Face `datasets` library for access checks and split statistics.
- Preserve original repository files under datasets/raw/<dataset_name>/source_files.
- Never overwrite existing downloads.
- Continue when individual datasets fail or require manual acceptance.
- Emit a machine-readable summary for downstream reporting.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from huggingface_hub import snapshot_download

from datasets import load_dataset_builder


@dataclass(frozen=True)
class DatasetCandidate:
    """One candidate source for a target dataset."""

    repo_id: str
    note: str


@dataclass(frozen=True)
class DatasetTarget:
    """Top-level dataset target with fallback candidate repositories."""

    key: str
    display_name: str
    destination_dir: str
    homepage: str
    candidates: tuple[DatasetCandidate, ...]
    manual_download_instructions: str


@dataclass
class DatasetResult:
    """Outcome for one target dataset."""

    key: str
    display_name: str
    status: str
    selected_repo: str | None
    destination: str
    split_counts: dict[str, int]
    files_downloaded: int
    requires_manual_acceptance: bool
    license: str | None
    scoring_labels: str
    message: str
    next_steps: list[str]


TARGETS: tuple[DatasetTarget, ...] = (
    DatasetTarget(
        key="asap_aes",
        display_name="ASAP-AES",
        destination_dir="asap_aes",
        homepage="https://huggingface.co/datasets/TasfiaS/ASAP-AES",
        candidates=(
            DatasetCandidate(repo_id="TasfiaS/ASAP-AES", note="Primary ASAP-AES mirror on HF."),
            DatasetCandidate(
                repo_id="llm-aes/asap-8-original",
                note="Fallback ASAP-based essay scoring dataset on HF.",
            ),
        ),
        manual_download_instructions=(
            "Open the dataset page, review usage terms/license, and download files manually into "
            "datasets/raw/asap_aes/source_files if the repo is gated/unavailable."
        ),
    ),
    DatasetTarget(
        key="persuade2",
        display_name="PERSUADE 2.0",
        destination_dir="persuade2",
        homepage="https://www.kaggle.com/competitions/feedback-prize-effectiveness",
        candidates=(
            DatasetCandidate(
                repo_id="nlpatunt/D_persuade_2",
                note="HF mirror used by S-GRADES work.",
            ),
            DatasetCandidate(
                repo_id="Ateeqq/PERSUADE-2.0",
                note="Alternative HF mirror candidate.",
            ),
        ),
        manual_download_instructions=(
            "If HF mirrors are unavailable, access the official Kaggle competition/source, "
            "accept terms, and place original files under datasets/raw/persuade2/source_files."
        ),
    ),
    DatasetTarget(
        key="asap2",
        display_name="ASAP 2.0",
        destination_dir="asap2",
        homepage="https://huggingface.co/datasets/jatinmehra/Automated-Essay-Scoring-2.0",
        candidates=(
            DatasetCandidate(
                repo_id="jatinmehra/Automated-Essay-Scoring-2.0",
                note="ASAP 2.0 mirror on HF.",
            ),
        ),
        manual_download_instructions=(
            "If unavailable, record the source and place licensed ASAP 2.0 files manually in "
            "datasets/raw/asap2/source_files."
        ),
    ),
)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Download essay datasets into datasets/raw.")
    parser.add_argument(
        "--raw-root",
        default="datasets/raw",
        help="Root directory for raw datasets.",
    )
    parser.add_argument(
        "--summary-json",
        default="outputs/data_ingestion/download_summary.json",
        help="Machine-readable summary output path.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Attempt redownload even when destination already contains files.",
    )
    return parser.parse_args()


def count_files(path: Path) -> int:
    """Count files recursively in a directory."""
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def parse_manual_requirement(error_text: str) -> tuple[bool, str]:
    """Classify exceptions into manual-acceptance/auth vs other failures."""
    lowered = error_text.lower()
    triggers = (
        "gated",
        "accept",
        "authentication",
        "authorization",
        "unauthorized",
        "forbidden",
        "token",
        "permission",
        "login",
        "403",
        "401",
    )
    requires_manual = any(token in lowered for token in triggers)
    if requires_manual:
        return True, "Authentication or manual acceptance required."
    return False, "Automatic download failed."


def split_counts_from_builder(repo_id: str) -> dict[str, int]:
    """Load split metadata using datasets builder without consuming full data."""
    builder = load_dataset_builder(repo_id)
    info = builder.info
    counts: dict[str, int] = {}
    if info.splits:
        for split_name, split_info in info.splits.items():
            num_examples = split_info.num_examples
            counts[split_name] = int(num_examples) if num_examples is not None else 0
    return counts


def try_load_basic(repo_id: str) -> tuple[dict[str, int], str | None]:
    """Try datasets-based access and return split counts and license metadata."""
    builder = load_dataset_builder(repo_id)
    counts: dict[str, int] = {}
    if builder.info.splits:
        counts = {
            split_name: int(split_info.num_examples or 0)
            for split_name, split_info in builder.info.splits.items()
        }
    license_value = builder.info.license if hasattr(builder.info, "license") else None
    return counts, license_value


def ensure_not_overwrite(destination: Path, force: bool) -> bool:
    """Return True when destination should be skipped to avoid overwriting."""
    existing_files = count_files(destination)
    return existing_files > 0 and not force


def download_source_repo(repo_id: str, destination: Path) -> None:
    """Download dataset repository source files via huggingface_hub snapshot."""
    destination.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        repo_type="dataset",
        local_dir=str(destination),
        local_dir_use_symlinks=False,
        resume_download=True,
    )


def process_target(target: DatasetTarget, raw_root: Path, force: bool) -> DatasetResult:
    """Attempt to acquire one dataset target from candidate repositories."""
    base_dir = raw_root / target.destination_dir
    source_dir = base_dir / "source_files"
    base_dir.mkdir(parents=True, exist_ok=True)
    source_dir.mkdir(parents=True, exist_ok=True)

    if ensure_not_overwrite(source_dir, force=force):
        return DatasetResult(
            key=target.key,
            display_name=target.display_name,
            status="skipped_existing",
            selected_repo=None,
            destination=str(source_dir),
            split_counts={},
            files_downloaded=count_files(source_dir),
            requires_manual_acceptance=False,
            license=None,
            scoring_labels="unknown",
            message="Skipped because files already exist.",
            next_steps=[],
        )

    last_error = ""
    for candidate in target.candidates:
        try:
            split_counts, license_value = try_load_basic(candidate.repo_id)
            download_source_repo(candidate.repo_id, source_dir)
            return DatasetResult(
                key=target.key,
                display_name=target.display_name,
                status="downloaded",
                selected_repo=candidate.repo_id,
                destination=str(source_dir),
                split_counts=split_counts,
                files_downloaded=count_files(source_dir),
                requires_manual_acceptance=False,
                license=license_value,
                scoring_labels="See dataset documentation/source metadata.",
                message=f"Downloaded from {candidate.repo_id}",
                next_steps=[],
            )
        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            requires_manual, reason = parse_manual_requirement(last_error)
            if requires_manual:
                return DatasetResult(
                    key=target.key,
                    display_name=target.display_name,
                    status="manual_required",
                    selected_repo=candidate.repo_id,
                    destination=str(source_dir),
                    split_counts={},
                    files_downloaded=count_files(source_dir),
                    requires_manual_acceptance=True,
                    license=None,
                    scoring_labels="unknown",
                    message=f"{reason} {last_error}",
                    next_steps=[target.manual_download_instructions],
                )
            continue

    return DatasetResult(
        key=target.key,
        display_name=target.display_name,
        status="failed",
        selected_repo=None,
        destination=str(source_dir),
        split_counts={},
        files_downloaded=count_files(source_dir),
        requires_manual_acceptance=False,
        license=None,
        scoring_labels="unknown",
        message=f"All candidates failed. Last error: {last_error}",
        next_steps=[target.manual_download_instructions],
    )


def main() -> None:
    """Run dataset acquisition."""
    args = parse_args()
    raw_root = Path(args.raw_root)
    summary_path = Path(args.summary_json)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    raw_root.mkdir(parents=True, exist_ok=True)

    results: list[DatasetResult] = []
    for target in TARGETS:
        result = process_target(target=target, raw_root=raw_root, force=args.force)
        results.append(result)

    payload: dict[str, Any] = {
        "raw_root": str(raw_root),
        "results": [asdict(item) for item in results],
    }
    summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
