# Teacher Pilot Validation Plan

## Scope

This pilot evaluates three teacher models on a small, manually reviewed subset before larger-scale validation.

Pilot size: `20` examples.

Models in scope:
1. GPT-5
2. Claude Opus 4
3. DeepSeek R1

Execution status in this document: design only. No run is executed.

## Goals

1. Verify that metric collection is stable on a small, stratified set.
2. Compare quality, agreement, and operational cost/latency across the three teachers.
3. Identify whether any model should be excluded before Gold100 evaluation.

## Dataset Design (20 Examples)

Sampling approach: stratified fixed-quota sampling from `datasets/gold/gold_v1.jsonl`.

Source composition for pilot:
1. ASAP: 6
2. Persuade: 4
3. AP essays: 4
4. Argumentative essays: 4
5. Logical fallacy examples: 2

Balancing constraints:
1. Difficulty target: low 6, medium 8, high 6.
2. Length target: short 5, medium 9, long 6.
3. Topic cap: no single topic above 25% of pilot set.
4. Deterministic seed: 42.

## Models and Run Settings

Models:
1. `gpt-5`
2. `claude_opus_4x`
3. `deepseek_r1`

Run settings:
1. Temperature: `0.0`
2. Seed: `42`
3. Max output tokens: `1200`
4. Timeout: `120s`
5. Strict JSON required.

Total estimated requests:
1. 3 models x 6 tasks x 20 examples x 1 seed x 1 temperature = `360` requests.

## Tasks Evaluated

1. `essay_scoring`
2. `rubric_adherence`
3. `educational_feedback`
4. `logical_reasoning`
5. `argument_quality`
6. `logical_fallacy_identification`

## Metrics

The pilot reports all requested metrics.

1. QWK
- Quadratic Weighted Kappa between predicted and gold essay scores.

2. MAE
- Mean absolute error between predicted and gold essay scores.

3. Rubric adherence
- Fraction of required rubric criteria correctly addressed with grounded evidence.

4. Feedback quality
- Human-rated usefulness (normalized) plus grounding checks.

5. JSON validity
- Valid strict JSON responses divided by total responses.

6. Hallucination rate
- Unsupported claims divided by total outputs.

7. Logical reasoning
- Reasoning completeness and coherence score from required reasoning fields.

8. Fallacy detection
- Macro F1 over fallacy labels including `no_fallacy`.

9. Agreement
- Pairwise model agreement using QWK for score outputs and macro agreement for rubric/fallacy labels.

10. Cost
- Estimated USD from recorded token usage and pricing config.

11. Latency
- End-to-end latency per response; report p50 and p95.

## Evaluation Procedure

1. Use the same 20 examples for all three models.
2. Run all six tasks per example.
3. Validate every output with the existing validation stack.
4. Aggregate metrics overall and by slices: source, difficulty, and task.

Pairwise agreement pairs:
1. GPT-5 vs Claude Opus 4
2. GPT-5 vs DeepSeek R1
3. Claude Opus 4 vs DeepSeek R1

## Quality Gates

Pilot passes if all conditions hold:
1. JSON validity >= 0.98.
2. Hallucination rate <= 0.10.
3. Score metrics (QWK and MAE) are computable for all models.
4. Fallacy detection metric is computable for all models.
5. Agreement, cost, and latency tables are complete.

If any gate fails:
1. Mark pilot as failed.
2. Identify blocking causes by model and task.
3. Fix config/prompt/schema issues before scaling to 100 examples.

## Deliverables

Primary deliverables for this pilot design:
1. `configs/teacher/teacher_pilot_v1.json`
2. `docs/reports/teacher_pilot_plan.md`

Planned runtime outputs when later executed:
1. `outputs/teacher_runs/teacher_pilot_v1/responses.jsonl`
2. `outputs/teacher_runs/teacher_pilot_v1/summary.json`
3. `outputs/teacher_runs/teacher_pilot_v1/validation/teacher_validation_summary.json`

## Guardrails

1. Do not modify datasets in this step.
2. Do not generate labels.
3. Do not run inference in this step.
