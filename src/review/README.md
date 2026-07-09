# Human Review Interface

Lightweight local UI to compare:

- gold answer
- selected teacher answer
- multiple teacher outputs

Reviewer actions:

- accept
- reject
- edit
- flag hallucination
- flag rubric error

Reviews are stored under `datasets/review/`.

## Entrypoint

```bash
python3 -m src.review.server \
  --gold-path datasets/gold/gold_v1.jsonl \
  --runs-root outputs/teacher_runs \
  --reviews-root datasets/review
```

Optional:

- `--source-run-id <run_id>` to lock review to one run.
- `--host` and `--port` to change binding.

No model inference is executed by this interface.
