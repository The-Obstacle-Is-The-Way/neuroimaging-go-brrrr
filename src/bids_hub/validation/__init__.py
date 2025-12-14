"""Validation module for BIDS and HuggingFace datasets.

Architecture (SOLID - Single Responsibility Principle):
- base.py: Generic BIDS/OpenNeuro validation framework
- hf.py: Generic HuggingFace validation framework
- arc.py: ARC-specific validation (OpenNeuro + HuggingFace)
- isles24.py: ISLES24-specific validation (Zenodo download)
"""

# --- Generic BIDS validation (base.py) ---
# --- ARC-specific validation (arc.py) ---
from .arc import (
    ARC_HF_EXPECTED_COUNTS,
    ARC_HF_EXPECTED_SCHEMA,
    ARC_VALIDATION_CONFIG,
    EXPECTED_COUNTS,  # Backward compat
    REQUIRED_BIDS_FILES,  # Backward compat
    validate_arc_download,
    validate_arc_hf,
    validate_arc_hf_from_hub,
)
from .base import (
    DatasetValidationConfig,
    ValidationCheck,
    ValidationResult,
    check_count,
    check_zero_byte_files,
    validate_dataset,
    verify_md5,
)

# --- Generic HuggingFace validation (hf.py) ---
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

# --- ISLES24-specific validation (isles24.py) ---
from .isles24 import (
    ISLES24_ARCHIVE_MD5,
    ISLES24_VALIDATION_CONFIG,
    check_phenotype_readable,
    validate_isles24_download,
    verify_isles24_archive,
)

__all__ = [
    # ARC-specific
    "ARC_HF_EXPECTED_COUNTS",
    "ARC_HF_EXPECTED_SCHEMA",
    "ARC_VALIDATION_CONFIG",
    "EXPECTED_COUNTS",
    # ISLES24-specific
    "ISLES24_ARCHIVE_MD5",
    "ISLES24_VALIDATION_CONFIG",
    "REQUIRED_BIDS_FILES",
    # Generic BIDS
    "DatasetValidationConfig",
    # Generic HuggingFace
    "HFValidationCheck",
    "HFValidationResult",
    "ValidationCheck",
    "ValidationResult",
    "check_count",
    "check_list_alignment",
    "check_list_sessions",
    "check_non_null_count",
    "check_phenotype_readable",
    "check_row_count",
    "check_schema",
    "check_total_list_items",
    "check_unique_values",
    "check_zero_byte_files",
    "validate_arc_download",
    "validate_arc_hf",
    "validate_arc_hf_from_hub",
    "validate_dataset",
    "validate_isles24_download",
    "verify_isles24_archive",
    "verify_md5",
]
