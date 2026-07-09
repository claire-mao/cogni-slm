from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.run_teacher_experiments import (  # noqa: E402
    EvalExample,
    ExperimentPlan,
    ModelSpec,
    TaskSpec,
    run_experiments,
)


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if raw:
            rows.append(json.loads(raw))
    return rows


def test_run_experiments_resume_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    output_root = tmp_path / "outputs"
    prompt_template = tmp_path / "prompt.txt"
    eval_jsonl = tmp_path / "eval.jsonl"
    prompt_template.write_text("Prompt:\n{{prompt}}\nEssay:\n{{essay}}\n", encoding="utf-8")
    eval_jsonl.write_text("", encoding="utf-8")

    plan = ExperimentPlan(
        round_id="round_1_pilot_live",
        run_id="resume-test",
        prompt_version="v1",
        models=(
            ModelSpec(
                model_id="gpt-5",
                display_name="GPT-5",
                api_availability="openai_api",
                pricing={"input": 1.25, "output": 10.0},
                raw={"api_model_name": "gpt-5"},
            ),
        ),
        tasks=(
            TaskSpec(
                task_id="essay_scoring",
                description="Score essay",
                required_output_fields=("score", "confidence"),
                scoring_mode="qwk",
            ),
        ),
        examples=(
            EvalExample(
                example_id="ex1",
                prompt="Prompt 1",
                essay="Essay 1",
                score=3.0,
                source="gold",
                difficulty="medium",
            ),
            EvalExample(
                example_id="ex2",
                prompt="Prompt 2",
                essay="Essay 2",
                score=4.0,
                source="gold",
                difficulty="medium",
            ),
        ),
        seeds=(42,),
        temperatures=(0.0,),
    )

    call_counter = {"count": 0}

    def _fake_call_provider(**_: object) -> tuple[dict, str, int, int]:
        call_counter["count"] += 1
        return ({"provider": "ok"}, '{"score": 4, "confidence": 0.9}', 10, 5)

    monkeypatch.setattr("teacher.run_teacher_experiments._call_provider", _fake_call_provider)

    first = run_experiments(
        plan=plan,
        prompt_template_path=prompt_template,
        output_root=output_root,
        evaluation_jsonl=eval_jsonl,
        max_output_tokens=256,
        timeout_seconds=30.0,
        dry_run=False,
        checkpoint_every=1,
    )
    assert first["attempted_requests"] == 2
    assert first["successful_requests"] == 2
    assert call_counter["count"] == 2

    second = run_experiments(
        plan=plan,
        prompt_template_path=prompt_template,
        output_root=output_root,
        evaluation_jsonl=eval_jsonl,
        max_output_tokens=256,
        timeout_seconds=30.0,
        dry_run=False,
        checkpoint_every=1,
    )

    # Resume should skip completed requests and avoid duplicate successful rows.
    assert second["attempted_requests"] == 0
    assert second["skipped_completed_requests"] == 2
    assert second["successful_requests"] == 0
    assert call_counter["count"] == 2

    responses_path = output_root / "resume-test" / "responses.jsonl"
    rows = _read_jsonl(responses_path)
    assert len(rows) == 2
    assert all("request_key" in row for row in rows)

    progress_path = output_root / "resume-test" / "progress.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    assert progress["completed_requests"] == 2
    assert progress["remaining_requests"] == 0
