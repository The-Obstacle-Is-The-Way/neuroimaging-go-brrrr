# Consumption Pipeline Gap Analysis

## Date: 2025-12-14

## Summary

This repo is **production-first**. Consumption works via the `datasets` dependency, with optional
opt-in patches for missing/undesired behaviors (e.g., NIfTI eager voxel materialization).

## Current State

| Feature | Status | Spec |
|---------|--------|------|
| Production (BIDS → Hub) | ✅ Complete | — |
| Hub consumption | ✅ Works via `datasets` | — |
| Lazy NIfTI loading | ✅ Optional patch | [docs/specs/nifti-lazy-loading.md](../specs/nifti-lazy-loading.md) |
| Local BIDS loader | ❌ Low priority | — |

## Next Steps

1. Keep patch coverage via `tests/test_patches.py`
2. Remove patches if/when dependency behavior no longer needs them
