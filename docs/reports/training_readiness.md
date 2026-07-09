# Training Readiness Assessment

Date: 2026-07-08  
Scope: Evaluate whether the current dataset is suitable for fine-tuning a small language model for educational assessment.

## Executive Verdict

**Not ready for full fine-tuning yet.**

The current dataset is strong enough for narrow internal experiments on prompt-conditioned essay scoring, but it is not yet robust for reliable educational-assessment training due to:

- single-source coverage (`asap_aes` only)
- score-scale mismatch across prompts
- prompt leakage across splits
- high semantic overlap between train and eval splits
- unresolved redistribution/licensing risk for ASAP-AES lineage

## Current Dataset Snapshot (Canonical Splits)

Source files: `datasets/final/train.jsonl`, `datasets/final/validation.jsonl`, `datasets/final/test.jsonl`

- Total examples: **12,413**
- Split sizes: **9,940 / 1,241 / 1,232**
- Task coverage: **1 task** (`essay_scoring`)
- Source coverage: **1 source** (`asap_aes`)
- Prompt coverage: **8 prompts** (`1..8`)
- Label range: **0.0 to 60.0** (prompt-dependent rubric scales)

## Readiness by Dimension

### 1) Dataset Size
**Assessment: Partially sufficient for narrow tasks; insufficient for broad educational assessment.**

- `12.4k` examples can support small-model adaptation for a focused scorer.
- For broad feedback quality, generalization, and robustness, this size is modest and currently mono-domain.

### 2) Label Quality
**Assessment: Mixed.**

Strengths:
- labels are present for all canonical rows
- no malformed JSON in canonical splits

Weaknesses:
- scores are prompt-specific and not directly comparable globally
- same numeric label value means different performance bands by prompt set

### 3) Class Balance
**Assessment: Skewed.**

- Majority class (`3.0`): **22.73%**
- Low-score share (`<=4`): **67.04%**
- Distribution is concentrated in lower bands, which can bias optimization and calibration.

### 4) Domain Diversity
**Assessment: Low.**

- all examples come from one dataset family (`asap_aes`)
- no additional argumentative corpora currently present in canonical training data

### 5) Reasoning Diversity
**Assessment: Low-to-moderate.**

- current supervision is score prediction, not rich instructional feedback/rationale generation
- limited evidence of multi-step reasoning targets in canonical training schema

### 6) Writing Diversity
**Assessment: Moderate.**

- unique essay ratio in canonical splits: **1.0** (no exact text duplicates)
- length coverage is broad (40 to 1064 words)
- still constrained to one source and 8 prompt families

### 7) Prompt Diversity
**Assessment: Limited and leakage-prone.**

- only 8 prompts overall
- all prompts appear in train, validation, and test
- prompt overlap across splits is 100%, which weakens out-of-prompt generalization claims

### 8) Evaluation Quality
**Assessment: Not yet reliable for strong readiness claims.**

From existing audits:
- Prompt leakage: **FAIL** (`docs/reports/final_verification.md`)
- High semantic contamination across splits (`docs/reports/leakage_report.md`)
- License status for current main source remains unresolved for redistribution (`docs/reports/license_audit.md`)

## Comparison Against Target Reference Datasets

This section compares the current dataset posture with common public benchmarks/datasets used for scoring or reasoning coverage.

| Dataset | Typical scale | Primary task signal | Relative value vs current dataset | Gap addressed |
|---|---:|---|---|---|
| ASAP-AES | ~12.9k essays, 8 prompts | Holistic essay scoring | Current dataset already reflects this profile | Baseline scoring exists, but diversity remains narrow |
| PERSUADE (corpus family) | larger argumentative essay corpus (commonly cited as 20k+) | Argument writing quality / discourse quality | Adds argument-centric domain breadth and richer writing styles | Improves domain and writing diversity |
| Feedback Prize (competition family) | large competition-scale supervised writing data | Rubric-linked writing quality traits/effectiveness | Adds trait-oriented supervision and feedback-related targets | Improves label richness and practical tutoring relevance |
| SQuAD | 100k+ QA pairs | reading comprehension QA | Not essay scoring, but improves instruction-following and answer grounding behavior | Improves reasoning and evaluation stress-testing |
| RACE | ~100k MCQ from exam passages | exam-style reasoning/comprehension | Adds harder exam-style reasoning and distractor robustness | Improves reasoning robustness and generalization pressure |

Note: ASAP-AES is the only source currently present in canonical Cogni training data.

## Is the Current Dataset Suitable for Fine-Tuning a Small LM?

**Answer: Not yet for production-grade educational assessment fine-tuning.**

It is suitable only for a constrained internal baseline (prompt-conditioned essay score prediction under ASAP-like distributions). It is not yet suitable for broader educational assessment claims due to leakage, limited source/task diversity, and label/rubric comparability constraints.

## Additional Datasets Needed Before Training

1. **License-cleared argumentative writing corpus with rubric-linked labels**
   - Prioritize PERSUADE/Feedback Prize variants where usage terms are explicit and compatible.
2. **Trait-level feedback supervision**
   - Add datasets with criterion-level signals (organization, evidence, style, conventions), not only holistic scores.
3. **Prompt-disjoint evaluation sources**
   - Hold out full prompt families and source families to measure true generalization.
4. **Reasoning/robustness benchmarks**
   - Add QA/comprehension benchmarks (for example SQuAD/RACE-style) for stress-testing inference behavior and consistency.
5. **License and provenance hardening**
   - Resolve ASAP-AES redistribution status from authoritative upstream documentation before downstream release/training artifacts.

## Minimum Preconditions to Start Fine-Tuning

- Prompt/source-disjoint split policy enforced
- At least one additional licensed essay dataset ingested into canonical training data
- Prompt-aware score normalization policy finalized and versioned
- Leakage checks rerun and passing thresholds defined
- License audit resolved for all included sources

## Conclusion

The current dataset supports **baseline experimentation** but not yet **training-ready, defensible fine-tuning** for a general educational-assessment SLM. Expand source coverage, strengthen split hygiene, and clear licensing before initiating full QLoRA training.
