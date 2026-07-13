"""Gemini-labeled teacher provider routed via TrueFoundry gateway."""

from __future__ import annotations

from .truefoundry_provider import TrueFoundryGatewayTeacherProvider


class GeminiTeacherProvider(TrueFoundryGatewayTeacherProvider):
    """Gemini alias provider using the TrueFoundry gateway."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(provider_label="gemini", **kwargs)

    @property
    def provider_name(self) -> str:
        return "gemini"
