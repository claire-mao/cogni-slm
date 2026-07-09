"""Run baseline held-out evaluation: base model -> responses -> judge -> metrics."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, cast

from evaluation.benchmark import BenchmarkRecord, JSONLBenchmarkLoader
from evaluation.deterministic_checks import (
    BehaviorId,
    CheckInput,
    DefaultDeterministicCheckSuite,
    ProhibitionId,
)
from evaluation.judge import DefaultBehaviorJudge, JudgeInputRecord

SYSTEM_PROMPT = (
    "You are Cogni, an educational logical-fallacy tutor. "
    "Follow the behavior specification with clear structure and safe language."
)

PROMPT_TEMPLATE = """Analyze this argument and provide educational feedback.

argument_text: {argument_text}
task_mode: {task_mode}
difficulty_level: {difficulty_level}
context: {context_json}

Required response sections (in this order):
fallacy_hypothesis:
reasoning_diagnosis:
analogy:
  source_scenario:
  mapping:
  limits:
repair:
confidence_note:
"""


class HuggingFaceGenerator:
    """Simple generator adapter for local inference."""

    def __init__(self, model_id: str, auth_token: str | None) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Missing dependencies. Install: transformers torch accelerate "
                "sentencepiece safetensors"
            ) from exc

        self.torch = torch
        self.model_id = model_id
        tokenizer_kwargs: dict[str, Any] = {"token": auth_token, "trust_remote_code": True}
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)
        except Exception:
            tokenizer_kwargs["trust_remote_code"] = False
            tokenizer_kwargs["local_files_only"] = True
            self.tokenizer = AutoTokenizer.from_pretrained(model_id, **tokenizer_kwargs)
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        if torch.cuda.is_available():
            torch_dtype = torch.float16
            device_map: str | None = "auto"
        elif torch.backends.mps.is_available():
            torch_dtype = torch.float16
            device_map = None
        else:
            torch_dtype = torch.float32
            device_map = None

        model_kwargs: dict[str, Any] = {
            "token": auth_token,
            "trust_remote_code": True,
            "torch_dtype": torch_dtype,
            "device_map": device_map,
        }
        try:
            self.model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        except Exception:
            model_kwargs["trust_remote_code"] = False
            model_kwargs["local_files_only"] = True
            self.model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        if device_map is None:
            self.device = "mps" if torch.backends.mps.is_available() else "cpu"
            self.model.to(self.device)
        else:
            self.device = str(getattr(self.model, "device", "cuda"))
        self.model.eval()

    def generate(self, prompt: str, max_new_tokens: int, temperature: float, top_p: float) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        if hasattr(self.tokenizer, "apply_chat_template"):
            prompt_text = self.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )
        else:
            prompt_text = f"SYSTEM: {SYSTEM_PROMPT}\nUSER: {prompt}\nASSISTANT:"

        encoded = self.tokenizer(prompt_text, return_tensors="pt")
        encoded = {key: value.to(self.model.device) for key, value in encoded.items()}

        do_sample = temperature > 0.0
        kwargs: dict[str, Any] = {
            **encoded,
            "max_new_tokens": max_new_tokens,
            "do_sample": do_sample,
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }
        if do_sample:
            kwargs["temperature"] = temperature
            kwargs["top_p"] = top_p

        with self.torch.inference_mode():
            output_ids = self.model.generate(**kwargs)

        generated_ids = output_ids[0][encoded["input_ids"].shape[-1] :]
        return self.tokenizer.decode(generated_ids, skip_special_tokens=True).strip()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run held-out baseline evaluation.")
    parser.add_argument(
        "--model-id",
        default=os.getenv("COGNI_BASE_MODEL", "Qwen/Qwen3-0.6B"),
        help="Base model to evaluate.",
    )
    parser.add_argument("--benchmark-root", default="datasets/eval")
    parser.add_argument("--output-dir", default="outputs/evaluation/baseline")
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--judge-threshold", type=float, default=0.70)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def build_prompt(record: BenchmarkRecord) -> str:
    context_json = json.dumps(record.context or {}, ensure_ascii=False)
    return PROMPT_TEMPLATE.format(
        argument_text=record.argument_text,
        task_mode=record.task_mode,
        difficulty_level=record.difficulty_level or "unspecified",
        context_json=context_json,
    )


def build_check_input(
    *,
    run_id: str,
    model_id: str,
    record: BenchmarkRecord,
    response_text: str,
) -> CheckInput:
    required_behaviors = cast(
        tuple[BehaviorId, ...],
        tuple(
            behavior
            for behavior in record.required_behaviors
            if behavior in {"B1", "B2", "B3", "B4", "B5", "B6", "B7"}
        ),
    )
    prohibited_behaviors = cast(
        tuple[ProhibitionId, ...],
        tuple(
            behavior
            for behavior in record.prohibited_behaviors
            if behavior in {"P1", "P2", "P3", "P4", "P5"}
        ),
    )

    return CheckInput(
        run_id=run_id,
        model_id=model_id,
        example_id=record.example_id,
        split=record.split,
        response_text=response_text,
        expected_sections=record.expected_sections,
        required_behaviors=required_behaviors,
        prohibited_behaviors=prohibited_behaviors,
        metadata=dict(record.metadata),
    )


def render_report(results: dict[str, Any]) -> str:
    lines = [
        "# Baseline Evaluation Report",
        "",
        f"- Run ID: `{results['run_id']}`",
        f"- Model: `{results['model_id']}`",
        f"- Benchmark split: `{results['benchmark_split']}`",
        f"- Total prompts: `{results['total_prompts']}`",
        f"- Passes: `{results['passes']}`",
        f"- Failures: `{results['failures']}`",
        f"- Pass rate: `{results['pass_rate']:.4f}`",
        "",
        "## Metrics",
        "",
        f"- Deterministic mean score: `{results['metrics']['deterministic_mean']:.4f}`",
        f"- Judge overall mean score: `{results['metrics']['judge_overall_mean']:.4f}`",
        "",
        "## Sample Failures",
        "",
    ]
    failures = [row for row in results["examples"] if not row["passed"]][:3]
    if not failures:
        lines.append("- None")
    else:
        for row in failures:
            lines.append(
                f"- `{row['example_id']}`: deterministic_pass={row['deterministic_pass']}, "
                f"judge_pass={row['judge']['passed']}"
            )

    lines.extend(["", "## Sample Successes", ""])
    successes = [row for row in results["examples"] if row["passed"]][:3]
    if not successes:
        lines.append("- None")
    else:
        for row in successes:
            lines.append(
                f"- `{row['example_id']}`: deterministic={row['deterministic_score']:.4f}, "
                f"judge={row['judge']['overall_score']:.4f}"
            )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    run_id = datetime.now(timezone.utc).strftime("baseline-eval-%Y%m%dT%H%M%SZ")
    loader = JSONLBenchmarkLoader(args.benchmark_root)
    records = list(loader.load_split("heldout_benchmark"))
    if args.limit is not None:
        records = records[: args.limit]
    if not records:
        raise ValueError("No held-out benchmark prompts found.")

    auth_token = os.getenv("HUGGINGFACE_HUB_TOKEN")
    generator = HuggingFaceGenerator(args.model_id, auth_token=auth_token)
    check_suite = DefaultDeterministicCheckSuite()
    judge = DefaultBehaviorJudge(pass_threshold=args.judge_threshold)

    examples: list[dict[str, Any]] = []
    deterministic_scores: list[float] = []
    judge_scores: list[float] = []

    for record in records:
        prompt = build_prompt(record)
        response = generator.generate(
            prompt=prompt,
            max_new_tokens=args.max_new_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
        )

        check_input = build_check_input(
            run_id=run_id,
            model_id=args.model_id,
            record=record,
            response_text=response,
        )
        check_results = list(check_suite.run(check_input))
        deterministic_score = mean([item.score for item in check_results]) if check_results else 0.0
        deterministic_pass = all(item.passed for item in check_results) if check_results else False

        judge_input = JudgeInputRecord(
            run_id=run_id,
            model_id=args.model_id,
            example_id=record.example_id,
            prompt=prompt,
            response=response,
            benchmark_record=record,
            metadata={"split": record.split},
        )
        judge_output = judge.evaluate(judge_input)

        deterministic_scores.append(deterministic_score)
        judge_scores.append(judge_output.overall_score)
        passed = deterministic_pass and judge_output.passed

        examples.append(
            {
                "example_id": record.example_id,
                "passed": passed,
                "deterministic_pass": deterministic_pass,
                "deterministic_score": deterministic_score,
                "deterministic_results": [asdict(item) for item in check_results],
                "judge": judge_output.to_json_dict(),
                "response": response,
            }
        )

    passes = sum(1 for row in examples if row["passed"])
    total_prompts = len(examples)
    results = {
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_id": args.model_id,
        "benchmark_split": "heldout_benchmark",
        "total_prompts": total_prompts,
        "passes": passes,
        "failures": total_prompts - passes,
        "pass_rate": passes / total_prompts,
        "metrics": {
            "deterministic_mean": mean(deterministic_scores) if deterministic_scores else 0.0,
            "judge_overall_mean": mean(judge_scores) if judge_scores else 0.0,
        },
        "examples": examples,
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "baseline_results.json"
    report_path = out_dir / "baseline_report.md"

    results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(render_report(results), encoding="utf-8")

    print(f"baseline_results={results_path}")
    print(f"baseline_report={report_path}")


if __name__ == "__main__":
    main()
