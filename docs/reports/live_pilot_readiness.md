# Live Pilot Readiness

Date: 2026-07-09  
Scope: first live teacher evaluation preflight (no inference executed)

## Executive Status

Overall readiness: **NO-GO (credentials pending)**

Implemented blockers:
- Resume/idempotency logic has been added to `src/teacher/run_teacher_experiments.py`.
- Environment validation CLI has been added: `src/teacher/validate_environment.py`.

Remaining blocker:
- Required API credentials are still missing in `.env`.

## Validation Results

| Area | Status | Evidence | Notes |
|---|---|---|---|
| API configuration | BLOCKED | `configs/providers/providers_v1.json`, `.env` | Required keys are currently missing in local environment. |
| Environment validator | READY | `src/teacher/validate_environment.py` | Validates `.env` format and required keys without printing secrets. |
| Dataset availability | READY | `datasets/gold/pilot20_v1.jsonl`, `datasets/gold/gold_v1.jsonl` | Required pilot and gold datasets exist and are readable. |
| Gold dataset | READY | `datasets/gold/gold_v1.jsonl` | 100 rows; parseable; unique `example_id`; no missing prompt/essay. |
| Pilot split | READY | `datasets/gold/pilot20_v1.jsonl`, `datasets/gold/pilot20_v1_manifest.json` | 20 rows; parseable; unique `example_id`; no missing prompt/essay. |
| Prompt versions | PARTIAL | `teacher_prompts/production_teacher.txt`, `teacher_prompts/versions/registry.json`, `configs/prompts/` | Prompt exists; registry governance artifacts are still sparse but not blocking pilot execution. |
| Teacher configurations | READY | `configs/teacher/teacher_pilot_live_v1.json`, `configs/teacher/teacher_task_suite_v1.json`, `configs/teacher/teacher_models_costs_v1.json` | Pilot model/provider references resolve. |
| Output directories | READY | `outputs/teacher_runs`, `docs/reports` | Writable and pre-created. |
| Logging | READY | `src/teacher/run_teacher_experiments.py` | Responses/failures/summary/manifest plus progress checkpoint metadata. |
| Resume support | READY | `src/teacher/run_teacher_experiments.py` | Completed requests are skipped on rerun using deterministic request keys and persisted progress. |

## Resume/Idempotency Changes

`src/teacher/run_teacher_experiments.py` now:
- computes deterministic request keys: `model|task|example|temperature|seed`
- loads completed request keys from:
  - existing `responses.jsonl`
  - `progress.json` checkpoint
- skips already completed requests on rerun (no duplicate successful outputs)
- preserves prior run artifacts (`responses.jsonl` and `failures.jsonl` are not truncated)
- writes progress checkpoints (`progress.json`) with:
  - `planned_requests`
  - `completed_request_keys`
  - `remaining_requests`
  - per-run attempted/success/failed counters
- updates summary metadata with:
  - `completed_requests_at_start`
  - `skipped_completed_requests`
  - `completed_requests_total`
  - `remaining_requests`

Result: rerunning the same `run_id` is idempotent for completed work.

## Environment Validation CLI

New command:

```bash
python3 -m src.teacher.validate_environment --env-file .env
```

Behavior:
- validates `.env` file existence and line format
- checks required keys:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `DEEPSEEK_API_KEY`
  - `GOOGLE_API_KEY`
- reports only key names/status (never values)
- exits with code `1` on validation failure and clear error text

## Go/No-Go Decision

Decision: **NO-GO** until credentials are set.

Minimum action to switch to GO:
1. Populate `.env` with non-empty values for required keys.
2. Re-run:
   - `python3 -m src.teacher.validate_environment --env-file .env`
3. Start pilot run using existing live pilot command.

## Execution Safety Note

No model inference was executed during this readiness update.
