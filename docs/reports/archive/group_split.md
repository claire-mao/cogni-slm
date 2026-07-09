# Prompt-Group Candidate Split Report

## Objective

Create a candidate split where each prompt appears in exactly one split, while balancing
split sizes and score distributions as much as possible.

## Candidate Output

- Candidate directory: `datasets/training_candidates/prompt_group_split`
- Data files: `train.jsonl`, `validation.jsonl`, `test.jsonl`
- Data schema: `prompt`, `essay`, `score`
- Provenance sidecar: `provenance/{train,validation,test}.jsonl`

## Search Method

- Prompt groups searched: `8`
- Exhaustive assignments evaluated: `6561`
- Constraint: each prompt assigned to one split only
- Objective: `size_weight * size_error + distribution_weight * distribution_error`
- Best objective: `3.522535`
- Size error component: `0.159091`
- Distribution error component: `1.681722`

## Prompt Assignment

| split | prompts |
|---|---|
| train | 1, 2, 3, 4, 7, 8 |
| validation | 5 |
| test | 6 |

## Prompt Overlap Check

- train ∩ validation: `0`
- train ∩ test: `0`
- validation ∩ test: `0`

## Split Summary

| split | examples | prompts | score_min | score_max | score_mean | score_std |
|---|---:|---:|---:|---:|---:|---:|
| train | 8943 | 6 | 0.0000 | 60.0000 | 8.7676 | 10.1746 |
| validation | 1706 | 1 | 0.0000 | 4.0000 | 2.4947 | 0.9227 |
| test | 1764 | 1 | 0.0000 | 4.0000 | 2.7647 | 0.9250 |

## Global Score Summary

- Total examples: `12413`
- Min: `0.0000`
- Max: `60.0000`
- Mean: `7.0524`
- Std: `9.0779`

## Provenance Preservation

- Candidate provenance rows: `12413`
- Missing provenance rows during load: `0`
- Essay hash mismatches vs provenance: `0`
- Each candidate provenance row includes:
  - `candidate_example_index`
  - `candidate_split`
  - `original_split`
  - `original_example_index`
  - `prompt`
  - `essay_sha256`
  - `source_records`
