# Repository Audit

Date: 2026-07-08

## Scope
- Full repository layout scan (files and folders).
- Static checks for Python/notebook syntax and style.
- Sanity checks for script entrypoints and expected deliverables.
- Git readiness and ignore-policy review.

## Current Directory Tree
```text
cogni-slm/
├── .env.example
├── .github/workflows/ci.yml
├── .gitignore
├── .pre-commit-config.yaml
├── DEVELOPMENT.md
├── LICENSE
├── Makefile
├── README.md
├── configs/
│   ├── .gitkeep
│   └── prompts/
│       ├── self_critique_prompts.md
│       └── teacher_prompts.md
├── datasets/
│   ├── eval/
│   │   └── .gitkeep
│   ├── processed/
│   │   ├── .gitkeep
│   │   └── golden/
│   │       ├── golden-20260708T183049Z/
│   │       │   ├── audit_traces.jsonl
│   │       │   ├── dataset.jsonl
│   │       │   └── manifest.json
│   │       └── golden-20260708T202613Z/
│   │           ├── audit_traces.jsonl
│   │           ├── dataset.jsonl
│   │           └── manifest.json
│   └── raw/
│       └── .gitkeep
├── docs/
│   ├── .gitkeep
│   ├── architecture.mmd
│   ├── behavior_spec.md
│   ├── data_generation.md
│   ├── dataset_spec.md
│   ├── evaluation_design.md
│   ├── experiment_plan.md
│   ├── literature_review.md
│   ├── problem.md
│   ├── project_architecture.md
│   ├── project_board.md
│   ├── prompt_test.md
│   └── roadmap.md
├── models/
│   └── .gitkeep
├── notebooks/
│   ├── .gitkeep
│   └── inference.ipynb
├── outputs/
│   ├── .gitkeep
│   └── inference_demo/
│       ├── report.md
│       └── response.txt
├── pyproject.toml
├── scripts/
│   ├── .gitkeep
│   ├── generate_golden_dataset.py
│   ├── run_inference.py
│   └── run_prompt_test.py
├── src/
│   ├── .gitkeep
│   ├── data/
│   │   ├── __init__.py
│   │   ├── deduplicate.py
│   │   ├── export.py
│   │   ├── filter.py
│   │   ├── generate.py
│   │   ├── prompts.py
│   │   ├── schemas.py
│   │   ├── teacher.py
│   │   └── validate.py
│   └── evaluation/
│       ├── __init__.py
│       ├── benchmark.py
│       ├── deterministic_checks.py
│       ├── evaluator.py
│       ├── llm_judge.py
│       ├── metrics.py
│       └── report.py
└── tests/
    ├── .gitkeep
    └── test_smoke.py
```

## Missing Files
- `datasets/eval/heldout_benchmark.jsonl` is missing.
  - Impact: `scripts/run_prompt_test.py` cannot run official held-out baseline without this file.
- No additional required top-level project folders are missing (`scripts/`, `src/`, `tests/`, `outputs/`, `docs/`, `notebooks/` are present).

## Unexpected Files
- Local system/generated artifacts present in workspace:
  - `.DS_Store`
  - `.pytest_cache/`
  - `.ruff_cache/`
  - `src/cogni_slm.egg-info/`
  - `src/**/__pycache__/`
  - `tests/__pycache__/`
- Multiple generated golden dataset run folders under `datasets/processed/golden/`:
  - `golden-20260708T183049Z`
  - `golden-20260708T202613Z`
  - This is valid for run-history, but creates duplication and larger repo footprint if both are committed.

## Suggested Moves
- Move stale run snapshots you do not intend to version long-term from `datasets/processed/golden/*` to an archival or external storage location.
- If you want reproducible examples in-repo, keep one canonical golden snapshot and move others to `outputs/` or off-repo archive.

## Suggested Deletions (Non-Destructive Recommendation Only)
- Remove obsolete `.gitkeep` files in directories that now have real content:
  - `docs/.gitkeep`
  - `scripts/.gitkeep`
  - `notebooks/.gitkeep`
  - `tests/.gitkeep`
  - `configs/.gitkeep`
  - `src/.gitkeep`
- Remove local OS/cache artifacts from working tree:
  - `.DS_Store`
  - `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, `*.egg-info/` (already ignored).

## Suggested Renames
- Optional naming alignment only:
  - `scripts/run_inference.py` uses `DEFAULT_MODEL_ID = "Qwen/Qwen3-0.6B"` while project docs/reference model are mostly `Qwen/Qwen3-1.7B-Instruct`.
  - Either:
    - keep as-is and update docs to explicitly call out a local lightweight default, or
    - change default model constant to align with documented baseline model.

## Code/Path/Import Findings
- Static lint check: passing after safe cleanup (`ruff check .` passed).
- Unit tests: passing (`pytest` smoke test).
- Script entrypoints parse correctly with `--help`.
- Potential fragility:
  - Scripts import `data` / `evaluation` as installed packages.
  - Works in editable-install environments; can fail in fresh environments if project is not installed with `pip install -e .`.

## Safe Refactors Applied
- `notebooks/inference.ipynb`
  - Fixed malformed escaped code content so notebook cells are valid Python.
  - Preserved notebook behavior and output intent.
- `scripts/run_inference.py`
  - Formatting/type-signature cleanup only.
  - No CLI/behavior/output contract changes.

## Project Structure Verification
- Expected folders are present:
  - `scripts/`
  - `src/`
  - `tests/`
  - `outputs/`
  - `docs/`
  - `notebooks/`
- No required folder from current architecture docs is missing.

## Deliverables Verification
- `scripts/run_inference.py`: present
- `outputs/inference_demo/report.md`: present
- `outputs/inference_demo/response.txt`: present

## Git Readiness

### Modified Tracked Files
- `.gitignore`
- `Makefile`
- `README.md`
- `pyproject.toml`

### Untracked Files/Folders
- `.github/`
- `.pre-commit-config.yaml`
- `DEVELOPMENT.md`
- `configs/prompts/`
- `datasets/processed/golden/`
- `docs/*.md` (multiple)
- `notebooks/inference.ipynb`
- `scripts/generate_golden_dataset.py`
- `scripts/run_inference.py`
- `scripts/run_prompt_test.py`
- `src/data/`
- `src/evaluation/`
- `tests/test_smoke.py`

### Ignored Generated Files (Current)
- `.DS_Store`
- `.pytest_cache/`
- `.ruff_cache/`
- `outputs/inference_demo/`
- `src/cogni_slm.egg-info/`
- `src/**/__pycache__/`
- `tests/__pycache__/`

## .gitignore Recommendations
- Keep current `outputs/*` ignore unless inference artifacts should be tracked intentionally.
- Add explicit patterns if you want stricter coverage for hidden macOS metadata and notebook noise:
  - `.DS_Store?`
  - `**/.DS_Store`
- If golden datasets are intended as generated artifacts (not source assets), consider:
  - ignore `datasets/processed/golden/*` and whitelist only one canonical snapshot.
