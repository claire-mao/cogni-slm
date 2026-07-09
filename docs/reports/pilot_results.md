# Pilot Results (pilot_v1)

Date: 2026-07-09  
Run target: `outputs/teacher_runs/pilot_v1/`

## Scope Requested

- Configuration reference: `configs/teacher/teacher_pilot_v1.json`
- Dataset: `datasets/gold/pilot20_v1.jsonl`
- Teachers:
  - GPT-5
  - Claude Opus 4
  - DeepSeek R1

## Execution Outcome

Status: **BLOCKED BEFORE INFERENCE**

The live pilot was attempted with the production runner (`src.teacher.run_teacher_experiments`) and failed at provider preflight validation:

- Missing provider credentials in `.env` for required providers:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `DEEPSEEK_API_KEY`

Error captured:

> `ValueError: Provider configuration validation failed for: anthropic, deepseek, openai. Populate required keys in .env.`

No model API calls were executed.

## Artifacts Written

- `outputs/teacher_runs/pilot_v1/summary.json` (blocked-preflight metadata)

No `responses.jsonl` was produced because inference did not start.

## Resume Plan (No Overwrite)

After `.env` is configured, rerun with the same `run_id` (`pilot_v1`).

The runner now supports idempotent resume + checkpointing, so completed request keys are skipped and prior outputs are preserved.

```bash
python3 -m src.teacher.run_teacher_experiments \
  --config-root configs/teacher_pilot20_live \
  --evaluation-jsonl datasets/gold/pilot20_v1.jsonl \
  --round-id round_1_pilot_live \
  --prompt-template teacher_prompts/production_teacher.txt \
  --prompt-version production_teacher_v1 \
  --providers-config configs/providers/providers_v1.json \
  --env-file .env \
  --output-root outputs/teacher_runs \
  --run-id pilot_v1 \
  --max-examples 20 \
  --max-output-tokens 1200 \
  --timeout-seconds 120 \
  --seeds 42 \
  --temperatures 0.0 \
  --checkpoint-every 10
```

## Requirement Coverage

- Resume support: implemented in runner, but no inference started due credential block
- Checkpointing: enabled in command (`--checkpoint-every 10`), but no checkpoint progressed due preflight block
- Output validation: blocked before generation
- Latency/token/cost recording: blocked before generation
- Experiment metadata/raw outputs: blocked summary metadata written

