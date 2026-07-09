# Teacher Stack v1

This report freezes the production teacher stack as Version 1 for educational assessment supervision.

## Frozen Stack

- Primary teacher: GPT-5
- Verifier: Claude Opus 4
- Reasoning checker: DeepSeek R1
- Config: `configs/teacher/teacher_stack_v1.json`
- Prompt version: `production_teacher_v1`
- JSON schema: `production_teacher_output_schema_v1` (`teacher_prompts/output_schema.json`)

## Why Each Model Was Selected

### GPT-5 (Primary Teacher)

- Selected for strong instruction following, stable strict-JSON behavior, and broad capability across scoring, rubric alignment, and educational feedback generation.
- Expected to provide the canonical first-pass supervision output for all intended tasks.

### Claude Opus 4 (Verifier)

- Selected as an independent high-capability verifier to reduce single-model bias in rubric interpretation and reasoning quality checks.
- Expected to be strong at catching nuanced rubric misses, argument-structure issues, and weak feedback grounding.

### DeepSeek R1 (Reasoning Checker)

- Selected for low-cost, high-throughput secondary reasoning checks and contradiction detection.
- Expected to provide an efficient logic/fallacy consistency signal before escalation.

## Responsibilities

- Primary teacher (GPT-5):
  - Produce full structured output for all seven tasks.
  - Provide score, rubric analysis, reasoning, fallacy analysis, feedback, and revision plan.
- Verifier (Claude Opus 4):
  - Cross-check rubric adherence, reasoning completeness, fallacy decisions, and feedback support.
  - Trigger escalation when confidence or agreement gates fail.
- Reasoning checker (DeepSeek R1):
  - Check logic consistency, fallacy detection coherence, and argument-quality alignment.
  - Flag inconsistencies quickly at lower marginal cost.

## Expected Strengths

- Better quality control than a single-teacher pipeline due to independent verification signals.
- Deterministic settings (`temperature=0`) and strict schema improve reproducibility.
- Cost containment by reserving Opus verification/escalation for uncertain or conflicting cases.

## Expected Failure Modes

- Shared blind spots across models on ambiguous or rubric-edge essays.
- Overconfident but shallow reasoning when evidence is weak.
- Occasional schema-valid but educationally generic feedback.
- Provider-side latency/rate-limit bursts causing retry churn.
- Divergent fallacy labels on subtle rhetorical cases.

## Escalation Policy

Escalate to human review when any of the following occurs:

- Invalid JSON or schema failure after retries.
- Primary/verifier disagreement on score (`>= 2` points).
- Primary/verifier disagreement on primary fallacy label.
- Any role confidence below configured low-confidence threshold.
- Retry policy exhausted for any role.

Operationally:

- Accept automatically only when confidence and agreement thresholds pass.
- Route borderline cases to verifier/checker.
- Route unresolved disagreements to human adjudication queue.

## Reproducibility Considerations

- Fixed prompt version and schema version are required for every run.
- Deterministic defaults (`temperature=0`, fixed seed where supported) are enforced.
- Prompt hash and schema hash should be logged with run metadata.
- Raw outputs, token usage, and latency should be persisted for auditability.
- Provider/model version pins should be reviewed before any stack version bump.

## Execution Guardrail

- This stack definition is configuration-only.
- No inference was executed while generating this report.
