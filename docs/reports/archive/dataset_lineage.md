# Dataset Lineage Reconciliation

Date: 2026-07-08

## Executive Summary

- There are **two distinct lineage branches** in the repository:
  - A **legacy merge branch** that produced `12,960` rows.
  - A **current reproducible build branch** that produced `12,413` rows.
- The `12,960` value comes from older artifacts (`reports/final_dataset.md` and `datasets/final/dataset_dict`).
- The current canonical outputs (`datasets/final/*.jsonl` and `datasets/training`) are `12,413` rows.
- I found **no report** in the repository claiming a dataset size of `15,557`.

## Lineage A (Legacy Merge Branch)

Source evidence:
- `reports/final_dataset.md`
- `datasets/final/dataset_dict`

| Stage | Artifact / Process | Rows | Delta | Reconciliation |
|---|---|---:|---:|---|
| A1 | HF ingest output | 12,964 | — | from `datasets/hf/dataset_dict` |
| A2 | Legacy merge (`reports/final_dataset.md`) kept before dedup | 12,964 | 0 | matches A1 |
| A3 | Legacy merge dedup removed duplicate text | 4 | -4 | `12,964 - 4 = 12,960` |
| A4 | Legacy final rows | 12,960 | — | reported split: train 10,365 / val 1,291 / test 1,304 |

Result: **12,960** (legacy branch)

## Lineage B (Current Reproducible Build Branch)

Source evidence:
- `reports/reproducibility.md`
- `reports/unified_sanitization.md`
- `reports/final_dataset_quality.md`
- `reports/deduplication.md`
- `reports/training_dataset.md`
- line counts from `datasets/final/*.jsonl`

| Stage | Artifact / Process | Rows | Delta | Reconciliation |
|---|---|---:|---:|---|
| B1 | Unified combined (`datasets/processed/unified/unified_all.jsonl`) | 562,856 | — | normalization output |
| B2 | Sanitized unified (`unified_all.sanitized.jsonl`) | 561,678 | -1,178 | `562,856 = 561,678 + 1,178` |
| B3 | Quality scored (`quality_scored.jsonl`) | 561,678 | 0 | one scored row per sanitized row |
| B4 | Quality kept (`quality_filtered.jsonl`) | 433,906 | -127,772 | `561,678 = 433,906 + 127,772` |
| B5 | Dedup input | 433,906 | 0 | same as B4 |
| B6 | Dedup kept (`quality_deduped.jsonl`) | 12,413 | -421,493 | `433,906 = 12,413 + 308,723 + 42,237 + 70,533` |
| B7 | Final splits (`train/validation/test.jsonl`) | 12,413 | 0 | `9,940 + 1,241 + 1,232 = 12,413` |
| B8 | Training dataset (`datasets/training`) | 12,413 | 0 | same split counts as B7 |

Dedup breakdown (B6):
- Removed duplicate IDs: `308,723`
- Removed duplicate text: `42,237`
- Skipped invalid rows: `70,533`

Result: **12,413** (current branch)

## Origin of Additional Rows Before Dedup (B4)

`quality_filtered.jsonl` has `433,906` rows because normalization recursively included many generated artifacts from prior runs.

| `metadata.source_case` | Rows |
|---|---:|
| `final/quality_filtered.jsonl` | 149,598 |
| `final/quality_scored.jsonl` | 149,598 |
| `processed/normalized/all_datasets.jsonl` | 20,076 |
| `processed/normalized/asap_aes.jsonl` | 20,076 |
| `hf/dataset_dict#hf` | 12,417 |
| `final` | 12,413 |
| `final/dataset_dict#hf` | 12,413 |
| `final/merged_all.jsonl` | 12,413 |
| `final/quality_deduped.jsonl` | 12,413 |
| `training#hf` | 12,413 |
| `raw/asap_aes/training_set_rel3.tsv` | 12,239 |
| `raw/asap_aes/test_set.tsv` | 3,925 |
| `raw/asap_aes/valid_set.tsv` | 3,912 |
| **Total** | **433,906** |

This table reconciles exactly to B4.

## Exact Reconciliation of the 12,960 vs 12,413 Difference

I compared IDs directly between:
- legacy artifact: `datasets/final/dataset_dict` (`12,960` rows)
- current final artifact: `datasets/final/merged_all.jsonl` (`12,413` rows)

Findings:
- IDs in legacy but not current: `547`
- IDs in current but not legacy: `0`
- Those `547` IDs all appear in `datasets/final/quality_removed.jsonl`

Interpretation:
- The `547`-row gap is fully explained by rows that survived the old branch but were filtered out in the current branch before final materialization.

## About the `15,557` Claim

- I searched repository reports/artifacts for a dataset-size claim of `15,557` and found none.
- The literal value `15557` appears as an **essay ID** in ASAP data, not as a total row count.
- Therefore, `15,557` cannot be reconciled from the current checked-in artifacts.

## Final Reconciled Totals

- Legacy branch final: **12,960**
- Current branch final/training: **12,413**
- Count discrepancy between branches: **547** (fully traced)
- `15,557` claim: **not present in repository lineage artifacts**
