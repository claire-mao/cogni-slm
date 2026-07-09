# Gold Dataset Construction Pipeline

Implemented:

- `/Users/clairemao/Documents/cogni-slm/src/data/build_gold_dataset.py`

This pipeline builds a versioned gold dataset from approved review examples and
adds integrity and review-governance metadata.

## Scope

- Input: approved review examples (`JSONL`)
- Optional input: adjudication log (`JSONL`) from reviewer history
- Output root: `datasets/gold/`
- No model inference

## Supported Requirements

The builder supports:

- versioning
- checksums
- review metadata
- adjudication history

## Input Contract

Primary input defaults to:

- `datasets/review/final/review_dataset.jsonl`

Each row should be an approved review record (typically `accept` or `edit`) with
fields such as:

- `case_id`
- `example_id`
- `prompt`
- `essay`
- `merged_label` (or equivalent label payload)
- review metadata (`review_id`, `reviewer_id`, `decision`, `flags`, `notes`)

Optional adjudication log defaults to:

- `datasets/review/reviews.jsonl`

When provided, full event history for each `case_id` is attached to output rows.

## Output Layout

Per version, the pipeline writes:

- `datasets/gold/versions/<version>/gold_dataset.jsonl`
- `datasets/gold/versions/<version>/adjudication_history.jsonl`
- `datasets/gold/versions/<version>/checksums.json`
- `datasets/gold/versions/<version>/manifest.json`

Root-level pointers:

- `datasets/gold/manifest.json` (latest build manifest)
- `datasets/gold/version_index.json` (all discovered versions + latest pointer)

## Gold Record Schema

Each row in `gold_dataset.jsonl` includes:

- `example_id`
- `version`
- `source`
- `license`
- `difficulty`
- `prompt`
- `essay`
- `gold_score`
- `rubric`
- `expected_reasoning_skills`
- `expected_fallacies`
- `gold_label`
- `notes_for_reviewers`
- `review_metadata`
- `adjudication_history`
- `provenance`
- `record_checksum_sha256`

## Versioning

- If `--version` is omitted, the builder auto-increments `gold_vN` by scanning
  `datasets/gold/versions/`.
- If `--version` is provided, it is normalized and stored as that release.

## Checksums

`checksums.json` contains deterministic hashes for:

- approved input file
- adjudication log file (if present)
- emitted gold dataset
- emitted adjudication history file
- aggregate row checksum digest

Each output row also carries `record_checksum_sha256` for row-level integrity.

## Review Metadata and Adjudication

`review_metadata` captures latest decision context:

- reviewer identity
- decision type
- selected teacher
- hallucination/rubric flags
- rubric correction marker
- notes and timestamps

`adjudication_history` contains chronological review events for the same
`case_id`, allowing traceability of edits and final acceptance.

## CLI

```bash
python3 -m src.data.build_gold_dataset \
  --approved-path datasets/review/final/review_dataset.jsonl \
  --adjudication-log datasets/review/reviews.jsonl \
  --output-root datasets/gold \
  --version gold_v1
```

All CLI flags are optional except the approved input existing at runtime.

## Guardrails

- Only approved rows are converted into gold rows (`accept`, `edit`, `approved`).
- Missing label payloads are skipped and listed in manifest diagnostics.
- Build order is deterministic via stable sorting on example/case/review IDs.
