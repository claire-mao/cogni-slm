"""Local Transformers teacher provider adapter."""

from __future__ import annotations

from typing import Any

from .base import BaseTeacherProvider
from .common import normalize_teacher_output, try_parse_json_output


class LocalTransformersTeacherProvider(BaseTeacherProvider):
    """Teacher provider backed by local Hugging Face Transformers models."""

    def __init__(
        self,
        *,
        model_name: str,
        prompt_template: str | None = None,
        temperature: float = 0.0,
        seed: int | None = None,
        timeout_seconds: float = 120.0,
        max_output_tokens: int = 1200,
        device_map: str = "auto",
        trust_remote_code: bool = True,
    ) -> None:
        super().__init__(
            model_name=model_name,
            prompt_template=prompt_template,
            temperature=temperature,
            seed=seed,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )
        self.device_map = device_map
        self.trust_remote_code = trust_remote_code
        self._pipeline: Any | None = None

    @property
    def provider_name(self) -> str:
        return "local_transformers"

    def _load_pipeline(self) -> Any:
        if self._pipeline is not None:
            return self._pipeline

        try:
            from transformers import pipeline
        except ImportError as exc:  # pragma: no cover - dependency variability
            raise RuntimeError(
                "transformers is required for LocalTransformersTeacherProvider. "
                "Install with: pip install transformers torch"
            ) from exc

        generator = pipeline(
            task="text-generation",
            model=self.model_name,
            device_map=self.device_map,
            trust_remote_code=self.trust_remote_code,
        )
        self._pipeline = generator
        return generator

    def _invoke(self, prompt: str) -> tuple[dict[str, Any], str, int | None, int | None]:
        generator = self._load_pipeline()
        generated = generator(
            prompt,
            max_new_tokens=self.max_output_tokens,
            do_sample=bool(self.temperature > 0),
            temperature=max(self.temperature, 1e-6),
            return_full_text=False,
        )

        text = ""
        if isinstance(generated, list) and generated:
            first = generated[0] if isinstance(generated[0], dict) else {}
            raw = first.get("generated_text")
            if isinstance(raw, str):
                text = raw

        return {"local_generation": generated}, text.strip(), None, None

    def generate(self, example: Any) -> dict[str, Any]:
        """Override to include parsed output in metadata for local runs."""
        prompt = self.build_prompt(example)
        provider_payload, response_text, input_tokens, output_tokens = self._invoke(prompt)

        parsed_output, parse_error = try_parse_json_output(response_text)
        metadata = {
            "provider": self.provider_name,
            "model_name": self.model_name,
            "example_id": getattr(example, "example_id", None),
            "task_id": getattr(example, "task_id", None),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "parse_error": parse_error,
            "raw_response_text": response_text,
            "provider_response": provider_payload,
            "raw_json_output": parsed_output,
        }
        if getattr(example, "metadata", None):
            metadata["example_metadata"] = example.metadata

        return normalize_teacher_output(parsed_output, metadata=metadata)
