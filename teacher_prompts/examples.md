# Production Teacher Prompt Examples

This file shows reusable invocation patterns for `production_teacher.txt`.
Examples use placeholders only and do not provide dataset labels.

## Example 1: Without Optional Score

Input payload:

```json
{
  "prompt": "<assignment prompt text>",
  "essay": "<student essay text>",
  "score": ""
}
```

Expected JSON structure (placeholders):

```json
{
  "score": "<integer_0_to_60>",
  "confidence": "<number_0_to_1>",
  "rubric": {
    "criteria": [
      {
        "criterion": "claim",
        "judgment": "meets|partially_meets|does_not_meet",
        "evidence": "<essay-grounded evidence>",
        "impact": "<learning impact>"
      },
      {
        "criterion": "evidence",
        "judgment": "meets|partially_meets|does_not_meet",
        "evidence": "<essay-grounded evidence>",
        "impact": "<learning impact>"
      },
      {
        "criterion": "reasoning",
        "judgment": "meets|partially_meets|does_not_meet",
        "evidence": "<essay-grounded evidence>",
        "impact": "<learning impact>"
      },
      {
        "criterion": "organization",
        "judgment": "meets|partially_meets|does_not_meet",
        "evidence": "<essay-grounded evidence>",
        "impact": "<learning impact>"
      },
      {
        "criterion": "style",
        "judgment": "meets|partially_meets|does_not_meet",
        "evidence": "<essay-grounded evidence>",
        "impact": "<learning impact>"
      }
    ],
    "summary": "<rubric summary>"
  },
  "reasoning": {
    "summary": "<compact rationale>",
    "steps": [
      "<step 1>",
      "<step 2>",
      "<step 3>"
    ]
  },
  "logical_analysis": {
    "claim_quality": "strong|mixed|weak",
    "evidence_quality": "strong|mixed|weak",
    "coherence": "strong|mixed|weak",
    "counterargument_handling": "strong|mixed|weak|not_present",
    "consistency_checks": [
      "<consistency note>"
    ]
  },
  "fallacies": {
    "detected": "<true_or_false>",
    "primary": "<fallacy_or_none>",
    "secondary": [
      "<optional_additional_fallacy>"
    ],
    "evidence": "<essay-grounded support>",
    "severity": "none|low|moderate|high"
  },
  "feedback": {
    "strengths": [
      "<strength 1>"
    ],
    "priorities": [
      "<priority 1>"
    ],
    "student_facing_summary": "<clear educational guidance>"
  },
  "revision_plan": {
    "goal": "<single revision goal>",
    "actions": [
      "<action 1>",
      "<action 2>",
      "<action 3>"
    ],
    "expected_impact": "<expected learning or score impact>"
  }
}
```

## Example 2: With Optional Score

Input payload:

```json
{
  "prompt": "<assignment prompt text>",
  "essay": "<student essay text>",
  "score": "<optional reference score>"
}
```

Behavior expectation:

- The model may consider `score` as weak context.
- The model must still produce an evidence-grounded independent judgment.
- The final output must always conform to `output_schema.json`.

## Validation Checklist

1. JSON parses with no trailing text.
2. Top-level keys exactly match required order in `production_teacher.txt`.
3. Output validates against `teacher_prompts/output_schema.json`.
4. Evidence fields are grounded in the essay text.
5. Tone is educational and actionable.
