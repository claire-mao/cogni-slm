"""Split deduplicated dataset into train/validation/test JSONL files."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split dataset with reproducible random seed.")
    parser.add_argument(
        "--input-jsonl",
        default="datasets/processed/training_dataset.deduped.jsonl",
        help="Deduplicated input JSONL path.",
    )
    parser.add_argument(
        "--output-dir",
        default="datasets/processed/splits",
        help="Output directory for train/validation/test JSONL files.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        payload = json.loads(raw)
        if isinstance(payload, dict):
            records.append(payload)
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_jsonl)
    output_dir = Path(args.output_dir)

    records = load_jsonl(input_path)
    if not records:
        output_dir.mkdir(parents=True, exist_ok=True)
        write_jsonl(output_dir / "train.jsonl", [])
        write_jsonl(output_dir / "validation.jsonl", [])
        write_jsonl(output_dir / "test.jsonl", [])
        print("No records found; wrote empty split files.")
        return

    rng = random.Random(args.seed)
    shuffled = list(records)
    rng.shuffle(shuffled)

    total = len(shuffled)
    train_end = int(total * 0.8)
    val_end = train_end + int(total * 0.1)

    train_records = shuffled[:train_end]
    validation_records = shuffled[train_end:val_end]
    test_records = shuffled[val_end:]

    write_jsonl(output_dir / "train.jsonl", train_records)
    write_jsonl(output_dir / "validation.jsonl", validation_records)
    write_jsonl(output_dir / "test.jsonl", test_records)

    print(
        json.dumps(
            {
                "total": total,
                "train": len(train_records),
                "validation": len(validation_records),
                "test": len(test_records),
                "seed": args.seed,
                "output_dir": str(output_dir),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
