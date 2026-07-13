"""Unified teacher provider abstraction package."""

from .anthropic_provider import AnthropicTeacherProvider
from .base import BaseTeacherProvider, TeacherExample, TeacherProvider
from .deepseek_provider import DeepSeekTeacherProvider
from .factory import canonical_provider_name, create_teacher_provider
from .gemini_provider import GeminiTeacherProvider
from .local_transformers_provider import LocalTransformersTeacherProvider
from .openai_provider import OpenAITeacherProvider
from .openrouter_provider import OpenRouterTeacherProvider
from .truefoundry_provider import TrueFoundryGatewayTeacherProvider

__all__ = [
    "AnthropicTeacherProvider",
    "BaseTeacherProvider",
    "DeepSeekTeacherProvider",
    "GeminiTeacherProvider",
    "LocalTransformersTeacherProvider",
    "OpenAITeacherProvider",
    "OpenRouterTeacherProvider",
    "TeacherExample",
    "TeacherProvider",
    "TrueFoundryGatewayTeacherProvider",
    "canonical_provider_name",
    "create_teacher_provider",
]
