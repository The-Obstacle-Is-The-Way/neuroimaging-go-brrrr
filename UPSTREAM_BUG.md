# Upstream Bug: huggingface/datasets#7894

**Status**: OPEN - Workaround implemented, upstream PR pending
**Last Updated**: 2025-12-05

---

## Summary

`embed_table_storage` crashes with SIGKILL when processing sharded datasets
containing `Sequence()` nested types like `Sequence(Nifti())`.

| Item | Link |
|------|------|
| Issue | https://github.com/huggingface/datasets/issues/7894 |
| Fix PR | https://github.com/huggingface/datasets/pull/7896 |
| Reproduction | https://github.com/The-Obstacle-Is-The-Way/bids-hub/tree/sandbox/reproduce-bug-7894 |

---

## Symptom

Upload crashes at 0% with:
- Exit code 137 (SIGKILL)
- "semaphore leak" warning
- No Python traceback (C++ level crash)

---

## Root Cause

When `ds.shard()` or `ds.select()` creates a subset, the resulting Arrow table
retains internal slice references. When `embed_table_storage` processes nested
struct types like `Sequence(Nifti())`, these references cause a crash.

**Key observations:**
- Full dataset embedding works fine
- Sharded/selected subsets crash
- Crashes even with empty `Sequence([])`
- Single (non-Sequence) Nifti columns work fine
- Only manifests at scale (not with small synthetic data)

---

## Workaround (in our codebase)

Convert shard to pandas and recreate the Dataset to break problematic references:

```python
shard = ds.shard(num_shards=num_shards, index=i, contiguous=True)

# Break Arrow slice references
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
fresh_shard = fresh_shard.cast(ds.features)

# Now embedding works
table = fresh_shard._data.table.combine_chunks()
embedded_table = embed_table_storage(table)
```

See: `src/bids_hub/core/builder.py` (search for "pandas workaround")

---

## Minimal Reproduction

```python
from datasets import Dataset, Features, Sequence, Value
from datasets.features import Nifti
from datasets.table import embed_table_storage

features = Features({
    "id": Value("string"),
    "images": Sequence(Nifti()),
})

ds = Dataset.from_dict({
    "id": ["a", "b"],
    "images": [["/path/to/file.nii.gz"], []],
}).cast(features)

# This works:
table = ds._data.table.combine_chunks()
embedded = embed_table_storage(table)  # OK

# This crashes:
shard = ds.shard(num_shards=2, index=0)
shard_table = shard._data.table.combine_chunks()
embedded = embed_table_storage(shard_table)  # SIGKILL
```

**Note:** This only reproduces at scale with real data (~273GB). Synthetic small
files don't trigger the crash.

---

## Environment

- macOS ARM64
- Python 3.13
- PyArrow 22.0.0
- datasets 4.4.2.dev0 (git main)

---

## Related Issues

| Issue | Title | Status | Notes |
|-------|-------|--------|-------|
| #7894 | embed_table_storage crashes on sharded Sequence() | OPEN | Our bug |
| #7896 | Fix: force contiguous copy for sliced list arrays | OPEN | Our fix PR |
| #5990 | Pushing large dataset hangs | OPEN | 2+ years, 46 comments, related symptoms |

---

## Closed Investigation: #7893 (OOM)

We initially filed #7893 claiming `push_to_hub` had memory accumulation issues.
After investigation, we determined this was **invalid**:

- The `free_memory=True` default in `preupload_lfs_files()` prevents accumulation
- We were misdiagnosing #7894 crashes as OOM
- Issue #7893 was closed with acknowledgment

The `gc.collect()` calls we added for #7893 have been removed from our codebase.

---

## Next Steps

1. Wait for upstream PR #7896 to be reviewed/merged
2. When merged, update `datasets` dependency to fixed version
3. Remove pandas workaround from `src/bids_hub/core/builder.py`
4. Consider switching to standard `push_to_hub` entirely
