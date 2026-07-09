# Rebuild Pipeline Report

## Goal

Rebuild dataset artifacts reproducibly starting only from `datasets/raw/`.

## Isolation Strategy

- Repository root: `/Users/clairemao/Documents/cogni-slm`
- Raw input root: `/Users/clairemao/Documents/cogni-slm/datasets/raw`
- Isolated workspace: `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace`
- Workspace includes only:
  - `datasets/raw/`
  - `scripts/` (thin wrappers)
  - `src/`
  - `evaluation/`
  - `training/`
  - `datasets/build_dataset.py`
- All rebuild commands run inside this isolated workspace.

## Preprocessing Steps

1. Validate raw files (`csv/tsv/json/jsonl/txt`) exist under `datasets/raw/`.
2. Build Hugging Face staging dataset from raw files (`datasets/build_dataset.py`).
3. Normalize to unified schema (`scripts/normalize_unified_schema.py`).
4. Sanitize unified JSONL (drop malformed rows).
5. Compute quality scores and filter low-quality rows.
6. Deduplicate and materialize canonical `datasets/final/{train,validation,test}.jsonl` + merged file.
7. Verify licenses and write license report.
8. Build provenance index (`datasets/final/provenance.parquet`).
9. Build training dataset (`datasets/training`) and provenance sidecar.
10. Verify final dataset integrity and HF loadability.
11. Regenerate provenance repair report (`docs/reports/provenance_repair.md`).
12. Remove score/label keys from training provenance sidecar.
13. Generate metadata leakage report (`docs/reports/metadata_leakage.md`).
14. Generate prompt-group candidate split (`docs/reports/group_split.md`).
15. Sync rebuilt artifacts back to repository.

## Execution

- Mode: `execute`
- Total step runtime: `35.47` seconds

| step | status | duration_s | details |
|---|---|---:|---|
| prepare_workspace | PASS | 0.15 | raw_files=8 |
| build_dataset_pipeline | PASS | 18.94 | (no output) |
| rebuild_provenance_index | PASS | 10.05 | { "records": 156428, "input_rows": 156428, "required_missing_counts": { "original_dataset": 0, "original_identifier": 0, "preprocessing_history": 0, "split_assignment": 0, "source_url": 0, "license": 0 }, "output_parquet": "datasets/final/provenance.parquet", "report_path": "docs/reports/provenance_repair.md" } /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.l1dcachesize'. Detail: [errno 1] Operation not permitted /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.l2cachesize'. Detail: [errno 1] Operation not permitted /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.l3cachesize'. Detail: [errno 1] Operation not permitted /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.optional.neon'. Detail: [errno 1] Operation not permitted |
| rebuild_training_dataset | PASS | 0.95 | { "output_dataset_dir": "datasets/training", "provenance_dir": "datasets/training_provenance", "report_path": "docs/reports/training_dataset.md", "train": 9930, "validation": 1241, "test": 1242, "load_ok": true } Saving the dataset (0/1 shards): 0%/ / 0/9930 [00:00<?, ? examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 9930/9930 [00:00<00:00, 1907724.38 examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 9930/9930 [00:00<00:00, 1805820.27 examples/s] Saving the dataset (0/1 shards): 0%/ / 0/1241 [00:00<?, ? examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 1241/1241 [00:00<00:00, 463956.79 examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 1241/1241 [00:00<00:00, 428864.73 examples/s] Saving the dataset (0/1 shards): 0%/ / 0/1242 [00:00<?, ? examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 1242/1242 [00:00<00:00, 527152.96 examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 1242/1242 [00:00<00:00, 485310.75 examples/s] |
| build_prompt_group_candidate | PASS | 4.04 | { "output_dir": "datasets/training_candidates/prompt_group_split", "report_path": "docs/reports/group_split.md", "counts": { "train": 8943, "validation": 1706, "test": 1764 }, "prompt_to_split": { "1": "train", "2": "train", "3": "train", "4": "train", "5": "validation", "6": "test", "7": "train", "8": "train" } } |
| sanitize_training_provenance | PASS | 0.07 | files=3, rows=12413 |
| metadata_leakage_report | PASS | 0.06 | status=PASS; rows_scanned=12413 |
| sync_artifacts | PASS | 1.21 | copied=19, missing=0 |

## Artifact Sync

- Paths copied: `19`
- Missing paths: `0`

## Rebuild Command

```bash
python3 scripts/rebuild_all.py
```

Use `--dry-run` to preview without executing.
