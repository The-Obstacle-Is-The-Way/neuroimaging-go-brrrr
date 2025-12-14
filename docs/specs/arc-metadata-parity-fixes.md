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

**Location (audit environment):** `/Users/ray/Desktop/CLARITY-DIGITAL-TWIN/bids-hub/data/openneuro/ds004884`  
**Note:** Use your local `ds004884` path when reproducing these checks.

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
participants.tsv data rows:         245 (plus 1 header row; file has no trailing newline)
Actual sub-* directories:     230
Subjects in TSV but no dir:   15 (sub-M2019, sub-M2085, sub-M2130, etc.)
Subjects with NaN race:       2 (sub-M2001, sub-M2003) - both have directories
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

**Note:** `sub-M2231` is one of the 15 `participants.tsv` IDs with no `sub-*` directory, so it will not appear in the built HF dataset (which is derived from `sub-*/ses-*` folders).

**Column descriptions:**
- `race`: Self-reported race.
  - All `participants.tsv` rows: `b` (Black, n=52), `w` (White, n=191), NaN (n=2). No other values exist.
  - Subjects with directories (included in built dataset): `b` (n=47), `w` (n=181), NaN (n=2).
- `wab_days`: Days since stroke when WAB assessment was collected.
  - All `participants.tsv` rows: 42 to 8798 days.
  - Subjects with directories (included in built dataset): 42 to 7998 days.

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
def _read_gradient_file(nifti_path: str, extension: str) -> str:
    """Read bval or bvec file content for a DWI NIfTI.

    DWI files in BIDS have companion gradient files with the same base name:
    - sub-X_ses-Y_dwi.nii.gz
    - sub-X_ses-Y_dwi.bval  (b-values)
    - sub-X_ses-Y_dwi.bvec  (gradient directions)

    Args:
        nifti_path: Absolute path to DWI NIfTI file
        extension: Either ".bval" or ".bvec"

    Returns:
        File content as string (whitespace-stripped).

    Raises:
        FileNotFoundError: If the gradient file does not exist.

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
        # WARNING not DEBUG: ARC has verified 1:1:1 match for all 2089 DWI files.
        # Missing gradient indicates data corruption, not expected absence.
        logger.warning("Gradient file not found (data corruption?): %s", gradient_path)
        raise FileNotFoundError(f"Missing gradient file: {gradient_path}")

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
- This allows: `for nifti, bval, bvec in zip(row["dwi"], row["dwi_bvals"], row["dwi_bvecs"])`

**Type annotation:** `dwi_bvals: list[str]` and `dwi_bvecs: list[str]`

**Note:** In OpenNeuro ds004884, ALL 2089 DWI files have matching bval/bvec (verified 1:1:1 match).
Fail fast on missing gradients to prevent pushing unusable DWI data.

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

    def test_raises_when_missing(self, tmp_path: Path) -> None:
        nifti = tmp_path / "sub-M2001_ses-1_dwi.nii.gz"
        nifti.touch()
        # No .bval file created -> should raise

        from bids_hub.datasets.arc import _read_gradient_file
        with pytest.raises(FileNotFoundError):
            _read_gradient_file(str(nifti), ".bval")

    def test_logs_warning_when_missing(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Missing gradient file should log WARNING (not debug) for ARC."""
        nifti = tmp_path / "sub-M2001_ses-1_dwi.nii.gz"
        nifti.touch()
        # No .bval file created

        from bids_hub.datasets.arc import _read_gradient_file
        with caplog.at_level(logging.WARNING), pytest.raises(FileNotFoundError):
            _read_gradient_file(str(nifti), ".bval")

        # Verify warning was logged (not debug)
        assert any("Gradient file not found" in record.message for record in caplog.records)
        assert all(record.levelno >= logging.WARNING for record in caplog.records if "Gradient" in record.message)
```

---

### Change 2: Split BOLD by Task (P0 - BLOCKING)

#### Design Decision: Split Columns vs Aligned Metadata

**Option A (Chosen): Split into separate columns**
```python
"bold_naming40": Sequence(Nifti()),
"bold_rest": Sequence(Nifti()),
```
- Pro: Simple to query by task type
- Pro: Type-safe (each column is well-defined)
- Con: Breaking change (removes `bold`)
- Con: Hard-codes current task set

**Option B (Alternative): Keep bold + add aligned metadata**
```python
"bold": Sequence(Nifti()),
"bold_task": Sequence(Value("string")),  # ["naming40", "rest", "rest", ...]
```
- Pro: Non-breaking (bold still works)
- Pro: Generalizes to any future tasks
- Con: Requires `zip(bold, bold_task)` to pair up

**Decision:** Option A is acceptable for ARC because:
1. ARC is a closed dataset (no new tasks will be added)
2. Breaking change is documented in migration guide
3. Simpler UX for downstream users (no zip needed)

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
bold_naming40 = [p for p in bold_all if "task-naming40" in p.lower()]
bold_rest = [p for p in bold_all if "task-rest" in p.lower()]

# GUARDRAIL: Detect unexpected tasks to prevent silent data loss
# ARC only has naming40 and rest tasks - any other task is a bug
unexpected = [p for p in bold_all if "task-naming40" not in p.lower() and "task-rest" not in p.lower()]
if unexpected:
    raise ValueError(
        f"Unexpected BOLD task(s) (not naming40/rest) for {subject_id}/{session_id}: "
        f"{[Path(p).name for p in unexpected[:3]]} (showing up to 3)"
    )
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


def test_bold_unexpected_task_raises(
    self, synthetic_bids_root: Path
) -> None:
    """Unexpected BOLD task types should fail fast (prevent silent data loss)."""
    # Create a BOLD file with unexpected task
    func_dir = synthetic_bids_root / "sub-M2001" / "ses-1" / "func"
    unexpected_bold = func_dir / "sub-M2001_ses-1_task-unknown_run-01_bold.nii.gz"
    _create_minimal_nifti(unexpected_bold)

    with pytest.raises(ValueError, match=r"Unexpected BOLD task"):
        build_arc_file_table(synthetic_bids_root)
```

---

### Required Test Suite Updates (TDD)

This spec changes the ARC schema (new columns + `bold` rename), so update the existing test suite accordingly:

1. Update `TestBuildArcFileTable.test_build_file_table_has_correct_columns` expected columns:
   - Remove: `bold`
   - Add: `bold_naming40`, `bold_rest`, `dwi_bvals`, `dwi_bvecs`, `race`, `wab_days`

2. Update any assertions that reference `ses["bold"]` to use `ses["bold_naming40"]` and `ses["bold_rest"]`.

3. Add an integration assertion for DWI gradients on the synthetic fixture:
   - `len(row["dwi"]) == len(row["dwi_bvals"]) == len(row["dwi_bvecs"])`
   - Verify at least one known `.bval` and `.bvec` content string matches the fixture text.

4. Add assertions for the new demographic/clinical columns:
   - `race` should be a `str | None` (preferably set one fixture row to `NaN` to validate `None` output).
   - `wab_days` should be a `float | None`.

5. Update `TestGetArcFeatures`:
   - Replace `"bold": Sequence(Nifti())` checks with `bold_naming40` and `bold_rest`.
   - Add checks for `dwi_bvals`/`dwi_bvecs` as `Sequence(Value("string"))`, and `race`/`wab_days` as `Value(...)`.

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

## Documentation Updates Required

The ARC schema changes in this spec (BOLD task split + new columns) affect these files:

| File | Current | Required Update |
|------|---------|-----------------|
| `docs/reference/schema.md:24` | ARC schema lists `"bold": Sequence(Nifti())` and lacks new columns | Update ARC schema to 19 columns (replace `bold`, add `dwi_bvals`, `dwi_bvecs`, `race`, `wab_days`) |
| `docs/reference/api.md:138` | ARC API docs list `bold` and 14 total columns | Update column list + count (14 → 19) and reflect `bold_naming40`/`bold_rest` + new columns |
| `docs/how-to/validate-before-upload.md:34` | `multi_run_cols = ["bold", "dwi", "sbref"]` | Replace `bold` with `bold_naming40`, `bold_rest` (and update example outputs accordingly) |
| `docs/explanation/architecture.md:82` | `- bold: Multiple fMRI runs per session` | Update to `bold_naming40`/`bold_rest` (and mention DWI gradients if described) |
| `CLAUDE.md` (ARC schema section) | Uses `bold` and lacks new columns | Update ARC schema to match the new 19-column SSOT |

**Not affected (other datasets):**
- `docs/issues/003a_aomic_piop1.md` - AOMIC dataset, not ARC
- `docs/issues/003b_aomic_id1000.md` - AOMIC dataset, not ARC

---

## Separate Issue: Validation Expected Counts

**IMPORTANT:** This spec does NOT fix validation, but documents the current SSOT mismatch so the "validate then upload" workflow is not misleading.

### What fails today (first-principles, pinned OpenNeuro data)

Running `uv run bids-hub arc validate <ds004884>` against the SSOT dataset currently fails on:

| Check | Expected (src/bids_hub/validation/arc.py) | Actual (SSOT) | Root Cause |
|------:|------------------------------------------:|--------------:|-----------|
| `t2w_count` | 447 | 440 | Expected counts are not aligned with the validator’s session-counting semantics |
| `flair_count` | 235 | 233 | Same as above (session-counting vs expected values) |
| `lesion_count` | 230 | 0 | Lesion masks live under `derivatives/`, but validation only scans `sub-*/ses-*` |

Separately, the SSOT dataset contains **228** lesion mask NIfTIs in `derivatives/lesion_masks`, not 230:
`find derivatives/lesion_masks -name '*_desc-lesion_mask.nii.gz' | wc -l  # 228`

**Impact:** `uv run bids-hub arc validate` currently fails on valid SSOT data, and `docs/tutorials/upload-arc.md` is misleading until validation is fixed.

**Recommendation (separate PR):**
- Update validation to count lesion masks in `derivatives/lesion_masks/...` (not under raw `sub-*/ses-*`)
- Align expected counts with the validator’s counting semantics (sessions vs raw file counts)
- Update the ARC upload tutorial to match the corrected validator behavior

Do NOT block metadata parity on the validation fix.

---

## Post-Implementation Checklist

- [ ] All tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] Dry-run build succeeds against local OpenNeuro data
- [ ] Update documentation files listed above
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

- **2025-12-14 (v5):** Make guardrails non-lossy + fix validation facts
  - Made BOLD task guardrail fail-fast (no silent dropping of unknown tasks)
  - Made missing DWI gradients fail-fast (DWI unusable without bval/bvec; SSOT is 1:1:1)
  - Corrected validation section to match actual SSOT validator output and root causes

- **2025-12-13 (v4):** Addressed spec completeness gaps
  - Added BOLD task guardrail to detect unexpected tasks
  - Changed gradient missing log level: `debug` → `warning`
  - Added "Documentation Updates Required" section enumerating all files affected by bold split
  - Added "Separate Issue: Validation Expected Counts" documenting lesion 230→228 discrepancy
  - Updated post-implementation checklist to include doc updates

- **2025-12-13 (v3):** Final corrections based on second senior review
  - Fixed participants.tsv count: 245 rows (was incorrectly 244)
  - Added NaN race subjects: sub-M2001, sub-M2003
  - Added BOLD schema design decision section (Option A vs B)
  - Added dwi_bvals/dwi_bvecs type annotation: `list[str | None]`
  - Noted 1:1:1 bval/bvec match in ds004884 (None handling is defensive)

- **2025-12-13 (v2):** Fixed inaccuracies based on senior review
  - Fixed column count: 19 (was incorrectly stated as 18)
  - Fixed race values: only `b` and `w` exist (removed "etc.")
  - Fixed wab_days range: 42-8798 (was incorrectly stated as ~800-8800)
  - Added participant vs subject count clarification (245 in TSV, 230 with directories)
  - Fixed test fixture instructions to match existing DWI naming (`_run-01_dwi.nii.gz`)
  - Added dwi/dwi_bvals/dwi_bvecs alignment invariant

- **2025-12-13 (v1):** Initial spec created based on audit findings
  - Covers P0: DWI gradients, BOLD task separation
  - Covers P1: race, wab_days columns

---

**Reviewed by:** _v5 - Guardrails + validation facts corrected. Ready for implementation._
