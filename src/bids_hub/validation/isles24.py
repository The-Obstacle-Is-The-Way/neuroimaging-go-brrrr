"""ISLES24 dataset validation.

Validates ISLES24 dataset structure (Zenodo v7 format).
Note: ISLES24 uses non-standard BIDS structure with raw_data/, derivatives/, phenotype/.
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    _check_nifti_integrity,
    check_count,
    check_zero_byte_files,
    verify_md5,
)

# MD5 checksum from Zenodo record 17652035 v7
ISLES24_ARCHIVE_MD5 = "4959a5dd2438d53e3c86d6858484e781"

# Expected counts from Zenodo v7 / ISLES24 challenge
# Note: Subject counts are based on raw_data/sub-* directories
ISLES24_EXPECTED_COUNTS = {
    "subjects": 149,
    # Raw data modalities (ses-01)
    "ncct": 149,  # All subjects have NCCT
    "cta": 149,  # All subjects have CTA
    "ctp": 140,  # ~94% have CTP (some missing)
    # Derivative perfusion maps (ses-01)
    "tmax": 140,
    "mtt": 140,
    "cbf": 140,
    "cbv": 140,
    # Derivative follow-up (ses-02)
    "dwi": 149,
    "adc": 149,
    "lesion_mask": 149,
    # Optional derivatives (~67%)
    "lvo_mask": 100,
    "cow_mask": 100,
}

# ISLES24 modality patterns - includes full path from bids_root
# Format: (glob_pattern, expected_key)
ISLES24_MODALITY_PATTERNS = {
    "ncct": "raw_data/sub-*/ses-01/*_ncct.nii.gz",
    "cta": "raw_data/sub-*/ses-01/*_cta.nii.gz",
    "tmax": "derivatives/sub-*/ses-01/perfusion-maps/*_space-ncct_tmax.nii.gz",
    "dwi": "derivatives/sub-*/ses-02/*_space-ncct_dwi.nii.gz",
    "lesion_mask": "derivatives/sub-*/ses-02/*_space-ncct_lesion-msk.nii.gz",
    "lvo_mask": "derivatives/sub-*/ses-01/*_space-ncct_lvo-msk.nii.gz",
}

# Configuration dataclass (primarily for documentation; custom validation is used)
ISLES24_VALIDATION_CONFIG = DatasetValidationConfig(
    name="isles24",
    expected_counts=ISLES24_EXPECTED_COUNTS,
    required_files=[
        "clinical_data-description.xlsx",  # NOTE: NOT participants.tsv!
    ],
    modality_patterns={},  # Not used - see ISLES24_MODALITY_PATTERNS above
    custom_checks=[],  # Phenotype check added in validate_isles24_download
)


def check_phenotype_readable(bids_root: Path) -> ValidationCheck:
    """
    Spot-check that phenotype XLSX files are readable.

    Note: Zenodo v7 uses .xlsx files in phenotype/ directory.

    Args:
        bids_root: Path to ISLES24 root (containing phenotype/ dir)

    Returns:
        ValidationCheck with pass/fail/skipped status
    """
    phenotype_dir = bids_root / "phenotype"
    if not phenotype_dir.exists():
        return ValidationCheck(
            name="phenotype_readable",
            expected="phenotype/ exists",
            actual="directory not found",
            passed=True,  # Skipped checks are passed but flagged
            skipped=True,
            details="phenotype/ directory not found - check may indicate incomplete extraction",
        )

    xlsx_files = list(phenotype_dir.rglob("*.xlsx"))
    if not xlsx_files:
        return ValidationCheck(
            name="phenotype_readable",
            expected="XLSX files in phenotype/",
            actual="none found",
            passed=True,  # Skipped checks are passed but flagged
            skipped=True,
            details="No XLSX files found in phenotype/ - metadata will be unavailable",
        )

    try:
        import pandas as pd

        sample_xlsx = xlsx_files[0]
        df = pd.read_excel(sample_xlsx)
        return ValidationCheck(
            name="phenotype_readable",
            expected="readable XLSX",
            actual=f"{len(df)} rows",
            passed=True,
            details=f"Phenotype XLSX readable: {sample_xlsx.name}",
        )
    except Exception as e:
        return ValidationCheck(
            name="phenotype_readable",
            expected="readable XLSX",
            actual="unreadable",
            passed=False,
            details=f"Phenotype XLSX unreadable: {e}",
        )


def _count_isles24_modality(bids_root: Path, pattern: str) -> int:
    """Count ISLES24 modality files using full glob pattern.

    Unlike generic BIDS, ISLES24 uses raw_data/sub-* and derivatives/sub-* structure.
    """
    files = list(bids_root.glob(pattern))
    # Only count non-zero byte files (exclude corrupted)
    return sum(1 for f in files if f.stat().st_size > 0)


def validate_isles24_download(
    bids_root: Path,
    nifti_sample_size: int = 10,
    tolerance: float = 0.1,  # 10% tolerance for optional modalities
) -> ValidationResult:
    """
    Validate an ISLES24 dataset download.

    This function checks:
    1. Zero-byte file detection (fast corruption check)
    2. Required files exist (clinical_data-description.xlsx)
    3. Required directories exist (raw_data/, derivatives/, phenotype/)
    4. Subject count in raw_data/ matches expected (~149)
    5. Modality counts match expected (with tolerance for optional ones)
    6. Sample NIfTI files are loadable
    7. Phenotype XLSX files are readable

    Note: ISLES24 uses non-standard BIDS structure, so this uses custom
    validation logic rather than the generic validate_dataset().

    Args:
        bids_root: Path to the ISLES24 root directory (e.g., train/).
        nifti_sample_size: Number of NIfTI files to spot-check.
        tolerance: Allowed missing fraction (0.0 to 1.0). Default 0.1 (10%).

    Returns:
        ValidationResult with all check outcomes.
    """
    bids_root = Path(bids_root).resolve()
    result = ValidationResult(bids_root=bids_root)

    # Check 0: Root exists
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

    # Check 1: Zero-byte files (fast corruption detection)
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

    # Check 2: Required files
    config = ISLES24_VALIDATION_CONFIG
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

    # Check 3: Required directories (ISLES24-specific)
    for dirname in ["raw_data", "derivatives", "phenotype"]:
        dir_path = bids_root / dirname
        result.add(
            ValidationCheck(
                name=f"dir_{dirname}",
                expected="exists",
                actual="exists" if dir_path.exists() else "MISSING",
                passed=dir_path.exists(),
            )
        )

    # Check 4: Subject count (in raw_data/)
    raw_data = bids_root / "raw_data"
    if raw_data.exists():
        subjects = list(raw_data.glob("sub-*"))
        result.add(
            check_count(
                "subjects",
                len(subjects),
                ISLES24_EXPECTED_COUNTS["subjects"],
                tolerance,
            )
        )

    # Check 5: Modality counts (using ISLES24-specific patterns)
    for modality, pattern in ISLES24_MODALITY_PATTERNS.items():
        expected = ISLES24_EXPECTED_COUNTS.get(modality, 0)
        if expected > 0:
            actual = _count_isles24_modality(bids_root, pattern)
            result.add(check_count(f"{modality}_count", actual, expected, tolerance))

    # Check 6: NIfTI integrity spot-check
    result.add(_check_nifti_integrity(bids_root, sample_size=nifti_sample_size))

    # Check 7: Phenotype XLSX readability
    result.add(check_phenotype_readable(bids_root))

    return result


def verify_isles24_archive(archive_path: Path) -> ValidationCheck:
    """
    Verify MD5 checksum of ISLES24 train.7z archive.

    Args:
        archive_path: Path to the train.7z archive

    Returns:
        ValidationCheck with pass/fail and computed hash
    """
    return verify_md5(archive_path, ISLES24_ARCHIVE_MD5)
