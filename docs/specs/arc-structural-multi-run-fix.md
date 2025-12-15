# SPEC: ARC Structural Multi-Run Schema Fix

**Date:** 2025-12-14 (Updated 2025-12-15)
**Status:** Ready to Implement
**Branch:** `fix/structural-multi-run-schema`
**Bug Doc:** `docs/bugs/arc-t2w-multi-run-data-loss.md`

## Problem Statement

The ARC build pipeline drops structural MRI data when a session has multiple files of the same modality (T1w, T2w, FLAIR). This violates data fidelity - OpenNeuro uploaded all files, we should too.

**Affected:** 6 sessions across 3 modalities

## SSOT File Counts (Verified)

From `data/openneuro/ds004884/` (excluding derivatives):
- **T1w:** 447 files across 444 sessions (3 sessions have 2 files)
- **T2w:** 441 files across 440 sessions (1 session has 2 files)
- **FLAIR:** 235 files across 233 sessions (2 sessions have 2 files)

**Multi-run sessions:**

| Modality | Session | Files |
|----------|---------|-------|
| T1w | sub-M2078/ses-3622 | 2 |
| T1w | sub-M2112/ses-310 | 2 |
| T1w | sub-M2181/ses-2085 | 2 |
| T2w | sub-M2105/ses-964 | 2 |
| FLAIR | sub-M2054/ses-1598 | 2 |
| FLAIR | sub-M2277/ses-722 | 2 |

---

## Implementation Checklist

### 1. Schema Change (`src/bids_hub/datasets/arc.py`)

**Location:** `get_arc_features()` function (line ~323)

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

**Location:** `build_arc_file_table()` function (line ~117)

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

**Location:** In `build_arc_file_table()`, after file discovery

```python
# BEFORE
if t2w_path:
    t2w_acquisition = _extract_acquisition_type(t2w_path)

# AFTER
if t2w_paths:
    # Use first T2w for acquisition type (all runs in a session use same sequence)
    t2w_acquisition = _extract_acquisition_type(t2w_paths[0])
else:
    t2w_acquisition = None
```

### 4. Row Construction Change (`src/bids_hub/datasets/arc.py`)

**Location:** Row dict construction in `build_arc_file_table()`

```python
# BEFORE
{
    "t1w": t1w_path,      # str | None
    "t2w": t2w_path,      # str | None
    "flair": flair_path,  # str | None
    ...
}

# AFTER
{
    "t1w": t1w_paths,      # list[str] (empty if none)
    "t2w": t2w_paths,      # list[str] (empty if none)
    "flair": flair_paths,  # list[str] (empty if none)
    ...
}
```

### 5. Validation Update (`src/bids_hub/validation/arc.py`)

**Location:** `_check_nifti_loadable()` function (line ~224)

This function currently assumes structural columns are single Nifti. Must update to handle lists:

```python
# BEFORE (assumes single Nifti)
if row["t1w"] is not None:
    _try_load(row["t1w"])

# AFTER (handles list of Nifti)
for t1w_path in row["t1w"]:
    _try_load(t1w_path)
```

**Also update:** `ARC_HF_EXPECTED_COUNTS` dict - change validation strategy:
- OLD: `"t1w_non_null": 441` (count of sessions where t1w is not None)
- NEW: `"t1w_sessions": 444, "t1w_files": 447`

### 6. Update Tests (`tests/test_arc.py`)

**Add multi-run structural fixture:**

```python
def test_multi_run_structural_sessions_included():
    """Verify sessions with multiple structural files have all files."""
    # Create synthetic BIDS with 2 T2w files for one session
    # Assert len(row["t2w"]) == 2
```

**Update existing tests:**

```python
# BEFORE
assert row["t2w"] is None or isinstance(row["t2w"], str)

# AFTER
assert isinstance(row["t2w"], list)
assert all(isinstance(p, str) for p in row["t2w"])
```

### 7. Update Dataset Card (`docs/dataset-cards/arc-aphasia-bids.md`)

#### Metrics Table (line ~30-42)

Update footnote to reflect new behavior:
```markdown
*Sessions with multiple runs of the same structural modality now include all runs as a list.
```

#### Schema Section

```python
# BEFORE
"t1w": <nibabel.Nifti1Image>,              # T1-weighted structural

# AFTER
"t1w": [<nibabel.Nifti1Image>, ...],       # T1-weighted structural (list of runs)
```

#### Data Fields Table

```markdown
| `t1w` | Sequence[Nifti] | T1-weighted structural MRI runs |
| `t2w` | Sequence[Nifti] | T2-weighted structural MRI runs |
| `flair` | Sequence[Nifti] | FLAIR structural MRI runs |
```

#### Usage Examples (line ~203)

**FIX:** Current comment claims 223 SPACE samples, but until v4 it's 222. After v4:

```python
# Filter by T2w acquisition type
space_only = ds.filter(
    lambda x: (
        x["lesion"] is not None
        and len(x["t2w"]) > 0
        and x["t2w_acquisition"] in ("space_2x", "space_no_accel")
    )
)
# Returns 223 SPACE samples (115 space_2x + 108 space_no_accel)
```

---

## Acceptance Criteria (Must Be True After Fix)

### File Counts Match SSOT
- `t1w` total items across all sessions: **447**
- `t2w` total items across all sessions: **441**
- `flair` total items across all sessions: **235**

### Session Counts Match SSOT
- Sessions with at least one `t1w`: **444**
- Sessions with at least one `t2w`: **440**
- Sessions with at least one `flair`: **233**

### Lesion SPACE Breakdown Correct
- Among 228 lesion sessions:
  - `space_2x`: **115**
  - `space_no_accel`: **108**
  - `turbo_spin_echo`: **5**
  - `None` (no T2w): **0** (was 1 before fix)
- Filter `(lesion present) AND (t2w present) AND (SPACE type)`: **223** (was 222)

### Multi-Run Sessions Have Data
```python
# sub-M2105/ses-964 must have 2 T2w files
session = get_session("sub-M2105", "ses-964")
assert len(session["t2w"]) == 2
assert session["t2w_acquisition"] == "space_no_accel"
```

---

## Verification Commands

```bash
# 1. Run tests
uv run pytest tests/test_arc.py -v

# 2. Type check
uv run mypy src/bids_hub/datasets/arc.py src/bids_hub/validation/arc.py

# 3. Dry-run build and verify counts
uv run python -c "
from bids_hub.datasets.arc import build_arc_file_table
from pathlib import Path

df = build_arc_file_table(Path('data/openneuro/ds004884'))

# File counts
t1w_total = sum(len(row) for row in df['t1w'])
t2w_total = sum(len(row) for row in df['t2w'])
flair_total = sum(len(row) for row in df['flair'])
print(f't1w_total={t1w_total} (expect 447)')
print(f't2w_total={t2w_total} (expect 441)')
print(f'flair_total={flair_total} (expect 235)')

# Session counts
t1w_sessions = sum(1 for row in df['t1w'] if row)
t2w_sessions = sum(1 for row in df['t2w'] if row)
flair_sessions = sum(1 for row in df['flair'] if row)
print(f't1w_sessions={t1w_sessions} (expect 444)')
print(f't2w_sessions={t2w_sessions} (expect 440)')
print(f'flair_sessions={flair_sessions} (expect 233)')

# SPACE lesion count
lesion_space = df[
    (df['lesion'].notna()) &
    (df['t2w'].apply(len) > 0) &
    (df['t2w_acquisition'].isin(['space_2x', 'space_no_accel']))
]
print(f'SPACE lesion sessions={len(lesion_space)} (expect 223)')

# Verify multi-run session
m2105 = df[(df['subject_id']=='sub-M2105') & (df['session_id']=='ses-964')].iloc[0]
print(f'sub-M2105/ses-964 t2w count={len(m2105[\"t2w\"])} (expect 2)')
"

# 4. Full upload (when verification passes)
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
```

---

## Breaking Change Summary

| Before (v3) | After (v4) |
|-------------|------------|
| `session["t2w"]` → `Nifti` or `None` | `session["t2w"]` → `list[Nifti]` (empty if none) |
| Check: `if session["t2w"]:` | Check: `if session["t2w"]:` (still works) |
| Access: `session["t2w"].get_fdata()` | Access: `session["t2w"][0].get_fdata()` |
