# Teacher Benchmark Framework

Offline benchmarking utilities for evaluating teacher-model outputs against:

- `datasets/gold/gold_v1.jsonl`

No provider APIs are called by this framework.

## Run

```bash
python3 scripts/run_teacher_benchmark.py \
  --gold-path datasets/gold/gold_v1.jsonl \
  --predictions-path <predictions.jsonl-or-dir> \
  --output-root outputs/teacher_benchmark
```

## Required Gold Fields

- `example_id`
- `source`
- `license`
- `prompt`
- `essay`
- `gold_score` (optional but used for scoring metrics)
- `rubric`
- `difficulty`
- `expected_reasoning_skills`
- `expected_fallacies`
- `notes_for_reviewers`

## Expected Prediction Fields

Per-row JSONL fields should include:

- `example_id`
- `model_id` or `model`

Supported optional fields:

- score: `score_prediction` or `predicted_score`
- rubric: `rubric_items` or `rubric_adherence_score`
- reasoning: `reasoning_skills` or `logical_reasoning_score`
- argument quality: `argument_quality_score`
- fallacies: `fallacy_label` or `predicted_fallacies`
- feedback: `educational_feedback` or `feedback`
- JSON validity: `json_valid` or `raw_output`
- latency: `latency_ms`
- token usage: `input_tokens`/`output_tokens` or `token_usage.*`
- cost: `cost_usd` (estimated from token pricing if omitted and available)

## Outputs

Each run writes to `outputs/teacher_benchmark/<run_id>/`:

- `manifest.json`
- `model_summary.json`
- `model_summary.csv`
- `per_example_metrics.jsonl`
- `report.md`

## Production SFT Pipeline

Use `src.teacher.generate_labels` to run the production label-generation pipeline:

dataset -> teacher inference -> validation -> quality filter ->
JSON schema validation -> confidence filter -> dataset export

CLI entrypoint:

```bash
python3 -m src.teacher.generate_labels \
  --input-jsonl datasets/gold/gold_v1.jsonl \
  --inference-mode precomputed \
  --predictions-path <predictions.jsonl-or-dir> \
  --output-root datasets/sft
```

No provider API inference is executed in this module. Supply precomputed outputs.
