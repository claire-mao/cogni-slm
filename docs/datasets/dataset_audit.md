# Dataset Audit (Phase 6)

## Audit Scope

Because no raw AP Language essays exist in `datasets/raw/`, a training-ready Dataset v1 could not be generated.

To satisfy audit readiness, a suitability audit was run on the only available 50-example dataset artifact:
- `datasets/processed/golden/golden-20260708T202613Z/dataset.jsonl`

This file is synthetic fallacy data and was audited only to confirm it is not suitable as AP rubric training data.

## Method

- Random sample size: 50 (seed = 42; all 50 records in file)
- Checks:
  - JSON validity
  - Required AP rubric schema fields
  - Rubric score availability
  - Feedback quality suitability for AP essay scoring
  - Duplicated reasoning patterns
  - Hallucination risk relative to real student essays

## Results

- Total examples inspected: 50
- Accepted: 0
- Rejected: 50

### Rejection Reasons

- Missing Dataset v1 AP schema fields (`id`, `essay`, `rubric_score`, `score_explanation`, `strongest_evidence`, `weakest_reasoning`, `revision`, `teacher_reasoning`, `metadata`): 50
- Synthetic non-student source (`source_id` begins with `synthetic:`): 50
- Missing AP rubric score field (`rubric_score`): 50

## Quality Signals Observed

- JSON validity: 50/50 valid JSON lines
- Feedback structure alignment to AP rubric: 0/50
- Duplicated reasoning signal:
  - Unique reasoning strings: 28
  - Duplicate reasoning instances: 22
  - Max repeat count for one reasoning string: 2
- Hallucination risk for AP essay supervision: High
  - Records are synthetic short arguments, not grounded student essays.

## Estimated Dataset Quality (for AP rubric fine-tuning)

- Overall quality estimate: **0/10 (not usable)**

## Recommendations

1. Populate `datasets/raw/` with real AP Language student argumentative essays under approved licensing.
2. Re-run `scripts/generate_training_dataset.py` with a real teacher provider (non-mock).
3. Run validation/filter/dedup/split pipeline on generated outputs.
4. Repeat a 50-example manual audit on generated AP-schema records before training.
