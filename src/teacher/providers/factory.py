"""Factory utilities for teacher provider adapters."""

from __future__ import annotations

from typing import Any

from .anthropic_provider import AnthropicTeacherProvider
from .base import TeacherProvider
from .deepseek_provider import DeepSeekTeacherProvider
from .gemini_provider import GeminiTeacherProvider
from .local_transformers_provider import LocalTransformersTeacherProvider
from .openai_provider import OpenAITeacherProvider
from .openrouter_provider import OpenRouterTeacherProvider

_PROVIDER_ALIASES: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "deepseek": "deepseek",
    "openrouter": "openrouter",
    "openrouter_compatible": "openrouter",
    "truefoundry": "openai",
    "local": "local_transformers",
    "local_transformers": "local_transformers",
    "transformers": "local_transformers",
}


def canonical_provider_name(value: str) -> str:
    """Normalize provider labels to one canonical provider name."""
    key = value.strip().lower()
    if key in _PROVIDER_ALIASES:
        return _PROVIDER_ALIASES[key]

    allowed = ", ".join(sorted(set(_PROVIDER_ALIASES.values())))
    raise ValueError(f"Unsupported provider '{value}'. Expected one of: {allowed}")


def create_teacher_provider(
    *,
    provider: str,
    model_name: str,
    prompt_template: str | None = None,
    temperature: float = 0.0,
    seed: int | None = None,
    timeout_seconds: float = 120.0,
    max_output_tokens: int = 1200,
    extra_config: dict[str, Any] | None = None,
) -> TeacherProvider:
    """Instantiate a provider adapter implementing TeacherProvider."""
    extra = extra_config or {}
    name = canonical_provider_name(provider)

    common = {
        "model_name": model_name,
        "prompt_template": prompt_template,
        "temperature": temperature,
        "seed": seed,
        "timeout_seconds": timeout_seconds,
        "max_output_tokens": max_output_tokens,
    }

    if name == "openai":
        return OpenAITeacherProvider(**common)
    if name == "anthropic":
        return AnthropicTeacherProvider(**common)
    if name == "gemini":
        return GeminiTeacherProvider(**common)
    if name == "deepseek":
        return DeepSeekTeacherProvider(**common)
    if name == "openrouter":
        return OpenRouterTeacherProvider(**common)
    if name == "local_transformers":
        return LocalTransformersTeacherProvider(
            **common,
            device_map=str(extra.get("device_map", "auto")),
            trust_remote_code=bool(extra.get("trust_remote_code", True)),
        )

    raise ValueError(f"Provider dispatch not implemented for: {name}")
