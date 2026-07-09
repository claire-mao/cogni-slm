"""Normalize all datasets into a single unified schema.

Required unified fields:
- id
- task
- prompt
- input
- response
- score
- rubric
- source
- license
- split
- metadata

This script preserves original row payloads under `metadata.original_fields`
and records source-to-unified field mappings in `docs/reports/schema_mapping.md`.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.utils.paths import repo_root

DATASET_ROOT = repo_root(Path(__file__)) / "datasets"
HF_CACHE_ROOT = DATASET_ROOT / ".hf_cache"

TEXT_ENCODINGS = ("utf-8-sig", "cp1252", "latin-1")
SPLIT_NAMES = ("train", "validation", "test")
STRUCTURED_FILE_EXTENSIONS = {".csv", ".tsv", ".json", ".txt"}

ID_FIELDS = (
    "id",
    "essay_id",
    "example_id",
    "uuid",
    "source_id",
)
TASK_FIELDS = ("task", "task_mode", "domain_tag")
PROMPT_FIELDS = (
    "prompt",
    "context",
    "essay_set",
    "prompt_id",
    "assignment",
    "task_prompt",
    "source_text",
)
INPUT_FIELDS = (
    "input",
    "text",
    "essay",
    "argument_text",
    "student_response",
    "response_text",
    "content",
)
RESPONSE_FIELDS = (
    "response",
    "output",
    "target",
    "teacher_reasoning",
    "score_explanation",
    "analysis",
    "feedback",
)
SCORE_FIELDS = (
    "score",
    "label",
    "rubric_score",
    "domain1_score",
    "holistic_essay_score",
    "overall_score",
)
RUBRIC_FIELDS = (
    "rubric",
    "rubric_hooks",
    "expected_sections",
    "prohibited_behaviors",
    "required_behaviors",
)
SOURCE_FIELDS = ("source", "dataset", "source_dataset")
LICENSE_FIELDS = ("license", "license_name", "dataset_license")
SPLIT_FIELDS = ("split", "dataset_split", "split_hint")

EXCLUDED_DIR_NAMES = {
    ".hf_cache",
    "hf_validation_artifacts",
    "processed/unified",
}


@dataclass(frozen=True)
class SourceCase:
    """One source dataset case."""

    name: str
    kind: str
    split_files: dict[str, Path] = field(default_factory=dict)
    dataset_dict_path: Path | None = None
    file_path: Path | None = None


@dataclass
class MappingTracker:
    """Tracks mapping usage for one source case."""

    source_fields_seen: set[str] = field(default_factory=set)
    target_to_source_counts: dict[str, Counter[str]] = field(
        default_factory=lambda: defaultdict(Counter)
    )
    parse_error_count: int = 0
    row_count: int = 0
    output_count: int = 0


@dataclass
class CaseOutput:
    """Normalization outputs and stats for one source case."""

    case: SourceCase
    output_path: Path
    tracker: MappingTracker


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description="Normalize datasets into one unified schema.")
    parser.add_argument(
        "--datasets-root",
        default="datasets",
        help="Datasets root directory to scan.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/processed/unified",
        help="Output directory for unified JSONL datasets.",
    )
    parser.add_argument(
        "--combined-output",
        default="datasets/processed/unified/unified_all.jsonl",
        help="Combined unified JSONL output path.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/schema_mapping.md",
        help="Schema mapping report output path.",
    )
    return parser.parse_args()


def is_excluded_path(path: Path, root: Path) -> bool:
    """Return whether a path should be excluded from source scan."""
    rel = str(path.relative_to(root)).replace("\\", "/")
    return any(rel == name or rel.startswith(f"{name}/") for name in EXCLUDED_DIR_NAMES)


def discover_jsonl_cases(root: Path) -> list[SourceCase]:
    """Discover JSONL-based dataset cases.

    Split triplets in the same directory are grouped into one case.
    Other JSONL files are treated as standalone train-only cases.
    """
    files = sorted(path for path in root.rglob("*.jsonl") if path.is_file())
    files = [path for path in files if not is_excluded_path(path, root)]

    consumed: set[Path] = set()
    grouped: list[SourceCase] = []

    by_parent: dict[Path, dict[str, Path]] = {}
    for path in files:
        stem = path.stem.lower()
        if stem in SPLIT_NAMES:
            by_parent.setdefault(path.parent, {})[stem] = path

    for parent, split_files in sorted(by_parent.items(), key=lambda item: str(item[0])):
        rel = str(parent.relative_to(root)).replace("\\", "/")
        grouped.append(
            SourceCase(name=rel, kind="jsonl", split_files=dict(sorted(split_files.items())))
        )
        consumed.update(split_files.values())

    for path in files:
        if path in consumed:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        grouped.append(SourceCase(name=rel, kind="jsonl", split_files={"train": path}))

    return sorted(grouped, key=lambda case: case.name)


def discover_hf_dataset_dict_cases(root: Path) -> list[SourceCase]:
    """Discover Hugging Face DatasetDict directories by dataset_dict.json."""
    cases: list[SourceCase] = []
    for config in sorted(root.rglob("dataset_dict.json")):
        ds_dir = config.parent
        if is_excluded_path(ds_dir, root):
            continue
        rel = str(ds_dir.relative_to(root)).replace("\\", "/")
        cases.append(SourceCase(name=f"{rel}#hf", kind="hf_dataset_dict", dataset_dict_path=ds_dir))
    return sorted(cases, key=lambda case: case.name)


def discover_structured_file_cases(root: Path) -> list[SourceCase]:
    """Discover standalone structured files (.csv/.tsv/.json/.txt)."""
    cases: list[SourceCase] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if is_excluded_path(path, root):
            continue
        if path.suffix.lower() not in STRUCTURED_FILE_EXTENSIONS:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        cases.append(SourceCase(name=rel, kind="structured_file", file_path=path))
    return sorted(cases, key=lambda case: case.name)


def infer_split_from_name(path: Path) -> str:
    """Infer split from filename/path heuristics."""
    name = path.name.lower()
    if "train" in name:
        return "train"
    if "valid" in name or "val" in name or "dev" in name:
        return "validation"
    if "test" in name:
        return "test"
    return "train"


def safe_case_filename(case_name: str, kind: str) -> str:
    """Build a stable filesystem-safe filename from case metadata."""
    normalized = case_name.replace("\\", "/")
    normalized = normalized.replace("/", "__").replace("#", "_")
    for suffix in (".jsonl", ".json", ".csv", ".tsv", ".txt"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
            break
    normalized = normalized.strip("_")
    if kind == "hf_dataset_dict":
        normalized = f"{normalized}_hf"
    if not normalized:
        normalized = "dataset"
    return f"{normalized}.jsonl"


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    """Read text with robust encoding fallback."""
    errors: list[str] = []
    for encoding in TEXT_ENCODINGS:
        try:
            return path.read_text(encoding=encoding), encoding
        except UnicodeDecodeError as exc:
            errors.append(f"{encoding}: {exc}")
    detail = " | ".join(errors) if errors else "unknown"
    raise UnicodeDecodeError("unknown", b"", 0, 1, f"Failed to decode {path}: {detail}")


def to_text(value: Any) -> str:
    """Convert arbitrary value to text representation."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict | list | tuple):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def normalize_split(value: str, fallback: str) -> str:
    """Normalize split to train/validation/test when possible."""
    raw = value.strip().lower()
    if not raw:
        return fallback
    if raw in {"train", "training"}:
        return "train"
    if raw in {"validation", "val", "valid", "dev"}:
        return "validation"
    if raw in {"test", "testing"}:
        return "test"
    return fallback


def choose_field(
    row: dict[str, Any],
    candidates: tuple[str, ...],
    target: str,
    tracker: MappingTracker,
) -> tuple[str, str]:
    """Choose first non-empty candidate field value for a target."""
    for key in candidates:
        if key in row:
            value = to_text(row.get(key))
            if value:
                tracker.target_to_source_counts[target][key] += 1
                return value, key
    tracker.target_to_source_counts[target]["<inferred>"] += 1
    return "", "<inferred>"


def infer_task(row: dict[str, Any], tracker: MappingTracker) -> tuple[str, str]:
    """Infer task from explicit fields or schema clues."""
    explicit, source_key = choose_field(row, TASK_FIELDS, "task", tracker)
    if explicit:
        return explicit, source_key

    keys = {key.lower() for key in row.keys()}
    if keys.intersection({"primary_fallacy_label", "acceptable_alternative_labels"}):
        tracker.target_to_source_counts["task"]["<inferred:fallacy_reasoning>"] += 1
        return "fallacy_reasoning", "<inferred:fallacy_reasoning>"
    if keys.intersection({"essay", "text", "domain1_score", "rubric_score"}):
        tracker.target_to_source_counts["task"]["<inferred:essay_scoring>"] += 1
        return "essay_scoring", "<inferred:essay_scoring>"

    tracker.target_to_source_counts["task"]["<inferred:unknown>"] += 1
    return "unknown", "<inferred:unknown>"


def infer_score(
    row: dict[str, Any],
    tracker: MappingTracker,
) -> tuple[float | None, str, str | None]:
    """Infer numeric score and keep raw fallback for metadata."""
    value, source_key = choose_field(row, SCORE_FIELDS, "score", tracker)
    if not value:
        return None, source_key, None
    try:
        return float(value), source_key, value
    except ValueError:
        tracker.target_to_source_counts["score"]["<non_numeric>"] += 1
        return None, source_key, value


def infer_id(
    row: dict[str, Any],
    tracker: MappingTracker,
    fallback_prefix: str,
    row_index: int,
) -> tuple[str, str]:
    """Infer record id with deterministic fallback."""
    rid, source_key = choose_field(row, ID_FIELDS, "id", tracker)
    if rid:
        return rid, source_key

    inferred = f"{fallback_prefix}:{row_index:08d}"
    tracker.target_to_source_counts["id"]["<generated>"] += 1
    return inferred, "<generated>"


def normalize_row(
    *,
    row: dict[str, Any],
    tracker: MappingTracker,
    case_name: str,
    source_ref: str,
    row_index: int,
    split_hint: str,
    encoding: str,
) -> dict[str, Any]:
    """Normalize one source row into unified schema."""
    tracker.source_fields_seen.update(row.keys())

    record_id, id_source = infer_id(row, tracker, fallback_prefix=case_name, row_index=row_index)
    task, task_source = infer_task(row, tracker)

    prompt, prompt_source = choose_field(row, PROMPT_FIELDS, "prompt", tracker)
    model_input, input_source = choose_field(row, INPUT_FIELDS, "input", tracker)
    response, response_source = choose_field(row, RESPONSE_FIELDS, "response", tracker)
    rubric, rubric_source = choose_field(row, RUBRIC_FIELDS, "rubric", tracker)

    source, source_source = choose_field(row, SOURCE_FIELDS, "source", tracker)
    if not source:
        source = case_name
        source_source = "<case_name>"
        tracker.target_to_source_counts["source"]["<case_name>"] += 1

    license_name, license_source = choose_field(row, LICENSE_FIELDS, "license", tracker)
    if not license_name:
        license_name = "unknown"
        license_source = "<unknown>"
        tracker.target_to_source_counts["license"]["<unknown>"] += 1

    split_value, split_source = choose_field(row, SPLIT_FIELDS, "split", tracker)
    split = normalize_split(split_value, fallback=split_hint)

    score, score_source, score_raw = infer_score(row, tracker)

    mapping_info = {
        "id": id_source,
        "task": task_source,
        "prompt": prompt_source,
        "input": input_source,
        "response": response_source,
        "score": score_source,
        "rubric": rubric_source,
        "source": source_source,
        "license": license_source,
        "split": split_source,
    }

    used_keys = {key for key in mapping_info.values() if key and not key.startswith("<")}
    metadata = {
        "source_case": case_name,
        "source_ref": source_ref,
        "row_index": row_index,
        "encoding": encoding,
        "score_raw": score_raw,
        "mapping": mapping_info,
        "unmapped_fields": sorted(key for key in row.keys() if key not in used_keys),
        "original_fields": row,
    }

    tracker.row_count += 1
    tracker.output_count += 1

    return {
        "id": record_id,
        "task": task,
        "prompt": prompt,
        "input": model_input,
        "response": response,
        "score": score,
        "rubric": rubric,
        "source": source,
        "license": license_name,
        "split": split,
        "metadata": metadata,
    }


def load_jsonl_rows(path: Path) -> tuple[list[dict[str, Any]], str, list[str]]:
    """Load rows from JSONL with parse error collection."""
    text, encoding = read_text_with_fallback(path)
    rows: list[dict[str, Any]] = []
    parse_errors: list[str] = []

    for line_number, line in enumerate(text.splitlines(), start=1):
        raw = line.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            parse_errors.append(f"line {line_number}: {exc.msg}")
            rows.append(
                {
                    "raw_line": raw,
                    "parse_error": exc.msg,
                    "line_number": line_number,
                }
            )
            continue

        if isinstance(payload, dict):
            rows.append(payload)
        else:
            rows.append(
                {
                    "raw_value": payload,
                    "parse_error": "non_object_jsonl_value",
                    "line_number": line_number,
                }
            )

    return rows, encoding, parse_errors


def load_structured_rows(path: Path) -> tuple[list[dict[str, Any]], str, list[str]]:
    """Load rows from structured file formats."""
    suffix = path.suffix.lower()
    parse_errors: list[str] = []

    if suffix == ".txt":
        text, encoding = read_text_with_fallback(path)
        return [{"id": path.stem, "text": text}], encoding, parse_errors

    if suffix in {".csv", ".tsv"}:
        text, encoding = read_text_with_fallback(path)
        delimiter = "," if suffix == ".csv" else "\t"
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            parse_errors.append("missing_header")
            return [{"parse_error": "missing_header"}], encoding, parse_errors
        rows = []
        for row in reader:
            rows.append({key: value for key, value in row.items()})
        return rows, encoding, parse_errors

    if suffix == ".json":
        text, encoding = read_text_with_fallback(path)
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            parse_errors.append(exc.msg)
            return (
                [{"parse_error": exc.msg, "raw_text": text}],
                encoding,
                parse_errors,
            )

        if isinstance(payload, dict):
            if "records" in payload and isinstance(payload["records"], list):
                rows = []
                for item in payload["records"]:
                    if isinstance(item, dict):
                        rows.append(item)
                    else:
                        rows.append({"raw_value": item, "parse_error": "non_object_record"})
                return rows, encoding, parse_errors
            return [payload], encoding, parse_errors

        if isinstance(payload, list):
            rows = []
            for item in payload:
                if isinstance(item, dict):
                    rows.append(item)
                else:
                    rows.append({"raw_value": item, "parse_error": "non_object_record"})
            return rows, encoding, parse_errors

        return (
            [{"raw_value": payload, "parse_error": "unsupported_json_root"}],
            encoding,
            parse_errors,
        )

    return [{"parse_error": "unsupported_extension"}], "unknown", ["unsupported_extension"]


def normalize_jsonl_case(case: SourceCase, output_root: Path) -> CaseOutput:
    """Normalize one JSONL case into unified schema JSONL."""
    tracker = MappingTracker()
    output_path = output_root / safe_case_filename(case.name, case.kind)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as handle:
        for split_hint, path in sorted(case.split_files.items()):
            rows, encoding, parse_errors = load_jsonl_rows(path)
            tracker.parse_error_count += len(parse_errors)

            for idx, row in enumerate(rows, start=1):
                normalized = normalize_row(
                    row=row,
                    tracker=tracker,
                    case_name=case.name,
                    source_ref=str(path),
                    row_index=idx,
                    split_hint=split_hint,
                    encoding=encoding,
                )
                handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    return CaseOutput(case=case, output_path=output_path, tracker=tracker)


def normalize_hf_case(case: SourceCase, output_root: Path) -> CaseOutput:
    """Normalize one Hugging Face DatasetDict case into unified schema JSONL."""
    from datasets import Dataset, DatasetDict, load_from_disk

    tracker = MappingTracker()
    output_path = output_root / safe_case_filename(case.name, case.kind)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if case.dataset_dict_path is None:
        raise ValueError(f"Missing dataset_dict_path for case {case.name}")

    loaded = load_from_disk(str(case.dataset_dict_path))
    if isinstance(loaded, DatasetDict):
        dataset_dict = loaded
    elif isinstance(loaded, Dataset):
        dataset_dict = DatasetDict({"train": loaded})
    else:
        raise TypeError(f"Unsupported HF dataset type: {type(loaded).__name__}")

    with output_path.open("w", encoding="utf-8") as handle:
        for split_hint in sorted(dataset_dict.keys()):
            split_dataset = dataset_dict[split_hint]
            for idx, row in enumerate(split_dataset, start=1):
                normalized = normalize_row(
                    row=dict(row),
                    tracker=tracker,
                    case_name=case.name,
                    source_ref=f"{case.dataset_dict_path}#{split_hint}",
                    row_index=idx,
                    split_hint=normalize_split(split_hint, fallback="train"),
                    encoding="hf_arrow",
                )
                handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    return CaseOutput(case=case, output_path=output_path, tracker=tracker)


def normalize_structured_case(case: SourceCase, output_root: Path) -> CaseOutput:
    """Normalize one structured file case into unified schema JSONL."""
    tracker = MappingTracker()
    output_path = output_root / safe_case_filename(case.name, case.kind)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if case.file_path is None:
        raise ValueError(f"Missing file_path for case {case.name}")

    split_hint = infer_split_from_name(case.file_path)
    rows, encoding, parse_errors = load_structured_rows(case.file_path)
    tracker.parse_error_count += len(parse_errors)

    with output_path.open("w", encoding="utf-8") as handle:
        for idx, row in enumerate(rows, start=1):
            normalized = normalize_row(
                row=row,
                tracker=tracker,
                case_name=case.name,
                source_ref=str(case.file_path),
                row_index=idx,
                split_hint=split_hint,
                encoding=encoding,
            )
            handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")

    return CaseOutput(case=case, output_path=output_path, tracker=tracker)


def render_mapping_report(
    case_outputs: list[CaseOutput],
    output_root: Path,
    combined_path: Path,
    combined_rows: int,
) -> str:
    """Render markdown schema mapping report."""
    total_parse_errors = sum(item.tracker.parse_error_count for item in case_outputs)

    lines = [
        "# Schema Mapping Report",
        "",
        "Unified schema:",
        "",
        "- `id`",
        "- `task`",
        "- `prompt`",
        "- `input`",
        "- `response`",
        "- `score`",
        "- `rubric`",
        "- `source`",
        "- `license`",
        "- `split`",
        "- `metadata`",
        "",
        f"- Source cases normalized: `{len(case_outputs)}`",
        f"- Total unified rows written: `{combined_rows}`",
        f"- Total parse errors captured (as metadata rows): `{total_parse_errors}`",
        f"- Per-case unified outputs dir: `{output_root}`",
        f"- Combined unified output: `{combined_path}`",
        "",
        "## Per-Source Field Mapping",
        "",
    ]

    target_order = (
        "id",
        "task",
        "prompt",
        "input",
        "response",
        "score",
        "rubric",
        "source",
        "license",
        "split",
    )

    for item in sorted(case_outputs, key=lambda out: out.case.name):
        tracker = item.tracker
        lines.append(f"### {item.case.name}")
        lines.append("")
        lines.append(f"- Kind: `{item.case.kind}`")
        lines.append(f"- Unified output: `{item.output_path}`")
        lines.append(f"- Rows normalized: `{tracker.output_count}`")
        lines.append(f"- Parse errors captured: `{tracker.parse_error_count}`")
        lines.append("")
        lines.append("| Unified field | Source field usage |")
        lines.append("|---|---|")

        for target in target_order:
            counter = tracker.target_to_source_counts.get(target, Counter())
            if counter:
                usage = ", ".join(f"`{src}` ({count})" for src, count in counter.most_common())
            else:
                usage = "`<none>`"
            lines.append(f"| `{target}` | {usage} |")

        lines.append("")
        lines.append("| Source field | Mapped to |")
        lines.append("|---|---|")

        source_to_targets: dict[str, set[str]] = defaultdict(set)
        for target, counter in tracker.target_to_source_counts.items():
            for source_field in counter:
                if source_field.startswith("<"):
                    continue
                source_to_targets[source_field].add(target)

        for source_field in sorted(tracker.source_fields_seen):
            targets = sorted(source_to_targets.get(source_field, set()))
            if targets:
                mapped = ", ".join(f"`{target}`" for target in targets)
            else:
                mapped = "`metadata.original_fields`"
            lines.append(f"| `{source_field}` | {mapped} |")

        lines.append("")

    lines.append("## Preservation Guarantee")
    lines.append("")
    lines.append(
        "All parsed source keys and values are preserved verbatim under "
        "`metadata.original_fields` for every unified row."
    )
    lines.append(
        "Fields not directly mapped to a unified top-level field are listed in "
        "`metadata.unmapped_fields`."
    )

    return "\n".join(lines)


def write_combined(case_outputs: list[CaseOutput], combined_path: Path) -> int:
    """Write a combined unified JSONL from all per-case outputs."""
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    row_count = 0

    with combined_path.open("w", encoding="utf-8") as out_handle:
        for item in sorted(case_outputs, key=lambda out: out.case.name):
            if not item.output_path.exists():
                continue
            for line in item.output_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                out_handle.write(line + "\n")
                row_count += 1

    return row_count


def main() -> None:
    """Run unified normalization and mapping report generation."""
    os.environ.setdefault("HF_HOME", str(HF_CACHE_ROOT))
    os.environ.setdefault("HF_DATASETS_CACHE", str(HF_CACHE_ROOT / "datasets"))

    args = parse_args()
    datasets_root = Path(args.datasets_root)
    output_root = Path(args.output_dir)
    combined_path = Path(args.combined_output)
    report_path = Path(args.report_path)

    output_root.mkdir(parents=True, exist_ok=True)
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    HF_CACHE_ROOT.mkdir(parents=True, exist_ok=True)

    jsonl_cases = discover_jsonl_cases(datasets_root)
    structured_cases = discover_structured_file_cases(datasets_root)
    hf_cases = discover_hf_dataset_dict_cases(datasets_root)

    case_outputs: list[CaseOutput] = []
    for case in jsonl_cases:
        case_outputs.append(normalize_jsonl_case(case=case, output_root=output_root))

    for case in structured_cases:
        case_outputs.append(normalize_structured_case(case=case, output_root=output_root))

    for case in hf_cases:
        case_outputs.append(normalize_hf_case(case=case, output_root=output_root))

    combined_rows = write_combined(case_outputs=case_outputs, combined_path=combined_path)
    report = render_mapping_report(
        case_outputs=case_outputs,
        output_root=output_root,
        combined_path=combined_path,
        combined_rows=combined_rows,
    )
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "datasets_root": str(datasets_root),
                "jsonl_cases": len(jsonl_cases),
                "structured_file_cases": len(structured_cases),
                "hf_dataset_dict_cases": len(hf_cases),
                "total_cases": len(case_outputs),
                "combined_rows": combined_rows,
                "output_root": str(output_root),
                "combined_output": str(combined_path),
                "report_path": str(report_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
