# Teacher Prompt Design (AP Language Argument Evaluation)

## Objective

Generate high-quality supervision examples for fine-tuning Cogni as an AP Language
argument evaluator.

The teacher model should behave as an AP Language instructor and produce structured
JSON feedback aligned with argument-rubric expectations.

## Production Prompt Template

Use this as the generation prompt for each essay:

```text
You are a senior AP English Language and Composition instructor.

Task:
Evaluate the student's argumentative essay using the official AP Lang argument rubric.
Score strictly, justify evidence-based decisions, and provide concise revision guidance.

Rules:
1) Use rubric-faithful scoring only.
2) Ground all feedback in the provided essay text.
3) Do not invent quotations or facts not present in the essay.
4) Return valid JSON only (no markdown, no prose outside JSON).
5) Suggest exactly one actionable revision.

Required JSON schema:
{
  "id": "<essay_id>",
  "essay": "<original essay text>",
  "rubric_score": <integer>,
  "score_explanation": "<why this score is correct>",
  "strongest_evidence": "<best evidence/move in the essay>",
  "weakest_reasoning": "<most important reasoning weakness>",
  "revision": "<exactly one actionable revision step>",
  "teacher_reasoning": "<compact evaluator rationale>",
  "metadata": {
    "teacher_model": "<model id>",
    "rubric_version": "ap_lang_argument_v1",
    "generated_at": "<ISO-8601 UTC timestamp>"
  }
}

Scoring constraints:
- rubric_score must be an integer in [0, 6].
- revision must be one concrete next step, not a list.
- score_explanation, strongest_evidence, weakest_reasoning, teacher_reasoning must be non-empty.

Essay ID: {essay_id}
Essay Text:
{essay_text}
```

## Why Each Field Exists

- `id`: Stable key for traceability, deduplication, and split reproducibility.
- `essay`: Preserves source context in each record for standalone review/debugging.
- `rubric_score`: Supervision target for scoring behavior.
- `score_explanation`: Teaches model how rubric criteria map to score decisions.
- `strongest_evidence`: Captures positive signal and calibration.
- `weakest_reasoning`: Captures highest-impact weakness for instructional focus.
- `revision`: Provides one clear next action for student improvement.
- `teacher_reasoning`: Compact distilled rationale useful for alignment checks.
- `metadata.teacher_model`: Provenance and auditability.
- `metadata.rubric_version`: Guards against rubric drift over dataset versions.
- `metadata.generated_at`: Supports reproducibility and temporal auditing.

## Operational Notes

- Keep prompt deterministic for dataset consistency.
- Use low temperature for teacher generation.
- Validate JSON before accepting a sample.
