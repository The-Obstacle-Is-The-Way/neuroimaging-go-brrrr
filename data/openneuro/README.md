# OpenNeuro Datasets

## ARC Aphasia Dataset (ds004884)

The Aphasia Recovery Cohort (ARC) dataset contains multimodal MRI data from 230 chronic stroke patients with aphasia.

### Download

```bash
# Using OpenNeuro CLI (recommended)
openneuro download --snapshot 1.0.1 ds004884 ds004884

# Or using DataLad
datalad install https://github.com/OpenNeuroDatasets/ds004884.git
cd ds004884
datalad get .
```

### Expected Structure

```
ds004884/
├── participants.tsv
├── sub-M2001/
│   └── ses-*/
│       ├── anat/       # T1w, T2w, FLAIR
│       ├── func/       # BOLD fMRI
│       └── dwi/        # Diffusion imaging
└── derivatives/
    └── lesion_masks/   # Expert lesion segmentations
```

### Validate Download

```bash
uv run bids-hub arc validate data/openneuro/ds004884
```

### Reference

- Paper: [Gibson et al., Scientific Data 2024](https://doi.org/10.1038/s41597-024-03819-7)
- OpenNeuro: https://openneuro.org/datasets/ds004884
