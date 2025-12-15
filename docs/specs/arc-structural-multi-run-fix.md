# SPEC: ARC Structural Multi-Run Schema Fix

**Date:** 2025-12-14
**Status:** Ready to Implement
**Branch:** `fix/structural-multi-run-schema`
**Bug Doc:** `docs/bugs/arc-t2w-multi-run-data-loss.md`

## Problem Statement

The ARC build pipeline drops structural MRI data when a session has multiple files of the same modality (T1w, T2w, FLAIR). This violates data fidelity - OpenNeuro uploaded all files, we should too.

**Affected:** 6 sessions across 3 modalities (see bug doc for list)

## Solution

Change structural modalities from singleton `Nifti()` to list `Sequence(Nifti())`, matching what we already do for BOLD and DWI.

---

## Implementation Checklist

### 1. Schema Change (`src/bids_hub/datasets/arc.py`)

**Location:** `ARC_FEATURES` dict (around line 30-50)

```python
# BEFORE
"t1w": Nifti(),
"t2w": Nifti(),
"flair": Nifti(),

# AFTER
"t1w": Sequence(Nifti()),
"t2w": Sequence(Nifti()),
"flair": Sequence(Nifti()),
```

### 2. File Discovery Change (`src/bids_hub/datasets/arc.py`)

**Location:** `build_file_table()` function

```python
# BEFORE (uses find_single_nifti)
t1w_path = find_single_nifti(anat_dir, "*_T1w.nii.gz")
t2w_path = find_single_nifti(anat_dir, "*_T2w.nii.gz")
flair_path = find_single_nifti(anat_dir, "*_FLAIR.nii.gz")

# AFTER (uses find_all_niftis)
t1w_paths = find_all_niftis(anat_dir, "*_T1w.nii.gz")
t2w_paths = find_all_niftis(anat_dir, "*_T2w.nii.gz")
flair_paths = find_all_niftis(anat_dir, "*_FLAIR.nii.gz")
```

### 3. t2w_acquisition Logic Change (`src/bids_hub/datasets/arc.py`)

**Current logic:** Extracts acquisition type from single T2w path
**New logic:** Extract from first T2w path (or None if empty list)

```python
# BEFORE
if t2w_path:
    t2w_acquisition = _extract_t2w_acquisition(t2w_path)

# AFTER
if t2w_paths:
    # Use first T2w for acquisition type (they should all be same type)
    t2w_acquisition = _extract_t2w_acquisition(t2w_paths[0])
else:
    t2w_acquisition = None
```

### 4. Row Construction Change (`src/bids_hub/datasets/arc.py`)

**Location:** Row dict construction in `build_file_table()`

```python
# BEFORE
{
    "t1w": t1w_path,
    "t2w": t2w_path,
    "flair": flair_path,
    ...
}

# AFTER
{
    "t1w": t1w_paths,  # List of paths (empty list if none)
    "t2w": t2w_paths,  # List of paths (empty list if none)
    "flair": flair_paths,  # List of paths (empty list if none)
    ...
}
```

### 5. Update Tests (`tests/test_arc.py`)

Update any tests that check structural fields to expect lists:

```python
# BEFORE
assert row["t2w"] is None or isinstance(row["t2w"], str)

# AFTER
assert isinstance(row["t2w"], list)
assert all(isinstance(p, str) for p in row["t2w"])
```

### 6. Update Dataset Card (`docs/dataset-cards/arc-aphasia-bids.md`)

#### Schema Section

```python
# BEFORE
"t1w": <nibabel.Nifti1Image>,
"t2w": <nibabel.Nifti1Image>,
"flair": <nibabel.Nifti1Image>,

# AFTER
"t1w": [<nibabel.Nifti1Image>, ...],   # List of T1w runs
"t2w": [<nibabel.Nifti1Image>, ...],   # List of T2w runs
"flair": [<nibabel.Nifti1Image>, ...], # List of FLAIR runs
```

#### Data Fields Table

```markdown
| `t1w` | Sequence[Nifti] | T1-weighted structural MRI runs |
| `t2w` | Sequence[Nifti] | T2-weighted structural MRI runs |
| `flair` | Sequence[Nifti] | FLAIR structural MRI runs |
```

#### Usage Examples

```python
# BEFORE
print(session["t1w"])  # nibabel.Nifti1Image

# AFTER
# Most sessions have exactly 1 structural scan
if session["t1w"]:
    t1w = session["t1w"][0]  # First (usually only) T1w
    print(t1w.shape)

# Some sessions have multiple runs (6 total across all modalities)
for i, t2w_run in enumerate(session["t2w"]):
    print(f"T2w run {i+1}: {t2w_run.shape}")
```

#### Add Known Limitations Note

```markdown
### Multi-Run Structural Sessions

Six sessions have multiple structural scans (reacquisitions):
- 3 sessions with 2 T1w files
- 1 session with 2 T2w files
- 2 sessions with 2 FLAIR files

For lesion analysis: The lesion mask filename contains the run number indicating which structural scan was used for annotation.
```

### 7. Update Validation (`src/bids_hub/validation/arc.py`)

Add t2w_acquisition breakdown counts:

```python
ARC_HF_EXPECTED_COUNTS = {
    "lesion_non_null": 228,
    "space_2x_count": 115,
    "space_no_accel_count": 108,
    "turbo_spin_echo_count": 5,
    ...
}
```

---

## Verification Steps

After implementation:

1. **Run tests:**
   ```bash
   uv run pytest tests/test_arc.py -v
   ```

2. **Dry-run build:**
   ```bash
   uv run bids-hub arc build data/openneuro/ds004884 --dry-run
   ```

3. **Verify SPACE count:**
   ```python
   # Should return 223 (not 222)
   space_count = len([
       r for r in rows
       if r["lesion"] and r["t2w"] and r["t2w_acquisition"] in ("space_2x", "space_no_accel")
   ])
   assert space_count == 223
   ```

4. **Verify multi-run sessions have data:**
   ```python
   # sub-M2105/ses-964 should have 2 T2w files now
   session = next(r for r in rows if r["subject_id"] == "sub-M2105" and r["session_id"] == "ses-964")
   assert len(session["t2w"]) == 2
   ```

5. **Full upload (when ready):**
   ```bash
   uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
   ```

---

## Breaking Change Summary

| Before | After |
|--------|-------|
| `session["t2w"]` returns `Nifti` or `None` | `session["t2w"]` returns `list[Nifti]` (empty if none) |
| Check `if session["t2w"]:` | Check `if session["t2w"]:` (still works, empty list is falsy) |
| Direct access: `session["t2w"].get_fdata()` | Index first: `session["t2w"][0].get_fdata()` |

**Impact:** This is a **v4 breaking change**. Update dataset card changelog.
