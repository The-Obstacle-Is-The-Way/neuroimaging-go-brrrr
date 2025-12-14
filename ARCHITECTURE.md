# Architecture

> **neuroimaging-go-brrrr** is the canonical HuggingFace extension for NIfTI/BIDS neuroimaging datasets.

---

## What This Project Is

```
+-----------------------------------------------------------------------------+
|                    THE HUGGINGFACE ECOSYSTEM FOR NEUROIMAGING               |
+-----------------------------------------------------------------------------+

    pip install datasets              pip install neuroimaging-go-brrrr
    -----------------------           ---------------------------------
    Standard HuggingFace              THIS PROJECT: Domain extension
    - Images, text, audio             - NIfTI file support (.nii.gz)
    - Parquet/Arrow storage           - BIDS directory structure
    - Hub integration                 - Neuroimaging validation
                                      - Upload utilities for BIDS->Hub

    +-------------------------+       +----------------------------------+
    |   huggingface/datasets  |       |   neuroimaging-go-brrrr          |
    |   (upstream library)    | <---- |   (bids_hub module)              |
    |                         |       |                                  |
    |   - Dataset             |       |   - Nifti() feature type         |
    |   - Features            |       |   - BIDS file discovery          |
    |   - Hub upload/download |       |   - Parquet sharding workarounds |
    +-------------------------+       +----------------------------------+
              ^                                      |
              |                                      |
              +--------------------------------------+
                     We EXTEND this, we don't fork it

+-----------------------------------------------------------------------------+
|  KEY INSIGHT: When you pip install this package, you get:                   |
|  - datasets (the standard HuggingFace library)                              |
|  - huggingface-hub (for Hub interactions)                                   |
|  - bids_hub module (our neuroimaging-specific extensions)                   |
|                                                                             |
|  We are NOT waiting on PRs to huggingface/datasets.                         |
|  We ARE the canonical extension for neuroimaging.                           |
+-----------------------------------------------------------------------------+
```

---

## The Two Pipelines

This project handles both **production** (uploading) and enables **consumption** (downloading).

### Pipeline 1: Production (Uploading to HuggingFace)

```
+---------------+     +----------------------+     +---------------------+
|  Local BIDS   |     |  neuroimaging-go-    |     |   HuggingFace Hub   |
|  Directory    | --> |  brrrr (bids_hub)    | --> |   hugging-science/  |
|  (OpenNeuro)  |     |                      |     |   arc-aphasia-bids  |
+---------------+     |  - build_*_file_     |     +---------------------+
                      |    table()           |
                      |  - get_*_features()  |
                      |  - push_dataset_     |
                      |    to_hub()          |
                      +----------------------+

   Data Flow:
   1. Download BIDS dataset from OpenNeuro/Zenodo
   2. bids_hub scans directory, builds pandas DataFrame with paths + metadata
   3. Convert to HuggingFace Dataset with Nifti() feature types
   4. Upload sharded Parquet files to HuggingFace Hub
```

**CLI for production:**
```bash
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
uv run bids-hub isles24 build data/zenodo/isles24/train --no-dry-run
```

### Pipeline 2: Consumption (Training from HuggingFace)

```
+---------------------+     +----------------------+     +-------------------+
|   HuggingFace Hub   |     |  datasets.load_      |     |  Your ML Code     |
|   hugging-science/  | --> |  dataset()           | --> |  - Training       |
|   arc-aphasia-bids  |     |  (standard HF)       |     |  - Inference      |
+---------------------+     +----------------------+     +-------------------+

   Data Flow:
   1. Consumer calls datasets.load_dataset("hugging-science/arc-aphasia-bids")
   2. HuggingFace downloads Parquet shards to local cache
   3. Nifti() columns automatically decode to nibabel objects
   4. Standard Dataset API (filter, map, batch) works normally
```

**Python for consumption:**
```python
from datasets import load_dataset

ds = load_dataset("hugging-science/arc-aphasia-bids", split="train")
example = ds[0]
print(example["subject_id"])  # "sub-M2001"
print(example["t1w"])         # nibabel.Nifti1Image object
```

---

## Dependency Relationship

```
+-----------------------------------------------------------------------------+
|                         PACKAGE DEPENDENCIES                                |
+-----------------------------------------------------------------------------+

   Downstream Consumer (e.g., arc-meshchop)
        |
        |  pip install neuroimaging-go-brrrr
        v
   +-----------------------------------+
   |   neuroimaging-go-brrrr           |
   |   (this repo)                     |
   |   - bids_hub module               |
   |   - CLI: bids-hub                 |
   +-----------------------------------+
        |
        |  automatically installs
        v
   +-----------------------------------+
   |   huggingface/datasets            |
   |   (upstream library)              |
   |   - Dataset, Features, Nifti      |
   |   - Hub upload/download           |
   +-----------------------------------+
        |
        |  automatically installs
        v
   +-----------------------------------+
   |   huggingface/huggingface_hub     |
   |   - HfApi                         |
   |   - upload_large_folder           |
   +-----------------------------------+
```

---

## Module Structure

```
src/bids_hub/
|-- __init__.py          # Public API re-exports
|-- cli.py               # Typer CLI (bids-hub command)
|-- core/                # Generic BIDS->HF utilities
|   |-- builder.py       # build_hf_dataset, push_dataset_to_hub
|   |-- config.py        # DatasetBuilderConfig dataclass
|   +-- utils.py         # File discovery helpers
|-- datasets/            # Per-dataset modules
|   |-- arc.py           # ARC schema, file discovery, pipeline
|   +-- isles24.py       # ISLES24 schema, file discovery, pipeline
+-- validation/          # Per-dataset validation
    |-- base.py          # ValidationResult, ValidationCheck framework
    |-- hf.py            # HuggingFace dataset validation helpers
    |-- arc.py           # ARC validation rules
    +-- isles24.py       # ISLES24 validation rules
```

### Layer Responsibilities

| Layer | Purpose | Key Functions |
|-------|---------|---------------|
| `core/` | Dataset-agnostic | `build_hf_dataset()`, `push_dataset_to_hub()` |
| `datasets/` | Dataset-specific schemas | `build_arc_file_table()`, `get_isles24_features()` |
| `validation/` | Data integrity checks | `validate_arc_download()`, expected counts |
| `cli.py` | User-facing commands | `bids-hub arc build`, `bids-hub isles24 validate` |

---

## Data Flow Detail

```
+-----------------------------------------------------------------------------+
|                              DATA FLOW                                      |
+-----------------------------------------------------------------------------+

   BIDS Dataset (Local)
         |
         |  build_*_file_table()
         |  - Scan BIDS directory structure
         |  - Extract metadata from sidecars
         |  - Return pandas DataFrame with absolute paths
         v
   +-----------------------------------+
   |  pandas DataFrame                 |
   |  - subject_id, session_id         |
   |  - t1w, t2w, flair (file paths)   |
   |  - metadata columns               |
   +-----------------------------------+
         |
         |  build_hf_dataset()
         |  - Convert DataFrame to Dataset
         |  - Cast columns to Features schema
         |  - Nifti() columns store file paths
         v
   +-----------------------------------+
   |  datasets.Dataset                 |
   |  - Nifti() feature types          |
   |  - Ready for embedding            |
   +-----------------------------------+
         |
         |  push_dataset_to_hub()
         |  - Shard dataset (1 per session)
         |  - Embed NIfTI bytes into Parquet
         |  - Upload via upload_large_folder()
         v
   +-----------------------------------+
   |  HuggingFace Hub                  |
   |  - Parquet shards with embedded   |
   |    NIfTI bytes                    |
   |  - Dataset card + metadata        |
   +-----------------------------------+
```

---

## Why We Exist

### The Problem

HuggingFace `datasets` natively supports images (JPEG, PNG), audio (WAV, MP3), and text.
It does NOT natively handle neuroimaging formats:

| Standard ML | Neuroimaging (BIDS) |
|-------------|---------------------|
| Images: JPEG, PNG | Images: NIfTI (.nii.gz) |
| Format: 2D arrays | Format: 3D/4D volumes + headers |
| Size: KB per image | Size: 50-200 MB per scan |
| Metadata: filename | Metadata: BIDS sidecar JSONs |
| Structure: flat folders | Structure: sub-*/ses-*/anat/ |

### The Solution

We extend HuggingFace datasets with:

1. **Nifti() Feature Type**: Native support for .nii.gz files
2. **BIDS File Discovery**: Automatic parsing of BIDS directory structures
3. **Sharded Upload**: Memory-efficient upload of large neuroimaging datasets
4. **Validation Framework**: Pre-upload checks against expected counts

---

## Upstream Workarounds

We include workarounds for upstream bugs that affect neuroimaging use cases:

| Bug | Workaround | Location |
|-----|------------|----------|
| Sequence(Nifti()) crashes during shard | Pandas round-trip | `core/builder.py` |
| Upload timeout on large files | Extended timeout | `core/builder.py` |
| Rate limit on many shards | `upload_large_folder()` | `core/builder.py` |

See [docs/bugs/](docs/bugs/) for detailed documentation.

---

## Adding a New Dataset

1. **Create `datasets/newdataset.py`**:
   - Define `get_newdataset_features()` returning a Features schema
   - Define `build_newdataset_file_table()` returning a DataFrame
   - Define `build_and_push_newdataset()` orchestrating the pipeline

2. **Create `validation/newdataset.py`**:
   - Define expected counts from source publication
   - Define `validate_newdataset_download()` using base framework

3. **Update `cli.py`**:
   - Add new Typer subcommand group
   - Wire up `build`, `validate`, and `info` commands

4. **Update exports**:
   - Add to `datasets/__init__.py`
   - Add to `validation/__init__.py`
   - Add to root `__init__.py`

---

## Related Documentation

- [README.md](README.md) - Quick start guide
- [docs/explanation/architecture.md](docs/explanation/architecture.md) - Detailed design decisions
- [docs/reference/schema.md](docs/reference/schema.md) - Dataset schemas
- [docs/bugs/](docs/bugs/) - Known issues and workarounds
