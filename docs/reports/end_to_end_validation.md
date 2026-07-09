# End-to-End Dry-Run Validation Report

Date: 2026-07-09
Repository: `/Users/clairemao/Documents/cogni-slm`
Mode: offline dry-run only (no external API calls, no model training)

## Scope
Validated the full pipeline path:

`datasets/raw/ -> processed -> teacher outputs (mock) -> validation -> SFT dataset -> training planning -> evaluation planning -> dashboard`

Also ran the full test suite after fixes.

## Validation Summary

- Pipeline status: completed in dry-run/mock mode.
- External APIs called: no.
- Training executed: no.
- Tests: `43 passed`.

## Stage Results

1. Raw -> Processed
- Command:
  - `python3 scripts/build_dataset.py --workspace-root . --skip-download --dry-run --report-path outputs/e2e_validation/reports/build_dataset_dryrun.md`
  - `python3 -m src.data.ingest_raw_essays --raw-dir datasets/raw --output-jsonl outputs/e2e_validation/processed/raw_essays.jsonl --report-path outputs/e2e_validation/reports/ingest_raw_essays.md --min-words 40`
- Result:
  - Dry-run pipeline plan printed successfully.
  - Ingestion succeeded with `20551` accepted and `897` rejected (`essay_too_short`).
  - Processed artifact: `outputs/e2e_validation/processed/raw_essays.jsonl`.

2. Processed -> Evaluation Slice
- Result:
  - Small manually reviewable dry-run slice created: `outputs/e2e_validation/processed/eval_examples.jsonl`.
  - Row count: `6`.

3. Teacher Outputs (Mock)
- Command:
  - `python3 -m src.teacher.run_teacher_experiments ... --run-id e2e-teacher-dryrun6b --max-examples 6 --seeds 11 --temperatures 0.0 --dry-run`
- Result:
  - Responses generated in dry-run mode.
  - `outputs/e2e_validation/teacher_runs/e2e-teacher-dryrun6b/responses.jsonl`
  - `total_requests=210`, `successful_requests=210`, `failed_requests=0`.

4. Validation + Quality + Schema + Confidence Filters
- Command:
  - `python3 -m src.teacher.generate_labels --input-jsonl outputs/e2e_validation/processed/eval_examples.jsonl --output-root outputs/e2e_validation/validation --teacher-model-id gpt-5 --inference-mode precomputed --predictions-path outputs/e2e_validation/teacher_runs/e2e-teacher-dryrun6b/responses.jsonl --schema-path teacher_prompts/output_schema.json --quality-threshold 0.1 --confidence-threshold 0.1`
- Result (`outputs/e2e_validation/validation/manifest.json`):
  - `input_examples=6`
  - `after_validation=6`
  - `after_quality_filter=6`
  - `after_schema_validation=6`
  - `after_confidence_filter=6`
  - export splits: train `4`, test `2`, validation `0`.

5. SFT Dataset Build
- Command:
  - `python3 -m src.data.build_sft_dataset --input-jsonl outputs/e2e_validation/processed/eval_examples.jsonl --teacher-outputs-path outputs/e2e_validation/teacher_runs/e2e-teacher-dryrun6b/responses.jsonl --output-root outputs/e2e_validation/sft --teacher-model-id gpt-5 --inference-mode precomputed --schema-path teacher_prompts/output_schema.json --quality-threshold 0.1 --confidence-threshold 0.1 --export-formats alpaca,sharegpt,chatml,huggingface`
- Result:
  - Canonical SFT plus all 4 export formats produced.
  - Split counts: train `4`, test `2`, validation `0`.

6. Training Planning (No Train)
- Command:
  - `python3 -m src.training.train_experiment --dataset-root outputs/e2e_validation/sft --experiments-dir configs/training/experiments --manifest-path configs/training/experiments/manifest.json --base-config configs/training/qlora_default.json --output-root outputs/e2e_validation/training_experiments --tracking-root outputs/experiments --phase-id phase1_ofat_screening --max-runs 2 --seed-mode base`
- Result (`run_summary.json`):
  - `runs_requested=2`
  - `runs_planned=2`
  - `runs_completed=0`
  - `runs_failed=0`
  - tracker folders created under `outputs/experiments/`.

7. Evaluation Planning (Offline Artifacts)
- Commands:
  - `python3 -m src.teacher.run_benchmark --gold-path outputs/e2e_validation/processed/eval_examples.jsonl --predictions-path outputs/e2e_validation/teacher_runs/e2e-teacher-dryrun6b/responses.jsonl --output-root outputs/e2e_validation/teacher_benchmark --run-id e2e-benchmark`
  - `python3 -m src.evaluation.calibration ... --output-dir outputs/e2e_validation/evaluation/calibration --bins 5 --target-mode score_only`
  - `python3 -m src.evaluation.error_analysis ... --output-dir outputs/e2e_validation/evaluation/error_analysis --top-k-examples 5`
- Result:
  - Benchmark artifacts produced (`leaderboard`, agreement/cost/latency tables).
  - Calibration artifacts produced (`bins=5`, `records=210`, `model_summaries=5`).
  - Error-analysis artifacts produced (`total_predictions=210`, `unmatched_gold_examples=0`, `model_summaries=5`).

8. Dashboard
- Command:
  - `python3 -m src.dashboard.build_dashboard --repo-root . --teacher-runs-root outputs/e2e_validation/teacher_runs --teacher-leaderboard-json outputs/e2e_validation/teacher_benchmark/e2e-benchmark/leaderboard.json --training-experiments-root outputs/e2e_validation/training_experiments --experiments-root outputs/experiments --evaluation-root outputs/e2e_validation/evaluation --error-analysis-root outputs/e2e_validation/evaluation/error_analysis --report-path outputs/e2e_validation/reports/dashboard.md`
- Result:
  - Dashboard successfully generated at `outputs/e2e_validation/reports/dashboard.md`.

9. Tests (after fixes)
- Command:
  - `pytest`
- Result:
  - `43 passed`, `0 failed`.

## Broken Dependencies Found and Fixed

1. Circular import in teacher benchmark stack
- Symptom: teacher CLIs failed to import due to calibration dependency cycle.
- Fix: removed direct dependency on `evaluation.calibration` inside `src/teacher/benchmark.py` and implemented local calibration helpers there.
- Files updated:
  - `src/teacher/benchmark.py`

2. Mock teacher output schema mismatch
- Symptom: dry-run responses failed downstream schema validation.
- Fixes:
  - Made dry-run response payload conform to teacher output schema.
  - Allowed label generator to parse both `raw_json_output` and `raw_response_text`.
- Files updated:
  - `src/teacher/run_teacher_experiments.py`
  - `src/teacher/generate_labels.py`

3. Evaluation CLI import-path breakage
- Symptom: `python3 -m src.evaluation.run_baseline_eval --help` and `run_prompt_test --help` raised `ModuleNotFoundError: evaluation.benchmark`.
- Fix: added dual import strategy (`src.evaluation.*` first, fallback to `evaluation.*`).
- Files updated:
  - `src/evaluation/run_baseline_eval.py`
  - `src/evaluation/run_prompt_test.py`

4. Dashboard leaderboard JSON-shape incompatibility
- Symptom: dashboard crashed with `ValueError: Expected JSON object ... leaderboard.json` when benchmark emitted top-level array.
- Fixes:
  - allowed leaderboard loader to accept either object-with-`leaderboard` or top-level list.
  - relaxed generic JSON loader used by dashboard to support non-object payloads where appropriate.
- File updated:
  - `src/dashboard/build_dashboard.py`

5. Dashboard leaderboard field-name mismatch
- Symptom: leaderboard rows rendered `n/a` for model/qwk/mae/latency/cost because benchmark uses keys like `model_id`, `score_prediction_qwk`, etc.
- Fix: added fallback key mapping in dashboard renderer.
- File updated:
  - `src/dashboard/build_dashboard.py`

## Remaining Issues / Notes

1. `build_dataset.py --dry-run --report-path ...` did not create `outputs/e2e_validation/reports/build_dataset_dryrun.md`; only the step plan was printed.
- Impact: non-blocking for pipeline execution; reporting artifact missing for this stage.

2. Runtime warning seen when launching some modules with `python -m`:
- `RuntimeWarning: ... found in sys.modules after import of package ...`
- Impact: non-blocking; commands completed successfully.

3. This validation used mock/dry-run outputs, so quality metrics are infrastructure checks, not model-quality conclusions.

## Key Output Artifacts

- Raw ingestion report:
  - `outputs/e2e_validation/reports/ingest_raw_essays.md`
- Processed data:
  - `outputs/e2e_validation/processed/raw_essays.jsonl`
  - `outputs/e2e_validation/processed/eval_examples.jsonl`
- Teacher dry-run outputs:
  - `outputs/e2e_validation/teacher_runs/e2e-teacher-dryrun6b/responses.jsonl`
  - `outputs/e2e_validation/teacher_runs/e2e-teacher-dryrun6b/summary.json`
- Validation outputs:
  - `outputs/e2e_validation/validation/manifest.json`
- SFT outputs:
  - `outputs/e2e_validation/sft/`
- Training planning outputs:
  - `outputs/e2e_validation/training_experiments/train-exp-20260709T171817Z/run_summary.json`
- Evaluation planning outputs:
  - `outputs/e2e_validation/teacher_benchmark/e2e-benchmark/`
  - `outputs/e2e_validation/evaluation/calibration/`
  - `outputs/e2e_validation/evaluation/error_analysis/`
- Dashboard:
  - `outputs/e2e_validation/reports/dashboard.md`

## Conclusion

The complete dry-run validation path is operational end-to-end with local/mock execution, all discovered import/path/config compatibility issues were fixed where feasible, and the repository test suite passes in full.
