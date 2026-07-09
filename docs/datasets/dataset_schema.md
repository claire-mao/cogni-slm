# Fine-Tuning Dataset Schema

## Canonical Record

```json
{
  "id": "essay-000123",
  "essay": "Student argumentative essay text...",
  "rubric_score": 4,
  "score_explanation": "The essay establishes a defensible thesis and relevant evidence, but commentary is uneven.",
  "strongest_evidence": "Paragraph 3 uses a concrete policy example tied to the claim.",
  "weakest_reasoning": "Counterargument handling is asserted but not fully developed.",
  "revision": "Add one paragraph that directly rebuts a plausible counterclaim using specific evidence.",
  "teacher_reasoning": "Score reflects thesis/evidence strength with limited line-of-reasoning development.",
  "metadata": {
    "teacher_model": "provider/model-name",
    "rubric_version": "ap_lang_argument_v1",
    "generated_at": "2026-07-08T00:00:00Z",
    "source_path": "datasets/raw/sample_001.txt",
    "placeholder": false
  }
}
```

## Field Definitions

- `id` (`string`, required)
  - Globally unique example identifier.
  - Used for deduplication, filtering, and split assignment.

- `essay` (`string`, required)
  - Raw essay content evaluated by the teacher.
  - Must be non-empty and above minimum length threshold.

- `rubric_score` (`integer`, required)
  - AP Lang argument rubric score.
  - Valid range: `0..6`.

- `score_explanation` (`string`, required)
  - Rubric-grounded explanation for assigned score.
  - Must be specific and evidence-based.

- `strongest_evidence` (`string`, required)
  - Most effective evidence/reasoning move in the essay.
  - Supports balanced instruction and model calibration.

- `weakest_reasoning` (`string`, required)
  - Most important logic/argument weakness.
  - Drives targeted revision feedback.

- `revision` (`string`, required)
  - Exactly one actionable revision recommendation.
  - Must be concrete and implementable.

- `teacher_reasoning` (`string`, required)
  - Compact rationale for auditability and supervision quality checks.

- `metadata` (`object`, required)
  - Provenance and generation context.
  - Expected keys:
    - `teacher_model` (`string`)
    - `rubric_version` (`string`)
    - `generated_at` (`string`, ISO-8601 UTC)
    - `source_path` (`string`)
    - `placeholder` (`boolean`, optional)

## Validation Rules

1. JSON must parse cleanly.
2. All required fields must exist.
3. Required text fields must be non-empty after trimming.
4. `rubric_score` must be an integer in `[0, 6]`.
5. `essay` must exceed configured minimum word count.
6. Feedback fields should exceed configured minimum word count.

## Storage Conventions

- Generator output: one JSON file per essay.
- Filtered/deduplicated/split output: JSONL for training pipelines.
- IDs must remain stable across pipeline stages.
