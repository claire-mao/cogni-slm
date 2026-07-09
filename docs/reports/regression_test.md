# Regression Test Report

- Objective: verify behavior is preserved after repository refactor.

## Regression Baselines

| Artifact | Current value |
|---|---|
| `datasets/final/train.jsonl` rows | `9940` |
| `datasets/final/validation.jsonl` rows | `1241` |
| `datasets/final/test.jsonl` rows | `1232` |
| `datasets/training` split rows | `train:9940`, `validation:1241`, `test:1232` |
| `datasets/final/train.jsonl` sha256 | `9307baf336c937c73a22001d12c216e9b9f5d8ab3a6dc069fbe8a4cdd2f9e912` |
| `datasets/final/validation.jsonl` sha256 | `dacc678796e22cc2cddeee6e3faeaed230102082575506708e9d6bba59b0b5ff` |
| `datasets/final/test.jsonl` sha256 | `9aebda18fd8cf296e11ec83cbc1d67f785736145cef5d674b376378dab325777` |

## Verification Matrix

| Check | Result | Notes |
|---|---|---|
| `ruff check .` | PASS | No lint violations. |
| `black --check .` | PASS | Formatting consistent. |
| `pytest -q` | PASS | `35 passed`. |
| Import checks (`src.*`, `evaluation`, `training`) | PASS | Imports succeed. |
| `python3 scripts/build_dataset.py --dry-run --skip-download` | PASS | Planned pipeline printed successfully. |
| `python3 scripts/rebuild_all.py --dry-run` | PASS | Rebuild dry-run completed and report regenerated. |
| `python3 -m training.run --help` | PASS | CLI intact. |
| `python3 -m evaluation.run_harness --help` | PASS | CLI intact. |
| `python3 scripts/run_inference.py --help` | PASS | CLI intact. |
| `load_dataset()` on `datasets/final/train.jsonl` | PASS | Loads successfully with local HF cache path. |
| `load_from_disk()` on `datasets/training` | PASS | Loads `train/validation/test`. |
| `scripts/validate_hf_roundtrip.py` on `datasets/final` | PARTIAL | `5 PASS / 1 FAIL` (`quality_filtered.jsonl` schema cast issue). |
| `python3 -m evaluation.run_harness ... --dry-run` | PASS | Produced run under `outputs/evaluation/harness/`. |

## Intentional Differences

- Script code now lives in `src/`; `scripts/` are wrappers.
- Report defaults changed from legacy `reports/` to `docs/reports/`.
- Evaluation output defaults use `outputs/evaluation/*` for new runs.

## Non-Intentional Differences

- None observed in dataset counts or primary split sizes.
