# Task Checklist

## Completed
- [x] Repository scaffold created (`src`, `configs`, `datasets`, `docs`, `notebooks`, `scripts`, `tests`, `models`, `outputs`)
- [x] Core project files present (`README.md`, `pyproject.toml`, `Makefile`, `LICENSE`, `.gitignore`)
- [x] Evaluation package scaffold exists under `src/evaluation/`
- [x] Evaluation design and dataset spec docs exist
- [x] Data generation pipeline modules exist under `src/data/`
- [x] Golden dataset snapshots exist under `datasets/processed/golden/`
- [x] Prompt-only baseline protocol doc exists (`docs/prompt_test.md`)
- [x] Prompt test runner exists (`scripts/run_prompt_test.py`)
- [x] Local inference script exists (`scripts/run_inference.py`)
- [x] Inference notebook exists (`notebooks/inference.ipynb`)
- [x] Inference output artifacts exist (`outputs/inference_demo/report.md`, `outputs/inference_demo/response.txt`)
- [x] CI workflow exists (`.github/workflows/ci.yml`)

## In Progress
- [ ] Held-out benchmark dataset population (`datasets/eval/heldout_benchmark.jsonl` is missing)
- [ ] Prompt-only official baseline execution on held-out benchmark
- [ ] Repository cleanup of generated run duplicates and obsolete `.gitkeep` files
- [ ] Broader automated tests beyond smoke test

## Not Started
- [ ] Fine-tuning pipeline implementation
- [ ] Full base-vs-tuned benchmark execution with calibrated thresholds
- [ ] Expanded unit/integration test suite for `src/data` and `src/evaluation`
- [ ] Formal release/versioning workflow for dataset snapshots and reports
