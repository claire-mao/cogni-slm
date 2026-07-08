# Cogni Evaluation Dataset Specification

## 1. Purpose
This document specifies dataset interfaces for evaluation architecture only.

It defines:
- JSONL schema
- split policy
- held-out benchmark requirements
- adversarial example requirements
- metadata fields
- versioning strategy

No dataset is generated in this milestone.

## 2. Canonical JSONL Schema

Each line in the dataset file is one JSON object with the following fields.

### 2.1 Required Core Fields
| Field | Type | Required | Description |
|---|---|---|---|
| `example_id` | `string` | yes | Stable unique identifier for an example |
| `dataset_version` | `string` | yes | Dataset semantic version (`major.minor.patch`) |
| `taxonomy_version` | `string` | yes | Fallacy taxonomy version used for labels |
| `source_id` | `string` | yes | Source/provenance identifier |
| `argument_text` | `string` | yes | Input argument text for model evaluation |
| `task_mode` | `string` | yes | One of `diagnose`, `teach`, `quiz_feedback` |
| `difficulty_level` | `string|null` | no | Expected explanation depth |
| `context` | `object|null` | no | Optional learner/task context |
| `primary_fallacy_label` | `string|null` | yes | Primary target fallacy or null for no-fallacy |
| `acceptable_alternative_labels` | `array[string]` | yes | Alternate acceptable labels |

### 2.2 Behavior and Rubric Hooks
| Field | Type | Required | Description |
|---|---|---|---|
| `expected_sections` | `array[string]` | yes | Required output sections per behavior spec |
| `required_behaviors` | `array[string]` | yes | Behavior IDs (for example `B1`, `B2`) |
| `prohibited_behaviors` | `array[string]` | yes | Prohibition IDs (for example `P1`, `P2`) |
| `rubric_hooks` | `array[string]` | yes | Rubric IDs used by LLM judge |

### 2.3 Adversarial Metadata
| Field | Type | Required | Description |
|---|---|---|---|
| `is_adversarial` | `boolean` | yes | Marks adversarial example |
| `adversarial_type` | `string|null` | no | Attack class for adversarial inputs |
| `attack_target` | `string|null` | no | Targeted component (format, safety, label, etc.) |

### 2.4 Provenance and Quality Metadata
| Field | Type | Required | Description |
|---|---|---|---|
| `annotator_id` | `string|null` | no | Annotator identifier |
| `review_state` | `string` | yes | `draft`, `reviewed`, or `approved` |
| `quality_flags` | `array[string]` | yes | Annotation quality/safety flags |
| `license` | `string` | yes | Source license descriptor |
| `safety_tags` | `array[string]` | yes | Sensitive-content and safety tags |
| `created_at` | `string` | yes | ISO-8601 timestamp |
| `updated_at` | `string` | yes | ISO-8601 timestamp |

## 3. Example JSONL Record (Informative)

```json
{
  "example_id": "eval-000001",
  "dataset_version": "1.0.0",
  "taxonomy_version": "v0",
  "source_id": "src-abc123",
  "argument_text": "If one expert was wrong, experts are always unreliable.",
  "task_mode": "teach",
  "difficulty_level": "beginner",
  "context": {"learner_profile": "intro_logic"},
  "primary_fallacy_label": "hasty_generalization",
  "acceptable_alternative_labels": ["anecdotal_fallacy"],
  "expected_sections": [
    "fallacy_hypothesis",
    "reasoning_diagnosis",
    "analogy",
    "repair",
    "confidence_note"
  ],
  "required_behaviors": ["B1", "B2", "B3", "B4", "B7"],
  "prohibited_behaviors": ["P1", "P2", "P3", "P4", "P5"],
  "rubric_hooks": ["rubric.diagnosis", "rubric.analogy_mapping"],
  "is_adversarial": false,
  "adversarial_type": null,
  "attack_target": null,
  "annotator_id": "ann-07",
  "review_state": "approved",
  "quality_flags": ["double_reviewed"],
  "license": "CC-BY-4.0",
  "safety_tags": ["education"],
  "created_at": "2026-07-08T00:00:00Z",
  "updated_at": "2026-07-08T00:00:00Z"
}
```

## 4. Split Policy

Default split policy for development datasets:
- `train`: 70%
- `validation`: 15%
- `test`: 15%

Rules:
- Splits are stratified by fallacy family, difficulty, and adversarial flags.
- Near-duplicate and source-overlap checks are applied before finalizing splits.
- Prompt/rubric tuning is allowed only on train/validation.

## 5. Held-Out Benchmark Requirements

Held-out benchmark is strictly isolated from development datasets.

Requirements:
- Source/topic separation from train/validation/test examples
- Controlled ambiguity coverage across fallacy families
- Balanced adversarial and non-adversarial strata
- Locked benchmark version with immutable snapshot hash
- No prompt or rubric tuning against held-out benchmark outcomes

## 6. Adversarial Example Requirements

Required adversarial categories:
- prompt injection
- misleading lexical cueing
- contradiction/conflicting premises
- style/format pressure attacks

Adversarial design constraints:
- Every adversarial example must define `adversarial_type` and `attack_target`.
- Adversarial examples must preserve evaluation relevance to behavior spec.
- Adversarial and non-adversarial examples should share comparable topic coverage.

## 7. Metadata Field Conventions

Identifier conventions:
- `example_id` is immutable once published.
- `source_id` links to provenance metadata in raw-data tracking.

Timestamp conventions:
- `created_at` and `updated_at` use UTC ISO-8601 format.

Review conventions:
- `review_state=approved` is required for held-out benchmark inclusion.
- `quality_flags` record known annotation caveats and audit status.

## 8. Versioning Strategy

Versioning model:
- Semantic dataset versioning (`major.minor.patch`)
- Immutable snapshot hash for each released version

Version increment rules:
- `major`: incompatible schema changes or label-policy shifts
- `minor`: backward-compatible example additions or metadata extensions
- `patch`: typo fixes, metadata corrections, and non-semantic updates

Changelog requirements per release:
- schema changes
- label/taxonomy changes
- split composition changes
- benchmark membership changes

## 9. Constraints and Assumptions Pending Validation

Constraints:
- No benchmark leakage into prompt/rubric tuning loops
- Stable taxonomy alignment across versions
- Full traceability for provenance and annotation state

Assumptions:
- A1: Primary + alternate label policy improves fairness under ambiguity.
- A2: Split stratification by adversarial flags improves robustness signal quality.
- A3: Held-out benchmark isolation is practical with available source diversity.
- A4: Metadata completeness can be maintained at research iteration speed.
