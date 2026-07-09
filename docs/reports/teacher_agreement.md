# Teacher Agreement Experiment Design

Scope:

- Design only.
- No execution in this step.

Goal:

- Compare multi-teacher aggregation strategies for supervision quality and operational efficiency.

Strategies compared:

1. single teacher
2. majority vote
3. weighted average
4. teacher + verifier
5. teacher + judge

## Experiment Setup

Evaluation set:

- `datasets/gold/gold_v1.jsonl`

Candidate teachers:

- GPT-5
- o3
- Claude Opus 4
- Claude Sonnet 4
- Gemini 2.5 Pro
- DeepSeek R1
- Qwen3
- Llama 4 Maverick

Common controls:

- Same prompt template and output schema for all teachers.
- Same deterministic settings (`temperature=0`, fixed decoding policy).
- Same input ordering and batching policy.
- Canonical JSON normalization before scoring (sorted keys, stable whitespace).

Recorded per output:

- `score`
- `confidence`
- `rubric` (criteria judgments)
- `reasoning`
- `logical_analysis`
- `fallacies`
- `feedback`
- timing/tokens/cost metadata

## Strategy Definitions

### 1) Single Teacher

- One model produces final output.
- Baseline for quality/cost/latency.

### 2) Majority Vote

- Discrete fields (`fallacies.primary`, rubric criterion judgments) chosen by mode across 3 teachers.
- Score chosen by rounded median, then tie-broken by highest-confidence teacher.

### 3) Weighted Average

- Numeric fields (score, confidence) aggregated as weighted mean.
- Weight source:
  - Round-1 calibration score per teacher (for example `w_i ~ QWK_i` with normalization).
- Discrete fields selected from teacher with highest weighted confidence on that example.

### 4) Teacher + Verifier

- Primary teacher generates full output.
- Verifier checks schema, rubric grounding, and logical consistency.
- If verifier fails hard checks, trigger one repair pass from primary teacher.

### 5) Teacher + Judge

- Primary teacher generates output.
- Independent judge scores rubric adherence and logical quality (0-1).
- If judge score below threshold, reject and regenerate once; else accept.

## Metrics

### Agreement

- Score agreement:
  - pairwise QWK between teachers
  - strategy-vs-gold QWK
- Rubric agreement:
  - macro-F1 over criterion judgments
  - Jaccard overlap on rubric evidence tags
- Fallacy agreement:
  - pairwise label agreement rate
  - macro-F1 vs gold fallacy labels
- Reasoning agreement:
  - section-level completeness agreement
  - normalized overlap of reasoning-step intent labels

### Disagreement

- Pairwise disagreement rate: `% examples where outputs conflict materially`.
- Score spread: `max(score_i) - min(score_i)` per example.
- Rubric conflict count: number of criteria with non-matching judgments.
- Fallacy conflict count: number of examples with non-matching primary fallacy labels.
- Conflict entropy: Shannon entropy over teacher categorical outputs.

### Confidence

- Mean confidence by strategy.
- Confidence variance by strategy.
- Calibration vs correctness:
  - Brier score
  - ECE (10-bin)
- Overconfidence rate:
  - `% examples with confidence >= 0.8 and incorrect decision`.

### Cost

- Input/output token totals.
- Cost per example.
- Cost per accepted output (for verifier/judge pipelines with retries).
- Incremental cost vs single-teacher baseline.

### Latency

- End-to-end latency per example:
  - p50
  - p95
  - max
- Wall-clock throughput (examples/minute).
- Queue amplification for multi-stage pipelines (verifier/judge retries).

## Analysis Plan

Primary ranking dimensions:

1. quality (agreement with gold + lower disagreement)
2. reliability (confidence calibration + deterministic consistency)
3. efficiency (cost + latency)

Composite view:

- Build Pareto frontier over:
  - `quality_score` (weighted quality metrics)
  - `cost_per_example`
  - `p95_latency`

Suggested quality composite:

- `0.35 * QWK_score`
- `0.20 * rubric_macro_f1`
- `0.15 * fallacy_macro_f1`
- `0.15 * reasoning_completeness`
- `0.15 * (1 - disagreement_rate)`

Statistical testing:

- Paired bootstrap CI for strategy deltas.
- Sign test for per-example wins/losses vs baseline.
- Report 95% confidence intervals for all primary deltas.

## Experiment Matrix

Phase 1 (pilot):

- 24 examples
- Strategies: all 5
- Purpose: validate instrumentation, logs, and aggregation logic.

Phase 2 (core):

- 100 examples (`gold_v1`)
- Strategies: all 5
- Purpose: selection-quality comparison.

Phase 3 (scale check):

- 1,000 examples (held-out extension)
- Strategies: top 2 from Phase 2
- Purpose: throughput/cost/latency stability.

## Decision Rules

Hard gates:

- JSON validity >= 0.98
- Missing-field rate <= 0.02
- Score-range violations = 0
- Unsupported-feedback rate <= 0.05

Selection rule:

- Pick highest-quality strategy among those passing hard gates.
- If top two are within 1% quality, choose lower cost.
- If cost tie, choose lower p95 latency.

## Artifacts to Produce During Execution

- `outputs/teacher_benchmark/<run_id>/strategy_summary.json`
- `outputs/teacher_benchmark/<run_id>/agreement_matrix.csv`
- `outputs/teacher_benchmark/<run_id>/disagreement_cases.jsonl`
- `outputs/teacher_benchmark/<run_id>/cost_latency_summary.csv`
- `outputs/teacher_benchmark/<run_id>/comparison_report.md`

This design intentionally separates experiment planning from execution.
