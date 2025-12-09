# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This package uploads BIDS neuroimaging datasets (ARC, ISLES24) to HuggingFace Hub. It converts BIDS-formatted NIfTI files to HuggingFace's `Dataset` format with proper `Nifti()` feature types.

## Commands

```bash
# Install dependencies
uv sync --all-extras

# Run tests
uv run pytest

# Run single test
uv run pytest tests/test_arc.py::TestBuildArcFileTable::test_build_file_table_returns_dataframe -v

# Lint
uv run ruff check .

# Type check (strict)
uv run mypy src tests

# Pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files

# ARC commands
uv run bids-hub arc validate data/openneuro/ds004884
uv run bids-hub arc build data/openneuro/ds004884 --dry-run
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
uv run bids-hub arc info

# ISLES24 commands
uv run bids-hub isles24 validate data/zenodo/isles24/train
uv run bids-hub isles24 build data/zenodo/isles24/train --dry-run
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
uv run bids-hub isles24 info
```

## Architecture

### Data Flow

```text
BIDS Dataset (Local)
        │
        ▼ build_file_table()
pandas DataFrame (paths + metadata)
        │
        ▼ build_hf_dataset()
datasets.Dataset with Nifti() features
        │
        ▼ push_dataset_to_hub(num_shards=N)
HuggingFace Hub
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| `core/builder.py` | Generic BIDS→HF conversion (build_hf_dataset, push_dataset_to_hub) |
| `core/config.py` | DatasetBuilderConfig dataclass |
| `core/utils.py` | File discovery helpers (find_single_nifti, find_all_niftis) |
| `datasets/arc.py` | ARC schema, file discovery, pipeline |
| `datasets/isles24.py` | ISLES24 schema, file discovery, pipeline |
| `validation/base.py` | Generic validation framework |
| `validation/arc.py` | ARC validation rules |
| `validation/isles24.py` | ISLES24 validation rules |
| `cli.py` | Typer CLI with subcommands |

## Dataset Schemas

### ARC Schema (one row per SESSION)

```python
Features({
    "subject_id": Value("string"),    # e.g., "sub-M2001"
    "session_id": Value("string"),    # e.g., "ses-1"
    "t1w": Nifti(),                   # T1-weighted structural
    "t2w": Nifti(),                   # T2-weighted structural
    "flair": Nifti(),                 # FLAIR structural
    "bold": Sequence(Nifti()),        # fMRI 4D time-series (list of runs)
    "dwi": Sequence(Nifti()),         # Diffusion-weighted (list of runs)
    "sbref": Sequence(Nifti()),       # Single-band reference (list of runs)
    "lesion": Nifti(),                # Expert lesion mask
    "age_at_stroke": Value("float32"),
    "sex": Value("string"),
    "wab_aq": Value("float32"),       # Aphasia severity score
    "wab_type": Value("string"),
})
```

### ISLES24 Schema (one row per SUBJECT, flattened)

```python
Features({
    "subject_id": Value("string"),
    # Acute (ses-01)
    "ncct": Nifti(),
    "cta": Nifti(),
    "ctp": Nifti(),
    # Perfusion Maps
    "tmax": Nifti(),
    "mtt": Nifti(),
    "cbf": Nifti(),
    "cbv": Nifti(),
    # Follow-up (ses-02)
    "dwi": Nifti(),
    "adc": Nifti(),
    # Masks
    "lesion_mask": Nifti(),
    "lvo_mask": Nifti(),
    "cow_segmentation": Nifti(),
    # Metadata
    "age": Value("float32"),
    "sex": Value("string"),
    "nihss_admission": Value("float32"),
    "mrs_admission": Value("float32"),
    "mrs_3month": Value("float32"),
})
```

## Testing

Tests use synthetic BIDS structures with minimal NIfTI files (2x2x2 voxels). The fixtures `synthetic_bids_root` (ARC) and `synthetic_isles24_root` (ISLES24) create complete datasets with all modalities for comprehensive coverage.

Key test patterns:
- `_create_minimal_nifti()`: Creates valid NIfTI files quickly
- Mocking `push_dataset_to_hub` for dry-run tests
- Validation tests check counts against paper/challenge expectations
