---
license: cc0-1.0
task_categories:
  - other
tags:
  - medical
  - neuroimaging
  - brain
  - healthy-subjects
  - MRI
  - fMRI
  - DWI
  - BIDS
  - AOMIC
  - OpenNeuro
size_categories:
  - n<1K
---

# AOMIC-PIOP1 Dataset

Amsterdam Open MRI Collection - Population Imaging of Psychology Dataset 1 (PIOP1).

## Dataset Description

- **Source:** [OpenNeuro ds002785](https://openneuro.org/datasets/ds002785)
- **Paper:** [Snoek et al., Scientific Data 2021](https://doi.org/10.1038/s41597-021-00870-6)
- **License:** CC0 (Public Domain)
- **Subjects:** 216 healthy young adults (after quality control)

## Dataset Structure

| Modality | Count | Description |
|----------|-------|-------------|
| T1w | 216 | T1-weighted structural MRI |
| DWI | 211 | Diffusion-weighted imaging |
| BOLD | 216 | Functional MRI (resting-state + tasks) |

**Note:** 211/216 subjects have DWI data. All 216 subjects have T1w and BOLD scans. Five subjects missing DWI: sub-0041, sub-0057, sub-0121, sub-0183, sub-0192.

## Usage

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/aomic-piop1", split="train")

# Access a subject
example = ds[0]
print(example["subject_id"])  # "sub-0001"
print(example["t1w"])         # NIfTI array (T1-weighted structural)
print(example["dwi"])          # List of NIfTI arrays (single file per subject)
print(example["bold"])         # List of NIfTI arrays (multiple tasks)
print(example["age"])          # Age in years
print(example["sex"])          # Sex (M/F)
print(example["handedness"])   # Handedness (left/right/ambidextrous)
```

## Citation

```bibtex
@article{snoek2021amsterdam,
  title={The Amsterdam Open MRI Collection, a set of multimodal MRI datasets for individual difference analyses},
  author={Snoek, Lukas and van der Miesen, Maite M and Beemsterboer, Tinka and Van Der Leij, Andries and Eigenhuis, Annemarie and Scholte, H Steven},
  journal={Scientific Data},
  volume={8},
  number={1},
  pages={85},
  year={2021},
  publisher={Nature Publishing Group},
  doi={10.1038/s41597-021-00870-6}
}
```
