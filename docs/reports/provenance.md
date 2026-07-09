# Provenance Repair Report

- Output parquet: `datasets/final/provenance.parquet`
- Final JSONL rows scanned: `144015`
- Provenance rows written: `144015`
- Fully traceable rows: `144015`
- All examples traceable: `YES`

## Required Field Completeness

| field | missing_rows |
|---|---:|
| original_dataset | 0 |
| original_identifier | 0 |
| preprocessing_history | 0 |
| split_assignment | 0 |
| source_url | 0 |
| license | 0 |

## Counts by Split Assignment

| split | rows |
|---|---:|
| test | 12122 |
| train | 81300 |
| validation | 50593 |

## Counts by Original Dataset

| original_dataset | rows |
|---|---:|
| asap_aes | 144007 |
| hf/build_summary.json | 2 |
| hf/dataset_dict/dataset_dict.json | 2 |
| hf/dataset_dict/train/dataset_info.json | 2 |
| hf/dataset_dict/train/state.json | 2 |

## Artifact Coverage

| artifact | input_rows | provenance_rows | match |
|---|---:|---:|---|
| final/merged_all.jsonl | 12413 | 12413 | yes |
| final/quality_deduped.jsonl | 12413 | 12413 | yes |
| final/quality_filtered.jsonl | 32493 | 32493 | yes |
| final/quality_removed.jsonl | 20895 | 20895 | yes |
| final/quality_scored.jsonl | 53388 | 53388 | yes |
| final/test.jsonl | 1242 | 1242 | yes |
| final/train.jsonl | 9930 | 9930 | yes |
| final/validation.jsonl | 1241 | 1241 | yes |

## Preview Rows

| example_id | original_dataset | original_identifier | split_assignment | source_url | license |
|---|---|---|---|---|---|
| 1 | asap_aes | 1 | train | datasets/hf/dataset_dict#train | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 2 | asap_aes | 2 | train | datasets/hf/dataset_dict#train | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 3 | asap_aes | 3 | train | datasets/hf/dataset_dict#train | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 4 | asap_aes | 4 | train | datasets/hf/dataset_dict#train | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 5 | asap_aes | 5 | train | datasets/hf/dataset_dict#train | ASAP-AES competition/research dataset terms (verify redistribution rights) |

## Schema

Each provenance row contains:
- `example_id`
- `dataset`
- `original_dataset`
- `original_identifier`
- `preprocessing_history` (JSON array string of stages)
- `split`
- `split_assignment`
- `source_url`
- `original_url` (compatibility alias)
- `license`
- `retrieval_date`
- `hash`
- `source_filename`
- `artifact_path`
- `artifact_row`

## Verification Result

Every example in `datasets/final` is traceable with required provenance fields.