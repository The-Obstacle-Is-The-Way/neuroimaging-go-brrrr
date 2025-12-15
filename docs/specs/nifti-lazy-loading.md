# NIfTI Lazy Loading Patch (bids_hub)

**Status:** RFC  
**Author:** @The-Obstacle-Is-The-Way  
**Date:** 2025-12-14

---

## Summary

This repo ships an opt-in runtime patch that prevents eager NIfTI voxel materialization when the
`datasets` dependency decodes NIfTI values.

**SSOT implementation:** `src/bids_hub/patches/nifti_lazy.py`

---

## Problem

When a NIfTI value is decoded, the `datasets` dependency wraps a nibabel image using a wrapper that
calls `get_fdata()` during construction. This eagerly materializes the full voxel array in RAM
(float64 by default), which defeats lazy-loading workflows.

Typical reproduction (consumption):

```python
from datasets import load_dataset

ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")
img = ds[0]["t1w"]  # decoding happens when the example is materialized
```

### What “lazy” means here (precise)

This patch makes voxel *materialization* lazy:

- Decoding returns an image whose `dataobj` is typically a nibabel proxy (lazy).
- Voxels are materialized only when the user calls `img.get_fdata()` or indexes `img.dataobj[...]`.

Notes:

- For `.nii` files, nibabel can often memory-map and read lazily.
- For `.nii.gz`, slice access may still require reading/decompressing more than the requested slice
  (gzip is not random-access friendly), but this still avoids eager full-array conversion/caching.

---

## Solution (This Repo)

Add an opt-in monkey-patch function:

- `bids_hub.apply_nifti_lazy_loading_patch()`
- idempotent: returns `True` when applied, `False` if already applied
- does not run on import (caller must opt in)

Implementation detail:

- Monkey-patch `datasets.features.nifti.Nifti1ImageWrapper.__init__` to pass
  `dataobj=nifti_image.dataobj` instead of `nifti_image.get_fdata()`.

---

## Files

- `src/bids_hub/patches/__init__.py`: re-exports patch functions
- `src/bids_hub/patches/nifti_lazy.py`: implements `apply_nifti_lazy_loading_patch()`
- `src/bids_hub/__init__.py`: re-exports `apply_nifti_lazy_loading_patch` for convenience
- `tests/test_patches.py`: verifies correctness and prevents regressions

---

## Usage

```python
from bids_hub import apply_nifti_lazy_loading_patch
from datasets import load_dataset

apply_nifti_lazy_loading_patch()

ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")
img = ds[0]["t1w"]  # now lazy: dataobj is a proxy, not a full ndarray

# Voxels only load when explicitly requested
data = img.get_fdata()
```

---

## Tests (This Repo)

`tests/test_patches.py` must prove (deterministically, without RSS/memory heuristics):

- Patch is idempotent (`True` then `False`)
- After patch, decoding a local `.nii.gz` does not call `get_fdata()` (monkeypatch `get_fdata` to
  raise)
- After patch, `decoded.dataobj` is a proxy (`nib.is_proxy(...)`)
- After patch, `decoded.get_fdata()` still returns a `np.ndarray`

---

## Non-goals / Known Limitations

- This does not implement a local BIDS loader.
- This does not guarantee random-access slice reads for `.nii.gz` (gzip limitations).
- NIfTI-2 is not addressed here; the bytes-based decode path may not support it.
