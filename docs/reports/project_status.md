# Project Status

## Current Repository Statistics

- Python files: **81**
- Notebooks: **2**
- Reports (`docs/reports/*.md`): **41**
- Tests (`tests/test_*.py`): **10**
- Registered datasets: **14**
- Script entrypoints (`scripts/*.py`): **28**

## Folder Architecture Review

- Expected core folders are present: `datasets/raw`, `datasets/processed`, `datasets/final`, `datasets/training`, `datasets/teacher`, `training`, `evaluation`, `teacher_prompts`, `scripts`, `reports`, `tests`, `notebooks`, `outputs`, `configs`, `docs`.
- No high-risk directory moves were applied in this cleanup to avoid breaking existing imports/paths.
- Implemented organization improvements:
  - normalized `src/evaluation` imports to package-relative paths
  - centralized duplicated harness parsing helpers in `evaluation/harness_common.py`
  - expanded `.gitignore` to keep generated/cached artifacts out of Git
- Recommendation for next cleanup pass:
  - continue consolidating dataset and licensing notes under `docs/datasets/`.

## Dataset Statistics

| Dataset | Source | Size | License | Split Sizes | Score Range | Preprocessing Completed |
|---|---|---:|---|---|---|---|
| asap_aes_raw | ASAP-AES (Automated Student Assessment Prize) | 177.70 MB | Unverified in-repo; do not redistribute until explicitly confirmed | train:12964, validation:0, test:0 | n/a | Yes |
| asap2_raw | ASAP 2.0 (mirror candidate) | 0.00 B | CC-BY-NC-4.0 on mirror metadata (not present locally) | n/a | n/a | Yes |
| persuade2_raw | PERSUADE 2.0 / Feedback Prize corpus | 0.00 B | CC-BY-NC-SA-4.0 (official repo declaration; not present locally) | n/a | n/a | Yes |
| hf_staging_dataset | Derived from raw datasets via HF staging build | 15.63 MB | Inherits upstream source license constraints | train:12964 | 0.00 to 60.00 | Yes |
| processed_raw_essays | Normalized ingestion output from local raw essays folder | 0.00 B | Depends on ingested sources | n/a | n/a | Yes |
| normalized_asap_aes | Normalized ASAP-AES records | 63.77 MB | Unknown/unverified for redistribution in current repo | n/a | 0.00 to 60.00 | Yes |
| normalized_asap2 | Normalized ASAP 2.0 records | 0.00 B | CC-BY-NC-4.0 if sourced from listed HF mirror | n/a | n/a | Yes |
| normalized_persuade2 | Normalized PERSUADE 2.0 records | 0.00 B | CC-BY-NC-SA-4.0 if sourced from official repo | n/a | n/a | Yes |
| normalized_all_datasets | Merged normalized datasets | 63.77 MB | Mixed/inherited from source datasets | n/a | 0.00 to 60.00 | Yes |
| cogni_golden_dataset | Internal synthetic golden set for pipeline evaluation | 183.28 KB | Internal project artifact | n/a | n/a | Yes |
| heldout_benchmark_placeholder | Derived placeholder held-out benchmark from golden dataset | 23.42 KB | Internal project artifact | n/a | n/a | Yes |
| cogni_final_dataset | Final merged and deduplicated dataset for Cogni | 60.09 MB | Inherited from sources (currently unknown due ASAP-AES license uncertainty) | test:1232, train:9940, validation:1241 | 0.00 to 60.00 | Yes |
| cogni_training_dataset | Projected training DatasetDict (prompt, essay, score) | 15.13 MB | Inherited from final dataset source licenses | test:1232, train:9940, validation:1241 | 0.00 to 60.00 | Yes |
| cogni_training_builder | Parquet DatasetBuilder artifact + metadata sidecar | 12.46 MB | Inherited from final dataset source licenses | n/a | n/a | Yes |

## Training Readiness

Completed:
- [x] Training dataset exists (`datasets/training`) with split counts: train:9940, validation:1241, test:1232
- [x] Unsloth training scaffold implemented (`training/`, `scripts/train_unsloth.py`)
- [x] Prompt templates and teacher schema scaffolds implemented
Remaining:
- [ ] Final license clearance for public redistribution
- [ ] Final dataset QA sign-off for first production training run
- [ ] First controlled `--do-train` experiment execution and analysis

## Evaluation Readiness

Completed:
- [x] `src/evaluation` interfaces and module scaffolding implemented
- [x] Baseline/prompt-test scripts implemented
- [x] Reusable base-vs-tuned harness implemented under `evaluation/`
Remaining:
- [ ] Threshold calibration and formal gate tuning on frozen benchmark
- [ ] Final benchmark licensing/provenance sign-off

## Teacher Pipeline Readiness

- Teacher prompt design documentation exists (`docs/teacher_prompt.md`).
- Teacher generation script exists (`scripts/generate_training_dataset.py`).
- Local teacher inference runner exists (`scripts/run_teacher_inference.py`).
- Provider configuration and credential handling remain environment-dependent.

## Current Training Pipeline Status

- Import and CLI checks pass for `python -m training.run --help`.
- Pipeline initializes by default and does not train unless `--do-train` is provided.

## Current Evaluation Pipeline Status

- Import and CLI checks pass for `python -m evaluation.run_harness --help`.
- Dry-run harness executed successfully and produced comparison artifacts under `outputs/evaluation_harness/`.

## Current Reproducibility Status

- `scripts/rebuild_all.py --dry-run` executes successfully.
- `datasets/build_dataset.py` executes successfully in isolated temp output.
- Dataset snapshots are reproducible from available raw files, but legal redistribution remains pending for ASAP-AES artifacts.

## Current Licensing Status

- ASAP-AES license remains marked **unverified for redistribution** in repository documentation.
- ASAP2/PERSUADE2 folders exist but are currently empty in this environment.
- Derived datasets inherit source-license constraints and should be treated as local research artifacts until legal review is complete.
