# Cogni Synthetic Data Generation Design

## 1. Scope and Non-Goals

This document defines the architecture and interfaces for synthetic dataset generation.

Scope:
- Teacher-model-driven synthetic data creation design
- Multi-stage generation and critique pipeline design
- Filtering, deduplication, validation, and export interfaces
- Versioning and metadata contracts

Non-goals for this milestone:
- No generation of training examples
- No implementation of generation logic
- No training or evaluation execution

## 2. Teacher Model Architecture

Teacher design uses role-specialized components:
- Generator role: drafts candidate examples for a target fallacy (or no-fallacy case)
- Critic role: audits behavior-spec alignment and pedagogical quality
- Refiner role: revises candidates using structured critique

Architecture pattern:
- `teacher.py` exposes abstract teacher interfaces, model configs, and role contracts.
- Teacher may be single-model multi-prompt or multi-model ensemble; interfaces support both.
- All teacher outputs must carry provenance metadata for auditability.

Teacher output contract (conceptual):
- Argument text and task metadata
- Target label metadata (`primary` + `acceptable_alternates`)
- Structured explanation fields aligned with behavior spec:
  - `fallacy_hypothesis`
  - `reasoning_diagnosis`
  - `analogy` (`source_scenario`, `mapping`, `limits`)
  - `repair`
  - `confidence_note`
- Critique and revision trace metadata

## 3. Prompt Template System

Prompt templates are defined as typed, versioned assets in `prompts.py`.

Template families:
- fallacy-targeted generation prompts
- no-fallacy generation prompts
- adversarial transformation prompts
- critique prompts
- revision prompts

Prompt contract requirements:
- `template_id`, `template_version`
- deterministic placeholders and required inputs
- output schema hints (required sections and constraints)
- safety constraints and style controls

Design goals:
- prompt composability for domain, difficulty, and reflection style controls
- full reproducibility through template version pinning

## 4. Multi-Stage Generation Pipeline

Pipeline stages:
1. **Plan**: sample target configuration (fallacy, domain, difficulty, reflection style).
2. **Generate**: teacher creates candidate example.
3. **Self-critique**: critic scores behavior-spec and pedagogical alignment.
4. **Revise**: refiner produces improved candidate when critique flags issues.
5. **Filter**: automatic quality filters remove weak/off-spec candidates.
6. **Deduplicate**: remove near duplicates across argument, rationale, and analogy.
7. **Validate**: schema and policy checks before dataset inclusion.
8. **Export**: write JSONL + manifest artifacts.

Orchestration:
- `generate.py` coordinates stage transitions.
- each stage emits structured artifacts and status for traceability.
- failed candidates are retained in audit traces, not in final export.

## 5. Self-Critique Pipeline

Self-critique objectives:
- improve behavior-spec adherence before final filtering
- reduce hallucinated evidence and weak analogy mappings
- enforce calibrated confidence language

Critique dimensions:
- structural completeness (required sections, deterministic order)
- label coherence (target fallacy vs explanation content)
- analogy quality (mapping explicitness and limits clarity)
- pedagogical quality (clarity at requested difficulty)
- safety/scope constraints

Interface policy:
- critique and revision are first-class typed artifacts in `schemas.py`.
- critique history is preserved for each candidate.

## 6. Automatic Quality Filtering

Filtering strategy combines hard and soft gates:
- hard gates (drop immediately):
  - missing required behavior-spec sections
  - unsafe or out-of-scope guidance
  - malformed schema fields
- soft gates (score thresholds):
  - weak diagnosis clarity
  - weak analogy mapping
  - poor repair quality
  - low uncertainty calibration quality

`filter.py` defines:
- filter configuration contract
- filter decisions (`pass`, `reject`, `needs_revision`)
- reason codes for audit and iteration analysis

## 7. Deduplication Strategy

Deduplication is multi-view:
- lexical similarity (argument overlap)
- semantic similarity (embedding-style interface placeholder)
- structural similarity (same diagnosis and analogy mapping shape)

Dedup scopes:
- intra-batch dedup
- cross-version dedup (against previous released datasets)
- split-aware dedup (avoid leakage between train/validation/test/held-out benchmark)

`deduplicate.py` defines:
- dedup configuration
- duplicate cluster records
- winner-selection policy interfaces

## 8. Dataset Validation

Validation must run after filtering and deduplication.

Validation checks:
- schema validity
- metadata completeness
- behavior-spec field integrity
- fallacy label policy consistency (`primary` + `acceptable_alternates`)
- no-fallacy policy consistency
- split and benchmark policy constraints

`validate.py` defines:
- validation config and issue model
- report contract with error/warning severities

## 9. JSONL Export Contract

Export artifacts:
- `dataset.jsonl`: validated example records only
- `manifest.json`: dataset metadata, version, prompt/teacher configs, counts, hashes
- optional `audit_traces.jsonl`: generation and critique trace records

`export.py` defines:
- export configuration
- JSONL exporter interface
- deterministic ordering and hash-policy placeholders

## 10. Dataset Versioning Strategy

Versioning is semantic with immutable snapshots:
- `major`: schema or label-policy incompatible changes
- `minor`: backward-compatible content additions
- `patch`: metadata corrections and non-semantic fixes

Version identifiers:
- `dataset_version` (semantic string)
- `snapshot_hash` (content-addressed hash of exported records + manifest)
- `prompt_bundle_version`
- `teacher_config_version`
- `taxonomy_version`

All versions and hashes are required in exported manifest metadata.

## 11. Required Metadata

Every generated record must include:
- identity/provenance:
  - `example_id`, `source_id`, `created_at`, `generation_run_id`
- task and label:
  - `task_mode`, `difficulty_level`, `primary_fallacy_label`,
    `acceptable_alternative_labels`, `is_no_fallacy`
- behavior hooks:
  - `expected_sections`, `required_behaviors`, `prohibited_behaviors`, `rubric_hooks`
- generation provenance:
  - `generator_model_id`, `critic_model_id`, `template_id`, `template_version`,
    `prompt_seed`, `decoding_config`
- diversity tags:
  - `domain_tag`, `analogy_source_domain`, `analogy_target_domain`,
    `reflection_style_tag`
- adversarial tags:
  - `is_adversarial`, `adversarial_type`, `attack_target`
- quality/audit:
  - `critique_scores`, `filter_decisions`, `dedup_cluster_id`, `validation_status`

## 12. Coverage and Diversity Strategy

### 12.1 Fallacy Coverage Strategy
- maintain explicit per-fallacy target quotas
- include ambiguous boundary cases with accepted alternative labels
- preserve distribution controls across difficulty levels

### 12.2 Adversarial Prompt Generation
- generate adversarial variants across:
  - prompt injection
  - lexical misdirection
  - contradiction framing
  - style-pressure attacks
- ensure adversarial examples remain behavior-relevant and pedagogically valid

### 12.3 No-Fallacy Examples
- include examples where reasoning is valid or uncertainty should be explicit
- require model behavior to avoid false-positive fallacy assignment
- ensure no-fallacy items include clear rationale for validity

### 12.4 Cross-Domain Analogy Diversity
- enforce analogy-source domain diversity (science, policy, health, finance, etc.)
- prevent repeated analogy templates dominating one fallacy class
- track domain pair distribution via metadata

### 12.5 Reflection Diversity
- vary explanation/reflection styles while preserving structure:
  - concise diagnostic
  - stepwise pedagogical
  - counterexample-driven
  - misconception-correction
- track style assignment with `reflection_style_tag`

## 13. Interface Mapping to `src/data/`

- `schemas.py`: canonical dataclasses/types for candidates, critiques, records, manifests
- `teacher.py`: teacher role and model adapter protocols
- `prompts.py`: template registry and rendering interfaces
- `generate.py`: pipeline orchestration contracts and run context
- `filter.py`: quality-gate interfaces and decision contracts
- `deduplicate.py`: dedup interfaces and cluster contracts
- `validate.py`: validation interfaces and report contracts
- `export.py`: dataset export interfaces and artifact contracts

No module in this milestone contains generation logic.

## 14. Assumptions To Validate

- A1: Teacher self-critique materially improves behavior-spec adherence.
- A2: Multi-view dedup prevents leakage without removing useful diversity.
- A3: Diversity tags can be operationalized without excessive manual curation.
- A4: No-fallacy examples can be generated with low false-positive ambiguity.
- A5: Version + hash metadata is sufficient for reproducibility and audit.

