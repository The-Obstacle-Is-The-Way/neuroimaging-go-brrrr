# BUG-004: Premature Staging Directory Deletion During Upload Retries

## Status: FIXED

## Summary

The `push_dataset_to_hub()` function was deleting the staging directory immediately after `upload_large_folder()` returned, but `upload_large_folder()` returns before all internal retries complete. This caused file-not-found errors when HuggingFace's retry mechanism tried to re-upload failed batches.

## Symptoms

- Upload appears to start successfully
- After some time, errors appear: "Failed to commit 20 files at once. Will retry with less files in next batch."
- Followed by: `[Errno 2] No such file or directory: '...parquet'`
- Partial upload: some shards make it to HuggingFace, others don't

## Root Cause

Our code did this:

```python
api.upload_large_folder(
    repo_id=config.hf_repo_id,
    folder_path=str(staging_dir),
    ...
)

# BUG: Deleted immediately after upload_large_folder() returned
shutil.rmtree(staging_dir)
```

The problem is that `upload_large_folder()`:
1. Returns before all upload operations complete
2. Has internal retry logic that runs asynchronously
3. When retries fail, it tries again with smaller batches

When our `shutil.rmtree()` ran, HuggingFace's retry workers were still trying to upload files that no longer existed.

## Impact

- 599/902 shards uploaded before staging was deleted
- 303 shards lost (need to regenerate from source BIDS data)
- ~90GB of data needs to be re-embedded and re-uploaded

## Solution

**Do NOT auto-delete the staging directory.** Instead, log instructions for manual verification and cleanup:

```python
logger.info("Upload command completed!")
logger.info("IMPORTANT: Verify upload before deleting staging directory:")
logger.info(f"  1. Check HuggingFace repo")
logger.info(f"  2. Verify all {num_shards} shards are present")
logger.info(f"  3. Then manually delete: rm -rf {staging_dir}")
```

This ensures:
1. User can verify all files uploaded successfully
2. If upload failed, staging dir is preserved for resume
3. No race condition with internal HF retry logic

## Lessons Learned

1. **Never assume a function is fully synchronous** - even if docs say it's blocking, verify behavior
2. **Cleanup of large artifacts should be manual** - especially for multi-hour operations
3. **gitignore ≠ protection from deletion** - gitignore only affects git tracking, not filesystem operations

## References

- Commit: `[pending]`

## Date

2025-12-14
