# Dataset Inventory

This inventory reflects datasets currently registered in `datasets/dataset_registry.json` and present in the workspace.

| Name | Source | Task | License | # Examples | Fields | Preprocessing History | Provenance Status | Quality Filtering Status | Included in Final Dataset |
|---|---|---|---|---:|---|---|---|---|---|
| asap_aes_raw | ASAP-AES (Automated Student Assessment Prize) | essay scoring | Unverified in-repo; do not redistribute until explicitly confirmed | 12964 | essay_id, essay_set, essay, domain1_score, ... | scripts/download_datasets.py -> hf_staging_dataset, normalized_asap_aes, normalized_all_datasets, cogni_final_dataset, cogni_training_dataset, cogni_training_builder | Source-level only | n/a or indirect | Yes |
| asap2_raw | ASAP 2.0 (mirror candidate) | essay scoring | CC-BY-NC-4.0 on mirror metadata (not present locally) | 0 | n/a | scripts/download_datasets.py -> normalized_asap2 | Source-level only | n/a or indirect | No |
| persuade2_raw | PERSUADE 2.0 / Feedback Prize corpus | essay scoring | CC-BY-NC-SA-4.0 (official repo declaration; not present locally) | 0 | n/a | scripts/download_datasets.py -> normalized_persuade2 | Source-level only | n/a or indirect | No |
| hf_staging_dataset | Derived from raw datasets via HF staging build | dataset normalization and consolidation | Inherits upstream source license constraints | 12964 | id, text, score, source, prompt, split | datasets/build_dataset.py -> normalized_all_datasets, cogni_final_dataset | Partial/derived | Pre-quality stage | Yes |
| processed_raw_essays | Normalized ingestion output from local raw essays folder | data pipeline artifact | Depends on ingested sources | 0 | n/a | scripts/ingest_raw_essays.py -> normalized_all_datasets | Source-level only | n/a or indirect | No |
| normalized_asap_aes | Normalized ASAP-AES records | essay scoring | Unknown/unverified for redistribution in current repo | 21448 | id, label, metadata, prompt, source, task, text | scripts/normalize_unified_schema.py -> normalized_all_datasets, cogni_final_dataset | Partial/derived | Pre-quality stage | Yes |
| normalized_asap2 | Normalized ASAP 2.0 records | essay scoring | CC-BY-NC-4.0 if sourced from listed HF mirror | 0 | n/a | scripts/normalize_unified_schema.py -> normalized_all_datasets | Partial/derived | Pre-quality stage | No |
| normalized_persuade2 | Normalized PERSUADE 2.0 records | essay scoring | CC-BY-NC-SA-4.0 if sourced from official repo | 0 | n/a | scripts/normalize_unified_schema.py -> normalized_all_datasets | Partial/derived | Pre-quality stage | No |
| normalized_all_datasets | Merged normalized datasets | dataset normalization and consolidation | Mixed/inherited from source datasets | 21148 | id, label, metadata, prompt, source, task, text | scripts/normalize_unified_schema.py -> cogni_final_dataset, cogni_training_dataset | Partial/derived | Pre-quality stage | Yes |
| cogni_golden_dataset | Internal synthetic golden set for pipeline evaluation | fallacy/behavior evaluation scaffolding | Internal project artifact | 50 | acceptable_alternative_labels, adversarial_type, analogy_source_domain, analogy_target_domain, argument_text, attack_target, created_at, critic_model_id, ... | scripts/generate_golden_dataset.py -> heldout_benchmark_placeholder | Partial/derived | n/a or indirect | No |
| heldout_benchmark_placeholder | Derived placeholder held-out benchmark from golden dataset | held-out benchmark evaluation | Internal project artifact | 18 | acceptable_alternative_labels, adversarial_type, argument_text, attack_target, context, dataset_version, difficulty_level, example_id, ... | scripts/run_prompt_test.py -> baseline_evaluation_outputs | Partial/derived | n/a or indirect | No |
| cogni_final_dataset | Final merged and deduplicated dataset for Cogni | dataset normalization and consolidation | Inherited from sources (currently unknown due ASAP-AES license uncertainty) | 12413 | id, label, metadata, prompt, source, split, task, text | scripts/build_dataset.py -> cogni_training_dataset, cogni_training_builder | Complete (`datasets/final/provenance.parquet`) | Applied (quality scoring + filter + dedup upstream) | Yes |
| cogni_training_dataset | Projected training DatasetDict (prompt, essay, score) | essay scoring training | Inherited from final dataset source licenses | 12413 | prompt, essay, score | scripts/build_training_dataset.py -> model_training_jobs | Complete (`datasets/final/provenance.parquet`) | Applied (quality scoring + filter + dedup upstream) | No |
| cogni_training_builder | Parquet DatasetBuilder artifact + metadata sidecar | essay scoring training | Inherited from final dataset source licenses | 8 | n/a | datasets/training_builder/README.md -> load_dataset_local_builder | Partial/derived | n/a or indirect | No |

## Totals

- Registered dataset entries: **14**
- Sum of per-entry example counts (non-unique, includes derived datasets): **93,426**
- Final dataset split sizes: **train:9940, validation:1241, test:1232**
- Training dataset split sizes: **train:9940, validation:1241, test:1232**
