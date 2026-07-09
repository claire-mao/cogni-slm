"""Generate dataset cards for configured source datasets.

Each card includes:
- source
- license
- citation
- task
- score range
- known limitations
- intended use
- ethical considerations
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DatasetSpec:
    """Metadata for a dataset card."""

    key: str
    name: str
    source: str
    homepage: str
    citation: str
    license_name: str
    task: str
    raw_dir: str
    primary_file: str | None
    score_field: str | None


def parse_args() -> argparse.Namespace:
    """Parse command line args."""
    parser = argparse.ArgumentParser(description="Generate markdown dataset cards.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root containing datasets/ and docs/.",
    )
    parser.add_argument(
        "--output-dir",
        default="docs/datasets/dataset_cards",
        help="Output directory for generated markdown cards.",
    )
    return parser.parse_args()


def detect_row_count_and_score_range(
    dataset_dir: Path,
    primary_file: str | None,
    score_field: str | None,
) -> tuple[int | None, tuple[float, float] | None, str | None]:
    """Detect row count and score range from a known tabular source file."""
    if not primary_file or not score_field:
        return None, None, None

    file_path = dataset_dir / primary_file
    if not file_path.exists():
        return None, None, None

    delimiter = "\t" if file_path.suffix.lower() == ".tsv" else ","
    encodings = ("utf-8-sig", "cp1252", "latin-1")

    last_error: str | None = None
    for encoding in encodings:
        try:
            row_count = 0
            score_min: float | None = None
            score_max: float | None = None
            with file_path.open("r", encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle, delimiter=delimiter)
                for row in reader:
                    row_count += 1
                    raw = (row.get(score_field) or "").strip()
                    if raw == "":
                        continue
                    try:
                        value = float(raw)
                    except ValueError:
                        continue
                    score_min = value if score_min is None else min(score_min, value)
                    score_max = value if score_max is None else max(score_max, value)
            score_range = (
                (score_min, score_max) if score_min is not None and score_max is not None else None
            )
            return row_count, score_range, encoding
        except UnicodeDecodeError as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            continue

    return None, None, f"decode_failed: {last_error}" if last_error else "decode_failed"


def load_download_status(repo_root: Path) -> dict[str, dict[str, Any]]:
    """Load existing acquisition summary if present."""
    summary_path = repo_root / "outputs" / "data_ingestion" / "download_summary.json"
    if not summary_path.exists():
        return {}

    try:
        payload = json.loads(summary_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    by_key: dict[str, dict[str, Any]] = {}
    for item in payload.get("results", []):
        key = item.get("key")
        if isinstance(key, str):
            by_key[key] = item
    return by_key


def format_score_range(value: tuple[float, float] | None) -> str:
    """Render score range."""
    if value is None:
        return "Unknown (source file unavailable or score field not provided)"
    return f"{value[0]:.2f} to {value[1]:.2f}"


def render_card(
    spec: DatasetSpec,
    raw_path: Path,
    row_count: int | None,
    score_range: tuple[float, float] | None,
    detected_encoding: str | None,
    download_status: dict[str, Any] | None,
) -> str:
    """Render one dataset card markdown."""
    file_count = len([p for p in raw_path.rglob("*") if p.is_file()]) if raw_path.exists() else 0
    status = (download_status or {}).get("status", "unknown")
    message = (download_status or {}).get("message", "No acquisition status recorded.")

    known_limitations = [
        "License metadata may differ across mirrors; verify official terms before redistribution.",
        "Scores and prompts may be prompt-specific and not directly comparable across datasets.",
    ]
    if row_count is None:
        known_limitations.append(
            "No parseable primary scoring file detected in this workspace; card fields are partial."
        )

    return "\n".join(
        [
            f"# Dataset Card: {spec.name}",
            "",
            "## Source",
            f"- Name: `{spec.name}`",
            f"- Source location: `{raw_path}`",
            f"- Homepage: {spec.homepage}",
            f"- Local file count: `{file_count}`",
            f"- Acquisition status: `{status}`",
            f"- Acquisition note: {message}",
            "",
            "## License",
            f"- {spec.license_name}",
            "",
            "## Citation",
            f"- {spec.citation}",
            "",
            "## Task",
            f"- {spec.task}",
            "",
            "## Score Range",
            f"- Score range: {format_score_range(score_range)}",
            (
                "- Example count from primary file: "
                f"`{row_count if row_count is not None else 'Unknown'}`"
            ),
            f"- Detected encoding: `{detected_encoding if detected_encoding else 'Unknown'}`",
            "",
            "## Known Limitations",
            *[f"- {item}" for item in known_limitations],
            "",
            "## Intended Use",
            (
                "- Local research and model development for rubric-based writing "
                "feedback, subject to upstream license terms."
            ),
            (
                "- Educational NLP experimentation (scoring calibration, feedback "
                "quality evaluation, and robustness testing)."
            ),
            "",
            "## Ethical Considerations",
            (
                "- Treat student writing as sensitive educational data; avoid "
                "re-identification attempts."
            ),
            (
                "- Assess and mitigate potential bias across prompt types, "
                "demographics, and writing styles."
            ),
            "- Do not present automated scores as replacement for human educator judgment.",
            "",
        ]
    )


def main() -> None:
    """Generate all dataset cards."""
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_dir = (repo_root / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    datasets = [
        DatasetSpec(
            key="asap_aes",
            name="ASAP-AES",
            source="Hewlett Foundation ASAP AES release / mirrors",
            homepage="https://www.kaggle.com/c/asap-aes",
            citation=(
                "Hewlett Foundation. Automated Student Assessment Prize (ASAP) - "
                "Automated Essay Scoring."
            ),
            license_name=(
                "Public competition/research dataset terms "
                "(verify official terms in your acquisition source)."
            ),
            task="Automated essay scoring",
            raw_dir="datasets/raw/asap_aes",
            primary_file="training_set_rel3.tsv",
            score_field="domain1_score",
        ),
        DatasetSpec(
            key="persuade2",
            name="PERSUADE 2.0",
            source="Kaggle Feedback Prize / official PERSUADE releases",
            homepage="https://www.kaggle.com/competitions/feedback-prize-effectiveness",
            citation="Kaggle Feedback Prize resources and PERSUADE corpus references.",
            license_name="Kaggle/official source terms (manual acceptance commonly required).",
            task="Argumentative writing quality and feedback effectiveness",
            raw_dir="datasets/raw/persuade2",
            primary_file=None,
            score_field=None,
        ),
        DatasetSpec(
            key="asap2",
            name="ASAP 2.0",
            source="ASAP 2.0 public mirrors / official source",
            homepage="https://huggingface.co/datasets/jatinmehra/Automated-Essay-Scoring-2.0",
            citation="ASAP 2.0 mirror references (verify canonical citation for chosen source).",
            license_name=(
                "Unknown on mirror; must be verified before redistribution " "or training release."
            ),
            task="Automated essay scoring",
            raw_dir="datasets/raw/asap2",
            primary_file=None,
            score_field=None,
        ),
    ]

    download_status = load_download_status(repo_root)

    generated: list[str] = []
    for spec in datasets:
        raw_path = repo_root / spec.raw_dir
        row_count, score_range, detected_encoding = detect_row_count_and_score_range(
            raw_path,
            spec.primary_file,
            spec.score_field,
        )
        content = render_card(
            spec=spec,
            raw_path=raw_path,
            row_count=row_count,
            score_range=score_range,
            detected_encoding=detected_encoding,
            download_status=download_status.get(spec.key),
        )
        out_path = output_dir / f"{spec.key}.md"
        out_path.write_text(content, encoding="utf-8")
        generated.append(str(out_path))

    print(
        json.dumps(
            {
                "generated_cards": generated,
                "output_dir": str(output_dir),
                "count": len(generated),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
