# Teacher Prompting Pipeline

This directory defines reusable prompt templates for teacher-style AP argument evaluation.

## Input Contract

Every template in this bundle is parameterized with:

- `{{prompt}}`: assignment prompt or task statement
- `{{essay}}`: student essay text
- `{{score}}`: provided score input (reference label)

## Output Contract

The final output must include exactly:

- `teacher_reasoning`
- `feedback`
- `rubric_analysis`
- `final_score`

See [output_schema.json](output_schema.json) for the strict JSON shape.

## Pipeline Modes

### Production single-pass

- `production_teacher.txt`
- `output_schema.json`
- `examples.md`

This is the recommended prompt bundle for deterministic supervision generation.

1. `single_pass_template.txt`
- One call that returns the final JSON directly.

2. Multi-stage mode
- `stage_1_rubric_analysis.txt`
- `stage_2_feedback.txt`
- `stage_3_finalize.txt`

The staged mode is useful when you want better controllability and easier debugging.

## Recommended Execution Order (Multi-Stage)

1. Run stage 1 with raw inputs.
2. Run stage 2 using stage 1 result as context.
3. Run stage 3 to produce final JSON only.

## Reuse Notes

- Keep placeholders unchanged to allow programmatic substitution.
- Use low temperature for deterministic teacher outputs.
- Validate outputs against `output_schema.json` before accepting records.
- Do not emit markdown; JSON only at finalization stage.
