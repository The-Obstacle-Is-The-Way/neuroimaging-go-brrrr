# BUG-003: HuggingFace Hub Commit Rate Limit

## Status: FIXED

## Summary

When uploading large datasets with many shards (e.g., 902 parquet files for ARC), HuggingFace Hub's commit rate limit (320 commits/hour) causes uploads to fail partway through.

## Symptoms

- Upload progresses normally for ~320 shards
- Fails with `429 Too Many Requests` error
- Error message: "You have exceeded the rate limit for repository commits (320 per hour)"

## Root Cause

Our initial upload implementation made **1 commit per shard**:

```python
for i in range(num_shards):
    # Write shard
    shard.to_parquet(local_path)
    # Upload immediately (1 COMMIT)
    api.upload_file(local_path, ...)
```

For ARC (902 shards), this meant 902 commits → guaranteed to hit the 320/hour limit.

## Solution

Use `upload_large_folder()` which batches commits internally:

```python
# Phase 1: Write ALL shards to local staging folder
for i in range(num_shards):
    shard.to_parquet(staging_dir / f"train-{i:05d}.parquet")

# Phase 2: Bulk upload (HF batches commits internally)
api.upload_large_folder(
    repo_id=repo_id,
    folder_path=staging_dir,
    repo_type="dataset",
)
```

This reduces commits from 902 to ~10-20 (HF's internal batching).

## Implementation

The fix is in `src/bids_hub/core/builder.py`:

1. **Write-then-upload**: All shards written to `./hf_upload_staging/data/` first
2. **Bulk upload**: `upload_large_folder()` uploads everything at once
3. **Resume support**: Staging dir persists, so crashes can resume from where they left off
4. **Manual cleanup**: User must manually delete staging dir after verifying upload (see BUG-004)

## Disk Space Requirement

The write-then-upload approach requires temporary disk space for all shards:
- ARC dataset: ~270GB
- Verify with `df -h` before running

## Additional Fixes

This PR also includes the timeout fix from BUG-002:
- `DEFAULT_REQUEST_TIMEOUT` increased to 300s (5 minutes)
- Prevents `ReadTimeout` on large file dedup checks

## References

- HuggingFace error message suggests using `upload-large-folder`
- Commit: `6af639f` (fix(upload): use upload_large_folder to avoid 320/hour rate limit)

## Date

2025-12-14
