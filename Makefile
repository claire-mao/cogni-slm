PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: install-dev test lint format clean

install-dev:
	$(PIP) install -e .[dev]

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff check --fix .

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
