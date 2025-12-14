"""
Command-line interface for uploading BIDS datasets to HuggingFace Hub.

Usage:
    # Show help
    bids-hub --help

    # ARC Commands
    bids-hub arc validate data/openneuro/ds004884
    bids-hub arc build data/openneuro/ds004884 --dry-run
    bids-hub arc info

    # ISLES24 Commands
    bids-hub isles24 validate data/zenodo/isles24/train
    bids-hub isles24 build data/zenodo/isles24/train --dry-run
    bids-hub isles24 info

    # List supported datasets
    bids-hub list
"""

from __future__ import annotations

from pathlib import Path

import typer

from .core import DatasetBuilderConfig
from .datasets.arc import build_and_push_arc
from .datasets.isles24 import build_and_push_isles24
from .validation import (
    validate_arc_download,
    validate_arc_hf_from_hub,
    validate_isles24_download,
)

app = typer.Typer(
    name="bids-hub",
    help="Upload neuroimaging datasets (ARC, ISLES24) to HuggingFace Hub.",
    add_completion=False,
)

# --- ARC Subcommand Group ---
arc_app = typer.Typer(
    help="ARC (Aphasia Recovery Cohort) dataset commands.\n\n"
    "Source: OpenNeuro ds004884\n"
    "License: CC0 (Public Domain)"
)
app.add_typer(arc_app, name="arc")

# --- ISLES'24 Subcommand Group ---
isles_app = typer.Typer(help="Commands for the ISLES'24 dataset.")
app.add_typer(isles_app, name="isles24")


# --- Global Commands ---
@app.command("list")
def list_datasets() -> None:
    """List all supported datasets."""
    typer.echo("Supported datasets:")
    typer.echo("  arc     - Aphasia Recovery Cohort (OpenNeuro ds004884)")
    typer.echo("  isles24 - ISLES 2024 Stroke (Zenodo)")


# --- ARC Commands ---
@arc_app.command("build")
def build_arc(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ARC BIDS root directory (ds004884).",
        exists=False,
    ),
    hf_repo: str = typer.Option(
        "hugging-science/arc-aphasia-bids",
        "--hf-repo",
        "-r",
        help="HuggingFace dataset repo ID.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="If true (default), build dataset but do not push to Hub.",
    ),
) -> None:
    """
    Build (and optionally push) the ARC HF dataset.
    """
    config = DatasetBuilderConfig(
        bids_root=bids_root,
        hf_repo_id=hf_repo,
        dry_run=dry_run,
    )

    typer.echo(f"Processing ARC dataset from: {bids_root}")
    typer.echo(f"Target HF repo: {hf_repo}")
    typer.echo(f"Dry run: {dry_run}")

    build_and_push_arc(config)

    if dry_run:
        typer.echo("Dry run complete. Dataset built but not pushed.")
    else:
        typer.echo(f"Dataset pushed to: https://huggingface.co/datasets/{hf_repo}")


@arc_app.command("validate")
def validate_arc(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ARC BIDS root directory (ds004884).",
    ),
    run_bids_validator: bool = typer.Option(
        False,
        "--bids-validator/--no-bids-validator",
        help="Run external BIDS validator (requires npx, slow on large datasets).",
    ),
    sample_size: int = typer.Option(
        10,
        "--sample-size",
        "-n",
        help="Number of NIfTI files to spot-check for integrity.",
    ),
    tolerance: float = typer.Option(
        0.0,
        "--tolerance",
        "-t",
        min=0.0,
        max=1.0,
        help="Allowed fraction of missing files (0.0 to 1.0). Default 0.0 (strict).",
    ),
) -> None:
    """
    Validate an ARC dataset download before pushing to HuggingFace.

    Checks:
    - Required BIDS files exist (dataset_description.json, participants.tsv)
    - Subject count matches expected (~230 from Sci Data paper)
    - Series counts match paper (T1w: 441, T2w: 447, FLAIR: 235)
    - Sample NIfTI files are loadable with nibabel
    - (Optional) External BIDS validator passes

    Run this after downloading to ensure data integrity before HF push.

    Example:
        bids-hub arc validate data/openneuro/ds004884
    """
    result = validate_arc_download(
        bids_root,
        run_bids_validator=run_bids_validator,
        nifti_sample_size=sample_size,
        tolerance=tolerance,
    )

    typer.echo(result.summary())

    if not result.all_passed:
        raise typer.Exit(code=1)


@arc_app.command("validate-hf")
def validate_arc_hf_cmd(
    repo_id: str = typer.Option(
        "hugging-science/arc-aphasia-bids",
        "--repo",
        "-r",
        help="HuggingFace dataset repository ID.",
    ),
    split: str = typer.Option(
        "train",
        "--split",
        "-s",
        help="Dataset split to validate.",
    ),
    sample_size: int = typer.Option(
        5,
        "--sample-size",
        "-n",
        help="Number of NIfTI files to spot-check for integrity.",
    ),
    skip_nifti: bool = typer.Option(
        False,
        "--skip-nifti",
        help="Skip NIfTI loadability checks (faster).",
    ),
) -> None:
    """
    Validate an ARC dataset downloaded from HuggingFace Hub.

    Checks that the HF dataset matches SSOT (OpenNeuro ds004884):
    - Schema has expected 19 columns
    - Row count matches (902 sessions)
    - Subject count matches (230 subjects)
    - Modality counts match (T1w, T2w, FLAIR, BOLD, DWI, lesion, etc.)
    - DWI gradients are aligned (dwi, bvals, bvecs same length)
    - (Optional) Sample NIfTI files are loadable

    Use this after loading the dataset to verify data integrity.

    Example:
        bids-hub arc validate-hf
        bids-hub arc validate-hf --repo my-org/arc-copy --skip-nifti
    """
    typer.echo(f"Validating HuggingFace dataset: {repo_id} (split={split})")
    typer.echo("Loading dataset from Hub (this may take a moment)...")

    result = validate_arc_hf_from_hub(
        repo_id=repo_id,
        split=split,
        nifti_sample_size=sample_size,
        check_nifti=not skip_nifti,
    )

    typer.echo(result.summary())

    if not result.passed:
        raise typer.Exit(code=1)


@arc_app.command("info")
def info_arc() -> None:
    """
    Show information about the ARC dataset.
    """
    typer.echo("Aphasia Recovery Cohort (ARC)")
    typer.echo("=" * 40)
    typer.echo("OpenNeuro ID: ds004884")
    typer.echo("URL: https://openneuro.org/datasets/ds004884")
    typer.echo("License: CC0 (Public Domain)")
    typer.echo("")
    typer.echo("Contains:")
    typer.echo("  - 230 chronic stroke patients")
    typer.echo("  - 902 scanning sessions")
    typer.echo("  - T1w, T2w, FLAIR, diffusion, fMRI")
    typer.echo("  - Expert lesion masks")
    typer.echo("  - WAB (Western Aphasia Battery) scores")
    typer.echo("")
    typer.echo("Expected series counts (from Sci Data paper):")
    typer.echo("  - T1w: 441 series")
    typer.echo("  - T2w: 447 series")
    typer.echo("  - FLAIR: 235 series")
    typer.echo("  - Lesion masks: 230")


# --- ISLES'24 Commands ---
@isles_app.command("build")
def build_isles(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ISLES'24 BIDS root directory (train/).",
        exists=False,
    ),
    hf_repo: str = typer.Option(
        "hugging-science/isles24-stroke",
        "--hf-repo",
        "-r",
        help="HuggingFace dataset repo ID.",
    ),
    dry_run: bool = typer.Option(
        True,
        "--dry-run/--no-dry-run",
        help="If true (default), build dataset but do not push to Hub.",
    ),
) -> None:
    """
    Build (and optionally push) the ISLES'24 HF dataset.
    """
    config = DatasetBuilderConfig(
        bids_root=bids_root,
        hf_repo_id=hf_repo,
        dry_run=dry_run,
    )

    typer.echo(f"Processing ISLES'24 dataset from: {bids_root}")
    typer.echo(f"Target HF repo: {hf_repo}")
    typer.echo(f"Dry run: {dry_run}")

    build_and_push_isles24(config)

    if dry_run:
        typer.echo("Dry run complete. Dataset built but not pushed.")
    else:
        typer.echo(f"Dataset pushed to: https://huggingface.co/datasets/{hf_repo}")


@isles_app.command("validate")
def validate_isles(
    bids_root: Path = typer.Argument(
        ...,
        help="Path to ISLES'24 root directory (e.g., train/).",
    ),
    sample_size: int = typer.Option(
        10,
        "--sample-size",
        "-n",
        help="Number of NIfTI files to spot-check for integrity.",
    ),
    tolerance: float = typer.Option(
        0.1,
        "--tolerance",
        "-t",
        min=0.0,
        max=1.0,
        help="Allowed fraction of missing files (0.0 to 1.0). Default 0.1 (10%).",
    ),
) -> None:
    """
    Validate an ISLES24 dataset download.

    Checks:
    - Zero-byte file detection (fast corruption check)
    - Required files exist (clinical_data-description.xlsx)
    - Required directories exist (raw_data/, derivatives/, phenotype/)
    - Subject count matches expected (~149 from Zenodo v7)
    - Modality counts match expected (NCCT, CTA, DWI, lesion masks)
    - Sample NIfTI files are loadable with nibabel
    - Phenotype XLSX files are readable

    Example:
        bids-hub isles24 validate data/zenodo/isles24/train
    """
    result = validate_isles24_download(
        bids_root,
        nifti_sample_size=sample_size,
        tolerance=tolerance,
    )

    typer.echo(result.summary())

    if not result.all_passed:
        raise typer.Exit(code=1)


@isles_app.command("info")
def info_isles() -> None:
    """
    Show information about the ISLES'24 dataset.
    """
    typer.echo("ISLES 2024 Stroke Dataset")
    typer.echo("=" * 40)
    typer.echo("Source: Zenodo (Record 17652035)")
    typer.echo("License: CC BY-NC-SA 4.0")
    typer.echo("")
    typer.echo("Contains:")
    typer.echo("  - 149 subjects (Acute + Follow-up)")
    typer.echo("  - Acute: NCCT, CTA, CTP")
    typer.echo("  - Follow-up: DWI, ADC")
    typer.echo("  - Lesion Segmentation Masks")


if __name__ == "__main__":
    app()
