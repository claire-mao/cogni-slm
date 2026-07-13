# Final Dataset Readiness Report

> Update (2026-07-11): This report reflects an earlier snapshot.
> Current consolidated status and blockers are tracked in `docs/reports/master_completion_checklist_20260711.md`.

- Generated (UTC): `2026-07-09T22:41:48.861806+00:00`
- Dataset root: `datasets/sft`

## Core Metrics

- Total examples: `24`
- Train/Validation/Test: `21/1/2`
- Duplicates removed during build: `0`
- Malformed JSON rows: `0`
- Invalid examples: `0`

## Length and Balance

- Avg prompt tokens: `340.17`
- Avg response tokens: `131.0`
- Avg total tokens: `471.17`
- Prompt/response token ratio: `2.5967`

## Label Distribution

- Score distribution:
  - `30`: `24`
- Confidence distribution:
  - `0.500`: `24`

## Duplicate Analysis

- Exact duplicate full records remaining: `0`
- Reused inputs remaining: `0`
- Reused outputs remaining: `23`

## Random Inspection

- Requested sample: `100`
- Inspected sample: `24` (dataset smaller than requested)
- identical_output_template: `24`
- dry_run_artifact: `24`
- fallacy_always_none: `24`
- score_no_variance: `24`
- confidence_no_variance: `24`
- anonymization_placeholders_in_input: `18`

## Readiness Verdict

- Status: **NOT_READY**
- Blocking issues:
  - `dataset_too_small_for_training`
  - `high_output_duplication`
  - `label_no_variance`
  - `dry_run_artifact_detected`

- JSON summary: `docs/reports/final_dataset_readiness.json`
