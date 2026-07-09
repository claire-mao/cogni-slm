# Final Rebuild Verification

## Objective

Verify full reproducibility starting from `datasets/raw/` with no external downloads.

## Command Executed

```bash
python3 scripts/rebuild_all.py
```

## Result

- Status: **PASS**
- Source of truth: `datasets/raw/`
- Rebuild report: `docs/reports/rebuild.md`

## Pipeline Stages Verified

- Dataset generation / staging build: PASS
- Normalization: PASS
- Quality scoring: PASS
- Deduplication: PASS
- License verification report generation: PASS
- Provenance index generation: PASS
- Provenance repair report generation: PASS
- Training dataset build: PASS
- Prompt-group candidate split generation: PASS
- Metadata leakage report generation: PASS
- Artifact synchronization from isolated workspace: PASS (`copied=19`, `missing=0`)

## Artifacts Confirmed

- `datasets/final/` regenerated
- `datasets/training/` regenerated
- `datasets/training_provenance/` regenerated
- `datasets/training_candidates/prompt_group_split/` regenerated
- `docs/reports/rebuild.md` regenerated
- `docs/reports/provenance_repair.md` regenerated
- `docs/reports/training_dataset.md` regenerated
- `docs/reports/final_verification.md` regenerated
- `docs/reports/metadata_leakage.md` regenerated
- `docs/reports/group_split.md` regenerated

## HF DatasetBuilder Verification

Executed:

```bash
python3 datasets/build_dataset.py --raw-root datasets/raw --output-dir datasets/hf/dataset_dict --overwrite --summary-path datasets/hf/build_summary.json
```

Result: PASS (`datasets/hf/dataset_dict` built and loadable via `datasets.load_from_disk`).

## Manual Steps

- Required manual steps to complete rebuild: **none**.
- Non-blocking environment warning observed from Arrow CPU capability probes (`sysctlbyname ... Operation not permitted`) during provenance generation; pipeline completed successfully.

## Notes

- Current rebuilt training dataset contains only `train` split rows (`12413`) and no `validation`/`test` rows. This is reproducible from current upstream processed inputs and does not block repository commit readiness, but should be addressed before GPU training/evaluation campaigns.
