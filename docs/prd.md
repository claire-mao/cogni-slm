# Cogni PRD

## Problem Statement
AP Language students often memorize fallacy labels but fail to transfer reasoning skills to unfamiliar arguments. Existing LLMs are inconsistent tutors and frequently skip instructional steps.

## Behavior Spec
See `docs/behavior_spec.md`. The model must execute a strict seven-step instructional sequence with complete pass/fail adherence.

## Dataset Plan
- Target size: 2,000-3,000 supervised examples.
- Current prepared candidate input: AP + public fallacy blend.
- Coverage requirements:
  - major AP logical fallacies
  - no-fallacy examples
  - ambiguous cases
  - adversarial prompts
  - varied writing quality and domains
- Quality gates:
  - reject missing or out-of-order steps
  - reject multiple primary fallacies
  - reject analogy domain leakage
  - reject transfer-answer leakage
  - reject missing reflective question

## Training Plan
- Base model target: `Qwen/Qwen3-1.7B-Instruct`.
- Method: SFT + QLoRA + Unsloth.
- Runtime: Google Colab GPU for training.
- Outputs: adapters/checkpoints, merged adapter export, training run summary.

## Evaluation Plan
- Evaluate base and tuned models on the same held-out set.
- Metrics:
  - strict behavior pass rate (7/7)
  - per-step adherence
  - robustness on adversarial prompts
  - consistency across similar prompts
  - primary-fallacy accuracy
  - LLM-as-judge dimensions (behavior adherence, robustness, task quality)

## Success Metrics
Project succeeds if tuned model exceeds base model on:
- complete behavior-spec pass rate
- adversarial robustness
- per-step consistency
- primary-fallacy accuracy
using the same held-out benchmark.
