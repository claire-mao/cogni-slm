# Full Pipeline Audit

Date: 2026-07-08

## Scope
This audit traces the dataset pipeline from `datasets/raw/` to `datasets/training/`, verifies counts against actual files, and checks whether reported counts are consistent with artifacts.

Canonical pipeline inspected:
1. Raw data discovery (`datasets/raw`)
2. HF ingest (`datasets/build_dataset.py`)
3. Unified normalization (`scripts/normalize_unified_schema.py`)
4. Unified sanitization (`scripts/build_dataset.py` sanitize step)
5. Quality scoring/filtering (`scripts/build_dataset.py` fast quality step)
6. Dedup + final materialization (`scripts/build_dataset.py` dedup step)
7. Provenance generation (`scripts/create_provenance_index.py`)
8. Training dataset build (`scripts/build_training_dataset.py`)

## Stage-by-Stage Reconciliation

| Stage | Input files | Output files | Reported count | Actual count | Status |
|---|---|---|---:|---:|---|
| 0. Raw discovery | `datasets/raw/**/*.csv|tsv|json|jsonl|txt` | candidates for ingest | `7` files scanned | `7` files scanned | MATCH |
| 1. HF ingest | 7 raw tabular files | `datasets/hf/dataset_dict` + `datasets/hf/build_summary.json` | train `12,964` | train `12,964` | MATCH |
| 2. Unified normalization | datasets root (multiple cases) | `datasets/processed/unified/unified_all.jsonl` | `562,856` rows | `562,856` rows | MATCH |
| 3. Sanitization | `unified_all.jsonl` | `unified_all.sanitized.jsonl` | kept `561,678`, skipped `1,178` | kept `561,678`, skipped `1,178` | MATCH |
| 4. Quality scoring/filter | `unified_all.sanitized.jsonl` | `quality_scored.jsonl`, `quality_filtered.jsonl`, `quality_removed.jsonl` | total `561,678`, kept `433,906`, removed `127,772` | same | MATCH |
| 5. Dedup + final split materialization | `quality_filtered.jsonl` | `quality_deduped.jsonl`, `merged_all.jsonl`, `train.jsonl`, `validation.jsonl`, `test.jsonl` | final `12,413` | final `12,413` | MATCH |
| 6. Provenance | final split JSONLs | `datasets/final/provenance.parquet` | `12,413` | `12,413` | MATCH |
| 7. Training dataset build | `quality_deduped.jsonl` | `datasets/training` + `datasets/training_provenance` | total `12,413` | total `12,413` | MATCH |

## Raw Stage Detail (What Was Ingested)

Ingest script only consumes structured files with supported extensions.

| Raw file | Parsed rows seen | Kept | Dropped missing text | Dropped missing score | Dropped bad score |
|---|---:|---:|---:|---:|---:|
| `datasets/raw/asap_aes/training_set_rel3.tsv` | 12,991 | 12,964 | 0 | 12 | 15 |
| `datasets/raw/asap_aes/test_set.tsv` | 4,261 | 0 | 4 | 4,257 | 0 |
| `datasets/raw/asap_aes/valid_set.tsv` | 4,221 | 0 | 3 | 4,218 | 0 |
| `datasets/raw/asap_aes/valid_sample_submission_1_column.csv` | 4,818 | 0 | 4,818 | 0 | 0 |
| `datasets/raw/asap_aes/valid_sample_submission_1_column_no_header.csv` | 4,817 | 0 | 4,817 | 0 | 0 |
| `datasets/raw/asap_aes/valid_sample_submission_2_column.csv` | 4,818 | 0 | 4,818 | 0 | 0 |
| `datasets/raw/asap_aes/valid_sample_submission_5_column.csv` | 4,818 | 0 | 4,818 | 0 | 0 |
| **Total** | **40,744** | **12,964** | **19,278** | **8,487** | **15** |

Notes:
- These are **parsed record counts**, not plain line counts. Some essay rows span multiple physical lines due quoted newlines.
- Only `training_set_rel3.tsv` contributes kept examples in current ingest.

## Schema and Transformation Audit by Stage

### Stage 1: HF ingest (`datasets/build_dataset.py`)
- Output schema:
  - `id: string`
  - `text: string`
  - `score: float64`
  - `source: string`
  - `prompt: string`
  - `split: string`
- Transformations:
  - Field mapping via priority keys (e.g., `essay -> text`, `domain1_score -> score`).
  - Split inference from filename when split field missing.
- Duplicate removal: none.
- Filtering: rows missing text, missing score, or non-numeric score are dropped.

### Stage 2: Unified normalization (`scripts/normalize_unified_schema.py`)
- Output schema (`unified_all.jsonl` rows):
  - `id, task, prompt, input, response, score, rubric, source, license, split, metadata`
- Transformations:
  - Normalizes varied source schemas into one canonical schema.
  - Preserves source payload in `metadata.original_fields`.
- Duplicate removal: none.
- Filtering: none; parse issues can be represented in rows/metadata and handled later.

### Stage 3: Sanitization
- Input: `562,856` rows.
- Output: `561,678` valid JSON-object rows.
- Filtering: removes malformed/non-object lines (`1,178`).
- Duplicate removal: none.

### Stage 4: Quality scoring/filtering
- `quality_scored.jsonl`: same row count as sanitized input (`561,678`), adds `quality` block.
- `quality_filtered.jsonl`: rows with score >= threshold (`433,906`).
- `quality_removed.jsonl`: summary rows for removed examples (`127,772`), schema: `id, source, overall_quality_score, reason`.
- Duplicate removal: none.

### Stage 5: Dedup + final materialization
- Input: `quality_filtered.jsonl` (`433,906`).
- Operations:
  - Remove duplicate IDs.
  - Remove duplicate normalized text hash.
  - Skip invalid rows at materialization time.
  - Convert to final schema for split files.
- Final schema (`datasets/final/{train,validation,test}.jsonl`):
  - `id, source, task, prompt, text, label, metadata, split`
- Count identity (verified):
  - `433,906 = 12,413 + 308,723 + 42,237 + 70,533`

### Stage 6: Provenance
- Input: final split JSONLs (`9,940 + 1,241 + 1,232`).
- Output: `datasets/final/provenance.parquet` with `12,413` rows.
- Schema:
  - `example_id, dataset, original_url, license, retrieval_date, hash, split, source_filename`

### Stage 7: Training dataset build
- Input: `datasets/final/quality_deduped.jsonl` (`12,413`).
- Output:
  - `datasets/training` (HF DatasetDict): train `9,940`, validation `1,241`, test `1,232`.
  - `datasets/training_provenance/*.jsonl` with same split counts.
- Final training schema:
  - `prompt: string`, `essay: string`, `score: float64`
- Duplicate removal at this stage: exact dedup on `(prompt, essay, score)`; removed `0`.
- Filtering at this stage: none triggered (all required fields present and valid).

## Contradictions Found (and Why)

| Item | Reported | Actual files | Why it contradicts |
|---|---:|---:|---|
| `reports/final_dataset.md` final rows | `12,960` | `12,413` in `datasets/final/merged_all.jsonl` and split JSONLs | This report is from an older merge branch (timestamp earlier than current reproducible build outputs). |
| `reports/final_dataset.md` split counts | train `10,365`, val `1,291`, test `1,304` | train `9,940`, val `1,241`, test `1,232` | Same stale branch as above. |
| `datasets/final/dataset_dict` | total `12,960` | canonical final/training artifacts are `12,413` | `scripts/verify_final_dataset.py` reuses existing HF artifact when present; it does not overwrite stale `datasets/final/dataset_dict`. |

Additional note:
- I found no pipeline report that claims `15,557` examples. The value `15557` appears in data as an **essay ID**, not as a dataset-size total.

## Final Reconciled Totals (Canonical Current Branch)

- Final materialized dataset (`datasets/final/merged_all.jsonl`): **12,413**
- Final split JSONLs: **9,940 / 1,241 / 1,232**
- Training dataset (`datasets/training`): **12,413** total, same split counts
- Provenance rows (`datasets/final/provenance.parquet`): **12,413**

All core pipeline stage counts reconcile exactly on the current branch.
