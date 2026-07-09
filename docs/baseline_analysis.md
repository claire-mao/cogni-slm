# Baseline Analysis: Is Fine-Tuning Needed?

## Context

This analysis uses the prompt-test baseline artifacts generated under:

- `outputs/evaluation/prompt_test/prompt_test_results.json`
- `outputs/evaluation/prompt_test/prompt_test_summary.md`
- `outputs/evaluation/baseline/baseline_results.json`
- `outputs/evaluation/baseline/baseline_report.md`

Behavior contract reference:

- `docs/behavior_spec.md`

## Observed Baseline Results

From `prompt_test_results.json`:

- total prompts: `5`
- passes: `0`
- failures: `5`
- pass rate: `0.0000`
- behavior-spec verdict: **No**, base model did not satisfy Behavior Spec thresholds.

From `baseline_results.json`:

- pass rate: `0.0000`
- deterministic mean: `0.6167`
- judge overall mean: `0.2800`

Failure pattern (qualitative):

- outputs did not consistently follow required structured sections/order (`B7`)
- weak structured diagnosis cues (`B1`)
- weak analogy/mapping completeness (`B3`)
- low judge scores for instruction-following/completeness

## Fine-Tuning Decision

**Fine-tuning is justified.**

Reasoning:

1. Prompting alone failed configured pass criteria on all evaluated prompts.
2. The main gaps are behavioral-format reliability and pedagogy structure, which are exactly the target of instruction tuning.
3. Deterministic failures (`B1/B3/B7`) indicate systematic behavior mismatch, not isolated prompt misses.

## Assumptions and Limitations

1. Current held-out set is a **placeholder benchmark** (`datasets/eval/heldout_benchmark.jsonl`) derived from internal golden data for integration testing.
2. This placeholder is not a leakage-safe final research benchmark.
3. The baseline run used a bounded subset (`--limit 5`) for practical runtime in the current environment.

## Recommendation

Proceed to fine-tuning pipeline initialization (LoRA/Unsloth) and rerun baseline on the full curated held-out benchmark once finalized.
