"""Tests for bids_hub.validation module."""

from __future__ import annotations

from pathlib import Path

import pytest

from bids_hub.validation import (
    ARC_VALIDATION_CONFIG,
    EXPECTED_COUNTS,
    REQUIRED_BIDS_FILES,
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    check_count,
    check_zero_byte_files,
    validate_arc_download,
    validate_dataset,
    verify_md5,
)


@pytest.fixture
def mock_bids_root(tmp_path: Path) -> Path:
    """Create a minimal mock BIDS structure for testing."""
    bids_root = tmp_path / "ds004884"
    bids_root.mkdir()

    # Required BIDS files
    (bids_root / "dataset_description.json").write_text('{"Name": "ARC"}')
    (bids_root / "participants.tsv").write_text(
        "participant_id\tsex\tage\nsub-M2001\tM\t50\nsub-M2002\tF\t60\n"
    )
    (bids_root / "participants.json").write_text("{}")

    # Create 2 subject directories with T1w files
    for sub in ["sub-M2001", "sub-M2002"]:
        sub_dir = bids_root / sub / "ses-01" / "anat"
        sub_dir.mkdir(parents=True)
        # Create empty file (nibabel won't load, but glob will find)
        (sub_dir / f"{sub}_ses-01_T1w.nii.gz").touch()

    return bids_root


def test_validation_check_creation() -> None:
    """Test ValidationCheck dataclass creation."""
    check = ValidationCheck(
        name="test_check",
        expected="10",
        actual="10",
        passed=True,
    )
    assert check.name == "test_check"
    assert check.passed is True


def test_validation_result_all_passed() -> None:
    """Test ValidationResult.all_passed property."""
    result = ValidationResult(bids_root=Path("/test"))
    result.add(ValidationCheck("check1", "a", "a", True))
    result.add(ValidationCheck("check2", "b", "b", True))

    assert result.all_passed is True
    assert result.passed_count == 2
    assert result.failed_count == 0


def test_validation_result_some_failed() -> None:
    """Test ValidationResult with failures."""
    result = ValidationResult(bids_root=Path("/test"))
    result.add(ValidationCheck("check1", "a", "a", True))
    result.add(ValidationCheck("check2", "b", "c", False))

    assert result.all_passed is False
    assert result.passed_count == 1
    assert result.failed_count == 1


def test_validation_result_summary() -> None:
    """Test ValidationResult.summary() formatting."""
    result = ValidationResult(bids_root=Path("/test"))
    result.add(ValidationCheck("check1", "expected", "actual", True))

    summary = result.summary()
    assert "Validation Results" in summary
    assert "PASS" in summary
    assert "check1" in summary


def test_validate_arc_download_missing_path() -> None:
    """Test validation on non-existent path."""
    result = validate_arc_download(Path("/nonexistent/path"))

    assert result.all_passed is False
    assert any("MISSING" in c.actual for c in result.checks)


def test_validate_arc_download_mock_structure(mock_bids_root: Path) -> None:
    """Test validation on mock BIDS structure."""
    # Run with strict validation (tolerance=0.0)
    result = validate_arc_download(mock_bids_root, tolerance=0.0)

    # Required files should pass (generic framework uses "required_files" name)
    required_check = next(c for c in result.checks if c.name == "required_files")
    assert required_check.passed is True

    # Subject count should fail (only 2 vs expected ~230)
    subject_check = next(c for c in result.checks if c.name == "subjects")
    assert subject_check.passed is False
    assert "2" in subject_check.actual

    # T1w count should fail (2 vs expected 441)
    # Generic framework uses "{modality}_count" naming
    t1w_check = next(c for c in result.checks if c.name == "t1w_count")
    assert t1w_check.passed is False
    assert "2" in t1w_check.actual


def test_validation_with_tolerance(mock_bids_root: Path) -> None:
    """Test validation with relaxed tolerance."""
    # 2 subjects vs 230 expected is ~99% missing
    # Even with 50% tolerance, this should fail
    result = validate_arc_download(mock_bids_root, tolerance=0.5)

    subject_check = next(c for c in result.checks if c.name == "subjects")
    assert subject_check.passed is False

    # But if we mock ONLY the expected counts to be small, we can test tolerance
    # This is tricky without mocking EXPECTED_COUNTS directly.
    # Instead, let's rely on the fact that 0.0 tolerance works as expected above.


# --- Tests for backward compatibility aliases ---


def test_expected_counts_matches_config() -> None:
    """Test that EXPECTED_COUNTS backward compat alias matches ARC_VALIDATION_CONFIG."""
    # Subjects count should match
    assert EXPECTED_COUNTS["subjects"] == ARC_VALIDATION_CONFIG.expected_counts["subjects"]
    # Sessions count should match
    assert EXPECTED_COUNTS["sessions"] == ARC_VALIDATION_CONFIG.expected_counts["sessions"]
    # T1w (legacy uses t1w_series)
    assert EXPECTED_COUNTS["t1w_series"] == ARC_VALIDATION_CONFIG.expected_counts["t1w"]
    # Lesion masks (legacy uses lesion_masks)
    assert EXPECTED_COUNTS["lesion_masks"] == ARC_VALIDATION_CONFIG.expected_counts["lesion"]


def test_required_bids_files_matches_config() -> None:
    """Test that REQUIRED_BIDS_FILES backward compat alias matches ARC_VALIDATION_CONFIG."""
    assert set(REQUIRED_BIDS_FILES) == set(ARC_VALIDATION_CONFIG.required_files)


# --- Tests for skipped checks ---


def test_validation_check_skipped_field() -> None:
    """Test ValidationCheck skipped field behavior."""
    # Default skipped is False
    check = ValidationCheck("test", "a", "a", True)
    assert check.skipped is False

    # Skipped check
    skipped_check = ValidationCheck("test", "a", "a", True, skipped=True)
    assert skipped_check.skipped is True
    assert skipped_check.passed is True  # Skipped checks are passed but flagged


def test_validation_result_skipped_count() -> None:
    """Test ValidationResult.skipped_count property."""
    result = ValidationResult(bids_root=Path("/test"))
    result.add(ValidationCheck("check1", "a", "a", True))
    result.add(ValidationCheck("check2", "b", "b", True, skipped=True))
    result.add(ValidationCheck("check3", "c", "d", False))

    assert result.skipped_count == 1
    assert result.passed_count == 1  # Skipped checks don't count as passed
    assert result.failed_count == 1
    assert result.all_passed is False  # check3 failed


def test_validation_result_summary_with_skipped() -> None:
    """Test ValidationResult.summary() includes skipped checks."""
    result = ValidationResult(bids_root=Path("/test"))
    result.add(ValidationCheck("check1", "a", "a", True))
    result.add(ValidationCheck("check2", "b", "b", True, skipped=True, details="skipped reason"))

    summary = result.summary()
    assert "SKIP" in summary
    assert "skipped reason" in summary
    assert "1 skipped" in summary


# --- Tests for exported functions ---


def test_check_count_exported() -> None:
    """Test that check_count is properly exported and works."""
    check = check_count("test", 10, 10)
    assert check.passed is True
    assert check.name == "test"


def test_check_zero_byte_files_exported(tmp_path: Path) -> None:
    """Test that check_zero_byte_files is properly exported and works."""
    # Create a zero-byte file
    (tmp_path / "test.nii.gz").touch()
    count, files = check_zero_byte_files(tmp_path)
    assert count == 1
    assert "test.nii.gz" in files[0]


def test_verify_md5_exported(tmp_path: Path) -> None:
    """Test that verify_md5 is properly exported and works."""
    import hashlib

    test_file = tmp_path / "test.bin"
    test_file.write_bytes(b"hello")
    expected_md5 = hashlib.md5(b"hello").hexdigest()

    check = verify_md5(test_file, expected_md5)
    assert check.passed is True


def test_validate_dataset_exported(tmp_path: Path) -> None:
    """Test that validate_dataset is properly exported and works."""
    # Create minimal structure
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "test.txt").write_text("test")

    config = DatasetValidationConfig(
        name="test",
        expected_counts={},
        required_files=["test.txt"],
        modality_patterns={},
    )

    result = validate_dataset(tmp_path, config)
    assert isinstance(result, ValidationResult)
    # Verify the required_files check passed
    req_check = next(c for c in result.checks if c.name == "required_files")
    assert req_check.passed


def test_dataset_validation_config_exported() -> None:
    """Test that DatasetValidationConfig is properly exported."""
    config = DatasetValidationConfig(
        name="test",
        expected_counts={"subjects": 10},
        required_files=["test.txt"],
        modality_patterns={"t1w": "*_T1w.nii.gz"},
    )
    assert config.name == "test"
    assert config.expected_counts["subjects"] == 10
