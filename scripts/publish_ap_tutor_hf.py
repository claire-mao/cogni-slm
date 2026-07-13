#!/usr/bin/env python3
"""Publish approved AP tutor dataset/model artifacts to Hugging Face Hub."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", default="datasets/sft_ap_tutor/production_v1")
    parser.add_argument("--model-dir", default="models/merged/ap_tutor_qwen3_1_7b_v1")
    parser.add_argument("--license-report", default="docs/reports/ap_release_license_report.json")
    parser.add_argument("--dataset-card", default="docs/release/dataset_card.md")
    parser.add_argument("--model-card", default="docs/release/model_card.md")
    parser.add_argument("--dataset-repo", required=True)
    parser.add_argument("--model-repo", required=True)
    parser.add_argument("--token-env", default="HUGGINGFACE_HUB_TOKEN")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    paths = [
        Path(args.dataset_dir),
        Path(args.model_dir),
        Path(args.license_report),
        Path(args.dataset_card),
        Path(args.model_card),
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise SystemExit("Missing release artifacts: " + ", ".join(missing))
    report = json.loads(Path(args.license_report).read_text(encoding="utf-8"))
    if report.get("ready") is not True:
        raise SystemExit("License report is not approved; refusing public release")

    plan = {
        "dataset_repo": args.dataset_repo,
        "model_repo": args.model_repo,
        "dataset_dir": args.dataset_dir,
        "model_dir": args.model_dir,
        "publish": args.publish,
    }
    print(json.dumps(plan, indent=2))
    if not args.publish:
        print("Dry run only. Pass --publish after reviewing the plan.")
        return

    token = os.getenv(args.token_env, "").strip()
    if not token:
        raise SystemExit(f"Missing Hugging Face token environment variable: {args.token_env}")
    try:
        from huggingface_hub import HfApi
    except ImportError as exc:
        raise SystemExit("Install huggingface_hub before publishing") from exc

    api = HfApi(token=token)
    api.create_repo(args.dataset_repo, repo_type="dataset", exist_ok=True, private=False)
    api.upload_folder(
        repo_id=args.dataset_repo,
        repo_type="dataset",
        folder_path=args.dataset_dir,
    )
    api.upload_file(
        repo_id=args.dataset_repo,
        repo_type="dataset",
        path_or_fileobj=args.dataset_card,
        path_in_repo="README.md",
    )
    api.create_repo(args.model_repo, repo_type="model", exist_ok=True, private=False)
    api.upload_folder(repo_id=args.model_repo, repo_type="model", folder_path=args.model_dir)
    api.upload_file(
        repo_id=args.model_repo,
        repo_type="model",
        path_or_fileobj=args.model_card,
        path_in_repo="README.md",
    )
    print("Published dataset and model successfully.")


if __name__ == "__main__":
    main()
