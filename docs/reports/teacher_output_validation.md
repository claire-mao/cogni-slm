# Teacher Output Validation Implementation

Implemented:

- `src/teacher/validation.py`

Scope:

- Validates precomputed teacher outputs only.
- Does not run model inference.
- Designed to work with records loaded via `src.teacher.io.load_predictions`.

## Checks Implemented

1. JSON validity

- Extracts output JSON from `output`, `predicted`, `response_json`, `raw_output`, or `response_text`.
- Fails when output is missing or not parseable as a JSON object.

2. Missing fields

- Enforces required structure for:
  - `score`
  - `confidence`
  - `rubric`
  - `reasoning`
  - `logical_analysis`
  - `fallacies`
  - `feedback`
  - `revision_plan`
- Reports missing/typed-wrong paths (for example `reasoning.steps`).

3. Score range

- Valid only when `score` is an integer in `[0, 60]`.

4. Hallucinated rubric items

- Validates rubric criteria against allowed set:
  - `claim`, `evidence`, `reasoning`, `organization`, `style`
- Flags unknown criteria, duplicates, and missing required criteria.
- Adds warning if there is zero overlap with gold rubric labels (when available).

5. Unsupported feedback

- Flags empty feedback.
- Flags feedback matching unsupported patterns (for example fabricated authority references).
- Uses lexical grounding heuristic against essay text; very low overlap is flagged as unsupported.

6. Reasoning completeness

- Computes completeness score in `[0,1]` from:
  - `reasoning.summary` presence
  - `reasoning.steps` completeness (>=3 non-empty steps)
  - `logical_analysis` required fields + non-empty `consistency_checks`
- Marks pass when completeness >= `0.67`.

7. Confidence calibration

- Extracts `confidence` in `[0,1]`.
- Builds per-example calibration target when gold is available:
  - score correctness proxy: `abs(predicted_score - gold_score) <= 1`
  - fallacy correctness proxy: overlap between predicted and expected fallacies
  - target = mean of available proxies
- Computes per-example Brier: `(confidence - target)^2`.
- Computes per-model:
  - mean Brier
  - 10-bin ECE
  - overconfidence rate (`confidence >= 0.8` and `target <= 0.5`)

## Outputs

The module provides:

- Example-level results: `ExampleValidationResult`
- Finding-level diagnostics: `ValidationFinding`
- Model-level summaries: `ModelValidationSummary`

Optional file writers:

- `teacher_validation_results.jsonl`
- `teacher_validation_summary.json`
- `teacher_validation_summary.csv`

via `write_validation_outputs(output_dir=..., results=..., summaries=...)`.

## Programmatic Usage

```python
from pathlib import Path
from teacher.io import load_gold_examples, load_predictions
from teacher.validation import run_validation, write_validation_outputs

gold = load_gold_examples(Path("datasets/gold/gold_v1.jsonl"))
preds = load_predictions(Path("path/to/predictions.jsonl"))
results, summaries = run_validation(predictions=preds, gold_examples=gold)
write_validation_outputs(
    output_dir=Path("outputs/teacher_benchmark/validation"),
    results=results,
    summaries=summaries,
)
```

## Notes

- Validation is deterministic and rule-based.
- No external API calls are performed.
- Heuristic checks (especially unsupported feedback grounding) are conservative and should be reviewed with sampled manual audits.
