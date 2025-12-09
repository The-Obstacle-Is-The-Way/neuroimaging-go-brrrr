"""Tests for ISLES24 validation module."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest

from bids_hub.validation.isles24 import (
    ISLES24_ARCHIVE_MD5,
    check_phenotype_readable,
    validate_isles24_download,
    verify_isles24_archive,
)


@pytest.fixture
def mock_isles24_root(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a mock ISLES24 structure."""
    root = tmp_path / "train"
    root.mkdir()

    # Required directories
    raw_data = root / "raw_data"
    derivatives = root / "derivatives"
    phenotype = root / "phenotype"
    raw_data.mkdir()
    derivatives.mkdir()
    phenotype.mkdir()

    # Required file
    (root / "clinical_data-description.xlsx").write_bytes(b"mock xlsx content")

    # Create 2 subjects in raw_data
    for i in [1, 2]:
        sub = raw_data / f"sub-stroke000{i}" / "ses-01"
        sub.mkdir(parents=True)
        # NCCT file (non-empty)
        (sub / f"sub-stroke000{i}_ses-01_ncct.nii.gz").write_text("fake nifti")

    # Create derivative structure
    for i in [1, 2]:
        deriv_sub = derivatives / f"sub-stroke000{i}"
        (deriv_sub / "ses-01" / "perfusion-maps").mkdir(parents=True)
        (deriv_sub / "ses-02").mkdir(parents=True)
        # DWI and lesion in ses-02
        (deriv_sub / "ses-02" / f"sub-stroke000{i}_space-ncct_dwi.nii.gz").write_text("fake dwi")
        (deriv_sub / "ses-02" / f"sub-stroke000{i}_space-ncct_lesion-msk.nii.gz").write_text(
            "fake lesion"
        )

    yield root


def test_validate_isles24_download_structure(mock_isles24_root: Path) -> None:
    """Test ISLES24 validation on mock structure."""
    # Use strict tolerance to verify our mock fails count checks
    result = validate_isles24_download(mock_isles24_root, tolerance=0.0)

    # Required files should pass
    req_check = next(c for c in result.checks if c.name == "required_files")
    assert req_check.passed

    # Directories should pass
    for dirname in ["raw_data", "derivatives", "phenotype"]:
        dir_check = next(c for c in result.checks if c.name == f"dir_{dirname}")
        assert dir_check.passed

    # Subject count should fail with strict tolerance (2 vs 149 expected)
    subj_check = next(c for c in result.checks if c.name == "subjects")
    assert not subj_check.passed
    assert "2" in subj_check.actual


def test_validate_isles24_download_missing_path() -> None:
    """Test validation on non-existent path."""
    result = validate_isles24_download(Path("/nonexistent/path"))
    assert not result.all_passed
    assert any("MISSING" in c.actual for c in result.checks)


def test_check_phenotype_readable_no_dir(tmp_path: Path) -> None:
    """Test phenotype check when directory doesn't exist."""
    check = check_phenotype_readable(tmp_path)
    # Should pass (optional directory)
    assert check.passed
    assert "not found" in check.details


def test_check_phenotype_readable_no_xlsx(tmp_path: Path) -> None:
    """Test phenotype check when no XLSX files exist."""
    phenotype_dir = tmp_path / "phenotype"
    phenotype_dir.mkdir()
    check = check_phenotype_readable(tmp_path)
    assert check.passed
    assert "No XLSX" in check.details


def test_verify_isles24_archive(tmp_path: Path) -> None:
    """Test ISLES24 archive MD5 verification."""
    # Test with missing file
    missing = tmp_path / "missing.7z"
    check = verify_isles24_archive(missing)
    assert not check.passed
    assert "MISSING" in check.actual

    # Test with wrong content
    fake_archive = tmp_path / "fake.7z"
    fake_archive.write_bytes(b"not the real archive")
    check = verify_isles24_archive(fake_archive)
    assert not check.passed  # MD5 won't match


def test_isles24_archive_md5_constant() -> None:
    """Verify ISLES24_ARCHIVE_MD5 is a valid MD5 hash format."""
    assert len(ISLES24_ARCHIVE_MD5) == 32
    assert all(c in "0123456789abcdef" for c in ISLES24_ARCHIVE_MD5)


def test_validate_isles24_tolerance(mock_isles24_root: Path) -> None:
    """Test that tolerance parameter affects validation."""
    # Strict (0% tolerance) - should fail
    result_strict = validate_isles24_download(mock_isles24_root, tolerance=0.0)
    subj_strict = next(c for c in result_strict.checks if c.name == "subjects")
    assert not subj_strict.passed

    # Very loose (99% tolerance) - passes for 2 vs 149 subjects
    # With 99% tolerance: allowed_missing = int(149 * 0.99) = 147
    # minimum = 149 - 147 = 2, so 2 subjects exactly meets the threshold
    result_loose = validate_isles24_download(mock_isles24_root, tolerance=0.99)
    subj_loose = next(c for c in result_loose.checks if c.name == "subjects")
    assert subj_loose.passed  # 2 subjects meets 99% tolerance minimum
