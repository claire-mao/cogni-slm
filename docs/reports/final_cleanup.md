# Final Cleanup Report

## Files Moved

- Implementations moved from `scripts/` into `src/`:
  - `src/data/*.py`
  - `src/evaluation/run_prompt_test.py`
  - `src/evaluation/run_baseline_eval.py`
  - `src/inference/run_inference.py`
  - `src/training/train_unsloth.py`
- Script wrappers kept in place under `scripts/` for backward compatibility.
- Cleanup/meta reports consolidated into `docs/reports/` and `docs/reports/archive/`.

## Files Archived

Archived one-time reports under `docs/reports/archive/` including:

- `delete_candidates.md`
- `script_cleanup.md`
- historical verification/analysis one-offs

## Delete Candidates

See `docs/reports/delete_candidates.md`.

## New Architecture Highlights

- Canonical config roots:
  - `configs/dataset/`
  - `configs/evaluation/`
  - `configs/teacher/`
  - `configs/training/`
- Canonical report root: `docs/reports/`
- Canonical new evaluation outputs: `outputs/evaluation/`
- Shared path logic centralized in `src/utils/paths.py`

## Remaining Technical Debt

1. `quality_filtered.jsonl` fails HF roundtrip casting due nested metadata shape drift.
2. Legacy output directory `outputs/evaluation_harness/` exists from prior runs.
3. A few historical docs still mention legacy report/output paths.

## Future Work

1. Merge overlapping validation scripts into one command with submodes.
2. Normalize metadata schema for all intermediate final artifacts.
3. Add cleanup target for `.DS_Store` and stale caches.
