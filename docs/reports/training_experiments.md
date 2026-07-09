# QLoRA Experiment Matrix

## Scope

Design the complete QLoRA experiment matrix to compare:

- LoRA ranks
- learning rates
- epochs
- batch sizes
- sequence lengths
- warmup
- packing
- optimizer

No training was executed.

## Generated Configs

- `configs/training/experiments/qlora_matrix_v1.json`
- `configs/training/experiments/qlora_phase1_ofat_v1.json`
- `configs/training/experiments/qlora_phase2_interactions_v1.json`
- `configs/training/experiments/qlora_phase3_full_factorial_v1.json`
- `configs/training/experiments/manifest.json`

## Matrix Definition

Base config:

- `configs/training/qlora_default.json`

Hyperparameter axes and levels:

- `lora_rank`: `8, 16, 32, 64`
- `learning_rate`: `5e-5, 1e-4, 2e-4, 3e-4`
- `num_train_epochs`: `1.0, 2.0, 3.0`
- `batch_profile_id`: `bsz16, bsz32, bsz64`
- `max_seq_length`: `1024, 1536, 2048, 3072`
- `warmup_ratio`: `0.0, 0.03, 0.06, 0.10`
- `packing`: `false, true`
- `optimizer`: `adamw_torch, adamw_torch_fused, paged_adamw_8bit`

Batch profile mapping:

- `bsz16`: per-device train `2`, grad accumulation `8`, effective batch `16`
- `bsz32`: per-device train `4`, grad accumulation `8`, effective batch `32`
- `bsz64`: per-device train `4`, grad accumulation `16`, effective batch `64`

LoRA policy:

- `lora_alpha = lora_rank`
- `lora_dropout = 0.0`

## Run Counts

Full-factorial combinations:

- `4 * 4 * 3 * 3 * 4 * 4 * 2 * 3 = 13,824`

With three repeat seeds (`42, 314, 2718`):

- `41,472` planned runs

## Phase Structure

Phase 1 (`qlora_phase1_ofat_v1.json`):

- OFAT screening around baseline
- `20` runs

Phase 2 (`qlora_phase2_interactions_v1.json`):

- Block A: rank x learning rate x sequence length x batch profile
- Block B: epochs x warmup x packing x optimizer
- `264` runs total

Phase 3 (`qlora_phase3_full_factorial_v1.json`):

- Exhaustive matrix over all axes
- `13,824` runs
- Sharded by sequence length and packing (`8` shards x `1,728` combinations)

## Notes

- This deliverable is design-only and does not launch training.
- Matrix configs include packing and optimizer as first-class variables for QLoRA comparison experiments.
- Before execution, training runtime should expose `packing` and `optimizer` as configurable fields.
