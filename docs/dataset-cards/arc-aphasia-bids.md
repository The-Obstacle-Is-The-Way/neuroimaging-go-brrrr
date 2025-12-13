---
license: cc0-1.0
task_categories:
  - image-segmentation
  - image-classification
tags:
  - medical
  - neuroimaging
  - stroke
  - aphasia
  - MRI
  - BIDS
size_categories:
  - 100K<n<1M
---

# Aphasia Recovery Cohort (ARC) Dataset

Multimodal neuroimaging dataset of 230 chronic stroke patients with aphasia.

## Dataset Description

- **Source:** [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884)
- **Paper:** [Gibson et al., Scientific Data 2024](https://doi.org/10.1038/s41597-024-03819-7)
- **License:** CC0 (Public Domain)

## Dataset Structure

| Modality | Count | Description |
|----------|-------|-------------|
| T1w | 441 | T1-weighted structural MRI |
| T2w | 447 | T2-weighted structural MRI |
| FLAIR | 235 | Fluid-attenuated inversion recovery |
| BOLD | 850 | Functional MRI |
| DWI | 613 | Diffusion-weighted imaging |
| Lesion Masks | 228 | Expert-drawn stroke lesion segmentations |

## Usage

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")

# Access a subject
example = ds[0]
print(example["subject_id"])  # "sub-M2001"
print(example["t1w"])         # NIfTI array
print(example["wab_aq"])      # Aphasia severity score

# Filter by T2w acquisition type (for paper replication)
# See: https://arxiv.org/abs/2503.05531 (MeshNet paper)
space_only = ds.filter(
    lambda x: (
        x["lesion"] is not None
        and x["t2w"] is not None
        and x["t2w_acquisition"] in ("space_2x", "space_no_accel")
    )
)
# Returns 222 SPACE samples (115 space_2x + 107 space_no_accel)
# Excludes: 5 TSE samples, 1 multi-T2w session (sub-M2105/ses-964)
```

## Citation

```bibtex
@article{gibson2024arc,
  title={The Aphasia Recovery Cohort, an open-source chronic stroke repository},
  author={Gibson, Makayla and Newman-Norlund, Roger and Bonilha, Leonardo and Fridriksson, Julius and Hickok, Gregory and Hillis, Argye E and den Ouden, Dirk-Bart and Rorden, Christopher},
  journal={Scientific Data},
  volume={11},
  pages={981},
  year={2024},
  publisher={Nature Publishing Group},
  doi={10.1038/s41597-024-03819-7}
}
```
