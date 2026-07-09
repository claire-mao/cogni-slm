# Teacher Pilot Live (20 Examples)

Date: 2026-07-09  
Run target: `teacher-pilot20-live-v1`

## Scope

- Dataset: `datasets/gold/pilot20_v1.jsonl` (20 examples)
- Teachers:
  - `gpt-5` (OpenAI)
  - `claude_opus_4x` (Anthropic)
  - `deepseek_r1` (DeepSeek)
- Tasks:
  - essay scoring
  - rubric adherence
  - educational feedback
  - logical reasoning
  - argument quality
  - logical fallacy identification

## Execution Attempt

Command was executed via `src.teacher.run_teacher_experiments` with `dry_run=false`.

Result: **BLOCKED before inference**.

## Blocker Details

Provider validation failed because `.env` does not exist and required API keys are missing.

Captured report:

- `outputs/teacher_runs/teacher-pilot20-live-v1_provider_validation.json`

Missing credentials:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DEEPSEEK_API_KEY`

## Resume Command

After creating `.env` with the required keys, run:

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
  --run-id teacher-pilot20-live-v1 \
  --max-examples 20 \
  --max-output-tokens 1400 \
  --timeout-seconds 120 \
  --seeds 42 \
  --temperatures 0.0
```

## Next Steps After Successful Pilot

1. Run benchmark:
```bash
python3 -m src.teacher.run_benchmark \
  --gold-path datasets/gold/pilot20_v1.jsonl \
  --predictions-path outputs/teacher_runs/teacher-pilot20-live-v1/responses.jsonl \
  --output-root outputs/teacher_benchmark \
  --run-id teacher-pilot20-live-v1
```

2. Generate leaderboard:
```bash
python3 -m src.teacher.leaderboard \
  --teacher-runs-root outputs/teacher_runs \
  --gold-path datasets/gold/pilot20_v1.jsonl \
  --task-suite configs/teacher/teacher_task_suite_v1.json \
  --output-json docs/reports/teacher_leaderboard.json \
  --output-md docs/reports/teacher_leaderboard.md
```

