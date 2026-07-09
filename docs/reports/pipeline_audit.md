# Teacher Pipeline Artifact Audit

Date: 2026-07-09  
Scope: generated artifacts and modules for teacher/gold/SFT/training pipeline integration

## Audit Method

1. Enumerated generated modules under `src/teacher`, `src/review`, `src/data`, `src/training`, `src/dashboard`.
2. Ran CLI smoke checks (`--help`) for major entrypoints.
3. Scanned for TODO/FIXME/placeholders/mock paths.
4. Checked import graph for cycles.
5. Compared runner output contracts against downstream consumers (review, leaderboard, validation, SFT).
6. Checked reference connectivity for manifests/schemas/prompts/configs.

## Summary

- Import cycles detected: **none**.
- TODO/FIXME markers in audited pipeline modules: **none material**.
- Major issues found: **schema/runner contract fragmentation**, **duplicate runner stacks**, **partially disconnected artifacts**, **one effectively broken execution path (`run_teacher_experiment`)**.

## Findings

| File | Severity | Issue | Recommended Fix |
|---|---|---|---|
| `src/teacher/run_teacher_experiments.py:1052` + `src/teacher/run_teacher_benchmark_execution.py:726` + `src/teacher/run_teacher_experiment.py:564` + `src/teacher/leaderboard.py:144` + `src/review/build_review_queue.py:316` + `src/review/merge_reviews.py:171` | HIGH | **Inconsistent response schema across teacher runners.** `run_teacher_experiments` writes `raw_json_output`, but `run_teacher_benchmark_execution` and `run_teacher_experiment` write top-level `output`. Downstream review/leaderboard paths read `raw_json_output`, so outputs from some runners are not consumable without adapters. | Standardize one canonical response schema for all runners. Add a shared serializer module and migrate all runner outputs to that format. Add schema contract tests across runner -> review/leaderboard/benchmark. |
| `src/teacher/run_teacher_experiment.py:435` + `teacher_prompts/versions/registry.json` | HIGH | **`run_teacher_experiment` is not usable by default** because it requires a prompt in prompt registry, but registry is empty. Runtime failure observed: `KeyError: Prompt id not found: production_teacher`. | Bootstrap prompt registry automatically from `teacher_prompts/production_teacher.txt` on first run, or add fallback path flag (`--prompt-template`) like other runners. |
| `src/teacher/run_teacher_experiment.py:205` + `src/teacher/run_teacher_experiment.py:736` + `src/teacher/provider_config.py:30` | HIGH | **Local provider path is broken.** Runner infers/supports `local_transformers`, but provider validation rejects `local`/`local_transformers` as unsupported. Runtime failure observed. | Update provider config validator to accept local provider with no API-key requirements, or bypass provider validation when provider is local. |
| `src/data/generate_production_dataset.py:238` | HIGH | **Teacher stage is metadata-only, not inference execution.** Workflow claims `teacher -> validation -> review -> gold -> sft`, but teacher stage only records `teacher_outputs_path`; no teacher run is launched. | Either: (a) integrate teacher inference runner invocation; or (b) rename stage/docs to explicitly “precomputed teacher outputs ingest” and enforce required artifacts. |
| `src/teacher/run_teacher_experiments.py:436` + `src/teacher/providers/openai_provider.py:1` (and other provider modules) | MEDIUM | **Duplicate provider implementations.** Manual provider HTTP logic in `run_teacher_experiments` duplicates `src/teacher/providers/*`, creating divergence risk. | Refactor `run_teacher_experiments` to use `create_teacher_provider(...)` and remove duplicated HTTP call codepaths. |
| `src/teacher/providers/common.py:127` + `src/teacher/validation.py:26` + `src/teacher/run_teacher_experiment.py:277` | MEDIUM | **Contract mismatch and synthetic reconstruction.** Provider normalization collapses model output to `{reasoning, rubric_analysis, feedback, score, confidence}`; `run_teacher_experiment` then fabricates full rubric/fallacy structures for validation (`_unified_output_to_validation_payload`). This can inflate/blur quality metrics. | Preserve raw structured teacher JSON in a canonical field, validate that directly against schema, and remove synthetic filler payload generation in evaluation paths. |
| `teacher_schemas/` + `teacher_schema_manifest.json` | MEDIUM | **Schema artifacts are disconnected.** No code reference found to `teacher_schemas/*` or `teacher_schema_manifest.json`; runtime validation uses `teacher_prompts/output_schema.json` and hardcoded rules. | Wire runtime schema loading to manifested schemas (task-specific), or remove/archive unused schema artifacts to avoid drift. |
| `teacher_prompt_manifest.json` + task prompt files `teacher_prompts/*.md` | MEDIUM | **Prompt manifest/task prompt docs not integrated with execution.** Runners consume `teacher_prompts/production_teacher.txt`; task prompt files/manifest are not read by pipeline code. | Integrate prompt selection via manifest/registry or move task prompt docs to documentation-only location with explicit non-runtime label. |
| `src/data/merge_reviewed_teacher_outputs.py` | MEDIUM | **Duplicate gold-merge implementation appears unused.** No references found from pipeline entrypoints/tests/docs; overlaps with `src/data/build_gold_dataset.py`. | Choose one canonical gold-merge path; deprecate/remove the other, or add clear compatibility wrapper with tests. |
| `src/data/generate_training_dataset.py:155` + `src/data/run_teacher_inference.py:1` + `src/training/train_unsloth.py:1` | MEDIUM | **Legacy scaffold/placeholder modules remain in active tree.** Includes `NotImplementedError` provider branch, dry-run placeholder reasoning, and placeholder dataset bootstrap. These are easy to confuse with production paths. | Move to `archive/` or mark experimental; gate with explicit `--experimental` flags and update README to point only to production runners. |
| `src/review/build_review_queue.py:24` + `src/data/build_sft_dataset.py:18` + `src/data/generate_production_dataset.py:24` | LOW | **Mixed internal import styles (`src.teacher...` vs `teacher...` vs `data...`).** Works in repo context but increases packaging/runtime ambiguity. | Standardize imports to one package style and add CI checks for both supported invocation modes. |
| `src/teacher/benchmark.py:191` + `src/evaluation/calibration.py:232` | LOW | **Duplicate calibration function implementations** (`brier_score`, `expected_calibration_error`, `temperature_scale_confidence`, `fit_temperature_scaling`) in two modules. | Consolidate into one calibration utility module and import from there. |
| `src/teacher/leaderboard.py:416` | LOW | **Leaderboard does not canonicalize model IDs**, so alias variants (e.g., `claude_sonnet_4x` vs `claude_sonnet_4`) can split results across separate rows. | Canonicalize model names via `canonical_model_id(...)` before aggregation. |
| `src/teacher/run_teacher_experiment.py`, `src/teacher/run_teacher_ensembles.py`, `src/review/server.py`, `src/review/build_review_queue.py`, `src/review/merge_reviews.py`, `src/dashboard/build_dashboard.py`, `src/training/train_experiment.py`, `src/data/generate_production_dataset.py` | LOW | **Test coverage gaps for key orchestration modules.** Existing tests focus on benchmark/generate_labels/provider config; several integration-critical runners have no direct tests. | Add smoke + contract tests for runner outputs, review ingestion, dashboard aggregation, and training experiment planning/execution metadata. |

## Broken CLI Entry Point Findings

1. `run_teacher_experiment` local mode currently fails because provider validator rejects `local`.
2. `run_teacher_experiment` default prompt-version flow fails when prompt registry is empty.

All major CLIs respond to `--help`, but the above two paths are operationally broken for real use.

## Categories with No Critical Findings

- Import cycles: none detected in audited modules.
- Hard TODO/FIXME debt in production teacher modules: none significant.

