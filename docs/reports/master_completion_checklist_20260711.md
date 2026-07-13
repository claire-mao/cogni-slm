# Master Completion Checklist (2026-07-11)

This checklist maps your requested plan to current project state.

Status legend:
- DONE = completed with evidence
- PARTIAL = started/completed locally but not complete for production
- BLOCKED = cannot complete in this environment right now

## Define the Problem

- [x] Choose one narrow behavior — **DONE**
  - Evidence: `docs/problem.md`, `docs/behavior_spec.md`
- [x] Verify it fails the prompt test — **DONE**
  - Evidence: `outputs/evaluation/prompt_test_public_v1/summary.json` (`overall_pass_rate=0.0`)
- [x] Write the Behavior Spec (pass/fail) — **DONE**
  - Evidence: `docs/behavior_spec.md`

## Brainlift

- [x] Research existing work — **DONE**
- [x] Research the base model — **DONE**
- [x] Research QLoRA + Unsloth — **DONE**
- [x] Research evaluation methods — **DONE**
  - Evidence (all): `docs/literature_review.md`, `docs/brainlift.md`

## PRD

- [x] Problem statement — **DONE**
- [x] Behavior Spec — **DONE**
- [x] Dataset plan — **DONE**
- [x] Training plan — **DONE**
- [x] Evaluation plan — **DONE**
- [x] Success metrics — **DONE**
  - Evidence: `docs/prd.md`

## AI Planning

- [x] Ask AI for end-to-end architecture — **DONE**
- [x] Mermaid workflow — **DONE**
- [x] Milestones — **DONE**
- [x] Tickets — **DONE**
- [x] Dependencies — **DONE**
- [x] Risks — **DONE**
  - Evidence: `docs/project_architecture.md`, `docs/architecture.mmd`, `docs/roadmap.md`, `docs/project_board.md`

## Environment

- [x] Create GitHub repo — **DONE**
  - Evidence: `.git`, `origin=https://github.com/claire-mao/cogni-slm.git`
- [x] Configure Git — **DONE**
- [x] Create `.env.example` — **DONE**
- [x] Install dependencies — **DONE (local)**
- [x] Configure linting/formatting — **DONE**
  - Evidence: `pyproject.toml`
- [x] Verify base model runs locally — **DONE**
  - Evidence: `outputs/inference_offline_qwen06/report.md`
- [x] Set up Unsloth — **DONE (Google Colab A100)**
  - Evidence: successful 840-step QLoRA run; see `docs/reports/final_ap_tutor_results.md`
- [ ] Set up Hugging Face — **PARTIAL/BLOCKED (network)**
  - Evidence: offline local cache works; publish/login steps blocked by reviewer/network gate
- [x] Set up inference notebook/script — **DONE**
  - Evidence: `scripts/run_inference.py`, `src/inference/run_inference.py`

## Evaluation (Before Training)

- [x] Write evaluation rubric — **DONE**
  - Evidence: `docs/evaluation_design.md`, `src/evaluation/judge.py`
- [x] Build LLM-as-judge — **DONE**
  - Evidence: `src/evaluation/llm_judge.py`
- [x] Build held-out evaluation set — **DONE**
  - Evidence: `datasets/eval/heldout_benchmark_public_v1.jsonl`, `scripts/build_public_heldout_set.py`
- [x] Build base vs. tuned comparison — **DONE**
  - Evidence: `evaluation/run_harness.py`
- [x] Run baseline evaluation — **DONE**
  - Evidence: `outputs/evaluation/baseline_public_v1/baseline_results.json`

## Data Pipeline

- [x] Design teacher prompt — **DONE**
  - Evidence: `teacher_prompts/production_teacher.txt`, `docs/teacher_prompt.md`
- [x] Generate dataset — **DONE (local)**
  - Evidence: `datasets/sft/train.jsonl`, `datasets/sft/validation.jsonl`, `datasets/sft/test.jsonl`
- [x] Filter low-quality examples — **DONE**
  - Evidence: `datasets/sft/quality_report.json`, `datasets/sft/quality_report.md`
- [x] Deduplicate — **DONE**
  - Evidence: `docs/reports/deduplication.md`
- [x] Split train/validation/test — **DONE**
  - Evidence: `datasets/sft/train.jsonl`, `datasets/sft/validation.jsonl`, `datasets/sft/test.jsonl`
- [ ] Publish dataset — **BLOCKED (source licensing)**
  - Evidence: dataset exists locally; public release is prohibited by `configs/release/source_licenses.json`

## Training

- [x] Configure QLoRA — **DONE**
  - Evidence: `notebooks/train_ap_tutor_production_colab.ipynb`
- [x] Train v1 — **DONE**
  - Evidence: Qwen3-1.7B A100 production run completed in Google Colab
- [x] Save checkpoints — **DONE**
  - Evidence: checkpoint artifacts saved in the production model directory on Drive
- [x] Export adapter/model — **DONE**
  - Evidence: Drive `adapter/` and `merged_16bit/`

## Evaluation

- [x] Run tuned model on held-out set — **DONE**
  - Evidence: 756/756 tuned predictions; `docs/reports/final_ap_tutor_results.md`
- [x] Compare base vs. tuned — **DONE**
  - Evidence: strict behavior 0.0% base vs. 99.3% tuned
- [x] Analyze failures — **DONE**
  - Evidence: full 756-example Claude semantic audit and `docs/reports/final_ap_tutor_results.md`
- [x] Identify data issues — **DONE**
  - Evidence: 1,898 label spellings and 1,701 rare spellings identified during quality review

## Iterate

- [ ] Improve dataset — **FUTURE WORK**
  - Status: canonical label ontology recommended
- [ ] Retrain & Re-evaluate — **FUTURE WORK**
  - Status: rerun after label canonicalization if the project continues
- [x] Document improvements — **DONE FOR V1**
  - Evidence: `docs/reports/final_ap_tutor_results.md`

## Deliverables

- [x] BrainLift — **DONE** (`docs/brainlift.md`)
- [x] PRD — **DONE** (`docs/prd.md`)
- [x] Dataset (primary artifact) — **DONE (local)** (`datasets/sft/`)
- [x] Fine-tuned model — **DONE (Drive)** (adapter, checkpoints, and merged model)
- [x] Evaluation harness — **DONE** (`evaluation/run_harness.py`)
- [x] Base vs. tuned results — **DONE** (`docs/reports/final_ap_tutor_results.md`)
- [x] Error analysis — **DONE** (`docs/reports/final_ap_tutor_results.md`)
- [ ] Hugging Face model — **BLOCKED (source licensing; private upload optional)**

## Release Blocker

Public dataset and model publication remain blocked because multiple incorporated
sources do not have verified redistribution licenses. The artifacts must remain
private unless permissions are obtained or the dataset and model are rebuilt from
approved sources.
