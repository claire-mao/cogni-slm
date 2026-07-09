"""Score dataset quality, filter by threshold, and report removed examples.

For each example, computes:
- length_score
- language_quality
- ocr_quality
- duplicate_probability
- missing_metadata_score
- readability
- estimated_usefulness
- overall_quality_score (0-100)

Outputs:
- scored JSONL (all examples with quality metrics)
- filtered JSONL (examples with overall score >= threshold)
- removed JSONL (examples below threshold, with removal reasons)
- markdown report summarizing removed examples
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

TEXT_FIELD_CANDIDATES = ("text", "essay", "argument_text", "student_response", "content")
LABEL_FIELD_CANDIDATES = ("label", "score", "rubric_score")
PROMPT_FIELD_CANDIDATES = ("prompt", "context", "task_prompt")

WORD_RE = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")
SENTENCE_END_RE = re.compile(r"[.!?]+")
NON_ALNUM_NONSPACE_RE = re.compile(r"[^\w\s]")
SYMBOL_RUN_RE = re.compile(r"[^\w\s]{3,}")
WEIRD_TOKEN_RE = re.compile(r"[A-Za-z]*[0-9]+[A-Za-z]+|[A-Za-z]{1,2}[|\\/_]{1,}[A-Za-z]{1,2}")


@dataclass(frozen=True)
class QualityScores:
    """Per-example quality signals."""

    length_score: float
    language_quality: float
    ocr_quality: float
    duplicate_probability: float
    missing_metadata_score: float
    readability: float
    estimated_usefulness: float
    overall_quality_score: float


@dataclass(frozen=True)
class RemovalDecision:
    """Represents one filtered-out record."""

    record_id: str
    source: str
    overall_quality_score: float
    reasons: list[str]


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Score dataset quality and filter low-quality examples."
    )
    parser.add_argument(
        "--input-jsonl",
        default="datasets/final/merged_all.jsonl",
        help="Input dataset JSONL.",
    )
    parser.add_argument(
        "--scored-output",
        default="datasets/final/quality_scored.jsonl",
        help="Output JSONL path with per-example quality scores.",
    )
    parser.add_argument(
        "--filtered-output",
        default="datasets/final/quality_filtered.jsonl",
        help="Output JSONL path with examples above threshold.",
    )
    parser.add_argument(
        "--removed-output",
        default="datasets/final/quality_removed.jsonl",
        help="Output JSONL path with removed examples.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/final_dataset_quality.md",
        help="Markdown report path for summary of removed examples.",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=60.0,
        help="Minimum overall quality score required to keep an example.",
    )
    parser.add_argument(
        "--optimal-min-words",
        type=int,
        default=120,
        help="Minimum preferred length in words.",
    )
    parser.add_argument(
        "--optimal-max-words",
        type=int,
        default=1200,
        help="Maximum preferred length in words.",
    )
    parser.add_argument(
        "--required-metadata-keys",
        default="source_split,source_row_index",
        help="Comma-separated metadata keys expected for completeness.",
    )
    parser.add_argument(
        "--sample-removed",
        type=int,
        default=20,
        help="How many removed examples to list in the report.",
    )
    return parser.parse_args()


def clamp(value: float, low: float, high: float) -> float:
    """Clamp value into [low, high]."""
    return max(low, min(high, value))


def first_non_empty(mapping: dict[str, Any], candidates: tuple[str, ...]) -> str:
    """Get first non-empty field value as string."""
    for key in candidates:
        if key in mapping:
            value = str(mapping.get(key, "")).strip()
            if value:
                return value
    return ""


def normalize_text(text: str) -> str:
    """Collapse whitespace for stable comparisons."""
    return " ".join(text.split())


def tokenize_words(text: str) -> list[str]:
    """Tokenize alphabetic words."""
    return WORD_RE.findall(text)


def count_syllables(word: str) -> int:
    """Heuristic syllable counter for readability scoring."""
    w = word.lower().strip()
    if not w:
        return 0

    vowels = "aeiouy"
    syllables = 0
    prev_vowel = False
    for char in w:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            syllables += 1
        prev_vowel = is_vowel

    if w.endswith("e") and syllables > 1:
        syllables -= 1

    return max(1, syllables)


def compute_length_score(word_count: int, optimal_min_words: int, optimal_max_words: int) -> float:
    """Score text length from 0 to 100 with a preferred range."""
    if word_count <= 0:
        return 0.0

    if word_count < optimal_min_words:
        return clamp((word_count / optimal_min_words) * 100.0, 0.0, 100.0)

    if word_count <= optimal_max_words:
        return 100.0

    overflow = word_count - optimal_max_words
    penalty = (overflow / optimal_max_words) * 70.0
    return clamp(100.0 - penalty, 0.0, 100.0)


def compute_language_quality(text: str, words: list[str]) -> float:
    """Heuristic language quality signal."""
    if not text:
        return 0.0

    length = len(text)
    alpha_chars = sum(1 for char in text if char.isalpha())
    alpha_ratio = alpha_chars / max(1, length)

    unique_ratio = len({word.lower() for word in words}) / max(1, len(words))
    unique_score = clamp(((unique_ratio - 0.2) / 0.6) * 100.0, 0.0, 100.0)

    symbol_ratio = len(NON_ALNUM_NONSPACE_RE.findall(text)) / max(1, length)
    symbol_score = clamp((1.0 - (symbol_ratio * 8.0)) * 100.0, 0.0, 100.0)

    sentence_count = max(1, len(SENTENCE_END_RE.findall(text)))
    words_per_sentence = len(words) / sentence_count if words else 0.0
    sentence_score = clamp(100.0 - abs(words_per_sentence - 20.0) * 3.0, 0.0, 100.0)

    alpha_score = clamp(alpha_ratio * 125.0, 0.0, 100.0)

    return clamp(
        0.35 * alpha_score + 0.25 * unique_score + 0.20 * symbol_score + 0.20 * sentence_score,
        0.0,
        100.0,
    )


def compute_ocr_quality(text: str, words: list[str]) -> float:
    """Estimate OCR cleanliness, where 100 means low artifact risk."""
    if not text:
        return 0.0

    replacement_chars = text.count("\ufffd")
    replacement_ratio = replacement_chars / max(1, len(text))

    single_char_tokens = sum(1 for token in words if len(token) == 1)
    single_char_ratio = single_char_tokens / max(1, len(words))

    symbol_runs = len(SYMBOL_RUN_RE.findall(text))
    symbol_run_ratio = symbol_runs / max(1, len(words) // 50 + 1)

    weird_tokens = len(WEIRD_TOKEN_RE.findall(text))
    weird_ratio = weird_tokens / max(1, len(words))

    penalty = (
        replacement_ratio * 4000.0
        + single_char_ratio * 120.0
        + symbol_run_ratio * 20.0
        + weird_ratio * 220.0
    )
    return clamp(100.0 - penalty, 0.0, 100.0)


def compute_readability(text: str, words: list[str]) -> float:
    """Compute normalized readability score (0-100) using Flesch Reading Ease."""
    if not text or not words:
        return 0.0

    sentence_count = max(1, len(SENTENCE_END_RE.findall(text)))
    syllable_count = sum(count_syllables(word) for word in words)

    flesch = 206.835 - 1.015 * (len(words) / sentence_count) - 84.6 * (syllable_count / len(words))
    return clamp(flesch, 0.0, 100.0)


def compute_metadata_score(
    metadata: dict[str, Any],
    required_keys: list[str],
) -> tuple[float, list[str]]:
    """Compute metadata completeness score and list of missing required keys."""
    if not isinstance(metadata, dict) or not metadata:
        return 0.0, [key for key in required_keys if key]

    required = [key for key in required_keys if key]
    missing_fields: list[str] = []
    if required:
        required_present = 0
        for key in required:
            if str(metadata.get(key, "")).strip():
                required_present += 1
            else:
                missing_fields.append(key)
        required_ratio = required_present / len(required)
    else:
        required_ratio = 1.0

    non_empty_values = sum(1 for value in metadata.values() if str(value).strip())
    non_empty_ratio = non_empty_values / max(1, len(metadata))

    score = clamp((0.7 * required_ratio + 0.3 * non_empty_ratio) * 100.0, 0.0, 100.0)
    return score, missing_fields


def compute_estimated_usefulness(
    *,
    length_score: float,
    language_quality: float,
    ocr_quality: float,
    metadata_score: float,
    readability: float,
    has_label: bool,
    has_prompt: bool,
) -> float:
    """Estimate downstream training usefulness."""
    score = (
        0.30 * length_score
        + 0.30 * language_quality
        + 0.15 * ocr_quality
        + 0.15 * metadata_score
        + 0.10 * readability
    )
    if has_label:
        score += 8.0
    else:
        score -= 20.0
    if has_prompt:
        score += 4.0
    return clamp(score, 0.0, 100.0)


def simhash(tokens: list[str], bits: int = 64) -> int:
    """Compute a simple token-based simhash signature."""
    if not tokens:
        return 0

    vector = [0] * bits
    counts = Counter(token.lower() for token in tokens)

    for token, weight in counts.items():
        digest = hashlib.md5(token.encode("utf-8")).digest()
        value = int.from_bytes(digest[:8], byteorder="big", signed=False)
        for idx in range(bits):
            bit = 1 if (value >> idx) & 1 else -1
            vector[idx] += bit * weight

    signature = 0
    for idx, value in enumerate(vector):
        if value >= 0:
            signature |= 1 << idx
    return signature


def compute_duplicate_probabilities(texts: list[str]) -> list[float]:
    """Estimate duplicate probability using exact hashes plus simhash locality."""
    normalized = [normalize_text(text).lower() for text in texts]
    hash_counts = Counter(hashlib.sha256(text.encode("utf-8")).hexdigest() for text in normalized)

    signatures: list[int] = []
    for text in normalized:
        tokens = tokenize_words(text)
        signatures.append(simhash(tokens))

    min_distance = [64] * len(signatures)
    buckets: dict[int, list[int]] = defaultdict(list)

    for idx, signature in enumerate(signatures):
        bucket = signature >> 48
        for other_idx in buckets[bucket]:
            distance = (signature ^ signatures[other_idx]).bit_count()
            if distance < min_distance[idx]:
                min_distance[idx] = distance
            if distance < min_distance[other_idx]:
                min_distance[other_idx] = distance
        buckets[bucket].append(idx)

    probabilities: list[float] = []
    for idx, text in enumerate(normalized):
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if hash_counts[text_hash] > 1:
            probabilities.append(1.0)
            continue

        distance = min_distance[idx]
        if distance <= 3:
            probabilities.append(0.85)
        elif distance <= 6:
            probabilities.append(0.65)
        elif distance <= 10:
            probabilities.append(0.35)
        else:
            probabilities.append(0.05)

    return probabilities


def compute_overall_quality(scores: QualityScores) -> float:
    """Weighted overall quality score (0-100)."""
    duplicate_cleanliness = (1.0 - scores.duplicate_probability) * 100.0
    value = (
        0.16 * scores.length_score
        + 0.20 * scores.language_quality
        + 0.14 * scores.ocr_quality
        + 0.18 * duplicate_cleanliness
        + 0.10 * scores.missing_metadata_score
        + 0.10 * scores.readability
        + 0.12 * scores.estimated_usefulness
    )
    return clamp(value, 0.0, 100.0)


def quality_reasons(scores: QualityScores) -> list[str]:
    """Generate explainable reasons for low-quality removals."""
    reasons: list[tuple[str, float]] = [
        ("low_length", scores.length_score),
        ("low_language_quality", scores.language_quality),
        ("low_ocr_quality", scores.ocr_quality),
        ("low_metadata_completeness", scores.missing_metadata_score),
        ("low_readability", scores.readability),
        ("low_usefulness", scores.estimated_usefulness),
    ]

    if scores.duplicate_probability >= 0.65:
        reasons.append(("high_duplicate_probability", (1.0 - scores.duplicate_probability) * 100.0))

    reasons_sorted = sorted(reasons, key=lambda item: item[1])
    return [reason for reason, _score in reasons_sorted[:2]]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records."""
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"Line {line_number} is not a JSON object.")
            records.append(payload)
    return records


def score_records(
    records: list[dict[str, Any]],
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], list[RemovalDecision]]:
    """Score all records and return enriched records + removal decisions."""
    required_metadata_keys = [
        key.strip() for key in args.required_metadata_keys.split(",") if key.strip()
    ]

    texts = [normalize_text(first_non_empty(record, TEXT_FIELD_CANDIDATES)) for record in records]
    duplicate_probabilities = compute_duplicate_probabilities(texts)

    enriched: list[dict[str, Any]] = []
    removed: list[RemovalDecision] = []

    for index, record in enumerate(records):
        text = texts[index]
        words = tokenize_words(text)
        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}

        label_value = first_non_empty(record, LABEL_FIELD_CANDIDATES)
        prompt_value = first_non_empty(record, PROMPT_FIELD_CANDIDATES)

        length_score = compute_length_score(
            word_count=len(words),
            optimal_min_words=args.optimal_min_words,
            optimal_max_words=args.optimal_max_words,
        )
        language_quality = compute_language_quality(text, words)
        ocr_quality = compute_ocr_quality(text, words)
        duplicate_probability = duplicate_probabilities[index]
        metadata_score, missing_metadata_fields = compute_metadata_score(
            metadata,
            required_metadata_keys,
        )
        readability = compute_readability(text, words)
        estimated_usefulness = compute_estimated_usefulness(
            length_score=length_score,
            language_quality=language_quality,
            ocr_quality=ocr_quality,
            metadata_score=metadata_score,
            readability=readability,
            has_label=bool(label_value),
            has_prompt=bool(prompt_value),
        )

        provisional = QualityScores(
            length_score=length_score,
            language_quality=language_quality,
            ocr_quality=ocr_quality,
            duplicate_probability=duplicate_probability,
            missing_metadata_score=metadata_score,
            readability=readability,
            estimated_usefulness=estimated_usefulness,
            overall_quality_score=0.0,
        )
        overall = compute_overall_quality(provisional)
        scores = QualityScores(
            length_score=provisional.length_score,
            language_quality=provisional.language_quality,
            ocr_quality=provisional.ocr_quality,
            duplicate_probability=provisional.duplicate_probability,
            missing_metadata_score=provisional.missing_metadata_score,
            readability=provisional.readability,
            estimated_usefulness=provisional.estimated_usefulness,
            overall_quality_score=overall,
        )

        enriched_record = dict(record)
        enriched_record["quality"] = {
            "length_score": round(scores.length_score, 3),
            "language_quality": round(scores.language_quality, 3),
            "ocr_quality": round(scores.ocr_quality, 3),
            "duplicate_probability": round(scores.duplicate_probability, 4),
            "missing_metadata_score": round(scores.missing_metadata_score, 3),
            "missing_metadata_count": len(missing_metadata_fields),
            "missing_metadata_fields": missing_metadata_fields,
            "readability": round(scores.readability, 3),
            "estimated_usefulness": round(scores.estimated_usefulness, 3),
            "overall_quality_score": round(scores.overall_quality_score, 3),
        }

        if scores.overall_quality_score < args.threshold:
            reasons = quality_reasons(scores)
            enriched_record["quality"]["removal_reasons"] = reasons
            removed.append(
                RemovalDecision(
                    record_id=str(record.get("id", f"idx_{index}")),
                    source=str(record.get("source", "unknown")),
                    overall_quality_score=scores.overall_quality_score,
                    reasons=reasons,
                )
            )

        enriched.append(enriched_record)

    return enriched, removed


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    """Write JSONL records."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def render_report(
    *,
    threshold: float,
    total: int,
    kept: int,
    removed: int,
    removed_decisions: list[RemovalDecision],
    scored_records: list[dict[str, Any]],
    sample_removed: int,
) -> str:
    """Render markdown report summarizing removed examples."""
    removed_scores = [
        float(record["quality"]["overall_quality_score"])
        for record in scored_records
        if float(record["quality"]["overall_quality_score"]) < threshold
    ]
    kept_scores = [
        float(record["quality"]["overall_quality_score"])
        for record in scored_records
        if float(record["quality"]["overall_quality_score"]) >= threshold
    ]

    reason_counts: Counter[str] = Counter()
    for decision in removed_decisions:
        reason_counts.update(decision.reasons)

    metric_keys = (
        "length_score",
        "language_quality",
        "ocr_quality",
        "duplicate_probability",
        "missing_metadata_score",
        "missing_metadata_count",
        "readability",
        "estimated_usefulness",
        "overall_quality_score",
    )
    metric_avgs: dict[str, float] = {}
    for key in metric_keys:
        values = [float(record["quality"][key]) for record in scored_records]
        metric_avgs[key] = mean(values) if values else 0.0

    lines = [
        "# Dataset Quality Scoring Report",
        "",
        f"- Total examples scored: `{total}`",
        f"- Threshold: `{threshold:.2f}`",
        f"- Kept: `{kept}`",
        f"- Removed: `{removed}`",
        f"- Keep rate: `{(kept / total * 100.0) if total else 0.0:.2f}%`",
        "",
        "## Quality Score Summary",
        "",
        f"- Average overall score (all): `{metric_avgs['overall_quality_score']:.2f}`",
        f"- Average overall score (kept): `{mean(kept_scores) if kept_scores else 0.0:.2f}`",
        (
            f"- Average overall score (removed): "
            f"`{mean(removed_scores) if removed_scores else 0.0:.2f}`"
        ),
        "",
        "## Metric Averages",
        "",
        "| metric | average |",
        "|---|---:|",
    ]

    for key in metric_keys:
        lines.append(f"| {key} | {metric_avgs[key]:.3f} |")

    lines.extend(["", "## Removal Reasons", "", "| reason | count |", "|---|---:|"])
    if reason_counts:
        for reason, count in reason_counts.most_common():
            lines.append(f"| {reason} | {count} |")
    else:
        lines.append("| none | 0 |")

    lines.extend(["", "## Removed Examples (sample)", ""])
    if removed_decisions:
        for decision in removed_decisions[:sample_removed]:
            lines.append(
                "- "
                f"`{decision.record_id}` "
                f"source=`{decision.source}` "
                f"score=`{decision.overall_quality_score:.2f}` "
                f"reasons={decision.reasons}"
            )
        remaining = len(removed_decisions) - min(sample_removed, len(removed_decisions))
        if remaining > 0:
            lines.append(f"- ... {remaining} additional removed examples omitted.")
    else:
        lines.append("- None")

    return "\n".join(lines)


def main() -> None:
    """Run quality scoring pipeline."""
    args = parse_args()
    input_jsonl = Path(args.input_jsonl)
    scored_output = Path(args.scored_output)
    filtered_output = Path(args.filtered_output)
    removed_output = Path(args.removed_output)
    report_path = Path(args.report_path)

    scored_output.parent.mkdir(parents=True, exist_ok=True)
    filtered_output.parent.mkdir(parents=True, exist_ok=True)
    removed_output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_jsonl(input_jsonl)
    scored_records, removed_decisions = score_records(records, args)

    kept_records = [
        record
        for record in scored_records
        if float(record["quality"]["overall_quality_score"]) >= args.threshold
    ]
    removed_records = [
        record
        for record in scored_records
        if float(record["quality"]["overall_quality_score"]) < args.threshold
    ]

    write_jsonl(scored_records, scored_output)
    write_jsonl(kept_records, filtered_output)
    write_jsonl(removed_records, removed_output)

    report = render_report(
        threshold=args.threshold,
        total=len(scored_records),
        kept=len(kept_records),
        removed=len(removed_records),
        removed_decisions=removed_decisions,
        scored_records=scored_records,
        sample_removed=args.sample_removed,
    )
    report_path.write_text(report, encoding="utf-8")

    print(
        json.dumps(
            {
                "input_jsonl": str(input_jsonl),
                "scored_output": str(scored_output),
                "filtered_output": str(filtered_output),
                "removed_output": str(removed_output),
                "report_path": str(report_path),
                "total": len(scored_records),
                "kept": len(kept_records),
                "removed": len(removed_records),
                "threshold": args.threshold,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
