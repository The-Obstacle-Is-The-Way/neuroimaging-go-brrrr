---
license: cc0-1.0
task_categories:
  - image-segmentation
  - image-classification
language:
  - en
tags:
  - medical
  - neuroimaging
  - mri
  - brain
  - stroke
  - aphasia
  - BIDS
  - diffusion
  - fMRI
size_categories:
  - n<1K
---

# Aphasia Recovery Cohort (ARC)

Multimodal neuroimaging dataset for stroke-induced aphasia research.

## Dataset Summary

The Aphasia Recovery Cohort (ARC) is a large-scale, longitudinal neuroimaging dataset containing multimodal MRI scans from **230 chronic stroke patients** with aphasia. This HuggingFace-hosted version provides direct Python access to the BIDS-formatted data with embedded NIfTI files.

| Metric | Count |
|--------|-------|
| Subjects | 230 |
| Sessions | 902 |
| T1-weighted scans | 441 sessions* |
| T2-weighted scans | 439 sessions* |
| FLAIR scans | 231 sessions* |
| BOLD fMRI (naming40 task) | 750 sessions (894 runs) |
| BOLD fMRI (resting state) | 498 sessions (508 runs) |
| Diffusion (DWI) | 613 sessions (2,089 runs) |
| Single-band reference | 88 sessions (322 runs) |
| Expert lesion masks | 228 |

*Sessions with exactly one scan. Sessions with multiple runs of the same structural modality are set to `None` to avoid ambiguity (3 T1w, 1 T2w, 2 FLAIR sessions affected).

- **Source:** [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884)
- **Paper:** [Gibson et al., Scientific Data 2024](https://doi.org/10.1038/s41597-024-03819-7)
- **License:** CC0 1.0 (Public Domain)

## Supported Tasks

- **Lesion Segmentation:** Expert-drawn lesion masks enable training/evaluation of stroke lesion segmentation models
- **Aphasia Severity Prediction:** WAB-AQ scores (0-100) provide continuous severity labels for regression tasks
- **Aphasia Type Classification:** WAB-derived aphasia type labels (Broca's, Wernicke's, Anomic, etc.)
- **Longitudinal Analysis:** Multiple sessions per subject enable recovery trajectory modeling
- **Diffusion Analysis:** Full bval/bvec gradients enable tractography and diffusion modeling
- **Task-based fMRI:** Naming40 and resting-state runs separated for targeted analysis

## Languages

Clinical metadata and documentation are in English.

## Dataset Structure

### Data Instance

Each row represents a single scanning session (subject + timepoint):

```python
{
    "subject_id": "sub-M2001",
    "session_id": "ses-1",
    "t1w": <nibabel.Nifti1Image>,              # T1-weighted structural
    "t2w": <nibabel.Nifti1Image>,              # T2-weighted structural
    "t2w_acquisition": "space_2x",             # T2w sequence type
    "flair": <nibabel.Nifti1Image>,            # FLAIR structural
    "bold_naming40": [<Nifti1Image>, ...],     # Naming task fMRI runs
    "bold_rest": [<Nifti1Image>, ...],         # Resting state fMRI runs
    "dwi": [<Nifti1Image>, ...],               # Diffusion runs
    "dwi_bvals": ["0 1000 1000...", ...],      # b-values per run
    "dwi_bvecs": ["0 0 0\n1 0 0\n...", ...],   # b-vectors per run
    "sbref": [<Nifti1Image>, ...],             # Single-band references
    "lesion": <nibabel.Nifti1Image>,           # Expert lesion mask
    "age_at_stroke": 58.0,
    "sex": "M",
    "race": "w",
    "wab_aq": 72.5,
    "wab_days": 180.0,
    "wab_type": "Anomic"
}
```

### Data Fields

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | string | BIDS subject identifier (e.g., "sub-M2001") |
| `session_id` | string | BIDS session identifier (e.g., "ses-1") |
| `t1w` | Nifti | T1-weighted structural MRI (nullable) |
| `t2w` | Nifti | T2-weighted structural MRI (nullable) |
| `t2w_acquisition` | string | T2w acquisition type: `space_2x`, `space_no_accel`, `turbo_spin_echo` (nullable) |
| `flair` | Nifti | FLAIR structural MRI (nullable) |
| `bold_naming40` | Sequence[Nifti] | BOLD fMRI runs for naming40 task |
| `bold_rest` | Sequence[Nifti] | BOLD fMRI runs for resting state |
| `dwi` | Sequence[Nifti] | Diffusion-weighted imaging runs |
| `dwi_bvals` | Sequence[string] | b-values for each DWI run (space-separated) |
| `dwi_bvecs` | Sequence[string] | b-vectors for each DWI run (3 lines, space-separated) |
| `sbref` | Sequence[Nifti] | Single-band reference images |
| `lesion` | Nifti | Expert-drawn lesion segmentation mask (nullable) |
| `age_at_stroke` | float32 | Subject age at stroke onset in years |
| `sex` | string | Biological sex ("M" or "F") |
| `race` | string | Self-reported race: "b" (Black), "w" (White), or null |
| `wab_aq` | float32 | Western Aphasia Battery Aphasia Quotient (0-100) |
| `wab_days` | float32 | Days since stroke when WAB was administered |
| `wab_type` | string | Aphasia type classification |

### Data Splits

| Split | Sessions | Description |
|-------|----------|-------------|
| train | 902 | All sessions (no predefined train/test split) |

Note: Users should implement their own train/validation/test splits, ensuring no subject overlap between splits for valid evaluation.

## Dataset Creation

### Curation Rationale

The ARC dataset was created to address the lack of large-scale, publicly available neuroimaging data for aphasia research. It enables:

- Development of automated lesion segmentation algorithms
- Machine learning models for aphasia severity prediction
- Studies of brain plasticity and language recovery

### Source Data

Data was collected at the University of South Carolina and Medical University of South Carolina as part of ongoing aphasia recovery research. All participants provided informed consent under IRB-approved protocols.

### Annotations

Lesion masks were manually traced by trained neuroimaging experts on T1-weighted or FLAIR images, following established stroke lesion delineation protocols.

## Personal and Sensitive Information

- **De-identified:** All data has been de-identified per HIPAA guidelines
- **Defaced:** Structural MRI images have been defaced to prevent facial reconstruction
- **No PHI:** No protected health information is included
- **Consent:** All participants consented to public data sharing

## Considerations for Using the Data

### Social Impact

This dataset enables research into:

- Improved stroke rehabilitation through better outcome prediction
- Automated clinical tools for aphasia assessment
- Understanding of brain-language relationships

### Known Biases

- **Geographic:** Data collected primarily from Southeastern US medical centers
- **Age:** Stroke predominantly affects older adults; pediatric cases underrepresented
- **Severity:** Very severe aphasia cases may be underrepresented due to consent requirements

### Known Limitations

- Not all sessions have all modalities (check for None/empty lists)
- Lesion masks available for 228/230 subjects
- Longitudinal follow-up varies by subject (1-12 sessions)

## Usage

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")

# Access a session
session = ds[0]
print(session["subject_id"])  # "sub-M2001"
print(session["t1w"])         # nibabel.Nifti1Image
print(session["wab_aq"])      # Aphasia severity score

# Access BOLD by task type
for run in session["bold_naming40"]:
    print(f"Naming40 run shape: {run.shape}")

for run in session["bold_rest"]:
    print(f"Resting state run shape: {run.shape}")

# Access DWI with gradient information
for i, (dwi_run, bval, bvec) in enumerate(zip(
    session["dwi"], session["dwi_bvals"], session["dwi_bvecs"]
)):
    print(f"DWI run {i+1}: shape={dwi_run.shape}")
    print(f"  b-values: {bval[:50]}...")
    print(f"  b-vectors: {bvec[:50]}...")

# Filter by T2w acquisition type (for paper replication)
space_only = ds.filter(
    lambda x: (
        x["lesion"] is not None
        and x["t2w"] is not None
        and x["t2w_acquisition"] in ("space_2x", "space_no_accel")
    )
)
# Returns 222 SPACE samples (115 space_2x + 107 space_no_accel)

# Clinical metadata analysis
import pandas as pd
df = ds.to_pandas()[[
    "subject_id", "session_id", "age_at_stroke",
    "sex", "race", "wab_aq", "wab_days", "wab_type"
]]
print(df.describe())
```

## Technical Notes

### Multi-Run Modalities

Functional and diffusion modalities support multiple runs per session:

- Empty list `[]` = no data for this session
- List with items = all runs for this session, sorted by filename

### DWI Gradient Files

Each DWI run has aligned gradient information:

- `dwi_bvals`: Space-separated b-values (e.g., "0 1000 1000 1000...")
- `dwi_bvecs`: Three lines of space-separated vectors (x, y, z directions)

These are essential for diffusion tensor imaging (DTI) and tractography analysis.

### Memory Considerations

NIfTI files are loaded on-demand. For large-scale processing:

```python
for session in ds:
    process(session)
    # Data is garbage collected after each iteration
```

### Original BIDS Source

This dataset is derived from [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884). The original BIDS structure is preserved in the column naming and organization.

## Additional Information

### Dataset Curators

- **Original Dataset:** Gibson et al. (University of South Carolina)
- **HuggingFace Conversion:** The-Obstacle-Is-The-Way

### Licensing

This dataset is released under **CC0 1.0 Universal (Public Domain)**. You can copy, modify, distribute, and perform the work, even for commercial purposes, all without asking permission.

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

## Contributions

Thanks to [@The-Obstacle-Is-The-Way](https://github.com/The-Obstacle-Is-The-Way) for converting this dataset to HuggingFace format with native `Nifti()` feature support.

## Changelog

### v2 (December 2025)

- **BREAKING:** `bold` column split into `bold_naming40` and `bold_rest` for task-specific analysis
- **NEW:** `dwi_bvals` and `dwi_bvecs` columns for diffusion gradient information
- **NEW:** `race` column from participants.tsv
- **NEW:** `wab_days` column (days since stroke when WAB administered)
- **NEW:** `t2w_acquisition` column for T2w sequence type filtering

### v1 (December 2025)

- Initial release with 13 columns
