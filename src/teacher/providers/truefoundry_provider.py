"""OpenAI-compatible teacher provider adapters.

Routing modes:
- ``TEACHER_PROVIDER_MODE=truefoundry`` (default):
  - TFY_BASE_URL (preferred) or TRUEFOUNDRY_BASE_URL
  - TFY_API_KEY (preferred) or TRUEFOUNDRY_API_KEY
- ``TEACHER_PROVIDER_MODE=direct``:
  - TEACHER_BASE_URL
  - TEACHER_API_KEY
"""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from utils.environment import (
    get_teacher_api_key,
    get_teacher_base_url,
    get_teacher_base_url_variable_name,
    get_teacher_provider_mode,
)

from .base import BaseTeacherProvider
from .common import openai_like_text_and_usage
from .http import ProviderError, http_json_post, raise_for_status


class TrueFoundryGatewayTeacherProvider(BaseTeacherProvider):
    """Base provider implementation for the TrueFoundry OpenAI-compatible gateway."""

    def __init__(self, *, provider_label: str, **kwargs: Any) -> None:
        self._provider_label = provider_label.strip().lower() or "truefoundry"
        super().__init__(**kwargs)

    @property
    def provider_name(self) -> str:
        return self._provider_label

    def _invoke(self, prompt: str) -> tuple[dict[str, Any], str, int | None, int | None]:
        mode = get_teacher_provider_mode()
        api_key = get_teacher_api_key()
        if not api_key:
            raise ProviderError(
                provider=self.provider_name,
                message=(
                    "Missing "
                    + (
                        "TEACHER_API_KEY"
                        if mode == "direct"
                        else "TFY_API_KEY or TRUEFOUNDRY_API_KEY"
                    )
                ),
                retriable=False,
                payload={},
            )

        base_url = get_teacher_base_url()
        base_url_var = get_teacher_base_url_variable_name()
        if not base_url:
            raise ProviderError(
                provider=self.provider_name,
                message=(
                    "Missing "
                    + (
                        "TEACHER_BASE_URL"
                        if mode == "direct"
                        else "TFY_BASE_URL or TRUEFOUNDRY_BASE_URL"
                    )
                ),
                retriable=False,
                payload={},
            )

        parsed = urlparse(base_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ProviderError(
                provider=self.provider_name,
                message=(
                    f"Invalid {base_url_var or 'base URL'}. "
                    "Expected absolute http(s) URL, "
                    f"received: {base_url!r}"
                ),
                retriable=False,
                payload={},
            )

        url = f"{base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        if self.seed is not None:
            payload["seed"] = int(self.seed)

        status, response_json, response_body = http_json_post(
            provider=self.provider_name,
            url=url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
            timeout_seconds=self.timeout_seconds,
        )
        raise_for_status(
            provider=self.provider_name,
            status=status,
            response_json=response_json,
            response_body=response_body,
        )
        text, input_tokens, output_tokens = openai_like_text_and_usage(response_json)
        return response_json, text, input_tokens, output_tokens
