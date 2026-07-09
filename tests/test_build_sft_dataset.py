from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "src" / "data" / "build_sft_dataset.py"
SPEC = importlib.util.spec_from_file_location("build_sft_dataset_module", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _teacher_output(score: int) -> dict:
    return {
        "score": score,
        "confidence": 0.92,
        "rubric": {
            "criteria": [
                {
                    "criterion": "claim",
                    "judgment": "meets",
                    "evidence": "The claim is explicit and consistent.",
                    "impact": "Readers can identify the thesis quickly.",
                },
                {
                    "criterion": "evidence",
                    "judgment": "partially_meets",
                    "evidence": "Some evidence is relevant but limited.",
                    "impact": "Support is present but needs expansion.",
                },
                {
                    "criterion": "reasoning",
                    "judgment": "partially_meets",
                    "evidence": "Reasoning links are present but uneven.",
                    "impact": "Argument logic is understandable but thin.",
                },
                {
                    "criterion": "organization",
                    "judgment": "meets",
                    "evidence": "Paragraph flow is clear.",
                    "impact": "Readers can follow the argument progression.",
                },
                {
                    "criterion": "style",
                    "judgment": "partially_meets",
                    "evidence": "Style is readable with minor repetition.",
                    "impact": "Clarity is mostly maintained.",
                },
            ],
            "summary": "Solid structure with room to strengthen evidence and reasoning.",
        },
        "reasoning": {
            "summary": "The score reflects a clear claim with partially supported reasoning.",
            "steps": [
                "Identify the main claim and stance consistency.",
                "Check whether evidence directly supports each claim.",
                "Assess whether reasoning explains how evidence proves the claim.",
            ],
        },
        "logical_analysis": {
            "claim_quality": "mixed",
            "evidence_quality": "mixed",
            "coherence": "mixed",
            "counterargument_handling": "not_present",
            "consistency_checks": ["No direct contradiction was found."],
        },
        "fallacies": {
            "detected": False,
            "primary": "none",
            "secondary": [],
            "evidence": "No dominant fallacy pattern is clearly present.",
            "severity": "none",
        },
        "feedback": {
            "strengths": ["Your essay has a clear claim and coherent structure."],
            "priorities": ["Add stronger evidence and explain your reasoning more clearly."],
            "student_facing_summary": (
                "Your essay claim is clear; improve evidence and reasoning links."
            ),
        },
        "revision_plan": {
            "goal": "Improve evidence-grounded argument strength.",
            "actions": [
                "Add one concrete evidence example for each body paragraph.",
                "Explain in one sentence how each evidence item supports your claim.",
                "Include and rebut one counterargument in the final body paragraph.",
            ],
            "expected_impact": "Higher rubric alignment for evidence and reasoning.",
        },
    }


def test_build_sft_dataset_exports_all_formats(tmp_path: Path) -> None:
    input_jsonl = tmp_path / "gold_v1.jsonl"
    _write_jsonl(
        input_jsonl,
        [
            {
                "example_id": "ex-train",
                "prompt": "Should schools require uniforms?",
                "essay": "My essay claim supports school uniforms with evidence and reasoning.",
                "score": 4,
                "split": "train",
                "source": "asap",
                "license": "research",
                "metadata": {"rubric": ["claim", "evidence", "reasoning", "organization", "style"]},
            },
            {
                "example_id": "ex-validation",
                "prompt": "Should social media be limited for teens?",
                "essay": "This essay has a clear claim and reasoning but needs stronger evidence.",
                "score": 3,
                "split": "validation",
                "source": "persuade",
                "license": "research",
                "metadata": {"rubric": ["claim", "evidence", "reasoning", "organization", "style"]},
            },
            {
                "example_id": "ex-test",
                "prompt": "Is remote learning effective?",
                "essay": (
                    "The argument presents a claim, partial evidence, and developing reasoning."
                ),
                "score": 2,
                "split": "test",
                "source": "argumentative",
                "license": "research",
                "metadata": {"rubric": ["claim", "evidence", "reasoning", "organization", "style"]},
            },
        ],
    )

    predictions_path = tmp_path / "teacher_outputs.jsonl"
    _write_jsonl(
        predictions_path,
        [
            {
                "model_id": "gpt-5",
                "example_id": "ex-train",
                "output": _teacher_output(4),
                "json_valid": True,
                "latency_ms": 220.0,
                "token_usage": {"input": 400, "output": 220},
            },
            {
                "model_id": "gpt-5",
                "example_id": "ex-validation",
                "output": _teacher_output(3),
                "json_valid": True,
                "latency_ms": 230.0,
                "token_usage": {"input": 420, "output": 230},
            },
            {
                "model_id": "gpt-5",
                "example_id": "ex-test",
                "output": _teacher_output(2),
                "json_valid": True,
                "latency_ms": 240.0,
                "token_usage": {"input": 410, "output": 210},
            },
        ],
    )

    output_root = tmp_path / "datasets" / "sft"
    schema_path = Path(__file__).resolve().parents[1] / "teacher_prompts" / "output_schema.json"
    config = MODULE.SFTBuildConfig(
        input_jsonl=input_jsonl,
        teacher_outputs_path=predictions_path,
        output_root=output_root,
        teacher_model_id="gpt-5",
        inference_mode="precomputed",
        schema_path=schema_path,
        quality_threshold=0.8,
        confidence_threshold=0.6,
        strict_source_split=True,
        instruction_text="Instruction text",
        export_formats=("alpaca", "sharegpt", "chatml", "huggingface"),
    )

    manifest = MODULE.build_sft_dataset(config)

    assert manifest["canonical_manifest"]["counts"]["after_confidence_filter"] == 3
    assert (output_root / "manifest.json").exists()
    assert (output_root / "sft_build_manifest.json").exists()

    for split in ("train", "validation", "test"):
        assert (output_root / split / "data.jsonl").exists()

    alpaca_train = _read_rows(output_root / "formats" / "alpaca" / "train.jsonl")
    assert len(alpaca_train) == 1
    assert set(alpaca_train[0]) == {"id", "instruction", "input", "metadata", "output"}

    sharegpt_train = _read_rows(output_root / "formats" / "sharegpt" / "train.jsonl")
    assert sharegpt_train[0]["conversations"][0]["from"] == "human"
    assert sharegpt_train[0]["conversations"][1]["from"] == "gpt"

    chatml_train = _read_rows(output_root / "formats" / "chatml" / "train.jsonl")
    roles = [message["role"] for message in chatml_train[0]["messages"]]
    assert roles == ["system", "user", "assistant"]

    hf_train = _read_rows(output_root / "formats" / "huggingface" / "train.jsonl")
    assert "messages" in hf_train[0]
    assert "text" in hf_train[0]
    assert hf_train[0]["text"].startswith("<|system|>")


def _read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
