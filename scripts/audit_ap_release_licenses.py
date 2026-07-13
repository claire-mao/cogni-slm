#!/usr/bin/env python3
"""Build a fail-closed source-license report for the compiled AP tutor dataset."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", default="datasets/sft_ap_tutor/production_v1")
    parser.add_argument("--license-config", default="configs/release/source_licenses.json")
    parser.add_argument("--output", default="docs/reports/ap_release_license_report.json")
    args = parser.parse_args()

    root = Path(args.dataset_root)
    config = json.loads(Path(args.license_config).read_text(encoding="utf-8"))
    configured = config.get("sources", {})
    counts: Counter[str] = Counter()
    for split in ("train", "validation", "test"):
        for row in read_jsonl(root / f"{split}.jsonl"):
            metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
            counts[str(metadata.get("source", "unknown"))] += 1

    sources: dict[str, Any] = {}
    blockers: list[str] = []
    for source, count in sorted(counts.items()):
        record = configured.get(source)
        if not isinstance(record, dict):
            record = {"status": "missing", "license": "unknown", "evidence_url": ""}
        status = str(record.get("status", "missing"))
        evidence = str(record.get("evidence_url", "")).strip()
        license_name = str(record.get("license", "unknown")).strip()
        approved = status == "approved" and bool(evidence) and license_name != "unknown"
        if not approved:
            blockers.append(source)
        sources[source] = {"rows": count, **record, "approved": approved}

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_root": str(root),
        "total_rows": sum(counts.values()),
        "sources": sources,
        "blocking_sources": blockers,
        "ready": not blockers and bool(counts),
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["ready"]:
        raise SystemExit("Public release blocked by unresolved source licenses")


if __name__ == "__main__":
    main()
