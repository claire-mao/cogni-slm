# Confidence Calibration Implementation

Implemented:

- `/Users/clairemao/Documents/cogni-slm/src/evaluation/calibration.py`

Scope:

- Analyzes precomputed prediction outputs only.
- Does not run inference or evaluate live models.

## Supported Methods

1. Expected Calibration Error (ECE)

- Implemented with configurable bin count (`--bins`, default `10`).
- Uses reliability bins with weighted absolute gap between confidence and target.

2. Reliability diagrams

- Produces per-model bin statistics:
  - bin range
  - count
  - average confidence
  - average target
  - absolute gap
- Exports both machine-readable JSON and lightweight SVG diagrams.

3. Brier Score

- Computes mean squared error between confidence and target:
  - before temperature scaling
  - after temperature scaling

4. Temperature scaling

- Applies binary-style calibration transform:
  - `p_scaled = sigmoid(logit(p) / T)`
- Fits temperature `T` via deterministic grid search minimizing NLL.
- Reports NLL before/after and overconfidence rate before/after.

## Calibration Target Modes

Configurable by `--target-mode`:

- `score_only`: target is `1` when score error is within tolerance (`--score-tolerance`, default `1.0`)
- `fallacy_only`: target is `1` when predicted fallacies overlap gold fallacies
- `score_and_fallacy` (default): target is mean of available score and fallacy targets

## Inputs

- Gold dataset JSONL (`--gold-path`, default: `datasets/gold/gold_v1.jsonl`)
- Prediction JSONL file or directory (`--predictions-path`)

Input loading uses existing repository IO:

- `teacher.io.load_gold_examples`
- `teacher.io.load_predictions`

## Outputs

Generated under `--output-dir` (default: `outputs/calibration`):

- `calibration_records.jsonl`
- `calibration_summary.json`
- `calibration_model_summary.csv`
- `calibration_report.md`
- `reliability_diagrams/<model>.json`
- `reliability_diagrams/<model>_before.svg`
- `reliability_diagrams/<model>_after.svg`

## CLI Usage

```bash
python3 -m src.evaluation.calibration \
  --gold-path datasets/gold/gold_v1.jsonl \
  --predictions-path outputs/teacher_runs \
  --output-dir outputs/calibration \
  --bins 10 \
  --target-mode score_and_fallacy
```

## Notes

- The implementation is deterministic for fixed inputs and configuration.
- It is designed for repeatable offline calibration analysis before any dataset relabeling decisions.
