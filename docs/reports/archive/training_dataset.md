# Training Dataset Build Report

- Input unified dataset: `datasets/final/quality_deduped.jsonl`
- Output dataset dir: `datasets/training`
- Output provenance dir: `datasets/training_provenance`

## Pipeline Summary

- Input non-empty lines processed: `12413`
- JSON parse errors skipped: `0`
- Non-object rows skipped: `0`
- Filtered missing split: `0`
- Filtered invalid split: `0`
- Filtered missing prompt: `0`
- Filtered missing essay: `0`
- Filtered missing score field: `0`
- Filtered non-numeric score: `0`
- Kept before deduplication: `12413`
- Exact duplicates removed: `0`
- Final examples: `12413`

## Final Split Counts

| split | examples | score_min | score_max | score_mean |
|---|---:|---:|---:|---:|
| train | 9940 | 0.0000 | 55.0000 | 7.0473 |
| validation | 1241 | 0.0000 | 50.0000 | 6.9444 |
| test | 1232 | 0.0000 | 60.0000 | 7.2029 |

## Output Schema

Training dataset fields (only):
- `prompt`
- `essay`
- `score`

Provenance is stored separately per split in JSONL files and contains source lineage.

## HF Load Verification

- `datasets.load_from_disk()` status: PASS
- Message: load_from_disk succeeded with required splits and columns