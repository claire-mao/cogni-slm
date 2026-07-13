#!/usr/bin/env python3
"""Resumable direct structured-output labeling for the AP tutor behavior."""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from teacher.providers.common import openai_like_text_and_usage  # noqa: E402
from teacher.providers.http import http_json_post, raise_for_status  # noqa: E402

DEFAULT_BASE_URL = "https://tfy.promptlens.trilogy.com/v1"
DEFAULT_MODEL = "gemini-group/gemini-3.1-pro"
REQUIRED_FIELDS = (
    "argument_summary",
    "assumptions",
    "primary_fallacy",
    "why_this_applies",
    "cross_domain_analogy",
    "transfer_check",
    "reflective_question",
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return rows


def build_prompt(example: dict[str, Any]) -> str:
    return f"""You are an AP English Language logical-fallacy tutor.

Analyze the argument and return exactly one JSON object matching the supplied schema.

Requirements:
1. Summarize the argument.
2. Identify its assumptions.
3. Name exactly one primary fallacy, or say "No clear fallacy".
4. Explain why.
5. Give one analogy from a different domain and map it back.
6. Give one new transfer example and ask the student to classify it without revealing the answer.
7. End with exactly one reflective question.

ARGUMENT:
{example["essay"]}"""


def validate_output(output: Any) -> list[str]:
    if not isinstance(output, dict):
        return ["not_json_object"]
    errors = [f"missing_{field}" for field in REQUIRED_FIELDS if field not in output]
    if not isinstance(output.get("assumptions"), list) or not output.get("assumptions"):
        errors.append("invalid_assumptions")
    analogy = output.get("cross_domain_analogy")
    if not isinstance(analogy, dict) or not analogy.get("analogy") or not analogy.get("mapping"):
        errors.append("invalid_cross_domain_analogy")
    transfer = output.get("transfer_check")
    if (
        not isinstance(transfer, dict)
        or not transfer.get("example")
        or not transfer.get("question")
    ):
        errors.append("invalid_transfer_check")
    reflection = str(output.get("reflective_question", "")).strip()
    if not reflection.endswith("?"):
        errors.append("invalid_reflective_question")
    return sorted(set(errors))


def request_one(
    example: dict[str, Any],
    *,
    base_url: str,
    api_key: str,
    model: str,
    schema: dict[str, Any],
    max_tokens: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": build_prompt(example)}],
        "temperature": 0,
        "max_tokens": max_tokens,
        "reasoning_effort": "low",
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "fallacy_tutor_response",
                "strict": True,
                "schema": schema,
            },
        },
    }
    status, response_json, response_body = http_json_post(
        provider="openai",
        url=f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        payload=payload,
        timeout_seconds=timeout_seconds,
    )
    raise_for_status(
        provider="openai",
        status=status,
        response_json=response_json,
        response_body=response_body,
    )
    content, input_tokens, output_tokens = openai_like_text_and_usage(response_json)
    try:
        output = json.loads(content)
        errors = validate_output(output)
    except Exception as exc:
        output = None
        errors = [f"parse_error:{type(exc).__name__}:{exc}"]
    return {
        "example_id": str(example["example_id"]),
        "valid": not errors,
        "errors": errors,
        "output": output,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        default="datasets/training_candidates/ap_fallacy_production_v1/labeling_input.jsonl",
    )
    parser.add_argument("--output", default="outputs/teacher_runs/direct_gemini_15k.jsonl")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--api-key-env", default="TEACHER_API_KEY")
    parser.add_argument("--schema", default="teacher_prompts/ap_fallacy_behavior_schema.json")
    parser.add_argument("--workers", type=int, default=32)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=2500)
    parser.add_argument("--timeout-seconds", type=float, default=180.0)
    args = parser.parse_args()

    api_key = os.getenv(args.api_key_env, "").strip()
    if not api_key:
        raise SystemExit(f"Missing API key environment variable: {args.api_key_env}")
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    inputs = read_jsonl(Path(args.inputs))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    valid_ids = (
        {str(row.get("example_id")) for row in read_jsonl(output_path) if row.get("valid") is True}
        if output_path.exists()
        else set()
    )
    pending = [row for row in inputs if str(row.get("example_id")) not in valid_ids]
    print(f"Already valid: {len(valid_ids):,}; pending: {len(pending):,}")

    def with_retry(example: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for attempt in range(1, max(1, args.attempts) + 1):
            try:
                result = request_one(
                    example,
                    base_url=args.base_url,
                    api_key=api_key,
                    model=args.model,
                    schema=schema,
                    max_tokens=args.max_tokens,
                    timeout_seconds=args.timeout_seconds,
                )
                result["attempt"] = attempt
                if result["valid"]:
                    return result
            except Exception as exc:
                result = {
                    "example_id": str(example.get("example_id")),
                    "valid": False,
                    "errors": [f"{type(exc).__name__}:{exc}"],
                    "attempt": attempt,
                }
            if attempt < args.attempts:
                time.sleep((2 ** (attempt - 1)) + random.random())
        return result

    started = time.time()
    valid_count = 0
    with output_path.open("a", encoding="utf-8") as handle:
        with ThreadPoolExecutor(max_workers=max(1, args.workers)) as executor:
            futures = [executor.submit(with_retry, row) for row in pending]
            for completed, future in enumerate(as_completed(futures), start=1):
                result = future.result()
                handle.write(json.dumps(result, ensure_ascii=False) + "\n")
                handle.flush()
                valid_count += int(result.get("valid") is True)
                if completed % 100 == 0:
                    rate = completed / max(time.time() - started, 1e-9)
                    eta_hours = (len(pending) - completed) / rate / 3600
                    print(
                        f"Processed {completed:,}/{len(pending):,}; valid={valid_count:,}; "
                        f"success={valid_count / completed:.1%}; eta={eta_hours:.1f}h"
                    )


if __name__ == "__main__":
    main()
