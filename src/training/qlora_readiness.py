"""Readiness checks for the first QLoRA training run.

This script verifies local prerequisites and attempts a single forward/backward
pass without launching full training.
"""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_BASE_CONFIG = Path("configs/training/qlora_default.json")
DEFAULT_PHASE1_CONFIG = Path("configs/training/experiments/qlora_phase1_ofat_v1.json")
DEFAULT_DATASET_ROOT = Path("datasets/sft")
DEFAULT_OUTPUT_ROOT = Path("outputs/training_experiments")
DEFAULT_PLAN_ID = "readiness_dry_run"
DEFAULT_RUN_ID = "p1_baseline"
DEFAULT_REPORT_MD = Path("docs/reports/qlora_first_run_readiness.md")
DEFAULT_REPORT_JSON = Path("docs/reports/qlora_first_run_readiness.json")

DEFAULT_BATCH_PROFILE_MAP: dict[str, dict[str, int]] = {
    "bsz16": {
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,
        "per_device_eval_batch_size": 2,
        "effective_batch_size": 16,
    },
    "bsz32": {
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 8,
        "per_device_eval_batch_size": 4,
        "effective_batch_size": 32,
    },
    "bsz64": {
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 16,
        "per_device_eval_batch_size": 4,
        "effective_batch_size": 64,
    },
}

REQUIRED_LORA_TARGET_MODULES = {
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
}

KNOWN_OPTIMIZERS = {
    "adamw_torch",
    "adamw_torch_fused",
    "adamw_hf",
    "adamw_bnb_8bit",
    "paged_adamw_8bit",
    "adafactor",
    "sgd",
}


@dataclass
class CheckResult:
    """One readiness check result."""

    key: str
    label: str
    status: str
    ok: bool
    details: str
    data: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value is None or isinstance(value, bool):
        return default
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if parsed != parsed or parsed in (float("inf"), float("-inf")):
        return default
    return parsed


def _status(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def _resolve_first_run(
    *,
    base_config_path: Path,
    phase1_config_path: Path,
    run_id: str,
    output_root: Path,
    plan_id: str,
) -> dict[str, Any]:
    base_payload = _read_json(base_config_path)
    phase_payload = _read_json(phase1_config_path)

    baseline = phase_payload.get("baseline")
    if not isinstance(baseline, dict):
        raise ValueError(f"Missing baseline object in {phase1_config_path}")

    selected_run: dict[str, Any] | None = None
    runs = phase_payload.get("runs")
    if isinstance(runs, list):
        for row in runs:
            if isinstance(row, dict) and str(row.get("run_id")) == run_id:
                selected_run = row
                break
    if selected_run is None:
        raise ValueError(f"Run id '{run_id}' not found in {phase1_config_path}")

    params = copy.deepcopy(baseline)
    overrides = selected_run.get("overrides")
    if isinstance(overrides, dict):
        params.update(overrides)

    qlora = copy.deepcopy(base_payload.get("qlora", {}))
    trainer = copy.deepcopy(base_payload.get("trainer", {}))
    batch_profile_id = str(params.get("batch_profile_id") or "").strip()
    if batch_profile_id:
        profile = DEFAULT_BATCH_PROFILE_MAP.get(batch_profile_id)
        if profile:
            trainer["per_device_train_batch_size"] = profile["per_device_train_batch_size"]
            trainer["per_device_eval_batch_size"] = profile["per_device_eval_batch_size"]
            trainer["gradient_accumulation_steps"] = profile["gradient_accumulation_steps"]

    lora_rank = params.get("lora_rank", params.get("lora_r"))
    if lora_rank is not None:
        qlora["lora_r"] = _safe_int(lora_rank, 16)

    lora_alpha = params.get("lora_alpha")
    if lora_alpha is not None:
        qlora["lora_alpha"] = _safe_int(lora_alpha, 16)

    max_seq_length = params.get("max_seq_length")
    if max_seq_length is not None:
        qlora["max_seq_length"] = _safe_int(max_seq_length, 2048)

    learning_rate = params.get("learning_rate")
    if learning_rate is not None:
        trainer["learning_rate"] = float(learning_rate)

    warmup_ratio = params.get("warmup_ratio")
    if warmup_ratio is not None:
        trainer["warmup_ratio"] = float(warmup_ratio)

    epochs = params.get("num_train_epochs", params.get("epochs"))
    if epochs is not None:
        trainer["num_train_epochs"] = float(epochs)

    optimizer = str(params.get("optimizer") or "adamw_torch")
    model_id = str(params.get("model_id") or base_payload.get("model_id") or "").strip()
    if not model_id:
        model_id = "Qwen/Qwen3-1.7B-Instruct"

    run_dir = output_root / plan_id / f"00001_{run_id}"
    checkpoints_dir = run_dir / "checkpoints"

    return {
        "run_id": run_id,
        "phase_id": str(phase_payload.get("phase_id") or "phase1_ofat_screening"),
        "model_id": model_id,
        "params": params,
        "qlora": qlora,
        "trainer": trainer,
        "optimizer": optimizer,
        "packing": bool(params.get("packing", False)),
        "base_output_dir": Path(str(trainer.get("output_dir") or "models/unsloth_qlora")),
        "base_checkpoint_dir": Path(
            str(base_payload.get("checkpoint_dir") or "models/unsloth_qlora/checkpoints")
        ),
        "run_dir": run_dir,
        "checkpoints_dir": checkpoints_dir,
    }


def _find_split_file(dataset_root: Path, split_name: str) -> Path | None:
    candidates = [
        dataset_root / split_name / "data.jsonl",
        dataset_root / "formats" / "huggingface" / f"{split_name}.jsonl",
        dataset_root / f"{split_name}.jsonl",
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def _normalize_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _format_score(value: Any) -> str:
    parsed = _safe_float(value)
    if parsed is None:
        return "unknown"
    return f"{parsed:.4f}"


def _build_text_from_row(row: dict[str, Any]) -> str:
    text = row.get("text")
    if isinstance(text, str) and text.strip():
        return text.strip()

    instruction = _normalize_text(row.get("instruction"))
    input_text = _normalize_text(row.get("input"))
    output_text = _normalize_text(row.get("output"))
    if instruction or input_text or output_text:
        return (
            f"Instruction:\n{instruction}\n\nInput:\n{input_text}\n\nOutput:\n{output_text}"
        ).strip()

    prompt = _normalize_text(row.get("prompt"))
    essay = _normalize_text(row.get("essay"))
    if prompt and essay:
        return (
            "You are an AP Language instructor. Evaluate the argument quality and score.\n\n"
            f"Prompt:\n{prompt}\n\n"
            f"Essay:\n{essay}\n\n"
            "Target:\n"
            f"Final score: {_format_score(row.get('score'))}\n"
        )

    messages = row.get("messages")
    if isinstance(messages, list):
        blocks: list[str] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            role = _normalize_text(message.get("role") or message.get("from"))
            content = _normalize_text(message.get("content") or message.get("value"))
            if role and content:
                blocks.append(f"<{role}>\n{content}")
        if blocks:
            return "\n\n".join(blocks)
    return ""


def _check_dataset_format(dataset_root: Path) -> tuple[CheckResult, str]:
    split_path = _find_split_file(dataset_root, "train")
    if split_path is None:
        return (
            CheckResult(
                key="dataset_formatting",
                label="Dataset formatting",
                status="FAIL",
                ok=False,
                details=f"Train split not found under {dataset_root}",
                data={"dataset_root": str(dataset_root)},
            ),
            "",
        )

    total_rows = 0
    valid_rows = 0
    first_text = ""
    with split_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            raw = line.strip()
            if not raw:
                continue
            total_rows += 1
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(row, dict):
                continue
            text = _build_text_from_row(row)
            if text:
                valid_rows += 1
                if not first_text:
                    first_text = text
            if line_number >= 250000:
                break

    ok = total_rows > 0 and valid_rows > 0
    details = (
        f"train_rows={total_rows}, valid_rows={valid_rows}, split_file={split_path}"
        if ok
        else f"No valid SFT rows found in {split_path}"
    )
    return (
        CheckResult(
            key="dataset_formatting",
            label="Dataset formatting",
            status=_status(ok),
            ok=ok,
            details=details,
            data={
                "dataset_root": str(dataset_root),
                "split_file": str(split_path),
                "train_rows": total_rows,
                "valid_rows": valid_rows,
            },
        ),
        first_text,
    )


def _check_unsloth_installation() -> tuple[CheckResult, CheckResult]:
    spec = importlib.util.find_spec("unsloth")
    installed = spec is not None
    install_result = CheckResult(
        key="unsloth_installation",
        label="Unsloth installation",
        status=_status(installed),
        ok=installed,
        details="Package location found."
        if installed
        else "Package not found in current Python env.",
        data={"module_found": installed},
    )

    runtime_ok = False
    version = ""
    error = ""
    if installed:
        code = (
            "import json\n"
            "import sys\n"
            "result = {'ok': False, 'version': '', 'error': ''}\n"
            "try:\n"
            "    import unsloth\n"
            "    result['ok'] = True\n"
            "    result['version'] = str(getattr(unsloth, '__version__', 'unknown'))\n"
            "except Exception as exc:\n"
            "    result['error'] = f'{type(exc).__name__}: {exc}'\n"
            "print(json.dumps(result, ensure_ascii=False))\n"
        )
        process = subprocess.run(
            [sys.executable, "-c", code],
            text=True,
            capture_output=True,
        )
        if process.returncode == 0:
            try:
                payload = json.loads(process.stdout.strip() or "{}")
            except json.JSONDecodeError:
                payload = {}
            runtime_ok = bool(payload.get("ok"))
            version = str(payload.get("version") or "")
            error = str(payload.get("error") or "")
        else:
            tail = (process.stderr or process.stdout or "").strip()
            if len(tail) > 500:
                tail = tail[-500:]
            error = (
                f"subprocess_exit={process.returncode}: {tail}"
                if tail
                else (f"subprocess_exit={process.returncode}")
            )

    runtime_result = CheckResult(
        key="unsloth_runtime_import",
        label="Unsloth runtime import",
        status=_status(runtime_ok),
        ok=runtime_ok,
        details=(
            f"Imported successfully (version={version})."
            if runtime_ok
            else (error or "Failed to import unsloth.")
        ),
        data={"runtime_import_ok": runtime_ok, "version": version, "error": error},
    )
    return install_result, runtime_result


def _check_cuda_gpu() -> tuple[CheckResult, bool]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover
        return (
            CheckResult(
                key="cuda_gpu_availability",
                label="CUDA/GPU availability",
                status="FAIL",
                ok=False,
                details=f"torch import failed: {type(exc).__name__}: {exc}",
                data={},
            ),
            False,
        )

    cuda_available = bool(torch.cuda.is_available())
    device_count = int(torch.cuda.device_count()) if cuda_available else 0
    devices: list[dict[str, Any]] = []
    if cuda_available:
        for index in range(device_count):
            capability = torch.cuda.get_device_capability(index)
            devices.append(
                {
                    "index": index,
                    "name": str(torch.cuda.get_device_name(index)),
                    "capability": f"{capability[0]}.{capability[1]}",
                }
            )

    ok = cuda_available and device_count > 0
    details = (
        f"cuda_available={cuda_available}, device_count={device_count}"
        if ok
        else (
            "No CUDA accelerator detected "
            f"(cuda_available={cuda_available}, device_count={device_count})."
        )
    )
    return (
        CheckResult(
            key="cuda_gpu_availability",
            label="CUDA/GPU availability",
            status=_status(ok),
            ok=ok,
            details=details,
            data={
                "torch_version": getattr(torch, "__version__", "unknown"),
                "cuda_available": cuda_available,
                "device_count": device_count,
                "devices": devices,
            },
        ),
        ok,
    )


def _check_model_and_tokenizer(
    *,
    model_id: str,
    local_only: bool,
) -> tuple[CheckResult, CheckResult]:
    try:
        from transformers import AutoConfig, AutoTokenizer
    except Exception as exc:  # pragma: no cover
        fail = CheckResult(
            key="base_model_download",
            label="Base model download",
            status="FAIL",
            ok=False,
            details=f"transformers import failed: {type(exc).__name__}: {exc}",
            data={"model_id": model_id},
        )
        tok_fail = CheckResult(
            key="tokenizer",
            label="Tokenizer",
            status="FAIL",
            ok=False,
            details=f"transformers import failed: {type(exc).__name__}: {exc}",
            data={"model_id": model_id},
        )
        return fail, tok_fail

    config_ok = False
    config_error = ""
    if model_id:
        try:
            AutoConfig.from_pretrained(model_id, local_files_only=local_only)
            config_ok = True
        except Exception as exc:
            config_error = f"{type(exc).__name__}: {exc}"

    model_result = CheckResult(
        key="base_model_download",
        label="Base model download",
        status=_status(config_ok),
        ok=config_ok,
        details=(
            "Model files are present locally."
            if config_ok
            else ("Model is not available in local cache." if config_error == "" else config_error)
        ),
        data={"model_id": model_id, "local_files_only": local_only, "error": config_error},
    )

    tokenizer_ok = False
    tokenizer_error = ""
    tokenizer_type = ""
    if model_id:
        try:
            tokenizer = AutoTokenizer.from_pretrained(model_id, local_files_only=local_only)
            tokenizer_ok = tokenizer is not None
            tokenizer_type = tokenizer.__class__.__name__ if tokenizer is not None else ""
        except Exception as exc:
            tokenizer_error = f"{type(exc).__name__}: {exc}"

    tokenizer_result = CheckResult(
        key="tokenizer",
        label="Tokenizer",
        status=_status(tokenizer_ok),
        ok=tokenizer_ok,
        details=(
            f"Tokenizer loaded ({tokenizer_type})."
            if tokenizer_ok
            else (tokenizer_error or "Tokenizer failed to load.")
        ),
        data={
            "model_id": model_id,
            "tokenizer_type": tokenizer_type,
            "local_files_only": local_only,
            "error": tokenizer_error,
        },
    )

    return model_result, tokenizer_result


def _check_lora_config(qlora: dict[str, Any]) -> CheckResult:
    lora_r = _safe_int(qlora.get("lora_r"), 0)
    lora_alpha = _safe_int(qlora.get("lora_alpha"), 0)
    lora_dropout = float(qlora.get("lora_dropout", 0.0))
    target_modules = qlora.get("target_modules", [])
    target_set = set(target_modules) if isinstance(target_modules, list) else set()
    missing_targets = sorted(REQUIRED_LORA_TARGET_MODULES - target_set)
    ok = lora_r > 0 and lora_alpha > 0 and lora_dropout >= 0.0 and not missing_targets
    details = (
        f"lora_r={lora_r}, lora_alpha={lora_alpha}, target_modules={len(target_set)}"
        if ok
        else (
            f"Invalid LoRA config. missing_targets={missing_targets}, "
            f"lora_r={lora_r}, lora_alpha={lora_alpha}"
        )
    )
    return CheckResult(
        key="lora_configuration",
        label="LoRA configuration",
        status=_status(ok),
        ok=ok,
        details=details,
        data={
            "lora_r": lora_r,
            "lora_alpha": lora_alpha,
            "lora_dropout": lora_dropout,
            "target_modules": sorted(target_set),
            "missing_targets": missing_targets,
        },
    )


def _check_qlora_config(qlora: dict[str, Any]) -> CheckResult:
    max_seq_length = _safe_int(qlora.get("max_seq_length"), 0)
    load_in_4bit = bool(qlora.get("load_in_4bit", False))
    gradient_checkpointing = qlora.get("use_gradient_checkpointing")
    bias = str(qlora.get("bias", ""))
    ok = (
        max_seq_length > 0
        and load_in_4bit
        and bool(gradient_checkpointing)
        and bias in {"none", "all", "lora_only"}
    )
    details = (
        f"max_seq_length={max_seq_length}, load_in_4bit={load_in_4bit}, "
        f"use_gradient_checkpointing={gradient_checkpointing}, bias={bias}"
        if ok
        else "QLoRA config has invalid values."
    )
    return CheckResult(
        key="qlora_configuration",
        label="QLoRA configuration",
        status=_status(ok),
        ok=ok,
        details=details,
        data={
            "max_seq_length": max_seq_length,
            "load_in_4bit": load_in_4bit,
            "use_gradient_checkpointing": gradient_checkpointing,
            "bias": bias,
        },
    )


def _check_optimizer(optimizer: str) -> CheckResult:
    normalized = optimizer.strip()
    ok = bool(normalized) and normalized in KNOWN_OPTIMIZERS
    details = f"optimizer={normalized}" if ok else f"Unsupported optimizer '{normalized}'."
    return CheckResult(
        key="optimizer",
        label="Optimizer",
        status=_status(ok),
        ok=ok,
        details=details,
        data={"optimizer": normalized, "known_optimizers": sorted(KNOWN_OPTIMIZERS)},
    )


def _check_batch_sizes(trainer: dict[str, Any]) -> CheckResult:
    train_bsz = _safe_int(trainer.get("per_device_train_batch_size"), 0)
    eval_bsz = _safe_int(trainer.get("per_device_eval_batch_size"), 0)
    ok = train_bsz > 0 and eval_bsz > 0
    details = (
        f"per_device_train_batch_size={train_bsz}, per_device_eval_batch_size={eval_bsz}"
        if ok
        else "Batch sizes must be > 0."
    )
    return CheckResult(
        key="batch_sizes",
        label="Batch sizes",
        status=_status(ok),
        ok=ok,
        details=details,
        data={
            "per_device_train_batch_size": train_bsz,
            "per_device_eval_batch_size": eval_bsz,
        },
    )


def _check_gradient_accumulation(trainer: dict[str, Any]) -> CheckResult:
    value = _safe_int(trainer.get("gradient_accumulation_steps"), 0)
    ok = value > 0
    details = (
        f"gradient_accumulation_steps={value}" if ok else "gradient_accumulation_steps must be > 0."
    )
    return CheckResult(
        key="gradient_accumulation",
        label="Gradient accumulation",
        status=_status(ok),
        ok=ok,
        details=details,
        data={"gradient_accumulation_steps": value},
    )


def _ensure_dir(path: Path) -> tuple[bool, str]:
    try:
        path.mkdir(parents=True, exist_ok=True)
        writable = os.access(path, os.W_OK)
        return writable, ("exists+writable" if writable else "not writable")
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def _check_directories(paths: dict[str, Path]) -> tuple[CheckResult, CheckResult]:
    output_dir = paths["base_output_dir"]
    checkpoint_dir = paths["checkpoints_dir"]

    output_ok, output_info = _ensure_dir(output_dir)
    checkpoint_ok, checkpoint_info = _ensure_dir(checkpoint_dir)

    output_result = CheckResult(
        key="output_directory",
        label="Output directory",
        status=_status(output_ok),
        ok=output_ok,
        details=f"{output_dir} -> {output_info}",
        data={"path": str(output_dir), "state": output_info},
    )
    checkpoint_result = CheckResult(
        key="checkpoint_directory",
        label="Checkpoint directory",
        status=_status(checkpoint_ok),
        ok=checkpoint_ok,
        details=f"{checkpoint_dir} -> {checkpoint_info}",
        data={"path": str(checkpoint_dir), "state": checkpoint_info},
    )
    return checkpoint_result, output_result


def _run_one_forward_backward(
    *,
    model_id: str,
    qlora: dict[str, Any],
    sample_text: str,
) -> CheckResult:
    if not sample_text:
        return CheckResult(
            key="dry_run_forward_backward",
            label="Dry-run forward/backward pass",
            status="FAIL",
            ok=False,
            details="No valid sample text found in dataset.",
            data={},
        )

    payload = {
        "model_id": model_id,
        "qlora": qlora,
        "sample_text": sample_text,
        "required_targets": sorted(REQUIRED_LORA_TARGET_MODULES),
    }
    code = (
        "import json\n"
        "import sys\n"
        "payload = json.loads(sys.stdin.read() or '{}')\n"
        "model_id = str(payload.get('model_id') or '')\n"
        "qlora = payload.get('qlora') or {}\n"
        "sample_text = str(payload.get('sample_text') or '')\n"
        "result = {'ok': False, 'error': '', 'loss': None, "
        "'grad_norm_first_param': None, 'tokens': 0, 'device': ''}\n"
        "try:\n"
        "    import torch\n"
        "    if not torch.cuda.is_available():\n"
        "        raise RuntimeError('CUDA is not available; cannot run Unsloth "
        "QLoRA forward/backward.')\n"
        "    from unsloth import FastLanguageModel\n"
        "    max_seq_length = int(qlora.get('max_seq_length', 2048))\n"
        "    model, tokenizer = FastLanguageModel.from_pretrained(\n"
        "        model_name=model_id,\n"
        "        max_seq_length=max_seq_length,\n"
        "        dtype=None,\n"
        "        load_in_4bit=bool(qlora.get('load_in_4bit', True)),\n"
        "    )\n"
        "    model = FastLanguageModel.get_peft_model(\n"
        "        model,\n"
        "        r=int(qlora.get('lora_r', 16)),\n"
        "        target_modules=qlora.get("
        "'target_modules', payload.get('required_targets') or []),\n"
        "        lora_alpha=int(qlora.get('lora_alpha', 16)),\n"
        "        lora_dropout=float(qlora.get('lora_dropout', 0.0)),\n"
        "        bias=str(qlora.get('bias', 'none')),\n"
        "        use_gradient_checkpointing=qlora.get('use_gradient_checkpointing', 'unsloth'),\n"
        "        random_state=int(qlora.get('random_state', 42)),\n"
        "    )\n"
        "    batch = tokenizer(\n"
        "        sample_text,\n"
        "        return_tensors='pt',\n"
        "        truncation=True,\n"
        "        max_length=max_seq_length,\n"
        "    )\n"
        "    if 'input_ids' not in batch:\n"
        "        raise ValueError('Tokenizer output missing input_ids.')\n"
        "    if batch['input_ids'].numel() < 2:\n"
        "        raise ValueError('Tokenized sample too short for language modeling loss.')\n"
        "    device = next(model.parameters()).device\n"
        "    batch = {k: v.to(device) for k, v in batch.items()}\n"
        "    labels = batch['input_ids'].clone()\n"
        "    model.train()\n"
        "    model.zero_grad(set_to_none=True)\n"
        "    outputs = model(**batch, labels=labels)\n"
        "    loss = outputs.loss\n"
        "    if loss is None:\n"
        "        raise RuntimeError('Model forward pass did not return loss.')\n"
        "    loss.backward()\n"
        "    grad_norm = None\n"
        "    for _, parameter in model.named_parameters():\n"
        "        if parameter.grad is not None:\n"
        "            grad_norm = float(parameter.grad.detach().float().norm().item())\n"
        "            break\n"
        "    result.update({\n"
        "        'ok': True,\n"
        "        'loss': float(loss.detach().float().item()),\n"
        "        'grad_norm_first_param': grad_norm,\n"
        "        'tokens': int(batch['input_ids'].shape[-1]),\n"
        "        'device': str(device),\n"
        "    })\n"
        "except Exception as exc:\n"
        "    result['error'] = f'{type(exc).__name__}: {exc}'\n"
        "print(json.dumps(result, ensure_ascii=False))\n"
    )
    process = subprocess.run(
        [sys.executable, "-c", code],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
    )

    if process.returncode != 0:
        tail = (process.stderr or process.stdout or "").strip()
        if len(tail) > 500:
            tail = tail[-500:]
        details = (
            f"subprocess_exit={process.returncode}: {tail}"
            if tail
            else (f"subprocess_exit={process.returncode}")
        )
        return CheckResult(
            key="dry_run_forward_backward",
            label="Dry-run forward/backward pass",
            status="FAIL",
            ok=False,
            details=details,
            data={},
        )

    try:
        payload_out = json.loads(process.stdout.strip() or "{}")
    except json.JSONDecodeError:
        payload_out = {}

    ok = bool(payload_out.get("ok"))
    if not ok:
        return CheckResult(
            key="dry_run_forward_backward",
            label="Dry-run forward/backward pass",
            status="FAIL",
            ok=False,
            details=str(payload_out.get("error") or "Unknown dry-run failure."),
            data=payload_out if isinstance(payload_out, dict) else {},
        )

    return CheckResult(
        key="dry_run_forward_backward",
        label="Dry-run forward/backward pass",
        status="PASS",
        ok=True,
        details="Executed exactly one forward/backward pass without starting trainer.train().",
        data=payload_out if isinstance(payload_out, dict) else {},
    )


def _render_markdown_report(
    *,
    generated_at_utc: str,
    overall_ready: bool,
    checks: list[CheckResult],
    resolved: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.append("# QLoRA First-Run Readiness Report")
    lines.append("")
    lines.append(f"- Generated (UTC): `{generated_at_utc}`")
    lines.append(f"- Overall status: `{'READY' if overall_ready else 'BLOCKED'}`")
    lines.append(f"- Run id: `{resolved['run_id']}`")
    lines.append(f"- Model id: `{resolved['model_id']}`")
    lines.append("")
    lines.append("## Check Results")
    lines.append("")
    lines.append("| Check | Status | Details |")
    lines.append("|---|---|---|")
    for row in checks:
        safe_details = row.details.replace("|", "\\|")
        lines.append(f"| {row.label} | {row.status} | {safe_details} |")
    lines.append("")
    lines.append("## Resolved First-Run Config")
    lines.append("")
    lines.append(f"- optimizer: `{resolved['optimizer']}`")
    lines.append(
        f"- per_device_train_batch_size: `{resolved['trainer'].get('per_device_train_batch_size')}`"
    )
    lines.append(
        f"- per_device_eval_batch_size: `{resolved['trainer'].get('per_device_eval_batch_size')}`"
    )
    lines.append(
        f"- gradient_accumulation_steps: `{resolved['trainer'].get('gradient_accumulation_steps')}`"
    )
    lines.append(f"- qlora.max_seq_length: `{resolved['qlora'].get('max_seq_length')}`")
    lines.append(f"- qlora.load_in_4bit: `{resolved['qlora'].get('load_in_4bit')}`")
    lines.append(f"- qlora.lora_r: `{resolved['qlora'].get('lora_r')}`")
    lines.append(f"- qlora.lora_alpha: `{resolved['qlora'].get('lora_alpha')}`")
    lines.append(f"- checkpoint_dir (run): `{resolved['checkpoints_dir']}`")
    lines.append(f"- output_dir (base): `{resolved['base_output_dir']}`")

    blockers = [row for row in checks if not row.ok]
    if blockers:
        lines.append("")
        lines.append("## Blocking Items")
        lines.append("")
        for row in blockers:
            lines.append(f"- {row.label}: {row.details}")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="QLoRA first-run readiness checker.")
    parser.add_argument("--base-config", default=str(DEFAULT_BASE_CONFIG))
    parser.add_argument("--phase1-config", default=str(DEFAULT_PHASE1_CONFIG))
    parser.add_argument("--dataset-root", default=str(DEFAULT_DATASET_ROOT))
    parser.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--plan-id", default=DEFAULT_PLAN_ID)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--report-md", default=str(DEFAULT_REPORT_MD))
    parser.add_argument("--report-json", default=str(DEFAULT_REPORT_JSON))
    parser.add_argument(
        "--allow-network-model-fetch",
        action="store_true",
        help="Allow model/tokenizer checks to fetch from remote Hub when missing locally.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if any required check fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    generated_at = _utc_now()

    resolved = _resolve_first_run(
        base_config_path=Path(args.base_config),
        phase1_config_path=Path(args.phase1_config),
        run_id=str(args.run_id),
        output_root=Path(args.output_root),
        plan_id=str(args.plan_id),
    )

    checks: list[CheckResult] = []

    unsloth_install, unsloth_runtime = _check_unsloth_installation()
    checks.append(unsloth_install)

    cuda_result, _gpu_ready = _check_cuda_gpu()
    checks.append(cuda_result)

    model_result, tokenizer_result = _check_model_and_tokenizer(
        model_id=resolved["model_id"],
        local_only=not bool(args.allow_network_model_fetch),
    )
    checks.append(model_result)
    checks.append(tokenizer_result)

    dataset_result, sample_text = _check_dataset_format(Path(args.dataset_root))
    checks.append(dataset_result)

    checks.append(_check_lora_config(resolved["qlora"]))
    checks.append(_check_qlora_config(resolved["qlora"]))
    checks.append(_check_optimizer(resolved["optimizer"]))
    checks.append(_check_batch_sizes(resolved["trainer"]))
    checks.append(_check_gradient_accumulation(resolved["trainer"]))

    checkpoint_result, output_result = _check_directories(resolved)
    checks.append(checkpoint_result)
    checks.append(output_result)

    # Runtime importability gates the single-pass dry-run.
    if not unsloth_runtime.ok:
        checks.append(
            CheckResult(
                key="dry_run_forward_backward",
                label="Dry-run forward/backward pass",
                status="FAIL",
                ok=False,
                details=(
                    "Skipped actual pass because unsloth runtime import failed: "
                    f"{unsloth_runtime.details}"
                ),
                data={},
            )
        )
    else:
        checks.append(
            _run_one_forward_backward(
                model_id=resolved["model_id"],
                qlora=resolved["qlora"],
                sample_text=sample_text,
            )
        )

    overall_ready = all(row.ok for row in checks)

    report_payload = {
        "generated_at_utc": generated_at,
        "overall_status": "READY" if overall_ready else "BLOCKED",
        "resolved_run": {
            "run_id": resolved["run_id"],
            "phase_id": resolved["phase_id"],
            "model_id": resolved["model_id"],
            "optimizer": resolved["optimizer"],
            "packing": resolved["packing"],
            "run_dir": str(resolved["run_dir"]),
            "checkpoints_dir": str(resolved["checkpoints_dir"]),
            "base_output_dir": str(resolved["base_output_dir"]),
            "base_checkpoint_dir": str(resolved["base_checkpoint_dir"]),
            "qlora": resolved["qlora"],
            "trainer": resolved["trainer"],
        },
        "checks": [
            {
                "key": row.key,
                "label": row.label,
                "status": row.status,
                "ok": row.ok,
                "details": row.details,
                "data": row.data,
            }
            for row in checks
        ],
    }

    report_json_path = Path(args.report_json)
    report_json_path.parent.mkdir(parents=True, exist_ok=True)
    report_json_path.write_text(
        json.dumps(report_payload, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )

    report_md = _render_markdown_report(
        generated_at_utc=generated_at,
        overall_ready=overall_ready,
        checks=checks,
        resolved=resolved,
    )
    report_md_path = Path(args.report_md)
    report_md_path.parent.mkdir(parents=True, exist_ok=True)
    report_md_path.write_text(report_md, encoding="utf-8")

    print(json.dumps(report_payload, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"report_markdown={report_md_path}")
    print(f"report_json={report_json_path}")
    if not overall_ready:
        print("readiness=BLOCKED")
    else:
        print("readiness=READY")

    if args.strict and not overall_ready:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
