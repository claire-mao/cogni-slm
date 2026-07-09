# Script Cleanup Recommendations

## Current State

- `scripts/` is now a thin compatibility layer.
- Core script logic lives in `src/data/`, `src/evaluation/`, `src/inference/`, and `src/training/`.
- Legacy script import behavior is preserved for tests and external tooling.

## Duplicate/Overlapping Areas

| Group | Current modules | Overlap | Recommendation |
|---|---|---|---|
| Final validation | `src/data/verify_final_dataset.py`, `src/data/validate_hf_roundtrip.py` | Both validate schema/HF compatibility. | Merge into a single validator with subcommands (`integrity`, `hf-roundtrip`, `full`). |
| Provenance workflows | `src/data/create_provenance_index.py` + provenance repair steps in `src/data/rebuild_all.py` | Shared provenance assumptions and reporting. | Extract shared provenance utilities to `src/utils/provenance.py`. |
| Baseline evaluation flows | `src/evaluation/run_prompt_test.py`, `src/evaluation/run_baseline_eval.py` | Shared prompting, generation, deterministic checks, reporting patterns. | Extract shared baseline runner utilities in `src/evaluation/baseline_common.py`. |
| Prompt split analysis | `src/data/analyze_prompt_leakage.py`, `src/data/create_prompt_group_split_candidate.py` | Both compute prompt grouping/leakage logic. | Consolidate prompt-cluster logic into one shared helper module. |

## Low-Risk Next Consolidations

1. Shared JSONL IO helpers (`read_jsonl`, `write_jsonl`) under `src/utils/dataset_io.py`.
2. Shared text normalization helpers under `src/utils/text_utils.py`.
3. Shared report rendering helpers under `src/utils/reporting.py`.

## Keep Separate

- `download_datasets.py` (acquisition)
- `normalize_unified_schema.py` (canonical mapping)
- `deduplicate_dataset.py` (dedup logic)
- `train_unsloth.py` (training scaffold)
