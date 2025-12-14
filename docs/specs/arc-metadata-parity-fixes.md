# Spec: ARC Dataset Metadata Parity Fixes

**Status:** Pending Senior Review
**Priority:** P0 (Blocking) + P1 (Must Fix)
**Upstream Dataset:** [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884)
**HuggingFace Target:** [hugging-science/arc-aphasia-bids](https://huggingface.co/datasets/hugging-science/arc-aphasia-bids)
**Audit Document:** [ARC_METADATA_PARITY_AUDIT.md](/ARC_METADATA_PARITY_AUDIT.md)
**Last Audit:** 2025-12-13

---

## Problem Statement

The ARC dataset on HuggingFace is missing critical metadata that exists in the OpenNeuro source. This makes portions of the dataset **unusable for their intended purpose**.

### Impact Summary

| Data Type | Current State | Impact |
|-----------|---------------|--------|
| DWI imaging | NIfTIs uploaded, **bval/bvec NOT uploaded** | DWI is **USELESS** for diffusion analysis |
| BOLD fMRI | All runs mixed together | Cannot distinguish task (naming40) from rest |
| Demographics | `race` column missing | Cannot perform demographic analysis |
| Longitudinal | `wab_days` column missing | Cannot analyze timing since stroke |

---

## Verified Facts (Source of Truth)

### 1. DWI Gradient Files

**Location:** `/Users/ray/Desktop/CLARITY-DIGITAL-TWIN/bids-hub/data/openneuro/ds004884`

```bash
$ find . -name "*.bval" | wc -l
2089

$ find . -name "*.bvec" | wc -l
2089

$ find . -name "*_dwi.nii.gz" | wc -l
2089
```

**PERFECT 1:1:1 MATCH** - Every DWI NIfTI has both gradient files.

**Sample file structure:**
```text
sub-M2001/ses-1/dwi/
├── sub-M2001_ses-1_acq-epb0p2_dir-AP_run-1_dwi.nii.gz  ← Uploaded
├── sub-M2001_ses-1_acq-epb0p2_dir-AP_run-1_dwi.bval    ← NOT uploaded
└── sub-M2001_ses-1_acq-epb0p2_dir-AP_run-1_dwi.bvec    ← NOT uploaded
```

**Why bval/bvec are required:**
- `.bval` contains b-values (diffusion weighting strength)
- `.bvec` contains gradient directions (3D vectors)
- Without these, DWI NIfTIs cannot be used for:
  - Tractography
  - FA/MD map calculation
  - Any diffusion tensor analysis

---

### 2. BOLD Task Entity

**BOLD files have two distinct tasks:**

```bash
$ find . -name "*_bold.nii.gz" | grep -oE 'task-[a-z0-9]+' | sort | uniq -c
 894 task-naming40
 508 task-rest
```

| Task | Purpose | Count |
|------|---------|-------|
| `task-naming40` | Picture naming cognitive task | 894 runs |
| `task-rest` | Resting state fMRI (baseline) | 508 runs |

**Current problem:** Both are stored in `bold: Sequence(Nifti())` with NO metadata.

**Sample filenames:**
```text
sub-M2221_ses-2332_task-rest_acq-epfid2p2m2_dir-AP_run-9_bold.nii.gz
sub-M2221_ses-2332_task-naming40_acq-epfid2_dir-AP_run-23_bold.nii.gz
```

---

### 3. participants.tsv Columns

**Source file:** `ds004884/participants.tsv`

**Verified counts:**
```text
participants.tsv rows (data): 244
Actual sub-* directories:     230
Subjects in TSV but no dir:   15 (sub-M2019, sub-M2085, sub-M2130, etc.)
```

```bash
$ head -1 participants.tsv | tr '\t' '\n' | cat -n
     1  participant_id
     2  sex
     3  age_at_stroke
     4  race              ← MISSING from HuggingFace
     5  wab_days          ← MISSING from HuggingFace
     6  wab_aq
     7  wab_type
```

**Sample data:**
```tsv
participant_id  sex  age_at_stroke  race  wab_days  wab_aq  wab_type
sub-M2231       F    23             b     8798      93.3    None
sub-M2182       F    27             w     802       79.2    Conduction
sub-M2146       F    29             w     4696      96.8    None
```

**Column descriptions:**
- `race`: Self-reported race. **Values:** `b` (Black, n=52), `w` (White, n=191), NaN (n=2). No other values exist.
- `wab_days`: Days since stroke when WAB assessment was collected. **Range:** 42 to 8798 days.

---

### 4. Current HuggingFace Dataset Status

**Verified 2025-12-13:** The live HuggingFace dataset has **13 columns**.

| Column | Status |
|--------|--------|
| subject_id | ✅ |
| session_id | ✅ |
| t1w | ✅ |
| t2w | ✅ |
| t2w_acquisition | ❌ **Code merged (PR #13), NOT pushed to HF** |
| flair | ✅ |
| bold | ✅ (but no task separation) |
| dwi | ✅ (but no gradients) |
| sbref | ✅ |
| lesion | ✅ |
| age_at_stroke | ✅ |
| sex | ✅ |
| wab_aq | ✅ |
| wab_type | ✅ |
| race | ❌ **MISSING** |
| wab_days | ❌ **MISSING** |
| dwi_bvals | ❌ **MISSING** |
| dwi_bvecs | ❌ **MISSING** |
| bold_naming40 | ❌ **MISSING** (task not separated) |
| bold_rest | ❌ **MISSING** (task not separated) |

---

## Implementation Specification

### Change 1: Add DWI Gradient Files (P0 - BLOCKING)

#### 1.1 Add Helper Function

**File:** `src/bids_hub/datasets/arc.py`
**Location:** After `_extract_acquisition_type()` (~line 76)

```python
def _read_gradient_file(nifti_path: str, extension: str) -> str | None:
    """Read bval or bvec file content for a DWI NIfTI.

    DWI files in BIDS have companion gradient files with the same base name:
    - sub-X_ses-Y_dwi.nii.gz
    - sub-X_ses-Y_dwi.bval  (b-values)
    - sub-X_ses-Y_dwi.bvec  (gradient directions)

    Args:
        nifti_path: Absolute path to DWI NIfTI file
        extension: Either ".bval" or ".bvec"

    Returns:
        File content as string (whitespace-stripped), or None if file doesn't exist.

    Example:
        >>> _read_gradient_file("/data/sub-M2001_ses-1_dwi.nii.gz", ".bval")
        "0 1000 2000 3000"
    """
    # Handle .nii.gz -> .bval/.bvec path conversion
    # Path("/foo/bar.nii.gz").with_suffix("") -> "/foo/bar.nii"
    # Path("/foo/bar.nii").with_suffix(".bval") -> "/foo/bar.bval"
    base_path = Path(nifti_path)
    if base_path.suffix == ".gz":
        base_path = base_path.with_suffix("")  # Remove .gz
    gradient_path = base_path.with_suffix(extension)  # Replace .nii with .bval/.bvec

    if not gradient_path.exists():
        logger.debug("Gradient file not found: %s", gradient_path)
        return None

    return gradient_path.read_text().strip()
```

#### 1.2 Update `build_arc_file_table()`

**Location:** After `dwi_paths = find_all_niftis(...)` (~line 193)

```python
# Find diffusion modalities in dwi/ (ALL runs)
dwi_paths = find_all_niftis(session_dir / "dwi", "*_dwi.nii.gz")

# NEW: Read gradient files for each DWI run
dwi_bvals = [_read_gradient_file(p, ".bval") for p in dwi_paths]
dwi_bvecs = [_read_gradient_file(p, ".bvec") for p in dwi_paths]
```

**Location:** Update `rows.append()` dict (~line 211)

```python
"dwi": dwi_paths,
"dwi_bvals": dwi_bvals,  # NEW
"dwi_bvecs": dwi_bvecs,  # NEW
```

#### 1.3 Update `get_arc_features()`

**Location:** After `"dwi": Sequence(Nifti()),` (~line 279)

```python
"dwi": Sequence(Nifti()),
"dwi_bvals": Sequence(Value("string")),  # NEW
"dwi_bvecs": Sequence(Value("string")),  # NEW
```

**CRITICAL INVARIANT:** `dwi`, `dwi_bvals`, and `dwi_bvecs` MUST have the same length and order:
- `dwi[i]` corresponds to `dwi_bvals[i]` and `dwi_bvecs[i]`
- If a gradient file is missing, the value is `None` (not omitted)
- This allows: `for nifti, bval, bvec in zip(row["dwi"], row["dwi_bvals"], row["dwi_bvecs"])`

#### 1.4 Update Tests

**File:** `tests/test_arc.py`

**IMPORTANT:** The existing test fixture creates DWI files with run numbers:
```python
# Existing fixture (lines 102-110):
root / "sub-M2001" / "ses-1" / "dwi" / "sub-M2001_ses-1_run-01_dwi.nii.gz"
root / "sub-M2001" / "ses-1" / "dwi" / "sub-M2001_ses-1_run-02_dwi.nii.gz"
root / "sub-M2001" / "ses-1" / "dwi" / "sub-M2001_ses-1_run-03_dwi.nii.gz"
```

**Add gradient files matching each DWI run (after DWI NIfTI creation):**
```python
# Create gradient files alongside each DWI run
dwi_dir = root / "sub-M2001" / "ses-1" / "dwi"
(dwi_dir / "sub-M2001_ses-1_run-01_dwi.bval").write_text("0 1000 2000")
(dwi_dir / "sub-M2001_ses-1_run-01_dwi.bvec").write_text("1 0 0\n0 1 0\n0 0 1")
(dwi_dir / "sub-M2001_ses-1_run-02_dwi.bval").write_text("0 1000")
(dwi_dir / "sub-M2001_ses-1_run-02_dwi.bvec").write_text("1 0\n0 1\n0 0")
(dwi_dir / "sub-M2001_ses-1_run-03_dwi.bval").write_text("0 500 1000 1500")
(dwi_dir / "sub-M2001_ses-1_run-03_dwi.bvec").write_text("1 0 0 0\n0 1 0 0\n0 0 1 0")
```

**Add test class:**
```python
class TestReadGradientFile:
    """Tests for _read_gradient_file helper."""

    def test_reads_bval_content(self, tmp_path: Path) -> None:
        nifti = tmp_path / "sub-M2001_ses-1_dwi.nii.gz"
        bval = tmp_path / "sub-M2001_ses-1_dwi.bval"
        nifti.touch()
        bval.write_text("0 1000 2000\n")

        from bids_hub.datasets.arc import _read_gradient_file
        result = _read_gradient_file(str(nifti), ".bval")
        assert result == "0 1000 2000"

    def test_returns_none_when_missing(self, tmp_path: Path) -> None:
        nifti = tmp_path / "sub-M2001_ses-1_dwi.nii.gz"
        nifti.touch()
        # No .bval file created

        from bids_hub.datasets.arc import _read_gradient_file
        result = _read_gradient_file(str(nifti), ".bval")
        assert result is None
```

---

### Change 2: Split BOLD by Task (P0 - BLOCKING)

#### 2.1 Update `build_arc_file_table()`

**Location:** Replace BOLD collection (~line 190)

**Before:**
```python
bold_paths = find_all_niftis(session_dir / "func", "*_bold.nii.gz")
```

**After:**
```python
# Find functional modalities in func/ - split by task
bold_all = find_all_niftis(session_dir / "func", "*_bold.nii.gz")
bold_naming40 = [p for p in bold_all if "task-naming40" in p]
bold_rest = [p for p in bold_all if "task-rest" in p]
```

**Location:** Update `rows.append()` dict

**Before:**
```python
"bold": bold_paths,
```

**After:**
```python
"bold_naming40": bold_naming40,
"bold_rest": bold_rest,
```

#### 2.2 Update `get_arc_features()`

**Before:**
```python
"bold": Sequence(Nifti()),
```

**After:**
```python
"bold_naming40": Sequence(Nifti()),
"bold_rest": Sequence(Nifti()),
```

#### 2.3 Update Docstrings

**In `build_arc_file_table()` Returns section:**
```python
- bold_naming40 (list[str]): Paths to BOLD runs for picture naming task
- bold_rest (list[str]): Paths to BOLD runs for resting state
```

**In `get_arc_features()` Schema section:**
```python
- bold_naming40: BOLD fMRI for naming40 task (Sequence of Nifti)
- bold_rest: BOLD fMRI for resting state (Sequence of Nifti)
```

#### 2.4 Update Tests

**IMPORTANT:** The existing fixture already has two `task-rest` BOLD files (lines 95-100):
```python
# Existing fixture:
root / "sub-M2001" / "ses-1" / "func" / "sub-M2001_ses-1_task-rest_run-01_bold.nii.gz"
root / "sub-M2001" / "ses-1" / "func" / "sub-M2001_ses-1_task-rest_run-02_bold.nii.gz"
```

**Add one `task-naming40` file to test task splitting:**
```python
# ADD this after existing BOLD files:
func_dir = root / "sub-M2001" / "ses-1" / "func"
_create_minimal_nifti(func_dir / "sub-M2001_ses-1_task-naming40_run-01_bold.nii.gz")
```

**Result:** Session will have 2 rest + 1 naming40 = 3 total BOLD files

**Add assertions:**
```python
def test_bold_split_by_task(self, synthetic_bids_root: Path) -> None:
    """Verify BOLD files are correctly split by task entity."""
    df = build_arc_file_table(synthetic_bids_root)
    ses1 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-1")].iloc[0]

    # Verify types
    assert isinstance(ses1["bold_naming40"], list)
    assert isinstance(ses1["bold_rest"], list)

    # Verify counts (1 naming40 + 2 rest from fixture)
    assert len(ses1["bold_naming40"]) == 1
    assert len(ses1["bold_rest"]) == 2

    # Verify task entities in paths
    assert "task-naming40" in ses1["bold_naming40"][0]
    assert all("task-rest" in p for p in ses1["bold_rest"])
```

---

### Change 3: Add `race` Column (P1 - MUST FIX)

#### 3.1 Update `build_arc_file_table()`

**Location:** After `wab_type` extraction (~line 177)

```python
wab_type = str(row.get("wab_type", "")) if pd.notna(row.get("wab_type")) else None

# NEW: Extract race
race = str(row.get("race", "")) if pd.notna(row.get("race")) else None
```

**Location:** Update `rows.append()` dict

```python
"race": race,
```

#### 3.2 Update `get_arc_features()`

```python
"race": Value("string"),
```

#### 3.3 Update Docstrings

**In `build_arc_file_table()` Returns:**
```python
- race (str | None): Self-reported race (e.g., "b", "w")
```

**In `get_arc_features()` Schema:**
```python
- race: Self-reported race
```

---

### Change 4: Add `wab_days` Column (P1 - MUST FIX)

#### 4.1 Update `build_arc_file_table()`

**Location:** After `race` extraction

```python
race = str(row.get("race", "")) if pd.notna(row.get("race")) else None

# NEW: Extract wab_days
wab_days_raw = row.get("wab_days")
wab_days: float | None = None
if wab_days_raw is not None and pd.notna(wab_days_raw):
    try:
        wab_days = float(wab_days_raw)
    except (ValueError, TypeError):
        logger.warning("Invalid wab_days for %s: %r", subject_id, wab_days_raw)
```

**Location:** Update `rows.append()` dict

```python
"wab_days": wab_days,
```

#### 4.2 Update `get_arc_features()`

```python
"wab_days": Value("float32"),
```

#### 4.3 Update Docstrings

**In `build_arc_file_table()` Returns:**
```python
- wab_days (float | None): Days since stroke when WAB assessment was collected
```

---

## New Schema (19 columns)

After all changes, the ARC dataset will have **19 columns** (up from 14):

**Column count breakdown:**
- Current HF: 13 columns
- + t2w_acquisition (code done, not pushed): 14 columns
- + race, wab_days: 16 columns
- + dwi_bvals, dwi_bvecs: 18 columns
- + bold_naming40, bold_rest (replaces bold): 19 columns (net +1)

```python
Features({
    # Identifiers
    "subject_id": Value("string"),
    "session_id": Value("string"),

    # Structural MRI (single file per session)
    "t1w": Nifti(),
    "t2w": Nifti(),
    "t2w_acquisition": Value("string"),
    "flair": Nifti(),

    # Functional MRI (multiple runs, SPLIT BY TASK)
    "bold_naming40": Sequence(Nifti()),  # CHANGED from "bold"
    "bold_rest": Sequence(Nifti()),       # NEW

    # Diffusion MRI (multiple runs, WITH GRADIENTS)
    "dwi": Sequence(Nifti()),
    "dwi_bvals": Sequence(Value("string")),  # NEW
    "dwi_bvecs": Sequence(Value("string")),  # NEW
    "sbref": Sequence(Nifti()),

    # Derivatives
    "lesion": Nifti(),

    # Demographics
    "age_at_stroke": Value("float32"),
    "sex": Value("string"),
    "race": Value("string"),  # NEW

    # Clinical
    "wab_aq": Value("float32"),
    "wab_days": Value("float32"),  # NEW
    "wab_type": Value("string"),
})
```

---

## Breaking Changes

| Change | Downstream Impact | Mitigation |
|--------|-------------------|------------|
| `bold` → `bold_naming40` + `bold_rest` | Code using `ds["bold"]` will break | Document in changelog, version bump |
| New columns added | Non-breaking | N/A |

### Migration Guide for Downstream Users

**Before:**
```python
bold_runs = row["bold"]  # All tasks mixed
```

**After:**
```python
# Option 1: Get specific task
naming_runs = row["bold_naming40"]
rest_runs = row["bold_rest"]

# Option 2: Combine if needed
all_bold = row["bold_naming40"] + row["bold_rest"]
```

---

## Verification Commands

```bash
# Run all ARC tests
uv run pytest tests/test_arc.py -v

# Type check
uv run mypy src/bids_hub/datasets/arc.py tests/test_arc.py

# Lint
uv run ruff check src/bids_hub/datasets/arc.py tests/test_arc.py

# Dry-run build (against real data)
uv run bids-hub arc build /path/to/ds004884 --dry-run
```

---

## Post-Implementation Checklist

- [ ] All tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Dry-run build succeeds against local OpenNeuro data
- [ ] Update `ARC_METADATA_PARITY_AUDIT.md` to mark items complete
- [ ] Update `CLAUDE.md` with new schema
- [ ] Update HuggingFace dataset card with new columns
- [ ] Rebuild and push to HuggingFace Hub
- [ ] Verify new columns appear in HuggingFace dataset viewer

---

## References

- [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884)
- [BIDS Specification - DWI](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/magnetic-resonance-imaging-data.html#diffusion-imaging-data)
- [BIDS Specification - Task Entity](https://bids-specification.readthedocs.io/en/stable/appendices/entities.html#task)
- [ARC_METADATA_PARITY_AUDIT.md](/ARC_METADATA_PARITY_AUDIT.md)

---

## Changelog

- **2025-12-13 (v2):** Fixed inaccuracies based on senior review
  - Fixed column count: 19 (was incorrectly stated as 18)
  - Fixed race values: only `b` and `w` exist (removed "etc.")
  - Fixed wab_days range: 42-8798 (was incorrectly stated as ~800-8800)
  - Added participant vs subject count clarification (244 in TSV, 230 with directories)
  - Fixed test fixture instructions to match existing DWI naming (`_run-01_dwi.nii.gz`)
  - Added dwi/dwi_bvals/dwi_bvecs alignment invariant

- **2025-12-13 (v1):** Initial spec created based on audit findings
  - Covers P0: DWI gradients, BOLD task separation
  - Covers P1: race, wab_days columns

---

**Reviewed by:** _Pending final approval_
