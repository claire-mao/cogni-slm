# Script Cleanup Recommendations

This report identifies overlap in `scripts/` and recommends consolidation paths without changing model behavior.

## High-Overlap Script Groups

| Group | Current Scripts | Overlap | Recommendation |
|---|---|---|---|
| Final dataset validation | `verify_final_dataset.py`, `validate_hf_roundtrip.py` | Both validate schema/HF compatibility/serialization behavior. | Merge under one command with modes: `--integrity`, `--hf-roundtrip`, `--full`. Keep old scripts as wrappers temporarily. |
| Score/statistics reporting | `analyze_score_distributions.py`, archived statistics reports | Both compute score distributions and class-imbalance diagnostics. | Fold into one canonical `analyze_dataset_statistics.py`; keep legacy report-generation as compatibility mode. |
| Provenance operations | `create_provenance_index.py`, provenance verification reports/scripts | Shared provenance schema and traceability checks. | Create one provenance module with two subcommands: `build` and `verify`. |
| Baseline evaluation runs | `run_prompt_test.py`, `run_baseline_eval.py` | Both execute held-out baseline-style inference and scoring outputs. | Keep separate entrypoints, but centralize shared orchestration into one helper module. |
| Split/leakage analysis | `create_prompt_group_split_candidate.py`, `analyze_prompt_leakage.py` | Both operate on prompt grouping and leakage prevention logic. | Move shared prompt-cluster logic into one utility module consumed by both scripts. |

## Moderate-Overlap Areas

| Scripts | Notes | Recommendation |
|---|---|---|
| `build_dataset.py` + `rebuild_all.py` | Both orchestrate multi-step pipelines with overlapping checks and reporting. | Keep both, but extract a shared orchestration library (`src/data/pipeline.py`) to avoid drift. |
| `ingest_raw_essays.py` + `ingest_private_documents.py` | Both perform ingestion + normalization with provenance capture. | Share parser and normalization utilities in `src/data/`. |

## Keep Separate (Different Responsibilities)

- `download_datasets.py` (acquisition)
- `normalize_unified_schema.py` (schema normalization)
- `deduplicate_dataset.py` (dedup logic)
- `score_dataset_quality.py` (quality scoring)
- `split_dataset.py` (split generation)
- `train_unsloth.py` (training scaffold)

## Suggested Consolidation Order

1. Unify validation scripts (`verify_final_dataset.py` + `validate_hf_roundtrip.py`).
2. Unify provenance build/verify commands.
3. Extract shared baseline evaluation orchestration.
4. Consolidate score-analysis scripts into one canonical statistics entrypoint.
