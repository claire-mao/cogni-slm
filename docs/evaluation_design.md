# Cogni Evaluation Design

## 1. Scope, Non-Goals, and Behavior-Spec Mapping

### Scope
This evaluation system measures whether a fine-tuned model follows the Cogni Behavior
Specification more reliably than the base model.

The system covers five required dimensions:
- Behavior Specification adherence
- Logical fallacy accuracy
- Robustness to adversarial prompts
- Consistency
- Base vs tuned model comparison

### Non-Goals (This Milestone)
- No dataset generation or annotation execution
- No model training or inference optimization
- No hardcoded acceptance thresholds
- No production deployment pipeline

### Mapping to Behavior Specification
Behavior checks are mapped directly to the current behavior IDs.

| Behavior Spec Item | Evaluation Surface | Check Family |
|---|---|---|
| B1 Structural diagnosis over keyword matching | semantic diagnosis quality | LLM judge rubric |
| B2 Pedagogical explanation at requested depth | pedagogical quality | LLM judge rubric |
| B3 Explicit analogy mapping | analogy structure and clarity | deterministic + LLM judge |
| B4 Uncertainty handling for ambiguity | uncertainty calibration | deterministic + LLM judge |
| B5 Safe and non-derogatory style | safety style compliance | deterministic + LLM judge |
| B6 No speculative intent attribution | evidence grounding | deterministic + LLM judge |
| B7 Deterministic section ordering | response structure order | deterministic checks |
| P1 Label-only response | required section presence | deterministic checks |
| P2 Invented evidence | grounding and citation fidelity | LLM judge rubric |
| P3 Overstated certainty | confidence-note calibration | deterministic + LLM judge |
| P4 Obscuring analogy | analogy faithfulness | LLM judge rubric |
| P5 Out-of-scope authority advice | scope guardrails | deterministic + LLM judge |

## 2. Evaluation Dimensions and Scoring Signals

### 2.1 Behavior Specification Adherence
Signals:
- Required field and section checks against behavior output contract
- Section ordering checks aligned with B7
- Semantic rubric scoring for diagnosis quality, analogy mapping, repair quality,
  and confidence calibration

Expected outputs:
- Per-example deterministic pass/fail vector
- Per-example rubric scores by behavior dimension
- Aggregated adherence score with confidence interval

### 2.2 Logical Fallacy Accuracy
Label policy:
- One `primary_fallacy_label`
- Optional `acceptable_alternative_labels`

Scoring:
- Full credit for primary-label match
- Partial/accepted credit for alternative-label match
- Error categories for near-miss vs unrelated fallacy predictions

Expected outputs:
- Per-example label outcome (`primary_match`, `alternative_match`, `miss`)
- Aggregate accuracy profile by fallacy family and ambiguity level

### 2.3 Robustness to Adversarial Prompts
Adversarial strata:
- Prompt injection against role/task
- Misleading lexical cues
- Internal contradictions
- Stylistic attacks (tone, verbosity pressure, irrelevant framing)

Scoring:
- Behavior adherence under attack
- Degradation relative to non-adversarial baseline
- Safety and scope retention under adversarial pressure

Expected outputs:
- Stratum-level robustness score
- Failure-mode histogram by attack type and behavior ID

### 2.4 Consistency
Consistency probes:
- Repeat-run stability (same input, repeated generations)
- Paraphrase invariance (semantically equivalent prompts)

Scoring:
- Variance metrics for scores across repeats
- Agreement metrics across paraphrase clusters
- Section-order stability checks

Expected outputs:
- Consistency score per dimension
- Drift summary across repeated/paraphrased inputs

### 2.5 Base vs Tuned Comparison
Comparison protocol:
- Paired evaluation over identical examples, prompts, and decoding settings
- Per-example paired deltas + aggregate confidence intervals

Expected outputs:
- Dimension-wise deltas (`tuned - base`)
- Comparison confidence intervals and significance diagnostics
- Gated composite decision outcome

## 3. Hybrid Scoring Pipeline Architecture

Pipeline stages:
1. Load benchmark records and evaluation configuration.
2. Generate base and tuned outputs with matched inference settings.
3. Run deterministic prechecks for behavior contract compliance.
4. Run LLM judge rubrics for semantic and pedagogical quality dimensions.
5. Aggregate metrics by split, dimension, and adversarial stratum.
6. Run paired base-vs-tuned comparison statistics.
7. Apply gating policy for milestone decisioning.
8. Emit report artifacts (machine-readable summary + detailed traces).

Design principles:
- Deterministic checks provide hard contract guarantees.
- LLM judging captures semantic quality not reducible to rigid rules.
- All aggregate scores must remain traceable to per-example evidence.

## 4. Gating Policy and Statistical Comparison

Default policy: gated composite.

Gate requirements:
- Tuned model must improve on primary quality dimensions:
  - behavior adherence
  - logical fallacy accuracy
- Tuned model must not regress on:
  - robustness dimensions
  - consistency dimensions

Statistical policy:
- Paired comparison only (same example evaluated by both models)
- Confidence intervals computed with paired bootstrap or sign-style paired tests
- Statistical method is configurable in evaluation config
- Threshold constants are intentionally not fixed in this milestone

Gate output:
- Per-dimension gate status (`pass`, `fail`, `inconclusive`)
- Final composite status and explanatory rationale

## 5. Output Artifacts Contract

All artifacts are written under `outputs/` by run ID.

Required artifacts:
- `outputs/<run_id>/summary.json`
  - Aggregate metrics, confidence intervals, gate outcomes, assumptions metadata
- `outputs/<run_id>/report.md`
  - Human-readable evaluation narrative and key findings
- `outputs/<run_id>/traces.jsonl`
  - Per-example paired outputs, deterministic checks, judge scores, and deltas

Machine-readable summary fields (minimum):
- `run_id`
- `base_model_id`
- `tuned_model_id`
- `dataset_version`
- `taxonomy_version`
- `comparison_method`
- `metrics` (by split and dimension)
- `gate_outcomes`
- `assumptions`

## 6. Risks and Assumptions Requiring Validation

Risks:
- R1: LLM judge drift may change scores over time.
- R2: Ambiguous fallacy boundaries can inflate apparent disagreement.
- R3: Adversarial strata may not cover realistic attack distribution.
- R4: Consistency metrics may over-penalize stylistic but valid variation.

Assumptions:
- A1: Hybrid deterministic + LLM judging improves reliability over either alone.
- A2: Primary + acceptable alternate label policy better reflects ambiguity.
- A3: Paired comparison on identical settings isolates tuning effect.
- A4: Gated composite policy prevents quality tradeoffs hidden by aggregate means.
- A5: Threshold calibration should happen only after annotation protocol lock.

## 7. Interface Alignment (Pre-Implementation)

The evaluation package under `src/evaluation/` will expose typed interfaces for:
- benchmark loading
- deterministic checks
- LLM judging
- metric aggregation and model comparison
- report rendering
- top-level evaluation orchestration

No evaluation logic is implemented in this milestone.
