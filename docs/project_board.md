# Cogni Project Board

## 1. Planning Gaps Identified in Repository Review
Before implementation, the following planning artifacts were missing and are now specified in this pass:
- `docs/literature_review.md`
- `docs/experiment_plan.md`
- `docs/architecture.mmd`
- `docs/project_board.md`

Additional planning artifacts still recommended before full-scale execution:
- taxonomy specification doc (`docs/taxonomy_v0.md`)
- annotation protocol (`docs/annotation_protocol.md`)
- training configuration spec (`docs/training_spec.md`)
- release and risk register (`docs/release_risk_register.md`)

## 2. Ticket Backlog

| Ticket | Title | Deliverable | Dependencies | Estimated Effort |
|---|---|---|---|---|
| PLN-001 | Finalize fallacy taxonomy v0 | `docs/taxonomy_v0.md` with boundary rules and label policy | None | 2 days |
| PLN-002 | Write annotation protocol | `docs/annotation_protocol.md` with QA workflow | PLN-001 | 2 days |
| PLN-003 | Define training spec | `docs/training_spec.md` for PEFT recipes, configs, run metadata | PLN-001, EVAL-001 | 2 days |
| PLN-004 | Create release risk register | `docs/release_risk_register.md` with mitigations and owners | PLN-003, EVAL-005 | 1 day |
| DATA-001 | Implement prompt registry and renderer | `src/data/prompts.py` implementation + tests | PLN-001 | 2 days |
| DATA-002 | Implement teacher orchestration | `src/data/teacher.py` generation/critique/revision adapters | DATA-001 | 3 days |
| DATA-003 | Implement generation orchestrator | `src/data/generate.py` stage control and artifacts | DATA-001, DATA-002 | 3 days |
| DATA-004 | Implement automatic filtering | `src/data/filter.py` hard/soft gates + reason codes | DATA-003 | 2 days |
| DATA-005 | Implement deduplication | `src/data/deduplicate.py` lexical/semantic/structural dedup | DATA-003 | 3 days |
| DATA-006 | Implement validation pipeline | `src/data/validate.py` schema and policy validation | DATA-004, DATA-005, PLN-002 | 2 days |
| DATA-007 | Implement JSONL export and manifests | `src/data/export.py` deterministic JSONL + manifest hash | DATA-006 | 2 days |
| DATA-008 | Build data pipeline integration tests | `tests/` for end-to-end data generation dry run | DATA-007 | 2 days |
| TRAIN-001 | Scaffold training package | `src/training/` interfaces and config loaders | PLN-003 | 2 days |
| TRAIN-002 | Implement PEFT training runner | LoRA/QLoRA SFT entrypoint with reproducible logging | TRAIN-001, DATA-007 | 4 days |
| TRAIN-003 | Implement checkpoint and adapter management | save/load/resume and artifact metadata | TRAIN-002 | 2 days |
| TRAIN-004 | Implement training smoke tests | minimal-run tests and config validation checks | TRAIN-003 | 2 days |
| EVAL-001 | Implement benchmark loader | `src/evaluation/benchmark.py` JSONL loaders and split controls | PLN-001, DATA-007 | 2 days |
| EVAL-002 | Implement deterministic checks | `src/evaluation/deterministic_checks.py` behavior contract checks | EVAL-001 | 3 days |
| EVAL-003 | Implement LLM judge layer | `src/evaluation/llm_judge.py` rubric scoring adapters | EVAL-001 | 3 days |
| EVAL-004 | Implement metrics and gate logic | `src/evaluation/metrics.py` aggregation, CI, gate decisions | EVAL-002, EVAL-003 | 3 days |
| EVAL-005 | Implement evaluator orchestration and reports | `evaluator.py` + `report.py` artifacts in `outputs/` | EVAL-004, TRAIN-003 | 3 days |
| EVAL-006 | Build evaluation regression tests | paired base-vs-tuned test harness and fixture suite | EVAL-005 | 2 days |
| OPS-001 | Add config package and schemas | config schemas for data/training/eval pipelines | PLN-003 | 2 days |
| OPS-002 | Add run registry and metadata tracking | run IDs, manifests, and reproducibility audit trail | DATA-007, TRAIN-003, EVAL-005 | 3 days |
| OPS-003 | Add CI checks for pipeline contracts | lint, import, schema-validation, and smoke tests in CI | DATA-008, TRAIN-004, EVAL-006 | 2 days |
| INF-001 | Scaffold inference package | `src/inference/` request/response and guard interfaces | EVAL-005 | 2 days |
| INF-002 | Implement inference behavior validator | output structure and safety guard enforcement | INF-001, EVAL-002 | 2 days |
| INF-003 | Build inference integration tests | tests for prompt -> structured response path | INF-002 | 2 days |

## 3. Dependency Summary by Milestone

### Milestone M1: Planning lock
- Complete: PLN-001, PLN-002, PLN-003
- Exit criterion: taxonomy, annotation, and training spec approved

### Milestone M2: Data pipeline implementation
- Complete: DATA-001 through DATA-008
- Exit criterion: reproducible validated JSONL exports with manifests

### Milestone M3: Training pipeline implementation
- Complete: TRAIN-001 through TRAIN-004
- Exit criterion: reproducible PEFT runs with checkpointed adapters

### Milestone M4: Evaluation pipeline implementation
- Complete: EVAL-001 through EVAL-006
- Exit criterion: paired base-vs-tuned gating reports on held-out benchmark

### Milestone M5: Inference and operations hardening
- Complete: OPS-001 through OPS-003, INF-001 through INF-003, PLN-004
- Exit criterion: end-to-end reproducibility and deployment-readiness checks

## 4. Critical Path
1. PLN-001 -> PLN-002 -> DATA-006
2. DATA-007 -> TRAIN-002 -> TRAIN-003 -> EVAL-005
3. EVAL-002 + EVAL-003 -> EVAL-004 -> EVAL-005 -> INF-002
4. TRAIN-004 + EVAL-006 -> OPS-003

## 5. Effort Rollup (Estimate)
- Planning tickets: 7 person-days
- Data pipeline tickets: 19 person-days
- Training tickets: 10 person-days
- Evaluation tickets: 16 person-days
- Ops and inference tickets: 11 person-days
- Total estimated effort: 63 person-days

## 6. Risks to Track in Execution
- fallacy taxonomy ambiguity causing noisy supervision labels
- low diversity in analogy/reflection generation despite target quotas
- quality-filter over-pruning that reduces useful training variation
- judge-model drift affecting evaluation comparability
- benchmark leakage from iterative prompt/data development loops
