# Rebuild Guide

## Goal

Rebuild downstream dataset artifacts starting only from `datasets/raw/` in an isolated workspace.

## Command

```bash
python scripts/rebuild_all.py --dry-run
python scripts/rebuild_all.py
```

## Isolation Strategy

The rebuild workspace includes only required code and data inputs:

- `datasets/raw/`
- `datasets/build_dataset.py`
- `scripts/` (CLI wrappers)
- `src/` (pipeline implementations)
- `evaluation/`
- `training/`
- `pyproject.toml`

## Processing Stages

1. Verify parseable raw files exist under `datasets/raw/`.
2. Build HF staging dataset.
3. Normalize into unified schema.
4. Sanitize malformed rows.
5. Run quality scoring/filtering.
6. Deduplicate and materialize final JSONL splits.
7. Verify licenses.
8. Build provenance index.
9. Build training dataset + provenance sidecar.
10. Verify final dataset integrity and HF compatibility.
11. Regenerate provenance repair report (`docs/reports/provenance_repair.md`).
12. Remove score-like keys from provenance sidecar.
13. Generate metadata leakage report (`docs/reports/metadata_leakage.md`).
14. Generate prompt-group candidate split report (`docs/reports/group_split.md`).
15. Sync rebuilt artifacts back into the repository.

## Outputs

- Canonical reports: `docs/reports/`
- Core artifacts: `datasets/final/`, `datasets/training/`, `datasets/training_provenance/`

## Notes

- `--dry-run` plans and validates steps without running transformations.
- Existing CLI interfaces are preserved through `scripts/` wrappers.
