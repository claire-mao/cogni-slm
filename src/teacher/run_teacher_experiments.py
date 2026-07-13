"""Run config-driven teacher model experiments across multiple API providers.

This runner:
- loads experiment configs from `configs/teacher/`
- executes every configured teacher model on the same evaluation examples
- records request/response metadata and model outputs to `outputs/teacher_runs/`

It does not modify datasets and does not generate production labels.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import urlparse

from utils.environment import (
    get_teacher_api_key,
    get_teacher_base_url,
    get_teacher_base_url_variable_name,
    get_teacher_provider_mode,
)

from .provider_config import validate_provider_configuration
from .providers.http import create_ssl_context


@dataclass(frozen=True)
class TaskSpec:
    """One task definition from teacher task suite config."""

    task_id: str
    description: str
    required_output_fields: tuple[str, ...]
    scoring_mode: str


@dataclass(frozen=True)
class ModelSpec:
    """One model definition from teacher cost/model registry config."""

    model_id: str
    display_name: str
    api_availability: str
    pricing: dict[str, Any]
    raw: dict[str, Any]


@dataclass(frozen=True)
class EvalExample:
    """Evaluation example row shared across all models."""

    example_id: str
    prompt: str
    essay: str
    score: float | None
    source: str
    difficulty: str


@dataclass(frozen=True)
class ExperimentPlan:
    """Resolved experiment plan for one run."""

    round_id: str
    run_id: str
    prompt_version: str
    models: tuple[ModelSpec, ...]
    tasks: tuple[TaskSpec, ...]
    examples: tuple[EvalExample, ...]
    seeds: tuple[int, ...]
    temperatures: tuple[float, ...]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_run_id() -> str:
    return datetime.now(timezone.utc).strftime("teacher-runs-%Y%m%dT%H%M%SZ")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing config file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Config must be a JSON object: {path}")
    return payload


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError(f"JSONL row must be object at {path}:{line_number}")
            rows.append(payload)
    return rows


def _safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _safe_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _is_simulated_example(payload: dict[str, Any]) -> bool:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    source_id = _normalize_text(payload.get("source_id")).lower()
    dataset_version = _normalize_text(payload.get("dataset_version")).lower()
    example_id = _normalize_text(payload.get("example_id") or payload.get("id")).lower()
    return (
        metadata.get("placeholder") is True
        or context.get("placeholder") is True
        or source_id.startswith("placeholder::synthetic")
        or "placeholder" in dataset_version
        or example_id.startswith("heldout-placeholder-")
    )


def _extract_examples(path: Path) -> tuple[EvalExample, ...]:
    rows = _read_jsonl(path)
    items: list[EvalExample] = []
    for index, payload in enumerate(rows, start=1):
        if _is_simulated_example(payload):
            raise ValueError(
                "Simulated/placeholder example detected in evaluation dataset at "
                f"{path}:{index}. Provide real reviewed evaluation examples."
            )
        example_id = _normalize_text(payload.get("example_id") or payload.get("id"))
        if not example_id:
            example_id = f"example-{index:06d}"

        prompt = _normalize_text(payload.get("prompt") or payload.get("prompt_text"))
        essay = _normalize_text(
            payload.get("essay")
            or payload.get("essay_text")
            or payload.get("text")
            or payload.get("input")
        )
        if not prompt or not essay:
            continue

        metadata = payload.get("metadata")
        if not isinstance(metadata, dict):
            metadata = {}

        items.append(
            EvalExample(
                example_id=example_id,
                prompt=prompt,
                essay=essay,
                score=_safe_float(payload.get("gold_score", payload.get("score"))),
                source=_normalize_text(payload.get("source", metadata.get("source"))) or "unknown",
                difficulty=(
                    _normalize_text(payload.get("difficulty", metadata.get("difficulty")))
                    or "unknown"
                ),
            )
        )
    return tuple(items)


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object start found in response.")

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
    raise ValueError("No complete JSON object found in response.")


def _try_parse_json_output(text: str) -> tuple[dict[str, Any] | None, str | None]:
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
    except Exception as exc:  # pragma: no cover - runtime parsing variability
        return None, f"{type(exc).__name__}: {exc}"
    if not isinstance(payload, dict):
        return None, "parsed_payload_not_object"
    return payload, None


def _extract_confidence(output_json: dict[str, Any] | None) -> float | None:
    if not isinstance(output_json, dict):
        return None
    for key in ("confidence", "rubric_adherence_confidence"):
        value = output_json.get(key)
        score = _safe_float(value)
        if score is not None:
            if score > 1.0:
                score = score / 100.0
            return max(0.0, min(1.0, score))
    inner = output_json.get("output")
    if isinstance(inner, dict):
        value = _safe_float(inner.get("confidence"))
        if value is not None:
            if value > 1.0:
                value = value / 100.0
            return max(0.0, min(1.0, value))
    return None


def _env_key_for_model_name(model_id: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", model_id).strip("_").upper()
    return f"TEACHER_MODEL_NAME_{normalized}"


def _canonicalish_model_id(model_id: str) -> str:
    raw = _normalize_text(model_id).lower().replace("-", "_")
    return raw


def _model_role_env_key(model: ModelSpec) -> str:
    model_id = _canonicalish_model_id(model.model_id)
    if model_id in {"gpt_5", "o3"}:
        return "PRIMARY_TEACHER_MODEL"
    if "claude" in model_id:
        return "VERIFIER_MODEL"
    return "SECONDARY_MODEL"


def _infer_provider(model: ModelSpec) -> str:
    key = model.api_availability.lower()
    if "openai_api" in key:
        return "openai"
    if "anthropic" in key:
        return "anthropic"
    if "gemini" in key or "vertex" in key:
        return "gemini"
    if "deepseek" in key:
        return "deepseek"
    if "openai_compatible" in key or "provider_dependent" in key:
        return "openrouter_compatible"
    return "openrouter_compatible"


def _first_numeric(value: Any) -> float | None:
    if isinstance(value, int | float) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, list):
        numeric_values = [
            float(item)
            for item in value
            if isinstance(item, int | float) and not isinstance(item, bool)
        ]
        if numeric_values:
            return sum(numeric_values) / len(numeric_values)
    return None


def _pricing_for_model(model: ModelSpec) -> tuple[float | None, float | None]:
    pricing = model.pricing
    input_price = _first_numeric(pricing.get("input"))
    if input_price is None:
        input_price = _first_numeric(pricing.get("input_estimated_range"))

    output_price = _first_numeric(pricing.get("output"))
    if output_price is None:
        output_price = _first_numeric(pricing.get("output_non_thinking"))
    if output_price is None:
        output_price = _first_numeric(pricing.get("output_thinking"))
    if output_price is None:
        output_price = _first_numeric(pricing.get("output_estimated_range"))
    return input_price, output_price


def _estimate_cost(
    *,
    model: ModelSpec,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float | None:
    if input_tokens is None or output_tokens is None:
        return None
    input_price, output_price = _pricing_for_model(model)
    if input_price is None or output_price is None:
        return None
    return (input_tokens / 1_000_000.0) * input_price + (output_tokens / 1_000_000.0) * output_price


def _http_json_post(
    *,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: float,
) -> tuple[int, dict[str, Any], str]:
    encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url=url, data=encoded, headers=headers, method="POST")
    ssl_context = create_ssl_context()
    try:
        with request.urlopen(req, timeout=timeout_seconds, context=ssl_context) as resp:
            status = int(resp.status)
            body = resp.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:  # pragma: no cover - runtime API failure path
        status = int(exc.code)
        body = exc.read().decode("utf-8", errors="replace")
    except error.URLError as exc:  # pragma: no cover - runtime API failure path
        raise RuntimeError(f"Network error: {exc}") from exc

    parsed: dict[str, Any]
    try:
        payload_json = json.loads(body) if body.strip() else {}
    except json.JSONDecodeError:
        payload_json = {"_raw_text": body}
    if isinstance(payload_json, dict):
        parsed = payload_json
    else:
        parsed = {"_raw_payload": payload_json}
    return status, parsed, body


def _build_prompt(
    *,
    prompt_template: str,
    example: EvalExample,
    task: TaskSpec,
) -> str:
    rendered = (
        prompt_template.replace("{{prompt}}", example.prompt)
        .replace("{{essay}}", example.essay)
        .replace("{{score}}", "" if example.score is None else f"{example.score:.2f}")
    )
    task_block = "\n".join(
        [
            "",
            "[EXPERIMENT TASK]",
            f"task_id: {task.task_id}",
            f"description: {task.description}",
            f"required_output_fields: {', '.join(task.required_output_fields)}",
            f"scoring_mode: {task.scoring_mode}",
            "",
            "[SERIALIZATION REQUIREMENT]",
            "Return strict JSON only, with fields required for this task.",
        ]
    )
    return rendered + task_block


def _openai_like_text_and_usage(
    response_json: dict[str, Any],
) -> tuple[str, int | None, int | None]:
    usage = response_json.get("usage")
    input_tokens = None
    output_tokens = None
    if isinstance(usage, dict):
        input_tokens = int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        output_tokens = int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)

    text = ""
    choices = response_json.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first, dict) else {}
        content = message.get("content") if isinstance(message, dict) else ""
        if isinstance(content, str):
            text = content
        elif isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    part = item.get("text")
                    if isinstance(part, str):
                        parts.append(part)
            text = "\n".join(parts)
    return text.strip(), input_tokens, output_tokens


def _anthropic_text_and_usage(response_json: dict[str, Any]) -> tuple[str, int | None, int | None]:
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

    text_parts: list[str] = []
    content = response_json.get("content")
    if isinstance(content, list):
        for item in content:
            if not isinstance(item, dict):
                continue
            part = item.get("text")
            if isinstance(part, str) and part.strip():
                text_parts.append(part.strip())
    return "\n".join(text_parts).strip(), input_tokens, output_tokens


def _gemini_text_and_usage(response_json: dict[str, Any]) -> tuple[str, int | None, int | None]:
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

    text_parts: list[str] = []
    candidates = response_json.get("candidates")
    if isinstance(candidates, list) and candidates:
        first = candidates[0] if isinstance(candidates[0], dict) else {}
        content = first.get("content") if isinstance(first, dict) else {}
        parts = content.get("parts") if isinstance(content, dict) else []
        if isinstance(parts, list):
            for part in parts:
                if isinstance(part, dict):
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        text_parts.append(text.strip())
    return "\n".join(text_parts).strip(), input_tokens, output_tokens


def _call_openai(
    *,
    model_name: str,
    provider: str,
    prompt: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str, int | None, int | None]:
    provider_mode = get_teacher_provider_mode()
    api_key = get_teacher_api_key()
    if not api_key:
        if provider_mode == "direct":
            raise RuntimeError("Missing TEACHER_API_KEY")
        raise RuntimeError("Missing TFY_API_KEY or TRUEFOUNDRY_API_KEY")
    base_url = get_teacher_base_url()
    base_url_var = get_teacher_base_url_variable_name()
    if not base_url:
        if provider_mode == "direct":
            raise RuntimeError("Missing TEACHER_BASE_URL")
        raise RuntimeError("Missing TFY_BASE_URL or TRUEFOUNDRY_BASE_URL")
    parsed_url = urlparse(base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        expected_name = (
            base_url_var
            or ("TEACHER_BASE_URL" if provider_mode == "direct" else "TFY_BASE_URL")
        )
        raise RuntimeError(
            f"Invalid {expected_name}. "
            f"Expected absolute http(s) URL, got: {base_url!r}"
        )
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "seed": seed,
        "max_tokens": max_output_tokens,
        "response_format": {"type": "json_object"},
    }
    status, response_json, _ = _http_json_post(
        url=url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    if status >= 400:
        raise RuntimeError(
            f"TrueFoundry gateway API error provider={provider} status={status}: {response_json}"
        )
    text, in_tokens, out_tokens = _openai_like_text_and_usage(response_json)
    return response_json, text, in_tokens, out_tokens


def _call_deepseek(
    *,
    model_name: str,
    prompt: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str, int | None, int | None]:
    return _call_openai(
        model_name=model_name,
        provider="deepseek",
        prompt=prompt,
        temperature=temperature,
        seed=seed,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )


def _call_openrouter_compatible(
    *,
    model_name: str,
    prompt: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str, int | None, int | None]:
    return _call_openai(
        model_name=model_name,
        provider="openrouter_compatible",
        prompt=prompt,
        temperature=temperature,
        seed=seed,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )


def _call_anthropic(
    *,
    model_name: str,
    prompt: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str, int | None, int | None]:
    return _call_openai(
        model_name=model_name,
        provider="anthropic",
        prompt=prompt,
        temperature=temperature,
        seed=seed,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )


def _call_gemini(
    *,
    model_name: str,
    prompt: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str, int | None, int | None]:
    return _call_openai(
        model_name=model_name,
        provider="gemini",
        prompt=prompt,
        temperature=temperature,
        seed=seed,
        timeout_seconds=timeout_seconds,
        max_output_tokens=max_output_tokens,
    )


def _call_provider(
    *,
    provider: str,
    model_name: str,
    prompt: str,
    temperature: float,
    seed: int,
    timeout_seconds: float,
    max_output_tokens: int,
) -> tuple[dict[str, Any], str, int | None, int | None]:
    if provider == "openai":
        return _call_openai(
            model_name=model_name,
            provider="openai",
            prompt=prompt,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    if provider == "anthropic":
        return _call_anthropic(
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    if provider == "gemini":
        return _call_gemini(
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    if provider == "deepseek":
        return _call_deepseek(
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    if provider == "openrouter_compatible":
        return _call_openrouter_compatible(
            model_name=model_name,
            prompt=prompt,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
    raise ValueError(f"Unsupported provider: {provider}")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temp_path.replace(path)


def _temp_key(value: float | int | str) -> str:
    if isinstance(value, str):
        parsed = _safe_float(value)
        if parsed is None:
            return value.strip()
        value = parsed
    if isinstance(value, int):
        return str(value)
    return format(float(value), ".12g")


def _request_key(
    *,
    model_id: str,
    task_id: str,
    example_id: str,
    temperature: float | str,
    seed: int | str,
) -> str:
    return "|".join(
        [
            _normalize_text(model_id),
            _normalize_text(task_id),
            _normalize_text(example_id),
            _temp_key(temperature),
            str(int(seed)),
        ]
    )


def _load_completed_keys_from_responses(path: Path, *, run_id: str) -> set[str]:
    if not path.exists():
        return set()

    completed: set[str] = set()
    for row in _read_jsonl(path):
        if _normalize_text(row.get("run_id")) and _normalize_text(row.get("run_id")) != run_id:
            continue
        request_key = _normalize_text(row.get("request_key"))
        if request_key:
            completed.add(request_key)
            continue

        model_id = _normalize_text(row.get("model"))
        task_id = _normalize_text(row.get("task_id"))
        example_id = _normalize_text(row.get("example_id"))
        seed_raw = row.get("seed")
        temperature = row.get("temperature")
        if not model_id or not task_id or not example_id:
            continue
        seed = _safe_int(seed_raw)
        if seed is None:
            continue
        temp_numeric = _safe_float(temperature)
        if temp_numeric is None:
            continue
        completed.add(
            _request_key(
                model_id=model_id,
                task_id=task_id,
                example_id=example_id,
                temperature=temp_numeric,
                seed=seed,
            )
        )
    return completed


def _load_progress_state(progress_path: Path, *, run_id: str) -> set[str]:
    if not progress_path.exists():
        return set()
    payload = _read_json(progress_path)
    if _normalize_text(payload.get("run_id")) != run_id:
        return set()
    keys = payload.get("completed_request_keys")
    if not isinstance(keys, list):
        return set()
    return {str(item).strip() for item in keys if str(item).strip()}


def _write_progress_state(
    *,
    progress_path: Path,
    run_id: str,
    planned_requests: int,
    completed_request_keys: set[str],
    attempted_requests: int,
    successful_requests: int,
    failed_requests: int,
    checkpoint_index: int,
    dry_run: bool,
) -> None:
    completed_count = len(completed_request_keys)
    payload = {
        "run_id": run_id,
        "updated_at_utc": _utc_now(),
        "planned_requests": planned_requests,
        "completed_requests": completed_count,
        "remaining_requests": max(0, planned_requests - completed_count),
        "attempted_requests_current_run": attempted_requests,
        "successful_requests_current_run": successful_requests,
        "failed_requests_current_run": failed_requests,
        "checkpoint_index": checkpoint_index,
        "dry_run": dry_run,
        "completed_request_keys": sorted(completed_request_keys),
    }
    _atomic_write_json(progress_path, payload)


def _load_plan(
    *,
    config_root: Path,
    evaluation_jsonl: Path,
    round_id: str,
    max_examples: int,
    prompt_template_path: Path,
    prompt_version: str,
    run_id: str,
    seeds_override: tuple[int, ...] | None,
    temperatures: tuple[float, ...],
) -> ExperimentPlan:
    master = _read_json(config_root / "teacher_validation_master.json")
    configs = master.get("configs")
    if not isinstance(configs, dict):
        raise ValueError("teacher_validation_master.json missing configs object.")

    rounds_cfg = _read_json(Path(str(configs["round_schedule"])))
    tasks_cfg = _read_json(Path(str(configs["task_suite"])))
    models_cfg = _read_json(Path(str(configs["models_costs"])))
    metrics_cfg = _read_json(Path(str(configs["metrics"])))

    rounds = rounds_cfg.get("rounds")
    if not isinstance(rounds, list):
        raise ValueError("teacher_rounds_v1.json missing rounds list.")
    selected_round = None
    for item in rounds:
        if isinstance(item, dict) and item.get("round_id") == round_id:
            selected_round = item
            break
    if not isinstance(selected_round, dict):
        raise ValueError(f"Round id not found in teacher_rounds_v1.json: {round_id}")

    configured_model_ids = selected_round.get("models")
    if not isinstance(configured_model_ids, list):
        raise ValueError(f"Round {round_id} missing model list.")
    unresolved_templates = [
        value for value in configured_model_ids if isinstance(value, str) and "_from_" in value
    ]
    if unresolved_templates:
        raise ValueError(
            f"Round {round_id} has unresolved template model ids: "
            f"{', '.join(unresolved_templates)}"
        )
    model_ids = [str(value) for value in configured_model_ids if isinstance(value, str)]

    models_list = models_cfg.get("models")
    if not isinstance(models_list, list):
        raise ValueError("teacher_models_costs_v1.json missing models list.")
    model_index: dict[str, ModelSpec] = {}
    for row in models_list:
        if not isinstance(row, dict):
            continue
        model_id = row.get("model_id")
        if not isinstance(model_id, str):
            continue
        pricing = row.get("pricing_usd_per_million_tokens")
        if not isinstance(pricing, dict):
            pricing = {}
        model_index[model_id] = ModelSpec(
            model_id=model_id,
            display_name=str(row.get("display_name", model_id)),
            api_availability=str(row.get("api_availability", "")),
            pricing=dict(pricing),
            raw=dict(row),
        )

    missing_models = [model_id for model_id in model_ids if model_id not in model_index]
    if missing_models:
        raise ValueError(f"Missing model definitions in models_costs config: {missing_models}")
    models = tuple(model_index[model_id] for model_id in model_ids)

    task_rows = tasks_cfg.get("tasks")
    if not isinstance(task_rows, list):
        raise ValueError("teacher_task_suite_v1.json missing tasks list.")
    tasks: list[TaskSpec] = []
    for row in task_rows:
        if not isinstance(row, dict):
            continue
        task_id = row.get("task_id")
        description = row.get("description")
        fields = row.get("required_output_fields")
        scoring_mode = row.get("scoring_mode")
        if not isinstance(task_id, str) or not isinstance(description, str):
            continue
        if not isinstance(fields, list):
            fields = []
        if not isinstance(scoring_mode, str):
            scoring_mode = "unknown"
        tasks.append(
            TaskSpec(
                task_id=task_id,
                description=description,
                required_output_fields=tuple(str(item) for item in fields),
                scoring_mode=scoring_mode,
            )
        )
    if not tasks:
        raise ValueError("No tasks resolved from teacher_task_suite_v1.json.")

    examples = list(_extract_examples(evaluation_jsonl))
    if not examples:
        raise ValueError(f"No valid evaluation examples found in: {evaluation_jsonl}")

    round_examples = selected_round.get("examples")
    if isinstance(round_examples, int):
        target_count = round_examples
    elif isinstance(round_examples, str) and round_examples.strip().lower() == "full_dataset":
        target_count = len(examples)
    else:
        target_count = len(examples)
    if max_examples > 0:
        target_count = min(target_count, max_examples)
    examples = examples[:target_count]

    repeatability = metrics_cfg.get("repeatability_tests")
    schedule = ()
    if isinstance(repeatability, dict):
        seeds = repeatability.get("seed_schedule")
        if isinstance(seeds, list):
            schedule = tuple(int(value) for value in seeds if isinstance(value, int))
    if seeds_override is not None:
        seed_values = seeds_override
    else:
        seed_values = schedule if schedule else (42,)

    prompt_template_text = prompt_template_path.read_text(encoding="utf-8")
    prompt_version_label = prompt_version.strip() if prompt_version.strip() else "v1"
    # Ensure template is read now; content is used later.
    _ = prompt_template_text

    return ExperimentPlan(
        round_id=round_id,
        run_id=run_id,
        prompt_version=prompt_version_label,
        models=models,
        tasks=tuple(tasks),
        examples=tuple(examples),
        seeds=tuple(seed_values),
        temperatures=temperatures,
    )


def _write_manifest(
    *,
    output_dir: Path,
    plan: ExperimentPlan,
    prompt_template_path: Path,
    evaluation_jsonl: Path,
    max_output_tokens: int,
    timeout_seconds: float,
    dry_run: bool,
) -> None:
    manifest = {
        "run_id": plan.run_id,
        "created_at": _utc_now(),
        "round_id": plan.round_id,
        "prompt_version": plan.prompt_version,
        "prompt_template_path": str(prompt_template_path),
        "evaluation_jsonl": str(evaluation_jsonl),
        "model_ids": [item.model_id for item in plan.models],
        "task_ids": [item.task_id for item in plan.tasks],
        "example_count": len(plan.examples),
        "seed_count": len(plan.seeds),
        "temperature_count": len(plan.temperatures),
        "max_output_tokens": max_output_tokens,
        "timeout_seconds": timeout_seconds,
        "dry_run": dry_run,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _resolve_api_model_name(model: ModelSpec) -> str:
    role_env_key = _model_role_env_key(model)
    role_model = os.getenv(role_env_key, "").strip()
    if role_model:
        return role_model

    per_model_key = _env_key_for_model_name(model.model_id)
    override = os.getenv(per_model_key, "").strip()
    if override:
        return override

    raw_key = model.raw.get("model_env_var")
    if isinstance(raw_key, str) and raw_key.strip():
        raw_override = os.getenv(raw_key.strip(), "").strip()
        if raw_override:
            return raw_override

    raise ValueError(
        "Missing model mapping env var for "
        f"model_id={model.model_id!r}. Set {role_env_key} "
        "or provide a model-specific override."
    )


def run_experiments(
    *,
    plan: ExperimentPlan,
    prompt_template_path: Path,
    output_root: Path,
    evaluation_jsonl: Path,
    max_output_tokens: int,
    timeout_seconds: float,
    dry_run: bool,
    checkpoint_every: int = 25,
) -> dict[str, Any]:
    """Execute configured experiments and write response artifacts."""
    output_dir = output_root / plan.run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    responses_path = output_dir / "responses.jsonl"
    failures_path = output_dir / "failures.jsonl"
    progress_path = output_dir / "progress.json"
    responses_path.touch(exist_ok=True)
    failures_path.touch(exist_ok=True)

    prompt_template = prompt_template_path.read_text(encoding="utf-8")
    _write_manifest(
        output_dir=output_dir,
        plan=plan,
        prompt_template_path=prompt_template_path,
        evaluation_jsonl=evaluation_jsonl,
        max_output_tokens=max_output_tokens,
        timeout_seconds=timeout_seconds,
        dry_run=dry_run,
    )

    total_requests = 0
    successful = 0
    failed = 0
    planned_requests = (
        len(plan.models)
        * len(plan.seeds)
        * len(plan.temperatures)
        * len(plan.tasks)
        * len(plan.examples)
    )

    completed_from_responses = _load_completed_keys_from_responses(
        responses_path,
        run_id=plan.run_id,
    )
    completed_from_progress = _load_progress_state(progress_path, run_id=plan.run_id)
    completed_request_keys = set(completed_from_responses | completed_from_progress)
    completed_requests_at_start = len(completed_request_keys)

    attempted_requests = 0
    skipped_completed_requests = 0
    checkpoint_index = 0

    _write_progress_state(
        progress_path=progress_path,
        run_id=plan.run_id,
        planned_requests=planned_requests,
        completed_request_keys=completed_request_keys,
        attempted_requests=attempted_requests,
        successful_requests=successful,
        failed_requests=failed,
        checkpoint_index=checkpoint_index,
        dry_run=dry_run,
    )

    if dry_run:
        total_requests = 0
    else:
        for model in plan.models:
            provider = _infer_provider(model)
            api_model_name = _resolve_api_model_name(model)
            for seed in plan.seeds:
                for temperature in plan.temperatures:
                    for task in plan.tasks:
                        for example in plan.examples:
                            request_key = _request_key(
                                model_id=model.model_id,
                                task_id=task.task_id,
                                example_id=example.example_id,
                                temperature=temperature,
                                seed=seed,
                            )
                            if request_key in completed_request_keys:
                                skipped_completed_requests += 1
                                continue

                            prompt = _build_prompt(
                                prompt_template=prompt_template,
                                example=example,
                                task=task,
                            )
                            attempted_requests += 1
                            total_requests += 1
                            started = time.perf_counter()
                            try:
                                (
                                    provider_response,
                                    response_text,
                                    in_tokens,
                                    out_tokens,
                                ) = _call_provider(
                                    provider=provider,
                                    model_name=api_model_name,
                                    prompt=prompt,
                                    temperature=temperature,
                                    seed=seed,
                                    timeout_seconds=timeout_seconds,
                                    max_output_tokens=max_output_tokens,
                                )
                                latency_ms = (time.perf_counter() - started) * 1000.0
                                output_json, parse_error = _try_parse_json_output(response_text)
                                confidence = _extract_confidence(output_json)
                                cost = _estimate_cost(
                                    model=model,
                                    input_tokens=in_tokens,
                                    output_tokens=out_tokens,
                                )
                                response_record = {
                                    "run_id": plan.run_id,
                                    "request_key": request_key,
                                    "timestamp_utc": _utc_now(),
                                    "model": model.model_id,
                                    "provider": provider,
                                    "api_model_name": api_model_name,
                                    "prompt_version": plan.prompt_version,
                                    "task_id": task.task_id,
                                    "example_id": example.example_id,
                                    "temperature": temperature,
                                    "seed": seed,
                                    "latency_ms": latency_ms,
                                    "input_tokens": in_tokens,
                                    "output_tokens": out_tokens,
                                    "estimated_cost_usd": cost,
                                    "confidence": confidence,
                                    "raw_json_output": output_json,
                                    "output_parse_error": parse_error,
                                    "raw_response_text": response_text,
                                    "provider_response": provider_response,
                                }
                                _append_jsonl(responses_path, response_record)
                                completed_request_keys.add(request_key)
                                successful += 1
                            except Exception as exc:  # pragma: no cover - runtime API variability
                                latency_ms = (time.perf_counter() - started) * 1000.0
                                failure_record = {
                                    "run_id": plan.run_id,
                                    "request_key": request_key,
                                    "timestamp_utc": _utc_now(),
                                    "model": model.model_id,
                                    "provider": provider,
                                    "api_model_name": api_model_name,
                                    "prompt_version": plan.prompt_version,
                                    "task_id": task.task_id,
                                    "example_id": example.example_id,
                                    "temperature": temperature,
                                    "seed": seed,
                                    "latency_ms": latency_ms,
                                    "error": f"{type(exc).__name__}: {exc}",
                                }
                                _append_jsonl(failures_path, failure_record)
                                failed += 1

                            if checkpoint_every > 0 and (
                                attempted_requests % checkpoint_every == 0
                            ):
                                checkpoint_index += 1
                                _write_progress_state(
                                    progress_path=progress_path,
                                    run_id=plan.run_id,
                                    planned_requests=planned_requests,
                                    completed_request_keys=completed_request_keys,
                                    attempted_requests=attempted_requests,
                                    successful_requests=successful,
                                    failed_requests=failed,
                                    checkpoint_index=checkpoint_index,
                                    dry_run=dry_run,
                                )

    _write_progress_state(
        progress_path=progress_path,
        run_id=plan.run_id,
        planned_requests=planned_requests,
        completed_request_keys=completed_request_keys,
        attempted_requests=attempted_requests,
        successful_requests=successful,
        failed_requests=failed,
        checkpoint_index=checkpoint_index + 1,
        dry_run=dry_run,
    )

    summary = {
        "run_id": plan.run_id,
        "round_id": plan.round_id,
        "created_at": _utc_now(),
        "output_dir": str(output_dir),
        "responses_path": str(responses_path),
        "failures_path": str(failures_path),
        "total_requests": total_requests,
        "attempted_requests": attempted_requests,
        "skipped_completed_requests": skipped_completed_requests,
        "completed_requests_at_start": completed_requests_at_start,
        "completed_requests_total": len(completed_request_keys),
        "remaining_requests": max(0, planned_requests - len(completed_request_keys)),
        "successful_requests": successful,
        "failed_requests": failed,
        "model_count": len(plan.models),
        "task_count": len(plan.tasks),
        "example_count": len(plan.examples),
        "seed_count": len(plan.seeds),
        "temperature_count": len(plan.temperatures),
        "planned_requests": planned_requests,
        "dry_run": dry_run,
        "progress_path": str(progress_path),
    }
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run teacher evaluation experiments from configs.")
    parser.add_argument("--config-root", default="configs/teacher")
    parser.add_argument("--evaluation-jsonl", default="datasets/gold/gold_v1.jsonl")
    parser.add_argument("--round-id", default="round_2_gold100")
    parser.add_argument("--prompt-template", default="teacher_prompts/production_teacher.txt")
    parser.add_argument("--prompt-version", default="production_teacher_v1")
    parser.add_argument("--providers-config", default="configs/providers/providers_v1.json")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--output-root", default="outputs/teacher_runs")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--max-examples", type=int, default=0)
    parser.add_argument("--max-output-tokens", type=int, default=1200)
    parser.add_argument("--timeout-seconds", type=float, default=120.0)
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=25,
        help="Write progress checkpoint after this many attempted requests.",
    )
    parser.add_argument(
        "--temperatures",
        default="0.0",
        help="Comma-separated temperatures.",
    )
    parser.add_argument(
        "--seeds",
        default="",
        help="Optional comma-separated seeds override. Default comes from metrics config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Preflight mode: validate configs and write run manifest only. "
            "No provider calls or synthetic outputs are generated."
        ),
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()
    run_id = args.run_id or _default_run_id()
    temperatures = tuple(
        float(item.strip()) for item in str(args.temperatures).split(",") if item.strip()
    )
    if not temperatures:
        raise ValueError("At least one temperature is required.")

    seeds_override: tuple[int, ...] | None = None
    if str(args.seeds).strip():
        seeds_override = tuple(
            int(item.strip()) for item in str(args.seeds).split(",") if item.strip()
        )
        if not seeds_override:
            raise ValueError("Seed override provided but no valid seeds were parsed.")

    plan = _load_plan(
        config_root=Path(args.config_root),
        evaluation_jsonl=Path(args.evaluation_jsonl),
        round_id=str(args.round_id),
        max_examples=int(args.max_examples),
        prompt_template_path=Path(args.prompt_template),
        prompt_version=str(args.prompt_version),
        run_id=run_id,
        seeds_override=seeds_override,
        temperatures=temperatures,
    )
    required_providers = sorted({_infer_provider(model) for model in plan.models})
    validate_provider_configuration(
        required_providers=required_providers,
        config_path=Path(args.providers_config),
        env_file=Path(args.env_file),
        strict=not bool(args.dry_run),
        load_env=True,
        override_env=False,
    )
    summary = run_experiments(
        plan=plan,
        prompt_template_path=Path(args.prompt_template),
        output_root=Path(args.output_root),
        evaluation_jsonl=Path(args.evaluation_jsonl),
        max_output_tokens=int(args.max_output_tokens),
        timeout_seconds=float(args.timeout_seconds),
        dry_run=bool(args.dry_run),
        checkpoint_every=max(1, int(args.checkpoint_every)),
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
