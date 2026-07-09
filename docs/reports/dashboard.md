# Experiment Dashboard

- generated_at_utc: `2026-07-09T20:16:02.403852+00:00`

## Teacher Experiments

- runs_found: `2`
- total_requests: `35`
- successful_requests: `35`
- failed_requests: `0`
- total_estimated_cost_usd: `0.000000`
- total_runtime_seconds: `0.00`

| run_id | round_id | dry_run | models | tasks | requests | avg_latency_ms | cost_usd |
|---|---|---:|---:|---:|---:|---:|---:|
| pilot_v1 | unknown | no | 0 | 0 | 0 | n/a | 0.000000 |
| teacher-runs-smoke | round_1_pilot | yes | 5 | 7 | 35 | 0.003 | 0.000000 |

## Training Runs

- plans_found: `1`
- runs_total: `1`
- runs_completed: `0`
- runs_failed: `1`
- runs_planned: `0`
- total_runtime_seconds: `14.82`

## Evaluation Metrics

- evaluation_runs_found: `6`

| run_id | total_examples | base_model | tuned_model | base_qwk | tuned_qwk | qwk_delta | mae_delta |
|---|---:|---|---|---:|---:|---:|---:|
| prompt-test-20260708T204605Z | 0 | n/a | n/a | n/a | n/a | 0.5167 | n/a |
| eval-20260709T050351Z | 8 | Qwen/Qwen3-0.6B | Qwen/Qwen3-1.7B-Instruct | 0.7681 | 0.7975 | 0.0294 | -0.0625 |
| eval-20260709T030014Z | 8 | Qwen/Qwen3-0.6B | Qwen/Qwen3-1.7B-Instruct | 0.7681 | 0.7975 | 0.0294 | -0.0625 |
| eval-20260709T023800Z | 8 | Qwen/Qwen3-0.6B | Qwen/Qwen3-1.7B-Instruct | 0.7681 | 0.7975 | 0.0294 | -0.0625 |
| eval-20260709T023749Z | 16 | Qwen/Qwen3-0.6B | Qwen/Qwen3-1.7B-Instruct | 0.8033 | 0.7772 | -0.0261 | 0.0156 |
| eval-20260709T023655Z | 16 | Qwen/Qwen3-0.6B | Qwen/Qwen3-1.7B-Instruct | 0.8033 | 0.7772 | -0.0261 | 0.0156 |

## Error Analysis

- available: `false`
- No error analysis summary found.

## Cost and Runtime

- teacher_cost_usd: `0.000000`
- teacher_runtime_seconds: `0.00`
- training_runtime_seconds: `14.82`
- combined_runtime_seconds: `14.83`

## Teacher Leaderboard Snapshot

- models_listed: `5`

| rank | model | qwk | mae | json_validity | latency_ms | cost_usd | rank_score |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | qwen3 | 0.0000 | 27.0000 | 1.0000 | 0.0020 | 0.000000 | 0.6766 |
| 2 | gemini_2_5_pro | 0.0000 | 27.0000 | 1.0000 | 0.0020 | 0.000000 | 0.6754 |
| 3 | deepseek_r1 | 0.0000 | 27.0000 | 1.0000 | 0.0021 | 0.000000 | 0.6741 |
| 4 | claude_sonnet_4x | 0.0000 | 27.0000 | 1.0000 | 0.0022 | 0.000000 | 0.6705 |
| 5 | gpt-5 | 0.0000 | 27.0000 | 1.0000 | 0.0042 | 0.000000 | 0.6198 |

## Notes

- This dashboard summarizes existing artifacts only.
- No experiments or training jobs were executed by this report builder.
