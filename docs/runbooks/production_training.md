# Production AP Tutor Training Runbook

## 1. Build the 15,000-row labeling batch

```bash
python3 scripts/build_ap_tutor_production_batch.py
```

## 2. Run or resume teacher labeling

The canonical AP tutor path uses direct strict structured output. It intentionally
does not use the legacy essay-grading fields (`score`, `confidence`,
`rubric_analysis`).

```bash
TEACHER_API_KEY="..." python3 scripts/run_direct_ap_labeling.py \
  --output outputs/teacher_runs/direct_gemini_15k.jsonl \
  --model gemini-group/gemini-3.1-pro \
  --workers 32
```

The run is resumable. Do not delete its response or checkpoint files.

## 3. Freeze the training dataset

```bash
python3 scripts/build_ap_tutor_sft_from_teacher.py \
  --responses outputs/teacher_runs/direct_gemini_15k.jsonl \
  --output-root datasets/sft_ap_tutor/production_v1

python3 scripts/validate_ap_sft_ready.py \
  --dataset-root datasets/sft_ap_tutor/production_v1
```

This command fails closed unless at least 10,000 examples pass all quality gates.
The test split is produced but excluded from training.

## 4. Train in Colab

Upload `datasets/sft_ap_tutor/production_v1` to
`MyDrive/cogni/production_v1`, open
`notebooks/train_ap_tutor_production_colab.ipynb`, choose a GPU runtime, and run all cells.

The notebook trains Qwen3-1.7B for two epochs with 4-bit QLoRA and saves both the
adapter and merged 16-bit model to Google Drive.
