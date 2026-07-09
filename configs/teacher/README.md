# Teacher Configs

Teacher-model validation and inference-related configuration files.

## Validation Protocol Configs

- `teacher_validation_master.json`: top-level orchestration config for pre-labeling teacher selection.
- `teacher_task_suite_v1.json`: evaluation task definitions and output contracts.
- `teacher_gold_set_v1.json`: exact 100-example gold-set construction protocol.
- `teacher_metrics_v1.json`: metric definitions, repeatability tests, and scorecard gates.
- `teacher_models_costs_v1.json`: model registry with deployment, cost, and runtime estimates.
- `teacher_ensembles_v1.json`: ensemble strategy definitions and planned comparisons.
- `teacher_rounds_v1.json`: multi-round execution order and exit criteria.
