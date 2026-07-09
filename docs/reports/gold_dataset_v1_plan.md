# Gold Dataset v1 Plan

## Objective

Design Gold Dataset Version 1 as a high-quality, manually reviewed benchmark for teacher-model evaluation.

Target size: `100` examples.

This document is planning-only. No dataset build is executed here.

## Fixed Composition

| Source | Count | Share |
|---|---:|---:|
| ASAP essays | 30 | 30% |
| Persuade essays | 20 | 20% |
| AP essays | 20 | 20% |
| Argumentative essays | 20 | 20% |
| Logical fallacy examples | 10 | 10% |
| Total | 100 | 100% |

## 1) Sampling Strategy

Sampling method: stratified sampling with deterministic seeds, followed by manual review and adjudication.

### 1.1 Source-specific pools

1. Build a candidate pool for each source family.
2. Enforce license and provenance eligibility before sampling.
3. Remove exact duplicates and near-duplicates before stratification.

### 1.2 Deterministic sampling controls

1. Use fixed random seed set for reproducibility: `42`, `314`, `2718`.
2. Sample by stratum in deterministic order: source -> difficulty -> topic -> length.
3. Store sampling metadata fields `sampling_seed`, `stratum_id`, and `sampling_reason` for each row.

### 1.3 Required record fields in candidate stage

1. `example_id`
2. `source`
3. `license`
4. `prompt`
5. `essay`
6. `original_id`
7. `topic`
8. `difficulty_provisional`
9. `length_bin`
10. `sampling_reason`

## 2) Difficulty Balancing

Difficulty balancing goal: ensure robust coverage of low, medium, and high difficulty writing and reasoning.

### 2.1 Difficulty definition

Difficulty is assigned using available source signals, normalized per source:
1. Score percentile where source gold score exists.
2. Rubric complexity indicators (argument depth, counterargument handling).
3. Readability and length complexity indicators.
4. Logical complexity (number of inferential steps/fallacy ambiguity).

### 2.2 Difficulty bands

Use three bands:
1. `low`
2. `medium`
3. `high`

Target distribution across all 100 examples:
1. `low`: 30
2. `medium`: 40
3. `high`: 30

### 2.3 Per-source minimums

Each source must include at least:
1. 20% low
2. 30% medium
3. 20% high

Remaining 30% per source is flexible to preserve topic/prompt diversity.

## 3) Topic Balancing

Topic balancing goal: avoid overfitting to narrow prompts or domains.

### 3.1 Topic taxonomy

Use a normalized topic taxonomy:
1. Education
2. Technology
3. Civics/policy
4. Environment
5. Health/society
6. Ethics/philosophy
7. Culture/media
8. Other

### 3.2 Topic constraints

1. No single topic may exceed 20% of final dataset.
2. At least 6 distinct topic buckets must be present.
3. For AP and argumentative subsets, enforce stance diversity where applicable.

### 3.3 Prompt balancing

1. Enforce prompt diversity within each source.
2. No single prompt ID should exceed 15% of entire dataset unless unavoidable due to source constraints.
3. If a prompt is overrepresented in candidates, downsample that prompt first.

## 4) Length and Quality Balancing

### 4.1 Length bins

Length bins by token count:
1. `short`: <250 tokens
2. `medium`: 250-700 tokens
3. `long`: >700 tokens

Target distribution:
1. short: 25
2. medium: 45
3. long: 30

### 4.2 Writing quality bands

Use provisional quality bands from source score percentiles and reviewer screening:
1. low quality: 30
2. medium quality: 40
3. high quality: 30

## 5) Manual Review Workflow

### 5.1 Roles

1. Reviewer A: independent annotation.
2. Reviewer B: independent annotation.
3. Adjudicator: resolves disagreements.
4. QA lead: agreement and quality-gate owner.

### 5.2 Workflow steps

1. Pre-screen sampled candidates for licensing/provenance completeness.
2. Assign each case to two independent reviewers.
3. Reviewers annotate all required fields without seeing each other’s labels.
4. Compute agreement and identify disagreement cases.
5. Route disagreement cases to adjudicator.
6. Apply adjudicated final label and reviewer metadata.
7. Run automatic validation checks.
8. Approve for v1 only if all quality gates pass.

### 5.3 Reviewer output requirements per example

1. score decision
2. rubric assessment
3. reasoning-skill expectation
4. fallacy label expectation
5. reviewer confidence
6. notes

## 6) Adjudication Protocol

### 6.1 Adjudication triggers

A case is adjudicated when any condition is true:
1. Score difference exceeds one score band.
2. Rubric disagreement on two or more core criteria.
3. Fallacy label mismatch.
4. Reviewer confidence <0.60 from either reviewer.
5. Hallucination or unsupported-evidence flag raised.

### 6.2 Adjudication decision rules

1. Adjudicator reviews source text plus both reviewer rationales.
2. Adjudicator records final decision and rationale.
3. Adjudicator marks resolved flags `hallucination`, `rubric_error`, and `logic_error`.
4. Adjudicated output is final for v1 release.

### 6.3 SLA

1. Standard disagreements: resolve within 2 business days.
2. Critical disagreement (hallucination/rubric integrity): resolve within 1 business day.

## 7) Versioning Plan

Version target: `gold_v1`.

### 7.1 Storage layout

1. `datasets/gold/versions/gold_v1/gold_dataset.jsonl`
2. `datasets/gold/versions/gold_v1/adjudication_history.jsonl`
3. `datasets/gold/versions/gold_v1/checksums.json`
4. `datasets/gold/versions/gold_v1/manifest.json`

Pointers:
1. `datasets/gold/manifest.json`
2. `datasets/gold/version_index.json`

### 7.2 Immutability policy

1. Freeze `gold_v1` once release gates pass.
2. Post-freeze edits require a new version (`gold_v2+`).
3. Preserve full lineage from review artifacts to released gold rows.

## 8) Checksums and Integrity

### 8.1 Required checksum artifacts

`checksums.json` must include hashes for:
1. input approved review dataset
2. adjudication log
3. emitted gold dataset
4. emitted adjudication history file
5. aggregate row checksum digest

### 8.2 Row-level integrity

Each gold row must include:
1. deterministic `record_checksum_sha256`
2. provenance metadata
3. review metadata

### 8.3 Determinism

1. Stable sort on `example_id`, `case_id`, `review_id`.
2. Stable JSON serialization for row hashing.
3. Fixed seed usage logged in manifest.

## 9) Quality Gates

All gates are mandatory before release.

### 9.1 Coverage gates

1. Total rows exactly `100`.
2. Source composition exactly `30/20/20/20/10`.
3. Difficulty, topic, and length quotas within +/-2 of target counts.

### 9.2 Annotation quality gates

1. Double-review coverage: `100%`.
2. Adjudication complete for all triggered cases.
3. No unresolved critical flags.

### 9.3 Agreement gates

1. Score QWK >= `0.75` on dual-reviewed set.
2. Rubric item agreement >= `0.80`.
3. Fallacy macro F1 >= `0.75`.
4. Decision agreement kappa >= `0.70`.

### 9.4 Structural validity gates

1. JSON row validity: `100%`.
2. Required field completeness: `100%`.
3. Schema validation pass: `100%`.

### 9.5 Provenance and compliance gates

1. License field present for every example.
2. Source and original_id present for every example.
3. Manifest and checksums generated and validated.

## 10) Confidence Requirements

### 10.1 Per-reviewer confidence

Reviewers provide confidence in `[0,1]` for each case.

Minimum standards:
1. Median reviewer confidence per batch >= `0.75`.
2. Cases with confidence < `0.60` auto-route to adjudication.
3. Cases with both reviewers < `0.55` are excluded unless adjudicator explicitly approves.

### 10.2 Adjudicator confidence

1. Adjudicator records final confidence.
2. Final confidence < `0.60` requires QA lead override to include in v1.

### 10.3 Release confidence summary

Manifest must report:
1. confidence distribution (p10, p50, p90)
2. count of low-confidence inclusions and approvals
3. justification for any borderline retained cases

## 11) Deliverables for v1 Planning Signoff

Before dataset build starts, approve:
1. source eligibility lists and licenses
2. final stratification tables
3. reviewer roster and calibration results
4. adjudication roster
5. quality gate checklist
6. versioning/checksum template

## 12) Explicit Non-Execution Statement

This document specifies the Gold Dataset v1 design only.

No dataset was built and no labels were generated in this step.
