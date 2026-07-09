# Provenance Index Report

- Output parquet: `datasets/final/provenance.parquet`
- Total records: `12413`

## Counts by Split

| split | records |
|---|---:|
| train | 9940 |
| validation | 1241 |
| test | 1232 |

## Counts by Dataset

| dataset | records |
|---|---:|
| asap_aes | 12413 |

## Completeness

- Unknown `original_url`: `0`
- Unknown `license`: `12413`
- Unknown `retrieval_date`: `0`

## Top Source Filenames

| source_filename | records |
|---|---:|
| training_set_rel3.tsv | 12413 |

## Schema

Each record contains:
- `example_id`
- `dataset`
- `original_url`
- `license`
- `retrieval_date`
- `hash` (SHA-256 of essay text)
- `split`
- `source_filename`