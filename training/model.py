"""Model and tokenizer builders for QLoRA/LoRA training.

Primary path uses Unsloth when accelerator runtime is available.
Fallback path uses Transformers + PEFT so local CPU-only environments can still
run minimal training and produce adapter artifacts.
"""

from __future__ import annotations

import os
from typing import Any

from .config import PipelineConfig


def _offline_mode_enabled() -> bool:
    raw = os.getenv("HF_HUB_OFFLINE") or os.getenv("TRANSFORMERS_OFFLINE")
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}


def _accelerator_available() -> bool:
    try:
        import torch
    except Exception:
        return False
    if torch.cuda.is_available():
        return True
    return bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())


def _load_with_unsloth(config: PipelineConfig) -> tuple[Any, Any]:
    from unsloth import FastLanguageModel

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


def _load_with_transformers_peft(config: PipelineConfig) -> tuple[Any, Any]:
    try:
        import torch
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "Fallback training requires transformers + peft. Install with:\n"
            "pip install transformers peft trl datasets accelerate"
        ) from exc

    offline = _offline_mode_enabled()
    common_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if offline:
        common_kwargs["local_files_only"] = True

    tokenizer = AutoTokenizer.from_pretrained(config.model_id, **common_kwargs)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        config.model_id,
        torch_dtype=torch.float32,
        **common_kwargs,
    )

    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.qlora.lora_r,
        lora_alpha=config.qlora.lora_alpha,
        lora_dropout=config.qlora.lora_dropout,
        target_modules=list(config.qlora.target_modules),
        bias=config.qlora.bias,
    )
    model = get_peft_model(model, peft_config)
    return model, tokenizer


def load_model_and_tokenizer(config: PipelineConfig) -> tuple[Any, Any]:
    """Load base model/tokenizer and attach LoRA adapters.

    Uses Unsloth when accelerator runtime is available; otherwise falls back to
    Transformers + PEFT for CPU-safe execution.
    """
    if _accelerator_available():
        try:
            return _load_with_unsloth(config)
        except Exception:
            # Fall back to a CPU-safe PEFT path if Unsloth runtime is unavailable.
            return _load_with_transformers_peft(config)
    return _load_with_transformers_peft(config)
