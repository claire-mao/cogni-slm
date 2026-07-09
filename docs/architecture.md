# Cogni-SLM Architecture

## End-to-End Dependency Graph

```mermaid
flowchart TD
    A["Raw datasets\ndatasets/raw"] --> B["Ingestion\nscripts/ingest_raw_essays.py"]
    B --> C["Normalization\nscripts/normalize_unified_schema.py"]
    C --> D["Quality scoring + filtering\nscripts/score_dataset_quality.py\nscripts/filter_dataset.py"]
    D --> E["Deduplication + merge\nscripts/deduplicate_dataset.py\nscripts/merge_hf_datasets.py"]
    E --> F["Final canonical dataset\ndatasets/final"]
    F --> G["Training dataset build\nscripts/build_training_dataset.py\ndatasets/training"]
    F --> H["Prompt-group split candidate\nscripts/create_prompt_group_split_candidate.py"]
    G --> I["Teacher generation/inference\nscripts/generate_training_dataset.py\nscripts/run_teacher_inference.py"]
    G --> J["Model training init\npython -m training.run"]
    G --> K["Evaluation + baseline\npython -m evaluation.run_harness\nscripts/run_prompt_test.py\nscripts/run_baseline_eval.py"]
```

## Code Organization

- `scripts/`: thin, backward-compatible CLI wrappers.
- `src/data/`: dataset acquisition, ingestion, normalization, quality, dedup, split, rebuild implementations.
- `src/evaluation/`: prompt test and baseline evaluation implementations plus shared evaluation interfaces.
- `src/inference/`: local inference runner implementation.
- `src/training/`: training entrypoint scaffolds migrated from script layer.
- `src/utils/`: shared path helpers and reusable utility functions.
- `evaluation/`: reusable base-vs-tuned harness package.
- `training/`: stable runtime training package.

## Runtime Artifact Conventions

- Reports default to `docs/reports/`.
- Evaluation artifacts default to `outputs/evaluation/`.
- Rebuild artifacts default to `outputs/rebuild/` and synchronized dataset targets.
- Experiment outputs should be written under `outputs/experiments/`.

## Compatibility Guarantees

- Existing script entrypoints remain usable.
- Existing test imports from `scripts/*.py` remain supported via wrapper attribute forwarding.
- Training config supports `configs/training/` with fallback to legacy `training/configs/`.
