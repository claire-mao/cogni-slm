# Final SFT Dataset Build

Date (UTC): 2026-07-09T20:13:22Z

## Status

Production SFT export pipeline completed and wrote canonical + multi-format datasets under `datasets/sft/`.

## Input Artifacts Used

- Teacher inputs: `outputs/teacher_runs/validated_inputs/validated_teacher_inputs_pilot24.jsonl`
- Validated teacher outputs: `outputs/teacher_runs/validated_inputs/validated_teacher_outputs_gpt5_pilot24.jsonl`
- Teacher model id: `gpt-5`
- Schema: `teacher_prompts/output_schema.json`
- Inference mode: `precomputed`

## Build Command

```bash
python3 -m src.data.build_sft_dataset \
  --input-jsonl outputs/teacher_runs/validated_inputs/validated_teacher_inputs_pilot24.jsonl \
  --teacher-outputs-path outputs/teacher_runs/validated_inputs/validated_teacher_outputs_gpt5_pilot24.jsonl \
  --output-root datasets/sft \
  --teacher-model-id gpt-5 \
  --inference-mode precomputed \
  --schema-path teacher_prompts/output_schema.json \
  --quality-threshold 0.0 \
  --confidence-threshold 0.0 \
  --strict-source-split \
  --export-formats alpaca,sharegpt,chatml,huggingface
```

## Pipeline Outcome

- input examples: `24`
- predictions available: `24`
- after validation: `24`
- after schema validation: `24`
- after quality filter: `24`
- after confidence filter: `24`

## Exported Datasets

- Canonical: `datasets/sft/train/data.jsonl` (`24`)
- Hugging Face: `datasets/sft/formats/huggingface/train.jsonl` (`24`)
- Alpaca: `datasets/sft/formats/alpaca/train.jsonl` (`24`)
- ShareGPT: `datasets/sft/formats/sharegpt/train.jsonl` (`24`)
- ChatML: `datasets/sft/formats/chatml/train.jsonl` (`24`)
- Validation split rows: `0`
- Test split rows: `0`

## Versioning

- Dataset version id: `sft_prod_v1_20260709T201322Z`
- Version manifest: `datasets/sft/version_manifest.json`
- Version snapshot: `datasets/sft/versions/sft_prod_v1_20260709T201322Z/`

## Checksums

- Root checksum manifest: `datasets/sft/checksums.json`
- Snapshot checksum manifest: `datasets/sft/versions/sft_prod_v1_20260709T201322Z/checksums.json`

Selected file hashes:

- `datasets/sft/train/data.jsonl`: `e029766998f9dbd6074fcb053eccd7799d66ea7f3331ee5de46a85e7780838e2`
- `datasets/sft/formats/huggingface/train.jsonl`: `78f9fd4325eaf40ee6dde5e73e6bf183d727acc724fa42303762c705397b7083`
- `datasets/sft/formats/alpaca/train.jsonl`: `aa001dafcd0ccc11715d673519c3431543361f9249a57d6632e2f4ab9e277790`
- `datasets/sft/formats/sharegpt/train.jsonl`: `a62e33fdb99ee40dffb283f855aa64c781323b220db136baac5c84d979ef6ee0`
- `datasets/sft/formats/chatml/train.jsonl`: `027109157991dd2de8ee4312b48cd49bed5a675e56040f1b223eccd20ab429b1`

## Important Caveat

This build uses the currently available validated teacher artifact set (`pilot24`) and not a completed live production teacher run over `datasets/training/`.

To produce the full production SFT dataset, rerun the same pipeline with validated outputs from the live production labeling run once provider credentials are configured and the production run completes.
