#!/usr/bin/env python3
"""Verify AP tutor environment setup and write a readiness report."""

from __future__ import annotations

import json
import os
from pathlib import Path


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", maxsplit=1)
        values[key.strip()] = value.strip()
    return values


def main() -> None:
    root = Path(".")
    env_values = _read_env_file(root / ".env")

    checks = {
        "github_remote_configured": (root / ".git" / "config").exists(),
        "git_user_name_set": bool(os.popen("git config --get user.name").read().strip()),
        "git_user_email_set": bool(os.popen("git config --get user.email").read().strip()),
        "env_example_exists": (root / ".env.example").exists(),
        "providers_config_exists": (root / "configs/providers/providers_v1.json").exists(),
        "unsloth_training_config_exists": (root / "configs/training/qlora_default.json").exists(),
        "colab_notebook_exists": (
            root / "notebooks/train_ap_tutor_production_colab.ipynb"
        ).exists(),
        "inference_notebook_exists": (root / "notebooks/inference.ipynb").exists(),
        "inference_script_exists": (root / "src/inference/run_inference.py").exists(),
        "huggingface_setup_scaffolded": "HUGGINGFACE_HUB_TOKEN"
        in (root / ".env.example").read_text(encoding="utf-8"),
        "baseline_eval_artifact_exists": (
            root / "outputs/evaluation/prompt_test_public_v1/summary.json"
        ).exists(),
        "teacher_models_set": all(
            bool(env_values.get(key, "").strip())
            for key in ("PRIMARY_TEACHER_MODEL", "VERIFIER_MODEL", "SECONDARY_MODEL")
        ),
    }

    ready_count = sum(1 for value in checks.values() if value)
    total_count = len(checks)

    summary = {
        "checks": checks,
        "ready_count": ready_count,
        "total_checks": total_count,
        "readiness": round(ready_count / max(1, total_count), 4),
    }

    out_json = root / "docs/reports/environment_ap_tutor_validation.json"
    out_md = root / "docs/reports/environment_ap_tutor_validation.md"
    out_json.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# AP Tutor Environment Validation",
        "",
        f"- Ready checks: `{ready_count}/{total_count}`",
        f"- Readiness: `{summary['readiness']:.2%}`",
        "",
        "| Check | Status |",
        "|---|---|",
    ]
    for key, value in checks.items():
        lines.append(f"| {key} | {'PASS' if value else 'FAIL'} |")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
