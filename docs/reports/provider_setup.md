# Provider Setup

This project now includes provider configuration and preflight validation for:

- OpenAI
- Anthropic
- Google (Gemini)
- DeepSeek
- OpenRouter

## Generated Configuration

- `configs/providers/providers_v1.json`
- `configs/providers/.env.template`
- `configs/providers/README.md`

## Credential Source

Provider credentials are read from `.env` (repository root) before execution.

Supported keys:

- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY` or `GOOGLE_API_KEY`
- `DEEPSEEK_API_KEY`
- `OPENROUTER_API_KEY` or `OPENROUTER_COMPAT_API_KEY`

Optional endpoint overrides are also supported (for example `OPENAI_BASE_URL`).

## Validation Implementation

New module:

- `src/teacher/provider_config.py`

Features:

- Loads `.env` without external dependencies.
- Validates required keys per provider.
- Supports provider aliases (`gemini -> google`, `openrouter_compatible -> openrouter`).
- Provides strict mode that fails fast before execution if config is incomplete.

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
  --providers openai,anthropic,google,deepseek,openrouter \
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
- `.env.example` has been expanded with provider key placeholders to simplify setup.
