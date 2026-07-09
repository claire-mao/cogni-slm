# Model v1 Error Analysis

## Scope

- score errors
- rubric failures
- hallucinations
- reasoning failures
- fallacy misses
- feedback weaknesses
- clustered failure patterns

## Data and Constraints

- Prediction source: `outputs/evaluation/harness/eval-20260709T050351Z/`
- Compared models: Base (`Qwen/Qwen3-0.6B`) vs Fine-tuned (`Qwen/Qwen3-1.7B-Instruct`)
- Sample size: `8` examples per model (`16` total rows).
- Training status: latest production training run failed before adapter/merged model creation (no GPU).
- This is therefore a post-training *pipeline* error analysis on available evaluation artifacts, not a full powered production benchmark.

## Failure Summary

| Metric | Base | Fine-tuned | Delta (Fine-Base) |
|---|---:|---:|---:|
| MAE | 0.5938 | 0.5312 | -0.0625 |
| Exact score match rate | 0.000 | 0.125 | +0.125 |
| Severe score error rate (>=1.0) | 0.250 | 0.125 | -0.125 |
| Rubric failure rate | 1.000 | 1.000 | +0.000 |
| Hallucination rate (unsupported feedback proxy) | 0.875 | 0.875 | +0.000 |
| Reasoning failure rate | 1.000 | 1.000 | +0.000 |
| Calibration-gap>=0.4 rate | 0.500 | 0.500 | +0.000 |

## Error Taxonomy Findings

1. Score errors
- Base top errors: validation:0000000 (|e|=1.00, overscore), validation:0000002 (|e|=1.00, overscore), validation:0000005 (|e|=0.75, overscore), validation:0000003 (|e|=0.50, overscore), validation:0000006 (|e|=0.50, underscore)
- Fine-tuned top errors: validation:0000003 (|e|=1.00, underscore), validation:0000001 (|e|=0.75, overscore), validation:0000002 (|e|=0.75, overscore), validation:0000000 (|e|=0.50, underscore), validation:0000006 (|e|=0.50, underscore)

2. Rubric failures
- All rows lack criterion-level rubric outputs in the evaluation artifact schema, so rubric adherence cannot be directly scored; treated as structural rubric coverage failures.

3. Hallucinations
- Unsupported feedback proxy is high because feedback text is generic and weakly grounded in essay tokens (low lexical overlap with source essay).

4. Reasoning failures
- Reasoning is templated (`"Dry-run reasoning for harness validation."`) and too shallow for educational diagnostic standards.

5. Fallacy misses
- Not directly measurable on this artifact set because expected fallacy labels and predicted fallacy fields are absent.

6. Feedback weaknesses
- Feedback is near-identical across examples, indicating low specificity and low pedagogical personalization.

## Failure Clusters

| Cluster signature | Count | Example rows |
|---|---:|---|
| `moderate_score_error+overscore+rubric_missing+unsupported_feedback+reasoning_template+miscalibrated` | 3 | Base (Qwen/Qwen3-0.6B)::validation:0000005; Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000001; Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000002 |
| `moderate_score_error+underscore+rubric_missing+unsupported_feedback+reasoning_template` | 3 | Base (Qwen/Qwen3-0.6B)::validation:0000007; Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000000; Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000007 |
| `high_score_error+overscore+rubric_missing+unsupported_feedback+reasoning_template+miscalibrated` | 2 | Base (Qwen/Qwen3-0.6B)::validation:0000000; Base (Qwen/Qwen3-0.6B)::validation:0000002 |
| `low_score_error+underscore+rubric_missing+unsupported_feedback+reasoning_template` | 2 | Base (Qwen/Qwen3-0.6B)::validation:0000001; Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000005 |
| `moderate_score_error+underscore+rubric_missing+unsupported_feedback+reasoning_template+miscalibrated` | 2 | Base (Qwen/Qwen3-0.6B)::validation:0000006; Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000006 |
| `moderate_score_error+overscore+rubric_missing+unsupported_feedback+reasoning_template` | 1 | Base (Qwen/Qwen3-0.6B)::validation:0000003 |
| `low_score_error+overscore+rubric_missing+reasoning_template` | 1 | Base (Qwen/Qwen3-0.6B)::validation:0000004 |
| `high_score_error+underscore+rubric_missing+unsupported_feedback+reasoning_template+miscalibrated` | 1 | Fine-tuned (Qwen/Qwen3-1.7B-Instruct)::validation:0000003 |

## Highest-Impact Dataset Improvements

| Rank | Improvement Area | Impact Score | Why It Matters | Recommended Change |
|---:|---|---:|---|---|
| 1 | Structured supervision completeness (rubric/fallacy fields) | 1.000 | prevalence=1.000, severity=1.00 | Add/require rubric-criterion and fallacy fields in all training targets; reject outputs missing those fields during dataset build. |
| 2 | Reasoning depth and non-template behavior | 0.900 | prevalence=1.000, severity=0.90 | Add counterexamples with high-quality multi-step reasoning and enforce min reasoning-step coverage + anti-template dedup checks. |
| 3 | Feedback grounding | 0.744 | prevalence=0.875, severity=0.85 | Curate feedback-grounding pairs with cited essay evidence spans; penalize unsupported/generic feedback during filtering. |
| 4 | Score calibration around decision boundaries | 0.350 | prevalence=0.500, severity=0.70 | Add boundary-score examples (adjacent rubric bands) and calibrate confidence via temperature scaling on held-out validation. |
| 5 | Large absolute score errors | 0.141 | prevalence=0.188, severity=0.75 | Upsample hard prompts with high score variance and add adjudicated exemplars for low/high-score tails. |

## Recommended Next Pass

1. Re-run this analysis after a successful GPU training run with real adapter + merged model outputs (not dry-run harness responses).
2. Extend evaluation outputs to include structured rubric and fallacy fields so rubric adherence/fallacy miss are first-class measurable metrics.
3. Add reviewer-adjudicated failure exemplars for top clusters and retrain with targeted oversampling.
