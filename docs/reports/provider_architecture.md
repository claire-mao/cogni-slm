# Unified Teacher Provider Architecture

Implemented unified teacher abstraction under:

- `/Users/clairemao/Documents/cogni-slm/src/teacher/providers/`

## Scope

Supported providers:

- OpenAI
- Anthropic
- Gemini
- DeepSeek
- OpenRouter
- Local Transformers

No inference was executed for this deliverable.

## Shared Interface

Core contract:

- `TeacherProvider.generate(example)`
- input type: `TeacherExample`
- output keys:
  - `reasoning`
  - `rubric_analysis`
  - `feedback`
  - `score`
  - `confidence`
  - `metadata`

Interface and base classes:

- `src/teacher/providers/base.py`
  - `TeacherExample`
  - `TeacherProvider` (abstract interface)
  - `BaseTeacherProvider` (shared lifecycle)

## Provider Adapters

Implemented adapters:

- `src/teacher/providers/openai_provider.py`
- `src/teacher/providers/anthropic_provider.py`
- `src/teacher/providers/gemini_provider.py`
- `src/teacher/providers/deepseek_provider.py`
- `src/teacher/providers/openrouter_provider.py`
- `src/teacher/providers/local_transformers_provider.py`

Shared helpers:

- `src/teacher/providers/common.py`
  - JSON extraction
  - provider response parsing utilities
  - normalized output mapping to unified schema
- `src/teacher/providers/http.py`
  - reusable JSON POST helper

Factory:

- `src/teacher/providers/factory.py`
  - `create_teacher_provider(...)`
  - `canonical_provider_name(...)`

Package exports:

- `src/teacher/providers/__init__.py`
- `src/teacher/__init__.py` updated to export provider interface/factory symbols

## Normalization Rules

All adapters map provider output to the same shape, with these defaults:

- `reasoning`: empty string if missing
- `rubric_analysis`: empty string if missing
- `feedback`: empty string if missing
- `score`: `0.0` if missing/unparseable
- `confidence`: clamped to `[0, 1]`, default `0.0`
- `metadata`: includes provider/model identifiers, latency, token counts when available,
  raw response text, parsed payload status, and provider raw response object

## Usage Example

```python
from src.teacher.providers import TeacherExample, create_teacher_provider

provider = create_teacher_provider(
    provider="openai",
    model_name="gpt-5",
    prompt_template=None,
    temperature=0.0,
    seed=11,
)

example = TeacherExample(
    example_id="ex-0001",
    prompt="Discuss whether school uniforms improve learning outcomes.",
    essay="...",
)

result = provider.generate(example)
# result has: reasoning, rubric_analysis, feedback, score, confidence, metadata
```

## Integration Notes

- Existing benchmarking/evaluation pipelines can now depend on `TeacherProvider` instead of
  provider-specific request code.
- The abstraction isolates provider transport details and keeps downstream logic provider-agnostic.
- Local Transformers support is lazy-loaded and requires local `transformers`/`torch` install.
