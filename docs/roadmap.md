# Cogni Roadmap

This roadmap is behavior-first. ML implementation begins only after specification and data foundations are validated.

## Phase 0: Repository Foundation (Complete)
Deliverables:
- Project scaffold and baseline tooling.
- Initial repository standards (`pyproject.toml`, `Makefile`, docs structure).

Exit criteria:
- Reproducible local setup and consistent project layout.

## Phase 1: Problem and Behavior Lock (Current)
Deliverables:
- `docs/problem.md`
- `docs/behavior_spec.md`
- `docs/project_architecture.md`
- `docs/roadmap.md`

Exit criteria:
- Team sign-off on problem scope and non-goals.
- Behavior contract accepted as implementation authority.
- Explicit assumptions logged for validation.

## Phase 2: Taxonomy and Data Design
Deliverables:
- Fallacy taxonomy version `v0` with definitions and boundary notes.
- Dataset schema specs for `raw`, `processed`, and `eval`.
- Annotation protocol for diagnosis quality and pedagogical quality.

Exit criteria:
- Taxonomy ambiguity rules documented.
- Annotation guide validated through pilot labeling.
- Data quality checks defined for ingestion and processing.

## Phase 3: Data Pipeline Implementation
Deliverables:
- Scripts for ingestion, cleaning, and split generation.
- Schema validators and provenance tracking.
- Initial evaluation set assembly in `datasets/eval/`.

Exit criteria:
- Deterministic pipeline from raw input to processed/eval outputs.
- Re-run reproducibility confirmed from config and scripts.
- Basic integration tests passing in `tests/`.

## Phase 4: Baseline Modeling and Evaluation
Deliverables:
- Baseline fine-tuning implementation aligned to behavior spec.
- Evaluation harness for structural correctness and instructional quality.
- Error taxonomy from first model iteration.

Exit criteria:
- Baseline model runs end-to-end without contract violations.
- Evaluation outputs are reproducible and auditable.
- Priority failure modes identified with remediation plan.

## Phase 5: Iterative Improvement and Hardening
Deliverables:
- Data and prompt refinements targeting known failure modes.
- Regression suite expansion.
- Candidate release checklist for controlled user trials.

Exit criteria:
- Behavior regressions are tracked and controlled.
- Quality gates are stable across repeated runs.
- Documentation and artifacts support external review.

## Cross-Phase Risks and Mitigations
- Risk: fallacy overlap causes unstable labeling.
  - Mitigation: explicit multi-label policy and ambiguity annotations.
- Risk: analogies become stylistic but structurally weak.
  - Mitigation: enforce mapping/limits fields and targeted evaluation rubrics.
- Risk: small model capacity limits pedagogical depth.
  - Mitigation: strict prioritization of high-value behaviors and scoped taxonomy.

## Assumptions To Validate
- R1: Phase sequencing is sufficient to prevent costly rework before ML starts.
- R2: Behavior-first gating improves downstream evaluation quality.
- R3: Pilot annotation can expose major taxonomy and rubric issues early.
- R4: Initial baseline can remain small while still meeting teaching objectives.
- R5: Evaluation design can separate reasoning quality from writing style quality.

## Immediate Next Actions
1. Review and approve behavior contract language in `docs/behavior_spec.md`.
2. Define taxonomy draft and annotation template in `docs/`.
3. Convert architecture and roadmap assumptions into tracked validation tasks.

