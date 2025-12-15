"""ARC dataset validation.

Provides validation for ARC datasets from both sources:
- OpenNeuro (BIDS source): validate_arc_download()
- HuggingFace (target): validate_arc_hf(), validate_arc_hf_from_hub()

Uses the generic validation frameworks from base.py (BIDS) and hf.py (HuggingFace).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    check_count,
    validate_dataset,
)
from .hf import (
    HFValidationCheck,
    HFValidationResult,
    check_list_alignment,
    check_list_sessions,
    check_non_null_count,
    check_row_count,
    check_schema,
    check_total_list_items,
    check_unique_values,
)

if TYPE_CHECKING:
    from datasets import Dataset

logger = logging.getLogger(__name__)


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
# | T1w      | 447          | 447              | 444 (3 sessions have 2)|
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


# =============================================================================
# ARC HuggingFace Validation
# =============================================================================

# ARC v2 schema: 19 columns (verified against OpenNeuro ds004884 SSOT)
ARC_HF_EXPECTED_SCHEMA = [
    "subject_id",
    "session_id",
    "t1w",
    "t2w",
    "t2w_acquisition",
    "flair",
    "bold_naming40",
    "bold_rest",
    "dwi",
    "dwi_bvals",
    "dwi_bvecs",
    "sbref",
    "lesion",
    "age_at_stroke",
    "sex",
    "race",
    "wab_aq",
    "wab_days",
    "wab_type",
]

# Expected counts for ARC v2 HuggingFace dataset
# Verified against OpenNeuro ds004884 SSOT (2025-12-14)
ARC_HF_EXPECTED_COUNTS = {
    "rows": 902,  # Total sessions
    "subjects": 230,  # Unique subjects
    # Singleton modality non-null counts
    "lesion_non_null": 228,
    # Structural modalities (now lists) - Sessions with at least one file
    "t1w_sessions": 444,
    "t2w_sessions": 440,
    "flair_sessions": 233,
    # Structural modalities - Total files across all sessions
    "t1w_files": 447,
    "t2w_files": 441,
    "flair_files": 235,
    # Sessions with at least one run (list length > 0)
    "bold_naming40_sessions": 750,
    "bold_rest_sessions": 498,
    "dwi_sessions": 613,
    "sbref_sessions": 88,
    # Total runs across all sessions
    "bold_naming40_runs": 894,
    "bold_rest_runs": 508,
    "dwi_runs": 2089,
    "sbref_runs": 322,
}


def _check_nifti_loadable(ds: Dataset, sample_size: int = 5) -> HFValidationCheck:
    """Spot-check that NIfTI files in the HF dataset are loadable."""
    import random

    errors = []
    checked = 0

    # Avoid decoding large list/NIfTI columns we don't need for this spot-check.
    ds_view = ds.select_columns(["subject_id", "session_id", "t1w", "bold_naming40"])

    # Sample random rows
    indices = random.sample(range(len(ds_view)), min(sample_size, len(ds_view)))

    for idx in indices:
        row = ds_view[idx]
        row_id = f"{row['subject_id']}/{row['session_id']}"
        try:
            # Check T1w if present (now a list)
            if row["t1w"]:
                for i, img in enumerate(row["t1w"]):
                    shape = img.shape
                    if len(shape) != 3:
                        errors.append(f"Row {idx} ({row_id}) t1w[{i}]: unexpected shape {shape}")
                    checked += 1

            # Check first BOLD run if present
            if row["bold_naming40"] and len(row["bold_naming40"]) > 0:
                shape = row["bold_naming40"][0].shape
                if len(shape) != 4:
                    errors.append(
                        f"Row {idx} ({row_id}) bold_naming40[0]: unexpected shape {shape}"
                    )
                checked += 1

        except Exception as e:
            errors.append(f"Row {idx} ({row_id}): {e}")

    if not errors:
        return HFValidationCheck(
            name="nifti_loadable",
            expected=f"{sample_size} samples loadable",
            actual=f"{checked} checked, all OK",
            passed=True,
        )

    return HFValidationCheck(
        name="nifti_loadable",
        expected=f"{sample_size} samples loadable",
        actual=f"{len(errors)} errors",
        passed=False,
        details="; ".join(errors[:3]),
    )


def validate_arc_hf(
    ds: Dataset,
    nifti_sample_size: int = 5,
    check_nifti: bool = True,
) -> HFValidationResult:
    """
    Validate an ARC HuggingFace dataset against SSOT expectations.

    Args:
        ds: HuggingFace Dataset to validate.
        nifti_sample_size: Number of NIfTI files to spot-check.
        check_nifti: If True, verify NIfTI files are loadable.

    Returns:
        HFValidationResult with all check outcomes.
    """
    result = HFValidationResult(dataset_name="hugging-science/arc-aphasia-bids")

    # Schema check
    result.add(check_schema(ds, ARC_HF_EXPECTED_SCHEMA))

    # Row count
    result.add(check_row_count(ds, ARC_HF_EXPECTED_COUNTS["rows"]))

    # Unique subjects
    result.add(
        check_unique_values(ds, "subject_id", ARC_HF_EXPECTED_COUNTS["subjects"], "unique_subjects")
    )

    # Singleton modality non-null counts
    for col, key in [
        ("lesion", "lesion_non_null"),
    ]:
        result.add(check_non_null_count(ds, col, ARC_HF_EXPECTED_COUNTS[key]))

    # List modality session counts
    for col, key in [
        ("t1w", "t1w_sessions"),
        ("t2w", "t2w_sessions"),
        ("flair", "flair_sessions"),
        ("bold_naming40", "bold_naming40_sessions"),
        ("bold_rest", "bold_rest_sessions"),
        ("dwi", "dwi_sessions"),
        ("sbref", "sbref_sessions"),
    ]:
        result.add(check_list_sessions(ds, col, ARC_HF_EXPECTED_COUNTS[key]))

    # Total run counts
    for col, key in [
        ("t1w", "t1w_files"),
        ("t2w", "t2w_files"),
        ("flair", "flair_files"),
        ("bold_naming40", "bold_naming40_runs"),
        ("bold_rest", "bold_rest_runs"),
        ("dwi", "dwi_runs"),
        ("sbref", "sbref_runs"),
    ]:
        result.add(check_total_list_items(ds, col, ARC_HF_EXPECTED_COUNTS[key]))

    # DWI gradient alignment
    result.add(
        check_list_alignment(
            ds,
            ["dwi", "dwi_bvals", "dwi_bvecs"],
            row_id_columns=["subject_id", "session_id"],
        )
    )

    # NIfTI loadability (optional, can be slow)
    if check_nifti:
        result.add(_check_nifti_loadable(ds, nifti_sample_size))

    return result


def validate_arc_hf_from_hub(
    repo_id: str = "hugging-science/arc-aphasia-bids",
    split: str = "train",
    nifti_sample_size: int = 5,
    check_nifti: bool = True,
) -> HFValidationResult:
    """
    Load and validate an ARC dataset directly from HuggingFace Hub.

    Args:
        repo_id: HuggingFace repository ID.
        split: Dataset split to validate.
        nifti_sample_size: Number of NIfTI files to spot-check.
        check_nifti: If True, verify NIfTI files are loadable.

    Returns:
        HFValidationResult with all check outcomes.
    """
    from datasets import load_dataset

    logger.info(f"Loading dataset from {repo_id}...")
    ds = load_dataset(repo_id, split=split)

    return validate_arc_hf(
        ds,
        nifti_sample_size=nifti_sample_size,
        check_nifti=check_nifti,
    )
