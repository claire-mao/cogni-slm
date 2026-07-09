from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.generate_labels import PipelineConfig, run_pipeline


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _teacher_output(score: int, confidence: float = 0.9) -> dict:
    return {
        "score": score,
        "confidence": confidence,
        "rubric": {
            "criteria": [
                {
                    "criterion": "claim",
                    "judgment": "meets",
                    "evidence": "Clear claim.",
                    "impact": "Argument stance is explicit.",
                },
                {
                    "criterion": "evidence",
                    "judgment": "partially_meets",
                    "evidence": "Evidence is present but limited.",
                    "impact": "Support is uneven.",
                },
                {
                    "criterion": "reasoning",
                    "judgment": "partially_meets",
                    "evidence": "Reasoning links are partially explicit.",
                    "impact": "Some logic gaps remain.",
                },
                {
                    "criterion": "organization",
                    "judgment": "meets",
                    "evidence": "Paragraph flow is coherent.",
                    "impact": "Reader can follow argument structure.",
                },
                {
                    "criterion": "style",
                    "judgment": "partially_meets",
                    "evidence": "Mostly clear language.",
                    "impact": "Minor clarity issues.",
                },
            ],
            "summary": "Clear structure with partially developed support.",
        },
        "reasoning": {
            "summary": "Score reflects partial rubric attainment.",
            "steps": [
                "Identify claim strength.",
                "Assess evidence relevance.",
                "Check claim-evidence reasoning links.",
            ],
        },
        "logical_analysis": {
            "claim_quality": "mixed",
            "evidence_quality": "mixed",
            "coherence": "mixed",
            "counterargument_handling": "not_present",
            "consistency_checks": ["No contradiction detected."],
        },
        "fallacies": {
            "detected": False,
            "primary": "none",
            "secondary": [],
            "evidence": "No dominant fallacy pattern.",
            "severity": "none",
        },
        "feedback": {
            "strengths": ["Clear claim and organization."],
            "priorities": ["Strengthen evidence detail."],
            "student_facing_summary": "Add stronger evidence and explain it explicitly.",
        },
        "revision_plan": {
            "goal": "Improve evidence-backed reasoning.",
            "actions": [
                "Add one concrete example per claim.",
                "Explain how each example supports the claim.",
                "Address one counterargument.",
            ],
            "expected_impact": "Higher evidence and reasoning rubric alignment.",
        },
    }


def test_generate_labels_pipeline_precomputed_mode(tmp_path: Path) -> None:
    input_path = tmp_path / "gold_v1.jsonl"
    _write_jsonl(
        input_path,
        [
            {
                "example_id": "ex-train",
                "prompt": "Prompt A",
                "essay": "Essay A includes a claim and some support.",
                "score": 3,
                "split": "train",
                "source": "asap",
                "license": "research-only",
                "metadata": {"rubric": ["claim", "evidence"]},
            },
            {
                "example_id": "ex-val",
                "prompt": "Prompt B",
                "essay": "Essay B discusses a counterargument with mixed evidence.",
                "score": 4,
                "split": "validation",
                "source": "ap_style",
                "license": "cc-by",
                "metadata": {"rubric": ["reasoning", "organization"]},
            },
            {
                "example_id": "ex-test",
                "prompt": "Prompt C",
                "essay": "Essay C is brief but coherent.",
                "score": 2,
                "split": "test",
                "source": "argumentative",
                "license": "open",
                "metadata": {"rubric": ["style"]},
            },
        ],
    )

    predictions_path = tmp_path / "predictions.jsonl"
    _write_jsonl(
        predictions_path,
        [
            {
                "model_id": "gpt-5",
                "example_id": "ex-train",
                "output": _teacher_output(3, 0.91),
                "json_valid": True,
                "latency_ms": 210.0,
                "token_usage": {"input": 220, "output": 160},
            },
            {
                "model_id": "gpt-5",
                "example_id": "ex-val",
                "output": _teacher_output(4, 0.89),
                "json_valid": True,
                "latency_ms": 230.0,
                "token_usage": {"input": 240, "output": 170},
            },
            {
                "model_id": "gpt-5",
                "example_id": "ex-test",
                "output": _teacher_output(2, 0.87),
                "json_valid": True,
                "latency_ms": 205.0,
                "token_usage": {"input": 200, "output": 150},
            },
        ],
    )

    output_root = tmp_path / "datasets" / "sft"
    schema_path = Path(__file__).resolve().parents[1] / "teacher_prompts" / "output_schema.json"
    config = PipelineConfig(
        input_jsonl=input_path,
        output_root=output_root,
        teacher_model_id="gpt-5",
        inference_mode="precomputed",
        predictions_path=predictions_path,
        schema_path=schema_path,
        quality_threshold=0.1,
        confidence_threshold=0.1,
        strict_source_split=True,
        instruction_text="Instruction text",
    )

    manifest = run_pipeline(config)
    assert manifest["counts"]["input_examples"] == 3
    assert manifest["counts"]["after_confidence_filter"] == 3
    assert manifest["counts"]["export_train"] == 1
    assert manifest["counts"]["export_validation"] == 1
    assert manifest["counts"]["export_test"] == 1

    for split in ("train", "validation", "test"):
        split_path = output_root / split / "data.jsonl"
        assert split_path.exists()
        rows = [json.loads(line) for line in split_path.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        row = rows[0]
        assert sorted(row.keys()) == ["input", "instruction", "metadata", "output"]
        assert row["instruction"] == "Instruction text"
        parsed_input = json.loads(row["input"])
        parsed_output = json.loads(row["output"])
        assert "prompt" in parsed_input
        assert "essay" in parsed_input
        assert "score" in parsed_input
        assert "score" in parsed_output
        assert "confidence" in parsed_output
        assert "metadata" in row
