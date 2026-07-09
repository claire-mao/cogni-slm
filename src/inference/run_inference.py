"""Local inference runner scaffold for Cogni."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.utils.paths import repo_root

DEFAULT_MODEL_ID = "Qwen/Qwen3-0.6B"
DEFAULT_PROMPT = (
    "AP Language sample argument: The school board should remove all long-form essays "
    "because students mostly consume short social posts, so essay writing is no longer useful. "
    "Analyze whether this argument is logically sound."
)


def _load_runner() -> callable:
    try:
        from src.inference.runner import run_once
    except ModuleNotFoundError:
        root = repo_root(Path(__file__))
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        from src.inference.runner import run_once
    return run_once


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one inference for Cogni.")
    parser.add_argument("--model-id", default=DEFAULT_MODEL_ID)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    parser.add_argument("--output-dir", default="outputs/inference_demo")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_once = _load_runner()
    result = run_once(
        model_id=args.model_id,
        prompt=args.prompt,
        max_new_tokens=args.max_new_tokens,
        output_dir=args.output_dir,
    )
    print(f"model name: {result['model_id']}")
    print(f"device: {result['device']}")
    print(f"load time: {result['load_time']:.4f}s")
    print(f"inference time: {result['inference_time']:.4f}s")
    print("generated response:")
    print(result["response"])


if __name__ == "__main__":
    main()
