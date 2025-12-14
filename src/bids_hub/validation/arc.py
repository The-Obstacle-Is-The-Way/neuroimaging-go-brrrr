"""ARC dataset validation.

Uses the generic validation framework with ARC-specific configuration.
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    check_count,
    validate_dataset,
)


def _check_lesion_masks(bids_root: Path) -> ValidationCheck:
    """Count lesion masks in derivatives/lesion_masks/.

    ARC lesion masks live in derivatives/lesion_masks/sub-*/ses-*/anat/
    rather than in the raw BIDS tree. The generic modality counter
    only searches sub-*/ses-*/, so we need this custom check.

    Verified against SSOT (OpenNeuro ds004884): 228 lesion masks.
    """
    lesion_dir = bids_root / "derivatives" / "lesion_masks"
    if not lesion_dir.exists():
        return ValidationCheck(
            name="lesion_count",
            expected=">= 228 (target: 228)",
            actual="0",
            passed=False,
            details="derivatives/lesion_masks/ directory not found",
        )

    # Count unique sessions with lesion masks
    lesion_files = list(lesion_dir.rglob("*_desc-lesion_mask.nii.gz"))
    # For ARC, we count raw files since each session has exactly 0 or 1 lesion mask
    actual = len(lesion_files)
    return check_count("lesion_count", actual, expected=228, tolerance=0.0)


# Expected counts verified against SSOT (OpenNeuro ds004884, 2025-12-14).
#
# IMPORTANT: The validator counts SESSIONS with at least one file of each modality,
# NOT raw file counts. This explains discrepancies vs. the Sci Data paper counts:
#
# | Modality | Paper Claims | Raw Files (SSOT) | Sessions w/ Modality |
# |----------|--------------|------------------|----------------------|
# | T1w      | 447          | 444              | 444 (1:1 mapping)    |
# | T2w      | 447          | 441              | 440 (1 session has 2)|
# | FLAIR    | 235          | 235              | 233 (2 sessions have 2)|
# | BOLD     | 1,402        | 1,402            | 850 (multiple runs)  |
# | DWI      | 2,089        | 2,089            | 613 (multiple runs)  |
# | sbref    | 322          | 322              | 88 (multiple runs)   |
# | Lesion   | 228          | 228              | 228 (in derivatives) |
#
# For raw multi-run modalities (BOLD/DWI/sbref), the paper correctly reports
# "sessions" not "files", so those match. Structural modalities (T1w/T2w/FLAIR)
# are reported as raw file counts in the paper but we count sessions.
ARC_VALIDATION_CONFIG = DatasetValidationConfig(
    name="arc",
    expected_counts={
        "subjects": 230,
        "sessions": 902,
        "t1w": 444,  # Sessions with T1w (verified from SSOT)
        "t2w": 440,  # Sessions with T2w (441 files, 1 session has 2)
        "flair": 233,  # Sessions with FLAIR (235 files, 2 sessions have 2)
        "bold": 850,  # Sessions with BOLD fMRI
        "dwi": 613,  # Sessions with diffusion imaging
        "sbref": 88,  # Sessions with single-band reference
        # NOTE: lesion is handled by custom check (_check_lesion_masks)
        # because masks live in derivatives/, not raw sub-*/ses-*/
    },
    required_files=[
        "dataset_description.json",
        "participants.tsv",
        "participants.json",
    ],
    modality_patterns={
        "t1w": "*_T1w.nii.gz",
        "t2w": "*_T2w.nii.gz",
        "flair": "*_FLAIR.nii.gz",
        "bold": "*_bold.nii.gz",
        "dwi": "*_dwi.nii.gz",
        "sbref": "*_sbref.nii.gz",
        # NOTE: lesion not included here - handled by custom check
    },
    custom_checks=[_check_lesion_masks],
)


# Backward compatibility aliases - preserve old API
# NOTE: These are SESSIONS with modality, not raw file counts (see comment above)
EXPECTED_COUNTS = {
    "subjects": 230,
    "sessions": 902,
    "t1w_series": 444,  # Sessions with T1w
    "t2w_series": 440,  # Sessions with T2w
    "flair_series": 233,  # Sessions with FLAIR
    "bold_series": 850,  # Sessions with BOLD
    "dwi_series": 613,  # Sessions with DWI
    "sbref_series": 88,  # Sessions with sbref
    "lesion_masks": 228,  # Lesion masks in derivatives (verified)
}

REQUIRED_BIDS_FILES = [
    "dataset_description.json",
    "participants.tsv",
    "participants.json",
]


def validate_arc_download(
    bids_root: Path,
    run_bids_validator: bool = False,
    nifti_sample_size: int = 10,
    tolerance: float = 0.0,
) -> ValidationResult:
    """
    Validate an ARC dataset download.

    This function checks:
    1. Zero-byte file detection (fast corruption check)
    2. Required BIDS files exist
    3. Subject count matches expected (~230)
    4. Session count matches expected (~902)
    5. Modality counts match expected (T1w, T2w, FLAIR, BOLD, DWI, sbref, lesion)
    6. Sample NIfTI files are loadable
    7. (Optional) BIDS validator passes

    Args:
        bids_root: Path to the ARC BIDS dataset root.
        run_bids_validator: If True, run external BIDS validator (slow).
        nifti_sample_size: Number of NIfTI files to spot-check.
        tolerance: Allowed missing fraction (0.0 to 1.0). Default 0.0 (strict).

    Returns:
        ValidationResult with all check outcomes.
    """
    return validate_dataset(
        bids_root,
        ARC_VALIDATION_CONFIG,
        run_bids_validator=run_bids_validator,
        nifti_sample_size=nifti_sample_size,
        tolerance=tolerance,
    )
