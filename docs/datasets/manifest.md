# Dataset Manifest (Human Summary)

This summary mirrors the machine-readable manifest at:

- `datasets/final/manifest.json`

## Canonical Final Dataset

- name: `cogni_final_dataset`
- dataset_version: `local-final-2026-07-08`
- total_examples: `12,413`
- split_sizes:
  - train: `9,940`
  - validation: `1,241`
  - test: `1,232`
- schema fields:
  - `id`, `text`, `label`, `source`, `prompt`, `split`, `task`, `metadata`

## Source Inclusion

- included source datasets:
  - `asap_aes` (license currently recorded as `unknown` in manifest)
- not included / empty in this environment:
  - `asap2`
  - `persuade2`

## Provenance + Hashes

- provenance index: `datasets/final/provenance.parquet`
- per-file SHA-256 entries are recorded in `datasets/final/manifest.json`.

## Pipeline Evidence

Manifest references pipeline evidence docs/scripts, including:

- `docs/reports/raw_verification.md`
- `datasets/hf/build_summary.json`
- `docs/reports/final_dataset_quality.md`
- `docs/reports/deduplication.md`
