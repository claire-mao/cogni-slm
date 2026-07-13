#!/usr/bin/env python3
"""Generate AP tutor held-out predictions for one base or tuned causal LM."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

SYSTEM_PROMPT = (
    "You are an AP English Language logical-fallacy tutor. Follow the required "
    "seven-section instructional sequence exactly: Argument Summary, Assumptions, "
    "Primary Fallacy, Why This Applies, Cross-Domain Analogy, Transfer Check, and "
    "Reflective Question."
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--benchmark", default="datasets/eval/heldout_benchmark_public_v1.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--max-examples", type=int, default=0)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument("--load-in-4bit", action="store_true")
    args = parser.parse_args()

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    except ImportError as exc:
        raise SystemExit("Install torch, transformers, accelerate, and bitsandbytes") from exc

    rows = read_jsonl(Path(args.benchmark))
    if args.max_examples > 0:
        rows = rows[: args.max_examples]
    tokenizer = AutoTokenizer.from_pretrained(args.model, trust_remote_code=True)
    quantization = (
        BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.bfloat16)
        if args.load_in_4bit
        else None
    )
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        trust_remote_code=True,
        device_map="auto",
        torch_dtype="auto",
        quantization_config=quantization,
    )
    model.eval()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as handle:
        for index, row in enumerate(rows, start=1):
            example_id = str(row.get("example_id") or f"example-{index:06d}")
            argument = str(row.get("argument_text") or row.get("essay") or "").strip()
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": argument},
            ]
            try:
                prompt = tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                    enable_thinking=False,
                )
            except TypeError:
                prompt = tokenizer.apply_chat_template(
                    messages, tokenize=False, add_generation_prompt=True
                )
            encoded = tokenizer(prompt, return_tensors="pt").to(model.device)
            with torch.inference_mode():
                generated = model.generate(
                    **encoded,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )
            response_ids = generated[0, encoded["input_ids"].shape[1] :]
            response = tokenizer.decode(response_ids, skip_special_tokens=True).strip()
            handle.write(
                json.dumps(
                    {
                        "run_id": "ap-heldout",
                        "model_id": args.model,
                        "example_id": example_id,
                        "response": response,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            handle.flush()
            if index % 10 == 0:
                print(f"Generated {index}/{len(rows)}")


if __name__ == "__main__":
    main()
