"""
Tests for AOMIC-PIOP1 (Amsterdam Open MRI Collection - PIOP1) dataset module.

These tests use synthetic BIDS structures to verify the AOMIC-PIOP1 file-table builder
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
    build_and_push_aomic_piop1,
    build_aomic_piop1_file_table,
    get_aomic_piop1_features,
)
from bids_hub.core import DatasetBuilderConfig


def _create_minimal_nifti(path: Path) -> None:
    """Create a minimal valid NIfTI file at the given path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.ones((2, 2, 2), dtype=np.float32)
    img = nib.Nifti1Image(data, np.eye(4))
    nib.save(img, path)


@pytest.fixture
def synthetic_aomic_piop1_bids_root() -> Generator[Path, None, None]:
    """Create a synthetic BIDS dataset for AOMIC-PIOP1 testing.

    Structure (no sessions, cross-sectional):
        ds002785/
        ├── participants.tsv
        ├── sub-0001/
        │   ├── anat/
        │   │   └── sub-0001_T1w.nii.gz
        │   ├── dwi/
        │   │   └── sub-0001_dwi.nii.gz
        │   └── func/
        │       ├── sub-0001_task-restingstate_acq-mb3_bold.nii.gz
        │       └── sub-0001_task-emomatching_acq-seq_bold.nii.gz
        ├── sub-0002/
        │   └── anat/
        │       └── sub-0002_T1w.nii.gz  (minimal - only T1w)
        └── sub-0003: no imaging data (only in participants.tsv)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "ds002785"
        root.mkdir()

        # Create participants.tsv
        participants = pd.DataFrame(
            {
                "participant_id": ["sub-0001", "sub-0002", "sub-0003"],
                "age": [25.0, 30.0, 28.0],
                "sex": ["F", "M", "F"],
                "handedness": ["right", "right", "left"],
            }
        )
        participants.to_csv(root / "participants.tsv", sep="\t", index=False)

        # sub-0001: FULL modalities (anat + dwi + func) with MULTIPLE RUNS
        _create_minimal_nifti(root / "sub-0001" / "anat" / "sub-0001_T1w.nii.gz")
        # Single DWI file (AOMIC-PIOP1 pattern)
        _create_minimal_nifti(root / "sub-0001" / "dwi" / "sub-0001_dwi.nii.gz")
        # Multiple BOLD tasks (realistic AOMIC-PIOP1 naming with acq-* entities)
        sub1_func = root / "sub-0001" / "func"
        _create_minimal_nifti(sub1_func / "sub-0001_task-restingstate_acq-mb3_bold.nii.gz")
        _create_minimal_nifti(sub1_func / "sub-0001_task-emomatching_acq-seq_bold.nii.gz")

        # sub-0002: has T1w only (minimal)
        _create_minimal_nifti(root / "sub-0002" / "anat" / "sub-0002_T1w.nii.gz")

        # sub-0003: no imaging data at all (only in participants.tsv)

        yield root


class TestBuildAomicPiop1FileTable:
    """Tests for build_aomic_piop1_file_table function."""

    def test_build_file_table_returns_dataframe(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that build_aomic_piop1_file_table returns a DataFrame."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        assert isinstance(df, pd.DataFrame)

    def test_build_file_table_has_correct_columns(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that the DataFrame has all expected columns."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        expected_columns = {
            "subject_id",
            "t1w",
            "dwi",
            "bold",
            "age",
            "sex",
            "handedness",
        }
        assert set(df.columns) == expected_columns

    def test_build_file_table_has_correct_row_count(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that DataFrame has one row per SUBJECT with imaging data."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        # sub-0001 has data, sub-0002 has data, sub-0003 has NO data
        assert len(df) == 2  # 2 subjects with imaging data

    def test_build_file_table_subject_with_all_modalities(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that subject with all modalities has all paths populated."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        # sub-0001 has ALL modalities: T1w, dwi (2 runs), bold (2 tasks)
        sub1 = df[df["subject_id"] == "sub-0001"].iloc[0]

        # Structural: single path (string)
        assert sub1["t1w"] is not None
        assert isinstance(sub1["t1w"], str)

        # Diffusion: list of paths (single file in AOMIC-PIOP1)
        assert isinstance(sub1["dwi"], list)
        assert len(sub1["dwi"]) == 1  # 1 DWI file

        # BOLD: list of paths (multi-task support)
        assert isinstance(sub1["bold"], list)
        assert len(sub1["bold"]) == 2  # 2 BOLD tasks

        # Metadata
        assert sub1["age"] == 25.0
        assert sub1["sex"] == "F"
        assert sub1["handedness"] == "right"

    def test_build_file_table_subject_partial_modalities(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that subject with partial modalities has empty lists for missing."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        # sub-0002 has only T1w (no dwi, no bold)
        sub2 = df[df["subject_id"] == "sub-0002"].iloc[0]

        assert sub2["t1w"] is not None
        assert isinstance(sub2["t1w"], str)
        assert sub2["dwi"] == []  # No dwi/ directory
        assert sub2["bold"] == []  # No func/ directory

    def test_build_file_table_dwi_as_list(self, synthetic_aomic_piop1_bids_root: Path) -> None:
        """Test that DWI files are captured as list (even when single file)."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        sub1 = df[df["subject_id"] == "sub-0001"].iloc[0]

        assert isinstance(sub1["dwi"], list)
        assert len(sub1["dwi"]) == 1
        # All should be strings
        assert all(isinstance(p, str) for p in sub1["dwi"])

    def test_build_file_table_multiple_bold_runs(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that multiple BOLD tasks are captured as list."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        sub1 = df[df["subject_id"] == "sub-0001"].iloc[0]

        assert isinstance(sub1["bold"], list)
        assert len(sub1["bold"]) == 2
        # All should be strings
        assert all(isinstance(p, str) for p in sub1["bold"])

    def test_build_file_table_missing_subject_excluded(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that subjects with no imaging data are excluded."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        # sub-0003 has no imaging data, should not appear
        sub3_rows = df[df["subject_id"] == "sub-0003"]
        assert len(sub3_rows) == 0

    def test_build_file_table_paths_are_strings(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that t1w column contains strings (not Path objects)."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        sub1 = df[df["subject_id"] == "sub-0001"].iloc[0]

        assert isinstance(sub1["t1w"], str)

    def test_build_file_table_metadata_extracted(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that metadata is correctly extracted from participants.tsv."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        sub1 = df[df["subject_id"] == "sub-0001"].iloc[0]
        sub2 = df[df["subject_id"] == "sub-0002"].iloc[0]

        # sub-0001 metadata
        assert sub1["age"] == 25.0
        assert sub1["sex"] == "F"
        assert sub1["handedness"] == "right"

        # sub-0002 metadata
        assert sub2["age"] == 30.0
        assert sub2["sex"] == "M"
        assert sub2["handedness"] == "right"

    def test_build_file_table_missing_participants_raises(self, tmp_path: Path) -> None:
        """Test that missing participants.tsv raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match=r"participants\.tsv"):
            build_aomic_piop1_file_table(tmp_path)

    def test_build_file_table_nonexistent_root_raises(self) -> None:
        """Test that non-existent BIDS root raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="BIDS root not found"):
            build_aomic_piop1_file_table(Path("/nonexistent/path"))

    def test_build_file_table_empty_lists_for_missing_sequences(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that missing sequences result in empty lists (not None)."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        sub2 = df[df["subject_id"] == "sub-0002"].iloc[0]

        assert sub2["dwi"] == []  # Empty list, not None
        assert sub2["bold"] == []  # Empty list, not None
        assert isinstance(sub2["dwi"], list)
        assert isinstance(sub2["bold"], list)

    def test_build_file_table_paths_are_absolute(
        self, synthetic_aomic_piop1_bids_root: Path
    ) -> None:
        """Test that file paths are absolute."""
        df = build_aomic_piop1_file_table(synthetic_aomic_piop1_bids_root)
        sub1 = df[df["subject_id"] == "sub-0001"].iloc[0]

        # Wrap strings in Path() to check absolute
        assert Path(sub1["t1w"]).is_absolute()
        # Check DWI paths
        assert all(Path(p).is_absolute() for p in sub1["dwi"])


class TestGetAomicPiop1Features:
    """Tests for get_aomic_piop1_features function."""

    def test_get_features_returns_features(self) -> None:
        """Test that get_aomic_piop1_features returns a Features object."""
        from datasets import Features

        features = get_aomic_piop1_features()
        assert isinstance(features, Features)

    def test_get_features_has_nifti_columns(self) -> None:
        """Test that Nifti columns are present with correct types."""
        from datasets import Nifti, Sequence

        features = get_aomic_piop1_features()

        # Structural: single file per subject
        assert isinstance(features["t1w"], Nifti)
        # Functional/Diffusion: multiple runs per subject (Sequence of Nifti)
        assert isinstance(features["dwi"], Sequence)
        assert isinstance(features["bold"], Sequence)

    def test_get_features_has_metadata_columns(self) -> None:
        """Test that metadata columns are present."""
        features = get_aomic_piop1_features()

        assert "subject_id" in features
        assert "age" in features
        assert "sex" in features
        assert "handedness" in features


class TestBuildAndPushAomicPiop1:
    """Tests for build_and_push_aomic_piop1 integration."""

    def test_dry_run_calls_build_hf_dataset(self, synthetic_aomic_piop1_bids_root: Path) -> None:
        """Test that dry run calls build_hf_dataset with correct arguments."""
        from unittest.mock import patch

        config = DatasetBuilderConfig(
            bids_root=synthetic_aomic_piop1_bids_root,
            hf_repo_id="test/test-repo",
            dry_run=True,
        )

        with patch("bids_hub.datasets.aomic_piop1.build_hf_dataset") as mock_build:
            mock_build.return_value = None
            build_and_push_aomic_piop1(config)
            mock_build.assert_called_once()

    def test_dry_run_does_not_push(self, synthetic_aomic_piop1_bids_root: Path) -> None:
        """Test that dry run does not call push_dataset_to_hub."""
        from unittest.mock import MagicMock, patch

        config = DatasetBuilderConfig(
            bids_root=synthetic_aomic_piop1_bids_root,
            hf_repo_id="test/test-repo",
            dry_run=True,
        )

        with (
            patch("bids_hub.datasets.aomic_piop1.build_hf_dataset") as mock_build,
            patch("bids_hub.datasets.aomic_piop1.push_dataset_to_hub") as mock_push,
        ):
            mock_build.return_value = MagicMock()
            build_and_push_aomic_piop1(config)
            mock_push.assert_not_called()
