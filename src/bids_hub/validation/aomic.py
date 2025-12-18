"""AOMIC dataset validation.

Uses the generic validation framework with AOMIC-specific configuration.

This module contains validation configs for AOMIC datasets:
- AOMIC-PIOP1 (ds002785): 216 subjects, multimodal MRI
- (Future) AOMIC-PIOP2 (ds002790): 226 subjects
- (Future) AOMIC-ID1000 (ds003097): 928 subjects
"""

from __future__ import annotations

from pathlib import Path

from .base import (
    DatasetValidationConfig,
    ValidationResult,
    validate_dataset,
)

# Expected counts from Scientific Data paper (Snoek et al., 2021)
# doi:10.1038/s41597-021-00870-6
# Originally 248 subjects recorded, 216 included after QC
AOMIC_PIOP1_VALIDATION_CONFIG = DatasetValidationConfig(
    name="aomic-piop1",
    expected_counts={
        "subjects": 216,
        "t1w": 216,  # All subjects have T1w
        "dwi": 211,  # 5 subjects missing DWI data
        "bold": 216,  # All subjects have BOLD (rest + tasks)
    },
    required_files=[
        "dataset_description.json",
        "participants.tsv",
        "participants.json",
    ],
    modality_patterns={
        "t1w": "*_T1w.nii.gz",
        "dwi": "*_dwi.nii.gz",
        "bold": "*_bold.nii.gz",
    },
    custom_checks=[],  # AOMIC-PIOP1 doesn't need custom checks beyond generic
)


def validate_aomic_piop1_download(
    bids_root: Path,
    run_bids_validator: bool = False,
    nifti_sample_size: int = 10,
    tolerance: float = 0.0,
) -> ValidationResult:
    """
    Validate an AOMIC-PIOP1 dataset download.

    This function checks:
    1. Zero-byte file detection (fast corruption check)
    2. Required BIDS files exist
    3. Subject count matches expected (216)
    4. Modality counts match expected (T1w, DWI, BOLD)
    5. Sample NIfTI files are loadable
    6. (Optional) BIDS validator passes

    Args:
        bids_root: Path to the AOMIC-PIOP1 BIDS dataset root.
        run_bids_validator: If True, run external BIDS validator (slow).
        nifti_sample_size: Number of NIfTI files to spot-check.
        tolerance: Allowed missing fraction (0.0 to 1.0). Default 0.0 (strict).

    Returns:
        ValidationResult with all check outcomes.
    """
    return validate_dataset(
        bids_root,
        AOMIC_PIOP1_VALIDATION_CONFIG,
        run_bids_validator=run_bids_validator,
        nifti_sample_size=nifti_sample_size,
        tolerance=tolerance,
    )
