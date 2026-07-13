"""OpenRouter-labeled teacher provider routed via TrueFoundry gateway."""

from __future__ import annotations

from .truefoundry_provider import TrueFoundryGatewayTeacherProvider


class OpenRouterTeacherProvider(TrueFoundryGatewayTeacherProvider):
    """OpenRouter alias provider using the TrueFoundry gateway."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(provider_label="openrouter", **kwargs)

    @property
    def provider_name(self) -> str:
        return "openrouter"
