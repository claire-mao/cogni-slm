# Candidate Gold Sampling Report

- Source dataset: `datasets/training/`
- Total source examples: `12413`
- Sample size: `100`
- Random seed: `20260709`

## Method

- Prompt/topic coverage: hard prompt quotas (balanced across 8 prompt IDs).
- Score stratification: global score-decile balancing target (10 per decile).
- Length stratification: global short/medium/long balancing target (34/33/33).
- Writing quality coverage: prompt-normalized low/medium/high balancing target (34/33/33).
- Diversity objective: lexical novelty bonus within each prompt to increase topical/angle spread.

## Selected Distribution

### Prompt ID

- prompt `1`: `13`
- prompt `2`: `13`
- prompt `3`: `12`
- prompt `4`: `12`
- prompt `5`: `13`
- prompt `6`: `13`
- prompt `7`: `12`
- prompt `8`: `12`

### Score Decile

- decile `0`: `10`
- decile `1`: `10`
- decile `2`: `10`
- decile `3`: `9`
- decile `4`: `10`
- decile `5`: `9`
- decile `6`: `10`
- decile `7`: `10`
- decile `8`: `11`
- decile `9`: `11`

### Essay Length Band

- short: `34`
- medium: `33`
- long: `33`

### Quality Band

- low: `34`
- medium: `33`
- high: `33`

## Range Checks

- score min/max/mean: `0.0000` / `50.0000` / `8.6500`
- essay_length min/max/mean: `40` / `921` / `303.90`

## Files

- `candidate_gold.jsonl`
- `manifest.json`
- `sampling_report.md`
- SHA256 (`candidate_gold.jsonl`): `b741d49588fa63ba811cd9bc059057250cce4c6082da5efd0b1dc3f415677ca0`

## Output Schema (per row)

- `example_id`
- `original_dataset`
- `original_id`
- `score`
- `prompt_id`
- `essay_length`
- `sampling_reason`
