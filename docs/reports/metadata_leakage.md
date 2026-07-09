# Metadata Leakage Report

## Scope

- Training dataset: `datasets/training`
- Provenance sidecar: `datasets/training_provenance`

## Training Dataset Schema

| split | rows | columns | only_prompt_essay_score |
|---|---:|---|---|
| train | 9930 | `['prompt', 'essay', 'score']` | PASS |
| validation | 1241 | `['prompt', 'essay', 'score']` | PASS |
| test | 1242 | `['prompt', 'essay', 'score']` | PASS |

## Provenance Key Audit

- Rows scanned: `12413`
- Result: PASS (no score/label keys found in provenance sidecar)

## Verdict

- Status: **PASS**
