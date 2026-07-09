# Git Ready

## Files Safe to Commit

- Source code and package modules: `src/`, `evaluation/`, `training/`, `scripts/`, `tests/`
- Documentation: `README.md`, `docs/`, `reports/` (except machine-generated local-only reports if desired)
- Config and workflow files: `pyproject.toml`, `Makefile`, `.github/`, `.pre-commit-config.yaml`, `.env.example`

## Files That Should Remain Local

- Private data: `datasets/private/`
- Caches: `.hf_cache/`, `datasets/.hf_cache/`, `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`
- Large derived artifacts: `datasets/final/*.jsonl`, `datasets/training/`, `datasets/training_builder/`, `datasets/hf/`, `datasets/processed/unified/`
- Model artifacts/checkpoints/adapters: `models/*`, `checkpoints/`, `adapters/`, `*.safetensors`, `*.ckpt`, `*.pt`, `*.pth`, `*.bin`
- Runtime outputs/logs: `outputs/*`, `logs/`, `*.log`, `tmp/`, `temp/`

## Estimated Repository Size

- Working tree size (current local): **22G** (`du -sh .`)
- `datasets/` dominates storage (~19G).

## Remaining Large Files

| File | Size |
|---|---:|
| datasets/final/quality_scored.jsonl | 2.48 GB |
| datasets/processed/unified/unified_all.jsonl | 2.41 GB |
| datasets/processed/unified/unified_all.sanitized.jsonl | 2.41 GB |
| datasets/final/quality_filtered.jsonl | 2.28 GB |
| datasets/processed/unified/final__quality_scored.jsonl | 962.74 MB |
| datasets/processed/unified/final__quality_filtered.jsonl | 854.19 MB |
| datasets/.hf_cache/datasets/json/default-cf84f08760be9934/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00000-of-00005.arrow | 482.14 MB |
| datasets/.hf_cache/datasets/json/default-cd81a1d28e5b5ce8/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00002-of-00005.arrow | 481.96 MB |
| datasets/.hf_cache/datasets/json/default-cd81a1d28e5b5ce8/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00000-of-00005.arrow | 481.39 MB |
| datasets/.hf_cache/datasets/json/default-cf84f08760be9934/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00001-of-00005.arrow | 480.81 MB |
| datasets/.hf_cache/datasets/json/default-cf84f08760be9934/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00002-of-00005.arrow | 480.01 MB |
| datasets/.hf_cache/datasets/json/default-cf84f08760be9934/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00003-of-00005.arrow | 479.75 MB |
| datasets/.hf_cache/datasets/json/default-f28db9a229822a67/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00000-of-00002.arrow | 478.14 MB |
| datasets/.hf_cache/datasets/json/default-cd81a1d28e5b5ce8/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00001-of-00005.arrow | 478.07 MB |
| datasets/.hf_cache/datasets/json/default-cd81a1d28e5b5ce8/0.0.0/2752a09ea3d59feeb3ad5ea2af11086f41ecd725fd528c98a89d75f546aba397/json-train-00003-of-00005.arrow | 477.66 MB |

## .gitignore Coverage

- Updated to include: private datasets, model checkpoints/adapters, HF cache, generic cache dirs, temporary logs, and large generated dataset directories.
- Additional recommendation: keep only metadata/manifest artifacts under version control when legal redistribution is unresolved.
