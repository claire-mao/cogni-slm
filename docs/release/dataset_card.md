---
language: en
task_categories:
  - text-generation
pretty_name: Cogni AP Logical-Fallacy Tutor
---

# Cogni AP Logical-Fallacy Tutor Dataset

Supervised examples for teaching AP English Language students to analyze one primary
logical fallacy through a fixed seven-section instructional sequence.

## Structure

Each example contains `system`, `user`, and `assistant` chat messages. The assistant
response includes argument summary, assumptions, primary fallacy, explanation,
cross-domain analogy, transfer check, and reflective question.

## Splits and leakage

The release contains train, validation, and untouched test splits. Run
`scripts/validate_ap_sft_ready.py` before release to verify section order,
deduplication, and split isolation.

## Limitations

Teacher-generated labels may contain analytical errors or pedagogical bias. This
dataset is educational research material, not an authoritative grading system.

## Licensing

The current mixed-source build is not approved for public redistribution. See
`THIRD_PARTY_NOTICES.md` and the generated license audit. Argotario English data is
CC0; the other current sources remain blocked pending explicit license evidence.
