"""Shared teacher-provider interface and base implementation."""

from __future__ import annotations

import logging
import os
import random
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from .common import (
    env_bool,
    env_float,
    env_int,
    estimate_cost_usd_for_usage,
    load_env_if_present,
    normalize_teacher_output,
    try_parse_json_output,
    validate_normalized_output,
)
from .http import ProviderError, ProviderValidationError

_LOGGER = logging.getLogger(__name__)
_RATE_LIMIT_LOCK = threading.Lock()
_RATE_LIMIT_STATE: dict[str, float] = {}


@dataclass(frozen=True)
class TeacherExample:
    """One evaluation example passed to a teacher provider."""

    example_id: str
    prompt: str
    essay: str
    score: float | None = None
    task_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TeacherProvider(ABC):
    """Unified teacher provider interface."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Stable provider identifier."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Concrete model identifier used for requests."""

    @abstractmethod
    def generate(self, example: TeacherExample) -> dict[str, Any]:
        """Generate one teacher response using the unified output contract."""


class BaseTeacherProvider(TeacherProvider, ABC):
    """Common request/response lifecycle for teacher providers."""

    def __init__(
        self,
        *,
        model_name: str,
        prompt_template: str | None = None,
        temperature: float = 0.0,
        seed: int | None = None,
        timeout_seconds: float = 120.0,
        max_output_tokens: int = 1200,
    ) -> None:
        load_env_if_present()
        self._model_name = model_name
        self.prompt_template = prompt_template
        self.temperature = float(temperature)
        self.seed = seed
        self.timeout_seconds = float(timeout_seconds)
        self.max_output_tokens = int(max_output_tokens)
        provider = self.provider_name.upper()
        self.max_retries = env_int(provider, "MAX_RETRIES", default=2)
        self.retry_base_delay_seconds = env_float(provider, "RETRY_BASE_DELAY_SECONDS", default=1.0)
        self.retry_max_delay_seconds = env_float(provider, "RETRY_MAX_DELAY_SECONDS", default=8.0)
        self.retry_jitter_seconds = env_float(provider, "RETRY_JITTER_SECONDS", default=0.0)
        self.rate_limit_rps = env_float(provider, "RATE_LIMIT_RPS", default=0.0)
        self.require_valid_output = env_bool(provider, "REQUIRE_VALID_OUTPUT", default=True)
        self.output_schema_path = self._resolve_output_schema_path(provider)

    @property
    def model_name(self) -> str:
        return self._model_name

    def _resolve_output_schema_path(self, provider: str) -> str | None:
        provider_specific = f"{provider}_OUTPUT_SCHEMA_PATH"
        value = os.getenv(provider_specific) or os.getenv("TEACHER_OUTPUT_SCHEMA_PATH")
        return str(value) if value else None

    def _rate_limit_key(self) -> str:
        return f"{self.provider_name}:{self.model_name}"

    def _maybe_wait_for_rate_limit(self) -> float:
        if self.rate_limit_rps <= 0:
            return 0.0
        min_interval = 1.0 / max(self.rate_limit_rps, 1e-9)
        now = time.monotonic()
        with _RATE_LIMIT_LOCK:
            key = self._rate_limit_key()
            last_ts = _RATE_LIMIT_STATE.get(key, 0.0)
            next_allowed = max(now, last_ts + min_interval)
            _RATE_LIMIT_STATE[key] = next_allowed
        sleep_seconds = max(0.0, next_allowed - now)
        if sleep_seconds > 0:
            time.sleep(sleep_seconds)
        return sleep_seconds

    def _retry_sleep_seconds(self, attempt_index: int) -> float:
        exponent = max(0, attempt_index - 1)
        base = self.retry_base_delay_seconds * (2**exponent)
        delay = min(self.retry_max_delay_seconds, base)
        if self.retry_jitter_seconds > 0:
            delay += random.uniform(0.0, self.retry_jitter_seconds)
        return max(0.0, delay)

    def _normalize_error(self, exc: Exception) -> ProviderError:
        if isinstance(exc, ProviderError):
            return exc
        return ProviderError(
            provider=self.provider_name,
            message=f"{self.provider_name} unexpected_error: {type(exc).__name__}: {exc}",
            retriable=False,
            payload={},
        )

    def build_prompt(self, example: TeacherExample) -> str:
        """Build provider prompt from template or default layout."""
        if self.prompt_template:
            score_value = "" if example.score is None else f"{example.score:.2f}"
            return (
                self.prompt_template.replace("{{prompt}}", example.prompt)
                .replace("{{essay}}", example.essay)
                .replace("{{score}}", score_value)
            )

        lines = [
            "Return strict JSON only.",
            "Required keys: reasoning, rubric_analysis, feedback, score, confidence, metadata.",
            "",
            "Prompt:",
            example.prompt,
            "",
            "Essay:",
            example.essay,
        ]
        if example.score is not None:
            lines.extend(["", f"Reference score (optional): {example.score:.2f}"])
        if example.task_id:
            lines.extend(["", f"Task ID: {example.task_id}"])
        return "\n".join(lines)

    def generate(self, example: TeacherExample) -> dict[str, Any]:
        """Generate unified teacher output for one example."""
        prompt = self.build_prompt(example)
        attempt = 0
        while True:
            attempt += 1
            rate_limit_sleep = self._maybe_wait_for_rate_limit()
            started = time.perf_counter()
            try:
                provider_payload, response_text, input_tokens, output_tokens = self._invoke(prompt)
                latency_ms = (time.perf_counter() - started) * 1000.0
                parsed_output, parse_error = try_parse_json_output(response_text)
                total_tokens = None
                if isinstance(input_tokens, int) and isinstance(output_tokens, int):
                    total_tokens = input_tokens + output_tokens
                estimated_cost_usd = estimate_cost_usd_for_usage(
                    model_name=self.model_name,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )

                metadata: dict[str, Any] = {
                    "provider": self.provider_name,
                    "model_name": self.model_name,
                    "example_id": example.example_id,
                    "task_id": example.task_id,
                    "latency_ms": latency_ms,
                    "rate_limit_sleep_seconds": rate_limit_sleep,
                    "attempt": attempt,
                    "max_retries": self.max_retries,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": estimated_cost_usd,
                    "parse_error": parse_error,
                    "raw_response_text": response_text,
                    "raw_json_output": parsed_output,
                    "provider_response": provider_payload,
                }
                if example.metadata:
                    metadata["example_metadata"] = example.metadata

                normalized = normalize_teacher_output(parsed_output, metadata=metadata)
                validation_errors = validate_normalized_output(
                    parsed_output=parsed_output,
                    normalized_output=normalized,
                    schema_path=self.output_schema_path,
                )
                metadata["validation_errors"] = validation_errors
                metadata["validation_passed"] = len(validation_errors) == 0
                normalized["metadata"] = metadata

                if validation_errors and self.require_valid_output:
                    raise ProviderValidationError(
                        provider=self.provider_name,
                        message=(
                            f"{self.provider_name} output validation failed: "
                            + ", ".join(validation_errors)
                        ),
                        retriable=False,
                        payload={
                            "validation_errors": validation_errors,
                            "example_id": example.example_id,
                            "task_id": example.task_id,
                        },
                    )

                _LOGGER.info(
                    "provider_call_success provider=%s model=%s example_id=%s task_id=%s "
                    "attempt=%s latency_ms=%.2f input_tokens=%s output_tokens=%s cost_usd=%s",
                    self.provider_name,
                    self.model_name,
                    example.example_id,
                    example.task_id,
                    attempt,
                    latency_ms,
                    input_tokens,
                    output_tokens,
                    estimated_cost_usd,
                )
                return normalized
            except Exception as exc:
                error = self._normalize_error(exc)
                should_retry = bool(error.retriable and attempt <= self.max_retries)
                _LOGGER.warning(
                    "provider_call_failed provider=%s model=%s example_id=%s task_id=%s "
                    "attempt=%s retriable=%s will_retry=%s error=%s",
                    self.provider_name,
                    self.model_name,
                    example.example_id,
                    example.task_id,
                    attempt,
                    error.retriable,
                    should_retry,
                    error.message,
                )
                if not should_retry:
                    raise error from exc
                delay = self._retry_sleep_seconds(attempt)
                if delay > 0:
                    time.sleep(delay)

    @abstractmethod
    def _invoke(self, prompt: str) -> tuple[dict[str, Any], str, int | None, int | None]:
        """Call provider endpoint and return payload/text/token counts."""
