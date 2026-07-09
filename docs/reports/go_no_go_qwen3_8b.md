# Go/No-Go Decision for Qwen3-8B Scale-Up

Date: 2026-07-09

## Decision

**NO-GO** for scaling to `Qwen/Qwen3-8B-Instruct` at this time.

## Basis of Analysis

Primary run analyzed:

- `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/run_summary.json`
- `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/00001_p1_qwen3_4b_baseline/run_manifest.json`
- `outputs/experiments/20260709T201547Z-p1_qwen3_4b_baseline/manifest.json`

Observed result on 2026-07-09:

- run status: `failed`
- error: `AssertionError: Torch not compiled with CUDA enabled`
- GPU availability: `false` (`count=0`)
- checkpoints/adapters/merged model: not produced
- eval artifacts for trained 4B model: not produced

## Base vs Fine-Tuned Comparison (Qwen3-4B)

There is no valid base-vs-fine-tuned evaluation for Qwen3-4B because training never completed.

| Dimension | Base Model (Qwen3-4B) | Fine-tuned Model (Qwen3-4B) | Evidence Quality |
|---|---|---|---|
| Rubric adherence | Not measured | Not measured | Missing (no 4B eval outputs) |
| Reasoning quality | Not measured | Not measured | Missing (no 4B eval outputs) |
| Hallucination rate | Not measured | Not measured | Missing (no 4B eval outputs) |
| Calibration | Not measured | Not measured | Missing (no 4B eval outputs) |
| Latency | Not measured (model eval) | Not measured (model eval) | Missing (only failure runtime exists) |

Notes:

- The only recorded runtime (`~3.39s`) is failure time before training/evaluation, not model inference latency.
- Existing harness comparisons in `docs/reports/model_v1_results.md` are dry-run artifacts and not Qwen3-4B fine-tuning evidence.

## Pipeline Readiness for 8B

### What is ready

- Experiment config exists for 8B: `configs/training/experiments/qlora_phase2_qwen3_8b_v1.json`
- Dataset versioning is in place (`datasets/sft/versions/sft_prod_v1_20260709T201322Z`)
- Experiment tracking works (manifest/events/metrics recorded)
- Dashboard update path works (`docs/reports/dashboard.md` updated)

### What is not ready

- No working accelerator runtime for Unsloth QLoRA in this environment.
- 4B training path is unvalidated end-to-end (train -> checkpoint -> adapter -> merge -> eval).
- No empirical quality deltas (base vs tuned) for requested educational metrics.

## Why Evidence Does Not Support Scaling

Scaling to 8B increases cost and runtime, but current evidence does not establish that the 4B pipeline can complete one successful training run, let alone deliver quality gains on rubric adherence, reasoning quality, hallucination reduction, calibration, or latency tradeoffs. The blocker is foundational infrastructure, not model capacity.

## Required Gates Before GO

1. Complete one successful Qwen3-4B run with generated artifacts:
   - checkpoints
   - adapter
   - merged model
   - eval metrics
2. Produce Qwen3-4B base vs fine-tuned comparison on target metrics:
   - rubric adherence
   - reasoning quality
   - hallucination rate
   - calibration
   - latency
3. Show non-regression or improvement thresholds on the gold/pilot evaluation suite.
4. Confirm resumability and reproducibility with one rerun (same config, deterministic metadata, stable outputs).

After these are satisfied, rerun go/no-go for 8B using measured deltas rather than infrastructure checks.
