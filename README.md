# neuroimaging-go-brrrr

Upload BIDS neuroimaging datasets to HuggingFace Hub.

## Supported Datasets

| Dataset | Source | HuggingFace | Size | License |
|---------|--------|-------------|------|---------|
| ARC (Aphasia Recovery Cohort) | [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884) | [hugging-science/arc-aphasia-bids](https://hf.co/datasets/hugging-science/arc-aphasia-bids) | 293 GB | CC0 |
| ISLES 2024 | [Zenodo 17652035](https://zenodo.org/records/17652035) | [hugging-science/isles24-stroke](https://hf.co/datasets/hugging-science/isles24-stroke) | ~100 GB | CC BY-NC-SA 4.0 |

## Installation

```bash
# Clone the repository
git clone https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr.git
cd neuroimaging-go-brrrr

# Install dependencies
uv sync --all-extras
```

## Quick Start

### ARC Dataset

```bash
# Validate local download
uv run bids-hub arc validate data/openneuro/ds004884

# Build and upload to HuggingFace
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
```

### ISLES24 Dataset

```bash
# Validate local download
uv run bids-hub isles24 validate data/zenodo/isles24/train

# Build and upload to HuggingFace
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
```

## Architecture

```text
src/bids_hub/
├── __init__.py          # Public API re-exports
├── cli.py               # Typer CLI
├── core/                # Generic BIDS→HF utilities
│   ├── builder.py       # build_hf_dataset, push_dataset_to_hub
│   ├── config.py        # DatasetBuilderConfig
│   └── utils.py         # File discovery helpers
├── datasets/            # Per-dataset modules
│   ├── arc.py           # ARC schema + pipeline
│   └── isles24.py       # ISLES24 schema + pipeline
└── validation/          # Per-dataset validation
    ├── base.py
    ├── arc.py
    └── isles24.py
```

See [docs/explanation/architecture.md](docs/explanation/architecture.md) for details.

## Usage (Python API)

```python
from datasets import load_dataset

# Load from HuggingFace
ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")

# Access a session
example = ds[0]
print(example["subject_id"])  # "sub-M2001"
print(example["t1w"])         # NIfTI array
print(example["wab_aq"])      # Aphasia severity score

# Filter by T2w acquisition type (for paper replication)
space_only = ds.filter(
    lambda x: (
        x["lesion"] is not None
        and x["t2w"] is not None
        and x["t2w_acquisition"] in ("space_2x", "space_no_accel")
    )
)
```

## Citation

If you use the ARC dataset, please cite:

### Paper

> Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. The Aphasia Recovery Cohort, an open-source chronic stroke repository. Scientific Data. 2024;11:981. doi:[10.1038/s41597-024-03819-7](https://doi.org/10.1038/s41597-024-03819-7).

### Dataset

> Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. Aphasia Recovery Cohort (ARC). OpenNeuro [dataset]. 2023. doi:[10.18112/openneuro.ds004884.v1.0.1](https://doi.org/10.18112/openneuro.ds004884.v1.0.1).

## Roadmap

| Priority | Task | Status |
|----------|------|--------|
| 1 | Add `t2w_acquisition` field to ARC schema | [PR #13](https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr/pull/13) |
| 2 | Monitor upstream `datasets` PR #7896 | Tracking |
| 3 | Add ATLAS v2.0 dataset support | Planned |

## References

- [HuggingFace Datasets - NIfTI](https://huggingface.co/docs/datasets/nifti_dataset)
- [BIDS Specification](https://bids-specification.readthedocs.io/)
- [nibabel Documentation](https://nipy.org/nibabel/)
- [OpenNeuro](https://openneuro.org)

## License

**This package**: Apache-2.0

**ARC dataset**: CC0 (Public Domain) via OpenNeuro

**ISLES24 dataset**: CC BY-NC-SA 4.0 via Zenodo
