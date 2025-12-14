# ARC Dataset Metadata Parity Audit

**Date:** 2025-12-13
**Auditor:** Claude Code (requested by Ray)
**Status:** 🔴 INCOMPLETE PARITY - Action Required
**Last Updated:** 2025-12-13 (expanded with DWI gradients, lesion sidecars, HF status)

## Summary

The HuggingFace dataset (`hugging-science/arc-aphasia-bids`) contains all **NIfTI imaging data** but is **missing metadata** that exists in the OpenNeuro source (`ds004884`).

### Critical Gaps Identified

| Gap | Severity | Status |
|-----|----------|--------|
| DWI gradients (bval/bvec) | 🔴 CRITICAL | 2089 files NOT uploaded |
| BOLD task entity | 🔴 CRITICAL | Cannot distinguish naming40 vs rest |
| `race` column | 🟡 HIGH | Missing from participants metadata |
| `wab_days` column | 🟡 HIGH | Missing from participants metadata |
| `t2w_acquisition` | 🟡 HIGH | Code merged (PR #13), **NOT yet pushed to HF** |
| Lesion mask SpatialReference | 🟢 LOW | Could resolve multi-T2w ambiguity |

### Current HuggingFace Dataset Status

**Verified 2025-12-13:** `hugging-science/arc-aphasia-bids` has **13 columns** (no `t2w_acquisition`).

PR #13 merged `t2w_acquisition` to our codebase, but **the HuggingFace dataset has NOT been rebuilt/re-pushed**.

## Local Dataset Paths (for verification)

```
OpenNeuro: /Users/ray/Desktop/CLARITY-DIGITAL-TWIN/bids-hub/data/openneuro/ds004884
```

---

## 1. participants.tsv Column Audit

### Source Evidence (OpenNeuro)

```bash
$ head -5 participants.tsv
participant_id	sex	age_at_stroke	race	wab_days	wab_aq	wab_type
sub-M2231	F	23	b	8798	93.3	None
sub-M2182	F	27	w	802	79.2	Conduction
sub-M2146	F	29	w	4696	96.8	None
sub-M2005	F	31	w	4334	54.8	Broca
```

### Parity Matrix

| Column | OpenNeuro | HuggingFace | Status |
|--------|-----------|-------------|--------|
| `participant_id` | ✅ | ✅ `subject_id` | ✅ Complete |
| `sex` | ✅ | ✅ | ✅ Complete |
| `age_at_stroke` | ✅ | ✅ | ✅ Complete |
| **`race`** | ✅ | ❌ | 🔴 **MISSING** |
| **`wab_days`** | ✅ | ❌ | 🔴 **MISSING** |
| `wab_aq` | ✅ | ✅ | ✅ Complete |
| `wab_type` | ✅ | ✅ | ✅ Complete |

### Missing Column Details

#### `race`
- **Description:** Self-reported race of participant
- **Values observed:** `b` (Black), `w` (White), and others
- **Use case:** Demographic analysis, bias auditing in ML models
- **Source:** `participants.json` does not document this column (undocumented in BIDS sidecar)

#### `wab_days`
- **Description:** Days since participant's stroke when WAB assessment was collected
- **Values observed:** Range from ~800 to ~8800 days
- **Use case:** Longitudinal analysis, understanding chronic phase timing
- **Source:** Documented in `participants.json`:
  ```json
  "wab_days": {
      "Description": "Days since participants stroke that the WAB (Western Aphasia Battery-Revised) was collected",
      "Units": "Days"
  }
  ```

---

## 2. BIDS Filename Entity Audit

### Source Evidence (OpenNeuro)

```bash
$ find . -name "*_bold.nii.gz" | head -5 | xargs basename
sub-M2221_ses-2332_task-rest_acq-epfid2p2m2_dir-AP_run-9_bold.nii.gz
sub-M2221_ses-2332_task-naming40_acq-epfid2_dir-AP_run-23_bold.nii.gz
sub-M2221_ses-784_task-naming40_acq-epfid2_dir-AP_run-13_bold.nii.gz
sub-M2221_ses-784_task-rest_acq-epfid2p2m2_dir-AP_run-3_bold.nii.gz
sub-M2221_ses-2045_task-rest_acq-epfid2p2m2_dir-AP_run-9_bold.nii.gz
```

### Entity Extraction (all NIfTIs)

```bash
$ find . -name "*.nii.gz" | sed 's/.*\///' | grep -oE '(acq|task|dir|run)-[a-zA-Z0-9]+' | sort | uniq -c | sort -rn | head -20
2937 dir-AP
1261 acq-epb5m2
 894 task-naming40
 894 acq-epfid2
 876 dir-PA
 672 acq-epb0p2
 508 task-rest
 399 acq-spc3p2
 397 acq-tfl3p2
 296 acq-epse2p2
 259 acq-spc3
 194 acq-spcir2p2
 145 acq-epb0p2m2
 102 acq-epfidp2p2
  31 acq-tir2
  26 acq-tfl3
  26 acq-epse2
  24 acq-tflme3p2
  11 acq-tse3
  10 acq-epb0m2
```

### Parity Matrix

| Entity | Values | HuggingFace | Status | Impact |
|--------|--------|-------------|--------|--------|
| T2w `acq-*` | spc3, spc3p2, tse3 | ✅ `t2w_acquisition` | ✅ Just added (PR #13) | High - needed for paper replication |
| **BOLD `task-*`** | naming40, rest | ❌ | 🔴 **MISSING** | 🔴 **CRITICAL** for fMRI analysis |
| T1w `acq-*` | tfl3, tfl3p2, tflme3p2 | ❌ | 🟡 Not exposed | Low - mostly uniform |
| FLAIR `acq-*` | tir2, spcir2p2, etc. | ❌ | 🟡 Not exposed | Low |
| DWI `acq-*` | epb0p2, epb5m2, etc. | ❌ | 🟡 Not exposed | Medium |
| BOLD `acq-*` | epfid2, epfid2p2m2 | ❌ | 🟡 Not exposed | Low |
| `dir-*` | AP, PA | ❌ | 🟡 Not exposed | Medium - needed for distortion correction |
| `run-*` | 2-33 | ❌ | 🟡 Lost | Medium - we collect all but lose IDs |

### Critical Missing: BOLD `task`

The BOLD fMRI data has **two distinct tasks**:
1. `task-naming40` - Picture naming task (894 runs)
2. `task-rest` - Resting state fMRI (508 runs)

**Current behavior:** Both are mixed together in `bold: Sequence(Nifti())` with no way to distinguish.

**Impact:** Anyone doing fMRI analysis CANNOT separate task from rest data without re-downloading from OpenNeuro.

---

## 3. DWI Gradient Files (bval/bvec) Audit

### Source Evidence (OpenNeuro)

```bash
$ find . -name "*.bval" | wc -l
2089

$ find . -name "*.bvec" | wc -l
2089

$ find . -name "*_dwi.nii.gz" | wc -l
2089
```

**PERFECT 1:1:1 MATCH** - Every DWI NIfTI has both `.bval` and `.bvec` gradient files.

### Sample Files

```text
sub-M2001/ses-1/dwi/
├── sub-M2001_ses-1_acq-epb0p2_dir-AP_run-1_dwi.nii.gz
├── sub-M2001_ses-1_acq-epb0p2_dir-AP_run-1_dwi.bval    ← NOT UPLOADED
├── sub-M2001_ses-1_acq-epb0p2_dir-AP_run-1_dwi.bvec    ← NOT UPLOADED
```

### Why This Matters

DWI analysis **requires** gradient information:
- `.bval` - b-values (diffusion weighting strength)
- `.bvec` - gradient directions (3D vectors)

Without these, DWI NIfTIs are **useless for diffusion analysis** (tractography, FA maps, etc.).

### Parity Status

| File Type | OpenNeuro | HuggingFace | Status |
|-----------|-----------|-------------|--------|
| `*_dwi.nii.gz` | 2089 | 2089 | ✅ Complete |
| `*_dwi.bval` | 2089 | 0 | 🔴 **MISSING** |
| `*_dwi.bvec` | 2089 | 0 | 🔴 **MISSING** |

---

## 4. Lesion Mask JSON Sidecars

### Source Evidence (OpenNeuro)

```bash
$ find . -name "*lesion_mask*.json" | head -3 | xargs cat
```

```json
{
    "Type": "Lesion",
    "SpatialReference": "bids:raw:sub-M2221/ses-2045/anat/sub-M2221_ses-2045_acq-spc3p2_run-4_T2w.nii.gz"
}
{
    "Type": "Lesion",
    "SpatialReference": "bids:raw:sub-M2013/ses-195/anat/sub-M2013_ses-195_acq-spc3_run-3_T2w.nii.gz"
}
```

### Why This Matters

The `SpatialReference` field **explicitly links each lesion mask to its corresponding T2w image**.

This could resolve the **multi-T2w session ambiguity** (sub-M2105/ses-964 has 2 T2w files):
- Instead of `find_single_nifti()` returning `None`, we could parse the JSON sidecar
- The sidecar tells us exactly which T2w the lesion was traced on

### Current Status

| Data | OpenNeuro | HuggingFace | Status |
|------|-----------|-------------|--------|
| Lesion mask NIfTI | 228 | 228 | ✅ Complete |
| Lesion mask JSON sidecar | 228 | 0 | 🟡 Not exposed (low priority) |
| SpatialReference parsing | N/A | ❌ | 🟡 Could resolve ambiguity |

---

## 5. Scanner/Sequence Sidecar JSON Metadata

Each NIfTI has a sidecar JSON with scanner/sequence parameters. Example:

```json
{
    "Manufacturer": "Siemens",
    "ManufacturersModelName": "TrioTim",
    "MagneticFieldStrength": 3,
    "EchoTime": 0.00452,
    "RepetitionTime": 2.25,
    "FlipAngle": 9,
    ...
}
```

**Status:** ❌ Not exposed in HuggingFace schema

**Impact:** Low for most use cases. Researchers needing this would download from OpenNeuro anyway.

---

## 6. Recommendations

### Priority 0: BLOCKING (makes data unusable for intended purpose)

| Field | Effort | Impact | Blocking? |
|-------|--------|--------|-----------|
| DWI `.bval` files | Medium | 🔴 CRITICAL - DWI unusable for diffusion analysis | **YES** |
| DWI `.bvec` files | Medium | 🔴 CRITICAL - DWI unusable for diffusion analysis | **YES** |
| `bold_task` | Medium (restructure) | 🔴 CRITICAL - fMRI unusable without this | **YES** |

### Priority 1: MUST FIX (breaks usability)

| Field | Effort | Impact |
|-------|--------|--------|
| `race` | Low (add to schema) | High - demographic analysis |
| `wab_days` | Low (add to schema) | High - longitudinal analysis |
| `t2w_acquisition` push | Low (rebuild + push) | High - already in code, not in HF yet |

### Priority 2: SHOULD FIX (improves completeness)

| Field | Effort | Impact |
|-------|--------|--------|
| `dir` (phase encoding) | Medium | Useful for distortion correction |
| `run` numbers | Medium | Useful for ordering/identification |

### Priority 3: NICE TO HAVE

| Field | Effort | Impact |
|-------|--------|--------|
| T1w/FLAIR acquisition types | Low | Marginal benefit |
| Lesion mask SpatialReference | Low | Could resolve multi-T2w edge case |
| Sidecar JSON fields | High | Low benefit (download from source) |

---

## 7. Impact on Downstream Projects

### arc-meshchop (lesion segmentation)
- ✅ T1w, T2w, FLAIR, lesion masks: **Complete**
- ✅ T2w acquisition type: **Just added** (code only, not yet on HF)
- ❌ `race`, `wab_days`: **Not needed** for segmentation
- ❌ BOLD task: **Not needed** for segmentation
- ❌ DWI gradients: **Not needed** for segmentation

**Verdict:** arc-meshchop is unaffected by missing metadata.

### Diffusion Research (tractography, FA maps, etc.)
- ❌ **BLOCKED** - DWI NIfTIs are present but bval/bvec are NOT
- Without gradient information, DWI data is **completely unusable**
- Researchers MUST re-download from OpenNeuro for any diffusion analysis

### fMRI Research
- ❌ **BLOCKED** - cannot distinguish task (naming40) vs rest
- Both task types mixed in `bold: Sequence(Nifti())`
- Researchers MUST re-download from OpenNeuro for fMRI analysis

### Demographic/Longitudinal Studies
- ❌ **BLOCKED** - missing `race`
- ❌ **BLOCKED** - missing `wab_days`

---

## 8. Action Items

### P0 - BLOCKING (must fix before dataset is usable)

- [ ] Add DWI `.bval` files to schema (new feature type needed?)
- [ ] Add DWI `.bvec` files to schema (new feature type needed?)
- [ ] Restructure BOLD to preserve `task` entity (breaking change?)

### P1 - MUST FIX

- [ ] Add `race` column to schema
- [ ] Add `wab_days` column to schema
- [ ] Rebuild and push to HuggingFace (includes `t2w_acquisition`)

### P2 - SHOULD FIX

- [ ] Consider adding `dir` (phase encoding direction)
- [ ] Consider preserving `run` numbers

### P3 - NICE TO HAVE

- [ ] Parse lesion mask SpatialReference to resolve multi-T2w ambiguity

---

## 9. Version History

| Date | Change |
|------|--------|
| 2025-12-13 | Initial audit created |
| 2025-12-13 | PR #13 merged: Added `t2w_acquisition` field (code only) |
| 2025-12-13 | Expanded audit: DWI gradients, lesion sidecars, HF status verified |

---

**Reviewed by:** _Pending senior review_
