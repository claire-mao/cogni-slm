# Metadata Leakage Report

## Scope

- Training dataset: `datasets/training`
- Provenance sidecar: `datasets/training_provenance`

## Training Dataset Schema

| split | rows | columns | only_prompt_essay_score |
|---|---:|---|---|
| train | 12413 | `['prompt', 'essay', 'score']` | PASS |
| validation | 0 | missing | SKIP |
| test | 0 | missing | SKIP |

## Provenance Key Audit

- Rows scanned: `12413`
- Result: PASS (no score/label keys found in provenance sidecar)

## Verdict

- Status: **PASS**
- Warnings:
  - Missing split: validation
  - Missing split: test
