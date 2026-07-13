# Repository Map

This file defines the responsibility of every top-level project folder. Generated
data and model artifacts remain local and are excluded from Git unless explicitly
allowlisted.

| Folder | Purpose | Keep / cleanup rule |
|---|---|---|
| `.github/` | Continuous-integration workflows and repository automation. | Keep only active workflows. |
| `configs/` | Versioned dataset, evaluation, provider, teacher, and training configuration. | One canonical config per active workflow; resolved run configs are artifacts. |
| `datasets/` | Raw sources, normalized data, evaluation sets, SFT splits, provenance, and registries. | Preserve source and final artifacts; ignore bulky generated contents by default. |
| `docs/` | Product definition, behavior contract, architecture, research, runbooks, and active reports. | Remove superseded snapshots; keep only evidence used by the current workflow. |
| `docs/release/` | Release runbook, risk register, cards, and third-party notices. | Public release stays blocked until every source is approved. |
| `evaluation/` | Standalone base-vs-tuned comparison harness. | Keep as the public harness entry point. |
| `models/` | Local base models, adapters, checkpoints, and merged exports. | Preserve locally; do not commit weights. |
| `notebooks/` | User-facing Colab/local workflows. | Keep one inference, one labeling, and one production-training notebook. |
| `outputs/` | Generated evaluations, experiment logs, reports, and run artifacts. | Preserve useful evidence locally; do not treat it as source code. |
| `scrapers/` | Reusable HTML/JSON acquisition utilities and source policies. | Keep while public-source ingestion is supported. |
| `scripts/` | Thin CLI entry points and reproducible one-off build/validation commands. | Business logic should live in `src/` when reused; remove superseded wrappers. |
| `src/data/` | Dataset ingestion, normalization, filtering, splitting, export, and provenance logic. | Canonical reusable data implementation. |
| `src/evaluation/` | Behavior checks, judges, calibration, metrics, reports, and error analysis. | Canonical behavior-evaluation implementation. |
| `src/inference/` | Local model loading and inference. | Canonical inference implementation. |
| `src/teacher/` | Provider adapters, teacher execution, benchmarking, prompt registry, and validation. | Retains legacy multi-task teachers; AP production uses the direct structured labeler. |
| `src/training/` | Experiment matrices and QLoRA readiness checks. | Complements, rather than duplicates, the runnable `training/` package. |
| `src/review/` | Human review queue and lightweight review UI. | Keep for adjudication and dataset audits. |
| `src/dashboard/` | Project/run status dashboard generation. | Keep for reporting. |
| `src/utils/` | Shared paths, environment resolution, and experiment tracking. | No task-specific logic. |
| `teacher_prompts/` | Versioned prompts and strict output schemas. | `ap_fallacy_behavior_schema.json` is the production AP behavior contract. |
| `teacher_schemas/` | Legacy multi-task teacher component schemas. | Keep while the general teacher pipeline remains supported. |
| `tests/` | Unit and regression tests. | Every reusable refactor should add or update coverage. |
| `training/` | Runnable Unsloth/Transformers QLoRA pipeline (`python -m training.run`). | Uses canonical configs from `configs/training/`. |

## Root files

- `README.md`, `LICENSE`, and `Makefile` provide project entry points and commands.
- `pyproject.toml` defines packaging, dependencies, linting, and tests.
- `.env.example` documents configuration without containing secrets.
- `teacher_prompt_manifest.json` and `teacher_schema_manifest.json` inventory the
  legacy teacher assets.
