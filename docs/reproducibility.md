# Reproducibility Audit (Raw-Only Rebuild)

Date: 2026-07-08

## Scope

Goal: verify whether the repository can be rebuilt from scratch **starting only from `datasets/raw/`**.

I intentionally did not assume any existing `datasets/processed/`, `datasets/final/`, `datasets/training/`, or prior reports.

## Verification Method

I executed the end-to-end build in an isolated scratch workspace containing:

- `datasets/raw/` (copied from repository)
- `scripts/` and `datasets/build_dataset.py`
- empty downstream directories

Command used (scratch):

```bash
python3 scripts/build_dataset.py --workspace-root /private/tmp/cogni_repro_check --skip-download --report-path /private/tmp/cogni_repro_check/reports/reproducibility_check.md
```

## Result Summary

**Conclusion: No, every downstream artifact is not currently reproducible from `datasets/raw/` alone.**

The pipeline partially rebuilt artifacts, but failed before completion and did not regenerate several committed outputs.

### Observed isolated run status

- Step results: PASS=6, WARN=1, FAIL=1
- Failure step: **Step 8 (`build training dataset`)**
- Failure mode: `build_training_dataset.py` crashes when one or more splits are empty (HF `Dataset.from_list(..., features=...)` mismatch on empty rows).

### Split mismatch vs current repository

- Current repository final splits:
  - train: `9940`
  - validation: `1241`
  - test: `1232`
- Raw-only isolated rebuild splits:
  - train: `12413`
  - validation: `0`
  - test: `0`

This means the current canonical split artifacts are **not reproducible from raw-only rebuild with current scripts/config defaults**.

## Missing Scripts / Unrebuildable Artifacts

The following downstream artifacts are present in the repository but have no clear reproducible generator path in the current automated raw-only build:

1. `datasets/final/manifest.json` (not produced by `scripts/build_dataset.py`)
2. `datasets/dataset_registry.json` (no generator in automated rebuild path)
3. `datasets/training_builder/` parquet + metadata outputs (no rebuild step in main pipeline)
4. Many reports under `docs/reports/` are not wired to a script default output path (appear one-off/manual).

Examples of report files without direct scripted regeneration in the current build flow:

- `docs/reports/dataset_lineage.md`
- `docs/reports/full_pipeline_audit.md`
- `docs/reports/license_audit.md`
- `docs/reports/leakage_report.md`
- `docs/reports/schema_validation.md`
- `docs/reports/training_readiness.md`

## Undocumented / Implicit Preprocessing

These behaviors materially affect outputs but are not fully documented in one canonical rebuild guide:

1. `scripts/normalize_unified_schema.py` scans broad `datasets/` trees (not only raw), so outputs depend on what derived files already exist.
2. `scripts/build_dataset.py` uses internal fast-quality and dedup logic (`compute_quality_scores_fast`, `deduplicate_quality_filtered`) that differs from standalone scripts and is not clearly documented as canonical vs non-canonical.
3. License verification step can report PASS even when `open_or_verified=False` (status semantics mismatch).
4. Current README dataset section documents a different script sequence (teacher-generation pipeline), not the same as the `make dataset-build` raw-to-training flow.

## Manual Steps Required

Even with scripts present, reproducibility still depends on manual/operator actions:

1. If `datasets/raw/` is absent/incomplete: dataset acquisition may require manual acceptance/authentication (Kaggle/gated sources).
2. Environment setup: core runtime dependencies used by dataset scripts (`datasets`, `pandas`, `huggingface_hub`, etc.) are not declared in base `pyproject.toml` dependencies.
3. Some reports and registry/manifest artifacts require manual regeneration workflow (no single scripted path today).

## Non-Deterministic or Environment-Dependent Operations

1. Timestamped outputs in multiple scripts (`datetime.now(...)`) change run-to-run metadata.
2. Optional algorithm branches change behavior by environment (for example embedding-based dedup vs text fallback in `scripts/deduplicate_dataset.py`).
3. File-system state dependence: normalization discovers whatever exists under `datasets/`, so prior derived artifacts can alter current run outputs.
4. Network/dataset-host dependence when running download steps (when not using `--skip-download`).

## Final Determination

From `datasets/raw/` alone, the repository can regenerate **some** downstream artifacts, but **cannot reliably regenerate all committed downstream artifacts** in a deterministic, single-pass, raw-only rebuild today.

Primary blockers:

1. Training dataset build failure on empty eval splits.
2. Missing scripted generation for key artifacts (manifest/registry/training_builder and many reports).
3. Pipeline output dependence on existing derived files and environment-specific behavior.
