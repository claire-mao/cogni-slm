"""Shared parsing, normalization, validation, and accounting helpers."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

_ENV_PATTERN = re.compile(r"^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
_ENV_LOCK = None
_ENV_LOADED_FILES: set[str] = set()


def _get_env_lock() -> Any:
    global _ENV_LOCK
    if _ENV_LOCK is None:
        import threading

        _ENV_LOCK = threading.Lock()
    return _ENV_LOCK


def _parse_env_value(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.startswith("'") and text.endswith("'") and len(text) >= 2:
        return text[1:-1]
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        inner = text[1:-1]
        return inner.replace(r"\n", "\n").replace(r"\t", "\t").replace(r"\\", "\\")
    if " #" in text:
        text = text.split(" #", maxsplit=1)[0].strip()
    return text


def load_env_if_present(path: str | Path | None = None, *, override: bool = False) -> None:
    """Load `.env` style key/value pairs into os.environ if a file exists."""
    env_path = Path(path or os.getenv("TEACHER_ENV_FILE", ".env"))
    key = str(env_path.resolve())
    lock = _get_env_lock()
    with lock:
        if key in _ENV_LOADED_FILES:
            return
        if not env_path.exists() or not env_path.is_file():
            _ENV_LOADED_FILES.add(key)
            return

        with env_path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                match = _ENV_PATTERN.match(raw)
                if not match:
                    raise ValueError(f"Invalid env line at {env_path}:{line_number}")
                env_key, env_value = match.group(1), _parse_env_value(match.group(2))
                if override:
                    os.environ[env_key] = env_value
                else:
                    os.environ.setdefault(env_key, env_value)
        _ENV_LOADED_FILES.add(key)


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _env_bool(key: str, *, default: bool) -> bool:
    raw = os.getenv(key)
    if raw is None:
        return default
    text = raw.strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def env_bool(provider: str, key_suffix: str, *, default: bool) -> bool:
    provider_key = f"{provider.upper()}_{key_suffix}"
    if os.getenv(provider_key) is not None:
        return _env_bool(provider_key, default=default)
    return _env_bool(f"TEACHER_{key_suffix}", default=default)


def env_float(provider: str, key_suffix: str, *, default: float) -> float:
    provider_key = f"{provider.upper()}_{key_suffix}"
    raw = os.getenv(provider_key)
    if raw is None:
        raw = os.getenv(f"TEACHER_{key_suffix}")
    if raw is None:
        return float(default)
    try:
        value = float(raw)
    except ValueError:
        return float(default)
    return float(value)


def env_int(provider: str, key_suffix: str, *, default: int) -> int:
    provider_key = f"{provider.upper()}_{key_suffix}"
    raw = os.getenv(provider_key)
    if raw is None:
        raw = os.getenv(f"TEACHER_{key_suffix}")
    if raw is None:
        return int(default)
    try:
        value = int(raw)
    except ValueError:
        return int(default)
    return int(value)


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split()).strip()
    if isinstance(value, dict | list):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return " ".join(str(value).split()).strip()


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed != parsed:
        return None
    return parsed


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object start found in response")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue

        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise ValueError("No complete JSON object found in response")


def try_parse_json_output(text: str) -> tuple[dict[str, Any] | None, str | None]:
    """Best-effort parse of model response text into one JSON object."""
    stripped = text.strip()
    if not stripped:
        return None, "empty_response_text"

    try:
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            return payload, None
    except json.JSONDecodeError:
        pass

    try:
        payload_text = _extract_json_object(stripped)
        payload = json.loads(payload_text)
    except Exception as exc:  # pragma: no cover - parse variability
        return None, f"{type(exc).__name__}: {exc}"

    if not isinstance(payload, dict):
        return None, "parsed_payload_not_object"
    return payload, None


def _pick_first(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None


def _extract_reasoning(payload: dict[str, Any]) -> str:
    value = _pick_first(payload, ("reasoning", "analysis", "logical_analysis"))
    return _normalize_text(value)


def _extract_rubric_analysis(payload: dict[str, Any]) -> str:
    value = _pick_first(payload, ("rubric_analysis", "rubric", "rubric_feedback"))
    return _normalize_text(value)


def _extract_feedback(payload: dict[str, Any]) -> str:
    value = _pick_first(payload, ("feedback", "educational_feedback", "revision_plan"))
    return _normalize_text(value)


def _extract_score(payload: dict[str, Any]) -> float | None:
    score = _pick_first(payload, ("score", "predicted_score", "score_prediction"))
    numeric = _safe_float(score)
    return numeric


def _extract_confidence(payload: dict[str, Any]) -> float | None:
    confidence = _pick_first(payload, ("confidence", "rubric_adherence_confidence"))
    numeric = _safe_float(confidence)
    if numeric is None:
        return None
    if numeric > 1.0:
        numeric = numeric / 100.0
    return max(0.0, min(1.0, numeric))


def normalize_teacher_output(
    parsed_output: dict[str, Any] | None,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize provider-specific payload to unified teacher output contract."""
    payload = parsed_output if isinstance(parsed_output, dict) else {}

    return {
        "reasoning": _extract_reasoning(payload),
        "rubric_analysis": _extract_rubric_analysis(payload),
        "feedback": _extract_feedback(payload),
        "score": _extract_score(payload),
        "confidence": _extract_confidence(payload),
        "metadata": metadata or {},
    }


def _validate_json_schema(payload: dict[str, Any], schema_path: Path) -> list[str]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        return [f"schema_path_invalid:{schema_path}"]
    try:
        from jsonschema import Draft202012Validator  # type: ignore
    except Exception:
        required = schema.get("required")
        if isinstance(required, list):
            return [f"missing_required:{key}" for key in required if key not in payload]
        return []
    validator = Draft202012Validator(schema)
    return [error.message for error in validator.iter_errors(payload)]


def validate_normalized_output(
    *,
    parsed_output: dict[str, Any] | None,
    normalized_output: dict[str, Any],
    schema_path: str | Path | None,
) -> list[str]:
    """Validate provider output for strict JSON + normalized contract."""
    errors: list[str] = []
    if not isinstance(parsed_output, dict):
        errors.append("response_not_json_object")

    required = ("reasoning", "rubric_analysis", "feedback", "score", "confidence")
    for key in required:
        if key not in normalized_output:
            errors.append(f"missing_field:{key}")

    for key in ("reasoning", "rubric_analysis", "feedback"):
        value = normalized_output.get(key)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"invalid_text_field:{key}")

    score = _safe_float(normalized_output.get("score"))
    if score is None:
        errors.append("invalid_score")

    confidence = _safe_float(normalized_output.get("confidence"))
    if confidence is None:
        errors.append("invalid_confidence")
    elif confidence < 0.0 or confidence > 1.0:
        errors.append("confidence_out_of_range")

    if schema_path:
        path = Path(schema_path)
        if not path.exists() or not path.is_file():
            errors.append(f"schema_not_found:{path}")
        elif isinstance(parsed_output, dict):
            for schema_error in _validate_json_schema(parsed_output, path):
                errors.append(f"schema_error:{schema_error}")

    return sorted(set(errors))


def estimate_cost_usd_for_usage(
    *,
    model_name: str,
    input_tokens: int | None,
    output_tokens: int | None,
    canonical_model_hint: str | None = None,
) -> float | None:
    """Estimate request cost from token usage when model pricing is known."""
    in_tokens = _safe_int(input_tokens)
    out_tokens = _safe_int(output_tokens)
    if in_tokens is None or out_tokens is None:
        return None
    if in_tokens < 0 or out_tokens < 0:
        return None

    try:
        from ..models import canonical_model_id, estimate_cost_usd
    except Exception:
        return None

    candidate_ids: list[str] = []
    if canonical_model_hint:
        candidate_ids.append(canonical_model_hint)
    candidate_ids.append(model_name)
    if "/" in model_name:
        candidate_ids.append(model_name.rsplit("/", maxsplit=1)[-1])
    if ":" in model_name:
        candidate_ids.append(model_name.rsplit(":", maxsplit=1)[-1])
    lowered = model_name.lower()
    heuristic_aliases = (
        "gpt-5",
        "o3",
        "claude_opus_4_8",
        "claude-opus-4-8",
        "claude_opus_4",
        "claude-opus-4",
        "claude_sonnet_4",
        "claude-sonnet-4",
        "gemini_3_1_pro",
        "gemini-3.1-pro",
        "gemini_2_5_pro",
        "gemini-2.5-pro",
        "deepseek_r1",
        "deepseek-r1",
        "qwen3",
        "llama_4_maverick",
        "llama-4-maverick",
    )
    for alias in heuristic_aliases:
        if alias in lowered:
            candidate_ids.append(alias)
    for candidate in candidate_ids:
        try:
            canonical = canonical_model_id(candidate)
        except Exception:
            continue
        return estimate_cost_usd(canonical, in_tokens, out_tokens)
    return None


def openai_like_text_and_usage(response_json: dict[str, Any]) -> tuple[str, int | None, int | None]:
    """Extract content and token usage from OpenAI-compatible responses."""
    usage = response_json.get("usage")
    input_tokens = None
    output_tokens = None
    if isinstance(usage, dict):
        in_value = usage.get("prompt_tokens", usage.get("input_tokens"))
        out_value = usage.get("completion_tokens", usage.get("output_tokens"))
        if isinstance(in_value, int):
            input_tokens = in_value
        if isinstance(out_value, int):
            output_tokens = out_value

    content_text = ""
    choices = response_json.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first, dict) else {}
        content = message.get("content") if isinstance(message, dict) else ""
        if isinstance(content, str):
            content_text = content
        elif isinstance(content, list):
            parts = []
            for row in content:
                if isinstance(row, dict) and isinstance(row.get("text"), str):
                    parts.append(row["text"])
            content_text = "\n".join(parts)

    return content_text.strip(), input_tokens, output_tokens


def anthropic_text_and_usage(response_json: dict[str, Any]) -> tuple[str, int | None, int | None]:
    """Extract content and token usage from Anthropic responses."""
    usage = response_json.get("usage")
    input_tokens = None
    output_tokens = None
    if isinstance(usage, dict):
        in_value = usage.get("input_tokens")
        out_value = usage.get("output_tokens")
        if isinstance(in_value, int):
            input_tokens = in_value
        if isinstance(out_value, int):
            output_tokens = out_value

    parts: list[str] = []
    content = response_json.get("content")
    if isinstance(content, list):
        for row in content:
            if isinstance(row, dict) and isinstance(row.get("text"), str):
                text = row["text"].strip()
                if text:
                    parts.append(text)

    return "\n".join(parts).strip(), input_tokens, output_tokens


def gemini_text_and_usage(response_json: dict[str, Any]) -> tuple[str, int | None, int | None]:
    """Extract content and token usage from Gemini responses."""
    usage = response_json.get("usageMetadata")
    input_tokens = None
    output_tokens = None
    if isinstance(usage, dict):
        in_value = usage.get("promptTokenCount")
        out_value = usage.get("candidatesTokenCount")
        if isinstance(in_value, int):
            input_tokens = in_value
        if isinstance(out_value, int):
            output_tokens = out_value

    parts: list[str] = []
    candidates = response_json.get("candidates")
    if isinstance(candidates, list) and candidates:
        first = candidates[0] if isinstance(candidates[0], dict) else {}
        content = first.get("content") if isinstance(first, dict) else {}
        rows = content.get("parts") if isinstance(content, dict) else []
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict) and isinstance(row.get("text"), str):
                    text = row["text"].strip()
                    if text:
                        parts.append(text)

    return "\n".join(parts).strip(), input_tokens, output_tokens
