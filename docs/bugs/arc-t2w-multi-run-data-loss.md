# BUG: Structural Data Loss for Multi-Run Sessions

**Date:** 2025-12-14
**Status:** Ready to Implement
**Severity:** Medium (6 sessions affected, data integrity violation)
**Branch:** `fix/structural-multi-run-schema`

## Summary

The ARC build pipeline silently drops structural MRI data (T1w, T2w, FLAIR) when a session has multiple files of the same modality. The code sets the field to `None` instead of storing all files.

**This violates data fidelity.** OpenNeuro is the source of truth. If they uploaded multiple runs, we should too.

## Root Cause

`src/bids_hub/core/utils.py:16-17`:

```python
def find_single_nifti(search_dir: Path, pattern: str) -> str | None:
    ...
    if len(matches) != 1:
        return None  # <-- WRONG: Discards data when multiple files exist
```

This function returns `None` when there are 2+ matches, treating "2 files" the same as "0 files".

## Affected Sessions

| Modality | Session | File Count |
|----------|---------|------------|
| T1w | sub-M2078/ses-3622 | 2 files |
| T1w | sub-M2112/ses-310 | 2 files |
| T1w | sub-M2181/ses-2085 | 2 files |
| T2w | sub-M2105/ses-964 | 2 files |
| FLAIR | sub-M2054/ses-1598 | 2 files |
| FLAIR | sub-M2277/ses-722 | 2 files |

**Total:** 6 sessions have structural data set to `None` when data exists.

## Why Multiple Runs Exist

In BIDS, `run-<n>` means the scanner acquired the same modality multiple times in one session:
- Motion artifacts on first scan → redo
- Technical issue → redo
- Quality control → keep both for comparison

For `sub-M2105/ses-964`:
- `run-6_T2w.nii.gz` - first acquisition
- `run-11_T2w.nii.gz` - second acquisition (lesion mask drawn on this one)

The JSON metadata for both runs is **identical** (same protocol, sequence, parameters). The clinician chose run-11 for lesion annotation (probably better quality).

## Gold Standard Solution

**Principle:** Mirror OpenNeuro exactly. Upload ALL data. Let downstream users filter.

From the [Scientific Data paper](https://www.nature.com/articles/s41597-024-03819-7):
> "Modalities include T1-weighted (229 individuals, **441 series**), T2-weighted (229, **447**)..."

447 T2w series across 229 individuals = some have multiple runs. OpenNeuro kept them all. **So should we.**

### Schema Change

```python
# CURRENT (wrong - loses data)
"t1w": Nifti(),
"t2w": Nifti(),
"flair": Nifti(),

# CORRECT (full data fidelity)
"t1w": Sequence(Nifti()),
"t2w": Sequence(Nifti()),
"flair": Sequence(Nifti()),
```

### Optional Enhancement: Lesion-Matched Index

For convenience, add fields indicating which run matches the lesion mask:

```python
"t2w_lesion_index": Value("int32"),  # Index into t2w[] that matches lesion mask filename
```

This allows:
- **Data fidelity:** All runs uploaded
- **Convenience:** Users can quickly find the "canonical" T2w for lesion analysis

## Implementation Plan

### Files to Modify

1. **`src/bids_hub/datasets/arc.py`**
   - Change schema: `t1w`, `t2w`, `flair` → `Sequence(Nifti())`
   - Use `find_all_niftis()` instead of `find_single_nifti()`
   - Add `t2w_lesion_index` field (optional)

2. **`src/bids_hub/core/utils.py`**
   - `find_single_nifti()` can remain for other uses
   - No changes needed if we use `find_all_niftis()`

3. **`docs/dataset-cards/arc-aphasia-bids.md`**
   - Update schema documentation
   - Add note about multi-run sessions
   - Update usage examples: `session["t2w"]` → `session["t2w"][0]`

4. **`src/bids_hub/validation/arc.py`**
   - Update `ARC_HF_EXPECTED_COUNTS` with correct t2w_acquisition breakdown

### Breaking Change Notes

- **API change:** `session["t2w"]` → `session["t2w"][0]` for single-file access
- **Most sessions (99.6%)** have exactly 1 structural scan, so `[0]` works
- **Empty list `[]`** means no data (replaces `None`)

## Verification

After fix, this should return **223** (not 222):

```python
# Count SPACE samples with lesion masks
space_samples = ds.filter(
    lambda x: (
        len(x["lesion"]) > 0  # has lesion
        and len(x["t2w"]) > 0  # has at least one T2w
        and x["t2w_acquisition"] in ("space_2x", "space_no_accel")
    )
)
print(len(space_samples))  # Should be 223
```

## Related Docs

- `docs/to_do/add-t2w-acquisition-validation.md` - Validation improvement (superseded by this fix)
- `docs/dataset-cards/arc-aphasia-bids.md` - Dataset card to update
