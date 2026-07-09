# Environment Validation

Date: 2026-07-09  
Scope: preflight validation before first live teacher run (no inference executed)

## Command Check

Requested command:

```bash
python -m src.teacher.validate_environment
```

Result on this machine:
- `python` executable is not available (`command not found`).

Equivalent validation command executed:

```bash
python3 -m src.teacher.validate_environment
```

Result:
- exit code: `1`
- reason: `.env` file is missing

## Validation Summary

| Check | Status | Evidence |
|---|---|---|
| `.env` exists | FAIL | `.env` not found in repository root |
| Required provider API keys configured | FAIL | Validator could not check keys because `.env` is missing |
| Prompt registry is valid | PASS | `configs/prompts/registry.json` is valid JSON with expected top-level structure |
| Teacher configuration loads | PASS | `_load_plan(...)` succeeded for `configs/teacher` (`round_2_gold100`) |
| Pilot configuration loads | PASS | `_load_plan(...)` succeeded for `configs/teacher_pilot20_live` (`round_1_pilot_live`) |
| Output directories exist | PASS | `outputs/`, `outputs/teacher_runs/` exist |
| Logging directories exist | PASS | `outputs/logs/` exists |

## Detailed Findings

### 1. Environment validator output

`python3 -m src.teacher.validate_environment` returned:

```json
{
  "empty_keys": [],
  "env_file": ".env",
  "env_file_exists": false,
  "format_error": "Environment file not found: .env",
  "format_valid": false,
  "missing_keys": [],
  "present_keys": [],
  "required_keys": [
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "GOOGLE_API_KEY"
  ],
  "valid": false
}
```

No secret values were printed.

### 2. Prompt registry

- `configs/prompts/registry.json` exists.
- File parses correctly and includes expected keys (`schema_version`, `prompts`, timestamps).
- Registry is currently empty (`"prompts": {}`), but structurally valid.

### 3. Configuration loading

Validated by importing and invoking plan loader (`_load_plan`) only:
- `configs/teacher` + `round_2_gold100`: loaded successfully
- `configs/teacher_pilot20_live` + `round_1_pilot_live`: loaded successfully

No provider calls were made.

### 4. Directories

- Output directories present: `outputs/`, `outputs/teacher_runs/`
- Logging directory present: `outputs/logs/`

## Conclusion

Environment is **not ready** for a live teacher run yet.

Blocking item:
1. Create `.env` in repository root and populate required keys:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `DEEPSEEK_API_KEY`
   - `GOOGLE_API_KEY`

After creating `.env`, rerun:

```bash
python3 -m src.teacher.validate_environment
```

No model inference was executed during this validation.
