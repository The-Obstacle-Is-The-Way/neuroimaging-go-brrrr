# Consolidation Strategy: neuroimaging-go-brrrr

> **Status**: Draft / Open for Discussion
> **Date**: 2024-12-05
> **Contributors**: Open to all

## Purpose

This repository consolidates neuroimaging tools and pipelines for working with BIDS datasets and NIfTI files. The goal is to coordinate community efforts, avoid duplication, and build practical demos for stroke lesion analysis and related use cases.

## What We're Building

### The Two Pipelines

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION PIPELINE                               │
│                        (Upload datasets to Hub)                          │
│                                                                          │
│   OpenNeuro BIDS ──► Validate ──► Convert ──► push_to_hub() ──► HF Hub   │
│                                                                          │
│   Tools: arc-aphasia-bids, stroke-deepisles-demo                         │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌───────────────────┐
                         │   HuggingFace Hub │
                         │   (NIfTI datasets)│
                         └───────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                       CONSUMPTION PIPELINE                               │
│                       (Load and visualize)                               │
│                                                                          │
│   load_dataset() ──► Stream ──► Decode NIfTI ──► NiiVue visualization    │
│                                                                          │
│   Tools: bids-neuroimaging Space, visualization notebooks                │
└──────────────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```text
neuroimaging-go-brrrr/
├── scripts/
│   ├── download_ds004884.sh
│   ├── push_to_hub_ds004884_full.py
│   └── visualization/
│       ├── ArcAphasiaBids.ipynb
│       └── ArcAphasiaBidsLoadData.ipynb
├── tools/
│   ├── arc-aphasia-bids/
│   └── bids-neuroimaging-space/  (git submodule)
├── docs/
│   └── brainstorming/
└── README.md
```

## Related Repositories

| Repository | Purpose | Link |
|------------|---------|------|
| neuroimaging-go-brrrr | Consolidation hub for neuroimaging tools | [GitHub](https://github.com/CloseChoice/neuroimaging-go-brrrr) |
| arc-aphasia-bids | Upload ARC dataset (ds004884) to Hub | [GitHub](https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids) |
| stroke-deepisles-demo | DeepISLES inference demo with Gradio UI | [GitHub](https://github.com/The-Obstacle-Is-The-Way/stroke-deepisles-demo) |
| DeepIsles | Stroke lesion segmentation (Nature 2025) | [GitHub](https://github.com/ezequieldlrosa/DeepIsles) |

## Live Demos & Datasets

| Resource | Description | Link |
|----------|-------------|------|
| arc-aphasia-bids | ARC dataset (293 GB, 902 sessions) | [HF Hub](https://huggingface.co/datasets/hugging-science/arc-aphasia-bids) |
| bids-neuroimaging | NiiVue visualization demo | [HF Space](https://huggingface.co/spaces/TobiasPitters/bids-neuroimaging) |

## Key Components

### 1. arc-aphasia-bids

Pipeline for the Aphasia Recovery Cohort (ARC) dataset:

- Converts OpenNeuro ds004884 (BIDS) to HuggingFace Dataset format
- Validation against the Scientific Data paper (230 subjects, 902 sessions)
- Session-level sharding for memory efficiency

### 2. stroke-deepisles-demo

End-to-end inference demo:

- Loads BIDS neuroimaging data
- Runs DeepISLES Docker container for stroke lesion segmentation
- Gradio UI for interactive visualization
- Comprehensive test suite (96 tests, 82% coverage)

### 3. bids-neuroimaging Space

Web-based visualization using NiiVue:

- Interactive 3D brain viewer
- Multiplanar views (axial, coronal, sagittal)
- Sample data from ARC dataset

## Candidate Datasets

Beyond ARC, other datasets to consider:

| Dataset | Size | Format | Use Case |
|---------|------|--------|----------|
| ATLAS v2.0 | 1,271 subjects | BIDS | Stroke lesion segmentation benchmark |
| ds004889 | Acute stroke | BIDS | Acute stroke imaging |
| AOMIC | 1,370 subjects | BIDS | Large-scale multimodal MRI |

## Consolidation Options

### Option A: Modular Structure (Current)

Keep repositories separate, use `neuroimaging-go-brrrr` as coordination hub with git submodules:

**Pros:**
- Minimal migration effort
- Repos remain independently maintainable
- Clear separation of concerns
- Git submodules link related tools

**Cons:**
- Coordination overhead
- Cross-repo changes require multiple PRs

### Option B: Monorepo

Migrate all code into `neuroimaging-go-brrrr` as packages:

**Pros:**
- Single source of truth
- Easier cross-package development
- Unified CI/CD

**Cons:**
- Larger repository size
- LFS/size constraints (e.g., 400MB parquet files)
- More complex release management

## Open Questions

1. **Additional datasets?** Should we prioritize ATLAS v2.0, ds004889, or others?

2. **Demo deployment?** Should `stroke-deepisles-demo` be deployed as a HuggingFace Space?

3. **Monorepo vs. linked repos?** What structure best serves contributors?

## Next Steps

- [ ] Discuss consolidation approach in GitHub Issues
- [ ] Add more visualization notebooks
- [ ] Explore ATLAS v2.0 dataset integration
- [ ] Document contribution workflow

## References

- [OpenNeuro ds004884 (ARC)](https://openneuro.org/datasets/ds004884) - Aphasia Recovery Cohort
- [OpenNeuro ds004889](https://openneuro.org/datasets/ds004889) - Acute stroke dataset
- [ATLAS v2.0](https://atlas.grand-challenge.org/) - Stroke lesion benchmark
- [DeepISLES Paper](https://www.nature.com/articles/s41467-025-62373-x) - Nature 2025
- [BIDS Specification](https://bids-specification.readthedocs.io/) - Brain Imaging Data Structure
- [NiiVue](https://github.com/niivue/niivue) - Web-based neuroimaging viewer
