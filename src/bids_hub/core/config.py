"""Configuration dataclasses for BIDS→HF conversion."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class DatasetBuilderConfig:
    """
    Configuration for building a Hugging Face Dataset from BIDS data.

    Attributes:
        bids_root: Path to the root of the BIDS dataset directory.
        hf_repo_id: Hugging Face Hub repository ID (e.g., "username/dataset-name").
        split: Optional split name (e.g., "train", "test"). If None, no split is assigned.
        dry_run: If True, skip pushing to Hub (useful for testing).
    """

    bids_root: Path
    hf_repo_id: str
    split: str | None = None
    dry_run: bool = False
