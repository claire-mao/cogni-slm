# Cogni Problem Definition

## 1. Objective
Build a fine-tuned small language model (SLM) that teaches logical fallacies through structured analogical reasoning.

The model should not only label a fallacy, but also produce an instructional analogy that helps a learner transfer understanding to new arguments.

## 2. Why This Problem Matters
- Fallacy education is often definition-heavy and hard to apply in unfamiliar contexts.
- Learners need explanation patterns that generalize beyond memorized examples.
- Analogical reasoning is a practical bridge between abstract logic concepts and concrete examples.

## 3. Primary Users and Use Cases
- Learners studying critical thinking, rhetoric, or argument analysis.
- Educators who need consistent, explainable examples.
- Self-study users who want feedback on why an argument is fallacious and how to improve it.

Core use cases:
- Diagnose potential fallacies in short arguments.
- Explain diagnosis with a structured analogy.
- Contrast flawed reasoning with a corrected alternative.

## 4. Scope
In scope:
- Technical foundation for data, behavior specification, architecture, and roadmap.
- Behavior-first specification before any ML implementation.
- Evaluation planning for pedagogical quality and reasoning faithfulness.

Out of scope (current phase):
- Training pipelines and model fine-tuning code.
- Reported benchmark scores or performance claims.
- Production serving infrastructure.

## 5. Research Questions
1. Does structured analogical explanation improve learner transfer compared with plain definitions?
2. Which output structure best balances pedagogical clarity and reasoning rigor?
3. How reliably can the model distinguish closely related fallacies?
4. What failure patterns appear when arguments contain multiple possible fallacies?

## 6. Success Criteria (Pre-Implementation)
- A clear and testable behavior contract exists (see `docs/behavior_spec.md`).
- Data lifecycle and project modules are specified against repository structure.
- Roadmap defines staged milestones, exit criteria, and risk controls.
- Known assumptions are explicit and tagged for validation.

## 7. Constraints
- Small-model orientation: design must remain parameter- and compute-conscious.
- Explanations must be pedagogically useful, not just taxonomic labels.
- Outputs must support future automated and human evaluation.
- No fabricated claims about training or evaluation outcomes.

## 8. Assumptions To Validate
- A1: Structured analogy improves comprehension for most target learners.
- A2: A compact fallacy taxonomy can cover initial use cases without major ambiguity.
- A3: Instructional quality can be evaluated with reliable annotation guidelines.
- A4: Reasoning-faithful explanations are feasible for a small model under constrained context.
- A5: The chosen output format can be scored consistently by both humans and scripted checks.

## 9. Relationship to Repository Layout
- `docs/` holds problem framing, behavior contract, architecture, and roadmap.
- `datasets/` will track the raw -> processed -> eval lifecycle once data work starts.
- `configs/` will hold behavior/eval/training configuration contracts.
- `tests/` will enforce behavior and interface invariants derived from the behavior spec.

