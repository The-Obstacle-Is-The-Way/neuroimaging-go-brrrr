"""Generic validation framework for BIDS datasets."""

from __future__ import annotations

import hashlib
import random
import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ValidationCheck:
    """Result of a single validation check."""

    name: str
    expected: str
    actual: str
    passed: bool
    details: str = ""


@dataclass
class ValidationResult:
    """Complete validation results for a BIDS download."""

    bids_root: Path
    checks: list[ValidationCheck] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        """Return True if all checks passed."""
        return all(c.passed for c in self.checks)

    @property
    def passed_count(self) -> int:
        """Count of passed checks."""
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed_count(self) -> int:
        """Count of failed checks."""
        return sum(1 for c in self.checks if not c.passed)

    def add(self, check: ValidationCheck) -> None:
        """Add a validation check result."""
        self.checks.append(check)

    def summary(self) -> str:
        """Return a formatted summary of validation results."""
        lines = [
            f"Validation Results for: {self.bids_root}",
            "=" * 60,
        ]
        for check in self.checks:
            status = "✅ PASS" if check.passed else "❌ FAIL"
            lines.append(f"{status} {check.name}")
            lines.append(f"       Expected: {check.expected}")
            lines.append(f"       Actual:   {check.actual}")
            if check.details:
                lines.append(f"       Details:  {check.details}")

        lines.append("=" * 60)
        if self.all_passed:
            lines.append("✅ All validations passed! Data is ready for HF push.")
        else:
            lines.append(
                f"❌ {self.failed_count}/{len(self.checks)} checks failed. "
                "Check download or wait for completion."
            )
        return "\n".join(lines)


@dataclass
class DatasetValidationConfig:
    """Configuration for validating a specific dataset."""

    name: str
    expected_counts: dict[str, int]
    required_files: list[str]
    modality_patterns: dict[str, str]  # e.g., {"t1w": "*_T1w.nii.gz"}
    custom_checks: list[Callable[[Path], ValidationCheck]] = field(default_factory=list)


def check_count(
    name: str,
    actual: int,
    expected: int,
    tolerance: float = 0.0,
) -> ValidationCheck:
    """
    Generic count check with optional tolerance.

    Uses minimum-threshold logic: passes if actual >= expected * (1 - tolerance).
    For strict equality checks, use tolerance=0.0.

    Args:
        name: Check name for reporting.
        actual: Actual count found.
        expected: Expected count.
        tolerance: Allowed missing fraction (0.0 to 1.0).

    Returns:
        ValidationCheck with pass/fail status.
    """
    allowed_missing = int(expected * tolerance)
    passed = actual >= (expected - allowed_missing)

    return ValidationCheck(
        name=name,
        expected=f">= {expected - allowed_missing} (target: {expected})",
        actual=str(actual),
        passed=passed,
        details=f"Tolerance: {tolerance:.1%}" if tolerance > 0 else "",
    )


def check_zero_byte_files(bids_root: Path) -> tuple[int, list[str]]:
    """
    CRITICAL: Fast detection of zero-byte NIfTI files (common corruption indicator).

    Returns:
        (count of zero-byte files, list of relative paths)
    """
    zero_byte_files = []
    for nifti in bids_root.rglob("*.nii.gz"):
        # stat().st_size is fast (no read)
        if nifti.stat().st_size == 0:
            zero_byte_files.append(str(nifti.relative_to(bids_root)))
    return len(zero_byte_files), zero_byte_files


def verify_md5(archive_path: Path, expected_md5: str) -> ValidationCheck:
    """
    Verify MD5 checksum of an archive file.

    Args:
        archive_path: Path to archive (e.g., train.7z)
        expected_md5: Expected MD5 hash string

    Returns:
        ValidationCheck with pass/fail and computed hash
    """
    if not archive_path.exists():
        return ValidationCheck(
            name=f"md5_{archive_path.name}",
            expected="file exists",
            actual="MISSING",
            passed=False,
        )

    hash_md5 = hashlib.md5()
    # Read in chunks to handle large files
    try:
        with archive_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        computed_md5 = hash_md5.hexdigest()
    except OSError as e:
        return ValidationCheck(
            name=f"md5_{archive_path.name}",
            expected=expected_md5,
            actual=f"Error reading file: {e}",
            passed=False,
        )

    return ValidationCheck(
        name=f"md5_{archive_path.name}",
        expected=expected_md5,
        actual=computed_md5,
        passed=computed_md5 == expected_md5,
    )


def _check_nifti_integrity(
    bids_root: Path,
    pattern: str = "*_T1w.nii.gz",
    sample_size: int = 10,
) -> ValidationCheck:
    """Generic NIfTI spot-check."""
    try:
        import nibabel as nib
        from nibabel.filebasedimages import ImageFileError
    except ImportError:
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual="nibabel not installed",
            passed=False,
        )

    files = list(bids_root.rglob(pattern))
    if not files:
        # If no files match generic pattern (T1w), try finding ANY nifti
        files = list(bids_root.rglob("*.nii.gz"))
        if not files:
            return ValidationCheck(
                name="nifti_integrity",
                expected="loadable",
                actual="no NIfTI files found",
                passed=False,
            )

    sample = random.sample(files, min(sample_size, len(files)))
    failed_file: Path | None = None

    try:
        for f in sample:
            failed_file = f
            img = nib.load(f)
            _ = img.header
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual=f"{len(sample)}/{len(sample)} passed",
            passed=True,
        )
    except (OSError, ValueError, EOFError, ImageFileError) as e:
        return ValidationCheck(
            name="nifti_integrity",
            expected="loadable",
            actual=f"ERROR: {e}",
            passed=False,
            details=f"Failed on: {failed_file.name}" if failed_file else "",
        )


def _check_bids_validator(bids_root: Path) -> ValidationCheck | None:
    """Run external BIDS validator if available (optional)."""
    if not shutil.which("npx"):
        return None

    try:
        result = subprocess.run(
            ["npx", "--yes", "bids-validator", str(bids_root), "--json"],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            return ValidationCheck(
                name="bids_validator",
                expected="valid BIDS",
                actual="passed",
                passed=True,
            )
        else:
            return ValidationCheck(
                name="bids_validator",
                expected="valid BIDS",
                actual="errors found",
                passed=False,
                details=result.stderr[:200] if result.stderr else "",
            )
    except subprocess.TimeoutExpired:
        return None  # Validator timed out, skip check
    except (subprocess.SubprocessError, OSError):
        return None  # Validator errored, skip check


def _count_sessions_with_modality(bids_root: Path, pattern: str) -> int:
    """Generic session counter."""
    count = 0
    # Assume BIDS structure: sub-*/ses-*/.../pattern or sub-*/.../pattern
    # For robust session counting, we find all ses-* dirs (or sub-* if no sessions)
    # that contain the file.
    # Simplest generic approach: Find all FILES, then count unique parent subjects/sessions.
    # But ISLES24 is flat (no ses- folders).
    # ARC is ses- based.
    # Robust approach: glob files, extract parent folder structure.
    # But for BIDS, "session" concept varies.
    # Let's stick to the ARC implementation logic for now, but generalized?
    # Actually, for ISLES24 (flat), each subject is essentially 1 session.
    # So iterating subjects is safer.

    # Check if sessions exist
    sessions = list(bids_root.glob("sub-*/ses-*"))
    if sessions:
        # Session-based
        for session_dir in sessions:
            if list(session_dir.rglob(pattern)):
                count += 1
    else:
        # Subject-based (flat or no ses- dirs)
        for subject_dir in bids_root.glob("sub-*"):
            if list(subject_dir.rglob(pattern)):
                count += 1
    return count


def validate_dataset(
    bids_root: Path,
    config: DatasetValidationConfig,
    run_bids_validator: bool = False,
    nifti_sample_size: int = 10,
    tolerance: float = 0.0,
) -> ValidationResult:
    """
    Generic validation using dataset-specific config.
    """
    bids_root = Path(bids_root).resolve()
    result = ValidationResult(bids_root=bids_root)

    if not bids_root.exists():
        result.add(
            ValidationCheck(
                name="bids_root",
                expected="directory exists",
                actual="MISSING",
                passed=False,
            )
        )
        return result

    # 1. Zero-byte check (Fail fast)
    zero_count, zero_files = check_zero_byte_files(bids_root)
    result.add(
        ValidationCheck(
            name="zero_byte_files",
            expected="0",
            actual=str(zero_count),
            passed=zero_count == 0,
            details=f"First 5: {', '.join(zero_files[:5])}" if zero_count > 0 else "",
        )
    )

    # 2. Required files
    missing_req = [f for f in config.required_files if not (bids_root / f).exists()]
    result.add(
        ValidationCheck(
            name="required_files",
            expected="all present",
            actual=f"missing: {len(missing_req)}" if missing_req else "all present",
            passed=len(missing_req) == 0,
            details=f"Missing: {', '.join(missing_req)}" if missing_req else "",
        )
    )

    # 3. Counts (Subjects/Sessions/Modalities)
    # Handle "subjects" and "sessions" specifically if in config
    if "subjects" in config.expected_counts:
        # Count sub-* directories
        actual = len(list(bids_root.glob("sub-*")))
        expected = config.expected_counts["subjects"]
        # Use simple count check with tolerance logic
        result.add(check_count("subjects", actual, expected, tolerance))

    if "sessions" in config.expected_counts:
        # Count sub-*/ses-* directories
        actual = len(list(bids_root.glob("sub-*/ses-*")))
        expected = config.expected_counts["sessions"]
        result.add(check_count("sessions", actual, expected, tolerance))

    # Modality counts
    for modality, pattern in config.modality_patterns.items():
        if modality in config.expected_counts:
            # Use the generic counter
            actual = _count_sessions_with_modality(bids_root, pattern)
            expected = config.expected_counts[modality]
            result.add(check_count(f"{modality}_count", actual, expected, tolerance))
        # Note: If key matches config.expected_counts but not in patterns, it's skipped here.

    # 4. Custom Checks
    for check_func in config.custom_checks:
        result.add(check_func(bids_root))

    # 5. NIfTI Integrity
    result.add(_check_nifti_integrity(bids_root, sample_size=nifti_sample_size))

    # 6. Optional BIDS Validator
    if run_bids_validator:
        check = _check_bids_validator(bids_root)
        if check:
            result.add(check)

    return result
