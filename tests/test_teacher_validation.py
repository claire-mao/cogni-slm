from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.io import GoldExample, PredictionRecord
from teacher.validation import run_validation, validate_prediction


def _gold_example() -> GoldExample:
    return GoldExample(
        example_id="ex1",
        source="asap",
        license="research-only",
        prompt="Evaluate argument quality.",
        essay=(
            "The author claims school uniforms improve focus. "
            "They cite attendance data and discuss counterarguments."
        ),
        gold_score=4.0,
        rubric=("claim", "evidence", "reasoning", "organization", "style"),
        difficulty="medium",
        expected_reasoning_skills=("claim_evidence_linking", "counterargument"),
        expected_fallacies=("none",),
        notes_for_reviewers="Check whether feedback cites essay evidence.",
    )


def test_validate_prediction_success_path() -> None:
    prediction = PredictionRecord(
        model_id="gpt-5",
        example_id="ex1",
        predicted_score=4.0,
        rubric_items=("claim", "evidence", "reasoning", "organization", "style"),
        rubric_score=1.0,
        reasoning_skills=("claim_evidence_linking",),
        reasoning_score=0.9,
        argument_quality_score=0.9,
        predicted_fallacies=("none",),
        feedback_text="Clear claim and evidence. Revise organization for stronger flow.",
        json_valid=True,
        latency_ms=1000.0,
        input_tokens=500,
        output_tokens=200,
        cost_usd=0.01,
        raw_payload={
            "output": {
                "score": 4,
                "confidence": 0.85,
                "rubric": {
                    "criteria": [
                        {
                            "criterion": "claim",
                            "judgment": "meets",
                            "evidence": "The claim is explicit.",
                            "impact": "Supports clear stance.",
                        },
                        {
                            "criterion": "evidence",
                            "judgment": "meets",
                            "evidence": "Attendance data is cited.",
                            "impact": "Strengthens support.",
                        },
                        {
                            "criterion": "reasoning",
                            "judgment": "partially_meets",
                            "evidence": "Links evidence to focus.",
                            "impact": "Reasoning is mostly clear.",
                        },
                        {
                            "criterion": "organization",
                            "judgment": "partially_meets",
                            "evidence": "Some transitions are abrupt.",
                            "impact": "Flow can improve.",
                        },
                        {
                            "criterion": "style",
                            "judgment": "meets",
                            "evidence": "Tone is formal and clear.",
                            "impact": "Improves readability.",
                        },
                    ],
                    "summary": "Strong overall with minor organization issues.",
                },
                "reasoning": {
                    "summary": "Score reflects strong support and mostly coherent logic.",
                    "steps": [
                        "Identify the main claim.",
                        "Check evidence relevance and sufficiency.",
                        "Assess coherence and counterargument handling.",
                    ],
                },
                "logical_analysis": {
                    "claim_quality": "strong",
                    "evidence_quality": "strong",
                    "coherence": "mixed",
                    "counterargument_handling": "mixed",
                    "consistency_checks": ["No direct contradiction detected."],
                },
                "fallacies": {
                    "detected": False,
                    "primary": "none",
                    "secondary": [],
                    "evidence": "No clear fallacy pattern appears in the essay.",
                    "severity": "none",
                },
                "feedback": {
                    "strengths": ["Clear thesis and evidence use."],
                    "priorities": ["Improve transition clarity."],
                    "student_facing_summary": "Strengthen organization between evidence points.",
                },
                "revision_plan": {
                    "goal": "Improve coherence between paragraphs.",
                    "actions": [
                        "Add transition sentence after each evidence paragraph.",
                        "Group related evidence under one sub-claim.",
                        "Revise concluding sentence to restate logic chain.",
                    ],
                    "expected_impact": "More coherent reasoning and higher rubric alignment.",
                },
            }
        },
    )

    result = validate_prediction(prediction, gold=_gold_example())
    assert result.json_validity is True
    assert not result.missing_fields
    assert result.score_range_valid is True
    assert not result.hallucinated_rubric_items
    assert result.unsupported_feedback is False
    assert result.reasoning_completeness >= 0.67
    assert result.calibration_brier is not None


def test_run_validation_flags_invalid_payload() -> None:
    bad_prediction = PredictionRecord(
        model_id="qwen3",
        example_id="ex1",
        predicted_score=75.0,
        rubric_items=(),
        rubric_score=None,
        reasoning_skills=(),
        reasoning_score=None,
        argument_quality_score=None,
        predicted_fallacies=(),
        feedback_text="",
        json_valid=False,
        latency_ms=None,
        input_tokens=0,
        output_tokens=0,
        cost_usd=None,
        raw_payload={"raw_output": "not-json"},
    )

    results, summaries = run_validation(
        predictions=[bad_prediction],
        gold_examples=[_gold_example()],
    )
    assert len(results) == 1
    assert results[0].json_validity is False
    assert results[0].score_range_valid is False
    assert summaries[0].json_validity_rate == 0.0
    assert summaries[0].unsupported_feedback_rate == 1.0
