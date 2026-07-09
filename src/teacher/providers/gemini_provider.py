"""Gemini teacher provider adapter."""

from __future__ import annotations

import os
from typing import Any
from urllib import parse

from .base import BaseTeacherProvider
from .common import gemini_text_and_usage
from .http import ProviderError, http_json_post, raise_for_status


class GeminiTeacherProvider(BaseTeacherProvider):
    """Teacher provider for Gemini generateContent APIs."""

    @property
    def provider_name(self) -> str:
        return "gemini"

    def _invoke(self, prompt: str) -> tuple[dict[str, Any], str, int | None, int | None]:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError(
                provider=self.provider_name,
                message="Missing GEMINI_API_KEY or GOOGLE_API_KEY",
                retriable=False,
                payload={},
            )

        base_url = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta")
        base_url = base_url.rstrip("/")

        model_encoded = parse.quote(self.model_name, safe="")
        key_encoded = parse.quote(api_key, safe="")
        url = f"{base_url}/models/{model_encoded}:generateContent?key={key_encoded}"

        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
                "responseMimeType": "application/json",
            },
        }
        if self.seed is not None:
            payload["generationConfig"]["seed"] = int(self.seed)

        status, response_json, response_body = http_json_post(
            provider=self.provider_name,
            url=url,
            headers={"Content-Type": "application/json"},
            payload=payload,
            timeout_seconds=self.timeout_seconds,
        )
        raise_for_status(
            provider=self.provider_name,
            status=status,
            response_json=response_json,
            response_body=response_body,
        )

        text, input_tokens, output_tokens = gemini_text_and_usage(response_json)
        return response_json, text, input_tokens, output_tokens
