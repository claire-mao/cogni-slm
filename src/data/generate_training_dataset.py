"""Generate AP Language training examples from raw essays.

This script:
1. Reads essays from datasets/raw/
2. Builds a teacher prompt per essay
3. Calls a provider abstraction
4. Writes one JSON file per essay

No API is hardcoded; provider execution is abstracted behind one function.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_REQUIRED_FIELDS = (
    "id",
    "essay",
    "rubric_score",
    "score_explanation",
    "strongest_evidence",
    "weakest_reasoning",
    "revision",
    "teacher_reasoning",
    "metadata",
)


@dataclass(frozen=True)
class EssayInput:
    """Single essay input extracted from datasets/raw."""

    essay_id: str
    essay_text: str
    source_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate training dataset from raw essays.")
    parser.add_argument("--raw-dir", default="datasets/raw", help="Input directory for raw essays.")
    parser.add_argument(
        "--teacher-prompt-path",
        default="docs/teacher_prompt.md",
        help="Path to teacher prompt documentation/template.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/processed/training_examples",
        help="Output directory for one JSON file per essay.",
    )
    parser.add_argument(
        "--provider",
        default="mock",
        help="Provider identifier (e.g. mock/custom).",
    )
    parser.add_argument(
        "--model",
        default="teacher-placeholder-v1",
        help="Teacher model identifier.",
    )
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size for generation loop.")
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip essays with an existing output JSON.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate deterministic mock outputs without external provider calls.",
    )
    parser.add_argument(
        "--failure-log",
        default="failures.log",
        help="Failure log filename relative to output directory.",
    )
    return parser.parse_args()


def load_teacher_prompt(path: Path) -> str:
    """Load teacher prompt text from documentation file."""
    if not path.exists():
        raise FileNotFoundError(f"Teacher prompt file not found: {path}")
    return path.read_text(encoding="utf-8")


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)


def discover_essays(raw_dir: Path) -> list[EssayInput]:
    """Discover essays from txt/md/json/jsonl files under raw_dir."""
    essays: list[EssayInput] = []
    for path in sorted(raw_dir.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue

        suffix = path.suffix.lower()
        if suffix in {".txt", ".md"}:
            text = path.read_text(encoding="utf-8").strip()
            if text:
                essay_id = _safe_id(path.stem)
                essays.append(EssayInput(essay_id=essay_id, essay_text=text, source_path=str(path)))
            continue

        if suffix == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict) and "essay" in payload:
                essay_text = str(payload["essay"]).strip()
                if essay_text:
                    essay_id = _safe_id(str(payload.get("id", path.stem)))
                    essays.append(
                        EssayInput(essay_id=essay_id, essay_text=essay_text, source_path=str(path))
                    )
            continue

        if suffix == ".jsonl":
            for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                raw = line.strip()
                if not raw:
                    continue
                payload = json.loads(raw)
                if isinstance(payload, dict) and "essay" in payload:
                    essay_text = str(payload["essay"]).strip()
                    if essay_text:
                        fallback_id = f"{path.stem}-{index:05d}"
                        essay_id = _safe_id(str(payload.get("id", fallback_id)))
                        essays.append(
                            EssayInput(
                                essay_id=essay_id,
                                essay_text=essay_text,
                                source_path=f"{path}:{index}",
                            )
                        )
    return essays


def build_prompt(teacher_prompt_doc: str, essay: EssayInput) -> str:
    """Build one teacher prompt instance."""
    return (
        f"{teacher_prompt_doc}\n\n"
        f"Essay ID: {essay.essay_id}\n"
        "Essay Text:\n"
        f"{essay.essay_text}\n"
    )


def call_teacher_provider(
    *,
    prompt: str,
    essay: EssayInput,
    provider: str,
    model: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Provider abstraction for teacher generation.

    This function intentionally avoids API-specific hardcoding.
    Replace the non-mock branch with your provider integration when ready.
    """
    if dry_run or provider == "mock":
        word_count = len(essay.essay_text.split())
        score = min(6, max(0, math.floor(word_count / 120)))
        return {
            "id": essay.essay_id,
            "essay": essay.essay_text,
            "rubric_score": int(score),
            "score_explanation": (
                "Placeholder teacher output generated in mock mode for pipeline testing."
            ),
            "strongest_evidence": "Placeholder strongest evidence.",
            "weakest_reasoning": "Placeholder weakest reasoning.",
            "revision": "Add one concrete counterargument and rebuttal with specific evidence.",
            "teacher_reasoning": (
                "Mock reasoning used for dry-run/provider-agnostic pipeline tests."
            ),
            "metadata": {
                "teacher_model": model,
                "rubric_version": "ap_lang_argument_v1",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source_path": essay.source_path,
                "placeholder": True,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "provider": provider,
            },
        }

    raise NotImplementedError(
        "No concrete provider implementation configured. "
        "Implement provider logic inside call_teacher_provider()."
    )


def validate_generated_record(record: dict[str, Any]) -> None:
    """Validate required top-level fields before writing output."""
    for field in DEFAULT_REQUIRED_FIELDS:
        if field not in record:
            raise ValueError(f"Missing required field: {field}")
    if not isinstance(record["rubric_score"], int):
        raise ValueError("rubric_score must be an integer")


def append_failure(log_path: Path, essay_id: str, error: str) -> None:
    """Append one failure line to log."""
    timestamp = datetime.now(timezone.utc).isoformat()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp}\t{essay_id}\t{error}\n")


def main() -> None:
    args = parse_args()
    raw_dir = Path(args.raw_dir)
    output_dir = Path(args.output_dir)
    failure_log_path = output_dir / args.failure_log

    output_dir.mkdir(parents=True, exist_ok=True)
    teacher_prompt_doc = load_teacher_prompt(Path(args.teacher_prompt_path))
    essays = discover_essays(raw_dir)

    if not essays:
        print("No essays found in raw directory. Nothing generated.")
        return

    processed = 0
    skipped = 0
    failed = 0

    for batch_start in range(0, len(essays), args.batch_size):
        batch = essays[batch_start : batch_start + args.batch_size]
        for essay in batch:
            out_path = output_dir / f"{essay.essay_id}.json"
            if args.resume and out_path.exists():
                skipped += 1
                continue

            try:
                prompt = build_prompt(teacher_prompt_doc, essay)
                record = call_teacher_provider(
                    prompt=prompt,
                    essay=essay,
                    provider=args.provider,
                    model=args.model,
                    dry_run=args.dry_run,
                )
                validate_generated_record(record)
                out_path.write_text(
                    json.dumps(record, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
                processed += 1
            except Exception as exc:
                failed += 1
                append_failure(failure_log_path, essay.essay_id, str(exc))

    summary = {
        "raw_dir": str(raw_dir),
        "output_dir": str(output_dir),
        "provider": args.provider,
        "model": args.model,
        "dry_run": args.dry_run,
        "batch_size": args.batch_size,
        "total_essays": len(essays),
        "processed": processed,
        "skipped": skipped,
        "failed": failed,
        "failure_log": str(failure_log_path),
    }
    (output_dir / "generation_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
