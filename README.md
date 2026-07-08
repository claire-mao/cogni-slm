# Cogni

Cogni is a small language model project focused on teaching logical fallacies through structured analogical reasoning.

This repository is currently scaffolded for production-grade development workflows. It intentionally does not include training code yet.

## Repository Layout

- `src/` - Core Python package code.
- `configs/` - Version-controlled configuration files.
- `datasets/raw/` - Immutable source datasets.
- `datasets/processed/` - Cleaned and transformed datasets.
- `datasets/eval/` - Evaluation and benchmark datasets.
- `docs/` - Design docs and technical documentation.
- `notebooks/` - Exploratory analysis notebooks.
- `scripts/` - Repeatable operational scripts.
- `tests/` - Unit and integration tests.
- `models/` - Model artifact placeholders and metadata.
- `outputs/` - Generated outputs, logs, and reports.

## Quick Start

1. Create a virtual environment.
2. Install the project in editable mode with dev tooling.
3. Run checks with `make lint`, `make test`, and `make format`.

## Status

- Project scaffold complete.
- ML/training implementation intentionally deferred.
