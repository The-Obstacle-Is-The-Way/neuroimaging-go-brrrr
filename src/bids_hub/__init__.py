"""bids_hub - Upload neuroimaging datasets to HuggingFace Hub."""

from __future__ import annotations

# Core (generic)
from .core import DatasetBuilderConfig, build_hf_dataset, push_dataset_to_hub

# Datasets
from .datasets import (
    build_and_push_aomic_piop1,
    build_and_push_arc,
    build_and_push_isles24,
    build_aomic_piop1_file_table,
    build_arc_file_table,
    build_isles24_file_table,
    get_aomic_piop1_features,
    get_arc_features,
    get_isles24_features,
)

# Patches (opt-in)
from .patches import apply_nifti_lazy_loading_patch

# Validation
from .validation import (
    ValidationResult,
    validate_aomic_piop1_download,
    validate_arc_download,
    validate_isles24_download,
)

__version__ = "0.2.0"

__all__ = [
    "DatasetBuilderConfig",
    "ValidationResult",
    "__version__",
    "apply_nifti_lazy_loading_patch",
    "build_and_push_aomic_piop1",
    "build_and_push_arc",
    "build_and_push_isles24",
    "build_aomic_piop1_file_table",
    "build_arc_file_table",
    "build_hf_dataset",
    "build_isles24_file_table",
    "get_aomic_piop1_features",
    "get_arc_features",
    "get_isles24_features",
    "push_dataset_to_hub",
    "validate_aomic_piop1_download",
    "validate_arc_download",
    "validate_isles24_download",
]
