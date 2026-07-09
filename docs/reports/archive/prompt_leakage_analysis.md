# Prompt Leakage Analysis

- Dataset directory: `/Users/clairemao/Documents/cogni-slm/datasets/final`
- Total examples analyzed: `12960`
- Unique prompts: `8`

## Exact Prompt Overlap

- `train ∩ validation`: `8` prompts
- `train ∩ test`: `8` prompts
- `validation ∩ test`: `8` prompts

| prompt | train | validation | test | split_count |
|---|---:|---:|---:|---:|
| `1` | 1436 | 172 | 174 | 3 |
| `2` | 1446 | 177 | 177 | 3 |
| `3` | 1376 | 179 | 166 | 3 |
| `4` | 1380 | 171 | 214 | 3 |
| `5` | 1448 | 191 | 166 | 3 |
| `6` | 1461 | 173 | 166 | 3 |
| `7` | 1240 | 161 | 163 | 3 |
| `8` | 578 | 67 | 78 | 3 |

## Paraphrased Prompt Overlap

Prompt values are ID-like (mostly numeric), so paraphrase detection on prompt text is not meaningful with the current split files.

## Prompt-Family Leakage Into Evaluation

Prompts appearing in multiple splits: `8/8`.
This indicates essays from the same prompt family are present in both training and evaluation splits.

## Recommendation

Recommended strategy: **prompt-group disjoint split** (no prompt appears in more than one split).

Suggested assignment (optimized for size + score-distribution preservation):

- train prompts: `['1', '2', '3', '4', '7', '8']`
- validation prompts: `['5']`
- test prompts: `['6']`

- Expected counts: train=`9355`, validation=`1805`, test=`1800`
- Size deviation objective: `0.155864`
- Score-distribution divergence objective: `0.136257`
- Combined objective: `0.564636`

Why this strategy:
- Prevents exact and prompt-family leakage by construction.
- Preserves score distributions better than arbitrary prompt holdout by optimizing divergence.
- Keeps evaluation prompts unseen during training, which is the correct generalization test.

## Operational Guidance (No Rewrite Performed)

- Keep current files unchanged for now (this report is analysis only).
- If you proceed, rebuild splits by grouping on prompt ID first, then assigning prompt groups to train/validation/test using the recommended partition.
- After re-splitting, rerun leakage and score-distribution checks to confirm zero prompt overlap.