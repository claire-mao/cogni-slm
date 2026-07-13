# Cogni AP Tutor Architecture

## End-to-End Flow
1. Collect AP/fallacy source text.
2. Build labeling candidates.
3. Run teacher labeling with strict AP tutor prompt/schema.
4. Filter, deduplicate, and split to train/validation/test.
5. Fine-tune with QLoRA (Colab GPU).
6. Evaluate base vs tuned on held-out benchmark.
7. Analyze failures and iterate data.

## Components
- `datasets/raw/`: AP docs + public fallacy corpora.
- `datasets/training_candidates/`: label-ready examples.
- `datasets/sft_ap_tutor/`: filtered/deduped split artifacts for training.
- `teacher_prompts/`: AP tutor teacher prompt + schema.
- `src/teacher/`: labeling runner and provider stack.
- `src/training/`: QLoRA experiment runner.
- `src/evaluation/`: deterministic checks + LLM judge.
- `outputs/`: experiment and evaluation artifacts.

## Invariants
- Behavior-spec contract is authoritative.
- Held-out benchmark is never used for training.
- Every dataset version has summary stats and provenance metadata.
