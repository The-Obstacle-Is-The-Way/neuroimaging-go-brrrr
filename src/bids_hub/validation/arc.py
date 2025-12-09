"""ARC dataset validation.

Uses the generic validation framework with ARC-specific configuration.
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    DatasetValidationConfig,
    ValidationResult,
    validate_dataset,
)

# Expected counts from Sci Data paper (Gibson et al., 2024)
# doi:10.1038/s41597-024-03819-7
# Note: BOLD/DWI/sbref counts are sessions with at least one file of that type
# (the raw file counts are higher due to multiple runs/acquisitions per session)
ARC_VALIDATION_CONFIG = DatasetValidationConfig(
    name="arc",
    expected_counts={
        "subjects": 230,
        "sessions": 902,
        "t1w": 441,
        "t2w": 447,
        "flair": 235,
        "bold": 850,  # Sessions with BOLD fMRI
        "dwi": 613,  # Sessions with diffusion imaging
        "sbref": 88,  # Sessions with single-band reference
        "lesion": 230,  # All subjects have lesion masks
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
        "lesion": "*_desc-lesion_mask.nii.gz",
    },
    custom_checks=[],  # ARC doesn't need custom checks beyond generic
)


# Backward compatibility aliases - preserve old API
EXPECTED_COUNTS = {
    "subjects": 230,
    "sessions": 902,
    "t1w_series": 441,
    "t2w_series": 447,
    "flair_series": 235,
    "bold_series": 850,
    "dwi_series": 613,
    "sbref_series": 88,
    "lesion_masks": 230,
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
