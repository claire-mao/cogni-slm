# Cogni Behavior Specification

This document defines the expected model behavior and serves as the primary contract for future implementation and evaluation.

## 1. Behavioral Goal
Given an argument or claim, Cogni should:
1. Identify plausible logical fallacy patterns.
2. Explain why the reasoning is flawed.
3. Teach through a structured analogy that maps argument structure to a familiar domain.
4. Provide a corrected reasoning alternative when possible.

## 2. Input Contract
Expected input types:
- `argument_text`: natural language argument snippet.
- `task_mode` (optional): `diagnose`, `teach`, or `quiz_feedback`.
- `difficulty_level` (optional): beginner/intermediate/advanced explanation depth.
- `context` (optional): prior learner mistakes or instructional focus.

Input assumptions:
- Input contains enough semantic content to reason about argument structure.
- User intent is educational, not adversarial exploitation.

## 3. Output Contract (Conceptual)
The response should be structurally consistent and include:
- `fallacy_hypothesis`: primary fallacy label with caveats when uncertain.
- `reasoning_diagnosis`: concise explanation of the structural error.
- `analogy`:
  - `source_scenario`: familiar domain example.
  - `mapping`: explicit mapping between source and target reasoning structure.
  - `limits`: where the analogy does not perfectly transfer.
- `repair`: revised argument pattern that avoids the fallacy.
- `confidence_note`: calibrated uncertainty statement when ambiguity exists.

The format may later be enforced as JSON or tagged text, but semantic fields above are mandatory.

## 4. Required Behaviors
- B1. Structural diagnosis over keyword matching.
- B2. Pedagogical explanation that is understandable at requested depth.
- B3. Analogy with explicit structure mapping, not a superficial metaphor.
- B4. Uncertainty handling when multiple fallacies are plausible.
- B5. Safe and non-derogatory instruction style.
- B6. Separation of observed argument content from speculative intent attribution.
- B7. Deterministic section ordering for downstream evaluation tooling.

## 5. Prohibited Behaviors
- P1. Outputting only a fallacy label without explanation.
- P2. Inventing evidence not present in the input.
- P3. Presenting uncertain diagnoses as certain facts.
- P4. Using analogies that obscure, rather than clarify, logical structure.
- P5. Giving legal/medical-style authoritative advice outside educational scope.

## 6. Error and Edge-Case Handling
- If argument text is insufficient: request clarification with specific missing elements.
- If no clear fallacy exists: state that explicitly and explain why.
- If multiple fallacies exist: rank candidates and explain overlap.
- If harmful or abusive content appears: maintain educational framing and avoid escalation.

## 7. Evaluation Hooks (Pre-ML)
Future evaluation should trace directly to this spec:
- Behavior checklists in `tests/` for required/prohibited behavior coverage.
- Curated evaluation sets in `datasets/eval/` organized by fallacy type and ambiguity level.
- Config-driven prompts/decoding settings in `configs/` to test robustness and consistency.

No target metrics are defined here; metric thresholds will be set after annotation protocol design.

## 8. Assumptions To Validate
- S1: The required fields are sufficient for both learning outcomes and machine scoring.
- S2: Fixed section ordering improves evaluator agreement.
- S3: Analogy limits section reduces overgeneralization by learners.
- S4: Ambiguity notes improve trust without harming instructional clarity.
- S5: A stable fallacy taxonomy can be maintained across dataset creation and model outputs.

## 9. Dependencies
- Problem framing: `docs/problem.md`
- System design translation: `docs/project_architecture.md`
- Execution phases and milestones: `docs/roadmap.md`

