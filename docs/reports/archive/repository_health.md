# Repository Health

## Verification Matrix

| Check | Status | Notes |
|---|---|---|
| imports_basic | PASS | ok |
| lint_ruff | PASS | All checks passed! |
| format_black | PASS | Skipping .ipynb files as Jupyter dependencies are not installed. You can fix this by running ``pip install "black[jupyter]"`` All done! ✨ 🍰 ✨ 81 files would be left unchanged. |
| tests_pytest | PASS | ...................................                                      [100%] 35 passed in 0.78s |
| rebuild_dry_run | PASS |  |
| dataset_builder | PASS | {   "raw_root": "datasets/raw",   "output_dir": "/private/tmp/cogni_build_health",   "split_counts": {     "train": 12964,     "validation": 0,     "test": 0   },   "stats": {     ... |
| training_cli_import | PASS | usage: run.py [-h] [--config CONFIG] [--model-id MODEL_ID]               [--dataset-path DATASET_PATH] [--output-dir OUTPUT_DIR]               [--checkpoint-dir CHECKPOINT_DIR]    ... |
| evaluation_cli_import | PASS | usage: run_harness.py [-h] --base-model-id BASE_MODEL_ID                       --tuned-model-id TUNED_MODEL_ID                       [--dataset-path DATASET_PATH]                  ... |
| hf_compatibility_quick | PASS | ok |
| readme_links | PASS | {"missing": []} |
| expected_folders | PASS | {"missing": []} |

## Required Audit Items

- Imports: **PASS**
- Lint (`ruff`): **PASS**
- Formatting (`black --check`): **PASS** (notebooks skipped because `black[jupyter]` is not installed)
- Tests (`pytest`): **PASS** (`35 passed`)
- Rebuild script dry-run: **PASS**
- Dataset builder execution: **PASS**
- Hugging Face compatibility quick validation: **PASS** (load_from_disk + load_dataset + Arrow/Parquet roundtrip validated earlier in session)
- Training pipeline imports/CLI: **PASS**
- Evaluation imports/CLI: **PASS**
- README links: **PASS**
- Broken expected paths check: **PASS**

## Notes

- Full exhaustive `scripts/validate_hf_roundtrip.py` can be long-running on very large artifacts; quick HF compatibility checks were executed successfully for canonical datasets.
- Relative import normalization was applied in `src/evaluation` to avoid package-name collisions with top-level `evaluation/`.
