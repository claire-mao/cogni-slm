# Teacher Inference Outputs

This directory stores local teacher-model generations produced by:

- `scripts/run_teacher_inference.py`

## Expected files

- `predictions.jsonl`: one record per essay with
  - `reasoning`
  - `feedback`
  - `predicted_score`
  - `confidence`
- `failures.jsonl`: failed inference attempts
- `summary.json`: run-level metadata and counters

## Notes

- Generations are local-only (`local_files_only=True`, offline env vars set in script).
- Input records must include `prompt`, `essay`, and `score`.
- Default input source is `datasets/training`.
