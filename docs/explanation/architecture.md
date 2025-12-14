# Architecture

> How the bids-hub module is designed and why.

---

## Module Structure

```text
src/bids_hub/
├── __init__.py              # Public API re-exports
├── cli.py                   # Typer CLI (bids-hub command)
├── core/                    # Generic BIDS→HF utilities
│   ├── __init__.py
│   ├── builder.py           # build_hf_dataset, push_dataset_to_hub
│   ├── config.py            # DatasetBuilderConfig dataclass
│   └── utils.py             # File discovery helpers
├── datasets/                # Per-dataset modules
│   ├── __init__.py
│   ├── arc.py               # ARC schema, file discovery, pipeline
│   └── isles24.py           # ISLES24 schema, file discovery, pipeline
└── validation/              # Per-dataset validation
    ├── __init__.py
    ├── base.py              # ValidationResult, ValidationCheck framework
    ├── arc.py               # ARC validation rules
    └── isles24.py           # ISLES24 validation rules
```

### Separation of Concerns

| Layer | Purpose | Examples |
|-------|---------|----------|
| `core/` | Dataset-agnostic utilities | `build_hf_dataset()`, `push_dataset_to_hub()` |
| `datasets/` | Dataset-specific schemas and file discovery | `build_arc_file_table()`, `get_isles24_features()` |
| `validation/` | Pre-upload data integrity checks | `validate_arc_download()`, expected counts |
| `cli.py` | User-facing commands | `bids-hub arc build`, `bids-hub isles24 validate` |

---

## Data Flow

```text
BIDS Dataset (Local)
        │
        ▼ build_*_file_table()
pandas DataFrame (paths + metadata)
        │
        ▼ build_hf_dataset()
datasets.Dataset with Nifti() features
        │
        ▼ push_dataset_to_hub(num_shards=N)
HuggingFace Hub (Parquet shards)
```

### Step-by-Step

1. **File Discovery**: `build_arc_file_table()` or `build_isles24_file_table()` scans the BIDS directory and returns a pandas DataFrame with absolute file paths and metadata.

2. **Dataset Creation**: `build_hf_dataset()` converts the DataFrame to a HuggingFace `Dataset`, casting columns to the appropriate `Features` (including `Nifti()` types).

3. **Hub Upload**: `push_dataset_to_hub()` handles the memory-efficient upload with explicit sharding and includes a workaround for the upstream `Sequence(Nifti())` crash bug.

---

## Design Decisions

### 1. Per-Session Rows (ARC) vs Per-Subject Rows (ISLES24)

**ARC**: One row per scanning session (902 rows for 230 subjects).
- ARC is longitudinal with multiple sessions per subject
- Sessions are independent data collection events
- Maps naturally to shards (one shard per session)

**ISLES24**: One row per subject (149 rows), flattening both sessions.
- ISLES24 has exactly 2 sessions per subject (Acute + Follow-up)
- Flattening simplifies ML pipelines (one row = one patient)
- All modalities accessible without nested indexing

### 2. Sequence Types for Multi-Run Modalities

ARC uses `Sequence(Nifti())` for modalities with multiple runs:
- `bold_naming40`/`bold_rest`: Multiple fMRI runs per session (split by task)
- `dwi`: Multiple diffusion runs per session (plus aligned gradients)
- `sbref`: Multiple single-band reference images

This preserves the full dataset structure rather than arbitrarily selecting one run.

### 3. Explicit `num_shards` Over `max_shard_size`

We force `num_shards=len(file_table)` instead of relying on `max_shard_size`:
- HuggingFace's size estimation is unreliable for external files
- Explicit sharding bounds memory usage predictably
- One shard per example aligns with logical data structure

### 4. Git-Based `datasets` Dependency

The stable PyPI release has bugs with `Nifti.embed_storage`. We pin to a specific GitHub commit:

```toml
[tool.uv.sources]
datasets = { git = "https://github.com/huggingface/datasets.git", rev = "0ec4d87d..." }
```

See [Why Uploads Fail](why-uploads-fail.md) for details.

### 5. Pandas Round-Trip Workaround

When sharding datasets with `Sequence(Nifti())` columns, Arrow slice references cause crashes. Our workaround:
```python
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
```
This breaks problematic slice references. See [Why Uploads Fail](why-uploads-fail.md).

---

## Adding a New Dataset

To add support for a new BIDS dataset:

1. **Create `datasets/newdataset.py`**:
   - Define `get_newdataset_features()` returning a `Features` schema
   - Define `build_newdataset_file_table()` returning a DataFrame
   - Define `build_and_push_newdataset()` orchestrating the pipeline

2. **Create `validation/newdataset.py`**:
   - Define expected counts from the source publication
   - Define `validate_newdataset_download()` using the base framework

3. **Update `cli.py`**:
   - Add a new Typer subcommand group
   - Wire up `build`, `validate`, and `info` commands

4. **Update exports**:
   - Add to `datasets/__init__.py`
   - Add to `validation/__init__.py`
   - Add to root `__init__.py`

---

## Related

- [Schema Specification](../reference/schema.md) - Dataset schemas
- [CLI Reference](../reference/cli.md) - Command-line interface
- [Why Uploads Fail](why-uploads-fail.md) - Upstream bug details
