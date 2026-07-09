"""Compute score statistics and distribution diagnostics for unified datasets.

Outputs a markdown report with:
- per-dataset minimum, maximum, mean, median, standard deviation
- score distribution histograms
- missing score range analysis
- skewness analysis
- class imbalance analysis
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any

MAX_BAR_WIDTH = 28


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Analyze score distributions across datasets.")
    parser.add_argument(
        "--mapping-report",
        default="docs/reports/schema_mapping.md",
        help="Schema mapping report used to discover unified dataset files.",
    )
    parser.add_argument(
        "--fallback-dir",
        default="datasets/processed/unified",
        help="Fallback directory when mapping report is missing/unreadable.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/score_analysis.md",
        help="Output markdown report path.",
    )
    return parser.parse_args()


def discover_datasets(mapping_report: Path, fallback_dir: Path) -> list[Path]:
    """Discover per-dataset unified JSONL files."""
    dataset_paths: list[Path] = []

    if mapping_report.exists():
        for line in mapping_report.read_text(encoding="utf-8").splitlines():
            marker = "- Unified output: `"
            if marker not in line:
                continue
            start = line.find(marker) + len(marker)
            end = line.find("`", start)
            if end == -1:
                continue
            path = Path(line[start:end])
            if path.exists():
                dataset_paths.append(path)

    if dataset_paths:
        deduped: list[Path] = []
        seen: set[str] = set()
        for path in dataset_paths:
            key = str(path.resolve())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(path)
        return deduped

    if not fallback_dir.exists():
        return []

    files = sorted(path for path in fallback_dir.glob("*.jsonl") if path.is_file())
    return [path for path in files if path.name != "unified_all.jsonl"]


def parse_score(value: Any) -> float | None:
    """Parse numeric score value."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        numeric = float(value)
        if math.isfinite(numeric):
            return numeric
        return None

    raw = str(value).strip()
    if not raw:
        return None
    try:
        numeric = float(raw)
    except ValueError:
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def is_integer_like(values: list[float]) -> bool:
    """Check if all values are effectively integers."""
    return all(abs(value - round(value)) < 1e-9 for value in values)


def skewness(values: list[float], values_mean: float, values_std: float) -> float:
    """Compute population skewness."""
    if not values or values_std <= 0:
        return 0.0
    centered = [(value - values_mean) / values_std for value in values]
    return sum(item**3 for item in centered) / len(centered)


def bar(count: int, peak: int) -> str:
    """Render histogram bar."""
    if peak <= 0 or count <= 0:
        return ""
    width = max(1, round((count / peak) * MAX_BAR_WIDTH))
    return "#" * width


def discrete_histogram(values: list[float]) -> tuple[list[str], list[int], list[int]]:
    """Return histogram rows for integer-like labels."""
    ints = [int(round(value)) for value in values]
    counts = Counter(ints)
    labels = sorted(counts.keys())
    peak = max(counts.values()) if counts else 0

    rows: list[str] = []
    for label in labels:
        count = counts[label]
        rows.append(f"{label:>4}: {count:>6} {bar(count, peak)}")

    return rows, labels, [counts[label] for label in labels]


def binned_histogram(
    values: list[float],
    bins: int = 10,
) -> tuple[list[str], list[tuple[float, float]], list[int]]:
    """Return histogram rows for continuous values."""
    if not values:
        return [], [], []

    vmin = min(values)
    vmax = max(values)
    if math.isclose(vmin, vmax):
        label = f"[{vmin:.3f}, {vmax:.3f}]"
        return (
            [f"{label:<24} {len(values):>6} {bar(len(values), len(values))}"],
            [(vmin, vmax)],
            [len(values)],
        )

    width = (vmax - vmin) / bins
    ranges: list[tuple[float, float]] = []
    counts = [0 for _ in range(bins)]

    for idx in range(bins):
        low = vmin + idx * width
        high = vmin + (idx + 1) * width
        ranges.append((low, high))

    for value in values:
        idx = int((value - vmin) / width)
        if idx >= bins:
            idx = bins - 1
        if idx < 0:
            idx = 0
        counts[idx] += 1

    peak = max(counts) if counts else 0
    rows: list[str] = []
    for (low, high), count in zip(ranges, counts, strict=True):
        label = f"[{low:.3f}, {high:.3f})"
        rows.append(f"{label:<24} {count:>6} {bar(count, peak)}")

    return rows, ranges, counts


def assess_missing_ranges(values: list[float]) -> str:
    """Identify missing score ranges."""
    if not values:
        return "No numeric scores."

    if is_integer_like(values):
        labels = sorted({int(round(value)) for value in values})
        lo = min(labels)
        hi = max(labels)
        missing = [score for score in range(lo, hi + 1) if score not in labels]
        if not missing:
            return f"No missing integer scores in [{lo}, {hi}]."

        ranges: list[tuple[int, int]] = []
        start = missing[0]
        prev = missing[0]
        for score in missing[1:]:
            if score == prev + 1:
                prev = score
                continue
            ranges.append((start, prev))
            start = score
            prev = score
        ranges.append((start, prev))

        chunks = [f"{start}" if start == end else f"{start}-{end}" for start, end in ranges]
        return f"Missing integer ranges within [{lo}, {hi}]: {', '.join(chunks)}"

    _rows, ranges, counts = binned_histogram(values)
    empty_ranges = [ranges[idx] for idx, count in enumerate(counts) if count == 0]
    if not empty_ranges:
        return "No empty score bins in 10-bin range partition."

    preview = ", ".join(f"[{low:.3f}, {high:.3f})" for low, high in empty_ranges[:6])
    if len(empty_ranges) > 6:
        preview += f", ... ({len(empty_ranges)} empty bins total)"
    return f"Empty score ranges (10-bin): {preview}"


def assess_skew(values: list[float]) -> tuple[float, str]:
    """Assess skewness and return interpretation."""
    if not values:
        return 0.0, "No numeric scores."
    if len(values) < 3:
        return 0.0, "Insufficient samples (<3)."

    values_mean = mean(values)
    values_std = stdev(values) if len(values) > 1 else 0.0
    if values_std <= 0:
        return 0.0, "No variance (all scores identical)."

    sk = skewness(values, values_mean, values_std)
    if sk > 0.75:
        label = "Right-skewed"
    elif sk < -0.75:
        label = "Left-skewed"
    else:
        label = "Approximately symmetric"

    return sk, f"{label} (skewness={sk:.3f})."


def assess_imbalance(values: list[float]) -> str:
    """Assess class/bin imbalance severity."""
    if not values:
        return "No numeric scores."

    if is_integer_like(values):
        labels = [int(round(value)) for value in values]
        counts = Counter(labels)
        peak = max(counts.values())
        low = min(counts.values())
        majority_share = peak / len(labels)
        ratio = peak / max(1, low)

        if majority_share >= 0.5 or ratio >= 10:
            level = "Severe"
        elif majority_share >= 0.35 or ratio >= 5:
            level = "Moderate"
        else:
            level = "Low"

        return (
            f"{level} imbalance (majority_share={majority_share:.3f}, "
            f"max/min_count_ratio={ratio:.2f})."
        )

    _rows, _ranges, counts = binned_histogram(values)
    nonzero = [count for count in counts if count > 0]
    if not nonzero:
        return "No numeric scores."

    peak = max(nonzero)
    low = min(nonzero)
    ratio = peak / max(1, low)
    majority_share = peak / max(1, len(values))

    if majority_share >= 0.5 or ratio >= 10:
        level = "Severe"
    elif majority_share >= 0.35 or ratio >= 5:
        level = "Moderate"
    else:
        level = "Low"

    return (
        f"{level} bin imbalance (peak_bin_share={majority_share:.3f}, "
        f"max/min_nonzero_bin_ratio={ratio:.2f})."
    )


def analyze_dataset(path: Path) -> dict[str, Any]:
    """Analyze one dataset JSONL file."""
    total_rows = 0
    score_values: list[float] = []
    missing_scores = 0
    parse_errors = 0

    with path.open("r", encoding="utf-8") as handle:
        for _line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                parse_errors += 1
                continue

            if not isinstance(row, dict):
                parse_errors += 1
                continue

            total_rows += 1
            score = parse_score(row.get("score"))
            if score is None:
                missing_scores += 1
                continue
            score_values.append(score)

    if score_values:
        values_min = min(score_values)
        values_max = max(score_values)
        values_mean = mean(score_values)
        values_median = median(score_values)
        values_std = stdev(score_values) if len(score_values) > 1 else 0.0
    else:
        values_min = None
        values_max = None
        values_mean = None
        values_median = None
        values_std = None

    skew_value, skew_note = assess_skew(score_values)
    imbalance_note = assess_imbalance(score_values)
    missing_ranges_note = assess_missing_ranges(score_values)

    if score_values and is_integer_like(score_values):
        hist_rows, _labels, _counts = discrete_histogram(score_values)
    else:
        hist_rows, _ranges, _counts = binned_histogram(score_values)

    return {
        "dataset": str(path),
        "rows": total_rows,
        "scores": len(score_values),
        "missing_scores": missing_scores,
        "parse_errors": parse_errors,
        "min": values_min,
        "max": values_max,
        "mean": values_mean,
        "median": values_median,
        "std": values_std,
        "skew": skew_value,
        "skew_note": skew_note,
        "imbalance_note": imbalance_note,
        "missing_ranges_note": missing_ranges_note,
        "hist_rows": hist_rows,
    }


def fmt(value: float | None) -> str:
    """Format optional float for report tables."""
    if value is None:
        return "N/A"
    return f"{value:.4f}"


def render_report(results: list[dict[str, Any]], source_list: list[Path]) -> str:
    """Render markdown score analysis report."""
    flagged_skew = [
        result for result in results if result["scores"] > 2 and abs(result["skew"]) > 0.75
    ]
    flagged_imbalance = [
        result
        for result in results
        if "Severe" in result["imbalance_note"] or "Moderate" in result["imbalance_note"]
    ]

    lines = [
        "# Score Analysis",
        "",
        f"- Datasets discovered: `{len(source_list)}`",
        f"- Datasets analyzed: `{len(results)}`",
        f"- Skew-flagged datasets: `{len(flagged_skew)}`",
        f"- Imbalance-flagged datasets: `{len(flagged_imbalance)}`",
        "",
        "## Summary Table",
        "",
        "| Dataset | Rows | Scored | Missing score | Min | Max | Mean | Median | Std Dev |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for result in results:
        lines.append(
            "| "
            f"`{result['dataset']}` | "
            f"{result['rows']} | "
            f"{result['scores']} | "
            f"{result['missing_scores']} | "
            f"{fmt(result['min'])} | "
            f"{fmt(result['max'])} | "
            f"{fmt(result['mean'])} | "
            f"{fmt(result['median'])} | "
            f"{fmt(result['std'])} |"
        )

    lines.extend(["", "## Per-Dataset Details", ""])

    for result in results:
        lines.append(f"### {result['dataset']}")
        lines.append("")
        lines.append(f"- Minimum score: `{fmt(result['min'])}`")
        lines.append(f"- Maximum score: `{fmt(result['max'])}`")
        lines.append(f"- Mean: `{fmt(result['mean'])}`")
        lines.append(f"- Median: `{fmt(result['median'])}`")
        lines.append(f"- Standard deviation: `{fmt(result['std'])}`")
        lines.append(f"- Missing score ranges: {result['missing_ranges_note']}")
        lines.append(f"- Skew analysis: {result['skew_note']}")
        lines.append(f"- Class imbalance: {result['imbalance_note']}")
        lines.append("")
        lines.append("Histogram:")
        lines.append("")
        if result["hist_rows"]:
            lines.append("```text")
            lines.extend(result["hist_rows"])
            lines.append("```")
        else:
            lines.append("- No numeric score histogram available.")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    """Run score analysis pipeline."""
    args = parse_args()
    mapping_report = Path(args.mapping_report)
    fallback_dir = Path(args.fallback_dir)
    report_path = Path(args.report_path)

    report_path.parent.mkdir(parents=True, exist_ok=True)

    datasets = discover_datasets(mapping_report, fallback_dir)
    results = [analyze_dataset(path) for path in datasets]

    report = render_report(results, datasets)
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "datasets": len(datasets),
                "report_path": str(report_path),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
