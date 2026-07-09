# Dataset Statistics

## Scope

This report summarizes the current canonical training dataset artifacts:

- `datasets/final/{train,validation,test}.jsonl`
- `datasets/training` (HF DatasetDict)

## Split Sizes

- train: **9,940**
- validation: **1,241**
- test: **1,232**
- total: **12,413**

## Score Range

- observed minimum: **0.0**
- observed maximum: **60.0**
- median (all splits): **3.0**
- distribution is right-skewed and imbalanced toward lower bands.

## Coverage Snapshot

- source datasets represented in canonical final splits: **asap_aes only**
- prompt IDs observed: **1-8**
- primary task: **essay_scoring**

## Figures

Figures are available in [docs/reports/figures](/Users/clairemao/Documents/cogni-slm/docs/reports/figures):

- `examples_per_dataset.png`
- `examples_per_split.png`
- `essay_length_distribution.png`
- `score_histogram_overall.png`
- `score_histogram_by_split.png`
- `prompt_distribution.png`
- `language_distribution.png`

## Notes

- This file is intentionally concise and serves as the retained canonical statistics summary.
- Detailed exploratory/one-off analyses were archived under `docs/reports/archive/`.
