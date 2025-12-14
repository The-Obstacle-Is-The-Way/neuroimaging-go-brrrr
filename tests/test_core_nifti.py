"""
Tests for core BIDS → HF Dataset conversion functionality.

These tests use fake/minimal data to verify the core plumbing works
without requiring real NIfTI files or BIDS datasets.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import nibabel as nib
import numpy as np
import pandas as pd
import pytest
from datasets import Dataset, Features, Nifti, Value

from bids_hub.core import (
    DatasetBuilderConfig,
    build_hf_dataset,
    push_dataset_to_hub,
    validate_file_table_columns,
)


@pytest.fixture
def dummy_config() -> DatasetBuilderConfig:
    """Create a dummy config for testing."""
    return DatasetBuilderConfig(
        bids_root=Path("/tmp/fake-bids"),
        hf_repo_id="test-user/test-dataset",
        dry_run=True,
    )


@pytest.fixture
def simple_features() -> Features:
    """Create a simple Features schema for testing."""
    return Features(
        {
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "age": Value("float32"),
        }
    )


@pytest.fixture
def temp_nifti_dir() -> Generator[Path, None, None]:
    """Create a temporary directory with fake NIfTI files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create minimal NIfTI files using nibabel
        for i in range(3):
            # Create a tiny 2x2x2 image (minimal valid NIfTI)
            data = np.ones((2, 2, 2), dtype=np.float32) * (i + 1)
            img = nib.Nifti1Image(data, np.eye(4))
            nib.save(img, tmppath / f"sub-{i:03d}_T1w.nii.gz")

        yield tmppath


class TestValidateFileTableColumns:
    """Tests for validate_file_table_columns function."""

    def test_valid_columns(self, simple_features: Features) -> None:
        """Test that validation passes when all columns are present."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-001", "sub-002"],
                "t1w": ["path/to/001.nii.gz", "path/to/002.nii.gz"],
                "age": [25.0, 30.0],
            }
        )

        # Should not raise
        validate_file_table_columns(file_table, simple_features)

    def test_extra_columns_allowed(self, simple_features: Features) -> None:
        """Test that extra columns in file_table are allowed."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-001"],
                "t1w": ["path/to/001.nii.gz"],
                "age": [25.0],
                "extra_column": ["extra_value"],  # Not in features
            }
        )

        # Should not raise
        validate_file_table_columns(file_table, simple_features)

    def test_missing_columns_raises(self, simple_features: Features) -> None:
        """Test that missing columns raise ValueError."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-001"],
                # Missing: t1w, age
            }
        )

        with pytest.raises(ValueError, match="missing columns"):
            validate_file_table_columns(file_table, simple_features)


class TestBuildHfDataset:
    """Tests for build_hf_dataset function."""

    def test_build_dataset_returns_dataset(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that build_hf_dataset returns a Dataset object."""
        # Create file table with real NIfTI paths
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000", "sub-001", "sub-002"],
                "t1w": [
                    str(temp_nifti_dir / "sub-000_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-001_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-002_T1w.nii.gz"),
                ],
                "age": [25.0, 30.0, 35.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        assert isinstance(ds, Dataset)
        assert len(ds) == 3

    def test_build_dataset_has_correct_columns(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that the resulting dataset has the expected columns."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000", "sub-001"],
                "t1w": [
                    str(temp_nifti_dir / "sub-000_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-001_T1w.nii.gz"),
                ],
                "age": [25.0, 30.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        assert set(ds.column_names) == {"subject_id", "t1w", "age"}

    def test_build_dataset_excludes_extra_columns(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that columns not in features are excluded from the dataset."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000"],
                "t1w": [str(temp_nifti_dir / "sub-000_T1w.nii.gz")],
                "age": [25.0],
                "extra_column": ["should_be_excluded"],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        assert "extra_column" not in ds.column_names

    def test_build_dataset_nifti_feature_type(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that Nifti columns have the correct feature type."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000"],
                "t1w": [str(temp_nifti_dir / "sub-000_T1w.nii.gz")],
                "age": [25.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        # Check that the t1w feature is a Nifti type
        assert isinstance(ds.features["t1w"], Nifti)

    def test_build_dataset_can_load_nifti(
        self,
        dummy_config: DatasetBuilderConfig,
        temp_nifti_dir: Path,
    ) -> None:
        """Test that NIfTI files can be loaded from the dataset."""
        file_table = pd.DataFrame(
            {
                "subject_id": ["sub-000"],
                "t1w": [str(temp_nifti_dir / "sub-000_T1w.nii.gz")],
                "age": [25.0],
            }
        )

        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
                "age": Value("float32"),
            }
        )

        ds = build_hf_dataset(dummy_config, file_table, features)

        # Access the first example's NIfTI image
        example = ds[0]
        nifti_img = example["t1w"]

        # Should be a nibabel Nifti1Image
        assert isinstance(nifti_img, nib.nifti1.Nifti1Image)

        # Check we can get the data
        data = nifti_img.get_fdata()
        assert data.shape == (2, 2, 2)
        assert np.allclose(data, 1.0)  # First subject has all 1s


class TestDatasetBuilderConfig:
    """Tests for DatasetBuilderConfig dataclass."""

    def test_config_creation(self) -> None:
        """Test that config can be created with required fields."""
        config = DatasetBuilderConfig(
            bids_root=Path("/path/to/bids"),
            hf_repo_id="user/dataset",
        )

        assert config.bids_root == Path("/path/to/bids")
        assert config.hf_repo_id == "user/dataset"
        assert config.split is None
        assert config.dry_run is False

    def test_config_with_optional_fields(self) -> None:
        """Test that optional fields can be set."""
        config = DatasetBuilderConfig(
            bids_root=Path("/path/to/bids"),
            hf_repo_id="user/dataset",
            split="train",
            dry_run=True,
        )

        assert config.split == "train"
        assert config.dry_run is True


class TestPushDatasetToHub:
    """Tests for push_dataset_to_hub function."""

    def test_push_dataset_to_hub_default_embeds_files(self) -> None:
        """Ensure embed_external_files defaults to True."""
        from unittest.mock import Mock, patch

        config = DatasetBuilderConfig(
            bids_root=Path("/fake/path"),
            hf_repo_id="test/arc-aphasia",
        )

        mock_ds = Mock()
        with patch.object(mock_ds, "push_to_hub") as mock_push:
            push_dataset_to_hub(mock_ds, config)
            mock_push.assert_called_once()
            # Verify embed_external_files=True was passed
            assert mock_push.call_args[1]["embed_external_files"] is True

    def test_push_dataset_to_hub_passes_repo_id(self) -> None:
        """Ensure the correct repo ID is passed to push_to_hub."""
        from unittest.mock import Mock, patch

        config = DatasetBuilderConfig(
            bids_root=Path("/fake/path"),
            hf_repo_id="hugging-science/arc-aphasia-bids",
        )

        mock_ds = Mock()
        with patch.object(mock_ds, "push_to_hub") as mock_push:
            push_dataset_to_hub(mock_ds, config)
            mock_push.assert_called_once()
            # First positional arg should be the repo ID
            assert mock_push.call_args[0][0] == "hugging-science/arc-aphasia-bids"

    def test_push_dataset_to_hub_explicit_false_allowed(self) -> None:
        """Ensure explicitly passing embed_external_files=False is allowed."""
        from unittest.mock import Mock, patch

        config = DatasetBuilderConfig(
            bids_root=Path("/fake/path"),
            hf_repo_id="test/arc-aphasia",
        )

        mock_ds = Mock()
        with patch.object(mock_ds, "push_to_hub") as mock_push:
            # Explicitly passing False is allowed (for local-only testing)
            push_dataset_to_hub(mock_ds, config, embed_external_files=False)
            mock_push.assert_called_once()
            assert mock_push.call_args[1]["embed_external_files"] is False

    def test_push_dataset_to_hub_passes_extra_kwargs(self) -> None:
        """Ensure additional kwargs are passed through to push_to_hub."""
        from unittest.mock import Mock, patch

        config = DatasetBuilderConfig(
            bids_root=Path("/fake/path"),
            hf_repo_id="test/arc-aphasia",
        )

        mock_ds = Mock()
        with patch.object(mock_ds, "push_to_hub") as mock_push:
            push_dataset_to_hub(mock_ds, config, private=True, commit_message="test")
            mock_push.assert_called_once()
            assert mock_push.call_args[1]["private"] is True
            assert mock_push.call_args[1]["commit_message"] == "test"

    def test_push_dataset_to_hub_custom_sharded_logic(self, temp_nifti_dir: Path) -> None:
        """Ensure custom sharding logic is triggered when num_shards > 1."""
        import shutil
        from unittest.mock import patch

        import pyarrow as pa

        config = DatasetBuilderConfig(
            bids_root=Path("/fake/path"),
            hf_repo_id="test/arc-aphasia",
        )

        # Create a real small dataset (2 rows) for testing
        features = Features(
            {
                "subject_id": Value("string"),
                "t1w": Nifti(),
            }
        )
        real_ds = Dataset.from_dict(
            {
                "subject_id": ["sub-001", "sub-002"],
                "t1w": [
                    str(temp_nifti_dir / "sub-000_T1w.nii.gz"),
                    str(temp_nifti_dir / "sub-001_T1w.nii.gz"),
                ],
            }
        ).cast(features)

        # Clean up any leftover staging dir from previous test runs
        staging_dir = Path("./hf_upload_staging")
        if staging_dir.exists():
            shutil.rmtree(staging_dir)

        # Mock HfApi and pq.write_table
        with (
            patch("bids_hub.core.builder.HfApi") as MockApi,
            patch("bids_hub.core.builder.embed_table_storage") as mock_embed,
            patch("bids_hub.core.builder.pq.write_table") as mock_write,
        ):
            mock_api_instance = MockApi.return_value
            # embed_table_storage returns a simple table
            mock_embed.return_value = pa.table({"col": [1]})

            # Side effect for write_table to create the file so unlink() works
            def create_dummy_file(table: pa.Table, path: str) -> None:
                Path(path).touch()

            mock_write.side_effect = create_dummy_file

            # Remote verification: all expected files are present in repo after upload
            mock_api_instance.list_repo_files.return_value = [
                "dataset_info.json",
                "data/train-00000-of-00002.parquet",
                "data/train-00001-of-00002.parquet",
            ]

            # Call with num_shards=2 using real dataset
            push_dataset_to_hub(real_ds, config, num_shards=2)

            # Verify create_repo called with explicit private parameter
            mock_api_instance.create_repo.assert_called_once_with(
                "test/arc-aphasia", repo_type="dataset", private=False, exist_ok=True
            )

            # Verify embed_table_storage called twice (once per shard)
            assert mock_embed.call_count == 2

            # Verify pq.write_table called twice
            assert mock_write.call_count == 2

            # Verify upload_large_folder called (bulk upload instead of per-shard)
            mock_api_instance.upload_large_folder.assert_called_once()

            # Verify remote verification was performed
            mock_api_instance.list_repo_files.assert_called()

        # Clean up staging directory after test (since we no longer auto-delete)
        # See BUG-004: We don't auto-delete to avoid race with HF retry logic
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
