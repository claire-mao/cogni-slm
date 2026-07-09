"""Detect semantic near-duplicates using MinHash, SimHash, and sentence embeddings.

This script is non-destructive: it does not remove data automatically.
It generates recommendations only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TOKEN_RE = re.compile(r"[A-Za-z0-9']+")
MERSENNE_61 = (1 << 61) - 1


@dataclass(frozen=True)
class Record:
    """Normalized record used for duplicate analysis."""

    index: int
    record_id: str
    split: str
    source: str
    score: float | None
    text: str


@dataclass(frozen=True)
class PairScore:
    """Pairwise similarity signals across all three methods."""

    left_index: int
    right_index: int
    minhash_similarity: float
    simhash_hamming: int
    embedding_cosine: float


class UnionFind:
    """Union-find for duplicate cluster construction."""

    def __init__(self, n: int) -> None:
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, value: int) -> int:
        """Find representative with path compression."""
        if self.parent[value] != value:
            self.parent[value] = self.find(self.parent[value])
        return self.parent[value]

    def union(self, left: int, right: int) -> None:
        """Union by rank."""
        left_root = self.find(left)
        right_root = self.find(right)
        if left_root == right_root:
            return

        if self.rank[left_root] < self.rank[right_root]:
            self.parent[left_root] = right_root
            return

        if self.rank[left_root] > self.rank[right_root]:
            self.parent[right_root] = left_root
            return

        self.parent[right_root] = left_root
        self.rank[left_root] += 1


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Detect semantic near-duplicates.")
    parser.add_argument(
        "--input-jsonl",
        default="datasets/final/merged_all.jsonl",
        help="Input JSONL dataset to analyze.",
    )
    parser.add_argument(
        "--report-path",
        default="docs/reports/near_duplicates.md",
        help="Markdown report path.",
    )
    parser.add_argument(
        "--json-report",
        default="outputs/dataset_validation/near_duplicates.json",
        help="Machine-readable JSON report path.",
    )
    parser.add_argument(
        "--minhash-permutations",
        type=int,
        default=64,
        help="Number of permutations for MinHash signatures.",
    )
    parser.add_argument(
        "--minhash-threshold",
        type=float,
        default=0.80,
        help="Minimum MinHash estimated similarity used in final duplicate rule.",
    )
    parser.add_argument(
        "--simhash-max-hamming",
        type=int,
        default=10,
        help="Maximum SimHash Hamming distance used in final duplicate rule.",
    )
    parser.add_argument(
        "--embedding-threshold",
        type=float,
        default=0.92,
        help="Minimum embedding cosine similarity used in final duplicate rule.",
    )
    parser.add_argument(
        "--high-confidence-embedding",
        type=float,
        default=0.97,
        help="Embedding-only high-confidence duplicate threshold.",
    )
    parser.add_argument(
        "--max-pairs-in-report",
        type=int,
        default=200,
        help="Maximum confirmed near-duplicate pairs listed in markdown report.",
    )
    parser.add_argument(
        "--max-removals-in-report",
        type=int,
        default=300,
        help="Maximum recommended removals listed in markdown report.",
    )
    return parser.parse_args()


def stable_hash64(text: str) -> int:
    """Return deterministic 64-bit hash for text."""
    digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, byteorder="big", signed=False)


def normalize_text(text: str) -> str:
    """Whitespace-normalize text."""
    return " ".join(text.split())


def tokenize(text: str) -> list[str]:
    """Tokenize text into alphanumeric tokens."""
    return TOKEN_RE.findall(text.lower())


def choose_text(payload: dict[str, Any]) -> str:
    """Choose candidate text field from common schemas."""
    for key in ("input", "text", "essay", "argument_text", "student_response", "content"):
        value = payload.get(key)
        if value is None:
            continue
        text = normalize_text(str(value))
        if text:
            return text
    return ""


def choose_id(payload: dict[str, Any], fallback: str) -> str:
    """Choose record id from common keys."""
    for key in ("id", "example_id", "essay_id", "uuid"):
        value = payload.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return fallback


def parse_score(value: Any) -> float | None:
    """Parse numeric score when possible."""
    if value is None or isinstance(value, bool):
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


def load_records(path: Path) -> list[Record]:
    """Load dataset rows and normalize to Record objects."""
    records: list[Record] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_idx, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, dict):
                continue

            text = choose_text(payload)
            if not text:
                continue

            record_id = choose_id(payload, fallback=f"row-{line_idx:08d}")
            split = str(payload.get("split", "")).strip().lower() or "unknown"
            source = str(payload.get("source", "")).strip() or "unknown"
            score = parse_score(payload.get("score", payload.get("label")))

            records.append(
                Record(
                    index=len(records),
                    record_id=record_id,
                    split=split,
                    source=source,
                    score=score,
                    text=text,
                )
            )

    return records


def token_shingles(tokens: list[str], size: int = 3) -> set[int]:
    """Build token shingles hashed to integers."""
    if not tokens:
        return set()
    if len(tokens) < size:
        return {stable_hash64(" ".join(tokens))}

    values: set[int] = set()
    for idx in range(len(tokens) - size + 1):
        shingle = " ".join(tokens[idx : idx + size])
        values.add(stable_hash64(shingle))
    return values


def minhash_params(num_perm: int, seed: int = 13) -> list[tuple[int, int]]:
    """Build random MinHash permutation coefficients."""
    rng = random.Random(seed)
    params: list[tuple[int, int]] = []
    for _ in range(num_perm):
        a = rng.randrange(1, MERSENNE_61 - 1)
        b = rng.randrange(0, MERSENNE_61 - 1)
        params.append((a, b))
    return params


def build_minhash_signature(shingles: set[int], params: list[tuple[int, int]]) -> tuple[int, ...]:
    """Compute MinHash signature from hashed shingles."""
    if not shingles:
        return tuple(0 for _ in range(len(params)))

    signature: list[int] = []
    for a, b in params:
        minimum = MERSENNE_61
        for value in shingles:
            hashed = (a * value + b) % MERSENNE_61
            if hashed < minimum:
                minimum = hashed
        signature.append(minimum)
    return tuple(signature)


def minhash_lsh_candidates(
    signatures: list[tuple[int, ...]],
    bands: int = 16,
    rows_per_band: int = 4,
) -> set[tuple[int, int]]:
    """Generate candidate pairs from MinHash LSH band collisions."""
    candidates: set[tuple[int, int]] = set()
    if not signatures:
        return candidates

    if bands * rows_per_band > len(signatures[0]):
        raise ValueError("bands * rows_per_band exceeds signature length")

    for band_idx in range(bands):
        start = band_idx * rows_per_band
        end = start + rows_per_band
        buckets: dict[tuple[int, ...], list[int]] = defaultdict(list)

        for row_idx, signature in enumerate(signatures):
            key = signature[start:end]
            buckets[key].append(row_idx)

        for group in buckets.values():
            if len(group) < 2:
                continue
            for left_pos in range(len(group)):
                for right_pos in range(left_pos + 1, len(group)):
                    left = group[left_pos]
                    right = group[right_pos]
                    if left > right:
                        left, right = right, left
                    candidates.add((left, right))

    return candidates


def minhash_similarity(sig_left: tuple[int, ...], sig_right: tuple[int, ...]) -> float:
    """Estimate Jaccard from MinHash signatures."""
    matches = 0
    for left, right in zip(sig_left, sig_right, strict=True):
        if left == right:
            matches += 1
    return matches / len(sig_left)


def build_simhash(tokens: list[str]) -> int:
    """Compute 64-bit SimHash signature from token frequencies."""
    if not tokens:
        return 0

    counts: dict[str, int] = defaultdict(int)
    for token in tokens:
        counts[token] += 1

    vector = [0] * 64
    for token, weight in counts.items():
        hashed = stable_hash64(token)
        for bit in range(64):
            delta = weight if ((hashed >> bit) & 1) else -weight
            vector[bit] += delta

    signature = 0
    for bit, value in enumerate(vector):
        if value >= 0:
            signature |= 1 << bit
    return signature


def hamming_distance(left: int, right: int) -> int:
    """Compute Hamming distance between two 64-bit integers."""
    return (left ^ right).bit_count()


def simhash_candidates(simhashes: list[int], prefix_bits: int = 16) -> set[tuple[int, int]]:
    """Generate candidate pairs from SimHash prefix bucket collisions."""
    buckets: dict[int, list[int]] = defaultdict(list)
    for idx, signature in enumerate(simhashes):
        key = signature >> (64 - prefix_bits)
        buckets[key].append(idx)

    pairs: set[tuple[int, int]] = set()
    for group in buckets.values():
        if len(group) < 2:
            continue
        for left_pos in range(len(group)):
            for right_pos in range(left_pos + 1, len(group)):
                left = group[left_pos]
                right = group[right_pos]
                if left > right:
                    left, right = right, left
                pairs.add((left, right))

    return pairs


def build_sentence_embedding(tokens: list[str], dimension: int = 384) -> list[float]:
    """Build deterministic sentence embedding via hashing trick."""
    if not tokens:
        return [0.0] * dimension

    vector = [0.0] * dimension
    for token in tokens:
        hashed = stable_hash64(token)
        index = hashed % dimension
        sign = 1.0 if ((hashed >> 63) & 1) else -1.0
        vector[index] += sign

    # Add lightweight bigram signal.
    for idx in range(len(tokens) - 1):
        bigram = f"{tokens[idx]}_{tokens[idx + 1]}"
        hashed = stable_hash64(bigram)
        index = hashed % dimension
        sign = 1.0 if ((hashed >> 62) & 1) else -1.0
        vector[index] += sign * 0.5

    norm = math.sqrt(sum(value * value for value in vector))
    if norm <= 0:
        return vector
    return [value / norm for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between normalized vectors."""
    return sum(lv * rv for lv, rv in zip(left, right, strict=True))


def duplicate_decision(pair: PairScore, args: argparse.Namespace) -> bool:
    """Apply combined decision rule across the three methods."""
    if pair.embedding_cosine >= args.high_confidence_embedding:
        return True

    condition_embedding = pair.embedding_cosine >= args.embedding_threshold
    condition_simhash = pair.simhash_hamming <= args.simhash_max_hamming
    condition_minhash = pair.minhash_similarity >= args.minhash_threshold
    return condition_embedding and (condition_simhash or condition_minhash)


def split_priority(split: str) -> int:
    """Higher is better when choosing canonical cluster member."""
    if split == "test":
        return 4
    if split == "validation":
        return 3
    if split == "train":
        return 2
    return 1


def choose_cluster_keep(record_indices: list[int], records: list[Record]) -> int:
    """Choose representative index to keep for a duplicate cluster."""
    ranked = sorted(
        record_indices,
        key=lambda idx: (
            split_priority(records[idx].split),
            1 if records[idx].score is not None else 0,
            len(records[idx].text),
            -idx,
        ),
        reverse=True,
    )
    return ranked[0]


def render_report(
    *,
    input_path: Path,
    records: list[Record],
    candidate_count: int,
    confirmed_pairs: list[PairScore],
    clusters: list[list[int]],
    recommended_removals: list[int],
    keep_indices: set[int],
    args: argparse.Namespace,
) -> str:
    """Render markdown duplicate analysis report."""
    lines = [
        "# Near-Duplicate Analysis",
        "",
        f"- Input dataset: `{input_path}`",
        f"- Records analyzed: `{len(records)}`",
        f"- Candidate pairs (MinHash/SimHash union): `{candidate_count}`",
        f"- Confirmed near-duplicate pairs: `{len(confirmed_pairs)}`",
        f"- Duplicate clusters (size >= 2): `{len(clusters)}`",
        f"- Recommended removals: `{len(recommended_removals)}`",
        "",
        "## Methods",
        "",
        "- MinHash: token 3-shingles, 64 permutations, LSH candidate generation.",
        "- SimHash: 64-bit signature over token frequencies with prefix-bucket candidates.",
        "- Sentence embeddings: deterministic hashing-based 384-d sentence vectors.",
        "",
        "## Thresholds",
        "",
        f"- `minhash_threshold`: `{args.minhash_threshold}`",
        f"- `simhash_max_hamming`: `{args.simhash_max_hamming}`",
        f"- `embedding_threshold`: `{args.embedding_threshold}`",
        f"- `high_confidence_embedding`: `{args.high_confidence_embedding}`",
        "",
        "Decision rule:",
        "",
        "- duplicate if embedding >= high_confidence OR",
        "- (embedding >= embedding_threshold AND (simhash <= max_hamming OR minhash >= threshold))",
        "",
        "## Recommended Removals",
        "",
        "Recommendations only; no records were deleted automatically.",
        "",
        "| remove_id | keep_id | remove_split | keep_split | remove_source | keep_source |",
        "|---|---|---|---|---|---|",
    ]

    keep_lookup: dict[int, int] = {}
    for cluster in clusters:
        keep_idx = choose_cluster_keep(cluster, records)
        for idx in cluster:
            if idx != keep_idx:
                keep_lookup[idx] = keep_idx

    shown = 0
    for remove_idx in recommended_removals:
        if shown >= args.max_removals_in_report:
            break
        keep_idx = keep_lookup[remove_idx]
        remove_rec = records[remove_idx]
        keep_rec = records[keep_idx]
        lines.append(
            "| "
            f"`{remove_rec.record_id}` | "
            f"`{keep_rec.record_id}` | "
            f"`{remove_rec.split}` | "
            f"`{keep_rec.split}` | "
            f"`{remove_rec.source}` | "
            f"`{keep_rec.source}` |"
        )
        shown += 1

    if len(recommended_removals) > shown:
        lines.append(
            "| ... "
            f"{len(recommended_removals) - shown} additional recommendations omitted "
            "| | | | | |"
        )

    lines.extend(
        [
            "",
            "## Confirmed Pair Samples",
            "",
            "| left_id | right_id | minhash | hamming | cosine |",
            "|---|---|---:|---:|---:|",
        ]
    )

    for pair in sorted(
        confirmed_pairs,
        key=lambda item: item.embedding_cosine,
        reverse=True,
    )[: args.max_pairs_in_report]:
        left = records[pair.left_index]
        right = records[pair.right_index]
        lines.append(
            "| "
            f"`{left.record_id}` | "
            f"`{right.record_id}` | "
            f"{pair.minhash_similarity:.3f} | "
            f"{pair.simhash_hamming} | "
            f"{pair.embedding_cosine:.3f} |"
        )

    lines.extend(
        [
            "",
            "## Cluster Summary",
            "",
            "| cluster_id | size | keep_id | keep_split |",
            "|---:|---:|---|---|",
        ]
    )

    for cluster_id, cluster in enumerate(sorted(clusters, key=len, reverse=True), start=1):
        keep_idx = choose_cluster_keep(cluster, records)
        keep_rec = records[keep_idx]
        lines.append(
            f"| {cluster_id} | {len(cluster)} | `{keep_rec.record_id}` | `{keep_rec.split}` |"
        )

    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- Keep-selection heuristic prioritizes `test` > `validation` > `train`, "
        "then non-null score, then longer text."
    )
    lines.append("- All recommendations are reversible because no dataset files were modified.")

    return "\n".join(lines)


def main() -> None:
    """Run near-duplicate detection pipeline."""
    args = parse_args()
    input_path = Path(args.input_jsonl)
    report_path = Path(args.report_path)
    json_report_path = Path(args.json_report)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_report_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(input_path)
    if not records:
        report_path.write_text(
            "# Near-Duplicate Analysis\n\nNo analyzable records found.\n",
            encoding="utf-8",
        )
        json_report_path.write_text(
            json.dumps({"input": str(input_path), "records": 0}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(json.dumps({"records": 0, "report_path": str(report_path)}, indent=2))
        return

    tokenized = [tokenize(record.text) for record in records]
    shingles = [token_shingles(tokens) for tokens in tokenized]

    params = minhash_params(args.minhash_permutations)
    minhash_signatures = [build_minhash_signature(item, params) for item in shingles]
    minhash_candidates = minhash_lsh_candidates(minhash_signatures)

    simhashes = [build_simhash(tokens) for tokens in tokenized]
    simhash_candidate_pairs = simhash_candidates(simhashes)

    candidate_pairs = minhash_candidates | simhash_candidate_pairs

    embeddings = [build_sentence_embedding(tokens) for tokens in tokenized]

    confirmed_pairs: list[PairScore] = []
    for left_idx, right_idx in sorted(candidate_pairs):
        minhash_sim = minhash_similarity(
            minhash_signatures[left_idx],
            minhash_signatures[right_idx],
        )
        simhash_dist = hamming_distance(simhashes[left_idx], simhashes[right_idx])
        cosine = cosine_similarity(embeddings[left_idx], embeddings[right_idx])

        pair = PairScore(
            left_index=left_idx,
            right_index=right_idx,
            minhash_similarity=minhash_sim,
            simhash_hamming=simhash_dist,
            embedding_cosine=cosine,
        )
        if duplicate_decision(pair, args):
            confirmed_pairs.append(pair)

    union = UnionFind(len(records))
    for pair in confirmed_pairs:
        union.union(pair.left_index, pair.right_index)

    cluster_map: dict[int, list[int]] = defaultdict(list)
    for idx in range(len(records)):
        root = union.find(idx)
        cluster_map[root].append(idx)

    clusters = [cluster for cluster in cluster_map.values() if len(cluster) >= 2]

    keep_indices: set[int] = set()
    recommended_removals: list[int] = []
    for cluster in clusters:
        keep_idx = choose_cluster_keep(cluster, records)
        keep_indices.add(keep_idx)
        for idx in sorted(cluster):
            if idx != keep_idx:
                recommended_removals.append(idx)

    report_text = render_report(
        input_path=input_path,
        records=records,
        candidate_count=len(candidate_pairs),
        confirmed_pairs=confirmed_pairs,
        clusters=clusters,
        recommended_removals=recommended_removals,
        keep_indices=keep_indices,
        args=args,
    )
    report_path.write_text(report_text, encoding="utf-8")

    json_payload = {
        "input": str(input_path),
        "records": len(records),
        "candidate_pairs": len(candidate_pairs),
        "confirmed_pairs": len(confirmed_pairs),
        "clusters": [
            {
                "size": len(cluster),
                "keep_id": records[choose_cluster_keep(cluster, records)].record_id,
                "member_ids": [records[idx].record_id for idx in cluster],
            }
            for cluster in sorted(clusters, key=len, reverse=True)
        ],
        "recommended_remove_ids": [records[idx].record_id for idx in recommended_removals],
        "thresholds": {
            "minhash_threshold": args.minhash_threshold,
            "simhash_max_hamming": args.simhash_max_hamming,
            "embedding_threshold": args.embedding_threshold,
            "high_confidence_embedding": args.high_confidence_embedding,
        },
    }
    json_report_path.write_text(
        json.dumps(json_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "records": len(records),
                "candidate_pairs": len(candidate_pairs),
                "confirmed_pairs": len(confirmed_pairs),
                "clusters": len(clusters),
                "recommended_removals": len(recommended_removals),
                "report_path": str(report_path),
                "json_report": str(json_report_path),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
