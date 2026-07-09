"""OpenRouter-compatible teacher provider adapter."""

from __future__ import annotations

import os
from typing import Any

from .base import BaseTeacherProvider
from .common import openai_like_text_and_usage
from .http import ProviderError, http_json_post, raise_for_status


class OpenRouterTeacherProvider(BaseTeacherProvider):
    """Teacher provider for OpenRouter and OpenAI-compatible routes."""

    @property
    def provider_name(self) -> str:
        return "openrouter"

    def _invoke(self, prompt: str) -> tuple[dict[str, Any], str, int | None, int | None]:
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_COMPAT_API_KEY")
        if not api_key:
            raise ProviderError(
                provider=self.provider_name,
                message="Missing OPENROUTER_API_KEY or OPENROUTER_COMPAT_API_KEY",
                retriable=False,
                payload={},
            )

        base_url = os.getenv("OPENROUTER_COMPAT_BASE_URL")
        if not base_url:
            base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        base_url = base_url.rstrip("/")

        url = f"{base_url}/chat/completions"
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},
        }
        if self.seed is not None:
            payload["seed"] = int(self.seed)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        title = os.getenv("OPENROUTER_X_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title

        status, response_json, response_body = http_json_post(
            provider=self.provider_name,
            url=url,
            headers=headers,
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
