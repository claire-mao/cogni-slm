# SFT Dataset Builder

Implemented final supervised fine-tuning dataset builder at:

- `/Users/clairemao/Documents/cogni-slm/src/data/build_sft_dataset.py`

The builder is deterministic and API-free. It consumes precomputed teacher outputs and exports
SFT-ready datasets under `datasets/sft/` in multiple training formats.

## Scope

- Input: teacher outputs (`JSONL` file or directory of `JSONL` files)
- Output root: `datasets/sft/`
- Supported formats:
  - Alpaca
  - ShareGPT
  - ChatML
  - Hugging Face JSONL
- No training execution

## Pipeline

The builder composes two stages:

1. Canonical label pipeline (reuses `src.teacher.generate_labels`):
   - dataset
   - teacher inference (precomputed or mock mode)
   - validation
   - quality filter
   - JSON schema validation
   - confidence filter
   - canonical split export
2. Format conversion:
   - canonical rows -> Alpaca / ShareGPT / ChatML / Hugging Face rows

## Input Contract

### Dataset rows (`--input-jsonl`)

Each row should include:

- `example_id`
- `prompt`
- `essay`
- optional: `score`, `split`, `source`, `license`, `metadata`

### Teacher output rows (`--teacher-outputs-path`)

Each row should include:

- `model_id` (or `model`)
- `example_id`
- `output` (or other accepted output payload forms from `src.teacher.io`)
- optional: `json_valid`, `latency_ms`, token usage, `cost_usd`

## Output Layout

The builder writes:

- `datasets/sft/manifest.json` (canonical pipeline manifest)
- `datasets/sft/sft_build_manifest.json` (final build manifest)
- `datasets/sft/train/data.jsonl`
- `datasets/sft/validation/data.jsonl`
- `datasets/sft/test/data.jsonl`
- `datasets/sft/formats/alpaca/{train,validation,test}.jsonl`
- `datasets/sft/formats/sharegpt/{train,validation,test}.jsonl`
- `datasets/sft/formats/chatml/{train,validation,test}.jsonl`
- `datasets/sft/formats/huggingface/{train,validation,test}.jsonl`

## Format Mapping

- Alpaca row:
  - `id`, `instruction`, `input`, `output`, `metadata`
- ShareGPT row:
  - `id`, `conversations` (`human` -> `gpt`), `metadata`
- ChatML row:
  - `id`, `messages` (`system`, `user`, `assistant`), `metadata`
- Hugging Face row:
  - `id`, `instruction`, `input`, `output`, `messages`, `text`, `metadata`

## CLI

```bash
python3 -m src.data.build_sft_dataset \
  --input-jsonl datasets/gold/gold_v1.jsonl \
  --teacher-outputs-path <predictions.jsonl-or-dir> \
  --output-root datasets/sft \
  --teacher-model-id gpt-5 \
  --inference-mode precomputed \
  --export-formats alpaca,sharegpt,chatml,huggingface
```

`--inference-mode mock` is available for deterministic pipeline tests without provider calls.
