# Repository Snapshot

## Current Statistics

- Python files: `114`
- Python lines of code: `22,965`
- Scripts (`scripts/*.py`): `28`
- Source modules (`src/**/*.py`): `50`
- Unit test files (`tests/test_*.py`): `10`
- Passing tests: `35`
- Config files (`configs/**`): `12`
- Active reports (`docs/reports/*.md`): `27`
- Archived reports (`docs/reports/archive/*.md`): `22`

## Dataset Inventory Snapshot

- Source datasets discovered under `datasets/raw/`: `asap2`, `asap_aes`, `persuade2`
- Final dataset rows:
  - `datasets/final/train.jsonl`: `12413`
  - `datasets/final/validation.jsonl`: `0`
  - `datasets/final/test.jsonl`: `0`
- Quality-deduped dataset rows: `12413`
- Training dataset rows (`datasets/training`): `12413` (`train` split)

## Pipeline State

- Rebuild pipeline from raw data: **PASS**
- HF compatibility validation: **PASS (6/6)**
- Provenance pipeline: **PASS**
- Metadata leakage check: **PASS**

## Current Project Phase

- Current phase: **Pre-commit verification / production hardening (post-Phase 6 data pipeline)**

## Remaining Tasks Before GPU Training

1. Restore non-empty validation/test training splits from reproducible source transformations.
2. Confirm training/evaluation split policy aligns with prompt leakage controls for model benchmarking.
3. Lock training run config (batch size, precision, checkpoints) for target GPU profile.
4. Run one controlled dry-run on target GPU hardware with adapter-only save path.
5. Freeze a release candidate dataset manifest for the first training run.
