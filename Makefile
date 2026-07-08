PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: setup install-dev lint format format-check test ci precommit-install precommit-run clean

setup:
	$(PIP) install --upgrade pip
	$(PIP) install -e .[dev]

install-dev: setup

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

format:
	$(PYTHON) -m ruff check --fix .
	$(PYTHON) -m black .

format-check:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m black --check .

test:
	$(PYTHON) -m pytest

ci: lint format-check test

precommit-install:
	$(PYTHON) -m pre_commit install

precommit-run:
	$(PYTHON) -m pre_commit run --all-files

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache .mypy_cache .venv build dist *.egg-info
