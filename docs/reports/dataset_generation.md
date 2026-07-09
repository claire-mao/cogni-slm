# Production Dataset Generation Workflow

Implemented workflow orchestrator:

- `/Users/clairemao/Documents/cogni-slm/src/data/generate_production_dataset.py`

This workflow composes the requested pipeline:

1. teacher
2. validation
3. human review (optional)
4. gold merge
5. SFT export

No automatic execution is performed by this report.

## Pipeline Mapping

The orchestrator reuses existing modules:

- teacher + validation:
  - `teacher.generate_labels.run_pipeline`
- human review merge (optional):
  - `review.merge_reviews.merge_reviews`
- gold merge:
  - `data.build_gold_dataset.build_gold_dataset`
- SFT export:
  - `data.build_sft_dataset.build_sft_dataset`

## Automatic Dataset Versioning

The workflow automatically versions each dataset stage:

- validation datasets:
  - `datasets/validation/versions/validation_vN/`
- review-final datasets (when enabled):
  - `datasets/review/final/versions/review_final_vN/`
- gold datasets:
  - `datasets/gold/versions/gold_vN/` (via gold builder)
- SFT datasets:
  - `datasets/sft/versions/sft_vN/`

Each versioned root also gets/updates:

- `version_index.json` with `latest_version`

Workflow runs are versioned separately under:

- `outputs/dataset_generation/runs/<run_id>/manifest.json`
- latest pointer:
  - `outputs/dataset_generation/manifest.json`

## Stage Inputs and Outputs

### Teacher stage

- uses `--teacher-outputs-path` in `precomputed` mode (or mock mode)
- records teacher source metadata and checksum

### Validation stage

- runs generation pipeline with schema/quality/confidence filters
- writes canonical filtered dataset artifacts into versioned validation directory

### Human review stage (optional)

- when `--enable-human-review` is set:
  - merges latest review decisions into a versioned review-final directory
- otherwise:
  - uses `--approved-reviews-path` directly

### Gold merge stage

- builds versioned gold dataset from approved review examples
- attaches review metadata, adjudication history, and checksums

### SFT export stage

- builds versioned SFT datasets from gold input
- supports:
  - Alpaca
  - ShareGPT
  - ChatML
  - Hugging Face JSONL

## Checksums and Reproducibility

Run manifest includes checksums for:

- input dataset
- teacher outputs
- approved reviews
- gold dataset
- final SFT version directory

This enables reproducible traceability across the full workflow.

## CLI

```bash
python3 -m src.data.generate_production_dataset \
  --input-jsonl datasets/gold/gold_v1.jsonl \
  --teacher-outputs-path outputs/teacher_runs \
  --teacher-model-id gpt-5 \
  --inference-mode precomputed \
  --enable-human-review \
  --review-runs-root outputs/teacher_runs \
  --review-reviews-root datasets/review \
  --gold-root datasets/gold \
  --sft-root datasets/sft
```

## Key Options

- `--enable-human-review`: enable review merge stage
- `--validation-version`, `--review-version`, `--gold-version`, `--sft-version`:
  optional explicit versions
- `--export-formats`: comma-separated SFT export targets
- `--strict-source-split`: preserve source split labels for SFT output

## Guardrails

- The workflow only orchestrates data-processing stages.
- It does not call teacher model APIs by itself.
- It does not run unless explicitly invoked.
