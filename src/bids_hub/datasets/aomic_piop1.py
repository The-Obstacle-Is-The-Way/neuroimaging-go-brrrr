"""
AOMIC-PIOP1 (Amsterdam Open MRI Collection - PIOP1) dataset module.

This module converts the AOMIC-PIOP1 BIDS dataset (OpenNeuro ds002785) into a
Hugging Face Dataset.

Dataset info:
- OpenNeuro ID: ds002785
- Description: Multimodal MRI from 216 healthy adults (university students)
- License: CC0 (Public Domain)
- URL: https://openneuro.org/datasets/ds002785
- Paper: https://www.nature.com/articles/s41597-021-00870-6

The AOMIC-PIOP1 dataset contains:
- 216 healthy adult subjects
- T1-weighted structural MRI scans
- Diffusion-weighted imaging (multiple runs per subject)
- BOLD fMRI scans (resting-state + multiple tasks)
- Demographics and psychometric data (age, sex, handedness, personality scores)

Schema: One row per SUBJECT (no longitudinal sessions in PIOP1)
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from datasets import Features, Nifti, Sequence, Value

from ..core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub
from ..core.utils import find_all_niftis, find_single_nifti

logger = logging.getLogger(__name__)


def build_aomic_piop1_file_table(bids_root: Path) -> pd.DataFrame:
    """
    Build a file table for the AOMIC-PIOP1 dataset.

    Walks the BIDS directory structure and builds a pandas DataFrame with
    one row per SUBJECT containing paths to imaging data and metadata.

    The function:
    1. Reads participants.tsv for demographics (age, sex, handedness)
    2. For each subject, finds ALL modalities:
       - T1w: Single T1-weighted structural scan
       - DWI: Multiple diffusion-weighted runs (list)
       - BOLD: Multiple fMRI runs (resting-state + tasks, list)
    3. Returns DataFrame with columns: subject_id, t1w, dwi, bold, age, sex, handedness

    Args:
        bids_root: Path to BIDS dataset root (should contain participants.tsv)

    Returns:
        DataFrame with one row per subject, columns for all modalities and metadata.
        Missing modalities are represented as None (single) or [] (sequence).

    Raises:
        FileNotFoundError: If bids_root doesn't exist or participants.tsv is missing
    """
    # Validate inputs
    bids_root = Path(bids_root)
    if not bids_root.exists():
        raise FileNotFoundError(f"BIDS root not found: {bids_root}")

    participants_tsv = bids_root / "participants.tsv"
    if not participants_tsv.exists():
        raise FileNotFoundError(f"participants.tsv not found: {participants_tsv}")

    # Read participants metadata
    logger.info("Reading participants.tsv from %s", participants_tsv)
    participants = pd.read_csv(participants_tsv, sep="\t")
    logger.info("Found %d subjects in participants.tsv", len(participants))

    # Initialize list to collect rows
    rows = []

    # Iterate over each subject in participants.tsv
    for _, row in participants.iterrows():
        subject_id = row["participant_id"]
        subject_dir = bids_root / subject_id

        # Skip if subject directory doesn't exist
        if not subject_dir.exists():
            logger.warning("Subject directory not found: %s (skipping)", subject_dir)
            continue

        logger.debug("Processing subject: %s", subject_id)

        # Find T1w (single structural scan)
        anat_dir = subject_dir / "anat"
        t1w_path = find_single_nifti(anat_dir, f"{subject_id}_T1w.nii.gz")

        # Find DWI (single file per subject in AOMIC-PIOP1)
        dwi_dir = subject_dir / "dwi"
        dwi_paths = find_all_niftis(dwi_dir, f"{subject_id}_dwi.nii.gz")

        # Find BOLD (all fMRI runs: resting-state + tasks)
        func_dir = subject_dir / "func"
        bold_paths = find_all_niftis(func_dir, f"{subject_id}_*_bold.nii.gz")

        # Extract metadata from participants.tsv
        age = float(row["age"]) if pd.notna(row.get("age")) else None
        sex = str(row["sex"]) if pd.notna(row.get("sex")) else None
        handedness = str(row["handedness"]) if pd.notna(row.get("handedness")) else None

        # Build row dictionary
        row_dict = {
            "subject_id": subject_id,
            "t1w": t1w_path,
            "dwi": dwi_paths,
            "bold": bold_paths,
            "age": age,
            "sex": sex,
            "handedness": handedness,
        }

        rows.append(row_dict)

    # Create DataFrame from collected rows
    file_table = pd.DataFrame(rows)
    logger.info("Built file table with %d subjects", len(file_table))

    return file_table


def get_aomic_piop1_features() -> Features:
    """
    Get HuggingFace Features schema for AOMIC-PIOP1 dataset.

    Returns:
        Features object defining the schema with:
        - subject_id: String identifier
        - t1w: Single NIfTI structural scan
        - dwi: Sequence of NIfTI diffusion scans
        - bold: Sequence of NIfTI fMRI scans (all tasks)
        - age: Float (years)
        - sex: String (M/F)
        - handedness: String (left/right/ambidextrous)
    """
    return Features(
        {
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "dwi": Sequence(Nifti()),
            "bold": Sequence(Nifti()),
            "age": Value("float32"),
            "sex": Value("string"),
            "handedness": Value("string"),
        }
    )


def build_and_push_aomic_piop1(config: DatasetBuilderConfig) -> None:
    """
    Build and optionally push AOMIC-PIOP1 dataset to HuggingFace Hub.

    This function orchestrates the full pipeline:
    1. Build file table from BIDS directory
    2. Get Features schema
    3. Build HuggingFace Dataset
    4. Push to Hub (if not dry-run)

    Args:
        config: Configuration containing bids_root, hf_repo_id, dry_run flag

    Raises:
        FileNotFoundError: If BIDS root or participants.tsv missing
    """
    logger.info("Building AOMIC-PIOP1 dataset from %s", config.bids_root)

    # Build file table
    file_table = build_aomic_piop1_file_table(config.bids_root)

    # Get schema
    features = get_aomic_piop1_features()

    # Build HuggingFace Dataset
    logger.info("Converting to HuggingFace Dataset format...")
    ds = build_hf_dataset(config, file_table, features)

    # Push to Hub if not dry-run
    if not config.dry_run:
        logger.info("Pushing dataset to HuggingFace Hub: %s", config.hf_repo_id)
        # Use num_shards = number of subjects to prevent OOM
        num_shards = len(file_table)
        push_dataset_to_hub(ds, config, num_shards=num_shards)
        logger.info("✓ Dataset successfully pushed to %s", config.hf_repo_id)
    else:
        logger.info("Dry run - skipping push to Hub")
