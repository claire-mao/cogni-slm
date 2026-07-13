#!/usr/bin/env python3
"""Compile strict seven-step teacher responses into Colab-ready SFT JSONL."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

SYSTEM = (
    "You are an AP English Language logical-fallacy tutor. Follow the required "
    "seven-section instructional sequence exactly."
)
SECTIONS = (
    ("Argument Summary", "argument_summary"),
    ("Assumptions", "assumptions"),
    ("Primary Fallacy", "primary_fallacy"),
    ("Why This Applies", "why_this_applies"),
    ("Cross-Domain Analogy", "cross_domain_analogy"),
    ("Transfer Check", "transfer_check"),
    ("Reflective Question", "reflective_question"),
)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return rows


def text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def validate_behavior(value: Any) -> tuple[bool, list[str]]:
    errors: list[str] = []
    if not isinstance(value, dict):
        return False, ["missing_behavior_output"]
    for _, key in SECTIONS:
        if key not in value:
            errors.append(f"missing_{key}")
    assumptions = value.get("assumptions")
    if (
        not isinstance(assumptions, list)
        or not assumptions
        or not all(text(x) for x in assumptions)
    ):
        errors.append("invalid_assumptions")
    analogy = value.get("cross_domain_analogy")
    if (
        not isinstance(analogy, dict)
        or not text(analogy.get("analogy"))
        or not text(analogy.get("mapping"))
    ):
        errors.append("invalid_cross_domain_analogy")
    transfer = value.get("transfer_check")
    if not isinstance(transfer, dict):
        errors.append("invalid_transfer_check")
    elif (
        transfer.get("answer_revealed") is True
        or not text(transfer.get("example"))
        or not text(transfer.get("question"))
    ):
        errors.append("transfer_answer_or_fields_invalid")
    reflection = text(value.get("reflective_question"))
    if not reflection.endswith("?") or reflection.count("?") != 1:
        errors.append("reflective_question_invalid")
    for key in ("argument_summary", "primary_fallacy", "why_this_applies"):
        if not text(value.get(key)):
            errors.append(f"empty_{key}")
    return not errors, errors


def render_behavior(value: dict[str, Any]) -> str:
    assumptions = "\n".join(f"- {text(item)}" for item in value["assumptions"])
    analogy = value["cross_domain_analogy"]
    transfer = value["transfer_check"]
    rendered = {
        "argument_summary": text(value["argument_summary"]),
        "assumptions": assumptions,
        "primary_fallacy": text(value["primary_fallacy"]),
        "why_this_applies": text(value["why_this_applies"]),
        "cross_domain_analogy": (
            f"{text(analogy['analogy'])}\n\nMapping: {text(analogy['mapping'])}"
        ),
        "transfer_check": f"{text(transfer['example'])}\n\n{text(transfer['question'])}",
        "reflective_question": text(value["reflective_question"]),
    }
    return "\n\n".join(f"## {title}\n{rendered[key]}" for title, key in SECTIONS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputs",
        default="datasets/training_candidates/ap_fallacy_production_v1/labeling_input.jsonl",
    )
    parser.add_argument("--responses", default="direct_gemini_15k.jsonl")
    parser.add_argument("--output-root", default="datasets/sft_ap_tutor/production_v1")
    parser.add_argument("--min-confidence", type=float, default=None)
    parser.add_argument("--min-accepted", type=int, default=10_000)
    args = parser.parse_args()

    inputs = {row["example_id"]: row for row in read_jsonl(Path(args.inputs))}
    responses = read_jsonl(Path(args.responses))
    accepted: dict[str, list[dict[str, Any]]] = {"train": [], "validation": [], "test": []}
    rejected: Counter[str] = Counter()
    seen_inputs: set[str] = set()
    seen_outputs: set[str] = set()

    for response in responses:
        example_id = text(response.get("example_id"))
        source = inputs.get(example_id)
        if source is None:
            rejected["unknown_example_id"] += 1
            continue
        if response.get("valid") is False:
            rejected["upstream_invalid"] += 1
            continue
        output = response.get("output")
        if not isinstance(output, dict):
            rejected["missing_output"] += 1
            continue
        metadata = output.get("metadata") if isinstance(output.get("metadata"), dict) else {}
        raw_output = metadata.get("raw_json_output")
        teacher_output = raw_output if isinstance(raw_output, dict) else output
        confidence = teacher_output.get("confidence", output.get("confidence"))
        if args.min_confidence is not None and (
            not isinstance(confidence, int | float) or float(confidence) < args.min_confidence
        ):
            rejected["low_confidence"] += 1
            continue
        behavior_output = teacher_output.get("behavior_output")
        if not isinstance(behavior_output, dict):
            behavior_output = teacher_output
        valid, errors = validate_behavior(behavior_output)
        if not valid:
            for error in errors:
                rejected[error] += 1
            continue
        user_input = text(source.get("essay"))
        assistant = render_behavior(behavior_output)
        input_hash = hashlib.sha256(user_input.casefold().encode()).hexdigest()
        output_hash = hashlib.sha256(assistant.casefold().encode()).hexdigest()
        if input_hash in seen_inputs:
            rejected["duplicate_input"] += 1
            continue
        if output_hash in seen_outputs:
            rejected["duplicate_output"] += 1
            continue
        seen_inputs.add(input_hash)
        seen_outputs.add(output_hash)
        split = source.get("split")
        if split not in accepted:
            rejected["invalid_split"] += 1
            continue
        messages = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": assistant},
        ]
        accepted[split].append(
            {
                "id": example_id,
                "messages": messages,
                "text": "\n\n".join(f"<|{item['role']}|>\n{item['content']}" for item in messages),
                "metadata": {
                    "source": source.get("source"),
                    "confidence": (
                        float(confidence) if isinstance(confidence, int | float) else None
                    ),
                    "expected_fallacies": source.get("metadata", {}).get("expected_fallacies", []),
                },
            }
        )

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    for split, rows in accepted.items():
        with (output_root / f"{split}.jsonl").open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    total = sum(map(len, accepted.values()))
    summary = {
        "input_rows": len(inputs),
        "response_rows": len(responses),
        "accepted_rows": total,
        "split_counts": {key: len(value) for key, value in accepted.items()},
        "rejections": dict(rejected.most_common()),
        "min_confidence": args.min_confidence,
        "min_accepted": args.min_accepted,
        "ready_for_training": total >= args.min_accepted,
    }
    (output_root / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if total < args.min_accepted:
        raise SystemExit(f"Only {total} accepted examples; minimum is {args.min_accepted}")


if __name__ == "__main__":
    main()
