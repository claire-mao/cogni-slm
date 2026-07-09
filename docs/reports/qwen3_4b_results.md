# Qwen3-4B QLoRA Phase 1 Results

Date (UTC): 2026-07-09

## Run Summary

- status: `FAILED`
- model: `Qwen/Qwen3-4B-Instruct`
- experiment config: `configs/training/experiments/qlora_phase1_qwen3_4b_v1.json`
- selected run: `p1_qwen3_4b_baseline`
- plan id: `qwen3_4b_prod_v1_20260709T201547Z`
- dataset root used: `datasets/sft/versions/sft_prod_v1_20260709T201322Z`
- dataset version: `sft_prod_v1_20260709T201322Z`
- teacher lineage: `teacher_version=gpt-5`, `prompt_version=production_teacher_v1`

## What Was Executed

Executed training runner with training enabled and one filtered run:

```bash
UNSLOTH_FORCE_GPU_PATH=1 UNSLOTH_ALLOW_CPU=1 \
python3 -m src.training.train_experiment \
  --dataset-root datasets/sft/versions/sft_prod_v1_20260709T201322Z \
  --experiments-dir configs/training/experiments \
  --phase-id phase1_qwen3_4b_validation \
  --run-filter p1_qwen3_4b_baseline \
  --max-runs 1 \
  --do-train \
  --plan-id qwen3_4b_prod_v1_20260709T201547Z
```

## Failure Cause

Training failed before model initialization completed.

- error: `AssertionError: Torch not compiled with CUDA enabled`
- source: `unsloth/_gpu_init.py` during CUDA capability checks
- environment state: `torch.cuda.is_available() = False`, GPU count `0`

## Artifact Results

### Created

- plan manifest: `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/plan_manifest.json`
- run summary: `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/run_summary.json`
- run results JSONL: `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/run_results.jsonl`
- run manifest (failed): `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/00001_p1_qwen3_4b_baseline/run_manifest.json`
- resolved run config: `outputs/training_experiments/qwen3_4b_prod_v1_20260709T201547Z/00001_p1_qwen3_4b_baseline/resolved_config.json`

Experiment tracking was recorded:

- tracker manifest: `outputs/experiments/20260709T201547Z-p1_qwen3_4b_baseline/manifest.json`
- tracker events: `outputs/experiments/20260709T201547Z-p1_qwen3_4b_baseline/events.jsonl`
- tracker metrics: `outputs/experiments/20260709T201547Z-p1_qwen3_4b_baseline/evaluation_metrics.json`
- tracker training config: `outputs/experiments/20260709T201547Z-p1_qwen3_4b_baseline/training_config.json`

### Not Produced (due early failure)

- checkpoints: not created
- adapter weights: not created
- merged model: not created
- eval/test metrics files: not created

## Automatic Requirements Status

- track experiment: `DONE`
- save checkpoints: `BLOCKED (no CUDA)`
- save adapters: `BLOCKED (no CUDA)`
- merge adapter: `BLOCKED (no CUDA)`
- evaluate: `BLOCKED (no CUDA)`
- record metrics: `DONE` (failure metrics + runtime logged)
- update dashboard: `DONE`

Dashboard was rebuilt at:

- `docs/reports/dashboard.md`

## Recommended Unblock

Run this same experiment on a CUDA-enabled machine (or environment with supported accelerator + compatible torch/unsloth build), then rerun the same command and plan id policy for true production training artifacts.
