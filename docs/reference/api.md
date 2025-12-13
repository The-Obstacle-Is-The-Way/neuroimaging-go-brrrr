# Python API Reference

> Module and function reference for the bids-hub package.

All public functions are re-exported from the top-level package:

```python
from bids_hub import (
    # Core
    DatasetBuilderConfig,
    build_hf_dataset,
    push_dataset_to_hub,
    # ARC
    build_arc_file_table,
    build_and_push_arc,
    get_arc_features,
    validate_arc_download,
    # ISLES24
    build_isles24_file_table,
    build_and_push_isles24,
    get_isles24_features,
    validate_isles24_download,
    # Validation
    ValidationResult,
)
```

---

## Core Module

### `DatasetBuilderConfig`

Configuration dataclass for BIDS-to-HuggingFace conversion.

```python
from bids_hub import DatasetBuilderConfig
from pathlib import Path

config = DatasetBuilderConfig(
    bids_root=Path("data/openneuro/ds004884"),
    hf_repo_id="hugging-science/arc-aphasia-bids",
    split="train",      # Optional, defaults to None
    dry_run=False,      # Skip Hub push if True
)
```

**Attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `bids_root` | `Path` | Path to the BIDS dataset root directory |
| `hf_repo_id` | `str` | HuggingFace Hub repository ID (e.g., `"org/name"`) |
| `split` | `str \| None` | Optional split name (e.g., `"train"`) |
| `dry_run` | `bool` | If `True`, skip pushing to Hub |

---

### `build_hf_dataset(config, file_table, features)`

Convert a pandas DataFrame to a HuggingFace Dataset.

```python
from bids_hub import build_hf_dataset, DatasetBuilderConfig

ds = build_hf_dataset(config, file_table, features)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `config` | `DatasetBuilderConfig` | Configuration object |
| `file_table` | `pd.DataFrame` | DataFrame with file paths and metadata |
| `features` | `datasets.Features` | Schema with `Nifti()`, `Value()`, etc. |

**Returns:** `datasets.Dataset`

---

### `push_dataset_to_hub(ds, config, **kwargs)`

Push a dataset to HuggingFace Hub with memory-efficient sharding.

```python
from bids_hub import push_dataset_to_hub

push_dataset_to_hub(
    ds,
    config,
    num_shards=902,           # Required for large datasets
    embed_external_files=True, # Embed NIfTI bytes (default)
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `ds` | `datasets.Dataset` | Dataset to push |
| `config` | `DatasetBuilderConfig` | Configuration with repo ID |
| `embed_external_files` | `bool` | Embed NIfTI bytes into Parquet (default: `True`) |
| `num_shards` | `int` | Number of Parquet shards (recommended for >10GB) |

**Note:** This function includes a workaround for [huggingface/datasets#7894](https://github.com/huggingface/datasets/issues/7894).

---

## ARC Module

### `build_arc_file_table(bids_root)`

Build a file table for the ARC dataset.

```python
from bids_hub import build_arc_file_table
from pathlib import Path

file_table = build_arc_file_table(Path("data/openneuro/ds004884"))
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `bids_root` | `Path` | Path to the ARC BIDS dataset root |

**Returns:** `pd.DataFrame` with columns:

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | `str` | BIDS subject ID (e.g., `"sub-M2001"`) |
| `session_id` | `str` | BIDS session ID (e.g., `"ses-1"`) |
| `t1w` | `str \| None` | Absolute path to T1w NIfTI |
| `t2w` | `str \| None` | Absolute path to T2w NIfTI |
| `t2w_acquisition` | `str \| None` | T2w acquisition type (`space_2x`, `space_no_accel`, `turbo_spin_echo`) |
| `flair` | `str \| None` | Absolute path to FLAIR NIfTI |
| `bold` | `list[str] \| None` | List of paths to BOLD fMRI NIfTIs |
| `dwi` | `list[str] \| None` | List of paths to DWI NIfTIs |
| `sbref` | `list[str] \| None` | List of paths to sbref NIfTIs |
| `lesion` | `str \| None` | Absolute path to lesion mask NIfTI |
| `age_at_stroke` | `float \| None` | Age at stroke |
| `sex` | `str \| None` | Biological sex |
| `wab_aq` | `float \| None` | WAB Aphasia Quotient |
| `wab_type` | `str \| None` | Aphasia type classification |

---

### `get_arc_features()`

Get the HuggingFace Features schema for ARC.

```python
from bids_hub import get_arc_features

features = get_arc_features()
# Returns Features with 14 columns (7 imaging, 1 acquisition type, 4 demographic, 2 identifiers)
```

**Returns:** `datasets.Features`

---

### `build_and_push_arc(config)`

High-level pipeline: build file table, create dataset, push to Hub.

```python
from bids_hub import build_and_push_arc, DatasetBuilderConfig
from pathlib import Path

config = DatasetBuilderConfig(
    bids_root=Path("data/openneuro/ds004884"),
    hf_repo_id="hugging-science/arc-aphasia-bids",
    dry_run=False,
)

build_and_push_arc(config)
```

---

### `validate_arc_download(bids_root, **kwargs)`

Validate an ARC dataset download against expected counts.

```python
from bids_hub import validate_arc_download
from pathlib import Path

result = validate_arc_download(
    Path("data/openneuro/ds004884"),
    tolerance=0.0,       # Allowed fraction of missing files
    sample_size=10,      # NIfTI files to spot-check
)

if result.all_passed:
    print("Ready for upload!")
else:
    print(result.summary())
```

**Returns:** `ValidationResult`

---

## ISLES24 Module

### `build_isles24_file_table(bids_root)`

Build a file table for the ISLES24 dataset.

```python
from bids_hub import build_isles24_file_table
from pathlib import Path

file_table = build_isles24_file_table(Path("data/zenodo/isles24/train"))
```

**Returns:** `pd.DataFrame` with columns for both sessions (Acute + Follow-up) flattened into one row per subject.

---

### `get_isles24_features()`

Get the HuggingFace Features schema for ISLES24.

```python
from bids_hub import get_isles24_features

features = get_isles24_features()
# Returns Features with 18 columns
```

**Returns:** `datasets.Features`

---

### `build_and_push_isles24(config)`

High-level pipeline for ISLES24.

```python
from bids_hub import build_and_push_isles24, DatasetBuilderConfig
from pathlib import Path

config = DatasetBuilderConfig(
    bids_root=Path("data/zenodo/isles24/train"),
    hf_repo_id="hugging-science/isles24-stroke",
    dry_run=False,
)

build_and_push_isles24(config)
```

---

### `validate_isles24_download(bids_root, **kwargs)`

Validate an ISLES24 dataset download.

```python
from bids_hub import validate_isles24_download
from pathlib import Path

result = validate_isles24_download(
    Path("data/zenodo/isles24/train"),
    tolerance=0.1,  # 10% tolerance (some subjects have missing modalities)
)
```

**Returns:** `ValidationResult`

---

## Validation Module

### `ValidationResult`

Result object from validation functions.

```python
@dataclass
class ValidationResult:
    bids_root: Path
    checks: list[ValidationCheck]

    @property
    def all_passed(self) -> bool: ...

    @property
    def passed_count(self) -> int: ...

    @property
    def failed_count(self) -> int: ...

    def summary(self) -> str: ...
```

**Usage:**

```python
result = validate_arc_download(path)

print(f"Passed: {result.passed_count}")
print(f"Failed: {result.failed_count}")
print(result.summary())
```

---

## Related

- [CLI Reference](cli.md) - Command-line interface
- [Schema Specification](schema.md) - Dataset schemas
- [Architecture](../explanation/architecture.md) - Design rationale
