from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.build_ap_tutor_sft_from_teacher import render_behavior, validate_behavior


def behavior() -> dict[str, object]:
    return {
        "argument_summary": "The author claims one event proves a broad conclusion.",
        "assumptions": ["The single event represents every relevant case."],
        "primary_fallacy": "Hasty generalization",
        "why_this_applies": "One example cannot support the universal conclusion.",
        "cross_domain_analogy": {
            "analogy": "Judging every restaurant from one meal.",
            "mapping": "The meal is the single example and all restaurants are the conclusion.",
        },
        "transfer_check": {
            "example": "One bus was late, so the entire transit system is unreliable.",
            "question": "How would you classify this reasoning?",
        },
        "reflective_question": "What additional evidence would support the conclusion?",
    }


def test_direct_behavior_validates_and_renders_in_contract_order() -> None:
    valid, errors = validate_behavior(behavior())
    assert valid is True
    assert errors == []

    rendered = render_behavior(behavior())
    headings = [
        "## Argument Summary",
        "## Assumptions",
        "## Primary Fallacy",
        "## Why This Applies",
        "## Cross-Domain Analogy",
        "## Transfer Check",
        "## Reflective Question",
    ]
    positions = [rendered.index(heading) for heading in headings]
    assert positions == sorted(positions)


def test_compiler_accepts_direct_response_format(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs.jsonl"
    responses = tmp_path / "responses.jsonl"
    output = tmp_path / "compiled"
    input_row = {
        "example_id": "example-1",
        "essay": "One dog barked at me, so all dogs are dangerous.",
        "source": "test",
        "split": "train",
        "metadata": {},
    }
    inputs.write_text(json.dumps(input_row) + "\n", encoding="utf-8")
    responses.write_text(
        json.dumps({"example_id": "example-1", "valid": True, "output": behavior()}) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/build_ap_tutor_sft_from_teacher.py",
            "--inputs",
            str(inputs),
            "--responses",
            str(responses),
            "--output-root",
            str(output),
            "--min-accepted",
            "1",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    compiled = [json.loads(line) for line in (output / "train.jsonl").read_text().splitlines()]
    assert len(compiled) == 1
    assert compiled[0]["id"] == "example-1"
