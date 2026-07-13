#!/usr/bin/env python3
"""Build a consolidated fallacy-labeled corpus from cloned public sources.

Sources expected under:
- datasets/raw/fallacy/source_files/argotario
- datasets/raw/fallacy/source_files/logical-fallacy
- datasets/raw/fallacy/source_files/MAFALDA

Outputs:
- datasets/raw/fallacy/normalized/fallacy_corpus_v1.jsonl
- outputs/data_ingestion/fallacy_corpus_report.json
- outputs/data_ingestion/fallacy_corpus_report.md
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path


def normalize_ws(text: str) -> str:
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def slugify_label(label: str) -> str:
    cleaned = label.strip().lower()
    cleaned = cleaned.replace("&", " and ")
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def normalize_label_list(raw: Iterable[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        if not item:
            continue
        candidate = item.strip()
        if not candidate:
            continue
        if candidate in {"-", "none", "nothing", "nan", "unknown"}:
            continue
        lbl = slugify_label(candidate)
        if lbl and lbl not in out:
            out.append(lbl)
    return out


@dataclass
class Example:
    argument_text: str
    labels: list[str]
    source_dataset: str
    source_file: str
    metadata: dict


def load_logical_fallacy(repo_root: Path) -> list[Example]:
    examples: list[Example] = []
    data_dir = repo_root / "data"

    edu_all = data_dir / "edu_all.csv"
    if edu_all.exists():
        with edu_all.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                text = normalize_ws(row.get("source_article", ""))
                if not text:
                    continue
                labels = normalize_label_list(
                    [row.get("updated_label", ""), row.get("old_label", "")]
                )
                examples.append(
                    Example(
                        argument_text=text,
                        labels=labels,
                        source_dataset="logical_fallacy_edu",
                        source_file=str(edu_all),
                        metadata={
                            "row_index": i,
                            "original_url": row.get("original_url"),
                            "rationale": row.get("rationale"),
                        },
                    )
                )

    climate_all = data_dir / "climate_all.csv"
    if climate_all.exists():
        with climate_all.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                text = normalize_ws(row.get("source_article", ""))
                if not text:
                    continue
                raw_label = row.get("logical_fallacies", "")
                labels = normalize_label_list(
                    [x.strip() for x in raw_label.split(",") if x.strip()]
                )
                examples.append(
                    Example(
                        argument_text=text,
                        labels=labels,
                        source_dataset="logical_fallacy_climate",
                        source_file=str(climate_all),
                        metadata={
                            "row_index": i,
                            "original_url": row.get("original_url"),
                        },
                    )
                )
    return examples


def load_argotario(repo_root: Path) -> list[Example]:
    examples: list[Example] = []
    tsv_path = repo_root / "data" / "arguments-en-2018-01-15.tsv"
    if not tsv_path.exists():
        return examples

    with tsv_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        for i, row in enumerate(reader):
            text = normalize_ws(row.get("Text", ""))
            if not text:
                continue

            voted = row.get("Voted Fallacy", "")
            intended = row.get("Intended Fallacy", "")
            labels = normalize_label_list([voted, intended])

            examples.append(
                Example(
                    argument_text=text,
                    labels=labels,
                    source_dataset="argotario",
                    source_file=str(tsv_path),
                    metadata={
                        "row_index": i,
                        "topic": row.get("Topic"),
                        "stance": row.get("Stance"),
                        "votes": row.get("Number of Votes"),
                        "intended_fallacy": intended,
                        "voted_fallacy": voted,
                    },
                )
            )
    return examples


def load_mafalda(repo_root: Path) -> list[Example]:
    examples: list[Example] = []
    dataset_dir = repo_root / "datasets"
    for fname, ds_name in [
        ("gold_standard_dataset.jsonl", "mafalda_gold"),
        ("user_study_examples_with_labels.jsonl", "mafalda_user_study"),
    ]:
        path = dataset_dir / fname
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                text = normalize_ws(str(obj.get("text", "")))
                if not text:
                    continue

                labels_raw = []
                for ann in obj.get("labels", []):
                    if isinstance(ann, list) and len(ann) >= 3:
                        labels_raw.append(str(ann[2]))
                labels = normalize_label_list(labels_raw)

                examples.append(
                    Example(
                        argument_text=text,
                        labels=labels,
                        source_dataset=ds_name,
                        source_file=str(path),
                        metadata={
                            "row_index": i,
                            "annotation_count": len(obj.get("labels", [])),
                        },
                    )
                )
    return examples


def build_corpus(repo_root: Path, output_jsonl: Path, report_json: Path, report_md: Path) -> None:
    source_root = repo_root / "datasets" / "raw" / "fallacy" / "source_files"

    all_examples: list[Example] = []
    all_examples.extend(load_logical_fallacy(source_root / "logical-fallacy"))
    all_examples.extend(load_argotario(source_root / "argotario"))
    all_examples.extend(load_mafalda(source_root / "MAFALDA"))

    kept = []
    seen_text = set()

    source_counts = Counter()
    label_counts = Counter()
    dropped_no_text = 0
    dropped_duplicates = 0

    for ex in all_examples:
        text = normalize_ws(ex.argument_text)
        if not text:
            dropped_no_text += 1
            continue

        text_key = text.lower()
        if text_key in seen_text:
            dropped_duplicates += 1
            continue
        seen_text.add(text_key)

        labels = ex.labels
        primary = labels[0] if labels else None
        alternatives = labels[1:] if len(labels) > 1 else []

        example_id = f"public-fallacy-{len(kept) + 1:06d}"
        rec = {
            "example_id": example_id,
            "argument_text": text,
            "primary_fallacy_label": primary,
            "acceptable_alternative_labels": alternatives,
            "source_dataset": ex.source_dataset,
            "source_file": ex.source_file,
            "metadata": ex.metadata,
        }
        kept.append(rec)

        source_counts[ex.source_dataset] += 1
        if primary:
            label_counts[primary] += 1
        else:
            label_counts["none"] += 1

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8") as fh:
        for rec in kept:
            fh.write(json.dumps(rec, ensure_ascii=True) + "\n")

    sha256 = hashlib.sha256(output_jsonl.read_bytes()).hexdigest()

    report = {
        "output_jsonl": str(output_jsonl),
        "sha256": sha256,
        "total_input_examples": len(all_examples),
        "total_output_examples": len(kept),
        "dropped_no_text": dropped_no_text,
        "dropped_duplicates": dropped_duplicates,
        "source_counts": dict(source_counts),
        "top_25_labels": dict(label_counts.most_common(25)),
    }

    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# Fallacy Corpus Build Report",
        "",
        f"- Output: `{output_jsonl}`",
        f"- SHA256: `{sha256}`",
        f"- Total input examples: `{len(all_examples)}`",
        f"- Total output examples: `{len(kept)}`",
        f"- Dropped duplicates: `{dropped_duplicates}`",
        "",
        "## Source Counts",
        "",
    ]
    for k, v in source_counts.most_common():
        lines.append(f"- {k}: `{v}`")

    lines.extend(["", "## Top Labels", ""])
    for k, v in label_counts.most_common(25):
        lines.append(f"- {k}: `{v}`")

    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build consolidated fallacy corpus JSONL.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Repository root (default: current directory).",
    )
    parser.add_argument(
        "--output-jsonl",
        default="datasets/raw/fallacy/normalized/fallacy_corpus_v1.jsonl",
        help="Output JSONL path.",
    )
    parser.add_argument(
        "--report-json",
        default="outputs/data_ingestion/fallacy_corpus_report.json",
        help="Output report JSON path.",
    )
    parser.add_argument(
        "--report-md",
        default="outputs/data_ingestion/fallacy_corpus_report.md",
        help="Output report markdown path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    output_jsonl = (repo_root / args.output_jsonl).resolve()
    report_json = (repo_root / args.report_json).resolve()
    report_md = (repo_root / args.report_md).resolve()

    build_corpus(
        repo_root=repo_root,
        output_jsonl=output_jsonl,
        report_json=report_json,
        report_md=report_md,
    )

    print(output_jsonl)
    print(report_json)
    print(report_md)


if __name__ == "__main__":
    main()
