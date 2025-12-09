"""Generic file discovery utilities."""

from __future__ import annotations

from pathlib import Path


def find_single_nifti(search_dir: Path, pattern: str) -> str | None:
    """Find a single NIfTI file matching pattern."""
    if not search_dir.is_dir():
        return None
    matches = list(search_dir.rglob(pattern))
    if not matches:
        return None
    matches.sort(key=lambda p: p.name)
    return str(matches[0].resolve())


def find_all_niftis(search_dir: Path, pattern: str) -> list[str]:
    """Find all NIfTI files matching pattern."""
    if not search_dir.is_dir():
        return []
    matches = list(search_dir.rglob(pattern))
    matches.sort(key=lambda p: p.name)
    return [str(p.resolve()) for p in matches]
