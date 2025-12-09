# Zenodo Datasets

## ISLES 2024 Stroke Dataset

The ISLES 2024 challenge dataset contains multimodal acute stroke imaging (CT/MRI) from 149 subjects.

### Download

```bash
# Download from Zenodo (requires registration)
# https://zenodo.org/records/17652035

# Extract to this directory
unzip ISLES24_Training.zip -d isles24
```

### Expected Structure

```
isles24/
└── train/
    ├── rawdata/
    │   └── sub-strokeXXXX/
    │       ├── ses-01/         # Acute imaging
    │       │   └── ct/         # NCCT, CTA, CTP, perfusion maps
    │       └── ses-02/         # Follow-up MRI
    │           └── dwi/        # DWI, ADC
    ├── derivatives/
    │   └── sub-strokeXXXX/
    │       └── ses-02/
    │           └── anat/       # Lesion masks
    └── phenotype/
        └── phenotype.xlsx      # Clinical metadata
```

### Validate Download

```bash
uv run bids-hub isles24 validate data/zenodo/isles24/train
```

### Reference

- Challenge: https://isles-24.grand-challenge.org/
- Zenodo: https://zenodo.org/records/17652035
