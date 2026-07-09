"""Verify final dataset integrity and compatibility.

Checks:
- schema consistency
- duplicate IDs
- duplicate text
- score validity
- split leakage
- prompt leakage
- train/test contamination
- corrupted files
- UTF-8 validity
- Hugging Face load_from_disk compatibility
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.utils.paths import repo_root

# Configure HF cache inside workspace before importing datasets.
_WORKSPACE_ROOT = repo_root(Path(__file__))
_HF_CACHE_ROOT = _WORKSPACE_ROOT / ".hf_cache"
os.environ.setdefault("HF_HOME", str(_HF_CACHE_ROOT))
os.environ.setdefault("HF_DATASETS_CACHE", str(_HF_CACHE_ROOT / "datasets"))

EXPECTED_FIELDS = {
    "id",
    "source",
    "task",
    "prompt",
    "text",
    "label",
    "metadata",
    "split",
}

SPLIT_FILES = {
    "train": "train.jsonl",
    "validation": "validation.jsonl",
    "test": "test.jsonl",
}


@dataclass
class FileCheckResult:
    """Per-file validation counters and issue tracking."""

    split: str
    path: Path
    line_count: int = 0
    utf8_errors: list[str] = None  # type: ignore[assignment]
    json_errors: list[str] = None  # type: ignore[assignment]
    schema_errors: list[str] = None  # type: ignore[assignment]
    invalid_score_count: int = 0
    invalid_split_count: int = 0
    empty_text_count: int = 0

    def __post_init__(self) -> None:
        if self.utf8_errors is None:
            self.utf8_errors = []
        if self.json_errors is None:
            self.json_errors = []
        if self.schema_errors is None:
            self.schema_errors = []


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Verify final dataset integrity.")
    parser.add_argument(
        "--dataset-dir",
        default="datasets/final",
        help="Directory containing train/validation/test JSONL files.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/final_verification.md",
        help="Markdown report output path.",
    )
    parser.add_argument(
        "--hf-disk-path",
        default="datasets/final/dataset_dict",
        help="Path to save/load Hugging Face DatasetDict for load_from_disk validation.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    """Normalize text for stable duplication checks."""
    return " ".join(text.split()).strip().lower()


def is_valid_score(value: Any) -> bool:
    """Return True if score is finite numeric."""
    if isinstance(value, bool):
        return False
    if isinstance(value, int | float):
        return math.isfinite(float(value))
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return False
        try:
            parsed = float(raw)
        except ValueError:
            return False
        return math.isfinite(parsed)
    return False


def parse_score(value: Any) -> float:
    """Parse score as float after validity check."""
    if isinstance(value, int | float):
        return float(value)
    return float(str(value).strip())


def read_jsonl_with_utf8(path: Path) -> tuple[str | None, list[dict[str, Any]], list[str]]:
    """Read a JSONL file with strict UTF-8 decode and JSON parse errors collected."""
    json_errors: list[str] = []
    try:
        raw_text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return str(exc), [], []

    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            json_errors.append(f"line {line_number}: {exc.msg}")
            continue
        if not isinstance(payload, dict):
            json_errors.append(f"line {line_number}: JSON value is not an object")
            continue
        records.append(payload)

    return None, records, json_errors


def verify_file(split: str, path: Path) -> tuple[FileCheckResult, list[dict[str, Any]]]:
    """Verify a split file and return parsed records."""
    result = FileCheckResult(split=split, path=path)
    utf8_error, records, json_errors = read_jsonl_with_utf8(path)
    if utf8_error is not None:
        result.utf8_errors.append(utf8_error)
        return result, []

    result.json_errors.extend(json_errors)
    result.line_count = len(records)

    for index, record in enumerate(records, start=1):
        keys = set(record.keys())
        if keys != EXPECTED_FIELDS:
            missing = sorted(EXPECTED_FIELDS - keys)
            extra = sorted(keys - EXPECTED_FIELDS)
            result.schema_errors.append(
                f"row {index}: missing={missing if missing else []}, extra={extra if extra else []}"
            )

        text = str(record.get("text", ""))
        if not text.strip():
            result.empty_text_count += 1

        if record.get("split") != split:
            result.invalid_split_count += 1

        if not is_valid_score(record.get("label")):
            result.invalid_score_count += 1

        if not isinstance(record.get("metadata"), dict):
            result.schema_errors.append(f"row {index}: metadata is not an object")

    return result, records


def summarize_duplicates(values: list[str]) -> tuple[int, int]:
    """Return duplicate count and unique count for a list."""
    counts = Counter(values)
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    return duplicate_count, len(counts)


def render_report(
    *,
    dataset_dir: Path,
    per_file: dict[str, FileCheckResult],
    split_sizes: dict[str, int],
    score_stats: dict[str, dict[str, float]],
    duplicate_ids_within: dict[str, int],
    duplicate_text_within: dict[str, int],
    split_id_overlap: dict[str, int],
    split_text_overlap: dict[str, int],
    prompt_overlap: dict[str, int],
    prompt_coverage: dict[str, float],
    hf_ok: bool,
    hf_message: str,
    hf_path: Path,
) -> str:
    """Render markdown verification report."""

    schema_ok = all(not result.schema_errors for result in per_file.values())
    duplicate_id_ok = all(count == 0 for count in duplicate_ids_within.values()) and all(
        count == 0 for count in split_id_overlap.values()
    )
    duplicate_text_ok = all(count == 0 for count in duplicate_text_within.values())
    score_ok = all(result.invalid_score_count == 0 for result in per_file.values())
    split_leak_ok = all(count == 0 for count in split_id_overlap.values())
    prompt_leak_ok = all(count == 0 for count in prompt_overlap.values())
    contamination_ok = all(count == 0 for count in split_text_overlap.values())
    corrupted_ok = all(
        not result.utf8_errors and not result.json_errors and not result.schema_errors
        for result in per_file.values()
    )
    utf8_ok = all(not result.utf8_errors for result in per_file.values())

    def status(ok: bool) -> str:
        return "PASS" if ok else "FAIL"

    lines = [
        "# Final Dataset Verification",
        "",
        f"- Dataset directory: `{dataset_dir}`",
        "",
        "## Check Status",
        "",
        f"- Schema consistency: **{status(schema_ok)}**",
        f"- Duplicate IDs: **{status(duplicate_id_ok)}**",
        f"- Duplicate text: **{status(duplicate_text_ok)}**",
        f"- Score validity: **{status(score_ok)}**",
        f"- Split leakage (ID overlap): **{status(split_leak_ok)}**",
        f"- Prompt leakage (prompt overlap): **{status(prompt_leak_ok)}**",
        f"- Train/test contamination (text overlap): **{status(contamination_ok)}**",
        f"- Corrupted files: **{status(corrupted_ok)}**",
        f"- UTF-8 validity: **{status(utf8_ok)}**",
        f"- Hugging Face compatibility (`load_from_disk`): **{status(hf_ok)}**",
        "",
        "## Split Sizes",
        "",
        "| split | rows |",
        "|---|---:|",
        f"| train | {split_sizes.get('train', 0)} |",
        f"| validation | {split_sizes.get('validation', 0)} |",
        f"| test | {split_sizes.get('test', 0)} |",
        "",
        "## Score Stats",
        "",
        "| split | min | max | mean |",
        "|---|---:|---:|---:|",
    ]

    for split in ("train", "validation", "test"):
        stat = score_stats.get(split, {})
        lines.append(
            f"| {split} | {stat.get('min', 0.0):.4f} | {stat.get('max', 0.0):.4f} | "
            f"{stat.get('mean', 0.0):.4f} |"
        )

    lines.extend(
        [
            "",
            "## Duplicate Summary",
            "",
            "| check | value |",
            "|---|---:|",
            f"| duplicate IDs within train | {duplicate_ids_within.get('train', 0)} |",
            f"| duplicate IDs within validation | {duplicate_ids_within.get('validation', 0)} |",
            f"| duplicate IDs within test | {duplicate_ids_within.get('test', 0)} |",
            f"| duplicate text within train | {duplicate_text_within.get('train', 0)} |",
            f"| duplicate text within validation | {duplicate_text_within.get('validation', 0)} |",
            f"| duplicate text within test | {duplicate_text_within.get('test', 0)} |",
            f"| ID overlap train∩validation | {split_id_overlap.get('train_validation', 0)} |",
            f"| ID overlap train∩test | {split_id_overlap.get('train_test', 0)} |",
            f"| ID overlap validation∩test | {split_id_overlap.get('validation_test', 0)} |",
            f"| text overlap train∩validation | {split_text_overlap.get('train_validation', 0)} |",
            f"| text overlap train∩test | {split_text_overlap.get('train_test', 0)} |",
            f"| text overlap validation∩test | {split_text_overlap.get('validation_test', 0)} |",
            "",
            "## Prompt Leakage",
            "",
            "| check | value |",
            "|---|---:|",
            f"| prompt overlap train∩validation | {prompt_overlap.get('train_validation', 0)} |",
            f"| prompt overlap train∩test | {prompt_overlap.get('train_test', 0)} |",
            f"| prompt overlap validation∩test | {prompt_overlap.get('validation_test', 0)} |",
            (
                "| test prompts also in train (%) | "
                f"{prompt_coverage.get('test_in_train_pct', 0.0):.2f} |"
            ),
            (
                "| validation prompts also in train (%) | "
                f"{prompt_coverage.get('validation_in_train_pct', 0.0):.2f} |"
            ),
        ]
    )

    lines.extend(["", "## File Integrity Details", ""])
    for split in ("train", "validation", "test"):
        result = per_file[split]
        lines.append(f"### {split}")
        lines.append(f"- Path: `{result.path}`")
        lines.append(f"- Parsed rows: `{result.line_count}`")
        lines.append(f"- UTF-8 errors: `{len(result.utf8_errors)}`")
        lines.append(f"- JSON errors: `{len(result.json_errors)}`")
        lines.append(f"- Schema/type errors: `{len(result.schema_errors)}`")
        lines.append(f"- Invalid score rows: `{result.invalid_score_count}`")
        lines.append(f"- Invalid split rows: `{result.invalid_split_count}`")
        lines.append(f"- Empty text rows: `{result.empty_text_count}`")

    lines.extend(
        [
            "",
            "## Hugging Face Compatibility",
            "",
            f"- Saved/loaded dataset path: `{hf_path}`",
            f"- Result: **{status(hf_ok)}**",
            f"- Message: {hf_message}",
            "",
            "The dataset is directly loadable via `datasets.load_from_disk()` at the path above.",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Run verification and write markdown report."""
    from datasets import DatasetDict, load_dataset, load_from_disk

    args = parse_args()
    dataset_dir = Path(args.dataset_dir)
    report_path = Path(args.report_path)
    hf_disk_path = Path(args.hf_disk_path)
    hf_cache_dir = dataset_dir / ".hf_cache"

    report_path.parent.mkdir(parents=True, exist_ok=True)
    hf_disk_path.parent.mkdir(parents=True, exist_ok=True)
    hf_cache_dir.mkdir(parents=True, exist_ok=True)

    # Keep Hugging Face cache local to workspace for restricted environments.
    os.environ.setdefault("HF_HOME", str(hf_cache_dir))
    os.environ.setdefault("HF_DATASETS_CACHE", str(hf_cache_dir / "datasets"))

    per_file: dict[str, FileCheckResult] = {}
    records_by_split: dict[str, list[dict[str, Any]]] = {}

    for split, filename in SPLIT_FILES.items():
        path = dataset_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Missing required split file: {path}")
        result, records = verify_file(split, path)
        per_file[split] = result
        records_by_split[split] = records

    split_sizes = {split: len(rows) for split, rows in records_by_split.items()}

    ids_by_split: dict[str, list[str]] = {}
    text_by_split: dict[str, list[str]] = {}
    prompts_by_split: dict[str, set[str]] = {}
    score_stats: dict[str, dict[str, float]] = {}

    duplicate_ids_within: dict[str, int] = {}
    duplicate_text_within: dict[str, int] = {}

    for split, rows in records_by_split.items():
        ids = [str(row.get("id", "")) for row in rows]
        texts = [normalize_text(str(row.get("text", ""))) for row in rows]
        prompts = {
            str(row.get("prompt", "")).strip() for row in rows if str(row.get("prompt", "")).strip()
        }

        ids_by_split[split] = ids
        text_by_split[split] = texts
        prompts_by_split[split] = prompts

        duplicate_ids_within[split], _ = summarize_duplicates(ids)
        duplicate_text_within[split], _ = summarize_duplicates(texts)

        valid_scores = [
            parse_score(row.get("label")) for row in rows if is_valid_score(row.get("label"))
        ]
        if valid_scores:
            score_stats[split] = {
                "min": min(valid_scores),
                "max": max(valid_scores),
                "mean": sum(valid_scores) / len(valid_scores),
            }
        else:
            score_stats[split] = {"min": 0.0, "max": 0.0, "mean": 0.0}

    id_sets = {split: set(values) for split, values in ids_by_split.items()}
    text_sets = {split: set(values) for split, values in text_by_split.items()}

    split_id_overlap = {
        "train_validation": len(id_sets["train"] & id_sets["validation"]),
        "train_test": len(id_sets["train"] & id_sets["test"]),
        "validation_test": len(id_sets["validation"] & id_sets["test"]),
    }
    split_text_overlap = {
        "train_validation": len(text_sets["train"] & text_sets["validation"]),
        "train_test": len(text_sets["train"] & text_sets["test"]),
        "validation_test": len(text_sets["validation"] & text_sets["test"]),
    }

    prompt_overlap = {
        "train_validation": len(prompts_by_split["train"] & prompts_by_split["validation"]),
        "train_test": len(prompts_by_split["train"] & prompts_by_split["test"]),
        "validation_test": len(prompts_by_split["validation"] & prompts_by_split["test"]),
    }

    test_prompts = prompts_by_split["test"]
    validation_prompts = prompts_by_split["validation"]
    train_prompts = prompts_by_split["train"]

    prompt_coverage = {
        "test_in_train_pct": (
            (len(test_prompts & train_prompts) / len(test_prompts) * 100.0) if test_prompts else 0.0
        ),
        "validation_in_train_pct": (
            (len(validation_prompts & train_prompts) / len(validation_prompts) * 100.0)
            if validation_prompts
            else 0.0
        ),
    }

    hf_ok = True
    hf_message = "OK"
    try:
        if hf_disk_path.exists():
            ds = load_from_disk(str(hf_disk_path))
            if not isinstance(ds, DatasetDict):
                raise TypeError(
                    f"Existing load_from_disk artifact is {type(ds).__name__}, expected DatasetDict"
                )
        else:
            data_files = {
                split: str(dataset_dir / filename) for split, filename in SPLIT_FILES.items()
            }
            built = load_dataset("json", data_files=data_files)
            built.save_to_disk(str(hf_disk_path))
            ds = load_from_disk(str(hf_disk_path))
            if not isinstance(ds, DatasetDict):
                raise TypeError(
                    f"Saved artifact reloaded as {type(ds).__name__}, expected DatasetDict"
                )

        if set(ds.keys()) != {"train", "validation", "test"}:
            raise ValueError(f"Unexpected HF splits: {sorted(ds.keys())}")
    except Exception as exc:  # pragma: no cover - environment/runtime specific
        hf_ok = False
        hf_message = str(exc)

    report = render_report(
        dataset_dir=dataset_dir,
        per_file=per_file,
        split_sizes=split_sizes,
        score_stats=score_stats,
        duplicate_ids_within=duplicate_ids_within,
        duplicate_text_within=duplicate_text_within,
        split_id_overlap=split_id_overlap,
        split_text_overlap=split_text_overlap,
        prompt_overlap=prompt_overlap,
        prompt_coverage=prompt_coverage,
        hf_ok=hf_ok,
        hf_message=hf_message,
        hf_path=hf_disk_path,
    )
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "dataset_dir": str(dataset_dir),
                "hf_disk_path": str(hf_disk_path),
                "hf_ok": hf_ok,
                "id_overlap_train_test": split_id_overlap["train_test"],
                "text_overlap_train_test": split_text_overlap["train_test"],
                "prompt_overlap_train_test": prompt_overlap["train_test"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
