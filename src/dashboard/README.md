# Dashboard Builder

Builds a consolidated experiment dashboard from existing artifacts only.

Entrypoint:

```bash
python3 -m src.dashboard.build_dashboard \
  --report-path docs/reports/dashboard.md
```

Default sources:

- teacher experiments: `outputs/teacher_runs/`
- training runs: `outputs/training_experiments/`
- tracked experiments: `outputs/experiments/`
- evaluation summaries:
  - `outputs/evaluation/harness/`
  - `outputs/evaluation_harness/`
  - `outputs/baseline/summary.json`
- error analysis: `outputs/error_analysis/error_analysis_summary.json`
- teacher leaderboard: `docs/reports/teacher_leaderboard.json`

Outputs:

- dashboard report: `docs/reports/dashboard.md`
