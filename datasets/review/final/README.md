# Review Final Dataset

This directory stores merged review artifacts produced by:

- `python3 -m src.review.merge_reviews`

Outputs:

- `review_dataset.jsonl` (accepted + edited merged labels)
- `merged_accepted.jsonl`
- `rejected.jsonl`
- `unresolved.jsonl`
- `summary.json`
- `manifest.json`

Generation is deterministic for the same review and teacher-run inputs.
