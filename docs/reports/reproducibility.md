# Dataset Reproducibility Report

- Generated: `2026-07-09 09:49:47`
- One-command entry point: `make dataset-build`
- Total runtime (seconds): `16.99`
- Step results: PASS=9, WARN=1, FAIL=0

## Step Execution

| # | step | status | duration_s | details |
|---:|---|---|---:|---|
| 1 | verify raw datasets | PASS | 0.17 | files=8, rows=40720, malformed=0, failures=0 |
| 2 | ingest Hugging Face datasets | WARN | 1.02 | download=skipped (--skip-download) / build: status=ok; output={ "raw_root": "datasets/raw", "output_dir": "datasets/hf/dataset_dict", "split_counts": { "train": 12964, "validation": 0, "test": 0 }, "stats": { "files_scanned": 7, "files_processed": 7, "rows_seen": 40744, "rows_kept": 12964, "rows_dropped_missing_text": 19278, "rows_dropped_missing_score": 8487, "rows_dropped_bad_score": 15, "parse_errors": 0 } } Saving the dataset (0/1 shards): 0%/ / 0/12964 [00:00<?, ? examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 12964/12964 [00:00<00:00, 1938708.49 examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 12964/12964 [00:00<00:00, 1843843.92 examples/s] |
| 3 | normalize schemas | PASS | 2.04 | status=ok; output={ "datasets_root": "datasets", "jsonl_cases": 0, "structured_file_cases": 12, "hf_dataset_dict_cases": 1, "total_cases": 13, "combined_rows": 54566, "output_root": "datasets/processed/unified", "combined_output": "datasets/processed/unified/unified_all.jsonl", "report_path": "docs/reports/schema_mapping.md" } |
| 4 | compute quality scores | PASS | 1.54 | total=53388, kept=32493, removed=20895, threshold=60.0 |
| 5 | deduplicate | PASS | 1.05 | input=32493, deduped=12413, final=12413, split_counts={'train': 12413, 'validation': 0, 'test': 0} |
| 6 | verify licenses | PASS | 0.08 | sources=1, open_or_verified=False |
| 7 | generate provenance | PASS | 8.62 | status=ok; output={ "records": 144015, "input_rows": 144015, "required_missing_counts": { "original_dataset": 0, "original_identifier": 0, "preprocessing_history": 0, "split_assignment": 0, "source_url": 0, "license": 0 }, "output_parquet": "datasets/final/provenance.parquet", "report_path": "docs/reports/provenance.md" } /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.l1dcachesize'. Detail: [errno 1] Operation not permitted /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.l2cachesize'. Detail: [errno 1] Operation not permitted /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.l3cachesize'. Detail: [errno 1] Operation not permitted /Users/runner/work/crossbow/crossbow/arrow/cpp/src/arrow/util/cpu_info.cc:242: IOError: sysctlbyname failed for 'hw.optional.neon'. Detail: [errno 1] Operation not permitted |
| 8 | build training dataset | PASS | 1.01 | status=ok; output={ "output_dataset_dir": "datasets/training", "provenance_dir": "datasets/training_provenance", "report_path": "docs/reports/training_dataset.md", "train": 12413, "validation": 0, "test": 0, "load_ok": true } Saving the dataset (0/1 shards): 0%/ / 0/12413 [00:00<?, ? examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 12413/12413 [00:00<00:00, 2361709.94 examples/s] Saving the dataset (1/1 shards): 100%/██████████/ 12413/12413 [00:00<00:00, 2229335.26 examples/s] |
| 9 | verify final dataset | PASS | 1.26 | status=ok; output={ "report_path": "docs/reports/final_verification.md", "dataset_dir": "datasets/final", "hf_disk_path": "datasets/final/dataset_dict", "hf_ok": false, "id_overlap_train_test": 0, "text_overlap_train_test": 0, "prompt_overlap_train_test": 0 } Generating train split: 0 examples [00:00, ? examples/s] Generating train split: 12413 examples [00:00, 117294.31 examples/s] Generating train split: 12413 examples [00:00, 117020.92 examples/s] Generating validation split: 0 examples [00:00, ? examples/s] Generating validation split: 0 examples [00:00, ? examples/s] Generating test split: 0 examples [00:00, ? examples/s] Generating test split: 0 examples [00:00, ? examples/s] |
| 10 | generate reports (dataset cards) | PASS | 0.19 | status=ok; output={ "generated_cards": [ "/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/datasets/dataset_cards/asap_aes.md", "/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/datasets/dataset_cards/persuade2.md", "/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/datasets/dataset_cards/asap2.md" ], "output_dir": "/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/datasets/dataset_cards", "count": 3 } |

## Artifacts

### 1. verify raw datasets
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/raw_verification.md`

### 2. ingest Hugging Face datasets
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/outputs/data_ingestion/download_summary.json`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/hf/dataset_dict`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/hf/build_summary.json`

### 3. normalize schemas
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/processed/unified/unified_all.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/schema_mapping.md`

### 4. compute quality scores
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/quality_scored.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/quality_filtered.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/quality_removed.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/final_dataset_quality.md`

### 5. deduplicate
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/quality_deduped.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/deduplication.md`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/train.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/validation.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/test.jsonl`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/merged_all.jsonl`

### 6. verify licenses
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/license_verification.md`

### 7. generate provenance
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/provenance.parquet`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/provenance.md`

### 8. build training dataset
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/training`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/training_provenance`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/training_dataset.md`

### 9. verify final dataset
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/reports/final_verification.md`
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/datasets/final/dataset_dict`

### 10. generate reports (dataset cards)
- `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace/docs/datasets/dataset_cards`
