"""Reusable local inference runner for Cogni."""

from __future__ import annotations

import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

DEFAULT_MODEL_ID = "Qwen/Qwen3-0.6B"
DEFAULT_PROMPT = (
    "AP Language sample argument: The school board should remove all long-form essays "
    "because students mostly consume short social posts, so essay writing is no longer useful. "
    "Analyze whether this argument is logically sound."
)


def resolve_device() -> str:
    """Select MPS when available, otherwise CPU."""
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def run_once(
    model_id: str,
    prompt: str,
    max_new_tokens: int,
    output_dir: str,
) -> dict[str, str | float]:
    """Load model, run one prompt, and persist response/report outputs."""
    device = resolve_device()
    dtype = torch.float16 if device == "mps" else torch.float32

    load_start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        trust_remote_code=True,
        torch_dtype=dtype,
    )
    model.to(device)
    model.eval()
    load_time = time.perf_counter() - load_start

    messages = [
        {
            "role": "system",
            "content": "You are Cogni, an educational assistant for logical reasoning.",
        },
        {"role": "user", "content": prompt},
    ]
    prompt_text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    encoded = tokenizer(prompt_text, return_tensors="pt")
    encoded = {k: v.to(device) for k, v in encoded.items()}

    infer_start = time.perf_counter()
    with torch.inference_mode():
        output_ids = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    inference_time = time.perf_counter() - infer_start

    generated_ids = output_ids[0][encoded["input_ids"].shape[-1] :]
    response = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    response_path = out_dir / "response.txt"
    report_path = out_dir / "report.md"
    response_path.write_text(response + "\n", encoding="utf-8")
    report_path.write_text(
        "\n".join(
            [
                "# Inference Verification Report",
                "",
                f"- model version: `{model_id}`",
                f"- device used: `{device}`",
                f"- load time (s): `{load_time:.4f}`",
                f"- inference time (s): `{inference_time:.4f}`",
                "",
                "## generated response",
                "",
                response,
                "",
            ]
        ),
        encoding="utf-8",
    )

    return {
        "model_id": model_id,
        "device": device,
        "load_time": load_time,
        "inference_time": inference_time,
        "response": response,
        "report_path": str(report_path),
        "response_path": str(response_path),
    }
