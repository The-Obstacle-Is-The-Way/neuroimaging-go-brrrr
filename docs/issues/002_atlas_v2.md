# Issue: ATLAS v2.0 Local Builder (NOT Public Upload)

**Status:** Ready for upstream
**Difficulty:** ⭐⭐⭐ Medium
**Labels:** `enhancement`, `dataset`, `documentation`

> **Note:** This issue is labeled `documentation` (not `help wanted`) because we **cannot** host ATLAS publicly. This issue creates tooling for users who have obtained their own DUA approval. We want contributors to know about this dataset and the legal constraints.

---

## ⚠️ IMPORTANT: This is NOT a public upload

ATLAS v2.0 requires a **Data Use Agreement (DUA)** through ICPSR. We **cannot** host this dataset publicly on HuggingFace. Instead, this issue creates tooling for users to build the HF dataset **locally** after they obtain access.

---

## Title

`[Dataset] Add ATLAS v2.0 Local Builder - Stroke Lesion Segmentation`

---

## Body

### Dataset Info

| Field | Value |
|-------|-------|
| **Name** | Anatomical Tracings of Lesions After Stroke v2.0 |
| **Source** | [ICPSR 36684](https://www.icpsr.umich.edu/web/ICPSR/studies/36684) |
| **Paper** | [Liew et al., Scientific Data 2022](https://www.nature.com/articles/s41597-022-01401-7) |
| **License** | ⚠️ Restricted - DUA Required |
| **Subjects** | 955 (public train+test), 316 (hidden) |
| **Format** | BIDS |
| **HuggingFace Target** | Local build only (user's own repo) |

### Why NOT Public Upload?

From [ICPSR](https://www.icpsr.umich.edu/web/ICPSR/studies/36684):
> "To access this data collection, you need to download and complete the data use agreement and email it to icpsr-addep@umich.edu."

**Redistribution is prohibited** without explicit permission. Creating a public HuggingFace dataset would violate the DUA.

### What This Issue Creates Instead

Tooling so users can:
1. Download ATLAS after obtaining DUA approval
2. Run `bids-hub atlas build` to create a local HF dataset
3. Use the dataset for their own research
4. Optionally push to their own private HF repo

### Description

ATLAS v2.0 is the **gold standard benchmark** for stroke lesion segmentation, used in ISLES 2022 Challenge (MICCAI). Contains T1w MRIs with manually segmented lesion masks from 44 research cohorts across 11 countries.

**Data includes:**
- T1-weighted structural MRI
- Manual lesion segmentation masks
- Site/cohort information (44 sites)

### Why This Matters

1. **Benchmark standard** - ISLES 2022 Challenge baseline
2. **Diverse data** - 44 sites, 11 countries
3. **Segmentation research** - Core task in stroke imaging
4. **Proves pipeline flexibility** - Shows bids-hub works with restricted datasets

### Exact Schema

```python
from datasets import Features, Value
from datasets.features import Nifti

def get_atlas_features() -> Features:
    """ATLAS schema - one row per SUBJECT."""
    return Features({
        "subject_id": Value("string"),
        "site_id": Value("string"),           # 44 different sites
        "t1w": Nifti(),                       # T1-weighted MRI
        "lesion_mask": Nifti(),               # Manual segmentation
        # Metadata
        "hemisphere": Value("string"),        # Left/Right/Bilateral
        "lesion_volume_mm3": Value("float32"),
    })
```

### Directory Structure

```
ATLAS_R2.0/
├── Training/
│   └── R001/                              # Site ID
│       └── sub-r001s001/
│           └── ses-1/
│               └── anat/
│                   ├── sub-r001s001_ses-1_T1w.nii.gz
│                   └── sub-r001s001_ses-1_label-L_desc-T1lesion_mask.nii.gz
└── Testing/
    └── ... (same structure, masks hidden for challenge)
```

### Files to Create

```
src/bids_hub/datasets/atlas.py          # Dataset module
src/bids_hub/validation/atlas.py        # Validation rules
scripts/download_atlas.sh               # Instructions (NOT auto-download)
tests/test_atlas.py                     # Tests
docs/how-to/build-atlas-locally.md      # User guide for DUA + local build
```

### Implementation Steps

1. **Create instructions script** (`scripts/download_atlas.sh`)
   ```bash
   #!/usr/bin/env bash
   echo "ATLAS v2.0 requires a Data Use Agreement."
   echo ""
   echo "Steps to obtain access:"
   echo "1. Go to: https://www.icpsr.umich.edu/web/ICPSR/studies/36684"
   echo "2. Download and complete the Data Use Agreement"
   echo "3. Email to: icpsr-addep@umich.edu"
   echo "4. Wait for approval and download link"
   echo ""
   echo "After downloading, run:"
   echo "  uv run bids-hub atlas build /path/to/ATLAS_R2.0 --dry-run"
   ```

2. **Create dataset module** (`src/bids_hub/datasets/atlas.py`)
   - Implement `build_atlas_file_table()` - walk Training/*/sub-*/ses-*/anat/
   - Implement `get_atlas_features()` - schema above
   - Implement `build_and_push_atlas()` - default to local save, not push

3. **Add CLI commands** (in `cli.py`)
   ```python
   @app.command()
   def atlas():
       """ATLAS dataset commands (local build only - DUA required)."""
   # Subcommands: validate, build, info
   # NOTE: build defaults to --dry-run, requires explicit --no-dry-run
   ```

4. **Add validation** (`src/bids_hub/validation/atlas.py`)
   - Check Training/ directory exists
   - Check T1w files exist per subject
   - Warn about missing lesion masks (expected for Testing/)

5. **Add user documentation** (`docs/how-to/build-atlas-locally.md`)
   - Step-by-step DUA process
   - How to build local HF dataset
   - How to push to private repo (optional)

6. **Add tests** (`tests/test_atlas.py`)
   - Follow `test_arc.py` pattern
   - Create synthetic BIDS fixture with ATLAS structure

### Acceptance Criteria

- [ ] `scripts/download_atlas.sh` prints DUA instructions
- [ ] `uv run bids-hub atlas info` shows dataset info + DUA notice
- [ ] `uv run bids-hub atlas validate <path>` works on local data
- [ ] `uv run bids-hub atlas build <path> --dry-run` succeeds
- [ ] `uv run pytest tests/test_atlas.py` passes
- [ ] Documentation explains DUA process clearly
- [ ] **NO automatic public upload** - respects license restrictions

### Resources

- [ICPSR 36684 (Data Access)](https://www.icpsr.umich.edu/web/ICPSR/studies/36684)
- [Scientific Data Paper](https://www.nature.com/articles/s41597-022-01401-7)
- [ATLAS Grand Challenge](https://atlas.grand-challenge.org/)
- [NITRC Archive (preprocessed)](http://fcon_1000.projects.nitrc.org/indi/retro/atlas.html)

### Citation

```bibtex
@article{liew2022atlas,
  title={A large, curated, open-source stroke neuroimaging dataset to improve lesion segmentation algorithms},
  author={Liew, Sook-Lei and Lo, Bethany P and others},
  journal={Scientific Data},
  volume={9},
  number={1},
  pages={320},
  year={2022},
  publisher={Nature Publishing Group}
}
```
