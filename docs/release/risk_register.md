# Release Risk Register

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| Behavior drift under adversarial prompts | High | Medium | Include adversarial training/eval examples and strict pass/fail gate |
| Data leakage into held-out benchmark | High | Low | Source tracking + hash-based overlap checks |
| Weak analogy quality despite pass format | Medium | Medium | Add analogy-specific rubric and rejection rule |
| Colab interruptions during training | Medium | High | Frequent checkpointing + resume-tested configs |
| Incomplete model artifact packaging | Medium | Medium | Pre-ship checklist for adapter, config, tokenizer, eval results |
