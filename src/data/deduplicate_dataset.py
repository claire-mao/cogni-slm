"""Deduplicate filtered dataset records with exact and near-duplicate checks."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class DuplicatePair:
    """Duplicate pair metadata."""

    left_id: str
    right_id: str
    similarity: float
    method: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deduplicate training dataset records.")
    parser.add_argument(
        "--input-jsonl",
        default="datasets/processed/training_dataset.filtered.jsonl",
        help="Input JSONL path from filtering stage.",
    )
    parser.add_argument(
        "--output-jsonl",
        default="datasets/processed/training_dataset.deduped.jsonl",
        help="Output JSONL after deduplication.",
    )
    parser.add_argument(
        "--duplicate-report",
        default="duplicate_report.json",
        help="Duplicate report JSON output path.",
    )
    parser.add_argument(
        "--near-threshold",
        type=float,
        default=0.95,
        help="Near-duplicate threshold for similarity.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    return " ".join(text.lower().split())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict):
            records.append(payload)
    return records


def detect_exact_duplicates(records: list[dict[str, Any]]) -> tuple[set[str], dict[str, list[str]]]:
    """Return duplicate IDs to remove and groups keyed by essay hash."""
    by_hash: dict[str, list[str]] = {}
    duplicate_ids: set[str] = set()

    for record in records:
        record_id = str(record.get("id", ""))
        essay = normalize_text(str(record.get("essay", "")))
        essay_hash = hashlib.sha256(essay.encode("utf-8")).hexdigest()
        by_hash.setdefault(essay_hash, []).append(record_id)

    for ids in by_hash.values():
        if len(ids) > 1:
            for duplicate_id in ids[1:]:
                duplicate_ids.add(duplicate_id)

    exact_groups = {key: ids for key, ids in by_hash.items() if len(ids) > 1}
    return duplicate_ids, exact_groups


def near_duplicate_pairs_with_embeddings(
    records: list[dict[str, Any]],
    threshold: float,
) -> tuple[list[DuplicatePair], bool]:
    """Try sentence-embedding duplicate detection. Returns (pairs, available)."""
    try:
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
    except Exception:
        return [], False

    essays = [normalize_text(str(record.get("essay", ""))) for record in records]
    ids = [str(record.get("id", "")) for record in records]
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode(essays, show_progress_bar=False)
    sim_matrix = cosine_similarity(embeddings)

    pairs: list[DuplicatePair] = []
    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sim = float(sim_matrix[i][j])
            if sim >= threshold:
                pairs.append(
                    DuplicatePair(
                        left_id=ids[i],
                        right_id=ids[j],
                        similarity=sim,
                        method="embedding_cosine",
                    )
                )
    return pairs, True


def near_duplicate_pairs_with_text(
    records: list[dict[str, Any]],
    threshold: float,
) -> list[DuplicatePair]:
    """Fallback near-duplicate detection using text similarity."""
    pairs: list[DuplicatePair] = []
    normalized = [normalize_text(str(record.get("essay", ""))) for record in records]
    ids = [str(record.get("id", "")) for record in records]

    for i in range(len(records)):
        for j in range(i + 1, len(records)):
            sim = SequenceMatcher(None, normalized[i], normalized[j]).ratio()
            if sim >= threshold:
                pairs.append(
                    DuplicatePair(
                        left_id=ids[i],
                        right_id=ids[j],
                        similarity=float(sim),
                        method="text_similarity",
                    )
                )
    return pairs


def main() -> None:
    args = parse_args()
    input_jsonl = Path(args.input_jsonl)
    output_jsonl = Path(args.output_jsonl)
    report_path = Path(args.duplicate_report)

    records = load_jsonl(input_jsonl)
    if not records:
        output_jsonl.parent.mkdir(parents=True, exist_ok=True)
        output_jsonl.write_text("", encoding="utf-8")
        report_path.write_text(
            json.dumps(
                {
                    "input_jsonl": str(input_jsonl),
                    "output_jsonl": str(output_jsonl),
                    "total_records": 0,
                    "kept_records": 0,
                    "removed_records": 0,
                    "exact_duplicate_groups": {},
                    "near_duplicates": [],
                    "embedding_available": False,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"duplicate_report={report_path}")
        return

    exact_duplicate_ids, exact_groups = detect_exact_duplicates(records)

    near_pairs, embedding_available = near_duplicate_pairs_with_embeddings(
        records,
        threshold=args.near_threshold,
    )
    if not embedding_available:
        near_pairs = near_duplicate_pairs_with_text(records, threshold=args.near_threshold)

    remove_ids = set(exact_duplicate_ids)
    for pair in near_pairs:
        remove_ids.add(pair.right_id)

    kept_records = [record for record in records if str(record.get("id", "")) not in remove_ids]

    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8") as handle:
        for record in kept_records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")

    report = {
        "input_jsonl": str(input_jsonl),
        "output_jsonl": str(output_jsonl),
        "total_records": len(records),
        "kept_records": len(kept_records),
        "removed_records": len(records) - len(kept_records),
        "exact_duplicate_groups": exact_groups,
        "near_duplicates": [
            {
                "left_id": pair.left_id,
                "right_id": pair.right_id,
                "similarity": pair.similarity,
                "method": pair.method,
            }
            for pair in near_pairs
        ],
        "embedding_available": embedding_available,
        "near_threshold": args.near_threshold,
    }
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"deduped_jsonl={output_jsonl}")
    print(f"duplicate_report={report_path}")


if __name__ == "__main__":
    main()
