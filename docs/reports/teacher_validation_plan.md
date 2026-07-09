# Teacher-Model Validation Plan (Pre-Labeling Only)

Scope:

- Protocol design only.
- No dataset modification.
- No label generation.
- No inference execution.

This plan integrates:

- `docs/reports/teacher_models_overview.md`
- `docs/reports/teacher_models_education.md`
- `docs/reports/teacher_models_deployment.md`
- `docs/reports/teacher_model_selection.md`

and is operationalized in:

- `configs/teacher/teacher_validation_master.json`
- `configs/teacher/teacher_task_suite_v1.json`
- `configs/teacher/teacher_gold_set_v1.json`
- `configs/teacher/teacher_metrics_v1.json`
- `configs/teacher/teacher_models_costs_v1.json`
- `configs/teacher/teacher_ensembles_v1.json`
- `configs/teacher/teacher_rounds_v1.json`

## 1) Evaluation Tasks

Evaluate every candidate teacher on the following tasks per example:

1. `essay_scoring`: predict rubric-aligned holistic score with confidence and rationale.
2. `rubric_adherence`: criterion-level scoring and evidence linking.
3. `educational_feedback`: student-facing strengths, priorities, and next actions.
4. `logical_reasoning`: evaluate logical coherence and claim-evidence linkage.
5. `argument_quality`: thesis clarity, evidence quality, counterargument handling.
6. `logical_fallacy_identification`: primary fallacy or no-fallacy classification.
7. `revision_suggestions`: targeted revision plan with expected score impact.

All outputs must be strict JSON and include required task-specific fields defined in `teacher_task_suite_v1.json`.

## 2) Gold Evaluation Set (100 Manually Reviewed Examples)

Construct exactly 100 examples with this composition:

- ASAP essays: 30
- Persuade essays: 20
- Argumentative essays: 20
- AP-style writing samples: 20
- Logical-fallacy examples: 10

Exact construction procedure:

1. Build candidate pools for each source category.
2. Stratify by difficulty and coverage dimensions:
   - score bands (`low`, `mid`, `high`)
   - length (`short`, `medium`, `long`)
   - prompt/topic diversity
   - fallacy label coverage (including `no_fallacy`)
3. Randomly sample within each stratum using fixed seeds.
4. Run manual review with 2 independent raters per example.
5. Adjudicate disagreements with 1 adjudicator.
6. Enforce calibration pass before full annotation:
   - 15 calibration examples
   - minimum thresholds: score QWK >= 0.75, fallacy F1 >= 0.75, rubric-item agreement >= 0.80
7. Freeze and version as `teacher_gold_v1.0` with checksum manifest.

Required gold fields per example:

- `example_id`, `source_id`, `prompt`, `essay_text`
- `gold_score`, `gold_rubric_items`
- `gold_feedback_reference`
- `gold_reasoning_completeness`, `gold_argument_quality`
- `gold_fallacy_label`, `gold_revision_targets`
- `reviewer_confidence`, `adjudication_note`

## 3) Evaluation Metrics

Primary metrics:

- Quadratic Weighted Kappa
- MAE
- score consistency
- rubric adherence
- JSON validity
- reasoning completeness
- feedback usefulness
- hallucination rate
- logical-fallacy precision/recall
- inter-model agreement

Operational definitions:

- `score_consistency`: `1 - normalized_stddev(score over repeats)`.
- `json_validity`: `valid_json_outputs / total_outputs`.
- `reasoning_completeness`: required section and evidence coverage score.
- `feedback_usefulness`: human-rated utility (normalized).
- `hallucination_rate`: unsupported claims divided by outputs.
- `inter_model_agreement`: pairwise QWK for scores and label overlap metrics for classification tasks.

Hard gates:

- `json_validity >= 0.98`
- `hallucination_rate <= 0.05`
- deterministic-output success >= 0.95

## 4) Repeatability Tests

For each model/task/example:

- Run 5 repeated generations with seeds: `11, 22, 33, 44, 55`.
- Measure variance across 5 runs for all core metrics.
- Measure deterministic output success at `temperature=0` (canonical JSON byte-identity).
- Measure confidence calibration with ECE and Brier score.
- Measure score stability via max delta and stddev across repeats.

Repeatability pass conditions:

- deterministic success >= 0.95
- max score delta <= 1 (ordinal score scale)
- no metric variance spike > predefined tolerance relative to cohort median

## 5) Cost/Runtime/Throughput Evaluation

Planning assumptions (per model):

- 100 examples
- 7 tasks/example
- base tokens/example: 5,700 input + 1,320 output
- 700 requests/run
- repeatability suite: 5 runs (3,500 requests)
- concurrency target: 10

Estimated cost and runtime (from `teacher_models_costs_v1.json`):

| Model | Est. cost (100 ex, 1 run) | Est. cost (100 ex, 5 runs) | Est. runtime (1 run) | Est. throughput (req/min) |
|---|---:|---:|---:|---:|
| GPT-5 | $2.03 | $10.16 | 14.00 min | 50.00 |
| o3 | $2.30 | $11.51 | 18.67 min | 37.50 |
| Claude Opus 4 | $18.95 | $94.73 | 16.33 min | 42.86 |
| Claude Sonnet 4 | $3.69 | $18.45 | 9.33 min | 75.00 |
| Gemini 2.5 Pro | $2.23 | $11.15 | 14.00 min | 50.00 |
| DeepSeek R1 | $0.12 | $0.62 | 8.17 min | 85.71 |
| Qwen3 | $0.33 (non-thinking) / $0.58 (thinking) | $1.65 / $2.90 | 9.33 min | 75.00 |
| Llama 4 Maverick | $0.56-$3.37 (provider-dependent) | $2.81-$16.87 | 11.67 min | 60.00 |

These are planning estimates for experiment design, not measured benchmarks.

## 6) Ensemble Experiments

Compare:

1. single teacher
2. majority vote
3. score averaging
4. teacher-judge pipeline
5. teacher + verifier
6. teacher + local checker

Experiment details:

- Majority vote: 3-teacher triplets for discrete tasks; tie-break by calibrated confidence.
- Score averaging: weighted mean for numeric scoring; weights from Round 2 validation scorecard.
- Teacher-judge: independent judge gates rubric adherence/format and triggers repair when below threshold.
- Teacher+verifier: secondary model checks factual/rubric consistency before acceptance.
- Teacher+local checker: deterministic local validators enforce schema/score-range/evidence fields.

Selection rule:

- Primary: highest weighted scorecard.
- Secondary: lowest cost among options within 1% of top quality.
- Must pass repeatability hard gates.

## 7) Evaluation Order

Round 1: small pilot

- 24 examples
- objective: validate protocol, schema, and annotation/judge flow
- exit: metrics computable, JSON validity gate passed

Round 2: 100 examples

- full gold set across all 8 models + all 6 ensemble strategies
- objective: select top candidates with full quality and repeatability evidence

Round 3: 1000 examples

- only top 3 single models + top 2 ensembles from Round 2
- objective: verify scale behavior and cost/latency stability

Round 4: full dataset (shadow mode)

- winner only
- objective: production-readiness dry run
- constraint: no label write-back until explicit signoff

## 8) Reusable Config Files

Created under `configs/teacher/`:

- `teacher_validation_master.json`
- `teacher_task_suite_v1.json`
- `teacher_gold_set_v1.json`
- `teacher_metrics_v1.json`
- `teacher_models_costs_v1.json`
- `teacher_ensembles_v1.json`
- `teacher_rounds_v1.json`

## 9) Execution Guardrails

- Do not modify datasets during protocol-design stage.
- Do not generate labels during validation planning.
- Do not run inference until the protocol and gold-set construction are approved.
