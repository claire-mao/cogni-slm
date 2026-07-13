# AP Tutor Release Runbook

Run these gates in order. Do not publish or train on the test split.

## 1. Finish and compile labeling

Wait for the active Colab labeling job to finish, then run the compilation cell in
`notebooks/label_compile_ap_tutor_colab_clean.ipynb`. Copy the resulting
`production_v1` folder into `datasets/sft_ap_tutor/production_v1` when syncing locally.

## 2. Validate final splits

```bash
python3 scripts/validate_ap_sft_ready.py \
  --dataset-root datasets/sft_ap_tutor/production_v1
```

## 3. Train on A100

Open `notebooks/train_ap_tutor_production_colab.ipynb`, select A100, and run all cells.
The notebook uses only train and validation splits and writes checkpoints, adapter,
and merged model artifacts to Google Drive.

## 4. Evaluate and analyze failures

Generate base and tuned predictions for the untouched public held-out benchmark, then
run:

```bash
python3 scripts/generate_ap_model_predictions.py \
  --model Qwen/Qwen3-1.7B \
  --benchmark datasets/eval/heldout_benchmark_public_v1.jsonl \
  --output outputs/evaluation/base/raw_predictions.jsonl \
  --load-in-4bit

python3 scripts/generate_ap_model_predictions.py \
  --model models/merged/ap_tutor_qwen3_1_7b_v1 \
  --benchmark datasets/eval/heldout_benchmark_public_v1.jsonl \
  --output outputs/evaluation/tuned/raw_predictions.jsonl \
  --load-in-4bit

python3 scripts/evaluate_ap_prompt_test_outputs.py \
  --raw-predictions outputs/evaluation/tuned/raw_predictions.jsonl \
  --benchmark datasets/eval/heldout_benchmark_public_v1.jsonl \
  --output-dir outputs/evaluation/tuned
```

Compare the resulting summary with the existing base summary. Do not release unless
strict behavior adherence and primary-fallacy accuracy improve. Use failed examples
to revise training data, retrain from the frozen base model, and rerun the same test.

## 5. License gate

Review every source in `configs/release/source_licenses.json`, record its exact license
and evidence URL, and change `status` to `approved` only with supporting evidence.

```bash
python3 scripts/audit_ap_release_licenses.py \
  --dataset-root datasets/sft_ap_tutor/production_v1
```

## 6. Hugging Face dry run and publish

```bash
python3 scripts/publish_ap_tutor_hf.py \
  --dataset-repo YOUR_USER/cogni-ap-tutor-dataset \
  --model-repo YOUR_USER/cogni-ap-tutor-qwen3-1.7b
```

After reviewing the plan and clearing the license gate, rerun with `--publish`.

## 7. Commit

Run lint, tests, CLI smoke checks, inspect `git diff`, and commit source/config/docs.
Keep credentials, raw private sources, model weights, caches, and generated outputs out
of Git.
