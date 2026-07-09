# Production Labeling Workflow

Workflow version: `production_labeling_workflow_v1`

Date: `2026-07-09`

## 1) Purpose

Define a production-grade labeling workflow for educational assessment supervision that is traceable, versioned, and recoverable.

This document is design-only. No labels are generated in this step.

## 2) End-to-End Pipeline

Ordered stages:
1. Teacher inference
2. Automatic validation
3. Quality filtering
4. Human review
5. Gold merge
6. SFT export
7. Experiment tracking and release logging

Primary orchestrator mapping:
1. `src/data/generate_production_dataset.py`
2. `src/teacher/generate_labels.py`
3. `src/teacher/validation.py`
4. `src/review/build_review_queue.py`
5. `src/review/merge_reviews.py`
6. `src/data/build_gold_dataset.py`
7. `src/data/build_sft_dataset.py`
8. `src/utils/experiment_tracker.py`

## 3) Stage-by-Stage Design

### 3.1 Teacher Inference

Goal:
1. Produce task-complete teacher outputs for each input example.

Input:
1. Source dataset JSONL.
2. Teacher stack configuration (model, prompt version, schema version).
3. Prompt artifacts under `teacher_prompts/`.

Output:
1. Response records (JSONL) with raw output and metadata.
2. Latency, token usage, and estimated cost fields.

Required metadata fields per response:
1. `run_id`
2. `model`
3. `provider`
4. `prompt_version`
5. `example_id`
6. `task_id`
7. `seed`
8. `temperature`
9. `input_tokens`
10. `output_tokens`
11. `estimated_cost_usd`
12. `latency_ms`

Operational settings:
1. Default deterministic mode: `temperature=0.0`.
2. Seed fixed per run schedule.
3. Strict JSON expected from teacher.

### 3.2 Automatic Validation

Goal:
1. Block structurally invalid or weakly grounded outputs before downstream use.

Validator mapping:
1. `src/teacher/validation.py`

Core checks:
1. JSON validity.
2. Missing required fields.
3. Score range validity (`0-60`, integer).
4. Hallucinated rubric items.
5. Unsupported feedback.
6. Reasoning completeness.
7. Confidence calibration availability.

Validation outputs:
1. Example-level findings JSONL.
2. Model-level summary JSON and CSV.
3. Validation pass/fail signals for filtering.

### 3.3 Quality Filtering

Goal:
1. Keep only high-confidence, schema-valid, instruction-faithful outputs.

Filter sequence:
1. Validation pass check.
2. Rule-based quality threshold.
3. JSON schema validation.
4. Confidence threshold.

Reference module:
1. `src/teacher/generate_labels.py`

Default thresholds (adjustable by run config):
1. Quality threshold >= `0.80`.
2. Confidence threshold >= `0.60`.
3. Schema validity required.

Outputs:
1. Filtered canonical split files (`train/validation/test`).
2. Stage manifest with counts at each filter step.

### 3.4 Human Review

Goal:
1. Resolve uncertain, conflicting, or high-risk outputs via manual decisions.

Queue construction:
1. Use `src/review/build_review_queue.py`.
2. Prioritize low confidence, disagreement, hallucination flags, score uncertainty, and reasoning variance.

Review actions:
1. `accept`
2. `reject`
3. `edit`
4. `flag hallucination`
5. `flag rubric_error`

Review interface:
1. `src/review/server.py`

Review storage:
1. `datasets/review/reviews.jsonl`
2. `datasets/review/latest_reviews.json`

### 3.5 Gold Merge

Goal:
1. Merge accepted and edited review decisions into a reviewed gold-ready dataset.

Merge logic:
1. `accept` and `edit` are eligible for merge.
2. `reject` remains excluded from merged gold candidates.
3. Latest review decision per `case_id` is authoritative.

Module mapping:
1. `src/review/merge_reviews.py`
2. `src/data/build_gold_dataset.py`

Gold outputs:
1. `gold_dataset.jsonl`
2. `adjudication_history.jsonl`
3. `checksums.json`
4. `manifest.json`

### 3.6 SFT Export

Goal:
1. Export approved gold-derived supervision in training-ready formats.

Module mapping:
1. `src/data/build_sft_dataset.py`

Supported formats:
1. Alpaca
2. ShareGPT
3. ChatML
4. Hugging Face JSONL

SFT outputs:
1. Canonical split JSONL files.
2. Format-specific split JSONL files.
3. `manifest.json` and `sft_build_manifest.json`.

## 4) Experiment Tracking

Tracking system:
1. `src/utils/experiment_tracker.py`

Track for each labeling run:
1. Git commit and dirty state.
2. Dataset checksum and file counts.
3. Teacher version and prompt version.
4. Schema version.
5. Runtime timestamps and duration.
6. GPU metadata when relevant.
7. Seed and run configuration.
8. Stage metrics and failure summary.

Tracking output root:
1. `outputs/experiments/`

Required linking fields:
1. `experiment_id`
2. `run_id`
3. `dataset_version`
4. `teacher_version`
5. `prompt_version`

## 5) Dataset Versioning Strategy

Versioned dataset roots:
1. Validation: `datasets/validation/versions/validation_vN/`
2. Review-final: `datasets/review/final/versions/review_final_vN/`
3. Gold: `datasets/gold/versions/gold_vN/`
4. SFT: `datasets/sft/versions/sft_vN/`

Version control rules:
1. Every run writes to a new immutable version directory.
2. `version_index.json` tracks all versions and latest pointer.
3. No in-place mutation of finalized versions.

Release metadata requirements:
1. Upstream input checksums.
2. Stage manifests.
3. Row counts by split.
4. Filter retention rates.
5. Quality-gate status.

## 6) Rollback Strategy

Rollback principle:
1. Roll back by pointer switch, not by destructive deletion.

Rollback units:
1. Validation dataset version.
2. Review-final version.
3. Gold dataset version.
4. SFT dataset version.

Rollback triggers:
1. Post-release schema inconsistency.
2. Elevated hallucination rate discovered in audit.
3. Incorrect merge logic or adjudication mismatch.
4. Corrupt or incomplete export artifacts.

Rollback procedure:
1. Freeze current failing version as quarantined.
2. Identify last known good version from `version_index.json` and manifests.
3. Update active deployment pointer to last good version.
4. Log rollback event in experiment tracking manifest.
5. Open corrective incident with root-cause details.

Rollback guardrails:
1. Never delete failed artifacts before root-cause closure.
2. Preserve all manifests and checksums for forensic traceability.

## 7) Failure Recovery Plan

### 7.1 Failure categories

1. Inference failures: provider timeouts, rate limits, malformed responses.
2. Validation failures: missing fields, invalid scores, low reasoning completeness.
3. Review failures: unresolved disagreements, invalid edits.
4. Merge failures: case mismatch, missing review decisions.
5. Export failures: split write errors, format conversion errors.

### 7.2 Recovery actions by stage

Inference recovery:
1. Retry per model retry policy with backoff.
2. Capture raw error and preserve partial responses.
3. Requeue only failed examples.

Validation recovery:
1. Route invalid outputs to reject/regenerate bucket.
2. Run schema-focused diagnostics on failure clusters.
3. Patch prompt/schema config only after failure analysis.

Review recovery:
1. Route unresolved cases to adjudication queue.
2. Enforce edit-schema validation before acceptance.
3. Block merge if unresolved critical flags exist.

Merge recovery:
1. Rebuild case index from raw teacher outputs.
2. Recompute latest review map deterministically.
3. Re-run merge in isolated new review_final version.

Export recovery:
1. Re-run format export from canonical validated rows.
2. Verify split counts and checksums match manifest.
3. Publish only when all format checks pass.

### 7.3 Incident management

For every failed run:
1. Create incident record with `run_id` and `experiment_id`.
2. Classify severity: blocker, major, minor.
3. Record root cause, impacted versions, and recovery actions.
4. Add prevention action item before next production run.

## 8) Quality Gates for Production Release

A labeling run is releasable only if all pass:
1. JSON validity >= `0.98`.
2. Hallucination rate <= configured max.
3. Required metrics computed and logged.
4. Review merge completed with no unresolved critical cases.
5. Gold and SFT checksums generated.
6. Version indices updated.
7. Experiment manifest complete.

## 9) Operational Checklist

Pre-run:
1. Confirm provider configs and keys.
2. Confirm teacher stack version and prompt version.
3. Confirm schema version and validator compatibility.
4. Confirm input dataset checksum.

In-run:
1. Monitor failure rate and retry behavior.
2. Monitor latency and cost drift.
3. Monitor validation rejection distribution.

Post-run:
1. Verify all manifests and checksums.
2. Verify version pointers.
3. Run post-label quality checks.
4. Publish release note and archive run metadata.

## 10) Guardrails

1. Do not generate labels outside the versioned workflow.
2. Do not bypass validation or review gates for production release.
3. Do not overwrite existing released dataset versions.
4. Do not perform destructive rollback operations.

---

This workflow is designed to maximize reproducibility, label quality, and operational safety while supporting controlled recovery from production failures.
