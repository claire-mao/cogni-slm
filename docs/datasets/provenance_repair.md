# Provenance Repair Report

- Output parquet: `datasets/final/provenance.parquet`
- Final JSONL rows scanned: `1173555`
- Provenance rows written: `1173555`
- Fully traceable rows: `1173555`
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
| test | 75684 |
| train | 984047 |
| validation | 113824 |

## Counts by Original Dataset

| original_dataset | rows |
|---|---:|
| asap_aes | 870489 |
| final/dataset_dict/dataset_dict.json | 6 |
| final/dataset_dict/test/dataset_info.json | 6 |
| final/dataset_dict/test/state.json | 6 |
| final/dataset_dict/train/dataset_info.json | 6 |
| final/dataset_dict/train/state.json | 6 |
| final/dataset_dict/validation/dataset_info.json | 6 |
| final/dataset_dict/validation/state.json | 6 |
| heldout_placeholder | 1320 |
| hf/build_summary.json | 6 |
| hf/dataset_dict/dataset_dict.json | 6 |
| hf/dataset_dict/train/dataset_info.json | 6 |
| hf/dataset_dict/train/state.json | 6 |
| processed/normalized/all_datasets.jsonl | 7068 |
| processed/normalized/summary.json | 6 |
| raw/asap_aes/test_set.tsv | 23550 |
| raw/asap_aes/training_set_rel3.tsv | 73434 |
| raw/asap_aes/valid_set.tsv | 23472 |
| training#hf | 87054 |
| training/dataset_dict.json | 6 |
| training/test/dataset_info.json | 6 |
| training/test/state.json | 6 |
| training/train/dataset_info.json | 6 |
| training/train/state.json | 6 |
| training/validation/dataset_info.json | 6 |
| training/validation/state.json | 6 |
| training_provenance | 87054 |

## Artifact Coverage

| artifact | input_rows | provenance_rows | match |
|---|---:|---:|---|
| final/dataset_dict/test | 1304 | 1304 | yes |
| final/dataset_dict/train | 10365 | 10365 | yes |
| final/dataset_dict/validation | 1291 | 1291 | yes |
| final/merged_all.jsonl | 12413 | 12413 | yes |
| final/quality_deduped.jsonl | 12413 | 12413 | yes |
| final/quality_filtered.jsonl | 433906 | 433906 | yes |
| final/quality_removed.jsonl | 127772 | 127772 | yes |
| final/quality_scored.jsonl | 561678 | 561678 | yes |
| final/test.jsonl | 1232 | 1232 | yes |
| final/train.jsonl | 9940 | 9940 | yes |
| final/validation.jsonl | 1241 | 1241 | yes |

## Preview Rows

| example_id | original_dataset | original_identifier | split_assignment | source_url | license |
|---|---|---|---|---|---|
| 12617 | asap_aes | 12617 | test | datasets/final/test.jsonl | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 10222 | asap_aes | 10222 | test | datasets/final/test.jsonl | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 15257 | asap_aes | 15257 | test | datasets/final/test.jsonl | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 4501 | asap_aes | 4501 | test | datasets/final/test.jsonl | ASAP-AES competition/research dataset terms (verify redistribution rights) |
| 7289 | asap_aes | 7289 | test | datasets/final/test.jsonl | ASAP-AES competition/research dataset terms (verify redistribution rights) |

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