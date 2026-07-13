# Final AP Tutor Results

## Outcome

The project completed end-to-end fine-tuning and evaluation for a Qwen3-1.7B AP
English Language logical-fallacy tutor. The tuned model learned the required
seven-section tutoring protocol reliably. Reasoning quality remains less consistent
than format adherence, so the model should be presented as an experimental tutor
rather than an authoritative grader.

## Dataset

- Teacher-labeled candidates: 15,000
- Valid compiled examples: 14,999
- Train: 13,463
- Validation: 780
- Test: 756 (kept out of training)
- Trainer examples after preprocessing: 13,421

The semantic audit found 1,898 distinct primary-fallacy label spellings in the
training split, including 1,701 spellings occurring fewer than five times. This
fragmented label space is the leading identified data-quality limitation.

## Training

- Base model: Qwen/Qwen3-1.7B
- Method: QLoRA with Unsloth
- Hardware: one A100 GPU in Google Colab
- Steps: 840
- Effective batch size: 32
- Trainable parameters: 34,865,152 / 1,755,440,128 (1.99%)
- Final aggregate training loss: 1.2817
- Validation loss: 1.3682 at step 100, improving to 1.2516 at step 840
- Runtime: 5,739.9 seconds

Saved Google Drive artifacts:

- `MyDrive/cogni/models/ap_tutor_qwen3_1_7b_v1/adapter_checkpoints/`
- `MyDrive/cogni/models/ap_tutor_qwen3_1_7b_v1/adapter`
- `MyDrive/cogni/models/ap_tutor_qwen3_1_7b_v1/merged_16bit`
- `MyDrive/cogni/models/ap_tutor_qwen3_1_7b_v1/training_metrics.json`

## Held-Out Evaluation

Both the base and tuned models generated responses for all 756 untouched test
examples. Deterministic scoring measured adherence to the seven-section behavior
contract.

| Metric | Base | Tuned | Delta |
|---|---:|---:|---:|
| Strict behavior pass rate | 0.0% | 99.3% | +99.3 pp |
| Each required section present | 0.0% | 99.7% | +99.7 pp |
| Correct section order | 0.0% | 99.7% | +99.7 pp |
| Transfer check without revealed answer | 0.0% | 99.7% | +99.7 pp |
| Exactly one final reflective question | 0.0% | 99.3% | +99.3 pp |

The tuned model passed 751 of 756 strict behavior checks. Manual inspection found
two long-input generation failures, one genuine multiple-reflective-question
failure, and two deterministic false positives caused by question marks inside
quoted source text.

## Reasoning Quality Review

An independent Claude Opus 4.8 review of all 756 tuned responses measured 47.1%
primary-fallacy accuracy. This result is materially weaker than the protocol score
and is the model's principal limitation. Error analysis found frequent confusion
between named fallacies and `No clear fallacy`, along with weaker explanations,
analogies, and transfer items.

## Decision

A future improvement should canonicalize the label ontology, audit teacher-label
correctness, balance hard `No clear fallacy` contrasts, preserve the generation
suffix when truncating long inputs, and rerun the frozen 756-example evaluation.

The current adapter and merged model are suitable as experimental artifacts showing
successful protocol tuning. They are not suitable as authoritative educational
graders because semantic accuracy remains below an acceptable threshold.

## Release and Licensing

The dataset and model remain private/internal. Several incorporated sources are
marked `blocked_no_license` in `configs/release/source_licenses.json`. Public
Hugging Face publication is prohibited unless permissions are obtained or the
dataset is rebuilt and the model retrained using approved sources only.

## Drive Evidence

- Structural comparison: `MyDrive/cogni/evaluation/ap_tutor_base_vs_tuned_v1/comparison.json`
- Base predictions: `MyDrive/cogni/evaluation/ap_tutor_base_vs_tuned_v1/base_predictions.jsonl`
- Tuned predictions: `MyDrive/cogni/evaluation/ap_tutor_base_vs_tuned_v1/tuned_predictions.jsonl`
- Semantic summary: `MyDrive/cogni/evaluation/ap_tutor_semantic_judge_v1/semantic_summary.json`
- Semantic judgments: `MyDrive/cogni/evaluation/ap_tutor_semantic_judge_v1/semantic_judgments.jsonl`
- Error analysis: `MyDrive/cogni/evaluation/ap_tutor_semantic_judge_v1/semantic_error_analysis.json`
