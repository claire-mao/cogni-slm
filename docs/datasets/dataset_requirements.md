# Dataset v1 Input Requirements

Dataset v1 cannot be generated from current repository contents because no usable raw AP Language student essays are present.

## Required Input Files

Place source essays in `datasets/raw/` using one of these formats:

1. `.txt` or `.md`
- One essay per file.
- Filename should be a stable essay identifier (for example `essay_0001.txt`).

2. `.json`
- One essay object per file.
- Required keys:
  - `id` (string)
  - `essay` (string)

3. `.jsonl`
- One essay object per line.
- Required keys per line:
  - `id` (string)
  - `essay` (string)

## Content Requirements

- Essays must be real student argumentative responses (no synthetic placeholders).
- Essays must be licensable for model training and internal evaluation.
- Essays must be de-identified (no student PII).
- Essays should be long enough for rubric scoring (recommended minimum: 150 words).
- Domain should match AP Language argument writing.

## Metadata Requirements (Recommended)

If available, include:
- `source` (exam/prompt origin)
- `year`
- `prompt_id`
- `grade_level`
- `license`

These can be stored in the same JSON/JSONL object or a sidecar manifest.

## Minimum Quantity for Dataset v1

- Recommended minimum for first training run: `>= 500` essays.
- Absolute minimum for a smoke fine-tune: `>= 100` essays.
- Validation/test quality improves materially above `1,000` essays.

## Blocking Gaps (Current Repository)

- `datasets/raw/` contains only `.gitkeep`.
- Existing files in `datasets/processed/golden/` and `datasets/eval/heldout_benchmark.jsonl` are synthetic fallacy-task artifacts, not AP student essay corpora for rubric supervision.
