# Cogni Experiment Plan

## 1. Objective
Design a controlled experiment to test whether a fine-tuned Cogni model follows the Behavior Specification more reliably than the untuned base model.

This is a pre-implementation plan only. No results are reported.

## 2. Core Research Hypothesis

### Primary hypothesis (H1)
A tuned model (trained with behavior-aligned synthetic supervision) will outperform the base model on Behavior Specification adherence while maintaining or improving logical fallacy accuracy and robustness.

### Secondary hypotheses
- H2: Explicit analogy-structure supervision improves transfer-oriented explanation quality.
- H3: No-fallacy and adversarial examples reduce false positives and brittle instruction-following.
- H4: PEFT-based tuning can achieve practical gains without full-model finetuning.

## 3. Experimental Variables

### 3.1 Independent variable
Model condition:
- `base`: Qwen3-1.7B (untuned baseline)
- `tuned`: Qwen3-1.7B + Cogni instruction/data tuning pipeline

### 3.2 Dependent variables
Measured on matched evaluation inputs:
- Behavior adherence score (B1-B7 and P1-P5 coverage)
- Logical fallacy accuracy (primary + acceptable alternate label policy)
- Robustness score under adversarial prompts
- Consistency score across repeats and paraphrases
- Composite gate outcome (`pass`, `fail`, `inconclusive`)

### 3.3 Controlled variables
Held constant for base vs tuned comparison:
- evaluation dataset version and split membership
- prompt templates and system instruction wrapper
- decoding parameters and max generation limits
- evaluator/judge versions and rubric definitions
- random seed policy and repeat count
- hardware class and runtime environment where feasible

## 4. Success Criteria

A run is successful if all are true:
1. Tuned model improves over base on primary dimensions:
   - behavior adherence
   - fallacy accuracy
2. Tuned model shows no regression on:
   - adversarial robustness
   - consistency
3. Paired comparison confidence intervals and significance diagnostics are reported for each dimension.
4. Outputs remain behavior-spec-compliant in required section structure and ordering.

Threshold values remain configuration-managed and are intentionally not hardcoded in this planning document.

## 5. Failure Criteria

A run is considered failed if any are true:
- tuned model regresses on robustness or consistency gates
- behavior-spec contract violations increase materially vs base
- gains appear only in aggregate while key fallacy families degrade
- evaluation is not reproducible from pinned configs/artifacts
- benchmark contamination or leakage is detected

## 6. Evaluation Methodology

### 6.1 Dataset and split policy
Use the dataset policy already defined in `docs/dataset_spec.md`:
- development splits: `train` 70%, `validation` 15%, `test` 15%
- strictly isolated held-out benchmark for final comparisons
- adversarial and non-adversarial strata in each evaluation context where applicable

### 6.2 Measurement stack
Use the hybrid stack from `docs/evaluation_design.md`:
1. deterministic contract checks
2. rubric-based LLM judge scoring
3. per-example paired deltas and aggregate metrics
4. gated composite decisioning

### 6.3 Statistical comparison protocol
- paired base-vs-tuned tests on identical examples
- confidence intervals via paired bootstrap (or configured paired test alternative)
- report uncertainty and inconclusive outcomes explicitly

### 6.4 Analysis slices
All metrics stratified by:
- fallacy family
- ambiguity level
- adversarial type
- no-fallacy subset
- domain and reflection-style tags

### 6.5 Human spot-audit protocol
Include a targeted manual audit subset to validate:
- analogy mapping faithfulness
- pedagogical clarity
- calibration of confidence language
- no-fallacy handling quality

Human review is a validation layer, not a replacement for automated evaluation.

## 7. Threats to Validity and Mitigations

### 7.1 Construct validity
Risk: metrics may not fully capture tutoring quality.
Mitigation: combine contract checks, rubric scores, and manual audit slices.

### 7.2 Internal validity
Risk: pipeline/config drift confounds base vs tuned differences.
Mitigation: strict config pinning, deterministic artifacts, and paired evaluation.

### 7.3 External validity
Risk: synthetic and benchmark distributions may not match real learner prompts.
Mitigation: include cross-domain coverage and adversarial variants; add future real-user pilot phase.

### 7.4 Statistical validity
Risk: over-interpretation of noisy differences.
Mitigation: confidence intervals, per-slice reporting, and explicit inconclusive status.

### 7.5 Data leakage validity
Risk: benchmark examples leak into prompt/rubric tuning.
Mitigation: held-out benchmark isolation and source-overlap checks.

## 8. Execution Sequence (Pre-Implementation to First Readout)
1. Lock taxonomy version and annotation guidance.
2. Implement data generation pipeline modules.
3. Produce dataset versions with manifests and hashes.
4. Implement training pipeline with PEFT-first path.
5. Implement evaluation pipeline end-to-end.
6. Run baseline base-vs-tuned experiment.
7. Publish reproducible report artifacts and error taxonomy.

## 9. Reporting Requirements
Every experiment report must include:
- hypothesis and run configuration
- dataset/model/evaluator versions
- aggregate and per-slice metrics
- gate outcomes and uncertainty
- top failure modes with representative examples
- threats to validity observed in the run

## 10. Assumptions to Validate
- A1: behavior adherence gains correlate with better learner-facing quality.
- A2: no-fallacy coverage reduces over-triggering in ambiguous cases.
- A3: PEFT tuning capacity is sufficient for target behavior improvements.
- A4: judge rubric stability is adequate for release gating.
- A5: held-out benchmark coverage reflects realistic classroom-like arguments.
