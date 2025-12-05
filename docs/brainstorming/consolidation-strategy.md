# Consolidation Strategy: neuroimaging-go-brrrr

> **Status**: Draft / Open for Discussion
> **Date**: 2024-12-05
> **Contributors**: Open to all

## The Problem

**HuggingFace has been slow to integrate neuroimaging and BIDS support.** The `datasets` library has excellent support for text, images, and audio, but scientific imaging formats (NIfTI, DICOM, BIDS) have lagged behind.

The Hugging Science community is working together to accelerate this. This document outlines how we can consolidate our efforts under `neuroimaging-go-brrrr` to reduce fragmentation and ship faster.

## Current State of HuggingFace Neuroimaging Support

### What's Already Merged (thanks to community contributions)

| PR | Title | Status | Date |
|----|-------|--------|------|
| [#7815](https://github.com/huggingface/datasets/pull/7815) | Add Nifti support | MERGED | Oct 24, 2025 |
| [#7853](https://github.com/huggingface/datasets/pull/7853) | Fix embed storage nifti | MERGED | Nov 6, 2025 |
| [#7874](https://github.com/huggingface/datasets/pull/7874) | Nifti visualization support | MERGED | Nov 19, 2025 |
| [#7878](https://github.com/huggingface/datasets/pull/7878) | Replace papaya with NiiVue | MERGED | Nov 21, 2025 |

### What's Still Pending (needs community push)

| PR | Title | Status | Author |
|----|-------|--------|--------|
| [#7886](https://github.com/huggingface/datasets/pull/7886) | **BIDS dataset loader** | OPEN | Community |
| [#7892](https://github.com/huggingface/datasets/pull/7892) | Encode nifti correctly when uploading lazily | OPEN | @CloseChoice |
| [#7885](https://github.com/huggingface/datasets/pull/7885) | Add visualization paragraph to nifti readme | OPEN | @CloseChoice |
| [#7835](https://github.com/huggingface/datasets/pull/7835) | Add DICOM support | DRAFT | @CloseChoice |

## The Two Pipelines

We've been building two complementary pipelines:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        PRODUCTION PIPELINE                               │
│                        (Upload TO HuggingFace)                           │
│                                                                          │
│   OpenNeuro BIDS ──► Validate ──► Convert ──► push_to_hub() ──► HF Hub  │
│                                                                          │
│   Repos: arc-aphasia-bids, stroke-deepisles-demo                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌───────────────────┐
                         │   HuggingFace Hub │
                         │   (Nifti datasets)│
                         └───────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                       CONSUMPTION PIPELINE                               │
│                       (Load FROM HuggingFace)                            │
│                                                                          │
│   load_dataset('bids') ──► Stream ──► Decode Nifti ──► NiiVue viz       │
│                                                                          │
│   PRs: #7886 (BIDS loader), #7815 (Nifti), #7874 (visualization)        │
└─────────────────────────────────────────────────────────────────────────┘
```

## Ecosystem Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                     neuroimaging-go-brrrr                                │
│                     ═══════════════════════                              │
│                     CONSOLIDATION HUB                                    │
│                                                                          │
│  Purpose: Coordinate community efforts to accelerate HF neuroimaging    │
│                                                                          │
│  Current contents:                                                       │
│  ├── scripts/push_to_hub_ds004884_full.py                               │
│  ├── tools/bids-neuroimaging/  (HF Space visualization)                 │
│  └── README.md                 (resource links)                         │
└─────────────────────────────────────────────────────────────────────────┘
                                    ▲
                                    │ (consolidates)
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐
│ arc-aphasia-bids │  │ stroke-deepisles │  │ huggingface/datasets     │
│ (PRODUCTION)     │  │ -demo            │  │ (CONSUMPTION)            │
│                  │  │                  │  │                          │
│ • Upload ARC     │  │ • DeepISLES      │  │ • Pending PRs for        │
│   to HF Hub      │  │   inference      │  │   BIDS loader, lazy      │
│ • BIDS→HF        │  │ • Gradio UI      │  │   upload, DICOM          │
│   conversion     │  │ • Full test      │  │ • Merged: Nifti,         │
│ • Validation     │  │   suite          │  │   NiiVue viz             │
└──────────────────┘  └──────────────────┘  └──────────────────────────┘
                                │
                                ▼
                      ┌──────────────────┐
                      │ DeepIsles        │
                      │ (External Ref)   │
                      │                  │
                      │ • Nature 2025    │
                      │ • Stroke lesion  │
                      │   segmentation   │
                      │ • Docker image   │
                      └──────────────────┘
```

## Related Repositories

| Repository | Type | Purpose | Link |
|------------|------|---------|------|
| neuroimaging-go-brrrr | Hub | Consolidation hub for neuroimaging tools | [GitHub](https://github.com/CloseChoice/neuroimaging-go-brrrr) |
| arc-aphasia-bids | Production | Upload ARC dataset (ds004884) to HuggingFace Hub | [GitHub](https://github.com/The-Obstacle-Is-The-Way/arc-aphasia-bids) |
| stroke-deepisles-demo | Production | DeepISLES inference demo with Gradio UI | [GitHub](https://github.com/The-Obstacle-Is-The-Way/stroke-deepisles-demo) |
| huggingface/datasets | Consumption | Pending PRs for BIDS loader, lazy upload fixes | [PR #7886](https://github.com/huggingface/datasets/pull/7886) |
| DeepIsles | Reference | State-of-the-art stroke lesion segmentation | [GitHub](https://github.com/ezequieldlrosa/DeepIsles) |

## HuggingFace Resources

| Resource | Description | Link |
|----------|-------------|------|
| arc-aphasia-bids dataset | ARC dataset on HF Hub (293 GB, 902 sessions) | [HF Hub](https://huggingface.co/datasets/hugging-science/arc-aphasia-bids) |
| bids-neuroimaging Space | NiiVue visualization demo | [HF Spaces](https://huggingface.co/spaces/TobiasPitters/bids-neuroimaging) |

## Key Technical Components

### 1. BIDS Loader (Consumption - PR #7886)

Native BIDS support for HuggingFace's `datasets` library:

```python
from datasets import load_dataset

# Load any BIDS dataset with one line
ds = load_dataset('bids', data_dir="path/to/bids/dataset", streaming=True)

# Push to Hub
ds.push_to_hub("org/dataset-name", num_shards={"train": 500})
```

Features:

- Uses `pybids` for BIDS-compliant file discovery
- `Nifti()` feature type for NIfTI file handling (already merged)
- `Nifti1ImageWrapper._repr_html_()` for NiiVue visualization (already merged)
- Streaming support for large datasets

### 2. arc-aphasia-bids (Production)

Custom pipeline for the Aphasia Recovery Cohort (ARC) dataset:

- Converts OpenNeuro ds004884 (BIDS) to HuggingFace Dataset format
- Validation against the Scientific Data paper (230 subjects, 902 sessions)
- Session-level sharding for memory efficiency

### 3. stroke-deepisles-demo (Production + Inference)

End-to-end inference demo:

- Loads BIDS/HF neuroimaging data
- Runs DeepISLES Docker container for stroke lesion segmentation
- Gradio UI for interactive visualization
- Comprehensive test suite (96 tests, 82% coverage)

## Consolidation Options

### Option A: Modular Monorepo

Migrate all code into `neuroimaging-go-brrrr` as packages:

```text
neuroimaging-go-brrrr/
├── packages/
│   ├── arc-bids/              ← arc-aphasia-bids code
│   ├── stroke-demo/           ← stroke-deepisles-demo code
│   └── bids-loader-examples/  ← Examples using native BIDS loader
├── scripts/
├── tools/
├── docs/
└── pyproject.toml             ← Workspace configuration
```

**Pros:**

- Single source of truth
- Easier cross-package development
- Unified CI/CD

**Cons:**

- Larger repository size
- More complex release management
- Migration effort required

### Option B: Hub with Linked Repositories

Keep repositories separate, use `neuroimaging-go-brrrr` as documentation/coordination hub:

```text
neuroimaging-go-brrrr/
├── docs/
│   ├── architecture.md        ← How repos relate
│   ├── getting-started.md     ← Quick start guide
│   └── contributing.md        ← Contribution guidelines
├── scripts/                   ← Shared utility scripts
├── tools/                     ← Shared tools
└── README.md                  ← Links to all repos
```

**Pros:**

- Minimal migration effort
- Repos remain independently maintainable
- Clear separation of concerns

**Cons:**

- Coordination overhead
- Potential for divergence
- Cross-repo changes require multiple PRs

### Option C: Focus on Upstream First

Prioritize getting pending PRs merged into `huggingface/datasets`, then reassess:

- Push [#7886](https://github.com/huggingface/datasets/pull/7886) (BIDS loader) to merge
- Push [#7892](https://github.com/huggingface/datasets/pull/7892) (lazy upload fix) to merge
- Once merged, `arc-aphasia-bids` simplifies to example usage
- Focus consolidation on inference/demo tooling

**Pros:**

- Leverages official HuggingFace support
- Reduces maintenance burden
- Community benefits from upstream contribution

**Cons:**

- Dependent on upstream merge timeline (HF is slow)
- May need interim solutions

## Open Questions

1. **How do we accelerate HuggingFace reviews?** The PRs have been open for weeks. Should we coordinate via Hugging Science Discord to add more reviewers/visibility?

2. **Monorepo vs. linked repos?** What structure best serves the community?

3. **Demo deployment?** Should `stroke-deepisles-demo` be deployed as a HuggingFace Space alongside `bids-neuroimaging`?

4. **Additional datasets?** What other OpenNeuro datasets should be prioritized for HuggingFace upload?
   - ds004889 (acute stroke) is mentioned in README.md

## Next Steps

- [ ] Coordinate via Hugging Science Discord to push pending PRs
- [ ] Discuss consolidation approach in GitHub Issues
- [ ] Decide on monorepo vs. linked repos structure
- [ ] Create issues for specific integration tasks
- [ ] Document contribution workflow for new collaborators

## References

- [OpenNeuro ds004884 (ARC)](https://openneuro.org/datasets/ds004884) - Aphasia Recovery Cohort
- [OpenNeuro ds004889](https://openneuro.org/datasets/ds004889) - Acute stroke dataset
- [DeepISLES Nature Paper](https://www.nature.com/articles/s41467-025-62373-x) - Stroke lesion segmentation
- [ISLES'22 Challenge](https://isles22.grand-challenge.org/) - Ischemic Stroke Lesion Segmentation
- [HuggingFace Datasets](https://huggingface.co/docs/datasets/) - Dataset library documentation
- [BIDS Specification](https://bids-specification.readthedocs.io/) - Brain Imaging Data Structure
- [Hugging Science Discord](https://discord.gg/huggingface) - Community coordination
