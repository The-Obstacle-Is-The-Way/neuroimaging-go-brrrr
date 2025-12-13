"""
ARC (Aphasia Recovery Cohort) dataset module.

This module converts the ARC BIDS dataset (OpenNeuro ds004884) into a
Hugging Face Dataset.

Dataset info:
- OpenNeuro ID: ds004884
- Description: Multimodal neuroimaging dataset for aphasia patients
- License: CC0 (Public Domain)
- URL: https://openneuro.org/datasets/ds004884

The ARC dataset contains:
- 230 chronic stroke patients with aphasia
- 902 scanning sessions (longitudinal)
- T1-weighted structural MRI scans (447)
- T2-weighted structural MRI scans (441)
- FLAIR structural MRI scans (235)
- BOLD fMRI scans (1,402)
- Diffusion-weighted imaging (2,089)
- Single-band reference images (322)
- Expert-drawn lesion segmentation masks (228)
- Demographic and clinical metadata (age, sex, WAB-AQ scores)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pandas as pd
from datasets import Features, Nifti, Sequence, Value

from ..core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub
from ..core.utils import find_all_niftis, find_single_nifti

logger = logging.getLogger(__name__)


# ARC acquisition type mapping (exact match, not substring)
_ARC_ACQUISITION_MAP: dict[str, str] = {
    "spc3p2": "space_2x",  # SPACE with 2x acceleration
    "spc3": "space_no_accel",  # SPACE without acceleration
    "tse3": "turbo_spin_echo",  # Turbo Spin Echo
}


def _extract_acquisition_type(filepath: str | None) -> str | None:
    """
    Extract acquisition type from BIDS filename.

    BIDS filenames contain acq-<label> entity that indicates the acquisition type.
    For ARC T2w images, we map known codes to human-readable names.

    Args:
        filepath: Path to NIfTI file (may be None)

    Returns:
        - Known code: mapped name (e.g., "spc3p2" -> "space_2x")
        - Unknown code: raw label (forward compatible)
        - No acq-* entity or None input: None
    """
    if filepath is None:
        return None

    match = re.search(r"acq-([a-z0-9]+)", str(filepath).lower())
    if not match:
        return None

    acq_label = match.group(1)

    # Use exact match mapping (not substring) to avoid mismapping
    # e.g., "spc3foo" should return "spc3foo", not "space_no_accel"
    return _ARC_ACQUISITION_MAP.get(acq_label, acq_label)


def build_arc_file_table(bids_root: Path) -> pd.DataFrame:
    """
    Build a file table for the ARC dataset.

    Walks the BIDS directory structure and builds a pandas DataFrame with
    one row per SESSION containing paths to imaging data and metadata.

    The function:
    1. Reads participants.tsv for demographics (age, sex, WAB scores)
    2. For each subject, iterates over all sessions (ses-*)
    3. For each session, finds ALL modalities:
       - anat/: T1w, T2w, FLAIR
       - func/: BOLD fMRI
       - dwi/: DWI, sbref
    4. Finds lesion masks in derivatives/lesion_masks/sub-*/ses-*/anat/
    5. Returns a DataFrame ready for HF Dataset conversion

    Args:
        bids_root: Path to the root of the ARC BIDS dataset (ds004884).

    Returns:
        DataFrame with columns:
            - subject_id (str): BIDS subject identifier (e.g., "sub-M2001")
            - session_id (str): BIDS session identifier (e.g., "ses-1")
            - t1w (str | None): Absolute path to T1-weighted NIfTI
            - t2w (str | None): Absolute path to T2-weighted NIfTI
            - t2w_acquisition (str | None): Acquisition type for T2w (e.g., "space_2x")
            - flair (str | None): Absolute path to FLAIR NIfTI
            - bold (list[str]): List of absolute paths to ALL BOLD runs
            - dwi (list[str]): List of absolute paths to ALL DWI runs
            - sbref (list[str]): List of absolute paths to ALL sbref runs
            - lesion (str | None): Absolute path to lesion mask NIfTI
            - age_at_stroke (float): Subject age at stroke
            - sex (str): Subject sex (M/F)
            - wab_aq (float): WAB Aphasia Quotient (severity score)
            - wab_type (str): Aphasia type classification

    Raises:
        FileNotFoundError: If participants.tsv doesn't exist.
        ValueError: If bids_root doesn't exist or is not a directory.
    """
    bids_root = Path(bids_root).resolve()

    if not bids_root.exists():
        raise ValueError(f"BIDS root does not exist: {bids_root}")
    if not bids_root.is_dir():
        raise ValueError(f"BIDS root is not a directory: {bids_root}")

    # Read participants.tsv
    participants_tsv = bids_root / "participants.tsv"
    if not participants_tsv.exists():
        raise FileNotFoundError(f"participants.tsv not found at {participants_tsv}")

    participants = pd.read_csv(participants_tsv, sep="\t")
    total_subjects_in_tsv = len(participants)

    # Build file table - one row per session
    rows: list[dict[str, str | float | list[str] | None]] = []

    # Track statistics for summary logging
    subjects_found = 0
    subjects_missing_dir = 0
    subjects_no_sessions = 0

    for _, row in participants.iterrows():
        subject_id = str(row["participant_id"])
        subject_dir = bids_root / subject_id

        if not subject_dir.exists():
            subjects_missing_dir += 1
            continue

        # Find all sessions for this subject
        session_dirs = sorted(subject_dir.glob("ses-*"))

        if not session_dirs:
            subjects_no_sessions += 1
            continue

        subjects_found += 1

        # Extract subject-level metadata (same for all sessions)
        age_at_stroke_raw = row.get("age_at_stroke")
        age_at_stroke: float | None = None
        if age_at_stroke_raw is not None and pd.notna(age_at_stroke_raw):
            try:
                age_at_stroke = float(age_at_stroke_raw)
            except (ValueError, TypeError):
                logger.warning("Invalid age_at_stroke for %s: %r", subject_id, age_at_stroke_raw)

        wab_aq_raw = row.get("wab_aq")
        wab_aq: float | None = None
        if wab_aq_raw is not None and pd.notna(wab_aq_raw):
            try:
                wab_aq = float(wab_aq_raw)
            except (ValueError, TypeError):
                logger.warning("Invalid wab_aq for %s: %r", subject_id, wab_aq_raw)

        sex = str(row.get("sex", "")) if pd.notna(row.get("sex")) else None
        wab_type = str(row.get("wab_type", "")) if pd.notna(row.get("wab_type")) else None

        # Iterate over each session
        for session_dir in session_dirs:
            session_id = session_dir.name  # e.g., "ses-1"

            # Find structural modalities in anat/ (single file per session)
            t1w_path = find_single_nifti(session_dir / "anat", "*_T1w.nii.gz")
            t2w_path = find_single_nifti(session_dir / "anat", "*_T2w.nii.gz")
            t2w_acquisition = _extract_acquisition_type(t2w_path)
            flair_path = find_single_nifti(session_dir / "anat", "*_FLAIR.nii.gz")

            # Find functional modalities in func/ (ALL runs)
            bold_paths = find_all_niftis(session_dir / "func", "*_bold.nii.gz")

            # Find diffusion modalities in dwi/ (ALL runs)
            dwi_paths = find_all_niftis(session_dir / "dwi", "*_dwi.nii.gz")
            sbref_paths = find_all_niftis(session_dir / "dwi", "*_sbref.nii.gz")

            # Find lesion mask in derivatives for this session (single file)
            # Note: find_single_nifti already handles missing directories
            lesion_session_dir = (
                bids_root / "derivatives" / "lesion_masks" / subject_id / session_id / "anat"
            )
            lesion_path = find_single_nifti(lesion_session_dir, "*_desc-lesion_mask.nii.gz")

            rows.append(
                {
                    "subject_id": subject_id,
                    "session_id": session_id,
                    "t1w": t1w_path,
                    "t2w": t2w_path,
                    "t2w_acquisition": t2w_acquisition,
                    "flair": flair_path,
                    "bold": bold_paths,  # List of paths (all runs)
                    "dwi": dwi_paths,  # List of paths (all runs)
                    "sbref": sbref_paths,  # List of paths (all runs)
                    "lesion": lesion_path,
                    "age_at_stroke": age_at_stroke,
                    "sex": sex,
                    "wab_aq": wab_aq,
                    "wab_type": wab_type,
                }
            )

    # Log summary of what was found vs what was expected
    total_sessions = len(rows)
    skipped = subjects_missing_dir + subjects_no_sessions
    if skipped > 0:
        logger.warning(
            "Built file table with %d sessions from %d subjects "
            "(participants.tsv lists %d; %d missing directories, %d with no sessions)",
            total_sessions,
            subjects_found,
            total_subjects_in_tsv,
            subjects_missing_dir,
            subjects_no_sessions,
        )
    else:
        logger.info(
            "Built file table with %d sessions from %d subjects",
            total_sessions,
            subjects_found,
        )

    return pd.DataFrame(rows)


def get_arc_features() -> Features:
    """
    Get the Hugging Face Features schema for the ARC dataset.

    Schema:
        - subject_id: BIDS identifier (e.g., "sub-M2001")
        - session_id: BIDS session identifier (e.g., "ses-1")
        - t1w: T1-weighted structural MRI (Nifti, single file)
        - t2w: T2-weighted structural MRI (Nifti, nullable, single file)
        - t2w_acquisition: T2w acquisition type (space_2x, space_no_accel, turbo_spin_echo)
        - flair: FLAIR structural MRI (Nifti, nullable, single file)
        - bold: BOLD fMRI 4D time-series (Sequence of Nifti, supports multiple runs)
        - dwi: Diffusion-weighted imaging (Sequence of Nifti, supports multiple runs)
        - sbref: Single-band reference images (Sequence of Nifti, supports multiple runs)
        - lesion: Expert-drawn lesion mask (Nifti, single file)
        - age_at_stroke: Age at time of stroke (float)
        - sex: Biological sex (M/F)
        - wab_aq: WAB Aphasia Quotient (severity score, 0-100)
        - wab_type: Aphasia type classification

    Returns:
        Features object with Nifti()/Sequence(Nifti()) for image columns.
    """
    return Features(
        {
            "subject_id": Value("string"),
            "session_id": Value("string"),
            # Structural: single file per session
            "t1w": Nifti(),
            "t2w": Nifti(),
            "t2w_acquisition": Value("string"),
            "flair": Nifti(),
            # Functional/Diffusion: multiple runs per session
            "bold": Sequence(Nifti()),
            "dwi": Sequence(Nifti()),
            "sbref": Sequence(Nifti()),
            # Derivatives: single file per session
            "lesion": Nifti(),
            # Metadata
            "age_at_stroke": Value("float32"),
            "sex": Value("string"),
            "wab_aq": Value("float32"),
            "wab_type": Value("string"),
        }
    )


def build_and_push_arc(config: DatasetBuilderConfig) -> None:
    """
    High-level pipeline: build ARC file table, convert to HF Dataset, optionally push.

    This is the main entry point for processing the ARC dataset. It:
    1. Calls `build_arc_file_table()` to create the file table
    2. Gets the features schema from `get_arc_features()`
    3. Uses `build_hf_dataset()` to create the HF Dataset
    4. Optionally pushes to Hub (unless dry_run=True)

    Args:
        config: Configuration with BIDS root path and HF repo info.

    Raises:
        FileNotFoundError: If participants.tsv doesn't exist.
        ValueError: If bids_root doesn't exist or is not a directory.
    """
    # Build the file table from BIDS directory
    file_table = build_arc_file_table(config.bids_root)

    # Get the features schema
    features = get_arc_features()

    # Build the HF Dataset
    ds = build_hf_dataset(config, file_table, features)

    # Push to Hub if not a dry run
    if not config.dry_run:
        # CRITICAL: Force sharding to prevent OOM.
        # The dataset library estimates size based on file paths (small),
        # but embedding NIfTIs makes it huge (278GB).
        # Without num_shards, it tries to build 1 giant shard in RAM -> CRASH.
        # 1 shard per session (~300MB) is safe and efficient.
        num_shards = len(file_table)
        logger.info("Pushing to Hub with num_shards=%d to prevent OOM", num_shards)

        push_dataset_to_hub(ds, config, num_shards=num_shards)
