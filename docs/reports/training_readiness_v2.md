# Production Training Readiness v2

Date: 2026-07-09  
Scope: repository audit for production training readiness (no training executed in this audit)

## Overall Verdict

Production training is **not ready** to proceed yet.

Current gating blockers are:

1. Gold dataset v1 has zero approved rows.
2. SFT dataset exports are empty (0 train / 0 validation / 0 test).
3. Training execution is blocked on missing GPU and empty SFT data.

## Component Status Matrix

| Component | Status | Evidence | Blocker (if any) | Exit Criteria |
|---|---|---|---|---|
| Teacher pipeline | PARTIAL | `src/teacher/run_teacher_benchmark_execution.py`, `src/teacher/providers/*`, `src/teacher/validation.py`, `outputs/teacher_round1/round1_teacher_validation/summary.json` (`dry_run: true`), `outputs/teacher_runs/teacher-runs-smoke/summary.json` (`dry_run: true`) | None at code level; operational evidence is dry-run only | Run a non-dry benchmark on gold examples with real provider calls and persist validated outputs/cost/latency |
| Gold pipeline | BLOCKED | `src/data/build_gold_dataset.py`, `datasets/gold/v1/manifest.json`, `datasets/gold/v1/summary.md`, `datasets/review/final/` (README only) | **No approved reviewed examples to merge** (`approved_rows_seen: 0`, `gold_rows_written: 0`) | Populate `datasets/review/final/review_dataset.jsonl` with approved/edit decisions, then rebuild gold v1 |
| SFT pipeline | BLOCKED | `src/data/build_sft_dataset.py`, `src/teacher/generate_labels.py`, `datasets/sft/manifest.json`, `datasets/sft/build_report.md` | **Upstream gold is empty**, so SFT exports are empty (`export_train: 0`, `export_validation: 0`, `export_test: 0`) | Rebuild SFT after non-empty gold v1 is produced and passes validation |
| Training pipeline | BLOCKED | `src/training/train_experiment.py`, `configs/training/experiments/qlora_phase1_ofat_v1.json`, `outputs/training_runs/run_v1/run_v1/run_summary.json`, `outputs/experiments/20260709T175524Z-p1_baseline/manifest.json` | **Runtime failure:** `NotImplementedError: Unsloth cannot find any torch accelerator? You need a GPU.` plus empty SFT splits | Provide supported GPU runtime and non-empty SFT dataset, then rerun Phase 1 |
| Evaluation pipeline | PARTIAL | `src/evaluation/error_analysis.py`, `src/evaluation/calibration.py`, evaluation harness outputs under `outputs/evaluation_harness/*`, `docs/reports/model_v1_results.md` (explicit dry-run caveat) | Not blocked by missing code; blocked for meaningful production conclusions until real trained model artifacts exist | Re-run evaluation on successful fine-tuned model outputs and real teacher labels |
| Experiment tracking | READY | `src/utils/experiment_tracker.py`, tracked manifest at `outputs/experiments/20260709T175524Z-p1_baseline/manifest.json` with git, dataset checksum, GPU, runtime, status | None | Keep as system of record for all future teacher/training/eval runs |
| Dashboard | PARTIAL | `src/dashboard/build_dashboard.py`, `docs/reports/dashboard.md` generated successfully | No hard blocker; currently summarizes mostly dry-run/placeholder artifacts | Rebuild dashboard after live teacher + training + evaluation runs |
| Review system | PARTIAL | `src/review/server.py`, `src/review/merge_reviews.py`, `datasets/review/queue/*` present, `datasets/review/final/` missing merged outputs | No technical blocker; workflow not yet completed by reviewers | Complete review decisions and run merge to produce final reviewed dataset |
| Configs | READY | `configs/teacher/*`, `configs/training/*`, `configs/providers/providers_v1.json`, provider validator in `src/teacher/provider_config.py` | None in repository structure; environment secrets still required at runtime | Validate `.env` in target runtime before live execution |
| Tests | READY | `pytest -q` result: `47 passed in 0.63s`; coverage includes teacher/data/provider/benchmark modules under `tests/*` | None | Keep CI gate green; add integration tests for live-run mode when credentials are available |
| Documentation | PARTIAL | Extensive docs under `docs/reports/*`, architecture and workflow docs present | Some docs reflect dry-run state and older test counts (example: `docs/reports/end_to_end_validation.md` shows `43 passed`) | Refresh run-dependent reports after live benchmark/training cycle |

## Blocked Dependency List (Exact)

1. **Human-reviewed gold inputs are missing**  
   - Missing artifact: `datasets/review/final/review_dataset.jsonl`  
   - Effect: gold merge produces 0 rows.

2. **Gold v1 is empty**  
   - `datasets/gold/v1/manifest.json` shows `gold_rows_written: 0`.  
   - Effect: no supervised examples for SFT build.

3. **SFT splits are empty**  
   - `datasets/sft/manifest.json` shows zero exported rows for all splits.  
   - Effect: training has no usable examples.

4. **No GPU accelerator for Unsloth/QLoRA run**  
   - `outputs/training_runs/run_v1/run_v1/run_summary.json` and tracker manifest capture the accelerator error.  
   - Effect: training fails immediately.

## Immediate Readiness Order

1. Complete human review decisions and generate `datasets/review/final/review_dataset.jsonl`.
2. Rebuild `datasets/gold/v1/` and confirm non-zero `gold_rows_written`.
3. Rebuild `datasets/sft/` and confirm non-zero train/validation/test rows.
4. Run Phase 1 on GPU-enabled runtime.
5. Re-run evaluation and dashboard on real artifacts (not dry-run).
