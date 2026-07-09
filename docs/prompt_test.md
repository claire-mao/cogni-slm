# Cogni Prompt-Only Baseline Test

## Objective
Determine whether the untuned base model (`Qwen/Qwen3-1.7B-Instruct`) can satisfy the full Cogni Behavior Specification (`B1-B7`, `P1-P5`) on the held-out benchmark using prompting alone.

This prompt-only run is the official pre-fine-tuning baseline. All later tuned-model gains are compared against this protocol.

## Experimental Setup
- Experiment type: prompt-only, no fine-tuning.
- Evaluation split: `heldout_benchmark` only.
- Inference mode: deterministic by default (`temperature=0.0`) to isolate prompt-following behavior.
- Repeated generations: default `2` runs per example to measure consistency.
- Evaluators:
  - Deterministic checks (`B1-B7`, `P1-P5`) from `src/evaluation/deterministic_checks.py`
  - LLM judge rubrics from `src/evaluation/llm_judge.py`

Reference runner:
- `scripts/run_prompt_test.py`

Default command:
```bash
python scripts/run_prompt_test.py --output-dir outputs/evaluation/prompt_test
```

## Base Model
- Model ID: `Qwen/Qwen3-1.7B-Instruct`
- Role: untuned baseline model only.
- No adapter loading, no fine-tune checkpoints, no weight updates.

## Prompt Template
Prompting enforces the behavior contract and deterministic section order.

System instruction summary:
- You are Cogni, an educational logical-fallacy tutor.
- Follow B1-B7 and avoid P1-P5.
- Return all required sections in fixed order.

User template fields:
- `argument_text`
- `task_mode`
- `difficulty_level`
- optional `context`

Required output sections (in order):
1. `fallacy_hypothesis`
2. `reasoning_diagnosis`
3. `analogy`
4. `repair`
5. `confidence_note`

Within `analogy`, the model must include:
- `source_scenario`
- `mapping`
- `limits`

## Held-Out Benchmark
Source:
- `datasets/eval/heldout_benchmark.jsonl`

Policy:
- Benchmark file is read-only for this experiment.
- No prompt or rubric tuning against held-out outcomes.
- Every held-out example is evaluated; optional `--limit` is only for local smoke runs and does not produce official baseline results.

## Metrics
The baseline run computes:

1. Behavior Spec adherence
- Aggregate pass rate across deterministic checks (`B` and `P` checks).

2. Per-step adherence (`B1-B7`)
- Step-level pass rates aggregated over all evaluated outputs.

3. Robustness
- Adversarial-only robustness score combining deterministic robustness checks and judge robustness rubric.

4. Consistency
- Repeat-run stability score across repeated generations per example.

5. Overall pass rate
- Fraction of examples meeting all per-example pass criteria.

Additional diagnostics:
- Fallacy accuracy (`primary` + `acceptable alternatives`)
- Judge dimension means
- Example-level failure reasons

## Pass/Fail Criteria
Official baseline pass criteria are intentionally strict and configurable in the script.

Default thresholds:
- `behavior_spec_adherence >= 0.90`
- `semantic_judge_mean >= 0.70`
- `consistency >= 0.80`
- `adversarial_robustness >= 0.80` (adversarial examples only)
- Each behavior step `B1-B7 >= 0.85`

Project-level outcome:
- The prompt-only baseline is considered **passing** only if overall pass rate reaches `0.80` or higher.
- Otherwise, the run is recorded as baseline evidence that prompting alone is insufficient.

## Output Artifacts
The script writes to `outputs/evaluation/prompt_test/` when run with `--output-dir outputs/evaluation/prompt_test`:
- `prompt_test_results.json`: machine-readable baseline verdict and examples
- `prompt_test_summary.md`: human-readable prompt-test summary
- `report.md`: human-readable experiment report
- `summary.json`: machine-readable aggregate metrics and thresholds
- `raw_predictions.jsonl`: per-example per-run outputs, checks, and judge scores

## Reproducibility Controls
The baseline report captures:
- model ID
- benchmark path
- prompt template hash
- decoding config
- repeat count
- run timestamp
- pass/fail thresholds

This metadata is required for later base-vs-tuned comparison integrity.
