"""Run local teacher-model inference for essays and save outputs to datasets/teacher/."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from datasets import load_from_disk

DEFAULT_MODEL_ID = "Qwen/Qwen3-0.6B"
DEFAULT_TEMPLATE_PATH = "teacher_prompts/local_teacher_inference_template.txt"
DEFAULT_SYSTEM_ROLE_PATH = "teacher_prompts/system_role.txt"


@dataclass(frozen=True)
class InputRecord:
    """One model input example."""

    example_id: str
    split: str
    prompt: str
    essay: str
    score: float


@dataclass(frozen=True)
class OutputRecord:
    """One model output example."""

    id: str
    split: str
    prompt: str
    essay: str
    score: float
    reasoning: str
    feedback: str
    predicted_score: float
    confidence: float
    model_id: str
    generated_at: str


@dataclass(frozen=True)
class FailureRecord:
    """One failed generation event."""

    id: str
    split: str
    error: str
    raw_response: str


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Run local teacher inference pipeline.")
    parser.add_argument(
        "--input-dataset-dir",
        default="datasets/training",
        help="HF dataset directory containing prompt/essay/score splits.",
    )
    parser.add_argument(
        "--input-jsonl",
        default="",
        help=(
            "Optional JSONL input with prompt/essay/score. "
            "If provided, overrides --input-dataset-dir."
        ),
    )
    parser.add_argument(
        "--splits",
        default="train,validation,test",
        help="Comma-separated splits when reading from HF dataset.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/teacher",
        help="Output directory for teacher generations.",
    )
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--template-path", default=DEFAULT_TEMPLATE_PATH)
    parser.add_argument("--system-role-path", default=DEFAULT_SYSTEM_ROLE_PATH)
    parser.add_argument("--max-new-tokens", type=int, default=320)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--max-examples", type=int, default=0)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def parse_score(value: Any) -> float | None:
    """Parse numeric score value."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        value_float = float(value)
        if value_float != value_float or value_float in (float("inf"), float("-inf")):
            return None
        return value_float

    raw = str(value).strip()
    if not raw:
        return None

    try:
        value_float = float(raw)
    except ValueError:
        return None

    if value_float != value_float or value_float in (float("inf"), float("-inf")):
        return None
    return value_float


def normalize_text(value: Any) -> str:
    """Normalize whitespace in text fields."""
    return " ".join(str(value or "").split()).strip()


def resolve_device() -> str:
    """Choose local inference device."""
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_text(path: Path) -> str:
    """Load UTF-8 text file."""
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_inputs_from_hf(
    dataset_dir: Path,
    splits: list[str],
    max_examples: int,
) -> list[InputRecord]:
    """Load prompt/essay/score rows from HF DatasetDict on disk."""
    dataset = load_from_disk(str(dataset_dir))
    records: list[InputRecord] = []

    for split in splits:
        if split not in dataset:
            continue

        for idx, row in enumerate(dataset[split]):
            prompt = normalize_text(row.get("prompt"))
            essay = normalize_text(row.get("essay"))
            score = parse_score(row.get("score"))

            if not prompt or not essay or score is None:
                continue

            records.append(
                InputRecord(
                    example_id=f"{split}:{idx:07d}",
                    split=split,
                    prompt=prompt,
                    essay=essay,
                    score=score,
                )
            )

            if max_examples > 0 and len(records) >= max_examples:
                return records

    return records


def load_inputs_from_jsonl(input_jsonl: Path, max_examples: int) -> list[InputRecord]:
    """Load prompt/essay/score rows from JSONL."""
    if not input_jsonl.exists():
        raise FileNotFoundError(f"Input JSONL not found: {input_jsonl}")

    records: list[InputRecord] = []
    with input_jsonl.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue

            payload = json.loads(raw)
            if not isinstance(payload, dict):
                continue

            prompt = normalize_text(payload.get("prompt"))
            essay = normalize_text(payload.get("essay"))
            score = parse_score(payload.get("score"))
            split = normalize_text(payload.get("split")) or "unknown"
            row_id = normalize_text(payload.get("id")) or f"jsonl:{idx:07d}"

            if not prompt or not essay or score is None:
                continue

            records.append(
                InputRecord(
                    example_id=row_id,
                    split=split,
                    prompt=prompt,
                    essay=essay,
                    score=score,
                )
            )

            if max_examples > 0 and len(records) >= max_examples:
                return records

    return records


def render_template(template: str, record: InputRecord) -> str:
    """Render user prompt template with input record values."""
    return (
        template.replace("{{prompt}}", record.prompt)
        .replace("{{essay}}", record.essay)
        .replace("{{score}}", f"{record.score:.4f}")
    )


def extract_json_object(text: str) -> str:
    """Extract the first top-level JSON object substring from a text blob."""
    start = text.find("{")
    if start < 0:
        raise ValueError("No JSON object start found in model response.")

    depth = 0
    in_string = False
    escaped = False

    for idx in range(start, len(text)):
        ch = text[idx]

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
                return text[start : idx + 1]

    raise ValueError("No complete JSON object found in model response.")


def parse_model_payload(raw_response: str) -> tuple[str, str, float, float]:
    """Parse model JSON output and return required output fields."""
    payload_text = extract_json_object(raw_response)
    payload = json.loads(payload_text)
    if not isinstance(payload, dict):
        raise ValueError("Model payload is not a JSON object.")

    reasoning = normalize_text(payload.get("reasoning"))
    feedback_value = payload.get("feedback")
    if isinstance(feedback_value, str):
        feedback = normalize_text(feedback_value)
    else:
        feedback = json.dumps(feedback_value, ensure_ascii=False)

    predicted_score = parse_score(payload.get("predicted_score"))
    confidence = parse_score(payload.get("confidence"))

    if not reasoning:
        raise ValueError("Missing or empty `reasoning` in model output.")
    if not feedback:
        raise ValueError("Missing or empty `feedback` in model output.")
    if predicted_score is None:
        raise ValueError("Missing or invalid `predicted_score` in model output.")
    if confidence is None:
        raise ValueError("Missing or invalid `confidence` in model output.")

    if confidence > 1.0:
        confidence = confidence / 100.0
    confidence = max(0.0, min(1.0, confidence))

    return reasoning, feedback, predicted_score, confidence


def load_existing_ids(predictions_path: Path) -> set[str]:
    """Load previously generated ids for resume mode."""
    ids: set[str] = set()
    if not predictions_path.exists():
        return ids

    with predictions_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            raw = line.strip()
            if not raw:
                continue
            payload = json.loads(raw)
            if isinstance(payload, dict):
                row_id = normalize_text(payload.get("id"))
                if row_id:
                    ids.add(row_id)
    return ids


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    """Append one JSON row to JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def main() -> None:
    """Run local teacher inference pipeline."""
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    predictions_path = output_dir / "predictions.jsonl"
    failures_path = output_dir / "failures.jsonl"
    summary_path = output_dir / "summary.json"

    template = load_text(Path(args.template_path))
    system_role = load_text(Path(args.system_role_path))

    split_list = [item.strip() for item in args.splits.split(",") if item.strip()]

    if args.input_jsonl:
        inputs = load_inputs_from_jsonl(Path(args.input_jsonl), max_examples=args.max_examples)
        input_source = args.input_jsonl
    else:
        inputs = load_inputs_from_hf(
            dataset_dir=Path(args.input_dataset_dir),
            splits=split_list,
            max_examples=args.max_examples,
        )
        input_source = args.input_dataset_dir

    if not inputs:
        raise ValueError("No valid input records found with prompt/essay/score fields.")

    processed = 0
    skipped = 0
    failed = 0
    total_inference_seconds = 0.0

    existing_ids = load_existing_ids(predictions_path) if args.resume else set()

    # Enforce offline/local-only generation.
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

    device = resolve_device()
    dtype = torch.float16 if device == "mps" else torch.float32

    load_start = time.perf_counter()
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            args.model_id,
            trust_remote_code=True,
            local_files_only=True,
        )
        if tokenizer.pad_token_id is None:
            tokenizer.pad_token = tokenizer.eos_token

        model = AutoModelForCausalLM.from_pretrained(
            args.model_id,
            trust_remote_code=True,
            local_files_only=True,
            torch_dtype=dtype,
        )
    except Exception as exc:  # pragma: no cover - runtime model availability varies
        raise RuntimeError(
            "Failed to load local model artifacts for run_teacher_inference. "
            "Ensure model files are available locally (offline mode is enabled) "
            f"for model_id='{args.model_id}'. Original error: {type(exc).__name__}: {exc}"
        ) from exc

    model.to(device)
    model.eval()
    load_seconds = time.perf_counter() - load_start

    for record in inputs:
        if args.resume and record.example_id in existing_ids:
            skipped += 1
            continue

        prompt_text = render_template(template, record)

        try:
            messages = [
                {"role": "system", "content": system_role},
                {"role": "user", "content": prompt_text},
            ]

            rendered_chat = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
            encoded = tokenizer(rendered_chat, return_tensors="pt")
            encoded = {name: value.to(device) for name, value in encoded.items()}

            infer_start = time.perf_counter()
            with torch.inference_mode():
                output_ids = model.generate(
                    **encoded,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=args.temperature > 0.0,
                    temperature=max(args.temperature, 1e-6),
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
            inference_seconds = time.perf_counter() - infer_start

            generated_ids = output_ids[0][encoded["input_ids"].shape[-1] :]
            raw_response = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
            reasoning, feedback, predicted_score, confidence = parse_model_payload(raw_response)

            output_record = OutputRecord(
                id=record.example_id,
                split=record.split,
                prompt=record.prompt,
                essay=record.essay,
                score=record.score,
                reasoning=reasoning,
                feedback=feedback,
                predicted_score=predicted_score,
                confidence=confidence,
                model_id=args.model_id,
                generated_at=datetime.now(timezone.utc).isoformat(),
            )
            append_jsonl(predictions_path, output_record.__dict__)
            processed += 1
            total_inference_seconds += inference_seconds
        except Exception as exc:  # pragma: no cover - runtime/provider errors
            failure = FailureRecord(
                id=record.example_id,
                split=record.split,
                error=f"{type(exc).__name__}: {exc}",
                raw_response="",
            )
            append_jsonl(failures_path, failure.__dict__)
            failed += 1

    summary = {
        "input_source": input_source,
        "output_dir": str(output_dir),
        "model_id": args.model_id,
        "device": device,
        "template_path": args.template_path,
        "system_role_path": args.system_role_path,
        "total_inputs": len(inputs),
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "load_seconds": load_seconds,
        "total_inference_seconds": total_inference_seconds,
        "predictions_path": str(predictions_path),
        "failures_path": str(failures_path),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
