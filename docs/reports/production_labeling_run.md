# Production Labeling Run

Date: 2026-07-09  
Status: **BLOCKED BEFORE INFERENCE**

## Run Setup

Requested pipeline:

`dataset -> teacher inference -> validation -> quality filter -> confidence filter -> experiment tracking -> export`

Selected production teacher used for this run:
- `gpt-5` (from frozen production stack `configs/teacher/teacher_stack_v1.json`, primary teacher)

Input dataset:
- `datasets/final/quality_filtered.jsonl`

Planned outputs:
- teacher run artifacts: `outputs/teacher_runs/production_labeling_v1/`
- exported labels: `datasets/sft/`

## Execution Attempt

Command executed:

```bash
python3 -m src.teacher.run_labeling \
  --dataset datasets/final/quality_filtered.jsonl \
  --output-dir outputs/teacher_runs/production_labeling_v1 \
  --teacher-model gpt-5 \
  --provider openai \
  --prompt-template teacher_prompts/production_teacher.txt \
  --prompt-version production_teacher_v1 \
  --schema-path teacher_prompts/output_schema.json \
  --resume \
  --checkpoint-every 50
```

## Blocking Issues

### 1. Runtime import defect (fixed)

Initial run failed due module import error in `src/teacher/run_labeling.py`:

- `compute_prompt_hash` was imported from `src.teacher.providers.common` (wrong module).

Fix applied:
- Updated import to use `src.teacher.prompt_registry.compute_prompt_hash`.

### 2. Provider credentials missing (current blocker)

After fixing import, run failed during provider validation:

- `ValueError: Provider configuration validation failed for: openai. Populate required keys in .env.`

Root cause:
- `.env` file is missing, so `OPENAI_API_KEY` is not configured.

No model API calls were made.

## Pipeline Stage Status

- Dataset load: not reached (blocked in provider preflight)
- Teacher inference: blocked
- Output validation: blocked
- Quality filter: blocked
- Confidence filter: blocked
- Experiment tracking: blocked (tracker init occurs after provider preflight)
- Export to `datasets/sft/`: blocked

## Resume / Checkpointing

The run invocation included resume and checkpoint flags:
- `--resume`
- `--checkpoint-every 50`

These features are available in `run_labeling.py` but were not exercised because execution stopped at provider preflight.

## Output State

- `datasets/sft/` was **not modified** by this run attempt.
- No new production teacher responses were generated.

## Validation

Post-fix test run:

- `pytest -q` -> `51 passed`

## Next Step to Unblock

1. Create `.env` in repository root with at least:
   - `OPENAI_API_KEY=...`
2. Re-run the same command above.

Once credentials are present, the run will proceed with inference + validation, then export filtered labels to `datasets/sft/`.
