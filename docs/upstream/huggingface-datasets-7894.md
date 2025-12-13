# Upstream Dependency Bug: HuggingFace datasets#7894

> **This is NOT a bug in this repository.** This documents a bug in our upstream dependency (`huggingface/datasets`) that we work around in our code.

**Status**: Workaround implemented in `src/bids_hub/core/builder.py`
**Upstream Issue**: https://github.com/huggingface/datasets/issues/7894
**Upstream Fix PR**: https://github.com/huggingface/datasets/pull/7896

---

## TL;DR

The HuggingFace `datasets` library crashes (SIGKILL) when uploading sharded datasets with `Sequence(Nifti())` columns. We pin to a specific commit and use a pandas workaround until the upstream fix is merged.

---

## Why This Matters to Us

This repo uploads BIDS neuroimaging datasets to HuggingFace Hub. Our schema uses `Sequence(Nifti())` for columns like `bold` and `dwi` (multiple runs per session). Without the workaround, uploads crash at 0%.

---

## Our Workaround

**Location:** `src/bids_hub/core/builder.py`

```python
# Break Arrow slice references that cause the crash
shard_df = shard.to_pandas()
fresh_shard = Dataset.from_pandas(shard_df, preserve_index=False)
fresh_shard = fresh_shard.cast(ds.features)
```

**Dependency pin:** `pyproject.toml` pins `datasets` to a specific commit:
```toml
[tool.uv.sources]
datasets = { git = "https://github.com/huggingface/datasets.git", rev = "0ec4d87..." }
```

---

## The Upstream Bug

**Symptom:** `embed_table_storage` crashes with SIGKILL when processing sharded datasets containing `Sequence()` nested types.

**Root cause:** When `ds.shard()` creates a subset, the Arrow table retains internal slice references that crash during embedding of nested struct types.

**Key observations:**
- Full dataset embedding works fine
- Sharded/selected subsets crash
- Only manifests at scale (not with small synthetic data)

---

## When Can We Remove the Workaround?

Once upstream PR #7896 is merged and released:
1. Update `datasets` dependency to fixed version
2. Remove pandas workaround from `builder.py`
3. Delete this document

---

## References

- [Issue #7894](https://github.com/huggingface/datasets/issues/7894) - Our bug report
- [PR #7896](https://github.com/huggingface/datasets/pull/7896) - Our fix PR
- [Issue #5990](https://github.com/huggingface/datasets/issues/5990) - Related (2+ years open, 46 comments)
