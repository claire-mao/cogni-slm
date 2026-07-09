# Raw Dataset Storage

This directory contains preserved source files for external essay datasets.

## Structure

- `datasets/raw/asap_aes/source_files/`
  - Intended for ASAP-AES source files downloaded by `scripts/download_datasets.py`.
- `datasets/raw/persuade2/source_files/`
  - Intended for PERSUADE 2.0 source files (HF mirror or official manual download).
- `datasets/raw/asap2/source_files/`
  - Intended for ASAP 2.0 source files downloaded by `scripts/download_datasets.py`.

## Reproducibility

Use:

```bash
python3 scripts/download_datasets.py
```

The script writes machine-readable results to:

- `outputs/data_ingestion/download_summary.json`

## Current Status

At the time of the latest run in this environment, network name resolution failed for Hugging Face requests, so no dataset files were retrieved automatically.

If automatic download fails, place manually acquired, licensed files into the corresponding `source_files/` folder and keep upstream license/readme files unchanged.
