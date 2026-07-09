# Teacher Round 1 Analysis

## Scope

- Run analyzed: `outputs/teacher_round1/round1_teacher_validation`
- Examples: `24`
- Teachers: `5` (`gpt-5`, `claude_sonnet_4`, `gemini_2_5_pro`, `deepseek_r1`, `qwen3`)
- Tasks: `7` (essay scoring, rubric adherence, feedback, reasoning, argument quality, fallacy detection, revision suggestions)
- Outputs validated: `4200`

## Important Context

- Round 1 execution mode was `dry_run=True`, so model outputs are synthetic placeholders from the runner (not live provider inference).
- Measured cost and latency in this run are therefore not production-representative.
- Cost/latency comparisons below use projected values from `configs/teacher/teacher_models_costs_v1.json` as tie-breakers.

## Comparison

| model | quality_score | agreement | rubric_adherence | hallucination_rate | json_validity | reasoning_completeness | brier | ece | measured_latency_ms(avg) | measured_cost_usd(total) | projected_cost_usd(round1) | projected_p50_latency_s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek_r1 | 0.8938 | 1.0000 | 1.0000 | 0.7083 | 1.0000 | 1.0000 | 0.2500 | 0.5000 | 0.0093 | 0.000000 | 0.144 | 7.0 |
| qwen3 | 0.8938 | 1.0000 | 1.0000 | 0.7083 | 1.0000 | 1.0000 | 0.2500 | 0.5000 | 0.0092 | 0.000000 | 0.396 | 8.0 |
| gpt-5 | 0.8938 | 1.0000 | 1.0000 | 0.7083 | 1.0000 | 1.0000 | 0.2500 | 0.5000 | 0.0096 | 0.000000 | 2.436 | 12.0 |
| gemini_2_5_pro | 0.8938 | 1.0000 | 1.0000 | 0.7083 | 1.0000 | 1.0000 | 0.2500 | 0.5000 | 0.0092 | 0.000000 | 2.676 | 12.0 |
| claude_sonnet_4 | 0.8938 | 1.0000 | 1.0000 | 0.7083 | 1.0000 | 1.0000 | 0.2500 | 0.5000 | 0.0092 | 0.000000 | 4.428 | 8.0 |

### Pairwise Agreement

| model_a | model_b | score_exact | confidence_exact | fallacy_exact | rubric_exact | overall | shared_rows |
|---|---|---:|---:|---:|---:|---:|---:|
| claude_sonnet_4 | deepseek_r1 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| claude_sonnet_4 | gemini_2_5_pro | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| claude_sonnet_4 | gpt-5 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| claude_sonnet_4 | qwen3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| deepseek_r1 | gemini_2_5_pro | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| deepseek_r1 | gpt-5 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| deepseek_r1 | qwen3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| gemini_2_5_pro | gpt-5 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| gemini_2_5_pro | qwen3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |
| gpt-5 | qwen3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 840 |

## Recommendation: Top Three Teachers

Ranking rule used for this round: quality score -> agreement -> projected cost -> projected latency.

1. `deepseek_r1` (quality=0.8938, agreement=1.0000, projected_cost=$0.144)
2. `qwen3` (quality=0.8938, agreement=1.0000, projected_cost=$0.396)
3. `gpt-5` (quality=0.8938, agreement=1.0000, projected_cost=$2.436)

## Interpretation

- Quality, agreement, calibration, hallucination, and rubric adherence were effectively tied across all models in this run because the run used deterministic dry-run responses.
- Under tied quality, projected deployment efficiency selected `deepseek_r1`, `qwen3`, and `gpt-5` as the top three for Round 1.
- For final teacher selection, rerun Round 1 (or Round 2 gold100) with live provider inference and the same validation stack to obtain meaningful model-quality separation.

## Artifacts Used

- `outputs/teacher_round1/round1_teacher_validation/responses.jsonl`
- `outputs/teacher_round1/round1_teacher_validation/validation/teacher_validation_summary.csv`
- `outputs/teacher_round1/round1_teacher_validation/summary.json`
- `configs/teacher/teacher_models_costs_v1.json`
