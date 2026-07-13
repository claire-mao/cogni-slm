"""Local model execution and output parsing for comparison harness."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from typing import Any

try:
    from .harness_common import parse_finite_float
    from .harness_data import EvalRecord
except ImportError:  # pragma: no cover - script-mode import fallback
    from harness_common import parse_finite_float
    from harness_data import EvalRecord


@dataclass(frozen=True)
class ParsedModelOutput:
    """Parsed model output contract."""

    reasoning: str
    feedback: str
    predicted_score: float | None
    confidence: float | None
    raw_response: str
    parse_error: str | None = None


class LocalModelRunner:
    """Local text-generation runner with optional dry-run mode."""

    _SCORE_KEYS = ("predicted_score", "score_prediction", "score")
    _CONFIDENCE_KEYS = ("confidence", "score_confidence", "confidence_score")

    def __init__(
        self,
        *,
        model_id: str,
        system_role: str,
        prompt_template: str,
        max_new_tokens: int,
        temperature: float,
        local_files_only: bool,
        dry_run: bool,
    ) -> None:
        self.model_id = model_id
        self.system_role = system_role
        self.prompt_template = prompt_template
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.local_files_only = local_files_only
        self.dry_run = dry_run

        self._tokenizer: Any = None
        self._model: Any = None
        self._device = "cpu"

        if not self.dry_run:
            self._load_model()

    def _load_model(self) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        if self.local_files_only:
            os.environ.setdefault("HF_HUB_OFFLINE", "1")
            os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

        if torch.backends.mps.is_available():
            device = "mps"
            dtype = torch.float16
        else:
            device = "cpu"
            dtype = torch.float32

        tokenizer = AutoTokenizer.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            local_files_only=self.local_files_only,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            local_files_only=self.local_files_only,
            torch_dtype=dtype,
        )
        model.to(device)
        model.eval()

        self._tokenizer = tokenizer
        self._model = model
        self._device = device

    def _render_prompt(self, record: EvalRecord) -> str:
        body = (
            self.prompt_template.replace("{{prompt}}", record.prompt)
            .replace("{{essay}}", record.essay)
            .replace("{{score}}", f"{record.score:.4f}")
        )
        # Qwen reasoning models often emit `<think>` blocks unless explicitly disabled.
        # Prefixing with `/no_think` improves JSON output reliability.
        return "/no_think\n" + body

    def _simulate(self, record: EvalRecord) -> ParsedModelOutput:
        key = f"{self.model_id}::{record.example_id}".encode()
        value = int(hashlib.sha256(key).hexdigest()[:8], 16)

        offset = ((value % 9) - 4) * 0.25
        predicted = max(0.0, record.score + offset)
        confidence = 0.55 + ((value % 40) / 100.0)
        confidence = min(0.99, max(0.0, confidence))

        return ParsedModelOutput(
            reasoning="Dry-run reasoning for harness validation.",
            feedback="Add clearer commentary linking evidence back to your claim.",
            predicted_score=predicted,
            confidence=confidence,
            raw_response="",
            parse_error=None,
        )

    @staticmethod
    def _extract_json_object(text: str) -> str:
        start = text.find("{")
        if start < 0:
            raise ValueError("No JSON object found in model response.")

        depth = 0
        in_string = False
        escaped = False

        for idx in range(start, len(text)):
            char = text[idx]

            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]

        raise ValueError("No complete JSON object in model response.")

    @staticmethod
    def _extract_json_payload(raw_response: str) -> dict[str, Any]:
        stripped = raw_response.strip()

        try:
            payload = json.loads(stripped)
            if isinstance(payload, dict):
                return payload
        except Exception:
            pass

        fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_response, flags=re.DOTALL)
        if fence_match:
            payload = json.loads(fence_match.group(1))
            if isinstance(payload, dict):
                return payload
            raise ValueError("Decoded fenced payload is not an object.")

        payload_text = LocalModelRunner._extract_json_object(raw_response)
        payload = json.loads(payload_text)
        if isinstance(payload, dict):
            return payload
        raise ValueError("Decoded payload is not an object.")

    def _parse_response(self, raw_response: str) -> ParsedModelOutput:
        try:
            payload = self._extract_json_payload(raw_response)

            reasoning = " ".join(str(payload.get("reasoning", "")).split()).strip()
            feedback = payload.get("feedback", "")
            feedback_text = (
                " ".join(str(feedback).split()).strip()
                if isinstance(feedback, str)
                else json.dumps(feedback, ensure_ascii=False)
            )

            predicted_score = None
            for key in self._SCORE_KEYS:
                predicted_score = parse_finite_float(payload.get(key))
                if predicted_score is not None:
                    break

            confidence = None
            for key in self._CONFIDENCE_KEYS:
                confidence = parse_finite_float(payload.get(key))
                if confidence is not None:
                    break

            if confidence is not None and confidence > 1.0:
                confidence = max(0.0, min(1.0, confidence / 100.0))

            return ParsedModelOutput(
                reasoning=reasoning,
                feedback=feedback_text,
                predicted_score=predicted_score,
                confidence=confidence,
                raw_response=raw_response,
                parse_error=None,
            )
        except Exception as exc:
            return ParsedModelOutput(
                reasoning="",
                feedback="",
                predicted_score=None,
                confidence=None,
                raw_response=raw_response,
                parse_error=f"{type(exc).__name__}: {exc}",
            )

    def generate(self, record: EvalRecord) -> ParsedModelOutput:
        if self.dry_run:
            return self._simulate(record)

        import torch

        assert self._tokenizer is not None
        assert self._model is not None

        user_prompt = self._render_prompt(record)
        messages = [
            {"role": "system", "content": self.system_role},
            {"role": "user", "content": user_prompt},
        ]

        prompt_text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        encoded = self._tokenizer(prompt_text, return_tensors="pt")
        encoded = {key: value.to(self._device) for key, value in encoded.items()}

        with torch.inference_mode():
            generated = self._model.generate(
                **encoded,
                max_new_tokens=self.max_new_tokens,
                do_sample=self.temperature > 0.0,
                temperature=max(self.temperature, 1e-6),
                pad_token_id=self._tokenizer.pad_token_id,
                eos_token_id=self._tokenizer.eos_token_id,
            )

        generated_ids = generated[0][encoded["input_ids"].shape[-1] :]
        raw_response = self._tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
        return self._parse_response(raw_response)
