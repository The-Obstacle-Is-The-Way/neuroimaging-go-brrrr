# Project Roadmap & Architecture

> **Status**: Active
> **Last Updated**: 2024-12-05

## Vision

We are building **generic BIDS/NIfTI infrastructure** for HuggingFace by implementing a **specific, high-value pipeline: Stroke Lesion Analysis**. This ensures our tools are battle-tested against real research needs (ARC, ATLAS, DeepISLES) rather than theoretical use cases.

## What We're Building

### The Two Pipelines

```text
┌──────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION PIPELINE                               │
│                        (Upload datasets to Hub)                          │
│                                                                          │
│   OpenNeuro BIDS ──► Validate ──► Convert ──► push_to_hub() ──► HF Hub   │
│                                                                          │
│   Tools: arc-aphasia-bids                                                │
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

## System Architecture

We use a **modular hub structure with Git submodules**. This approach:

- Bypasses GitHub LFS limits for large assets (e.g., 400MB parquet files in visualization Spaces)
- Allows independent development and release cycles per tool
- Maintains a unified entry point for discovery

```text
neuroimaging-go-brrrr/           # Coordination hub
├── scripts/                     # Standalone utilities
├── tools/
│   ├── arc-aphasia-bids/        # Production pipeline tool
│   └── bids-neuroimaging-space/ # Git submodule → HF Space
└── docs/
```

Tools are standalone utilities, not necessarily PyPI-distributable packages. We call them "tools" to reflect this.

## Live Resources

| Resource | Description | Link |
|----------|-------------|------|
| arc-aphasia-bids | ARC dataset (293 GB, 902 sessions) | [HF Hub](https://huggingface.co/datasets/hugging-science/arc-aphasia-bids) |
| bids-neuroimaging | NiiVue visualization demo | [HF Space](https://huggingface.co/spaces/TobiasPitters/bids-neuroimaging) |

## Key Components

### arc-aphasia-bids

Production pipeline for the Aphasia Recovery Cohort (ARC) dataset:

- Converts OpenNeuro ds004884 (BIDS) to HuggingFace Dataset format
- Validation against the Scientific Data paper (230 subjects, 902 sessions)
- Session-level sharding for memory efficiency

### stroke-deepisles-demo

End-to-end stroke lesion segmentation:

- Loads BIDS neuroimaging data from HuggingFace Hub
- Runs DeepISLES Docker container (SEALS + NVAUTO + FACTORIZER ensemble)
- Outputs lesion masks for visualization

**Note**: Visualization uses NiiVue directly (not Gradio, which blocks external JavaScript). For deployment, we recommend Docker-based HF Spaces with a Python backend (FastAPI) serving a static NiiVue frontend.

### bids-neuroimaging Space

Web-based visualization using NiiVue:

- Interactive 3D brain viewer
- Multiplanar views (axial, coronal, sagittal)
- Sample data from ARC dataset

## Phase 1 Roadmap: The Stroke Pilot

| Priority | Task | Status |
|----------|------|--------|
| 1 | **Data Expansion**: Upload ATLAS v2.0 to Hub (955 public T1w images, ISLES 2022 benchmark) | Planned |
| 2 | **Preprocessing**: Integrate skull stripping (HD-BET, used by DeepISLES) | Planned |
| 3 | **Demo Deployment**: Deploy stroke-deepisles-demo as Docker-based HF Space | Planned |
| 4 | **Documentation**: Create CONTRIBUTING.md with conventions | Planned |

## Compute & Data Requirements

### GPU Requirements

DeepISLES requires GPU for inference. For HF Space deployment:
- Minimum: T4 GPU (16GB VRAM)
- Recommended: A10G for faster ensemble inference

### Data Governance

All datasets require proper citation per their respective licenses:

| Dataset | Citation |
|---------|----------|
| ARC (ds004884) | [Wilson et al., Scientific Data 2024](https://pubmed.ncbi.nlm.nih.gov/39251640/) |
| ATLAS v2.0 | [Liew et al., Scientific Data 2022](https://www.nature.com/articles/s41597-022-01401-7) |
| ISLES 2022 | [Hernandez Petzsche et al., Scientific Data 2022](https://www.nature.com/articles/s41597-022-01875-5) |

## Related Repositories

| Repository | Purpose | Link |
|------------|---------|------|
| neuroimaging-go-brrrr | Coordination hub | [GitHub](https://github.com/CloseChoice/neuroimaging-go-brrrr) |
| arc-aphasia-bids | ARC dataset upload pipeline | [GitHub](https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids) |
| stroke-deepisles-demo | DeepISLES inference pipeline | [GitHub](https://github.com/The-Obstacle-Is-The-Way/stroke-deepisles-demo) |
| DeepIsles | Stroke segmentation (Nature 2025) | [GitHub](https://github.com/ezequieldlrosa/DeepIsles) |

## References

- [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884) - Aphasia Recovery Cohort
- [ATLAS v2.0](https://atlas.grand-challenge.org/) - Stroke lesion benchmark
- [DeepISLES](https://www.nature.com/articles/s41467-025-62373-x) - Nature Communications 2025
- [BIDS Specification](https://bids-specification.readthedocs.io/) - Brain Imaging Data Structure
- [NiiVue](https://github.com/niivue/niivue) - Web-based neuroimaging viewer (Chris Rorden et al.)
- [HD-BET](https://github.com/MIC-DKFZ/HD-BET) - Brain extraction tool
