# Teacher Leaderboard

## Coverage

- runs_scanned: `1`
- responses_loaded: `35`
- models_ranked: `5`

## Metrics

- QWK
- MAE
- rubric adherence
- fallacy F1
- agreement
- consistency
- JSON validity
- hallucination rate
- latency
- cost

## Ranking

| rank | model | responses | qwk | mae | rubric | fallacy_f1 | agreement | consistency | json_validity | hallucination_rate | latency_ms | cost_usd | rank_score |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | qwen3 | 7 | 0.0000 | 27.0000 | 0.1286 | n/a | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.00 | 0.000000 | 0.6766 |
| 2 | gemini_2_5_pro | 7 | 0.0000 | 27.0000 | 0.1286 | n/a | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.00 | 0.000000 | 0.6754 |
| 3 | deepseek_r1 | 7 | 0.0000 | 27.0000 | 0.1286 | n/a | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.00 | 0.000000 | 0.6741 |
| 4 | claude_sonnet_4x | 7 | 0.0000 | 27.0000 | 0.1286 | n/a | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.00 | 0.000000 | 0.6705 |
| 5 | gpt-5 | 7 | 0.0000 | 27.0000 | 0.1286 | n/a | 1.0000 | 1.0000 | 1.0000 | 0.0000 | 0.00 | 0.000000 | 0.6198 |

## Method Notes

- `rubric adherence` is task-field coverage on `rubric_adherence` task outputs.
- `agreement` combines pairwise score agreement and fallacy-label agreement where available.
- `consistency` checks identical canonical JSON for repeated runs of same model/task/example.
- `hallucination rate` is heuristic and flags parse failures plus known unsupported-claim patterns.
- Composite `rank_score` normalizes available metrics and reweights if some metrics are unavailable.

## Data Notes

- Run `teacher-runs-smoke` is marked dry_run=true.
