"""HTTP helpers for teacher provider adapters."""

from __future__ import annotations

import json
from typing import Any
from urllib import error, request


class ProviderError(RuntimeError):
    """Base exception for provider runtime failures."""

    def __init__(
        self,
        *,
        provider: str,
        message: str,
        retriable: bool,
        status_code: int | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.message = message
        self.retriable = bool(retriable)
        self.status_code = status_code
        self.payload = payload or {}


class ProviderNetworkError(ProviderError):
    """Network-level transport error."""


class ProviderHTTPError(ProviderError):
    """HTTP response error from provider."""


class ProviderValidationError(ProviderError):
    """Output validation failure."""


def _extract_error_message(response_json: dict[str, Any], response_body: str) -> str:
    error_obj = response_json.get("error")
    if isinstance(error_obj, dict):
        message = error_obj.get("message")
        if isinstance(message, str) and message.strip():
            return " ".join(message.split())
    message = response_json.get("message")
    if isinstance(message, str) and message.strip():
        return " ".join(message.split())
    if response_body.strip():
        return " ".join(response_body.split())[:300]
    return "unknown_error"


def raise_for_status(
    *,
    provider: str,
    status: int,
    response_json: dict[str, Any],
    response_body: str,
) -> None:
    """Raise typed provider HTTP errors for non-2xx responses."""
    if status < 400:
        return

    provider_name = provider.strip().lower() or "provider"
    message = _extract_error_message(response_json, response_body)
    retriable = status in {408, 409, 425, 429} or status >= 500

    # Provider-specific hints from structured error payloads.
    error_obj = response_json.get("error")
    if isinstance(error_obj, dict):
        error_type = str(error_obj.get("type", "")).strip().lower()
        if error_type in {"rate_limit_error", "overloaded_error"}:
            retriable = True
        if error_type in {"authentication_error", "permission_error", "invalid_request_error"}:
            retriable = False

    if status in {401, 403, 404}:
        retriable = False

    raise ProviderHTTPError(
        provider=provider_name,
        message=f"{provider_name} http_status={status}: {message}",
        retriable=retriable,
        status_code=status,
        payload=response_json,
    )


def http_json_post(
    *,
    provider: str,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> tuple[int, dict[str, Any], str]:
    """Submit a JSON POST request and parse JSON response when possible."""
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url=url,
        data=encoded,
        headers=headers,
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            status = int(response.status)
            body = response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:  # pragma: no cover - runtime API variability
        status = int(exc.code)
        body = exc.read().decode("utf-8", errors="replace")
    except error.URLError as exc:  # pragma: no cover - runtime API variability
        provider_name = provider.strip().lower() or "provider"
        raise ProviderNetworkError(
            provider=provider_name,
            message=f"{provider_name} network_error: {exc}",
            retriable=True,
            payload={},
        ) from exc

    try:
        payload_json = json.loads(body) if body.strip() else {}
    except json.JSONDecodeError:
        payload_json = {"_raw_text": body}

    if isinstance(payload_json, dict):
        return status, payload_json, body

    return status, {"_raw_payload": payload_json}, body
