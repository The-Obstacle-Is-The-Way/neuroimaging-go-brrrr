.PHONY: help install lint format typecheck test test-cov clean pre-commit all

help:
	@echo "Available targets:"
	@echo "  all         - Run lint, typecheck, and test"
	@echo "  install     - Install dependencies with uv"
	@echo "  lint        - Run ruff linter"
	@echo "  format      - Format code with ruff"
	@echo "  typecheck   - Run mypy type checker"
	@echo "  test        - Run pytest"
	@echo "  test-cov    - Run pytest with coverage"
	@echo "  pre-commit  - Run pre-commit on all files"
	@echo "  clean       - Remove build artifacts"

all: lint typecheck test

install:
	uv sync --all-extras

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

test:
	uv run pytest

test-cov:
	uv run pytest --cov=bids_hub --cov-report=term-missing

pre-commit:
	uv run pre-commit run --all-files

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete