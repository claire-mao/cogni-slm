# Evaluation Harness

Reusable base-vs-fine-tuned evaluation harness for essay scoring outputs.

## What it compares

- `score_accuracy`
- `quadratic_weighted_kappa`
- `MAE`
- `feedback_quality`

## Inputs

Each evaluation row must contain:

- `prompt`
- `essay`
- `score`

Use either:

- HF dataset directory (default: `datasets/training`, split default `validation`), or
- JSONL input file via `--input-jsonl`.

## Outputs

By default, each run writes to `outputs/evaluation/harness/<run_id>/`:

- `base_predictions.jsonl`
- `tuned_predictions.jsonl`
- `summary.json`
- `report.md`

## Usage

Dry-run smoke test:

```bash
python3 evaluation/run_harness.py \
  --base-model-id Qwen/Qwen3-0.6B \
  --tuned-model-id Qwen/Qwen3-1.7B-Instruct \
  --dataset-path datasets/training \
  --dataset-split validation \
  --max-examples 32 \
  --dry-run
```

Local model inference (offline/local files only):

```bash
python3 evaluation/run_harness.py \
  --base-model-id <base_model_id> \
  --tuned-model-id <tuned_model_id> \
  --dataset-path datasets/training \
  --dataset-split validation \
  --local-files-only
```

## Notes

- `feedback_quality` is heuristic and deterministic for reproducibility.
- QWK is computed on rounded ordinal scores.
- No network access is required when `--local-files-only` is set and models are cached locally.
