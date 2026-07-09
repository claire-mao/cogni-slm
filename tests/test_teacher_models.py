from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from teacher.models import canonical_model_id, estimate_cost_usd


def test_canonical_model_aliases() -> None:
    assert canonical_model_id("GPT-5") == "gpt-5"
    assert canonical_model_id("Claude Sonnet 4") == "claude_sonnet_4"
    assert canonical_model_id("gemini-2.5-pro") == "gemini_2_5_pro"
    assert canonical_model_id("llama 4 maverick") == "llama_4_maverick"


def test_estimate_cost_known_and_unknown() -> None:
    cost = estimate_cost_usd("gpt-5", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == 11.25

    # Provider-dependent in registry.
    assert estimate_cost_usd("llama_4_maverick", input_tokens=1000, output_tokens=1000) is None
