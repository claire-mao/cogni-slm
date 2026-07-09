"""Anthropic teacher provider adapter."""

from __future__ import annotations

import os
from typing import Any

from .base import BaseTeacherProvider
from .common import anthropic_text_and_usage
from .http import ProviderError, http_json_post, raise_for_status


class AnthropicTeacherProvider(BaseTeacherProvider):
    """Teacher provider for Anthropic messages APIs."""

    @property
    def provider_name(self) -> str:
        return "anthropic"

    def _invoke(self, prompt: str) -> tuple[dict[str, Any], str, int | None, int | None]:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ProviderError(
                provider=self.provider_name,
                message="Missing ANTHROPIC_API_KEY",
                retriable=False,
                payload={},
            )

        base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com/v1").rstrip("/")
        url = f"{base_url}/messages"

        payload = {
            "model": self.model_name,
            "max_tokens": self.max_output_tokens,
            "temperature": self.temperature,
            "system": "Return one strict JSON object and nothing else.",
            "messages": [{"role": "user", "content": prompt}],
        }

        status, response_json, response_body = http_json_post(
            provider=self.provider_name,
            url=url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": os.getenv("ANTHROPIC_VERSION", "2023-06-01"),
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

        text, input_tokens, output_tokens = anthropic_text_and_usage(response_json)
        return response_json, text, input_tokens, output_tokens
