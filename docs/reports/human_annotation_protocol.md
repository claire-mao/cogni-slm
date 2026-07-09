# Human Annotation Protocol

Protocol version: `human_annotation_protocol_v1`

Effective date: `2026-07-09`

## 1) Purpose and Scope

This protocol defines how human reviewers evaluate teacher-model outputs for educational assessment tasks before gold-dataset integration.

In scope:
1. Review workflow for queued cases.
2. Reviewer qualification and calibration.
3. Accept/reject/edit decision rules.
4. Hallucination and rubric-correction handling.
5. Adjudication and versioning.
6. Quality assurance and inter-rater agreement.

Out of scope:
1. Model inference execution.
2. Training execution.
3. Direct modification of source datasets during review.

## 2) Review Units and Artifacts

Primary review unit:
1. One `case_id` from the review queue.

Primary artifacts:
1. Queue input: `datasets/review/queue/review_queue.jsonl`.
2. Gold/reference context: `datasets/gold/review_package/review_forms.jsonl` or approved gold source.
3. Review interface: `src/review/server.py`.
4. Review decisions store: `datasets/review/reviews.jsonl` and `datasets/review/latest_reviews.json`.
5. Merge output: `datasets/review/final/review_dataset.jsonl` via `src/review/merge_reviews.py`.

## 3) Task Coverage

Reviewers must evaluate model outputs for all configured tasks:
1. `essay_scoring`
2. `rubric_adherence`
3. `educational_feedback`
4. `logical_reasoning`
5. `argument_quality`
6. `logical_fallacy_identification`
7. `revision_suggestions`

## 4) Reviewer Qualifications

Minimum reviewer requirements:
1. Demonstrated experience with analytic writing assessment or AP-style rubric scoring.
2. Ability to identify claim/evidence/reasoning quality and logical fallacies.
3. Successful completion of calibration with required agreement thresholds.
4. Completion of protocol training and signed reviewer guide acknowledgment.

Recommended reviewer profile:
1. Education, writing instruction, assessment, linguistics, or rhetoric background.
2. Prior annotation experience with quality-controlled labeling pipelines.

Role definitions:
1. Reviewer: performs first-pass case decisions.
2. Senior reviewer: handles difficult cases and supports calibration.
3. Adjudicator: final arbiter for disputed cases.
4. QA lead: monitors agreement, drift, and audit outcomes.

## 5) End-to-End Review Workflow

1. Queue generation
Use priority signals from queue builder: low confidence, disagreement, hallucination flags, score uncertainty, reasoning variance.

2. Assignment
Assign cases in balanced batches by task and difficulty.
Ensure at least 20% overlap for double-review agreement measurement.

3. Independent review
Each reviewer inspects prompt, essay, gold context, and teacher outputs.
Reviewer selects one decision: `accept`, `reject`, or `edit`.
Reviewer sets flags: `hallucination` and `rubric_error` when applicable.

4. Edit submission
If `edit`, reviewer provides corrected JSON object in `edited_output`.
Edited output must preserve required schema fields for the task.

5. Automated validation gate
Validate reviewed output with existing validation stack (`src/teacher/validation.py` + schema checks).
Route validation failures to adjudication or rework.

6. Adjudication
Triggered on disagreement, critical flags, or low-confidence edge cases.
Adjudicator finalizes decision and rationale.

7. Merge and finalize
Merge only `accept` and `edit` decisions via `src/review/merge_reviews.py`.
Keep full audit trail in review logs and manifests.

## 6) Calibration Procedure

Calibration is mandatory before production review.

Calibration setup:
1. Use a fixed calibration set of 30 cases covering all seven tasks and difficulty bands.
2. Run blind independent review by all active reviewers.
3. Compare against adjudicated reference outcomes.

Calibration pass thresholds:
1. Holistic score agreement (QWK): `>= 0.75`.
2. Criterion-level agreement (mean weighted kappa across rubric dimensions): `>= 0.70`.
3. Fallacy label macro F1: `>= 0.75`.
4. Decision agreement (`accept/reject/edit`) Cohen's kappa: `>= 0.70`.
5. Hallucination flag agreement kappa: `>= 0.65`.

Calibration failure policy:
1. Reviewer receives targeted feedback and retraining.
2. Reviewer repeats calibration on a new 15-case set.
3. Reviewer is blocked from production batches until thresholds are met.

Ongoing recalibration:
1. Weekly mini-calibration (10 cases) for active reviewers.
2. Immediate recalibration if drift alerts fire (see QA section).

## 7) Accept Criteria

Mark `accept` only when all conditions are true:
1. Output is valid JSON and task-appropriate schema-complete.
2. Score and confidence are plausible and internally consistent.
3. Rubric analysis is evidence-grounded and criterion-consistent.
4. Reasoning is coherent and sufficiently complete for the task.
5. Fallacy label is supported by explicit text evidence or correctly marked absent.
6. Feedback is specific, educational, and non-generic.
7. No material hallucination or rubric error is present.

## 8) Reject Criteria

Mark `reject` when any condition is true and cannot be reliably corrected with a minimal edit:
1. Invalid or unrecoverable JSON structure.
2. Missing core required fields for the task.
3. Major hallucination (fabricated evidence, fabricated quote, fabricated rubric claim).
4. Severe rubric mismatch that requires full-output rewrite.
5. Contradictory reasoning that invalidates the decision.
6. Unsafe or inappropriate educational feedback tone.

## 9) Edit Policy

Mark `edit` when output is salvageable with bounded corrections.

Allowed edits:
1. Correct score if rationale supports a nearby band.
2. Fix rubric criteria labels, judgments, or missing evidence fields.
3. Replace unsupported feedback with text-grounded feedback.
4. Correct fallacy label/evidence alignment.
5. Clarify reasoning steps while preserving task intent.

Edit constraints:
1. Do not introduce external facts.
2. Do not change prompt or essay content.
3. Keep edits minimal and traceable.
4. Preserve required schema keys.
5. Record brief rationale in reviewer notes.

## 10) Hallucination Policy

Hallucination definition:
1. Any claim, quote, evidence, rubric statement, or feedback assertion not supported by provided essay/prompt context.

Hallucination severity:
1. Critical: fabricated quote/evidence used to justify score or fallacy call.
2. Major: unsupported claims that change rubric reasoning or feedback priorities.
3. Minor: unsupported phrasing that does not alter decision outcome.

Action policy:
1. Critical hallucination: `reject` and set `flags.hallucination=true`.
2. Major hallucination: `edit` if fully correctable, else `reject`; always set flag true.
3. Minor hallucination: `edit` and set flag true.

## 11) Rubric Correction Policy

Rubric error definition:
1. Incorrect rubric criterion use, missing required criteria, mismatched evidence, or inconsistent criterion judgment.

Correction policy:
1. If criterion set is wrong but repairable, use `edit` and set `flags.rubric_error=true`.
2. If rubric reasoning is fundamentally invalid and requires full re-annotation, use `reject` and set flag true.
3. Preserve canonical criterion set expected by validator (`claim`, `evidence`, `reasoning`, `organization`, `style`) for teacher outputs.
4. Document correction reason in notes with criterion-specific evidence.

## 12) Adjudication Workflow

Adjudication triggers:
1. Reviewer disagreement on decision (`accept/reject/edit`).
2. Absolute score disagreement above operational threshold (default: `>= 2` points on 0-60 scale).
3. Disagreement on primary fallacy label when fallacy is marked present.
4. Presence of critical hallucination or unresolved rubric conflict.
5. Low reviewer confidence (`< 0.60`) after attempted edit.

Adjudication steps:
1. Adjudicator reviews full case and both reviewer notes.
2. Adjudicator selects final decision and final label content.
3. Adjudicator records rationale and resolved flags.
4. Final adjudicated output supersedes prior conflicting decisions.

Adjudication SLA:
1. Standard cases resolved within 2 business days.
2. Critical cases resolved within 1 business day.

## 13) Versioning and Traceability

Versioning rules:
1. Protocol updates use semantic versioning: `human_annotation_protocol_vMAJOR.MINOR`.
2. Any change to accept/reject/edit logic increments at least MINOR.
3. Breaking changes to schema expectations increment MAJOR.

Per-batch metadata requirements:
1. `protocol_version`
2. `teacher_stack_version`
3. `prompt_version`
4. `schema_version`
5. `review_batch_id`
6. `reviewer_ids`
7. `adjudicator_id` when used
8. timestamp range

Audit requirements:
1. Preserve all raw review actions in `datasets/review/reviews.jsonl`.
2. Preserve latest state in `datasets/review/latest_reviews.json`.
3. Preserve merge summary and manifest in `datasets/review/final/`.

## 14) Quality Assurance

QA controls:
1. Double-review at least 20% of production cases.
2. Blind audit sample of at least 10% of accepted/edit cases per batch.
3. Weekly drift report by task and reviewer.
4. Automatic revalidation of edited outputs before merge.

QA thresholds:
1. JSON-valid reviewed outputs: `>= 99%`.
2. Post-review unsupported-feedback rate: `<= 10%`.
3. Post-review rubric-error flag rate trending downward batch-over-batch.
4. Unresolved cases: `<= 2%` per batch.

Escalation conditions:
1. Any reviewer falls below agreement thresholds in two consecutive QA windows.
2. Hallucination flag rate increases by `> 5` percentage points week-over-week.
3. Adjudication volume exceeds 25% of reviewed cases.

## 15) Inter-Rater Agreement Metrics

Report these metrics per batch and per task:
1. Holistic score agreement: Quadratic Weighted Kappa.
2. Criterion-level agreement: weighted kappa per criterion and macro average.
3. Decision agreement (`accept/reject/edit`): Cohen's kappa for pairwise overlap and Fleiss' kappa for multi-rater subsets.
4. Fallacy label agreement: macro F1 and Cohen's kappa.
5. Hallucination and rubric-error flag agreement: Cohen's kappa.
6. Reviewer confidence reliability: Brier score against adjudicated correctness.

Operational targets:
1. Holistic QWK `>= 0.75`.
2. Criterion macro kappa `>= 0.70`.
3. Decision kappa `>= 0.70`.
4. Fallacy macro F1 `>= 0.75`.
5. Flag kappa `>= 0.65`.

## 16) Reviewer Checklists

### A) Pre-Review Checklist

1. Confirm assigned `review_batch_id` and protocol version.
2. Confirm current prompt/schema versions used in the case.
3. Confirm access to queue file and review UI.
4. Confirm calibration status is active.
5. Confirm no conflict of interest for assigned examples.

### B) Per-Case Review Checklist

1. Read prompt and full essay before inspecting model output.
2. Validate score reasonableness against essay evidence.
3. Verify rubric criteria and criterion evidence alignment.
4. Verify reasoning coherence and completeness.
5. Verify fallacy decision against explicit text evidence.
6. Verify feedback is specific, actionable, and respectful.
7. Check for hallucinated statements or fabricated evidence.
8. Choose one decision: `accept`, `reject`, or `edit`.
9. Set `hallucination` and `rubric_error` flags accurately.
10. If `edit`, provide corrected JSON and concise notes.
11. Record reviewer confidence for the decision.

### C) Adjudicator Checklist

1. Confirm adjudication trigger reason.
2. Compare conflicting reviewer decisions and notes.
3. Resolve score/rubric/fallacy disagreements with evidence.
4. Finalize flags and final decision.
5. Record adjudication rationale and completion timestamp.

### D) QA Lead Checklist

1. Compute agreement metrics for overlap set.
2. Run schema and validator checks on reviewed outputs.
3. Sample accepted/edit cases for manual audit.
4. Review drift trends by reviewer and task.
5. Issue retraining or recalibration actions if thresholds fail.
6. Publish batch QA summary with pass/fail status.

## 17) Decision Logging Requirements

Each submitted review record must include:
1. `case_id`
2. `reviewer_id`
3. `decision`
4. `selected_teacher_model` when applicable
5. `edited_output` for edit decisions
6. `flags.hallucination`
7. `flags.rubric_error`
8. reviewer `notes`
9. `created_at`

## 18) Release Criteria for Gold Merge

A review batch is eligible for merge when all conditions hold:
1. QA thresholds pass.
2. All adjudication-required cases are resolved.
3. No blocking schema-validation errors remain.
4. Manifest and summary files are generated for the batch.

---

This protocol is intentionally strict to maximize supervision quality and reproducibility before SFT dataset construction.
