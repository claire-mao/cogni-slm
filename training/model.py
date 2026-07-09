"""Model and tokenizer builders for Unsloth QLoRA."""

from __future__ import annotations

from typing import Any

from .config import PipelineConfig


def load_model_and_tokenizer(config: PipelineConfig) -> tuple[Any, Any]:
    """Load base model/tokenizer and attach LoRA adapters via Unsloth."""
    try:
        from unsloth import FastLanguageModel
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Unsloth is required for this pipeline. Install with: "
            "pip install 'unsloth[colab-new]' trl transformers peft bitsandbytes accelerate"
        ) from exc

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config.model_id,
        max_seq_length=config.qlora.max_seq_length,
        dtype=None,
        load_in_4bit=config.qlora.load_in_4bit,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=config.qlora.lora_r,
        target_modules=config.qlora.target_modules,
        lora_alpha=config.qlora.lora_alpha,
        lora_dropout=config.qlora.lora_dropout,
        bias=config.qlora.bias,
        use_gradient_checkpointing=config.qlora.use_gradient_checkpointing,
        random_state=config.qlora.random_state,
    )

    return model, tokenizer
