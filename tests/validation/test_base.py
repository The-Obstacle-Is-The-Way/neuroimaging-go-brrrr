"""Tests for the generic validation framework."""

import hashlib
from collections.abc import Generator
from pathlib import Path

import pytest

from bids_hub.validation.base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    check_count,
    check_zero_byte_files,
    validate_dataset,
    verify_md5,
)


@pytest.fixture
def mock_bids_root(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a mock BIDS structure."""
    bids_root = tmp_path / "mock_bids"
    bids_root.mkdir()

    # Subject 1: Complete
    (bids_root / "sub-001" / "anat").mkdir(parents=True)
    (bids_root / "sub-001" / "anat" / "sub-001_T1w.nii.gz").write_text("fake nifti content")

    # Subject 2: Empty NIfTI (corruption)
    (bids_root / "sub-002" / "anat").mkdir(parents=True)
    (bids_root / "sub-002" / "anat" / "sub-002_T1w.nii.gz").touch()  # 0 bytes

    # Required files
    (bids_root / "dataset_description.json").write_text("{}")

    yield bids_root


def test_validation_check_creation() -> None:
    check = ValidationCheck("test", "A", "A", True)
    assert check.passed
    assert check.name == "test"


def test_validation_result_summary() -> None:
    res = ValidationResult(Path("/tmp"))
    res.add(ValidationCheck("ok", "1", "1", True))
    res.add(ValidationCheck("fail", "1", "0", False))
    summary = res.summary()
    assert "✅ PASS ok" in summary
    assert "❌ FAIL fail" in summary
    assert "1/2 checks failed" in summary


def test_check_count() -> None:
    # Exact match
    c = check_count("test", 10, 10)
    assert c.passed

    # Tolerance (10% of 10 = 1 allowed missing -> min 9)
    c = check_count("test", 9, 10, tolerance=0.1)
    assert c.passed

    # Below tolerance
    c = check_count("test", 8, 10, tolerance=0.1)
    assert not c.passed


def test_check_zero_byte_files(mock_bids_root: Path) -> None:
    count, files = check_zero_byte_files(mock_bids_root)
    assert count == 1
    assert "sub-002_T1w.nii.gz" in files[0]


def test_verify_md5(tmp_path: Path) -> None:
    f = tmp_path / "test.bin"
    content = b"hello world"
    f.write_bytes(content)

    expected = hashlib.md5(content).hexdigest()

    # Correct
    assert verify_md5(f, expected).passed
    # Incorrect
    assert not verify_md5(f, "wronghash").passed
    # Missing
    assert not verify_md5(tmp_path / "missing", expected).passed


def test_validate_dataset_generic(mock_bids_root: Path) -> None:
    # Setup config
    config = DatasetValidationConfig(
        name="test_ds",
        expected_counts={
            "subjects": 2,
            "t1w": 2,
        },
        required_files=["dataset_description.json"],
        modality_patterns={"t1w": "*_T1w.nii.gz"},
    )

    # Run validation
    # Note: We expect failure on zero-byte file (sub-002) but subject count passes (2)
    # T1w count: sub-002 has a file, even if empty, it matches glob pattern.
    # But check_zero_byte_files is separate.

    result = validate_dataset(mock_bids_root, config, run_bids_validator=False)

    # Check individual results
    zero_check = next(c for c in result.checks if c.name == "zero_byte_files")
    assert not zero_check.passed  # Should fail due to sub-002 being 0 bytes

    req_check = next(c for c in result.checks if c.name == "required_files")
    assert req_check.passed

    subj_check = next(c for c in result.checks if c.name == "subjects")
    assert subj_check.passed  # 2 subjects found

    t1w_check = next(c for c in result.checks if c.name == "t1w_count")
    # Both files exist (one empty), so count should be 2
    assert t1w_check.passed
