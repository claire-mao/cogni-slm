# Production SFT Build Report

- build_time_utc: `2026-07-09T20:13:22.804334Z`
- input_file: `outputs/teacher_runs/validated_inputs/validated_teacher_inputs_pilot24.jsonl`
- teacher_outputs_file: `outputs/teacher_runs/validated_inputs/validated_teacher_outputs_gpt5_pilot24.jsonl`
- output_root: `datasets/sft`
- inference_mode: `precomputed`
- teacher_model_id: `gpt-5`

## Build Status

- Canonical SFT pipeline completed successfully.
- Multi-format exports completed successfully.

## Filtering and Validation

- input_examples: `24`
- predictions_available: `24`
- after_validation: `24`
- after_schema_validation: `24`
- after_quality_filter: `24`
- after_confidence_filter: `24`
- quality_threshold: `0.0`
- confidence_threshold: `0.0`

## Split Counts

- train: `24`
- validation: `0`
- test: `0`

## Exported Formats

### alpaca

- train: `24` -> `datasets/sft/formats/alpaca/train.jsonl`
- validation: `0` -> `datasets/sft/formats/alpaca/validation.jsonl`
- test: `0` -> `datasets/sft/formats/alpaca/test.jsonl`

### sharegpt

- train: `24` -> `datasets/sft/formats/sharegpt/train.jsonl`
- validation: `0` -> `datasets/sft/formats/sharegpt/validation.jsonl`
- test: `0` -> `datasets/sft/formats/sharegpt/test.jsonl`

### chatml

- train: `24` -> `datasets/sft/formats/chatml/train.jsonl`
- validation: `0` -> `datasets/sft/formats/chatml/validation.jsonl`
- test: `0` -> `datasets/sft/formats/chatml/test.jsonl`

### huggingface

- train: `24` -> `datasets/sft/formats/huggingface/train.jsonl`
- validation: `0` -> `datasets/sft/formats/huggingface/validation.jsonl`
- test: `0` -> `datasets/sft/formats/huggingface/test.jsonl`
