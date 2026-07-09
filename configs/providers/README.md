# Provider Configuration

Provider preflight configuration used by teacher execution runners.

## Files

- `providers_v1.json`: provider requirements (required/optional env vars and aliases).
- `.env.template`: template of provider credentials and optional endpoint overrides.

## Validation

Use:

```bash
python3 -m src.teacher.provider_config \
  --config-path configs/providers/providers_v1.json \
  --env-file .env \
  --providers openai,anthropic,google,deepseek,openrouter
```

Add `--strict` to fail on missing required keys.
