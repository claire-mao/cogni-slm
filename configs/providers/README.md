# Provider Configuration

Provider preflight configuration used by teacher execution runners.
Default routing uses the TrueFoundry OpenAI-compatible gateway.

Optional bypass mode:
- set `TEACHER_PROVIDER_MODE=direct`
- provide `TEACHER_API_KEY` and `TEACHER_BASE_URL`
- all provider calls use that OpenAI-compatible endpoint directly

Default production stack routes:
- `PRIMARY_TEACHER_MODEL=openai-group/gpt-5`
- `VERIFIER_MODEL=claude-group/claude-opus-4-8`
- `SECONDARY_MODEL=gemini-group/gemini-3.1-pro`

## Files

- `providers_v1.json`: provider requirements (required/optional env vars and aliases).
- `.env.template`: template of required TrueFoundry credentials and model routes.

## Validation

Use:

```bash
python3 -m src.teacher.provider_config \
  --config-path configs/providers/providers_v1.json \
  --env-file .env \
  --providers openai,anthropic,google,openrouter
```

Add `--strict` to fail on missing required keys.

Required environment variables:

- Gateway mode (`TEACHER_PROVIDER_MODE=truefoundry`, default):
  - `TFY_API_KEY` (preferred) or `TRUEFOUNDRY_API_KEY`
  - `TFY_BASE_URL` (preferred) or `TRUEFOUNDRY_BASE_URL`
- Direct mode (`TEACHER_PROVIDER_MODE=direct`):
  - `TEACHER_API_KEY`
  - `TEACHER_BASE_URL`
- `PRIMARY_TEACHER_MODEL`
- `VERIFIER_MODEL`
- `SECONDARY_MODEL`
