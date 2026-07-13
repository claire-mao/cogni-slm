# Experimentation Plan v1

Date: 2026-07-09

## Completed Now

1. Populated 100-example gold dataset:
   - `datasets/gold/gold_v1.jsonl` (100 rows)
   - `datasets/gold/v1/gold_dataset.jsonl` (100 rows)
   - `datasets/gold/v1/manifest.json`
   - `datasets/gold/v1/checksums.json`
2. Prepared pilot slice:
   - `datasets/gold/pilot20_v1.jsonl` (20 rows)
   - `datasets/gold/pilot20_v1_manifest.json`
3. Added live pilot config artifacts:
   - `configs/teacher/teacher_pilot_live_v1.json`
   - `configs/teacher/teacher_rounds_pilot20_v2.json`
   - `configs/teacher_pilot20_live/teacher_validation_master.json`
4. Added QLoRA experiment configs:
   - `configs/training/experiments/qlora_phase1_qwen3_4b_v1.json`
   - `configs/training/experiments/qlora_phase2_qwen3_8b_v1.json`

## Current Blockers

1. Live teacher pilot is blocked by missing provider credentials:
   - `.env` is missing.
   - Required keys: `TFY_API_KEY` (or `TRUEFOUNDRY_API_KEY`), `TFY_BASE_URL` (or `TRUEFOUNDRY_BASE_URL`), `PRIMARY_TEACHER_MODEL`, `VERIFIER_MODEL`, `SECONDARY_MODEL`.
2. QLoRA training is blocked by unavailable accelerator:
   - `torch.cuda.is_available() == False`
   - Runtime also reports no Metal device in this headless session.

## Execution Order (Once Unblocked)

1. **Run live teacher pilot (20 examples)**
   - Command documented in `docs/reports/teacher_pilot_live.md`.

2. **Select production teacher stack based on measured results**
   - Benchmark and leaderboard commands documented in `docs/reports/teacher_pilot_live.md`.
   - Selection rule:
     - Primary objective: quality metrics (`QWK`, `MAE`, rubric adherence, fallacy F1).
     - Secondary objective: JSON validity and hallucination rate.
     - Tiebreakers: latency and cost.

3. **Generate first real SFT dataset**
   - Use winning teacher outputs (non-dry-run) as `--teacher-outputs-path`.
```bash
python3 -m src.data.build_sft_dataset \
  --input-jsonl datasets/gold/gold_v1.jsonl \
  --teacher-outputs-path outputs/teacher_runs/teacher-pilot20-live-v1/responses.jsonl \
  --output-root datasets/sft \
  --teacher-model-id <winning_teacher_model_id> \
  --inference-mode precomputed \
  --schema-path teacher_prompts/output_schema.json \
  --quality-threshold 0.8 \
  --confidence-threshold 0.6 \
  --export-formats alpaca,sharegpt,chatml,huggingface
```

4. **Train Qwen3-4B-Instruct with QLoRA**
```bash
python3 -m src.training.train_experiment \
  --dataset-root datasets/sft \
  --experiments-dir configs/training/experiments \
  --manifest-path configs/training/experiments/manifest.json \
  --base-config configs/training/qlora_default.json \
  --output-root outputs/training_runs/qwen3_4b_v1 \
  --tracking-root outputs/experiments \
  --phase-id phase1_qwen3_4b_validation \
  --max-runs 1 \
  --seed-mode base \
  --do-train
```

5. **Scale to Qwen3-8B-Instruct after validation gate**
   - Validation gate:
     - Fine-tuned 4B improves vs base on `QWK` and `MAE`.
     - JSON validity remains >= 0.98.
     - Hallucination rate does not regress materially.
```bash
python3 -m src.training.train_experiment \
  --dataset-root datasets/sft \
  --experiments-dir configs/training/experiments \
  --manifest-path configs/training/experiments/manifest.json \
  --base-config configs/training/qlora_default.json \
  --output-root outputs/training_runs/qwen3_8b_v1 \
  --tracking-root outputs/experiments \
  --phase-id phase2_qwen3_8b_scale \
  --max-runs 1 \
  --seed-mode base \
  --do-train
```

## Notes

- This plan intentionally keeps deterministic settings (`temperature=0.0`, fixed seed).
- Dataset and model lineage should be tracked in `outputs/experiments/` for every run.
