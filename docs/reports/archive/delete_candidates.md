# Delete Candidates (Review Before Any Deletion)

This list identifies files/directories that look generated, temporary, superseded, duplicated, or obsolete.
No deletions were performed in this step.

| Filename / Path | Reason | safe_to_delete |
|---|---|---|
| `outputs/evaluation_harness/` | Run-specific generated benchmark outputs; reproducible from scripts. | yes |
| `outputs/baseline/` | Generated baseline artifacts (`.json/.md/.jsonl`); reproducible. | yes |
| `outputs/inference_demo/` | One-off inference demo outputs; reproducible. | yes |
| `outputs/data_ingestion/report.md` | Generated report output; reproducible from ingestion script. | yes |
| `.hf_cache/` | Local HF cache only; not source-of-truth. | yes |
| `datasets/.hf_cache/` | Local datasets cache; regenerable from pipeline runs. | yes |
| `reports/*.md` (legacy one-time analysis reports) | Most are one-time generated analyses; should be archived, not deleted immediately. | no |
| `reports/figures/` | Generated chart outputs backing reports; archive with reports. | no |
| `dataset_cards/*.md` | Generated docs; should be moved under docs, not deleted. | no |
| `docs/architecture.mmd` | Potentially superseded by `docs/architecture.md` narrative + graph; keep until migration complete. | no |
| `datasets/training_builder/*.parquet` | Derived artifacts (can be rebuilt), but useful for reproducibility checkpoints. | no |
| `datasets/training_candidates/` | Candidate split outputs; usually temporary but may be needed for audit trail. | no |
| `datasets/training_provenance/` | Derived provenance sidecar; rebuildable but important for traceability checks. | no |
| `scripts/train_unsloth.py` | Partially overlaps with `training/run.py`; still useful as standalone scaffold entrypoint. | no |
| `scripts/validate_hf_roundtrip.py` + `scripts/verify_final_dataset.py` | Overlap in validation domain; keep for now until merged strategy is finalized. | no |

## Notes

- "yes" means safe from a functionality perspective (reproducible or cache/output only).
- For long-term maintainability, archive one-time reports first, then prune after a retention decision.
