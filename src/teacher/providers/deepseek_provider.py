"""DeepSeek-labeled teacher provider routed via TrueFoundry gateway."""

from __future__ import annotations

from .truefoundry_provider import TrueFoundryGatewayTeacherProvider


class DeepSeekTeacherProvider(TrueFoundryGatewayTeacherProvider):
    """DeepSeek alias provider using the TrueFoundry gateway."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(provider_label="deepseek", **kwargs)

    @property
    def provider_name(self) -> str:
        return "deepseek"
