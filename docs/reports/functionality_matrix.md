# Functionality Matrix

| Feature | CLI | Tests | Verified | Status |
|---|---|---|---|---|
| Script compatibility wrappers | `scripts/*.py` | `pytest` script-import tests | yes | PASS |
| Dataset build orchestration | `scripts/build_dataset.py` | yes (indirect + unit tests) | dry-run executed | PASS |
| Full rebuild orchestration | `scripts/rebuild_all.py` | no direct unit test | dry-run executed | PASS |
| Raw ingestion pipeline | `scripts/ingest_raw_essays.py` | yes | unit tests pass | PASS |
| Unified normalization | `scripts/normalize_unified_schema.py` | yes | unit tests pass | PASS |
| Quality scoring | `scripts/score_dataset_quality.py` | yes | unit tests pass + CLI help | PASS |
| Deduplication | `scripts/deduplicate_dataset.py` | yes | unit tests pass | PASS |
| Provenance index | `scripts/create_provenance_index.py` | yes | unit tests pass + CLI help | PASS |
| Final dataset verification | `scripts/verify_final_dataset.py` | no dedicated unit test | available/importable | PASS |
| HF roundtrip validation | `scripts/validate_hf_roundtrip.py` | no dedicated unit test | executed on `datasets/final` | PARTIAL |
| Prompt-test baseline | `scripts/run_prompt_test.py` | no dedicated unit test | import + CLI wrapper verified | PASS |
| Baseline evaluation | `scripts/run_baseline_eval.py` | no dedicated unit test | import + CLI wrapper verified | PASS |
| Evaluation harness | `python -m evaluation.run_harness` | no direct unit test | `--help` + `--dry-run` executed | PASS |
| Local inference | `scripts/run_inference.py` | no direct unit test | `--help` executed | PASS |
| Training pipeline entry | `python -m training.run` | no direct unit test | `--help` executed | PASS |
| Lint/format gate | n/a | yes | `ruff`, `black --check` | PASS |
| Unit/integration tests | n/a | yes | `35 passed` | PASS |
