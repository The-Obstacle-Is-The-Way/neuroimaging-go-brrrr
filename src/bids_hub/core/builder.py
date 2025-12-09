"""Core build and push functions."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
from datasets import Dataset, Features
from datasets.table import embed_table_storage
from huggingface_hub import HfApi
from tqdm.auto import tqdm

from .config import DatasetBuilderConfig

logger = logging.getLogger(__name__)


def validate_file_table_columns(
    file_table: pd.DataFrame,
    features: Features,
) -> None:
    """
    Validate that all columns defined in features exist in the file table.

    Args:
        file_table: DataFrame containing file paths and metadata.
        features: HF Features schema defining expected columns.

    Raises:
        ValueError: If any feature column is missing from the file table.
    """
    expected_columns = set(features.keys())
    actual_columns = set(file_table.columns)
    missing = expected_columns - actual_columns

    if missing:
        raise ValueError(
            f"File table is missing columns required by features: {sorted(missing)}. "
            f"Expected: {sorted(expected_columns)}, Got: {sorted(actual_columns)}"
        )


def build_hf_dataset(
    config: DatasetBuilderConfig,
    file_table: pd.DataFrame,
    features: Features,
) -> Dataset:
    """
    Build a Hugging Face Dataset from a pandas DataFrame with NIfTI file paths.

    This is the core generic function that converts a BIDS file table into an
    HF Dataset with properly typed columns (including Nifti columns).

    Args:
        config: Configuration containing BIDS root path and HF repo info.
            Currently reserved for API consistency; future versions may use
            this for resolving relative file paths against bids_root.
        file_table: DataFrame with one row per "example" containing:
            - One or more columns with NIfTI file paths (as strings)
            - Scalar metadata columns (subject_id, age, etc.)

            **Important**: All file paths in the DataFrame MUST be absolute paths.
            The HuggingFace datasets library requires absolute paths to locate
            and embed NIfTI files. Use `Path.resolve()` when building file tables
            to ensure paths are absolute.
        features: HF Features object defining the schema, including:
            - `Nifti()` for NIfTI image columns
            - `Value("string")`, `Value("float32")`, etc. for metadata

    Returns:
        A Hugging Face Dataset with columns cast to the specified features.

    Raises:
        ValueError: If file_table is missing columns required by features.

    Example:
        ```python
        from datasets import Features, Nifti, Value

        file_table = pd.DataFrame({
            "subject_id": ["sub-001", "sub-002"],
            "t1w": ["/abs/path/to/t1w_001.nii.gz", "/abs/path/to/t1w_002.nii.gz"],
            "age": [25.0, 30.0],
        })

        features = Features({
            "subject_id": Value("string"),
            "t1w": Nifti(),
            "age": Value("float32"),
        })

        ds = build_hf_dataset(config, file_table, features)
        ```
    """
    # Validate columns before processing
    validate_file_table_columns(file_table, features)

    # Select only the columns defined in features (in case file_table has extras)
    columns_to_use = list(features.keys())
    file_table_subset = file_table[columns_to_use].copy()

    # Create dataset from pandas DataFrame
    ds = Dataset.from_pandas(file_table_subset, preserve_index=False)

    # Cast columns to the specified features (this enables Nifti loading)
    ds = ds.cast(features)

    return ds


def push_dataset_to_hub(
    ds: Dataset,
    config: DatasetBuilderConfig,
    embed_external_files: bool = True,
    *,
    num_shards: int | None = None,
    private: bool = False,
    token: str | None = None,
    revision: str | None = None,
    commit_message: str | None = None,
) -> None:
    """
    Push a dataset to the Hugging Face Hub.

    This custom implementation supports sharded uploads for large datasets
    (like ARC-BIDS) and includes a workaround for huggingface/datasets#7894
    where `embed_table_storage` crashes on sharded `Sequence()` nested types.
    See: https://github.com/huggingface/datasets/issues/7894

    Assumes the user has already authenticated via `huggingface-cli login`
    or has set the HF_TOKEN environment variable.

    Args:
        ds: The Hugging Face Dataset to push.
        config: Configuration containing the target repo ID.
        embed_external_files: If True (default), NIfTI file contents are embedded
            into Parquet shards and uploaded to Hub. Required for datasets to be
            usable by others. Only set to False for local-only testing.
        num_shards: Number of Parquet shards to split the dataset into.
            Recommended for large datasets to prevent OOM during embedding.
            A good rule of thumb is one shard per example (subject/session).
        private: If True, create a private repository on the Hub.
        token: HuggingFace API token. If None, uses cached credentials.
        revision: Git branch to push to. If None (default), uses "main".
        commit_message: Custom commit message for standard (non-sharded) uploads.
    """

    # Use standard push_to_hub if we don't need heavy sharding logic
    if not num_shards or num_shards <= 1:
        ds.push_to_hub(
            config.hf_repo_id,
            embed_external_files=embed_external_files,
            private=private,
            token=token,
            revision=revision,
            commit_message=commit_message,
        )
        return

    # Memory-Efficient Custom Upload Loop
    logger.info(
        f"Starting memory-efficient push to {config.hf_repo_id} with {num_shards} shards..."
    )

    api = HfApi(token=token)
    api.create_repo(config.hf_repo_id, repo_type="dataset", private=private, exist_ok=True)

    split_name = config.split if config.split else "train"

    with tempfile.TemporaryDirectory() as tmpdir_root:
        tmp_path = Path(tmpdir_root)

        # 1. Upload Shards Sequentially
        for i in tqdm(range(num_shards), desc="Uploading Shards"):
            # Create the shard slice
            shard = ds.shard(num_shards=num_shards, index=i, contiguous=True)

            # Write shard to temporary Parquet file
            shard_fname = f"{split_name}-{i:05d}-of-{num_shards:05d}.parquet"
            local_parquet_path = tmp_path / shard_fname

            if embed_external_files:
                # WORKAROUND for huggingface/datasets#7894:
                # ds.shard() creates Arrow table slices that crash embed_table_storage
                # with SIGKILL on Sequence(Nifti()) columns. Converting to pandas and
                # back breaks the problematic slice references.
                # Remove this workaround when upstream PR #7896 is merged.
                # See: https://github.com/huggingface/datasets/issues/7894
                shard_df = shard.to_pandas()
                fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
                fresh_shard = fresh_shard.cast(ds.features)

                # Now get the clean Arrow table
                table = fresh_shard._data.table.combine_chunks()

                # Embed external files (NIfTIs) into the Arrow table
                embedded_table = embed_table_storage(table)

                # Write embedded table directly with PyArrow
                pq.write_table(embedded_table, str(local_parquet_path))

                # Clean up the intermediate objects
                del fresh_shard, shard_df
            else:
                # No embedding needed, use standard parquet writer
                shard.to_parquet(str(local_parquet_path))

            # Upload the shard immediately using HfApi
            # This streams the file from disk -> network, keeping RAM low.
            try:
                api.upload_file(
                    path_or_fileobj=str(local_parquet_path),
                    path_in_repo=f"data/{shard_fname}",
                    repo_id=config.hf_repo_id,
                    repo_type="dataset",
                    revision=revision,
                    commit_message=f"Upload shard {i + 1}/{num_shards}",
                )
            except Exception:
                logger.exception("Failed to upload shard %d", i)
                raise

            # Cleanup immediately to save disk space
            local_parquet_path.unlink()

            # Delete shard reference to allow garbage collection
            del shard

        # 2. Upload Metadata (dataset_info.json)
        logger.info("Generating and uploading dataset info...")
        ds.info.write_to_directory(str(tmp_path))

        # 'write_to_directory' usually creates 'dataset_info.json'
        # We check for it and upload it.
        info_files = list(tmp_path.glob("dataset_info.json"))
        if info_files:
            api.upload_file(
                path_or_fileobj=str(info_files[0]),
                path_in_repo="dataset_info.json",
                repo_id=config.hf_repo_id,
                repo_type="dataset",
                revision=revision,
                commit_message="Upload dataset metadata",
            )
        else:
            logger.warning(
                "dataset_info.json was not generated. The dataset may not load correctly. "
                "This can happen if the dataset has no features defined or is empty. "
                "To fix: ensure the dataset has rows and features are set via ds.cast(). "
                "You may need to manually upload a dataset_info.json file to the repository."
            )

    logger.info("Memory-efficient upload complete.")
