# Refactor Summary

- Timestamp: `2026-07-09 00:07:06 CDT`
- Scope: behavior-preserving repository refactor before first Git release.

## Files Moved

- Script implementations moved from `scripts/` into `src/` modules:
  - `src/data/*` for data pipeline scripts.
  - `src/evaluation/run_prompt_test.py` and `src/evaluation/run_baseline_eval.py`.
  - `src/inference/run_inference.py`.
  - `src/training/train_unsloth.py`.
- Script entrypoints in `scripts/` were converted to thin compatibility wrappers.
- Report artifacts were consolidated under `docs/reports/` and `docs/reports/archive/`.
- Evaluation config template was copied to `configs/evaluation/harness.example.json`.
- Training default config was copied to `configs/training/qlora_default.json`.

## Imports Changed

- Added wrapper forwarding so `scripts/*.py` continue exposing legacy module symbols for tests.
- Added shared path utilities in `src/utils/paths.py` and adopted them in moved modules that depend on repository root inference.
- Updated training config defaults in `training/run.py` to `configs/training/*` with legacy fallback to `training/configs/*`.

## Duplicate Modules Removed / Consolidated

- Consolidated repeated repo-root/path detection into `src/utils/paths.py`.
- Centralized script runtime behavior into `src/` modules while preserving `scripts/` CLI compatibility.
- Report path defaults standardized to `docs/reports/` in moved data pipeline modules.

## Scripts Simplified

- `28` files under `scripts/` now function as wrappers (import + forward + `main()`).
- Wrapper behavior preserves:
  - direct CLI execution,
  - old script import paths,
  - monkeypatch-based unit tests.

## Remaining Technical Debt

- `outputs/evaluation_harness/` (legacy output location) still exists from prior runs.
- HF roundtrip validation currently fails for `datasets/final/quality_filtered.jsonl` due heterogeneous nested metadata schema.
- Some historical docs still reference legacy output/report paths and should be harmonized in a follow-up doc pass.

## Future Cleanup Recommendations

1. Consolidate overlapping validation scripts (`verify_final_dataset` + `validate_hf_roundtrip`) under one subcommand-based entrypoint.
2. Normalize nested metadata schema in `quality_filtered.jsonl` to make all intermediate artifacts HF-roundtrip clean.
3. Remove empty/generated macOS/system artifacts (`.DS_Store`) and keep enforcement in pre-commit.
4. Migrate remaining reusable helpers from large pipeline modules into `src/utils/` incrementally.
