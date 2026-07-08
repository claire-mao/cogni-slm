# Development README

This guide describes the local development workflow for Cogni.

## 1. Prerequisites
- Python 3.10+
- Git

## 2. Environment Setup
1. Create and activate a virtual environment.
2. Copy `.env.example` to `.env` and fill in required values.
3. Install development dependencies:

```bash
make setup
```

## 3. Common Commands
- Install/update development dependencies: `make setup`
- Run lints: `make lint`
- Run formatters: `make format`
- Verify formatting only: `make format-check`
- Run tests: `make test`
- Run full local CI checks: `make ci`
- Install pre-commit hooks: `make precommit-install`
- Run pre-commit on all files: `make precommit-run`

## 4. Project Quality Gates
Before pushing changes:
1. `make format`
2. `make lint`
3. `make test`
4. `make precommit-run`

## 5. CI
GitHub Actions runs linting and tests for Python 3.10 and 3.11 on pushes and pull requests.

## 6. Notes
- Do not commit secrets. Keep credentials in `.env` only.
- ML training and dataset generation are intentionally deferred until design milestones are complete.
