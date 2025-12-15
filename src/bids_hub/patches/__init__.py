"""Opt-in runtime patches for third-party dependencies.

These patches are intentionally isolated (and not applied on import) to avoid
surprising side effects for downstream users.
"""

from __future__ import annotations

from .nifti_lazy import apply_nifti_lazy_loading_patch

__all__ = ["apply_nifti_lazy_loading_patch"]
