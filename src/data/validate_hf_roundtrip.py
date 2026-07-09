"""Validate JSONL datasets through Hugging Face roundtrip serialization.

For each discovered JSONL dataset under datasets/ this script will:
1. load JSONL via datasets.load_dataset("json", data_files=...)
2. validate feature/type compatibility by encoding every row
3. save_to_disk() to a local artifact path
4. load_from_disk() from that artifact
5. iterate through every split to catch serialization/runtime issues

Outputs a markdown PASS/FAIL report at docs/reports/hf_validation.md by default.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.paths import repo_root

DATASET_ROOT = repo_root(Path(__file__)) / "datasets"
HF_CACHE_ROOT = DATASET_ROOT / ".hf_cache"

SPLIT_NAMES = ("train", "validation", "test")


@dataclass(frozen=True)
class DatasetCase:
    """One dataset validation target and its split->file mapping."""

    name: str
    split_files: dict[str, Path]


@dataclass
class CaseResult:
    """Validation result for one dataset case."""

    name: str
    status: str
    files: dict[str, str]
    split_rows: dict[str, int] = field(default_factory=dict)
    feature_types: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    """Parse command-line args."""
    parser = argparse.ArgumentParser(description="Validate JSONL datasets via HF roundtrip.")
    parser.add_argument(
        "--datasets-root",
        default="datasets",
        help="Root directory to scan for JSONL datasets.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/hf_validation.md",
        help="Markdown output report path.",
    )
    parser.add_argument(
        "--artifacts-dir",
        default="datasets/hf_validation_artifacts",
        help="Directory for temporary save_to_disk artifacts.",
    )
    return parser.parse_args()


def discover_jsonl_files(root: Path) -> list[Path]:
    """Recursively discover JSONL files."""
    return sorted(path for path in root.rglob("*.jsonl") if path.is_file())


def group_cases(files: list[Path], root: Path) -> list[DatasetCase]:
    """Group split files into dataset cases; keep standalone JSONLs as single-split cases."""
    consumed: set[Path] = set()
    cases: list[DatasetCase] = []

    by_parent: dict[Path, dict[str, Path]] = {}
    for path in files:
        stem = path.stem.lower()
        if stem in SPLIT_NAMES:
            by_parent.setdefault(path.parent, {})[stem] = path

    for parent, split_files in sorted(by_parent.items(), key=lambda item: str(item[0])):
        name = str(parent.relative_to(root))
        cases.append(DatasetCase(name=name, split_files=dict(sorted(split_files.items()))))
        consumed.update(split_files.values())

    for path in files:
        if path in consumed:
            continue
        name = str(path.relative_to(root))
        cases.append(DatasetCase(name=name, split_files={"train": path}))

    return sorted(cases, key=lambda case: case.name)


def features_to_string(features: object) -> str:
    """Stable feature summary string."""
    to_dict = getattr(features, "to_dict", None)
    if callable(to_dict):
        return json.dumps(to_dict(), sort_keys=True, ensure_ascii=False)
    return str(features)


def validate_feature_types(dataset: object) -> list[str]:
    """Validate all rows can be encoded by the split features."""
    errors: list[str] = []
    features = dataset.features  # type: ignore[attr-defined]
    for row_index, row in enumerate(dataset):
        try:
            features.encode_example(row)
        except Exception as exc:  # pragma: no cover - runtime-specific decoder errors
            errors.append(f"row {row_index}: {exc}")
            if len(errors) >= 50:
                errors.append("feature validation truncated after 50 errors")
                break
    return errors


def _to_hf_safe_scalar(value: Any) -> Any:
    """Convert complex JSON-compatible values into stable scalar representations."""
    if value is None or isinstance(value, bool | int | float | str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return repr(value)


def _load_jsonl_case_with_fallback(
    case: DatasetCase,
) -> tuple[object | None, list[str], list[str]]:
    """Load JSONL splits with a schema-tolerant fallback using Dataset.from_list."""
    from datasets import Dataset, DatasetDict

    notes: list[str] = []
    errors: list[str] = []
    split_datasets: dict[str, Dataset] = {}

    for split, path in sorted(case.split_files.items()):
        rows: list[dict[str, Any]] = []
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    raw = line.strip()
                    if not raw:
                        continue
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        errors.append(f"[{split}] line {line_number} JSON parse error: {exc}")
                        continue

                    if isinstance(payload, dict):
                        row = {key: _to_hf_safe_scalar(value) for key, value in payload.items()}
                    else:
                        row = {"__raw_json": _to_hf_safe_scalar(payload)}
                    rows.append(row)
        except UnicodeDecodeError as exc:
            errors.append(f"[{split}] utf-8 decode error: {exc}")
            continue
        except OSError as exc:
            errors.append(f"[{split}] read error: {exc}")
            continue

        split_datasets[split] = Dataset.from_list(rows)

    if errors:
        return None, notes, errors

    notes.append(
        "Loaded with schema-tolerant fallback " "(complex fields serialized to JSON strings)."
    )
    return DatasetDict(split_datasets), notes, errors


def validate_case(case: DatasetCase, artifacts_dir: Path) -> CaseResult:
    """Run full roundtrip validation for one case."""
    from datasets import Dataset, DatasetDict, load_dataset, load_from_disk

    result = CaseResult(
        name=case.name,
        status="PASS",
        files={split: str(path) for split, path in case.split_files.items()},
    )

    data_files = {split: str(path) for split, path in case.split_files.items()}
    save_path = artifacts_dir / case.name.replace("/", "__")

    try:
        if save_path.exists():
            shutil.rmtree(save_path)

        loaded: Dataset | DatasetDict
        try:
            loaded = load_dataset("json", data_files=data_files)
        except Exception as exc:
            fallback_ds, fallback_notes, fallback_errors = _load_jsonl_case_with_fallback(case)
            if fallback_errors:
                raise RuntimeError("Primary load failed and fallback loader also failed.") from exc
            if fallback_ds is None:
                raise RuntimeError("Fallback loader returned no dataset.") from exc
            loaded = fallback_ds
            result.notes.extend(fallback_notes)
        if isinstance(loaded, Dataset):
            dataset_dict = DatasetDict({"train": loaded})
        elif isinstance(loaded, DatasetDict):
            dataset_dict = loaded
        else:
            raise TypeError(f"Unexpected dataset object: {type(loaded).__name__}")

        for split in sorted(dataset_dict.keys()):
            split_ds = dataset_dict[split]
            result.split_rows[split] = split_ds.num_rows
            result.feature_types[split] = features_to_string(split_ds.features)

            type_errors = validate_feature_types(split_ds)
            if type_errors:
                result.errors.extend([f"[{split}] {error}" for error in type_errors])

        dataset_dict.save_to_disk(str(save_path))
        reloaded = load_from_disk(str(save_path))
        if isinstance(reloaded, Dataset):
            reloaded_dict = DatasetDict({"train": reloaded})
        elif isinstance(reloaded, DatasetDict):
            reloaded_dict = reloaded
        else:
            raise TypeError(f"Unexpected reloaded object: {type(reloaded).__name__}")

        for split in sorted(reloaded_dict.keys()):
            iter_count = 0
            for _row in reloaded_dict[split]:
                iter_count += 1
            expected = result.split_rows.get(split, 0)
            if iter_count != expected:
                result.errors.append(
                    f"[{split}] row count mismatch after reload: "
                    f"expected {expected}, got {iter_count}"
                )

            original_feature = result.feature_types.get(split, "")
            reloaded_feature = features_to_string(reloaded_dict[split].features)
            if original_feature != reloaded_feature:
                result.errors.append(f"[{split}] feature schema changed across roundtrip")

    except Exception as exc:  # pragma: no cover - runtime-specific I/O/parser errors
        message = str(exc).strip() or repr(exc)
        if exc.__cause__ is not None:
            cause_message = str(exc.__cause__).strip() or repr(exc.__cause__)
            message = f"{message} | cause: {cause_message}"
        result.errors.append(f"{type(exc).__name__}: {message}")

    if result.errors:
        result.status = "FAIL"

    return result


def render_report(results: list[CaseResult], datasets_root: Path) -> str:
    """Render markdown report."""
    passed = sum(1 for item in results if item.status == "PASS")
    failed = len(results) - passed

    lines = [
        "# HF Validation Report",
        "",
        f"- Datasets root: `{datasets_root}`",
        f"- Dataset cases checked: `{len(results)}`",
        f"- PASS: `{passed}`",
        f"- FAIL: `{failed}`",
        "",
        "## Case Summary",
        "",
        "| Dataset | Status | Splits | Rows |",
        "|---|---|---|---|",
    ]

    for item in results:
        splits = ", ".join(sorted(item.files.keys()))
        rows = ", ".join(f"{split}:{count}" for split, count in sorted(item.split_rows.items()))
        lines.append(f"| `{item.name}` | **{item.status}** | `{splits}` | `{rows}` |")

    lines.extend(["", "## Details", ""])

    for item in results:
        lines.append(f"### {item.name}")
        lines.append(f"- Status: **{item.status}**")
        lines.append("- Files:")
        for split, path in sorted(item.files.items()):
            lines.append(f"- `{split}`: `{path}`")

        lines.append("- Feature types by split:")
        if item.feature_types:
            for split, feature_json in sorted(item.feature_types.items()):
                lines.append(f"- `{split}`: `{feature_json}`")
        else:
            lines.append("- None")

        lines.append("- Errors:")
        if item.errors:
            for error in item.errors:
                lines.append(f"- {error}")
        else:
            lines.append("- None")
        lines.append("- Notes:")
        if item.notes:
            for note in item.notes:
                lines.append(f"- {note}")
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Entry point."""
    # Keep Hugging Face cache inside workspace for restricted environments.
    os.environ.setdefault("HF_HOME", str(HF_CACHE_ROOT))
    os.environ.setdefault("HF_DATASETS_CACHE", str(HF_CACHE_ROOT / "datasets"))

    args = parse_args()
    datasets_root = Path(args.datasets_root)
    report_path = Path(args.report_path)
    artifacts_dir = Path(args.artifacts_dir)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    HF_CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    files = discover_jsonl_files(datasets_root)
    cases = group_cases(files, datasets_root)
    results = [validate_case(case, artifacts_dir) for case in cases]

    report = render_report(results, datasets_root)
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "datasets_root": str(datasets_root),
                "cases": len(cases),
                "passed": sum(1 for item in results if item.status == "PASS"),
                "failed": sum(1 for item in results if item.status == "FAIL"),
                "report_path": str(report_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
