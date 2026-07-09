from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.benchmark import run_benchmark, write_benchmark_outputs
from teacher.io import load_gold_examples, load_predictions


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def test_benchmark_end_to_end(tmp_path: Path) -> None:
    gold_path = tmp_path / "datasets" / "gold" / "gold_v1.jsonl"
    _write_jsonl(
        gold_path,
        [
            {
                "example_id": "ex1",
                "source": "asap",
                "license": "research-only",
                "prompt": "Prompt 1",
                "essay": "Essay text one.",
                "gold_score": 4,
                "rubric": ["thesis", "evidence", "organization"],
                "difficulty": "medium",
                "expected_reasoning_skills": ["claim_evidence_linking", "coherence"],
                "expected_fallacies": ["none"],
                "notes_for_reviewers": "Ask for stronger evidence links.",
            },
            {
                "example_id": "ex2",
                "source": "fallacy_examples",
                "license": "cc-by",
                "prompt": "Prompt 2",
                "essay": "Essay text two.",
                "gold_score": 2,
                "rubric": ["clarity", "support"],
                "difficulty": "hard",
                "expected_reasoning_skills": ["counterargument"],
                "expected_fallacies": ["strawman"],
                "notes_for_reviewers": "Counterargument handling is weak.",
            },
        ],
    )

    predictions_path = tmp_path / "preds.jsonl"
    _write_jsonl(
        predictions_path,
        [
            {
                "model_id": "gpt-5",
                "example_id": "ex1",
                "predicted_score": 4,
                "rubric_items": ["thesis", "evidence"],
                "reasoning_skills": ["claim_evidence_linking", "coherence"],
                "argument_quality_score": 4,
                "fallacy_label": "none",
                "educational_feedback": (
                    "Revise your thesis and add more evidence to strengthen logic."
                ),
                "json_valid": True,
                "latency_ms": 1100,
                "input_tokens": 500,
                "output_tokens": 180,
                "cost_usd": 0.01,
            },
            {
                "model_id": "gpt-5",
                "example_id": "ex2",
                "predicted_score": 3,
                "rubric_items": ["clarity"],
                "reasoning_skills": ["counterargument"],
                "argument_quality_score": 2,
                "fallacy_label": "strawman",
                "educational_feedback": (
                    "Clarify your counterargument and support each claim with evidence."
                ),
                "json_valid": True,
                "latency_ms": 1500,
                "token_usage": {"input": 620, "output": 220},
            },
            {
                "model_id": "Claude Sonnet 4",
                "example_id": "ex1",
                "score_prediction": 3,
                "rubric_items": ["thesis"],
                "logical_reasoning_score": 0.5,
                "argument_quality_score": 3,
                "predicted_fallacies": ["none"],
                "feedback": "Improve evidence support and organization.",
                "raw_output": "{\"score\":3}",
                "latency_ms": 900,
                "input_tokens": 490,
                "output_tokens": 140,
            },
            {
                "model_id": "Claude Sonnet 4",
                "example_id": "ex2",
                "score_prediction": 2,
                "rubric_items": ["clarity", "support"],
                "logical_reasoning_score": 0.7,
                "argument_quality_score": 2,
                "predicted_fallacies": ["ad_hominem"],
                "feedback": "Explain why the opposing claim fails and add direct support.",
                "raw_output": "not-json",
                "latency_ms": 800,
                "input_tokens": 600,
                "output_tokens": 170,
            },
        ],
    )

    gold_examples = load_gold_examples(gold_path)
    predictions = load_predictions(predictions_path)
    rows, summaries, manifest = run_benchmark(
        gold_examples=gold_examples,
        predictions=predictions,
        model_ids=("gpt-5", "claude_sonnet_4"),
    )

    assert len(rows) == 4
    assert len(summaries) == 2
    assert manifest["gold_examples"] == 2
    assert summaries[0].model_id in {"gpt-5", "claude_sonnet_4"}

    output_dir = tmp_path / "outputs" / "teacher_benchmark" / "run1"
    write_benchmark_outputs(
        output_dir=output_dir,
        run_id="run1",
        per_example_rows=rows,
        summaries=summaries,
        manifest={"run_id": "run1", **manifest},
    )
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "model_summary.json").exists()
    assert (output_dir / "model_summary.csv").exists()
    assert (output_dir / "per_example_metrics.jsonl").exists()
    assert (output_dir / "report.md").exists()
