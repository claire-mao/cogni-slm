# Prompt Version Management

Implemented prompt version management at:

- `/Users/clairemao/Documents/cogni-slm/src/teacher/prompt_registry.py`

Storage root:

- `/Users/clairemao/Documents/cogni-slm/teacher_prompts/versions/`

## Supported Features

- prompt versions
- A/B prompt testing
- prompt metadata
- automatic prompt hashes

## Registry Design

The registry is file-backed and deterministic.

Primary artifacts:

- `teacher_prompts/versions/registry.json`
- `teacher_prompts/versions/prompts/<prompt_id>/<version>/prompt.txt`
- `teacher_prompts/versions/prompts/<prompt_id>/<version>/metadata.json`
- `teacher_prompts/versions/ab_tests/<experiment_id>.json`

## Core API

Main objects:

- `PromptRegistry`
- `PromptVersion`
- `ABVariant`
- `ABAssignment`

Main functions:

- `compute_prompt_hash(prompt_text)`
- `get_default_prompt_registry()`

Main methods:

- `register_prompt(...)`
- `register_prompt_file(...)`
- `list_prompt_versions(prompt_id)`
- `get_prompt_version(prompt_id, version="latest")`
- `get_prompt_text(prompt_id, version="latest")`
- `create_ab_test(...)`
- `list_ab_tests()`
- `load_ab_test(experiment_id)`
- `assign_ab_variant(experiment_id, unit_id, salt="")`

## Automatic Hashing

Each prompt version computes and stores:

- `prompt_hash_sha256`

Hash is generated from raw prompt text bytes and saved in both:

- version metadata file
- central registry index

## Versioning Behavior

- Prompt IDs are normalized to canonical slugs.
- Version IDs are supported explicitly or auto-generated.
- Auto version format: `v001`, `v002`, `v003`, ...
- `latest_version` is tracked per prompt in `registry.json`.

## A/B Testing Behavior

A/B tests are defined as weighted variants referencing prompt versions.

Deterministic assignment uses:

- `sha256(experiment_id | unit_id | salt)`

This provides stable assignment for repeated runs on the same unit.

## Usage Example

```python
from src.teacher.prompt_registry import PromptRegistry

registry = PromptRegistry("teacher_prompts/versions")

v1 = registry.register_prompt(
    prompt_id="production_teacher",
    prompt_text="Return strict JSON ...",
    metadata={"author": "team", "notes": "baseline"},
)

v2 = registry.register_prompt(
    prompt_id="production_teacher",
    prompt_text="Return strict JSON ... improved rubric instructions ...",
    metadata={"author": "team", "notes": "candidate"},
)

registry.create_ab_test(
    experiment_id="production_teacher_ab_v1",
    variants=[
        {"label": "A", "prompt_id": "production_teacher", "version": v1.version, "weight": 1.0},
        {"label": "B", "prompt_id": "production_teacher", "version": v2.version, "weight": 1.0},
    ],
    metadata={"objective": "compare rubric adherence"},
)

assignment = registry.assign_ab_variant(
    experiment_id="production_teacher_ab_v1",
    unit_id="example-000123",
)
```

## Notes

- This module only manages prompt artifacts and assignment logic.
- It does not run teacher inference and does not generate labels.
