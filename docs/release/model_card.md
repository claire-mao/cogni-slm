---
language: en
base_model: Qwen/Qwen3-1.7B
pipeline_tag: text-generation
---

# Cogni AP Logical-Fallacy Tutor

QLoRA fine-tune of Qwen3-1.7B for a fixed seven-section AP English Language
logical-fallacy tutoring behavior.

## Intended use

Educational practice and research on structured reasoning feedback. The model should
not be used as an authoritative grader or as a replacement for teacher judgment.

## Training

The adapter was trained with response-only loss on 13,421 preprocessed examples from
the 13,463-example training split. QLoRA trained 34,865,152 parameters (1.99%) for
840 optimization steps on one A100 GPU. Validation loss improved from 1.3682 at
step 100 to 1.2516 at completion.

## Evaluation

On 756 untouched test examples, strict seven-section adherence improved from 0.0%
for the base model to 99.3% for the tuned model. Independent quality review found
that fallacy selection and explanation remain less reliable than protocol adherence.
See `docs/reports/final_ap_tutor_results.md`.

## Limitations

The model reliably follows the requested protocol but frequently misidentifies the
primary fallacy, gives an incorrect explanation, or produces weak analogies and
transfer items. It must not be used as an authoritative grader. Teacher-generated
supervision contains a highly fragmented label vocabulary and may propagate
source-model bias.

## Release status

Private/internal only. Multiple incorporated sources have no verified redistribution
license, so neither the dataset nor this derivative model is approved for public
release.
