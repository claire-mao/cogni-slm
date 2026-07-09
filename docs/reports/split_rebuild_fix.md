# Split Rebuild Fix Report

## Goal

Investigate why reproducible rebuild produced only `train` and fix the pipeline so `rebuild_all.py` regenerates:

- `datasets/training/train`
- `datasets/training/validation`
- `datasets/training/test`

without manual split creation.

## Root-Cause Trace

### 1. Split state across stages

Observed split counts during rebuild pipeline:

- `datasets/processed/unified/unified_all.sanitized.jsonl`
  - `train: 25755`, `validation: 23435`, `test: 4198`
- `datasets/final/quality_scored.jsonl`
  - `train: 25755`, `validation: 23435`, `test: 4198`
- `datasets/final/quality_filtered.jsonl`
  - `train: 24656`, `validation: 3912`, `test: 3925`
- `datasets/final/quality_deduped.jsonl` (before fix)
  - `train: 12413`, `validation: 0`, `test: 0`

### 2. Why splits collapsed

The collapse happened in `src/data/build_dataset.py::deduplicate_quality_filtered`:

- Deduplication used global ID/text dedup across all splits.
- Records were processed in file order.
- First-seen duplicates were predominantly from `train`.
- Duplicate `validation/test` rows were removed and never reassigned.

Net effect: deduped dataset retained only `train` split assignment.

## Requested Cause Classification

| Candidate cause | Result | Evidence |
|---|---|---|
| missing metadata | Not primary cause | Split metadata existed through `quality_filtered.jsonl`. |
| prompt grouping | Not cause | Prompt grouping runs after training build and did not create collapse. |
| filtering | Contributing, not root cause | Filtering reduced val/test volume but did not remove them entirely. |
| rebuild ordering | Not cause | Stage order is valid; collapse occurs inside dedup stage logic. |
| split assignment | **Root cause** | Global dedup preserved first-seen split labels (`train`). |

## Fix Implemented

File changed: `src/data/build_dataset.py`

### Behavior-preserving constraints honored

- No raw dataset content changes.
- No manual split files authored by hand.
- Reproducibility preserved.

### Logic update

After deduplicating records, the pipeline now assigns splits deterministically using a stable hash partition on each deduped record (`id + normalized text`):

- deterministic ratio target: `0.8 / 0.1 / 0.1`
- exact deterministic assignment by hash-sorted order
- safeguards to avoid empty splits when record count permits

This ensures split assignment is reproducible and independent of input ordering.

### Additional robustness

- `src/data/build_training_dataset.py` now verifies `load_from_disk()` expects all required splits: `train/validation/test`.

## Verification

Executed:

```bash
python3 scripts/rebuild_all.py
```

Post-fix rebuilt outputs:

- `datasets/final/quality_deduped.jsonl`
  - `train: 9930`, `validation: 1241`, `test: 1242`
- `datasets/final/train.jsonl`: `9930`
- `datasets/final/validation.jsonl`: `1241`
- `datasets/final/test.jsonl`: `1242`
- `datasets/training` via `load_from_disk()`:
  - splits: `['train', 'validation', 'test']`
  - rows: `train=9930, validation=1241, test=1242`
  - schema per split: `['prompt', 'essay', 'score']`

## Reproducibility Status

- Deterministic split regeneration: **PASS**
- `rebuild_all.py` end-to-end: **PASS**
- `load_from_disk()` integrity: **PASS**
