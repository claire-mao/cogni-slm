"""TrueFoundry connectivity smoke test.

This command sends a single OpenAI-compatible chat-completions request through the
configured TrueFoundry gateway and validates the assistant response is exactly:
{"status":"ok"}
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import ssl
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urllib_error
from urllib.parse import urlparse

from utils.environment import get_truefoundry_api_key, get_truefoundry_base_url

from .provider_config import load_env_file
from .providers.http import ProviderNetworkError, http_json_post

EXPECTED_RESPONSE: dict[str, str] = {"status": "ok"}
PROMPT_TEXT = 'Reply with exactly:\n{"status":"ok"}'


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extract_response_text(response_json: dict[str, Any]) -> str:
    choices = response_json.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n".join(parts).strip()
    return ""


def _extract_token_usage(response_json: dict[str, Any]) -> dict[str, int | None]:
    usage = response_json.get("usage")
    if not isinstance(usage, dict):
        return {"input_tokens": None, "output_tokens": None, "total_tokens": None}

    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")

    def _as_int(value: Any) -> int | None:
        if isinstance(value, int) and not isinstance(value, bool):
            return value
        return None

    in_value = _as_int(input_tokens)
    out_value = _as_int(output_tokens)
    total_value = _as_int(total_tokens)
    if total_value is None and in_value is not None and out_value is not None:
        total_value = in_value + out_value
    return {
        "input_tokens": in_value,
        "output_tokens": out_value,
        "total_tokens": total_value,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _normalize_base_url(base_url: str) -> str:
    return base_url.strip().rstrip("/")


def _validate_configuration() -> tuple[str, str, str]:
    api_key = get_truefoundry_api_key()
    if not api_key:
        raise ValueError("Missing TFY_API_KEY/TRUEFOUNDRY_API_KEY")

    base_url = get_truefoundry_base_url()
    if not base_url:
        raise ValueError("Missing TFY_BASE_URL/TRUEFOUNDRY_BASE_URL")

    normalized_base_url = _normalize_base_url(base_url)
    parsed = urlparse(normalized_base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(
            "Invalid TFY_BASE_URL/TRUEFOUNDRY_BASE_URL; "
            f"expected absolute http(s) URL, got {base_url!r}"
        )

    model_name = str(os.getenv("PRIMARY_TEACHER_MODEL", "")).strip()
    if not model_name:
        raise ValueError("Missing PRIMARY_TEACHER_MODEL")
    return api_key, normalized_base_url, model_name


def _response_error_message(response_json: dict[str, Any], response_body: str) -> str:
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
    return "No error payload returned."


def _http_error_category(status: int) -> str:
    if status == 401:
        return "http_401"
    if status == 403:
        return "http_403"
    if status == 404:
        return "http_404"
    if status >= 500:
        return "http_5xx"
    return "http_error"


def _iter_exception_chain(exc: BaseException) -> list[BaseException]:
    seen: set[int] = set()
    chain: list[BaseException] = []
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        chain.append(current)
        next_exc: BaseException | None = None
        if isinstance(current, Exception):
            if current.__cause__ is not None:
                next_exc = current.__cause__
            elif current.__context__ is not None:
                next_exc = current.__context__
        current = next_exc
    return chain


def _network_error_category(exc: BaseException) -> str:
    chain = _iter_exception_chain(exc)
    for item in chain:
        if isinstance(item, socket.gaierror):
            return "dns_resolution_failure"
        if isinstance(item, TimeoutError | socket.timeout):
            return "connection_timeout"
        if isinstance(item, ssl.SSLError):
            return "tls_ssl_error"
        if isinstance(item, urllib_error.URLError):
            reason = item.reason
            if isinstance(reason, socket.gaierror):
                return "dns_resolution_failure"
            if isinstance(reason, TimeoutError | socket.timeout):
                return "connection_timeout"
            if isinstance(reason, ssl.SSLError):
                return "tls_ssl_error"

    message = " ".join(str(item) for item in chain).lower()
    if any(
        text in message
        for text in (
            "nodename nor servname provided",
            "name or service not known",
            "temporary failure in name resolution",
        )
    ):
        return "dns_resolution_failure"
    if "timed out" in message or "timeout" in message:
        return "connection_timeout"
    if "ssl" in message or "tls" in message or "certificate" in message:
        return "tls_ssl_error"
    return "network_error"


def _request_diagnostics(
    *,
    base_url: str | None,
    endpoint: str | None,
    model_name: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    normalized_base_url = _normalize_base_url(base_url or "") if base_url else None
    endpoint_value = endpoint or None
    has_chat_suffix = bool(endpoint_value and endpoint_value.endswith("/chat/completions"))

    return {
        "resolved_base_url": base_url,
        "normalized_base_url": normalized_base_url,
        "final_request_url": endpoint_value,
        "selected_model": model_name,
        "http_method": "POST",
        "timeout_seconds": float(timeout_seconds),
        "base_url_has_http_scheme": bool(
            normalized_base_url and urlparse(normalized_base_url).scheme in {"http", "https"}
        ),
        "base_url_has_host": bool(normalized_base_url and urlparse(normalized_base_url).netloc),
        "chat_completions_appended": has_chat_suffix,
        "headers": {
            "authorization_scheme": "Bearer",
            "authorization_header_format": "Bearer <redacted>",
            "authorization_header_is_bearer": True,
            "content_type": "application/json",
        },
    }


def run_smoke_test(
    *,
    output_path: Path,
    timeout_seconds: float = 30.0,
    env_file: Path = Path(".env"),
    load_env: bool = True,
) -> dict[str, Any]:
    """Run one connectivity test request and save output artifact."""
    result: dict[str, Any] = {
        "timestamp_utc": _utc_now(),
        "success": False,
        "failure_category": None,
        "http_status": None,
        "latency_ms": None,
        "token_usage": {"input_tokens": None, "output_tokens": None, "total_tokens": None},
        "model_name": None,
        "request_diagnostics": _request_diagnostics(
            base_url=None,
            endpoint=None,
            model_name=None,
            timeout_seconds=timeout_seconds,
        ),
        "error": None,
    }

    try:
        env_loaded = False
        if load_env:
            if env_file.exists() and env_file.is_file():
                load_env_file(env_file, override=False)
                env_loaded = True
        result["env_file_loaded_before_env_read"] = env_loaded

        api_key, base_url, model_name = _validate_configuration()
        result["model_name"] = model_name
        endpoint = f"{base_url}/chat/completions"
        result["request_diagnostics"] = _request_diagnostics(
            base_url=base_url,
            endpoint=endpoint,
            model_name=model_name,
            timeout_seconds=timeout_seconds,
        )

        payload = {
            "model": model_name,
            "messages": [{"role": "user", "content": PROMPT_TEXT}],
            "temperature": 0.0,
            "max_tokens": 32,
        }

        started = time.perf_counter()
        status, response_json, response_body = http_json_post(
            provider="truefoundry_smoke_test",
            url=endpoint,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        latency_ms = (time.perf_counter() - started) * 1000.0

        result["http_status"] = status
        result["latency_ms"] = latency_ms
        result["token_usage"] = _extract_token_usage(response_json)

        if status < 200 or status >= 300:
            category = _http_error_category(status)
            detail = _response_error_message(response_json, response_body)
            result["failure_category"] = category
            raise RuntimeError(f"{category}: HTTP {status}. {detail}")

        response_text = _extract_response_text(response_json)
        if not response_text:
            result["failure_category"] = "json_parse_failure"
            raise ValueError("Empty assistant response text.")

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError as exc:
            result["failure_category"] = "json_parse_failure"
            raise ValueError(f"Assistant response is not valid JSON: {exc}") from exc

        if parsed != EXPECTED_RESPONSE:
            result["failure_category"] = "response_mismatch"
            raise ValueError(
                "Assistant response mismatch; expected exactly "
                f"{json.dumps(EXPECTED_RESPONSE, separators=(',', ':'))}"
            )

        result["success"] = True
        result["failure_category"] = None
    except ProviderNetworkError as exc:
        category = _network_error_category(exc)
        result["failure_category"] = category
        result["error"] = f"{category}: {exc.message}"
    except Exception as exc:
        category = result.get("failure_category")
        if not category:
            if isinstance(exc, ValueError) and (
                "Missing TFY_API_KEY/TRUEFOUNDRY_API_KEY" in str(exc)
                or "Missing TFY_BASE_URL/TRUEFOUNDRY_BASE_URL" in str(exc)
                or "Missing PRIMARY_TEACHER_MODEL" in str(exc)
                or "Invalid TFY_BASE_URL/TRUEFOUNDRY_BASE_URL" in str(exc)
            ):
                category = "configuration_error"
            else:
                category = _network_error_category(exc)
        result["failure_category"] = category
        result["error"] = f"{category}: {type(exc).__name__}: {exc}"

    _write_json(output_path, result)
    return result


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run TrueFoundry connectivity smoke test.")
    parser.add_argument("--env-file", default=".env", help="Path to .env file.")
    parser.add_argument(
        "--output-path",
        default="outputs/connectivity/smoke_test.json",
        help="Where to save smoke test result JSON.",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=30.0,
        help="HTTP timeout for the smoke test request.",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    result = run_smoke_test(
        output_path=Path(args.output_path),
        timeout_seconds=float(args.timeout_seconds),
        env_file=Path(args.env_file),
        load_env=True,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if not bool(result.get("success")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
