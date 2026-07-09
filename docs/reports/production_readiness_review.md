# Production Readiness Review

Date: 2026-07-09

Scope: reliability, maintainability, reproducibility, test coverage, configuration management, failure recovery, logging, versioning, checkpoint recovery.

Methods:
- Static code audit of `src/`, `configs/`, `tests/`.
- Validation of current test health (`47 passed in 0.98s`).
- Cross-check of runtime contracts between teacher, review, dataset, training, and dashboard pipelines.

## Executive Verdict
Overall status: **PARTIAL / Not production-ready yet**.

Blocking items:
- **2 Critical** issues
- **7 Major** issues
- **4 Minor** issues

## Findings (Ordered by Severity)

### Critical
| ID | Area | Issue | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| PR-001 | Reliability, Failure Recovery | **Teacher response schema is inconsistent across runners and breaks downstream review ingestion depending on runner choice.** `run_teacher_experiments` writes `raw_json_output`, but `run_teacher_experiment` and `run_teacher_benchmark_execution` write `output`. Review code only reads `raw_json_output`. | `src/teacher/run_teacher_experiments.py:1004`, `src/teacher/run_teacher_experiment.py:593`, `src/teacher/run_teacher_benchmark_execution.py:763`, `src/review/build_review_queue.py:316`, `src/review/merge_reviews.py:171` | Production runs can silently degrade into invalid/empty review queues or unresolved merges when the "wrong" runner is used. | Define one canonical response schema and enforce it in all runners plus downstream consumers. Add contract tests for runner -> review -> merge path. |
| PR-002 | Reliability, Configuration Management | **Local provider execution path is broken at config validation.** Runtime supports `local_transformers`, provider factory supports it, but config validator rejects it as unsupported. | `src/teacher/run_teacher_experiment.py:235-237`, `src/teacher/providers/factory.py:22-24`, `src/teacher/provider_config.py:19-27`, `src/teacher/provider_config.py:30-37`; runtime check: `ValueError: Unsupported provider 'local_transformers'` | Local fallback cannot be used for production failover/repro runs. | Add `local` / `local_transformers` to provider validator with no API-key requirement, and cover with tests. |

### Major
| ID | Area | Issue | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| PR-003 | Failure Recovery, Reliability | **Retry/backoff policy is declared but not enforced by runtime request paths.** | `configs/teacher/teacher_stack_v1.json:41-50`, `src/teacher/providers/http.py:26-44`, `src/teacher/run_teacher_experiments.py:1011-1028` | Transient network/rate-limit failures are handled as one-shot failures, reducing robustness and increasing manual reruns. | Implement shared retry middleware honoring attempt/backoff policy and per-error retryability. |
| PR-004 | Configuration Management, Maintainability | **Production teacher stack config is not wired into teacher execution runners.** Runners load `teacher_validation_master.json` / `teacher_ensembles_v1.json`, not `teacher_stack_v1.json`. | `src/teacher/run_teacher_experiments.py:732`, `src/teacher/run_teacher_benchmark_execution.py:563`, `src/teacher/run_teacher_ensembles.py:703`; no references found for `teacher_stack_v1` in `src/teacher`, `src/training`, `src/review`, `src/dashboard`. | High risk of config drift between documented production stack and actual runtime behavior. | Make `teacher_stack_v1.json` the single source of truth or remove it from production claims. |
| PR-005 | Maintainability | **Duplicate provider call implementations create divergence risk.** `run_teacher_experiments` reimplements provider HTTP call logic already present in `src/teacher/providers/*`. | `src/teacher/run_teacher_experiments.py:456-527`, `src/teacher/providers/openai_provider.py:20-50` | Bug fixes and API changes must be patched in multiple places; drift is likely. | Refactor `run_teacher_experiments` to use `create_teacher_provider(...)` and remove duplicate HTTP code. |
| PR-006 | Logging, Operability | **No structured logging framework is used in core runtime modules.** Runtime emits mostly `print(...)` and ad hoc JSON files; no `logging` instrumentation found. | No matches for `logging`/`getLogger` in `src`/`tests`; examples: `src/teacher/run_teacher_experiments.py:1138`, `src/training/train_experiment.py:1835`, `src/dashboard/build_dashboard.py:749` | Weak observability in long-running jobs; harder incident triage and alerting. | Introduce structured logging (`logging` + JSON formatter) with run IDs, model IDs, and stage tags. |
| PR-007 | Reproducibility | **Runtime dependencies are not pinned in project metadata.** Core dependencies list is empty while training imports heavy runtime packages dynamically. | `pyproject.toml:15`, `src/training/train_experiment.py:1115-1139`, `src/training/train_unsloth.py:50-62` | Environment drift across machines/CI can alter outcomes or break runs. | Add pinned runtime dependency sets (or lockfile) for data/teacher/training/eval paths. |
| PR-008 | Test Coverage | **Coverage is broad for units but thin for production orchestrators/integration paths.** Key runners have no direct tests. | No test references for `run_teacher_experiment`, `run_teacher_experiments`, `run_teacher_ensembles`, `build_review_queue`, `merge_reviews`, `train_experiment`, `build_dashboard`, `generate_production_dataset`; trivial smoke test: `tests/test_smoke.py:4-5` | Regressions in cross-stage wiring can pass CI until late manual runs. | Add integration tests for full pipeline contracts and failure paths (runner output -> review -> gold -> sft -> training metadata). |
| PR-009 | Reliability, Configuration Management | **Prompt registry bootstrapping is manual and can hard-fail teacher execution.** Default registry may be empty; `run_teacher_experiment` hard requires prompt registry entry. | `teacher_prompts/versions/registry.json` (empty prompts), `src/teacher/run_teacher_experiment.py:447-449`, `src/teacher/prompt_registry.py:287-289` | First-run failures for otherwise valid setups; fragile operational onboarding. | Add auto-bootstrap from `teacher_prompts/production_teacher.txt` or fallback prompt-template argument. |

### Minor
| ID | Area | Issue | Evidence | Impact | Recommended Fix |
|---|---|---|---|---|---|
| PR-010 | Checkpoint Recovery | **Checkpoint recovery is manual-only.** Resume requires explicit CLI path; no automatic latest-checkpoint discovery/retry loop. | `src/training/train_experiment.py:1769`, `src/training/train_experiment.py:1827-1831`, `src/training/train_experiment.py:1430-1432` | Slower operator recovery after interrupted jobs. | Add optional `--resume latest` and auto-detect latest valid checkpoint per run. |
| PR-011 | Reliability, Failure Recovery | **Run directory idempotency is weak.** Some runners append to existing response files when reusing run IDs. | `src/teacher/run_teacher_experiments.py:920-925`, `src/teacher/run_teacher_experiments.py:1009`, `src/teacher/run_teacher_experiment.py:459-463` | Duplicate/contaminated artifacts if rerun with same run ID. | Enforce unique run IDs by default and add explicit `--resume` / `--overwrite` modes. |
| PR-012 | Test Coverage, QA Governance | **No coverage threshold/gating configured.** | No `--cov`/coverage settings in `pyproject.toml` or `Makefile`; `pyproject.toml:33-35` | High pass rate can still hide untested production-critical branches. | Add coverage reporting and minimum threshold gates for core pipeline packages. |
| PR-013 | Versioning, Reproducibility | **Not all run manifests record config checksums/hashes.** Example multi-teacher run manifest records config paths/ids but not config file hashes. | `src/teacher/run_teacher_experiments.py:875-890` | Harder to guarantee exact reruns if configs change in-place. | Persist SHA256 hashes for all consumed config/prompt files in run manifests. |

## Category Scorecard
| Category | Status | Notes |
|---|---|---|
| Reliability | PARTIAL | Critical runner contract mismatch and local-provider validation breakage. |
| Maintainability | PARTIAL | Duplicate provider logic and config drift between intended and executed stack. |
| Reproducibility | PARTIAL | Strong dataset/tracker manifests exist, but environment dependency pinning and config hashing are incomplete. |
| Test Coverage | PARTIAL | Unit tests healthy (`47 passed`), but key orchestration and integration paths remain uncovered. |
| Configuration Management | PARTIAL | Provider validation exists, but production stack config is not runtime-authoritative. |
| Failure Recovery | PARTIAL | Failures are captured, but retries/backoff and robust resume semantics are incomplete. |
| Logging | PARTIAL | Artifact JSON outputs exist; structured runtime logging/levels are missing. |
| Versioning | PARTIAL | Dataset versioning/checksums are strong; some run-level config immutability gaps remain. |
| Checkpoint Recovery | PARTIAL | Manual resume works; automated recovery ergonomics are limited. |

## Immediate Remediation Order
1. Fix canonical teacher response schema and downstream parser compatibility (PR-001).
2. Fix local provider validation mismatch (PR-002).
3. Implement retry/backoff and make teacher stack config executable source-of-truth (PR-003, PR-004).
4. Add integration tests for orchestrators and contract boundaries (PR-008).
5. Add structured logging and dependency pinning/lock strategy (PR-006, PR-007).
