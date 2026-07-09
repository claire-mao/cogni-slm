# Rebuild Pipeline Report

## Goal

Rebuild dataset artifacts reproducibly starting only from `datasets/raw/`.

## Isolation Strategy

- Repository root: `/Users/clairemao/Documents/cogni-slm`
- Raw input root: `/Users/clairemao/Documents/cogni-slm/datasets/raw`
- Isolated workspace: `/Users/clairemao/Documents/cogni-slm/.rebuild_workspace`
- Workspace includes only:
  - `datasets/raw/`
  - `scripts/` (thin wrappers)
  - `src/`
  - `evaluation/`
  - `training/`
  - `datasets/build_dataset.py`
- All rebuild commands run inside this isolated workspace.

## Preprocessing Steps

1. Validate raw files (`csv/tsv/json/jsonl/txt`) exist under `datasets/raw/`.
2. Build Hugging Face staging dataset from raw files (`datasets/build_dataset.py`).
3. Normalize to unified schema (`scripts/normalize_unified_schema.py`).
4. Sanitize unified JSONL (drop malformed rows).
5. Compute quality scores and filter low-quality rows.
6. Deduplicate and materialize canonical `datasets/final/{train,validation,test}.jsonl` + merged file.
7. Verify licenses and write license report.
8. Build provenance index (`datasets/final/provenance.parquet`).
9. Build training dataset (`datasets/training`) and provenance sidecar.
10. Verify final dataset integrity and HF loadability.
11. Regenerate provenance repair report (`docs/reports/provenance_repair.md`).
12. Remove score/label keys from training provenance sidecar.
13. Generate metadata leakage report (`docs/reports/metadata_leakage.md`).
14. Generate prompt-group candidate split (`docs/reports/group_split.md`).
15. Sync rebuilt artifacts back to repository.

## Execution

- Mode: `dry-run`
- Total step runtime: `0.10` seconds

| step | status | duration_s | details |
|---|---|---:|---|
| prepare_workspace | PASS | 0.10 | raw_files=8 |
| planned | PLANNED | 0.00 | scripts/build_dataset.py --workspace-root . --skip-download |
| planned | PLANNED | 0.00 | scripts/create_provenance_index.py --final-dir datasets/final |
| planned | PLANNED | 0.00 | scripts/build_training_dataset.py --input-jsonl datasets/final/quality_deduped.jsonl |
| planned | PLANNED | 0.00 | scripts/create_prompt_group_split_candidate.py |
| planned | PLANNED | 0.00 | sync artifacts back to repository |

## Artifact Sync

- Paths copied: `0`
- Missing paths: `0`

## Rebuild Command

```bash
python3 scripts/rebuild_all.py
```

Use `--dry-run` to preview without executing.
