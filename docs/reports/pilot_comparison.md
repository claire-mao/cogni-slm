# Pilot Comparison (pilot_v1)

Date: 2026-07-09
Run analyzed: `outputs/teacher_runs/pilot_v1/summary.json`

## Executive Finding

The requested live pilot (`pilot_v1`) did **not complete inference**. It was blocked during provider credential validation, so there are no measured teacher outputs for GPT-5, Claude Opus 4, or DeepSeek R1.

Because no live responses were produced, the requested model comparison metrics cannot be computed from this run.

## Evidence

Source artifact: `outputs/teacher_runs/pilot_v1/summary.json`

- `status`: `blocked_preflight`
- `inference_executed`: `false`
- failure message: provider configuration validation failed due to missing `.env` keys for OpenAI, Anthropic, and DeepSeek

Additional context:
- Existing `teacher-runs-smoke` and `round1_teacher_validation` artifacts are `dry_run` outputs with synthetic provider responses and zero token/cost usage, so they are not valid for live pilot ranking.

## Requested Metric Comparison

| Metric | GPT-5 | Claude Opus 4 | DeepSeek R1 | Status |
|---|---:|---:|---:|---|
| QWK | N/A | N/A | N/A | Not measurable (no live outputs) |
| MAE | N/A | N/A | N/A | Not measurable (no live outputs) |
| Rubric adherence | N/A | N/A | N/A | Not measurable (no live outputs) |
| Feedback quality | N/A | N/A | N/A | Not measurable (no live outputs) |
| Hallucination rate | N/A | N/A | N/A | Not measurable (no live outputs) |
| JSON validity | N/A | N/A | N/A | Not measurable (no live outputs) |
| Logical reasoning | N/A | N/A | N/A | Not measurable (no live outputs) |
| Fallacy detection | N/A | N/A | N/A | Not measurable (no live outputs) |
| Agreement with gold | N/A | N/A | N/A | Not measurable (no live outputs) |
| Latency | N/A | N/A | N/A | Not measurable (no live outputs) |
| Cost | N/A | N/A | N/A | Not measurable (no live outputs) |

## Recommendations (Evidence-Constrained)

Using measured results from `pilot_v1`, no ranking is currently defensible.

- Best overall teacher: **Not determinable** (no measured pilot outputs)
- Best verifier: **Not determinable** (no measured pilot outputs)
- Best cost/performance: **Not determinable** (no measured pilot outputs)

## What is required to produce the requested ranking

To generate a valid comparison and recommendations, complete one successful live pilot run with:

1. Provider credentials present in `.env`:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `DEEPSEEK_API_KEY`
2. Re-run the pilot with the same run id (`pilot_v1`) to use resume/checkpoint support.
3. Confirm artifacts exist after execution:
   - `outputs/teacher_runs/pilot_v1/responses.jsonl`
   - `outputs/teacher_runs/pilot_v1/summary.json`
   - checkpoint/progress metadata
4. Compute metric tables from those live responses against `datasets/gold/pilot20_v1.jsonl`.

Once those artifacts are available, I can generate the full metric comparison and concrete model recommendations immediately.
