# Cogni-SLM

Cogni-SLM is a local-first ML repository for AP-style educational assessment workflows: dataset acquisition and normalization, quality/traceability checks, teacher-generation scaffolds, training initialization, and base-vs-tuned evaluation.

## Repository Layout

```text
configs/
  dataset/
  evaluation/
  teacher/
  training/
datasets/
  raw/
  processed/
  final/
  training/
  teacher/
  private/
docs/
  architecture.md
  rebuild.md
  datasets/
  reports/
    archive/
evaluation/
models/
  base/
  adapters/
  merged/
  checkpoints/
notebooks/
outputs/
  evaluation/
  experiments/
  logs/
  rebuild/
scripts/                Backward-compatible thin CLI wrappers
src/
  data/
  evaluation/
  inference/
  training/
  utils/
tests/
training/
teacher_prompts/
```

## Installation

1. Create a Python 3.10+ environment.
2. Install dependencies:

```bash
make setup
```

## Quickstart

Run lint/tests:

```bash
ruff check .
black --check .
pytest -q
```

Run dry-run dataset orchestration:

```bash
python scripts/build_dataset.py --dry-run
python scripts/rebuild_all.py --dry-run
```

Run one inference:

```bash
python scripts/run_inference.py --help
```

## Pipelines

### Dataset Pipeline

Primary sequence:

1. `scripts/download_datasets.py`
2. `scripts/ingest_raw_essays.py`
3. `scripts/normalize_unified_schema.py`
4. `scripts/score_dataset_quality.py`
5. `scripts/deduplicate_dataset.py`
6. `scripts/split_dataset.py`
7. `scripts/build_training_dataset.py`
8. `scripts/verify_final_dataset.py`

### Teacher Pipeline

- Prompt templates: `teacher_prompts/`
- Generation scaffold: `scripts/generate_training_dataset.py`
- Local teacher inference: `scripts/run_teacher_inference.py`

### Training Pipeline

- Runtime entrypoint: `python -m training.run`
- Default config: `configs/training/qlora_default.json`
- Legacy fallback remains supported: `training/configs/qlora_default.json`

### Evaluation Pipeline

- Core interfaces: `src/evaluation/`
- Harness: `python -m evaluation.run_harness`
- Prompt/baseline scripts:
  - `scripts/run_prompt_test.py`
  - `scripts/run_baseline_eval.py`

## Reproducibility

- Architecture and stage graph: `docs/architecture.md`
- Rebuild process: `docs/rebuild.md`
- Active reports: `docs/reports/`
- Archived one-time reports: `docs/reports/archive/`
- Dataset documentation and cards: `docs/datasets/`

## Current Status

This repository is refactored for first Git release with behavior-preserving script wrappers and `src/`-hosted implementations. Run `docs/reports/functionality_matrix.md` and `docs/reports/regression_test.md` for verification status.
