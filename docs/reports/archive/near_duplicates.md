# Near-Duplicate Analysis

- Input dataset: `/Users/clairemao/Documents/cogni-slm/datasets/final/merged_all.jsonl`
- Records analyzed: `12960`
- Candidate pairs (MinHash/SimHash union): `158027`
- Confirmed near-duplicate pairs: `7`
- Duplicate clusters (size >= 2): `7`
- Recommended removals: `7`

## Methods

- MinHash: token 3-shingles, 64 permutations, LSH candidate generation.
- SimHash: 64-bit signature over token frequencies with prefix-bucket candidates.
- Sentence embeddings: deterministic hashing-based 384-d sentence vectors.

## Thresholds

- `minhash_threshold`: `0.8`
- `simhash_max_hamming`: `10`
- `embedding_threshold`: `0.92`
- `high_confidence_embedding`: `0.97`

Decision rule:

- duplicate if embedding >= high_confidence OR
- (embedding >= embedding_threshold AND (simhash <= max_hamming OR minhash >= threshold))

## Recommended Removals

Recommendations only; no records were deleted automatically.

| remove_id | keep_id | remove_split | keep_split | remove_source | keep_source |
|---|---|---|---|---|---|
| `15739` | `16181` | `train` | `train` | `asap_aes` | `asap_aes` |
| `16348` | `15629` | `train` | `train` | `asap_aes` | `asap_aes` |
| `9147` | `9507` | `train` | `train` | `asap_aes` | `asap_aes` |
| `9894` | `9950` | `train` | `train` | `asap_aes` | `asap_aes` |
| `9831` | `8965` | `train` | `train` | `asap_aes` | `asap_aes` |
| `9739` | `10602` | `train` | `validation` | `asap_aes` | `asap_aes` |
| `15844` | `15955` | `train` | `train` | `asap_aes` | `asap_aes` |

## Confirmed Pair Samples

| left_id | right_id | minhash | hamming | cosine |
|---|---|---:|---:|---:|
| `9739` | `10602` | 0.844 | 1 | 0.990 |
| `9507` | `9147` | 0.891 | 2 | 0.985 |
| `8965` | `9831` | 0.672 | 5 | 0.970 |
| `9950` | `9894` | 0.719 | 4 | 0.967 |
| `16348` | `15629` | 0.453 | 6 | 0.924 |
| `15955` | `15844` | 0.391 | 7 | 0.921 |
| `16181` | `15739` | 0.438 | 9 | 0.920 |

## Cluster Summary

| cluster_id | size | keep_id | keep_split |
|---:|---:|---|---|
| 1 | 2 | `16181` | `train` |
| 2 | 2 | `15629` | `train` |
| 3 | 2 | `9507` | `train` |
| 4 | 2 | `9950` | `train` |
| 5 | 2 | `8965` | `train` |
| 6 | 2 | `10602` | `validation` |
| 7 | 2 | `15955` | `train` |

## Notes

- Keep-selection heuristic prioritizes `test` > `validation` > `train`, then non-null score, then longer text.
- All recommendations are reversible because no dataset files were modified.