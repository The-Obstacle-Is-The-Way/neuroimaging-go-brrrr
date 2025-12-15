# Spec: Add T2w Acquisition Type Metadata to ARC Dataset Schema

**Status:** Ready for Implementation
**Priority:** High
**Upstream Dataset:** [OpenNeuro ds004884](https://openneuro.org/datasets/ds004884) (commit `0885e5939abc8f909a175dd782369b7afc3fdd08`)
**HuggingFace Target:** [hugging-science/arc-aphasia-bids](https://huggingface.co/datasets/hugging-science/arc-aphasia-bids)
**Last Audit:** 2025-12-13

---

## Problem Statement

The ARC dataset uploaded to HuggingFace is missing the `t2w_acquisition` field. This BIDS metadata exists in OpenNeuro filenames but is not extracted during the upload pipeline.

**Impact:** Downstream consumers cannot filter samples by acquisition type (SPACE vs TSE), which is **required** to replicate the [MeshNet stroke lesion segmentation paper](https://arxiv.org/abs/2503.05531).

---

## Verified Facts

### Source Data (OpenNeuro ds004884, commit `0885e5939abc8f909a175dd782369b7afc3fdd08`)

**CRITICAL DISTINCTION:** T2w files and lesion masks have different counts.

#### All T2w Files (441 total)

| Acquisition Code | T2w Files | Distribution |
|------------------|-----------|--------------|
| `acq-spc3p2`     | 284       | 64.4%        |
| `acq-spc3`       | 151       | 34.2%        |
| `acq-tse3`       | 6         | 1.4%         |
| **Total**        | **441**   |              |

#### Lesion Masks Only (228 total) - THIS IS WHAT MATTERS FOR TRAINING

| Acquisition Code | Meaning               | Mask Count | Paper Used |
|------------------|-----------------------|------------|------------|
| `acq-spc3p2`     | SPACE 2x acceleration | 115        | 115        |
| `acq-spc3`       | SPACE no acceleration | 108        | 109*       |
| `acq-tse3`       | Turbo Spin Echo       | 5          | 0 (excluded) |
| **Total**        |                       | **228**    | **224**    |

\* The paper reports 109 SPACE no-accel, but only 108 have public lesion masks. `sub-M2039/ses-1222` has a SPACE T2w but no lesion mask in OpenNeuro (likely internal to the research team).

#### Real Filename Examples (Verified in Commit)

**T2w files:**
- `sub-M2005/ses-4334/anat/sub-M2005_ses-4334_acq-spc3p2_run-7_T2w.nii.gz`
- `sub-M2001/ses-1253/anat/sub-M2001_ses-1253_acq-spc3_run-3_T2w.nii.gz`
- `sub-M2002/ses-1441/anat/sub-M2002_ses-1441_acq-tse3_run-4_T2w.nii.gz`

**Lesion masks:**
- `derivatives/lesion_masks/sub-M2117/ses-505/anat/sub-M2117_ses-505_acq-spc3p2_run-8_T2w_desc-lesion_mask.nii.gz`
- `derivatives/lesion_masks/sub-M2001/ses-1253/anat/sub-M2001_ses-1253_acq-spc3_run-3_T2w_desc-lesion_mask.nii.gz`
- `derivatives/lesion_masks/sub-M2002/ses-1441/anat/sub-M2002_ses-1441_acq-tse3_run-4_T2w_desc-lesion_mask.nii.gz`

#### Multi-Run Sessions (Fixed in v4)

Some sessions have multiple T2w files (e.g., `sub-M2105/ses-964` has 2). As of v4, structural modalities use `Sequence(Nifti())` so all files are preserved. The `t2w_acquisition` is derived from the first file (all runs in a session use the same sequence).

See `docs/specs/arc-structural-multi-run-fix.md` for full multi-run schema specification.

---

### Current Pipeline Gap

| File | Line | Current Behavior | Missing |
|------|------|------------------|---------|
| `arc.py` | 146 | Finds T2w path only | Acquisition extraction |
| `arc.py` | 163-178 | Row dict built | `t2w_acquisition` field |
| `arc.py` | 226-246 | Features schema | `t2w_acquisition: Value("string")` |
| `test_arc.py` | 87,113 | Test fixtures | Filenames with `acq-*` entity |
| `test_arc.py` | 164-178 | Column assertions | `t2w_acquisition` in expected set |

---

## Implementation

### Step 1: Add `_extract_acquisition_type()` Helper

**File:** `src/bids_hub/datasets/arc.py`
**Location:** After imports (around line 37)

```python
import re

# ARC acquisition type mapping (exact match, not substring)
_ARC_ACQUISITION_MAP: dict[str, str] = {
    "spc3p2": "space_2x",        # SPACE with 2x acceleration
    "spc3": "space_no_accel",    # SPACE without acceleration
    "tse3": "turbo_spin_echo",   # Turbo Spin Echo
}


def _extract_acquisition_type(filepath: str | None) -> str | None:
    """
    Extract acquisition type from BIDS filename.

    BIDS filenames contain acq-<label> entity that indicates the acquisition type.
    For ARC T2w images, we map known codes to human-readable names.

    Args:
        filepath: Path to NIfTI file (may be None)

    Returns:
        - Known code: mapped name (e.g., "spc3p2" -> "space_2x")
        - Unknown code: raw label (forward compatible)
        - No acq-* entity or None input: None
    """
    if filepath is None:
        return None

    match = re.search(r'acq-([a-z0-9]+)', str(filepath).lower())
    if not match:
        return None

    acq_label = match.group(1)

    # Use exact match mapping (not substring) to avoid mismapping
    # e.g., "spc3foo" should return "spc3foo", not "space_no_accel"
    return _ARC_ACQUISITION_MAP.get(acq_label, acq_label)
```

**Key change from original spec:** Using `dict.get()` for exact match instead of substring `in` checks. This prevents `acq-spc3foo` from incorrectly mapping to `space_no_accel`.

---

### Step 2: Update `build_arc_file_table()`

**File:** `src/bids_hub/datasets/arc.py`
**Location:** After line 146, add acquisition extraction:

```python
# Line 146 (existing):
t2w_path = find_single_nifti(session_dir / "anat", "*_T2w.nii.gz")

# ADD after line 146:
t2w_acquisition = _extract_acquisition_type(t2w_path)
```

**Location:** Update `rows.append()` dict (lines 163-178):

```python
rows.append(
    {
        "subject_id": subject_id,
        "session_id": session_id,
        "t1w": t1w_path,
        "t2w": t2w_path,
        "t2w_acquisition": t2w_acquisition,  # ADD THIS LINE
        "flair": flair_path,
        "bold": bold_paths,
        "dwi": dwi_paths,
        "sbref": sbref_paths,
        "lesion": lesion_path,
        "age_at_stroke": age_at_stroke,
        "sex": sex,
        "wab_aq": wab_aq,
        "wab_type": wab_type,
    }
)
```

---

### Step 3: Update `get_arc_features()`

**File:** `src/bids_hub/datasets/arc.py`
**Location:** In Features dict (after line 232)

```python
def get_arc_features() -> Features:
    return Features(
        {
            "subject_id": Value("string"),
            "session_id": Value("string"),
            "t1w": Nifti(),
            "t2w": Nifti(),
            "t2w_acquisition": Value("string"),  # ADD THIS LINE
            "flair": Nifti(),
            "bold": Sequence(Nifti()),
            "dwi": Sequence(Nifti()),
            "sbref": Sequence(Nifti()),
            "lesion": Nifti(),
            "age_at_stroke": Value("float32"),
            "sex": Value("string"),
            "wab_aq": Value("float32"),
            "wab_type": Value("string"),
        }
    )
```

---

### Step 4: Update Test Fixture

**File:** `tests/test_arc.py`
**Location:** `synthetic_bids_root` fixture

Update T2w filenames to include `acq-*` entity:

```python
# Line 87 (change from):
_create_minimal_nifti(root / "sub-M2001" / "ses-1" / "anat" / "sub-M2001_ses-1_T2w.nii.gz")

# (change to):
_create_minimal_nifti(
    root / "sub-M2001" / "ses-1" / "anat" / "sub-M2001_ses-1_acq-spc3p2_T2w.nii.gz"
)

# Line 113 (change from):
_create_minimal_nifti(root / "sub-M2001" / "ses-2" / "anat" / "sub-M2001_ses-2_T2w.nii.gz")

# (change to):
_create_minimal_nifti(
    root / "sub-M2001" / "ses-2" / "anat" / "sub-M2001_ses-2_acq-tse3_T2w.nii.gz"
)
```

---

### Step 5: Add New Tests

**File:** `tests/test_arc.py`

```python
class TestExtractAcquisitionType:
    """Tests for _extract_acquisition_type helper function."""

    def test_space_2x(self) -> None:
        """Test extraction of SPACE 2x acceleration."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type(
            "/data/sub-M2005_ses-4334_acq-spc3p2_run-7_T2w.nii.gz"
        )
        assert result == "space_2x"

    def test_space_no_accel(self) -> None:
        """Test extraction of SPACE no acceleration."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type(
            "/data/sub-M2001_ses-1253_acq-spc3_run-3_T2w.nii.gz"
        )
        assert result == "space_no_accel"

    def test_turbo_spin_echo(self) -> None:
        """Test extraction of Turbo Spin Echo."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type(
            "/data/sub-M2002_ses-1441_acq-tse3_run-4_T2w.nii.gz"
        )
        assert result == "turbo_spin_echo"

    def test_no_acq_entity_returns_none(self) -> None:
        """Test that filenames without acq-* return None."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type("/data/sub-M2001_ses-1_T2w.nii.gz")
        assert result is None

    def test_none_input_returns_none(self) -> None:
        """Test that None input returns None."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        assert _extract_acquisition_type(None) is None

    def test_unknown_code_returns_raw_label(self) -> None:
        """Test that unknown codes return the raw label (forward compat)."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type(
            "/data/sub-M2001_ses-1_acq-newseq_T2w.nii.gz"
        )
        assert result == "newseq"

    def test_exact_match_not_substring(self) -> None:
        """Test that mapping uses exact match, not substring.

        Critical: 'spc3foo' should NOT map to 'space_no_accel'.
        It should return 'spc3foo' (raw label).
        """
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type(
            "/data/sub-M2001_ses-1_acq-spc3foo_T2w.nii.gz"
        )
        assert result == "spc3foo"  # NOT "space_no_accel"

    def test_case_insensitive(self) -> None:
        """Test that extraction is case-insensitive."""
        from bids_hub.datasets.arc import _extract_acquisition_type

        result = _extract_acquisition_type(
            "/DATA/SUB-M2001_SES-1_ACQ-SPC3P2_T2W.NII.GZ"
        )
        assert result == "space_2x"


class TestBuildArcFileTableAcquisition:
    """Tests for t2w_acquisition column in file table."""

    def test_acquisition_column_exists(self, synthetic_bids_root: Path) -> None:
        """Verify t2w_acquisition column is present."""
        df = build_arc_file_table(synthetic_bids_root)
        assert "t2w_acquisition" in df.columns

    def test_acquisition_populated_correctly(self, synthetic_bids_root: Path) -> None:
        """Verify acquisition values are correctly populated."""
        df = build_arc_file_table(synthetic_bids_root)

        # sub-M2001 ses-1 should have space_2x (acq-spc3p2)
        ses1 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-1")].iloc[0]
        assert ses1["t2w_acquisition"] == "space_2x"

        # sub-M2001 ses-2 should have turbo_spin_echo (acq-tse3)
        ses2 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-2")].iloc[0]
        assert ses2["t2w_acquisition"] == "turbo_spin_echo"

    def test_acquisition_none_when_no_t2w(self, synthetic_bids_root: Path) -> None:
        """Verify acquisition is None when T2w is missing."""
        df = build_arc_file_table(synthetic_bids_root)

        # sub-M2002 ses-1 has no T2w
        sub2 = df[(df["subject_id"] == "sub-M2002") & (df["session_id"] == "ses-1")].iloc[0]
        assert sub2["t2w_acquisition"] is None


class TestGetArcFeaturesAcquisition:
    """Tests for t2w_acquisition in Features schema."""

    def test_acquisition_in_schema(self) -> None:
        """Verify t2w_acquisition is in the Features schema."""
        from datasets import Value

        features = get_arc_features()

        assert "t2w_acquisition" in features
        assert isinstance(features["t2w_acquisition"], Value)
```

---

### Step 6: Update Existing Test

**File:** `tests/test_arc.py`

Update `test_build_file_table_has_correct_columns` expected columns:

```python
def test_build_file_table_has_correct_columns(self, synthetic_bids_root: Path) -> None:
    """Test that the DataFrame has all expected columns."""
    df = build_arc_file_table(synthetic_bids_root)
    expected_columns = {
        "subject_id",
        "session_id",
        "t1w",
        "t2w",
        "t2w_acquisition",  # ADD THIS
        "flair",
        "bold",
        "dwi",
        "sbref",
        "lesion",
        "age_at_stroke",
        "sex",
        "wab_aq",
        "wab_type",
    }
    assert set(df.columns) == expected_columns
```

---

## Verification Commands

```bash
# Run all ARC tests
uv run pytest tests/test_arc.py -v

# Run specific acquisition tests
uv run pytest tests/test_arc.py -k "acquisition" -v

# Type check
uv run mypy src/bids_hub/datasets/arc.py

# Lint
uv run ruff check src/bids_hub/datasets/arc.py

# Full validation (dry run against real data)
uv run bids-hub arc build /path/to/ds004884 --dry-run
```

---

## Expected Outcome After Re-upload

**Important:** The HuggingFace dataset has 902 rows (one per session), not 228 rows. Filtering requires multiple conditions.

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/arc-aphasia-bids")

# HF dataset structure: 902 sessions total
print(len(ds["train"]))  # 902

# To get paper-replication subset (lesion + T2w + SPACE only):
paper_subset = ds["train"].filter(
    lambda x: (
        x["lesion"] is not None
        and len(x["t2w"]) > 0  # v4: t2w is now a list
        and x["t2w_acquisition"] in ("space_2x", "space_no_accel")
    )
)
# Returns 223 samples (115 space_2x + 108 space_no_accel with masks)
# Paper reports 224, but sub-M2039 mask is not in public dataset

# Check distribution of samples WITH lesion masks
lesion_subset = ds["train"].filter(lambda x: x["lesion"] is not None)
df = lesion_subset.to_pandas()
print(df["t2w_acquisition"].value_counts())
# Expected:
# space_2x           115
# space_no_accel     108
# turbo_spin_echo      5
```

---

## Documentation Updates Required

After implementation, update these files:

1. **`CLAUDE.md`** - Add `t2w_acquisition` to ARC Schema section
2. **HuggingFace dataset card** - Document new field and filtering examples
3. **`src/bids_hub/datasets/arc.py`** docstrings - Add field to docstrings

---

## References

- [OpenNeuro ds004884](https://github.com/OpenNeuroDatasets/ds004884) (commit `0885e5939abc8f909a175dd782369b7afc3fdd08`)
- [MeshNet paper](https://arxiv.org/abs/2503.05531) (Section 2: Dataset)
- [BIDS Specification - Acquisition Entity](https://bids-specification.readthedocs.io/en/stable/appendices/entities.html#acq)
- [HuggingFace Dataset](https://huggingface.co/datasets/hugging-science/arc-aphasia-bids)

---

## Changelog

- **2025-12-13 (v2):** Major revision based on external audit
  - Fixed example filenames to match real data in commit
  - Changed mapping logic from substring to exact match
  - Clarified lesion-mask vs all-T2w count distinction
  - Fixed downstream filtering snippet for real dataset shape (902 sessions)
  - Added `test_exact_match_not_substring` test case
  - Documented multi-T2w edge case (sub-M2105/ses-964)
  - Reconciled paper's 224 vs public dataset's 223 SPACE samples

- **2025-12-12 (v1):** Initial spec
