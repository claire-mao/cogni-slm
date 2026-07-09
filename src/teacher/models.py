"""Model registry and pricing utilities for teacher benchmarking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    """Token pricing metadata used for cost rollups."""

    input_per_million: float | None
    output_per_million: float | None


SUPPORTED_MODELS: tuple[str, ...] = (
    "gpt-5",
    "o3",
    "claude_opus_4",
    "claude_sonnet_4",
    "gemini_2_5_pro",
    "deepseek_r1",
    "qwen3",
    "llama_4_maverick",
)

MODEL_ALIASES: dict[str, str] = {
    "gpt-5": "gpt-5",
    "gpt5": "gpt-5",
    "o3": "o3",
    "claude_opus_4": "claude_opus_4",
    "claude-opus-4": "claude_opus_4",
    "claude opus 4": "claude_opus_4",
    "claude_opus_4x": "claude_opus_4",
    "claude_sonnet_4": "claude_sonnet_4",
    "claude-sonnet-4": "claude_sonnet_4",
    "claude sonnet 4": "claude_sonnet_4",
    "claude_sonnet_4x": "claude_sonnet_4",
    "gemini_2_5_pro": "gemini_2_5_pro",
    "gemini-2.5-pro": "gemini_2_5_pro",
    "gemini 2.5 pro": "gemini_2_5_pro",
    "deepseek_r1": "deepseek_r1",
    "deepseek-r1": "deepseek_r1",
    "deepseek r1": "deepseek_r1",
    "qwen3": "qwen3",
    "llama_4_maverick": "llama_4_maverick",
    "llama4_maverick": "llama_4_maverick",
    "llama-4-maverick": "llama_4_maverick",
    "llama 4 maverick": "llama_4_maverick",
}

MODEL_PRICING_USD_PER_MILLION: dict[str, ModelPricing] = {
    "gpt-5": ModelPricing(input_per_million=1.25, output_per_million=10.0),
    "o3": ModelPricing(input_per_million=2.0, output_per_million=8.0),
    "claude_opus_4": ModelPricing(input_per_million=15.0, output_per_million=75.0),
    "claude_sonnet_4": ModelPricing(input_per_million=3.0, output_per_million=15.0),
    "gemini_2_5_pro": ModelPricing(input_per_million=1.25, output_per_million=10.0),
    "deepseek_r1": ModelPricing(input_per_million=0.14, output_per_million=0.28),
    "qwen3": ModelPricing(input_per_million=0.287, output_per_million=1.147),
    # Provider-dependent for hosted routes; keep unset for automatic estimation.
    "llama_4_maverick": ModelPricing(input_per_million=None, output_per_million=None),
}


def canonical_model_id(value: str) -> str:
    """Normalize a model id/label to one of SUPPORTED_MODELS."""
    normalized = value.strip().lower().replace("/", "_")
    normalized = " ".join(normalized.split())
    if normalized in MODEL_ALIASES:
        return MODEL_ALIASES[normalized]
    raise ValueError(
        f"Unsupported model id '{value}'. Expected one of: {', '.join(SUPPORTED_MODELS)}"
    )


def estimate_cost_usd(model_id: str, input_tokens: int, output_tokens: int) -> float | None:
    """Estimate call cost using token totals and known pricing tables."""
    pricing = MODEL_PRICING_USD_PER_MILLION.get(model_id)
    if pricing is None:
        return None
    if pricing.input_per_million is None or pricing.output_per_million is None:
        return None

    return (
        (input_tokens / 1_000_000.0) * pricing.input_per_million
        + (output_tokens / 1_000_000.0) * pricing.output_per_million
    )
