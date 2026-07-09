from __future__ import annotations

import json
import sys
from argparse import Namespace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.run_teacher_benchmark_execution import _build_plan, run_execution_pipeline


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_prepare_teacher_benchmark_execution_scaffold(tmp_path: Path) -> None:
    config_root = tmp_path / "configs" / "teacher"
    dataset_root = tmp_path / "datasets" / "gold"
    output_root = tmp_path / "outputs" / "teacher_benchmark"

    _write_json(
        config_root / "teacher_validation_master.json",
        {
            "configs": {
                "task_suite": "configs/teacher/teacher_task_suite_v1.json",
                "models_costs": "configs/teacher/teacher_models_costs_v1.json",
            }
        },
    )

    _write_json(
        config_root / "teacher_task_suite_v1.json",
        {
            "tasks": [
                {
                    "task_id": "essay_scoring",
                    "description": "Score one essay.",
                    "required_output_fields": ["score", "confidence"],
                    "scoring_mode": "qwk",
                }
            ]
        },
    )

    _write_json(
        config_root / "teacher_models_costs_v1.json",
        {
            "models": [
                {"model_id": "gpt-5", "display_name": "GPT-5", "api_availability": "openai_api"},
                {"model_id": "o3", "display_name": "o3", "api_availability": "openai_api"},
                {
                    "model_id": "claude_sonnet_4x",
                    "display_name": "Claude Sonnet 4",
                    "api_availability": "anthropic_api",
                },
                {
                    "model_id": "claude_opus_4x",
                    "display_name": "Claude Opus 4",
                    "api_availability": "anthropic_api",
                },
                {
                    "model_id": "gemini_2_5_pro",
                    "display_name": "Gemini 2.5 Pro",
                    "api_availability": "gemini_api",
                },
                {
                    "model_id": "deepseek_r1",
                    "display_name": "DeepSeek R1",
                    "api_availability": "deepseek_api",
                },
                {
                    "model_id": "qwen3",
                    "display_name": "Qwen3",
                    "api_availability": "openai_compatible",
                },
                {
                    "model_id": "llama4_maverick",
                    "display_name": "Llama 4 Maverick",
                    "api_availability": "provider_dependent",
                },
            ]
        },
    )

    _write_jsonl(
        dataset_root / "gold_v1.jsonl",
        [
            {
                "example_id": "ex1",
                "prompt": "Write an argument.",
                "essay": "This is a sample essay with adequate length and detail.",
                "score": 3.0,
                "source": "asap",
                "difficulty": "medium",
            }
        ],
    )

    prompt_template = tmp_path / "teacher_prompt.txt"
    prompt_template.write_text("prompt:\\n{{prompt}}\\nessay:\\n{{essay}}\\n", encoding="utf-8")

    args = Namespace(
        config_root=str(config_root),
        dataset_root=str(dataset_root),
        prompt_template=str(prompt_template),
        prompt_version="v_test",
        models_costs=str(config_root / "teacher_models_costs_v1.json"),
        task_suite=str(config_root / "teacher_task_suite_v1.json"),
        output_root=str(output_root),
        run_id="prep-test",
        temperatures="0.0",
        seeds="42",
        max_examples=0,
        timeout_seconds=30.0,
        max_output_tokens=200,
        execute=False,
    )

    plan, dataset_stats = _build_plan(args)
    summary = run_execution_pipeline(plan, output_root=output_root, dataset_stats=dataset_stats)

    assert summary["status"] == "prepared"
    assert summary["planned_requests"] == 8
    assert summary["successful_requests"] == 0
    assert summary["failed_requests"] == 0

    run_dir = output_root / "prep-test"
    assert (run_dir / "responses" / "responses.jsonl").exists()
    assert (run_dir / "responses" / "failures.jsonl").exists()
    assert (run_dir / "cost" / "summary.json").exists()
    assert (run_dir / "latency" / "summary.json").exists()
    assert (run_dir / "confidence" / "summary.json").exists()
    assert (run_dir / "metadata" / "manifest.json").exists()
