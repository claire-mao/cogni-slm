# Teacher Round 1 Validation

## Run Configuration

- run_id: `round1_teacher_validation`
- round_id: `round_1_pilot`
- dataset input: `datasets/gold/review_package/review_forms.jsonl` (from `datasets/gold/`)
- examples used: `24`
- configured teachers executed: `5`
- tasks per example: `7`
- seeds: `5`
- temperatures: `1`
- total requests: `4200`
- successful requests: `4200`
- failed requests: `0`
- execution mode: `dry_run=True`

## Teachers Included (Round 1 Config)

- `gpt-5`
- `claude_sonnet_4x` (canonical: `claude_sonnet_4`)
- `gemini_2_5_pro`
- `deepseek_r1`
- `qwen3`

## Outputs Collected

- essay score: `score`
- rubric analysis: `rubric`
- feedback: `feedback`
- reasoning: `reasoning`
- fallacy detection: `fallacy_detection`
- confidence: `confidence`

Collected file: `outputs/teacher_round1/round1_teacher_validation/collected_outputs.jsonl`
Collected rows: `4200`

## Validation Coverage

- validated outputs: `4200`
- overall json_validity_rate: `1.0`
- overall reasoning_completeness_mean: `1.0`
- overall unsupported_feedback_rate: `0.7083333333333334`

### Per-Model Validation Summary

| model_id | examples_total | json_validity_rate | missing_fields_rate | score_range_valid_rate | hallucinated_rubric_rate | unsupported_feedback_rate | reasoning_completeness_mean | brier_mean | ece_10bin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| claude_sonnet_4 | 840 | 1.0 | 0.0 | 1.0 | 0.0 | 0.7083333333333334 | 1.0 | 0.25 | 0.5 |
| deepseek_r1 | 840 | 1.0 | 0.0 | 1.0 | 0.0 | 0.7083333333333334 | 1.0 | 0.25 | 0.5 |
| gemini_2_5_pro | 840 | 1.0 | 0.0 | 1.0 | 0.0 | 0.7083333333333334 | 1.0 | 0.25 | 0.5 |
| gpt-5 | 840 | 1.0 | 0.0 | 1.0 | 0.0 | 0.7083333333333334 | 1.0 | 0.25 | 0.5 |
| qwen3 | 840 | 1.0 | 0.0 | 1.0 | 0.0 | 0.7083333333333334 | 1.0 | 0.25 | 0.5 |

## Task Coverage

- `argument_quality`: `600` outputs
- `educational_feedback`: `600` outputs
- `essay_scoring`: `600` outputs
- `logical_fallacy_identification`: `600` outputs
- `logical_reasoning`: `600` outputs
- `revision_suggestions`: `600` outputs
- `rubric_adherence`: `600` outputs

## Artifacts

- run manifest: `outputs/teacher_round1/round1_teacher_validation/manifest.json`
- run summary: `outputs/teacher_round1/round1_teacher_validation/summary.json`
- raw responses: `outputs/teacher_round1/round1_teacher_validation/responses.jsonl`
- collected outputs: `outputs/teacher_round1/round1_teacher_validation/collected_outputs.jsonl`
- validation results: `outputs/teacher_round1/round1_teacher_validation/validation/teacher_validation_results.jsonl`
- validation summary (csv): `outputs/teacher_round1/round1_teacher_validation/validation/teacher_validation_summary.csv`
- validation summary (json): `outputs/teacher_round1/round1_teacher_validation/validation/teacher_validation_summary.json`

## Notes

- No SFT dataset was generated in this round.
- No SFT labeling pipeline was executed.
- This run used dry-run generation because provider credentials were not configured in `.env`.
- To run live provider validation, populate `.env` and rerun without `--dry-run`.
