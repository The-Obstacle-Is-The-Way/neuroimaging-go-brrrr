"""
ISLES'24 (Ischemic Stroke Lesion Segmentation 2024) dataset module.

This module converts the ISLES'24 BIDS dataset (Zenodo record 17652035 v7) into a
Hugging Face Dataset.

Dataset info:
- Source: Zenodo (https://zenodo.org/records/17652035)
- Description: Multimodal acute stroke (CT/CTA/CTP) + follow-up (DWI/ADC)
- License: CC BY-NC-SA 4.0
- Task: Acute stroke lesion segmentation & outcome prediction

Schema Design:
- One row per SUBJECT (flattened).
- Acute admission (ses-01) and Follow-up (ses-02) are in the same row.
- This aligns with the ML task: Input (Acute) -> Target (Follow-up Lesion).

Zenodo v7 Structure (SSOT):
```
train/
├── clinical_data-description.xlsx    # Metadata (NOT participants.tsv!)
├── raw_data/                         # NOTE: raw_data (with underscore)
│   └── sub-stroke0001/               # Subject ID pattern
│       └── ses-01/                   # Session: ses-01, ses-02 (NOT ses-0001!)
│           ├── sub-stroke0001_ses-01_ncct.nii.gz
│           └── perfusion-maps/
├── derivatives/
│   └── sub-stroke0001/               # Per-subject (NOT per-derivative-type!)
│       ├── ses-01/
│       │   ├── perfusion-maps/
│       │   │   └── *_space-ncct_tmax.nii.gz  # lowercase!
│       │   └── *_space-ncct_*.nii.gz
│       └── ses-02/
│           └── *_space-ncct_*.nii.gz
└── phenotype/
    └── sub-stroke0001/
        ├── ses-01/
        └── ses-02/
```
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd
from datasets import Features, Nifti, Value

from ..core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub
from ..core.utils import find_single_nifti

logger = logging.getLogger(__name__)


def _load_phenotype_data(phenotype_dir: Path, subject_id: str) -> dict[str, Any]:
    """
    Load phenotype data for a subject from the phenotype directory.

    The phenotype directory structure is:
    phenotype/sub-strokeXXXX/ses-01/  and  phenotype/sub-strokeXXXX/ses-02/

    Zenodo v7 has two files per subject:
    - ses-01/*_demographic_baseline.xlsx: Age, Sex, NIHSS at admission, mRS at admission
    - ses-02/*_outcome.xlsx: mRS 3 months

    Args:
        phenotype_dir: Path to the phenotype directory.
        subject_id: Subject ID (e.g., "sub-stroke0001").

    Returns:
        Dictionary with parsed phenotype values.
    """
    # EXACT column name mapping based on Zenodo v7 SSOT
    # demographic_baseline.xlsx columns: Age, Sex, NIHSS at admission, mRS at admission
    # outcome.xlsx columns: mRS 3 months
    COLUMN_MAP = {
        "Age": "age",
        "Sex": "sex",
        "NIHSS at admission": "nihss_admission",
        "mRS at admission": "mrs_admission",
        "mRS 3 months": "mrs_3month",
    }

    meta: dict[str, Any] = {
        "age": None,
        "sex": None,
        "nihss_admission": None,
        "mrs_admission": None,
        "mrs_3month": None,
    }

    subject_pheno_dir = phenotype_dir / subject_id
    if not subject_pheno_dir.exists():
        return meta

    # Look for XLSX files in ses-01 and ses-02 (Zenodo v7 uses xlsx, not csv)
    for ses_dir in [subject_pheno_dir / "ses-01", subject_pheno_dir / "ses-02"]:
        if not ses_dir.exists():
            continue
        for xlsx_file in ses_dir.glob("*.xlsx"):
            try:
                df = pd.read_excel(xlsx_file)
                if df.empty:
                    continue
                row = df.iloc[0]
                # Use EXACT column name matching (no substring matching!)
                for col in df.columns:
                    if col in COLUMN_MAP:
                        field_name = COLUMN_MAP[col]
                        if meta[field_name] is None:
                            val = row[col]
                            if pd.notna(val):
                                if field_name == "sex":
                                    meta[field_name] = str(val)
                                else:
                                    meta[field_name] = float(val)
            except Exception as e:
                logger.debug("Error reading %s: %s", xlsx_file, e)
                continue

    return meta


def build_isles24_file_table(bids_root: Path) -> pd.DataFrame:
    """
    Build a file table for the ISLES'24 dataset.

    Walks the directory structure and builds a pandas DataFrame with
    one row per SUBJECT (flattening ses-01 and ses-02).

    Zenodo v7 Structure:
    - raw_data/sub-strokeXXXX/ses-01/ (Acute): ncct, cta, ctp, perfusion-maps/
    - derivatives/sub-strokeXXXX/ses-01/ (processed): space-ncct files
    - derivatives/sub-strokeXXXX/ses-02/ (follow-up): dwi, adc, lesion-msk
    - phenotype/sub-strokeXXXX/ses-01/ and ses-02/: CSV files

    Args:
        bids_root: Path to the root of the ISLES24 dataset (e.g., data/zenodo/isles24/train).

    Returns:
        DataFrame with one row per subject.
    """
    bids_root = Path(bids_root).resolve()

    # NOTE: Zenodo v7 uses "raw_data" (with underscore), NOT "rawdata"
    raw_data_root = bids_root / "raw_data"
    derivatives_root = bids_root / "derivatives"
    phenotype_root = bids_root / "phenotype"

    if not raw_data_root.exists():
        raise ValueError(f"raw_data directory not found at {raw_data_root}")

    rows = []

    # Iterate over subjects in raw_data
    subject_dirs = sorted(raw_data_root.glob("sub-*"))
    for subject_dir in subject_dirs:
        subject_id = subject_dir.name  # e.g., "sub-stroke0001"

        # --- SESSION 01: ACUTE (CT/CTA/CTP) ---
        # Raw data structure: raw_data/sub-X/ses-01/
        ses01_raw = subject_dir / "ses-01"

        # Raw CTs - files are directly in ses-01/ (NOT in ct/, cta/, ctp/ subdirs)
        ncct = find_single_nifti(ses01_raw, "*_ncct.nii.gz")
        cta = find_single_nifti(ses01_raw, "*_cta.nii.gz")
        ctp = find_single_nifti(ses01_raw, "*_ctp.nii.gz")

        # Note: Raw perfusion maps exist in raw_data/sub-X/ses-01/perfusion-maps/
        # but we prefer the derivatives (space-ncct registered) versions below

        # --- DERIVATIVES (NCCT-space registered) ---
        # Structure: derivatives/sub-X/ses-01/ and derivatives/sub-X/ses-02/
        deriv_subject_dir = derivatives_root / subject_id

        # Session 01 derivatives (perfusion maps, CTA, CTP in NCCT space)
        ses01_deriv = deriv_subject_dir / "ses-01"

        # Perfusion Maps (space-ncct registered)
        perf_dir = ses01_deriv / "perfusion-maps"
        tmax = find_single_nifti(perf_dir, "*_space-ncct_tmax.nii.gz")
        mtt = find_single_nifti(perf_dir, "*_space-ncct_mtt.nii.gz")
        cbf = find_single_nifti(perf_dir, "*_space-ncct_cbf.nii.gz")
        cbv = find_single_nifti(perf_dir, "*_space-ncct_cbv.nii.gz")

        # CTA and CTP in NCCT space
        cta_deriv = find_single_nifti(ses01_deriv, "*_space-ncct_cta.nii.gz")
        ctp_deriv = find_single_nifti(ses01_deriv, "*_space-ncct_ctp.nii.gz")

        # LVO and CoW masks
        lvo_mask = find_single_nifti(ses01_deriv, "*_space-ncct_lvo-msk.nii.gz")
        cow_seg = find_single_nifti(ses01_deriv, "*_space-ncct_cow-msk.nii.gz")

        # --- SESSION 02: FOLLOW-UP (MRI) ---
        # Structure: derivatives/sub-X/ses-02/
        ses02_deriv = deriv_subject_dir / "ses-02"

        dwi = find_single_nifti(ses02_deriv, "*_space-ncct_dwi.nii.gz")
        adc = find_single_nifti(ses02_deriv, "*_space-ncct_adc.nii.gz")
        lesion_mask = find_single_nifti(ses02_deriv, "*_space-ncct_lesion-msk.nii.gz")

        # --- METADATA ---
        meta = _load_phenotype_data(phenotype_root, subject_id)

        row = {
            "subject_id": subject_id,
            # Acute raw (ses-01)
            "ncct": ncct,
            "cta": cta if cta else cta_deriv,  # Prefer raw, fallback to derivative
            "ctp": ctp if ctp else ctp_deriv,
            # Perfusion Maps (from derivatives, NCCT-space)
            "tmax": tmax,
            "mtt": mtt,
            "cbf": cbf,
            "cbv": cbv,
            # Follow-up (ses-02, from derivatives)
            "dwi": dwi,
            "adc": adc,
            # Masks
            "lesion_mask": lesion_mask,
            "lvo_mask": lvo_mask,
            "cow_segmentation": cow_seg,
            # Metadata (from phenotype xlsx files)
            "age": meta.get("age"),
            "sex": meta.get("sex"),
            "nihss_admission": meta.get("nihss_admission"),
            "mrs_admission": meta.get("mrs_admission"),
            "mrs_3month": meta.get("mrs_3month"),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def get_isles24_features() -> Features:
    """
    Get the Flattened Schema for ISLES'24.
    """
    return Features(
        {
            "subject_id": Value("string"),
            # Acute (ses-01)
            "ncct": Nifti(),
            "cta": Nifti(),
            "ctp": Nifti(),
            # Perfusion Maps
            "tmax": Nifti(),
            "mtt": Nifti(),
            "cbf": Nifti(),
            "cbv": Nifti(),
            # Follow-up (ses-02)
            "dwi": Nifti(),
            "adc": Nifti(),
            # Derivatives
            "lesion_mask": Nifti(),
            "lvo_mask": Nifti(),
            "cow_segmentation": Nifti(),
            # Metadata (from phenotype xlsx files)
            "age": Value("float32"),
            "sex": Value("string"),
            "nihss_admission": Value("float32"),
            "mrs_admission": Value("float32"),
            "mrs_3month": Value("float32"),
        }
    )


def build_and_push_isles24(config: DatasetBuilderConfig) -> None:
    """
    Orchestrate the ISLES'24 build and upload.
    """
    # 1. Build File Table
    logger.info("Building ISLES'24 file table from %s...", config.bids_root)
    file_table = build_isles24_file_table(config.bids_root)
    logger.info("Found %d subjects.", len(file_table))

    # 2. Get Features
    features = get_isles24_features()

    # 3. Build HF Dataset
    logger.info("Building HF Dataset object...")
    ds = build_hf_dataset(config, file_table, features)

    # 4. Push to Hub
    if not config.dry_run:
        # One shard per subject (149 total) to prevent OOM
        num_shards = len(file_table)
        logger.info("Pushing to %s with num_shards=%d...", config.hf_repo_id, num_shards)
        push_dataset_to_hub(ds, config, num_shards=num_shards)
    else:
        logger.info("Dry run complete. Dataset built but not pushed.")
