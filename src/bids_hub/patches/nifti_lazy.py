"""Lazy voxel-loading patch for `datasets` NIfTI decoding.

The `datasets` dependency currently constructs a `Nifti1ImageWrapper` by calling
`nibabel.Nifti1Image.get_fdata()` inside `__init__`, which eagerly materializes
the full voxel array in RAM.

This module provides an opt-in monkey-patch that replaces that eager call with
`nifti_image.dataobj` to preserve nibabel's lazy proxy behavior.
"""

from __future__ import annotations

from typing import Any

_PATCH_SENTINEL_ATTR = "_BIDS_HUB_NIFTI_LAZY_LOADING_PATCH_APPLIED"


def apply_nifti_lazy_loading_patch() -> bool:
    """Enable lazy voxel materialization for `datasets` NIfTI decoding.

    This monkey-patches `datasets.features.nifti.Nifti1ImageWrapper.__init__` to
    pass `dataobj=nifti_image.dataobj` instead of `nifti_image.get_fdata()`.

    Call once before decoding NIfTI columns (e.g., before `datasets.load_dataset`
    materializes examples).

    Returns:
        True if the patch was applied, False if it was already applied.

    Raises:
        ImportError: If `datasets` or `nibabel` is not available.
        RuntimeError: If `Nifti1ImageWrapper` is not available (typically when
            `nibabel` isn't installed alongside `datasets`).
    """
    try:
        import inspect

        import nibabel as nib
        from datasets.features import nifti as ds_nifti
    except ImportError as exc:
        raise ImportError("NIfTI lazy-loading patch requires `datasets` and `nibabel`.") from exc

    if getattr(ds_nifti, _PATCH_SENTINEL_ATTR, False):
        return False

    wrapper_class = getattr(ds_nifti, "Nifti1ImageWrapper", None)
    if wrapper_class is None:
        raise RuntimeError(
            "`datasets.features.nifti.Nifti1ImageWrapper` not found. Ensure `nibabel` is installed."
        )

    init_params = set(inspect.signature(nib.nifti1.Nifti1Image.__init__).parameters)

    def _lazy_init(self: Any, nifti_image: nib.nifti1.Nifti1Image) -> None:
        kwargs: dict[str, Any] = {
            "dataobj": nifti_image.dataobj,
            "affine": nifti_image.affine,
            "header": nifti_image.header,
            "extra": nifti_image.extra,
        }
        if "file_map" in init_params:
            kwargs["file_map"] = getattr(nifti_image, "file_map", None)
        if "dtype" in init_params and hasattr(nifti_image, "get_data_dtype"):
            kwargs["dtype"] = nifti_image.get_data_dtype()

        nib.nifti1.Nifti1Image.__init__(self, **kwargs)
        self.nifti_image = nifti_image

    wrapper_class.__init__ = _lazy_init
    setattr(ds_nifti, _PATCH_SENTINEL_ATTR, True)
    return True
