# Unsloth Training Pipeline

This directory contains a complete local Unsloth + QLoRA training pipeline.

## Included Components

- QLoRA configuration: `training/config.py` + `configs/training/qlora_default.json`
- Backward-compatible legacy config path remains supported: `training/configs/qlora_default.json`
- Tokenizer/model loading: `training/model.py`
- Dataset loading/prep: `training/data.py`
- Training arguments: `training/pipeline.py`
- Checkpoint saving: `training/pipeline.py` (`checkpoint_dir`)
- Evaluation callback: `training/callbacks.py`

## Entry Point

Initialize (no training):

```bash
python -m training.run
```

Explicitly start training:

```bash
python -m training.run --do-train
```

## Notes

- By default, this pipeline only initializes and writes run metadata.
- Training only starts when `--do-train` is provided.
