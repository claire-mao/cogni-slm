# Delete Candidates (Review Before Any Deletion)

No deletions were executed in this refactor phase.

| filename | reason | safe_to_delete |
|---|---|---|
| `.DS_Store` files (repo-wide) | OS-generated metadata files, not source artifacts. | yes |
| `__pycache__/` directories (repo-wide) | Runtime cache artifacts; fully regenerable. | yes |
| `.hf_cache/` and `datasets/.hf_cache/` | Local cache artifacts; regenerable from source data. | yes |
| `outputs/evaluation_harness/` | Legacy run output location superseded by `outputs/evaluation/harness/`. | yes |
| `outputs/baseline/` | Legacy baseline output location superseded by `outputs/evaluation/*`. | yes |
| `outputs/inference_demo/` | One-time local demo output, reproducible. | yes |
| `datasets/hf_validation_artifacts/` | Intermediate serialization artifacts from validation scripts. | yes |
| `docs/reports/archive/*` | Historical one-time reports retained for auditability. | no |
| `datasets/training_provenance/` | Derived but important traceability artifact. | no |
| `datasets/training_candidates/` | Candidate split artifacts useful for audit and experiments. | no |
| `scripts/verify_final_dataset.py` + `scripts/validate_hf_roundtrip.py` | Overlapping scope; keep until merged command exists. | no |

## Notes

- `safe_to_delete=yes` indicates no functional dependency.
- Archive-first policy is recommended for analysis reports.
