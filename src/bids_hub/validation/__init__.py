"""Validation module - re-exports for backward compatibility."""

from .arc import (
    ARC_VALIDATION_CONFIG,
    EXPECTED_COUNTS,  # Backward compat
    REQUIRED_BIDS_FILES,  # Backward compat
    validate_arc_download,
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
from .isles24 import (
    ISLES24_ARCHIVE_MD5,
    ISLES24_VALIDATION_CONFIG,
    check_phenotype_readable,
    validate_isles24_download,
    verify_isles24_archive,
)

__all__ = [
    "ARC_VALIDATION_CONFIG",
    "EXPECTED_COUNTS",
    "ISLES24_ARCHIVE_MD5",
    "ISLES24_VALIDATION_CONFIG",
    "REQUIRED_BIDS_FILES",
    "DatasetValidationConfig",
    "ValidationCheck",
    "ValidationResult",
    "check_count",
    "check_phenotype_readable",
    "check_zero_byte_files",
    "validate_arc_download",
    "validate_dataset",
    "validate_isles24_download",
    "verify_isles24_archive",
    "verify_md5",
]
