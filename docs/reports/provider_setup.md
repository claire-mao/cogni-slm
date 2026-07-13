# Provider Setup

This project uses a single TrueFoundry OpenAI-compatible gateway for all remote teacher calls.
Provider labels are retained for experiment metadata and routing intent, but all requests go through one endpoint.

Default production stack:
- GPT-5 (primary teacher)
- Claude Opus 4.8 (verifier)
- Gemini 3.1 Pro (secondary teacher)

## Generated Configuration

- `configs/providers/providers_v1.json`
- `configs/providers/.env.template`
- `configs/providers/README.md`

## Credential Source

Provider credentials are read from `.env` (repository root) before execution.

Supported keys:

- `TFY_API_KEY` (preferred) or `TRUEFOUNDRY_API_KEY` (compatibility)
- `TFY_BASE_URL` (preferred) or `TRUEFOUNDRY_BASE_URL` (compatibility)
- `PRIMARY_TEACHER_MODEL`
- `VERIFIER_MODEL`
- `SECONDARY_MODEL`

Recommended:

- `TFY_API_KEY=...`
- `TFY_BASE_URL=https://tfy.promptlens.trilogy.com/v1`
- `PRIMARY_TEACHER_MODEL=openai-group/gpt-5`
- `VERIFIER_MODEL=claude-group/claude-opus-4-8`
- `SECONDARY_MODEL=gemini-group/gemini-3.1-pro`

## Validation Implementation

New module:

- `src/teacher/provider_config.py`

Features:

- Loads `.env` without external dependencies.
- Validates required keys for gateway-backed provider execution.
- Supports provider aliases (`gemini -> google`, `openrouter_compatible -> openrouter`).
- Provides strict mode that fails fast before execution if config is incomplete.

Model resolution:

- `PRIMARY_TEACHER_MODEL` is used for primary-teacher model slots (for example GPT-5, o3).
- `VERIFIER_MODEL` is used for verifier slots (for example Claude models).
- `SECONDARY_MODEL` is used for secondary/checker slots (for example Gemini, Qwen, Llama).

## Integrated Runners

Pre-execution provider validation is integrated into:

- `src/teacher/run_teacher_benchmark_execution.py`
- `src/teacher/run_teacher_experiment.py`
- `src/teacher/run_teacher_experiments.py`

Behavior:

- prepare/dry-run modes: validation runs in non-strict mode (report-only).
- execution modes: validation runs in strict mode and aborts if required keys are missing.

## Usage

Validate provider config directly:

```bash
python3 -m src.teacher.provider_config \
  --config-path configs/providers/providers_v1.json \
  --env-file .env \
  --providers openai,anthropic,google,openrouter \
  --strict
```

Prepare benchmark pipeline (no inference) with provider preflight report:

```bash
python3 -m src.teacher.run_teacher_benchmark_execution \
  --config-root configs/teacher \
  --dataset-root datasets/gold \
  --output-root outputs/teacher_benchmark \
  --providers-config configs/providers/providers_v1.json \
  --env-file .env
```

## Notes

- This setup does not call any provider APIs unless execution flags are explicitly enabled.
- `.env.example` now includes TrueFoundry gateway placeholders to simplify setup.
