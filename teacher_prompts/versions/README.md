# Prompt Versions

This directory stores prompt-version artifacts and A/B test configs managed by:

- `src/teacher/prompt_registry.py`

Layout:

- `teacher_prompts/versions/registry.json`
- `teacher_prompts/versions/prompts/<prompt_id>/<version>/prompt.txt`
- `teacher_prompts/versions/prompts/<prompt_id>/<version>/metadata.json`
- `teacher_prompts/versions/ab_tests/<experiment_id>.json`

The registry is file-backed and deterministic.
