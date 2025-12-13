# Contributing to neuroimaging-go-brrrr

Thank you for your interest in contributing!

## Development Setup

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (required)
- Docker (optional, for DeepISLES inference)

### Installation

```bash
# Clone the repository
git clone https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr.git
cd neuroimaging-go-brrrr

# Install dependencies (including dev extras)
uv sync --all-extras

# Install pre-commit hooks
uv run pre-commit install
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=bids_hub

# Run a specific test
uv run pytest tests/test_arc.py::TestBuildArcFileTable -v
```

### Code Quality

```bash
# Lint
uv run ruff check .

# Format
uv run ruff format .

# Type check (strict)
uv run mypy src tests

# Run all checks
make all
```

## Pull Request Process

1. **Fork** the repository and create a branch from `main`
2. **Make changes** following the code style below
3. **Add tests** for any new functionality
4. **Run the full test suite** (`make all`) to ensure nothing breaks
5. **Update documentation** if you changed public APIs
6. **Submit PR** with a clear description of changes

## Code Style

- **Formatting**: `ruff format` is authoritative
- **Linting**: `ruff check` must pass
- **Types**: Strict `mypy` compliance required
- **Imports**: Use `from __future__ import annotations`
- **Docstrings**: Google style for public functions

## Adding a New Dataset

See [docs/explanation/architecture.md](docs/explanation/architecture.md) for the step-by-step guide.

In brief:

1. Create `src/bids_hub/datasets/newdataset.py` with schema and file discovery
2. Create `src/bids_hub/validation/newdataset.py` with validation rules
3. Add CLI subcommands in `src/bids_hub/cli.py`
4. Update exports in `__init__.py` files
5. Add tests in `tests/`

## Testing with Real Data

Tests use synthetic BIDS structures by default. If you have access to real datasets:

```bash
# ARC (OpenNeuro ds004884)
uv run bids-hub arc validate data/openneuro/ds004884

# ISLES24 (Zenodo)
uv run bids-hub isles24 validate data/zenodo/isles24/train
```

## Known Issues

See [docs/upstream/huggingface-datasets-7894.md](docs/upstream/huggingface-datasets-7894.md) for the `Sequence(Nifti())` sharding bug and our workaround.

## Questions?

Open an issue on GitHub for questions or discussion.
