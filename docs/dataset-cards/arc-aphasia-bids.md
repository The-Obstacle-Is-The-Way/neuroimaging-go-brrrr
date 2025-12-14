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
  - 100K<n<1M
---

# Aphasia Recovery Cohort (ARC)

Multimodal neuroimaging dataset for stroke-induced aphasia research.

## Dataset Summary

The Aphasia Recovery Cohort (ARC) is a large-scale, longitudinal neuroimaging dataset containing multimodal MRI scans from **230 chronic stroke patients** with aphasia. This HuggingFace-hosted version provides direct Python access to the BIDS-formatted data with embedded NIfTI files.

| Metric | Count |
|--------|-------|
| Subjects | 230 |
| Sessions | 902 |
| T1-weighted scans | 444 sessions |
| T2-weighted scans | 440 sessions |
| FLAIR scans | 233 sessions |
| BOLD fMRI (naming40 task) | 606 sessions (894 runs) |
| BOLD fMRI (resting state) | 337 sessions (508 runs) |
| Diffusion (DWI) | 613 sessions (2,089 runs) |
| Single-band reference | 88 sessions (322 runs) |
| Expert lesion masks | 228 |

- **Source:** [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884)
- **Paper:** [Gibson et al., Scientific Data 2024](https://doi.org/10.1038/s41597-024-03819-7)
- **License:** CC0 1.0 (Public Domain)

## Schema (19 columns)

Each row represents a single scanning session (subject + timepoint):

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
| `race` | string | Self-reported race (nullable) |
| `wab_aq` | float32 | Western Aphasia Battery Aphasia Quotient (0-100) |
| `wab_days` | float32 | Days since stroke when WAB was administered |
| `wab_type` | string | Aphasia type classification |

## Usage

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")

# Access a session
session = ds[0]
print(session["subject_id"])  # "sub-M2001"
print(session["t1w"])         # nibabel.Nifti1Image
print(session["wab_aq"])      # Aphasia severity score

# Access BOLD by task type (NEW in v2)
for run in session["bold_naming40"]:
    print(f"Naming40 run shape: {run.shape}")

for run in session["bold_rest"]:
    print(f"Resting state run shape: {run.shape}")

# Access DWI with gradient information (NEW in v2)
for i, (dwi_run, bval, bvec) in enumerate(zip(
    session["dwi"], session["dwi_bvals"], session["dwi_bvecs"]
)):
    print(f"DWI run {i+1}: shape={dwi_run.shape}")
    print(f"  b-values: {bval[:50]}...")  # First 50 chars
    print(f"  b-vectors: {bvec[:50]}...")

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

# Clinical metadata analysis (NEW: race, wab_days)
import pandas as pd
df = ds.to_pandas()[[
    "subject_id", "session_id", "age_at_stroke",
    "sex", "race", "wab_aq", "wab_days", "wab_type"
]]
print(df.describe())
```

## Supported Tasks

- **Lesion Segmentation:** Expert-drawn lesion masks enable training/evaluation of stroke lesion segmentation models
- **Aphasia Severity Prediction:** WAB-AQ scores (0-100) provide continuous severity labels for regression tasks
- **Aphasia Type Classification:** WAB-derived aphasia type labels (Broca's, Wernicke's, Anomic, etc.)
- **Longitudinal Analysis:** Multiple sessions per subject enable recovery trajectory modeling
- **Diffusion Analysis:** Full bval/bvec gradients enable tractography and diffusion modeling
- **Task-based fMRI:** Naming40 and resting-state runs separated for targeted analysis

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
# Stream without loading all into memory
for session in ds:
    process(session)
    # Data is garbage collected after each iteration
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

## Changelog

### v2 (December 2025)

- **BREAKING:** `bold` column split into `bold_naming40` and `bold_rest` for task-specific analysis
- **NEW:** `dwi_bvals` and `dwi_bvecs` columns for diffusion gradient information
- **NEW:** `race` column from participants.tsv
- **NEW:** `wab_days` column (days since stroke when WAB administered)
- **NEW:** `t2w_acquisition` column for T2w sequence type filtering

### v1 (December 2025)

- Initial release with 13 columns
