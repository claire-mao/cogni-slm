# Final Regression Suite

## Core Checks

| Check | Result |
|---|---|
| `ruff check .` | PASS |
| `black --check .` | PASS |
| `pytest -q` | PASS (`35 passed`) |

## CLI Smoke Tests

| Command | Result |
|---|---|
| `python3 scripts/build_dataset.py --dry-run --skip-download --report-path docs/reports/reproducibility.md` | PASS |
| `python3 scripts/rebuild_all.py --dry-run` | PASS |
| `python3 -m training.run --help` | PASS |
| `python3 -m evaluation.run_harness --help` | PASS |
| `python3 scripts/run_inference.py --help` | PASS |

## Import Verification

| Import Group | Result |
|---|---|
| `src.*` | PASS |
| `training.*` | PASS |
| `evaluation.*` | PASS |

## Hugging Face Loading Verification

| Check | Result |
|---|---|
| `datasets.load_dataset()` on `datasets/final/train.jsonl` | PASS (`12413` rows) |
| `datasets.load_from_disk()` on `datasets/training` | PASS (`train` split present) |
| `datasets/build_dataset.py` output (`datasets/hf/dataset_dict`) load_from_disk | PASS |
| `scripts/validate_hf_roundtrip.py` on `datasets/final` | PASS (`6/6` cases) |

## Regression Verdict

- Overall: **PASS**
- No functional regressions detected in lint, tests, CLI entrypoints, imports, or HF compatibility checks.
