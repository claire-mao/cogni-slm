"""OpenAI-labeled teacher provider routed via TrueFoundry gateway."""

from __future__ import annotations

from .truefoundry_provider import TrueFoundryGatewayTeacherProvider


class OpenAITeacherProvider(TrueFoundryGatewayTeacherProvider):
    """OpenAI alias provider using the TrueFoundry gateway."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(provider_label="openai", **kwargs)

    @property
    def provider_name(self) -> str:
        return "openai"
