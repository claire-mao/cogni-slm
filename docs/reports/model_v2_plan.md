# Model v2 Plan

## 1) Evidence From v1 Artifacts

### Training status

- `outputs/training_runs/run_v1/run_v1/run_summary.json` shows the only Phase 1 run failed on `2026-07-09` with: `Unsloth cannot find any torch accelerator? You need a GPU.`
- `outputs/experiments/20260709T175524Z-p1_baseline/manifest.json` confirms `gpu.available=false`, no adapters, no merged model, and no train/eval rows.

### Evaluation status

- `docs/reports/model_v1_results.md` is explicitly a dry-run harness comparison, not a true trained-model result.
- Reported v1 deltas (QWK/MAE changes) are useful only as pipeline smoke tests.

### Error-analysis signal

- `docs/reports/model_v1_error_analysis.md` identifies highest-impact issues:
  1. Missing structured rubric/fallacy supervision.
  2. Templated shallow reasoning.
  3. Weak feedback grounding (unsupported feedback proxy high).
  4. Calibration gaps around score boundaries.

### Teacher-output signal

- `docs/reports/teacher_round1_analysis.md` and `outputs/teacher_round1/round1_teacher_validation/summary.json` show Round 1 used `dry_run=true`.
- All teacher quality metrics were effectively tied; no meaningful teacher-quality separation is available yet.

### Data readiness

- `datasets/sft/build_report.md` shows SFT exports are valid format-wise but empty (`train=0`, `validation=0`, `test=0`), so no production training can proceed.

## 2) v2 Objectives

1. Convert pipeline-valid artifacts into quality-valid artifacts (live teacher outputs + non-empty reviewed data).
2. Improve supervision quality for rubric adherence, fallacy detection, reasoning depth, and grounded feedback.
3. Run a real first training cycle with traceable experiment metadata and calibrated evaluation.

## 3) Immediate Unblockers (Must Pass Before Any v2 Training)

1. **Compute gate**
- Confirm at least one supported GPU environment for Unsloth QLoRA.
- Abort condition: any run reports `torch accelerator` missing.

2. **Teacher-inference gate**
- Execute non-dry-run teacher validation on a pilot slice (24 examples) with strict JSON validation enabled.
- Abort condition: JSON validity `< 0.98` for any primary candidate.

3. **Data gate**
- Build non-empty reviewed gold dataset and regenerate SFT splits.
- Minimum launch threshold for first v2 training: `>=300` train examples and `>=50` validation examples.
- Abort condition: any split count is zero.

4. **Traceability gate**
- Every run must include dataset checksum, prompt version hash, teacher version, git commit, runtime, and GPU metadata.

## 4) New Teacher Prompt Strategy (v2)

Create two new production prompt variants under `teacher_prompts/versions/` and compare directly.

### Prompt v2A: Evidence-anchored analytic

- Require criterion-level evidence anchors (short quoted spans or paraphrase anchors).
- Require each reasoning step to include:
  - claim being evaluated
  - essay evidence
  - inference to rubric impact
- Require explicit uncertainty statement when confidence `<0.70`.
- Enforce non-generic feedback by requiring references to specific essay content.

### Prompt v2B: Concise calibrated

- Same schema contract, but tighter response-length controls to reduce verbosity and cost.
- Add stricter confidence rubric:
  - high confidence only if rubric criteria and fallacy evidence are both complete.

### Schema updates recommended for v2 (backward-compatible migration)

1. Add `rubric.criteria[].evidence_anchor`.
2. Add `reasoning.steps[].evidence_anchor` (or structured step object).
3. Add `fallacies.candidates` with `label`, `present`, `evidence_anchor`.
4. Add `feedback.priorities[].justification`.
5. Add `confidence_rationale` (short string).

Use schema versioning (`output_schema_v2.json`) and keep v1 compatibility in loaders.

## 5) New Data Collection Plan (v2)

Build a targeted supervision set focused on failure modes, then merge through existing review workflows.

### Target collection blocks (next increment: +300 reviewed examples)

1. **Score-boundary block (100)**
- Essays near adjacent score bands to improve calibration and MAE/QWK sensitivity.

2. **Rubric-coverage block (80)**
- Essays with mixed performance across claim/evidence/reasoning/organization/style to force criterion discrimination.

3. **Fallacy block (60)**
- Balanced positives/negatives across common fallacies and no-fallacy controls.

4. **Feedback-grounding block (60)**
- Examples where reviewers can clearly verify whether feedback is supported by essay evidence.

### Curation requirements

- Stratify by prompt, topic, length, and quality band.
- Deduplicate by essay text similarity before review.
- Require adjudication notes for disagreement cases.
- Store reviewer confidence and rationale for auditing.

## 6) New Experiment Plan (v2)

### Phase T1: Live prompt screening (small)

- Data: 24 reviewed examples.
- Teachers: `gpt-5`, `o3`, `claude_sonnet_4`, `deepseek_r1`.
- Prompts: `v1`, `v2A`, `v2B`.
- Goal: select top prompt per teacher on structural quality.

Pass thresholds:
- JSON validity `>=0.99`
- missing-field rate `<=0.01`
- unsupported-feedback proxy reduced vs v1 baseline

### Phase T2: Gold100 teacher benchmark (full)

- Data: 100 reviewed examples.
- Teachers: all configured candidates (`GPT-5`, `o3`, `Claude Opus 4`, `Claude Sonnet 4`, `Gemini 2.5 Pro`, `DeepSeek R1`, `Qwen3`, `Llama 4 Maverick`).
- Repeats: 5 seeds.
- Measure: QWK, MAE, rubric adherence, fallacy F1, agreement, consistency, JSON validity, hallucination proxy, latency, cost.

Expected planning cost range from existing assumptions:
- One 100-example pass across all teachers: roughly `$30-$33`.
- Five-run repeatability suite: roughly `$151-$166`.

### Phase T3: Ensemble comparison

- Compare:
  - single teacher
  - majority vote
  - weighted score averaging
  - teacher + verifier
  - teacher + judge
- Candidate policy: keep ensemble only if quality gain is material (`>=1.5%` composite gain) at acceptable cost/latency.

### Phase T4: Pre-training quality gate

- Freeze teacher/prompt pair only after live evidence (not dry-run) confirms:
  - JSON validity `>=0.99`
  - hallucination proxy `<=0.10`
  - rubric adherence `>=0.85`
  - fallacy F1 `>=0.75`

## 7) New QLoRA Settings (v2)

Do not retrain now; prepare configs for execution once gates pass.

### Baseline-v2 (recommended first real run)

- `lora_rank=16`
- `lora_alpha=32`
- `learning_rate=1e-4`
- `num_train_epochs=3.0`
- `max_seq_length=1536`
- `batch_profile_id=bsz32` (fallback `bsz16` if memory constrained)
- `warmup_ratio=0.06`
- `packing=false`
- `optimizer=paged_adamw_8bit`

### Ablation set (minimal, high-signal)

1. **Capacity-up**: `rank=32`, `alpha=64`, `lr=1e-4`, `seq=2048`.
2. **Stability/calibration**: `rank=16`, `alpha=32`, `lr=7e-5`, `warmup=0.10`.
3. **Efficiency**: `rank=8`, `alpha=16`, `lr=2e-4`, `seq=1024`, `packing=true`.
4. **Higher-capacity control**: `rank=64`, `alpha=128`, `lr=8e-5`, `seq=2048`.

### QLoRA execution rules

- Stop early if validation MAE degrades for 3 consecutive eval checkpoints.
- Reject runs with schema-valid output rate `<0.98` on evaluation exports.
- Keep best checkpoint by composite metric:
  - `0.35*QWK + 0.20*(1-normalized_MAE) + 0.20*rubric_adherence + 0.15*fallacy_F1 + 0.10*feedback_quality`

## 8) v2 Success Criteria

v2 is considered successful only when all conditions are true:

1. At least one training run completes with saved adapters and merged model.
2. Evaluation is run on non-dry-run predictions.
3. Compared to base model, v2 shows:
- QWK improvement `>= +0.03`
- MAE reduction `>= 0.05`
- rubric adherence `>= 0.85`
- fallacy F1 `>= 0.75`
- JSON validity `>= 0.99`
- improved calibration (lower ECE and Brier than baseline)
4. Teacher pipeline demonstrates stable cost/latency within planned budget envelope.

## 9) Recommended Execution Order

1. Resolve compute and non-empty data gates.
2. Run T1 live prompt screening.
3. Run T2 Gold100 benchmark and pick top 3 teachers.
4. Run T3 ensemble comparison on shortlisted teachers.
5. Freeze teacher/prompt/schema versions.
6. Regenerate reviewed gold + SFT exports.
7. Execute Baseline-v2 training, then minimal ablations.
8. Publish v2 results and updated error analysis before scaling.
