from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.sft_quality import analyze_sft_quality


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_sft_quality_checks(tmp_path: Path) -> None:
    sft_root = tmp_path / "datasets" / "sft"
    schema_path = Path(__file__).resolve().parents[1] / "teacher_prompts" / "output_schema.json"

    base_output = {
        "score": 10,
        "confidence": 0.9,
        "rubric": {
            "criteria": [
                {"criterion": "claim", "judgment": "meets", "evidence": "e1", "impact": "i1"},
                {
                    "criterion": "evidence",
                    "judgment": "partially_meets",
                    "evidence": "e2",
                    "impact": "i2",
                },
                {
                    "criterion": "reasoning",
                    "judgment": "partially_meets",
                    "evidence": "e3",
                    "impact": "i3",
                },
                {
                    "criterion": "organization",
                    "judgment": "partially_meets",
                    "evidence": "e4",
                    "impact": "i4",
                },
                {"criterion": "style", "judgment": "meets", "evidence": "e5", "impact": "i5"},
            ],
            "summary": "ok",
        },
        "reasoning": {"summary": "r", "steps": ["s1", "s2", "s3"]},
        "logical_analysis": {
            "claim_quality": "mixed",
            "evidence_quality": "mixed",
            "coherence": "mixed",
            "counterargument_handling": "not_present",
            "consistency_checks": ["c1"],
        },
        "fallacies": {
            "detected": False,
            "primary": "none",
            "secondary": [],
            "evidence": "none",
            "severity": "none",
        },
        "feedback": {
            "strengths": ["a"],
            "priorities": ["b"],
            "student_facing_summary": "Use clearer evidence.",
        },
        "revision_plan": {"goal": "g", "actions": ["a1", "a2", "a3"], "expected_impact": "ei"},
    }
    duplicate_output = json.dumps(base_output, ensure_ascii=False)

    # Train has duplicate label + identical reasoning + identical feedback.
    _write_jsonl(
        sft_root / "train" / "data.jsonl",
        [
            {
                "instruction": "i",
                "input": json.dumps({"prompt": "p1", "essay": "essay one", "score": 10}),
                "output": duplicate_output,
                "metadata": {"example_id": "ex1", "teacher_model_id": "gpt-5"},
            },
            {
                "instruction": "i",
                "input": json.dumps({"prompt": "p2", "essay": "essay two", "score": 9}),
                "output": duplicate_output,
                "metadata": {"example_id": "ex2", "teacher_model_id": "gpt-5"},
            },
        ],
    )

    # Validation has low confidence + schema invalid output (missing revision_plan).
    invalid_output = dict(base_output)
    invalid_output["confidence"] = 0.2
    invalid_output.pop("revision_plan")
    _write_jsonl(
        sft_root / "validation" / "data.jsonl",
        [
            {
                "instruction": "i",
                "input": json.dumps({"prompt": "p3", "essay": "essay three", "score": 5}),
                "output": json.dumps(invalid_output, ensure_ascii=False),
                "metadata": {"example_id": "ex3", "teacher_model_id": "gpt-5"},
            }
        ],
    )

    summary = analyze_sft_quality(
        sft_root=sft_root,
        schema_path=schema_path,
        confidence_threshold=0.6,
    )

    assert summary.dataset_found is True
    assert summary.examples_total == 3
    assert summary.duplicates_count == 2
    assert summary.identical_reasoning_count >= 2
    assert summary.identical_feedback_count >= 2
    assert summary.low_confidence_count >= 1
    assert summary.schema_invalid_count >= 1

