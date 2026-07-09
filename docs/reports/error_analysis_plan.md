# Post-Training Error Analysis Plan

## Goal

Provide a reusable, offline framework to categorize and summarize post-training failures on
educational-assessment predictions without running model inference.

Implemented module:

- `/Users/clairemao/Documents/cogni-slm/src/evaluation/error_analysis.py`

## Error Categories

The framework analyzes:

- score errors
- rubric failures
- hallucinations
- fallacy misses
- reasoning failures

## Inputs

Required:

- Gold dataset JSONL (`--gold-path`, default: `datasets/gold/gold_v1.jsonl`)
- Prediction JSONL file or directory (`--predictions-path`)

Prediction loading and normalization rely on existing teacher IO contracts
(`teacher.io.load_predictions`) and validation logic (`teacher.validation.run_validation`).

## Analysis Logic

### 1) Score Errors

- Computes `abs(predicted_score - gold_score)` when both are available.
- Buckets each example:
  - `exact`
  - `off_by_1`
  - `off_by_2_to_threshold`
  - `severe`
  - `unavailable`
- Aggregates:
  - MAE
  - RMSE
  - exact-match rate
  - severe-error rate

### 2) Rubric Failures

- Uses validation outcome `hallucinated_rubric_items`.
- Counts rate per model and preserves issue notes per example.

### 3) Hallucinations

- Flags examples as hallucinations when either:
  - rubric hallucination exists, or
  - unsupported feedback is detected.
- Stores hallucination type tags for diagnostics.

### 4) Fallacy Misses

- Normalizes expected and predicted fallacy labels.
- Marks a miss when gold has at least one expected fallacy and predicted set has zero overlap.

### 5) Reasoning Failures

- Uses validation `reasoning_completeness`.
- Marks failure when below configurable threshold (`--reasoning-failure-threshold`, default `0.67`).

## Outputs

Generated in `--output-dir` (default: `outputs/error_analysis`):

- `error_analysis_records.jsonl` (per-example taxonomy records)
- `error_analysis_summary.json` (full structured summary)
- `error_analysis_model_summary.csv` (model-level aggregate table)
- `error_analysis_report.md` (readable report)

## CLI

```bash
python3 -m src.evaluation.error_analysis \
  --gold-path datasets/gold/gold_v1.jsonl \
  --predictions-path <predictions.jsonl-or-dir> \
  --output-dir outputs/error_analysis
```

## Guardrails

- No model generation or evaluation execution is performed by this deliverable.
- The framework only analyzes precomputed prediction artifacts.
