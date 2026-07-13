# Teacher Prompting Pipeline

This directory stores prompt templates and output schemas used by teacher-model labeling runs.

## Prompt Bundles
- `production_teacher.txt` + `output_schema.json`
  - Legacy essay-evaluation prompt bundle.
- `ap_fallacy_tutor_teacher.txt` + `ap_fallacy_tutor_output_schema.json`
  - Legacy wrapped AP fallacy tutor bundle.
- `ap_fallacy_behavior_schema.json`
  - Canonical direct seven-field schema used by production labeling.

## Input Placeholders
- `{{prompt}}`
- `{{essay}}`
- `{{score}}`

## AP Tutor Production Notes

Production labeling uses the direct schema and intentionally omits legacy essay-grading
fields such as `score`, `confidence`, and `rubric_analysis`. The resulting object has
exactly the seven tutoring fields required for supervised training.

Use low temperature and strict validation for consistent labels.
