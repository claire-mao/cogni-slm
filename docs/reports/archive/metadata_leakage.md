# Metadata Leakage Report

## Scope

- Training dataset: `datasets/training`
- Provenance sidecar: `datasets/training_provenance`

## Training Dataset Schema

| split | rows | columns | only_prompt_essay_score |
|---|---:|---|---|
| train | 9940 | `['prompt', 'essay', 'score']` | PASS |
| validation | 1241 | `['prompt', 'essay', 'score']` | PASS |
| test | 1232 | `['prompt', 'essay', 'score']` | PASS |

## Column Leakage Check

- Result: PASS (no metadata/label columns in training splits)

## Provenance Key Audit

- Rows scanned: `12413`
- Result: PASS (no keys containing `score` or `label` found in provenance sidecar)

## Verdict

- Status: **PASS**
- Training dataset is restricted to `prompt`, `essay`, `score`.
- No metadata field contains label/derived score keys in training artifacts.
