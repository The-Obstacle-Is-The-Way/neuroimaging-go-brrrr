"""
Tests for ARC (Aphasia Recovery Cohort) dataset module.

These tests use synthetic BIDS structures to verify the ARC file-table builder
and HF Dataset conversion work correctly.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest

from bids_hub import (
    build_and_push_arc,
    build_arc_file_table,
    get_arc_features,
)
from bids_hub.core import DatasetBuilderConfig
from bids_hub.datasets.arc import _extract_acquisition_type


def _create_minimal_nifti(path: Path) -> None:
    """Create a minimal valid NIfTI file at the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.ones((2, 2, 2), dtype=np.float32)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, path)


@pytest.fixture
def synthetic_bids_root() -> Generator[Path, None, None]:
    """Create a synthetic BIDS dataset for testing.

    Structure (multi-session, ALL modalities):
        ds004884/
        ├── participants.tsv
        ├── sub-M2001/
        │   ├── ses-1/
        │   │   ├── anat/
        │   │   │   ├── sub-M2001_ses-1_T1w.nii.gz
        │   │   │   ├── sub-M2001_ses-1_acq-spc3p2_T2w.nii.gz
        │   │   │   └── sub-M2001_ses-1_FLAIR.nii.gz
        │   │   ├── func/
        │   │   │   └── sub-M2001_ses-1_task-rest_bold.nii.gz
        │   │   └── dwi/
        │   │       ├── sub-M2001_ses-1_dwi.nii.gz
        │   │       └── sub-M2001_ses-1_sbref.nii.gz
        │   └── ses-2/
        │       └── anat/
        │           ├── sub-M2001_ses-2_T1w.nii.gz
        │           └── sub-M2001_ses-2_acq-tse3_T2w.nii.gz  (no FLAIR, no func, no dwi)
        ├── sub-M2002/
        │   └── ses-1/
        │       └── anat/
        │           └── sub-M2002_ses-1_T1w.nii.gz  (minimal - only T1w)
        └── derivatives/
            └── lesion_masks/
                ├── sub-M2001/
                │   ├── ses-1/...
                │   └── ses-2/...
                └── sub-M2002/
                    └── ses-1/...
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "ds004884"
        root.mkdir()

        # Create participants.tsv
        participants = pd.DataFrame(
            {
                "participant_id": ["sub-M2001", "sub-M2002", "sub-M2003"],
                "sex": ["F", "M", "F"],
                "age_at_stroke": [38.0, 55.0, 42.0],
                "race": [None, "w", "b"],  # sub-M2001 has missing race
                "wab_days": [895, 3682, 1500],
                "wab_aq": [87.1, 72.6, None],  # sub-M2003 has missing wab_aq
                "wab_type": ["Anomic", "Broca", "n/a"],
            }
        )
        participants.to_csv(root / "participants.tsv", sep="\t", index=False)

        # sub-M2001 ses-1: FULL modalities (anat + func + dwi) with MULTIPLE RUNS
        _create_minimal_nifti(root / "sub-M2001" / "ses-1" / "anat" / "sub-M2001_ses-1_T1w.nii.gz")
        _create_minimal_nifti(
            root / "sub-M2001" / "ses-1" / "anat" / "sub-M2001_ses-1_acq-spc3p2_T2w.nii.gz"
        )
        _create_minimal_nifti(
            root / "sub-M2001" / "ses-1" / "anat" / "sub-M2001_ses-1_FLAIR.nii.gz"
        )
        # Multiple BOLD runs (testing multi-run support)
        # Task split testing: 2 rest, 1 naming40
        _create_minimal_nifti(
            root / "sub-M2001" / "ses-1" / "func" / "sub-M2001_ses-1_task-rest_run-01_bold.nii.gz"
        )
        _create_minimal_nifti(
            root / "sub-M2001" / "ses-1" / "func" / "sub-M2001_ses-1_task-rest_run-02_bold.nii.gz"
        )
        _create_minimal_nifti(
            root
            / "sub-M2001"
            / "ses-1"
            / "func"
            / "sub-M2001_ses-1_task-naming40_run-01_bold.nii.gz"
        )

        # Multiple DWI runs WITH GRADIENTS
        dwi_dir = root / "sub-M2001" / "ses-1" / "dwi"
        _create_minimal_nifti(dwi_dir / "sub-M2001_ses-1_run-01_dwi.nii.gz")
        (dwi_dir / "sub-M2001_ses-1_run-01_dwi.bval").write_text("0 1000 2000")
        (dwi_dir / "sub-M2001_ses-1_run-01_dwi.bvec").write_text("1 0 0\n0 1 0\n0 0 1")

        _create_minimal_nifti(dwi_dir / "sub-M2001_ses-1_run-02_dwi.nii.gz")
        (dwi_dir / "sub-M2001_ses-1_run-02_dwi.bval").write_text("0 1000")
        (dwi_dir / "sub-M2001_ses-1_run-02_dwi.bvec").write_text("1 0\n0 1\n0 0")

        _create_minimal_nifti(dwi_dir / "sub-M2001_ses-1_run-03_dwi.nii.gz")
        (dwi_dir / "sub-M2001_ses-1_run-03_dwi.bval").write_text("0 500 1000 1500")
        (dwi_dir / "sub-M2001_ses-1_run-03_dwi.bvec").write_text("1 0 0 0\n0 1 0 0\n0 0 1 0")

        # Single sbref
        _create_minimal_nifti(root / "sub-M2001" / "ses-1" / "dwi" / "sub-M2001_ses-1_sbref.nii.gz")

        # sub-M2001 ses-2: has T1w and T2w only (no FLAIR, no func, no dwi)
        _create_minimal_nifti(root / "sub-M2001" / "ses-2" / "anat" / "sub-M2001_ses-2_T1w.nii.gz")
        _create_minimal_nifti(
            root / "sub-M2001" / "ses-2" / "anat" / "sub-M2001_ses-2_acq-tse3_T2w.nii.gz"
        )

        # sub-M2002 ses-1: has T1w only (minimal)
        _create_minimal_nifti(root / "sub-M2002" / "ses-1" / "anat" / "sub-M2002_ses-1_T1w.nii.gz")

        # sub-M2003: no imaging data at all (only in participants.tsv)

        # Create derivatives/lesion_masks
        _create_minimal_nifti(
            root
            / "derivatives"
            / "lesion_masks"
            / "sub-M2001"
            / "ses-1"
            / "anat"
            / "sub-M2001_ses-1_desc-lesion_mask.nii.gz"
        )
        _create_minimal_nifti(
            root
            / "derivatives"
            / "lesion_masks"
            / "sub-M2001"
            / "ses-2"
            / "anat"
            / "sub-M2001_ses-2_desc-lesion_mask.nii.gz"
        )
        _create_minimal_nifti(
            root
            / "derivatives"
            / "lesion_masks"
            / "sub-M2002"
            / "ses-1"
            / "anat"
            / "sub-M2002_ses-1_desc-lesion_mask.nii.gz"
        )
        # sub-M2003: no lesion mask

        yield root


class TestBuildArcFileTable:
    """Tests for build_arc_file_table function."""

    def test_build_file_table_returns_dataframe(self, synthetic_bids_root: Path) -> None:
        """Test that build_arc_file_table returns a DataFrame."""
        df = build_arc_file_table(synthetic_bids_root)
        assert isinstance(df, pd.DataFrame)

    def test_build_file_table_has_correct_columns(self, synthetic_bids_root: Path) -> None:
        """Test that the DataFrame has all expected columns (FULL dataset)."""
        df = build_arc_file_table(synthetic_bids_root)
        expected_columns = {
            "subject_id",
            "session_id",
            "t1w",
            "t2w",
            "t2w_acquisition",
            "flair",
            "bold_naming40",
            "bold_rest",
            "dwi",
            "dwi_bvals",
            "dwi_bvecs",
            "sbref",
            "lesion",
            "age_at_stroke",
            "sex",
            "race",
            "wab_aq",
            "wab_days",
            "wab_type",
        }
        assert set(df.columns) == expected_columns

    def test_build_file_table_has_correct_row_count(self, synthetic_bids_root: Path) -> None:
        """Test that DataFrame has one row per SESSION (not per subject)."""
        df = build_arc_file_table(synthetic_bids_root)
        # sub-M2001 has 2 sessions, sub-M2002 has 1 session, sub-M2003 has 0 sessions
        assert len(df) == 3  # 3 sessions total (not 3 subjects)

    def test_build_file_table_session_with_all_modalities(self, synthetic_bids_root: Path) -> None:
        """Test that session with all modalities has all paths populated."""
        df = build_arc_file_table(synthetic_bids_root)
        # sub-M2001 ses-1 has ALL modalities: T1w, T2w, FLAIR, bold, dwi, sbref, lesion
        ses1 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-1")].iloc[0]

        # Structural: single paths
        assert ses1["t1w"] is not None
        assert ses1["t2w"] is not None
        assert ses1["flair"] is not None
        assert ses1["lesion"] is not None

        # Functional/Diffusion: lists of paths (multi-run support)
        assert isinstance(ses1["bold_naming40"], list)
        assert len(ses1["bold_naming40"]) == 1
        assert isinstance(ses1["bold_rest"], list)
        assert len(ses1["bold_rest"]) == 2

        assert isinstance(ses1["dwi"], list)
        assert len(ses1["dwi"]) == 3  # 3 DWI runs
        assert isinstance(ses1["dwi_bvals"], list)
        assert len(ses1["dwi_bvals"]) == 3
        assert isinstance(ses1["dwi_bvecs"], list)
        assert len(ses1["dwi_bvecs"]) == 3
        # Invariant check
        assert len(ses1["dwi"]) == len(ses1["dwi_bvals"]) == len(ses1["dwi_bvecs"])

        assert isinstance(ses1["sbref"], list)
        assert len(ses1["sbref"]) == 1  # 1 sbref

        # Metadata
        assert ses1["age_at_stroke"] == 38.0
        assert ses1["sex"] == "F"
        assert ses1["race"] is None  # sub-M2001 has None/NaN race
        assert ses1["wab_aq"] == 87.1
        assert ses1["wab_days"] == 895.0
        assert ses1["wab_type"] == "Anomic"

    def test_build_file_table_session_partial_modalities(self, synthetic_bids_root: Path) -> None:
        """Test that session with partial modalities has None for missing paths."""
        df = build_arc_file_table(synthetic_bids_root)
        # sub-M2001 ses-2 has only T1w and T2w (no FLAIR, no func, no dwi)
        ses2 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-2")].iloc[0]

        assert ses2["t1w"] is not None
        assert ses2["t2w"] is not None
        assert ses2["flair"] is None  # No FLAIR in ses-2
        assert ses2["bold_naming40"] == []  # No func/ in ses-2 (empty list)
        assert ses2["bold_rest"] == []
        assert ses2["dwi"] == []  # No dwi/ in ses-2 (empty list)
        assert ses2["dwi_bvals"] == []
        assert ses2["dwi_bvecs"] == []
        assert ses2["sbref"] == []  # No dwi/ in ses-2 (empty list)
        assert ses2["lesion"] is not None

    def test_build_file_table_session_with_minimal_data(self, synthetic_bids_root: Path) -> None:
        """Test that session with minimal data has None for missing paths."""
        df = build_arc_file_table(synthetic_bids_root)
        # sub-M2002 ses-1 has T1w only (minimal - only structural T1w)
        sub2_ses1 = df[(df["subject_id"] == "sub-M2002") & (df["session_id"] == "ses-1")].iloc[0]

        assert sub2_ses1["t1w"] is not None
        assert sub2_ses1["t2w"] is None  # No T2w
        assert sub2_ses1["flair"] is None  # No FLAIR
        assert sub2_ses1["bold_naming40"] == []  # No func/ (empty list)
        assert sub2_ses1["bold_rest"] == []
        assert sub2_ses1["dwi"] == []  # No dwi/ (empty list)
        assert sub2_ses1["dwi_bvals"] == []
        assert sub2_ses1["dwi_bvecs"] == []
        assert sub2_ses1["sbref"] == []  # No dwi/ (empty list)
        assert sub2_ses1["lesion"] is not None

        # Verify race and wab_days for sub-M2002
        assert sub2_ses1["race"] == "w"
        assert sub2_ses1["wab_days"] == 3682.0

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

    def test_bold_unexpected_task_raises(self, synthetic_bids_root: Path) -> None:
        """Unexpected BOLD task types should fail fast (prevent silent data loss)."""
        # Create a BOLD file with unexpected task
        func_dir = synthetic_bids_root / "sub-M2001" / "ses-1" / "func"
        unexpected_bold = func_dir / "sub-M2001_ses-1_task-unknown_run-01_bold.nii.gz"
        _create_minimal_nifti(unexpected_bold)

        with pytest.raises(ValueError, match=r"Unexpected BOLD task"):
            build_arc_file_table(synthetic_bids_root)

    def test_build_file_table_no_sessions_excluded(self, synthetic_bids_root: Path) -> None:
        """Test that subjects with no sessions are excluded from output."""
        df = build_arc_file_table(synthetic_bids_root)
        # sub-M2003 has no imaging data (no sessions), should not appear
        sub3_rows = df[df["subject_id"] == "sub-M2003"]
        assert len(sub3_rows) == 0

    def test_build_file_table_multiple_sessions(self, synthetic_bids_root: Path) -> None:
        """Test that subjects with multiple sessions have multiple rows."""
        df = build_arc_file_table(synthetic_bids_root)
        # sub-M2001 has 2 sessions
        sub1_rows = df[df["subject_id"] == "sub-M2001"]
        assert len(sub1_rows) == 2
        assert set(sub1_rows["session_id"]) == {"ses-1", "ses-2"}

    def test_build_file_table_paths_are_absolute(self, synthetic_bids_root: Path) -> None:
        """Test that file paths are absolute."""
        df = build_arc_file_table(synthetic_bids_root)
        ses1 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-1")].iloc[0]

        assert Path(ses1["t1w"]).is_absolute()
        assert Path(ses1["lesion"]).is_absolute()

    def test_build_file_table_missing_participants_raises(self, tmp_path: Path) -> None:
        """Test that missing participants.tsv raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match=r"participants\.tsv"):
            build_arc_file_table(tmp_path)

    def test_build_file_table_nonexistent_root_raises(self) -> None:
        """Test that non-existent BIDS root raises ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            build_arc_file_table(Path("/nonexistent/path"))


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
        import logging

        nifti = tmp_path / "sub-M2001_ses-1_dwi.nii.gz"
        nifti.touch()
        # No .bval file created

        from bids_hub.datasets.arc import _read_gradient_file

        with caplog.at_level(logging.WARNING), pytest.raises(FileNotFoundError):
            _read_gradient_file(str(nifti), ".bval")

        # Verify warning was logged (not debug)
        assert any("Gradient file not found" in record.message for record in caplog.records)
        assert all(
            record.levelno >= logging.WARNING
            for record in caplog.records
            if "Gradient" in record.message
        )


class TestGetArcFeatures:
    """Tests for get_arc_features function."""

    def test_get_features_returns_features(self) -> None:
        """Test that get_arc_features returns a Features object."""
        from datasets import Features

        features = get_arc_features()
        assert isinstance(features, Features)

    def test_get_features_has_nifti_columns(self) -> None:
        """Test that ALL Nifti columns are present (FULL dataset)."""
        from datasets import Nifti, Sequence

        features = get_arc_features()

        # Structural: single file per session
        assert isinstance(features["t1w"], Nifti)
        assert isinstance(features["t2w"], Nifti)
        assert isinstance(features["flair"], Nifti)
        # Functional/Diffusion: multiple runs per session (Sequence of Nifti)
        assert isinstance(features["bold_naming40"], Sequence)
        assert isinstance(features["bold_rest"], Sequence)
        assert isinstance(features["dwi"], Sequence)
        assert isinstance(features["sbref"], Sequence)
        # Derivatives: single file per session
        assert isinstance(features["lesion"], Nifti)

    def test_get_features_has_gradient_columns(self) -> None:
        """Test that dwi_bvals/dwi_bvecs are present as list[str]."""
        from datasets import Sequence, Value

        features = get_arc_features()

        assert isinstance(features["dwi_bvals"], Sequence)
        assert isinstance(features["dwi_bvecs"], Sequence)
        # Check inner type is string
        assert isinstance(features["dwi_bvals"].feature, Value)
        assert features["dwi_bvals"].feature.dtype == "string"

    def test_get_features_has_metadata_columns(self) -> None:
        """Test that metadata columns are present including session_id."""
        features = get_arc_features()

        assert "subject_id" in features
        assert "session_id" in features
        assert "age_at_stroke" in features
        assert "sex" in features
        assert "race" in features
        assert "wab_aq" in features
        assert "wab_days" in features
        assert "wab_type" in features


class TestBuildAndPushArc:
    """Tests for build_and_push_arc integration."""

    def test_dry_run_calls_build_hf_dataset(self, synthetic_bids_root: Path) -> None:
        """Test that dry run calls build_hf_dataset with correct arguments."""
        from unittest.mock import patch

        config = DatasetBuilderConfig(
            bids_root=synthetic_bids_root,
            hf_repo_id="test/test-repo",
            dry_run=True,
        )

        with patch("bids_hub.datasets.arc.build_hf_dataset") as mock_build:
            mock_build.return_value = None
            build_and_push_arc(config)
            mock_build.assert_called_once()

    def test_dry_run_does_not_push(self, synthetic_bids_root: Path) -> None:
        """Test that dry run does not call push_dataset_to_hub."""
        from unittest.mock import MagicMock, patch

        config = DatasetBuilderConfig(
            bids_root=synthetic_bids_root,
            hf_repo_id="test/test-repo",
            dry_run=True,
        )

        with (
            patch("bids_hub.datasets.arc.build_hf_dataset") as mock_build,
            patch("bids_hub.datasets.arc.push_dataset_to_hub") as mock_push,
        ):
            mock_build.return_value = MagicMock()
            build_and_push_arc(config)
            mock_push.assert_not_called()


class TestExtractAcquisitionType:
    """Tests for _extract_acquisition_type helper function."""

    def test_space_2x(self) -> None:
        """Test extraction of SPACE 2x acceleration."""
        result = _extract_acquisition_type("/data/sub-M2005_ses-4334_acq-spc3p2_run-7_T2w.nii.gz")
        assert result == "space_2x"

    def test_space_no_accel(self) -> None:
        """Test extraction of SPACE no acceleration."""
        result = _extract_acquisition_type("/data/sub-M2001_ses-1253_acq-spc3_run-3_T2w.nii.gz")
        assert result == "space_no_accel"

    def test_turbo_spin_echo(self) -> None:
        """Test extraction of Turbo Spin Echo."""
        result = _extract_acquisition_type("/data/sub-M2002_ses-1441_acq-tse3_run-4_T2w.nii.gz")
        assert result == "turbo_spin_echo"

    def test_no_acq_entity_returns_none(self) -> None:
        """Test that filenames without acq-* return None."""
        result = _extract_acquisition_type("/data/sub-M2001_ses-1_T2w.nii.gz")
        assert result is None

    def test_none_input_returns_none(self) -> None:
        """Test that None input returns None."""
        assert _extract_acquisition_type(None) is None

    def test_unknown_code_returns_raw_label(self) -> None:
        """Test that unknown codes return the raw label (forward compat)."""
        result = _extract_acquisition_type("/data/sub-M2001_ses-1_acq-newseq_T2w.nii.gz")
        assert result == "newseq"

    def test_exact_match_not_substring(self) -> None:
        """Test that mapping uses exact match, not substring.

        Critical: 'spc3foo' should NOT map to 'space_no_accel'.
        It should return 'spc3foo' (raw label).
        """
        result = _extract_acquisition_type("/data/sub-M2001_ses-1_acq-spc3foo_T2w.nii.gz")
        assert result == "spc3foo"  # NOT "space_no_accel"

    def test_case_insensitive(self) -> None:
        """Test that extraction is case-insensitive."""
        result = _extract_acquisition_type("/DATA/SUB-M2001_SES-1_ACQ-SPC3P2_T2W.NII.GZ")
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

    def test_multi_t2w_session_sets_t2w_none(self, synthetic_bids_root: Path) -> None:
        """Verify sessions with multiple T2w files are treated as ambiguous (t2w=None).

        When a session contains multiple T2w files, find_single_nifti returns None
        to avoid ambiguity. Consequently, t2w_acquisition should also be None.
        """
        # Add a second T2w to an existing session to force ambiguity
        anat_dir = synthetic_bids_root / "sub-M2001" / "ses-1" / "anat"
        _create_minimal_nifti(anat_dir / "sub-M2001_ses-1_acq-spc3_T2w.nii.gz")

        df = build_arc_file_table(synthetic_bids_root)
        ses1 = df[(df["subject_id"] == "sub-M2001") & (df["session_id"] == "ses-1")].iloc[0]

        # With two T2w files, both t2w and t2w_acquisition should be None
        assert ses1["t2w"] is None
        assert ses1["t2w_acquisition"] is None


class TestGetArcFeaturesAcquisition:
    """Tests for t2w_acquisition in Features schema."""

    def test_acquisition_in_schema(self) -> None:
        """Verify t2w_acquisition is in the Features schema."""
        from datasets import Value

        features = get_arc_features()

        assert "t2w_acquisition" in features
        assert isinstance(features["t2w_acquisition"], Value)
