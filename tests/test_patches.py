"""Tests for bids_hub.patches.* modules."""

from __future__ import annotations

from pathlib import Path

import nibabel as nib
import numpy as np
import pytest


@pytest.fixture
def nifti_file(tmp_path: Path) -> Path:
    path = tmp_path / "test.nii.gz"
    data = np.ones((2, 3, 4), dtype=np.float32)
    img = nib.Nifti1Image(data, affine=np.eye(4))
    nib.save(img, path)
    return path


@pytest.fixture(autouse=True)
def reset_nifti_wrapper_patch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure tests don't leak global monkey-patches between each other."""
    import datasets.features.nifti as ds_nifti

    original_init = ds_nifti.Nifti1ImageWrapper.__init__

    sentinel = "_BIDS_HUB_NIFTI_LAZY_LOADING_PATCH_APPLIED"
    monkeypatch.setattr(ds_nifti, sentinel, False, raising=False)
    monkeypatch.setattr(ds_nifti.Nifti1ImageWrapper, "__init__", original_init, raising=True)


def test_apply_nifti_lazy_loading_patch_is_idempotent() -> None:
    from bids_hub import apply_nifti_lazy_loading_patch

    assert apply_nifti_lazy_loading_patch() is True
    assert apply_nifti_lazy_loading_patch() is False


def test_decode_does_not_call_get_fdata_after_patch(
    nifti_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from datasets.features import Nifti

    from bids_hub import apply_nifti_lazy_loading_patch

    apply_nifti_lazy_loading_patch()

    def _boom(*args: object, **kwargs: object) -> None:
        raise AssertionError("get_fdata() must not be called during decode")

    monkeypatch.setattr(nib.nifti1.Nifti1Image, "get_fdata", _boom, raising=True)

    feature = Nifti()
    decoded = feature.decode_example(feature.encode_example(str(nifti_file)))
    assert decoded is not None


def test_dataobj_is_proxy_after_patch(nifti_file: Path) -> None:
    from datasets.features import Nifti

    from bids_hub import apply_nifti_lazy_loading_patch

    apply_nifti_lazy_loading_patch()

    feature = Nifti()
    decoded = feature.decode_example(feature.encode_example(str(nifti_file)))
    assert nib.is_proxy(decoded.dataobj)


def test_get_fdata_still_materializes_after_patch(nifti_file: Path) -> None:
    from datasets.features import Nifti

    from bids_hub import apply_nifti_lazy_loading_patch

    apply_nifti_lazy_loading_patch()

    feature = Nifti()
    decoded = feature.decode_example(feature.encode_example(str(nifti_file)))
    data = decoded.get_fdata()

    assert isinstance(data, np.ndarray)
    assert data.shape == (2, 3, 4)
