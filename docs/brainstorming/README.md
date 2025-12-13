# bids-hub

> **Note: This repository has been consolidated into [neuroimaging-go-brrrr](https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr).**
>
> `bids-hub` has been re-vendored and integrated into our unified neuroimaging platform. All active development now continues there. This repository is archived for reference but is **no longer actively maintained**.
>
> **New location:** <https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr>

---

Upload BIDS neuroimaging datasets to HuggingFace Hub.

## Supported Datasets

| Dataset | Source | HuggingFace | Size | License |
|---------|--------|-------------|------|---------|
| ARC (Aphasia Recovery Cohort) | [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884) | [hugging-science/arc-aphasia-bids](https://hf.co/datasets/hugging-science/arc-aphasia-bids) | 293 GB | CC0 |
| ISLES 2024 | [Zenodo 17652035](https://zenodo.org/records/17652035) | [hugging-science/isles24-stroke](https://hf.co/datasets/hugging-science/isles24-stroke) | ~100 GB | CC BY-NC-SA 4.0 |

## Quick Start

### ARC Dataset
```bash
# Validate local download
uv run bids-hub arc validate data/openneuro/ds004884

# Upload to HuggingFace
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
```

### ISLES24 Dataset
```bash
# Validate local download
uv run bids-hub isles24 validate data/zenodo/isles24/train

# Upload to HuggingFace
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
```

## Architecture

```
src/bids_hub/
├── __init__.py          # Public API re-exports
├── cli.py               # Typer CLI
├── core/                # Generic BIDS→HF utilities
│   ├── __init__.py
│   ├── builder.py       # build_hf_dataset, push_dataset_to_hub
│   ├── config.py        # DatasetBuilderConfig
│   └── utils.py         # File discovery helpers
├── datasets/            # Per-dataset modules
│   ├── __init__.py
│   ├── arc.py           # ARC schema + pipeline
│   └── isles24.py       # ISLES24 schema + pipeline
└── validation/          # Per-dataset validation
    ├── __init__.py
    ├── base.py
    ├── arc.py
    └── isles24.py
```

See [docs/explanation/architecture.md](docs/explanation/architecture.md) for details.

## Citation

If you use the ARC dataset, please cite both the paper and the dataset:

### Paper

> Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. The Aphasia Recovery Cohort, an open-source chronic stroke repository. Scientific Data. 2024;11:981. doi:10.1038/s41597-024-03819-7.

### Dataset

> Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. Aphasia Recovery Cohort (ARC). OpenNeuro [dataset]. 2023. doi:10.18112/openneuro.ds004884.v1.0.1.

## References

- Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. *The Aphasia Recovery Cohort, an open-source chronic stroke repository.* Scientific Data. 2024;11:981. doi:[10.1038/s41597-024-03819-7](https://doi.org/10.1038/s41597-024-03819-7).

- Gibson M, Newman-Norlund R, Bonilha L, Fridriksson J, Hickok G, Hillis AE, den Ouden DB, Rorden C. *Aphasia Recovery Cohort (ARC).* OpenNeuro [dataset]. 2023. doi:[10.18112/openneuro.ds004884.v1.0.1](https://doi.org/10.18112/openneuro.ds004884.v1.0.1).

- OpenNeuro. *OpenNeuro brain imaging data repository.* CC0-licensed BIDS datasets. <https://openneuro.org>.

- [HuggingFace Datasets - NIfTI](https://huggingface.co/docs/datasets/nifti_dataset)
- [BIDS Specification](https://bids-specification.readthedocs.io/)
- [nibabel Documentation](https://nipy.org/nibabel/)

## License

**This package**: Apache-2.0

**ARC dataset**: The ARC dataset (OpenNeuro ds004884) is released under a Creative Commons CC0 license via OpenNeuro, meaning it can be freely reused, redistributed, and mirrored (including to Hugging Face), with appropriate scholarly citation.
