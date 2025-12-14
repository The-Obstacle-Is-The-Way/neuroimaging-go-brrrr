# BUG-004: Premature Staging Directory Deletion During Upload Retries

## Status: FIXED

## Environment

```
Python: 3.13.5
huggingface_hub: 1.2.1
datasets: 4.4.2.dev0
```

## Summary

The `push_dataset_to_hub()` function was deleting the staging directory immediately after `upload_large_folder()` returned. We **observed** that file-not-found errors occurred during what appeared to be ongoing retry operations, suggesting the function returned while upload operations were still in progress.

**Note:** Per `huggingface_hub==1.2.1` documentation, `upload_large_folder()` is implemented as a blocking loop that joins worker threads and should not return before retries complete. The observed behavior may indicate:
- An upstream bug or async backend behavior
- Environment-specific behavior (hf_xet, HF_* env vars)
- A race condition we haven't fully characterized

Regardless of root cause, the fix (no auto-deletion) is the correct safety measure.

## Symptoms

- Upload appears to start successfully
- After some time, errors appear: "Failed to commit 20 files at once. Will retry with less files in next batch."
- Followed by: `[Errno 2] No such file or directory: '...parquet'`
- Partial upload: some shards make it to HuggingFace, others don't

## Root Cause (Observed)

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

We observed that after `upload_large_folder()` returned:
1. Retry-related log messages continued to appear
2. These retries attempted to read files that no longer existed
3. This resulted in `[Errno 2]` errors and partial uploads

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
logger.info(f"  3. Then manually delete: rm -rf '{staging_dir.resolve()}'")
```

This ensures:
1. User can verify all files uploaded successfully
2. If upload failed, staging dir is preserved for resume
3. No race condition with any internal HF retry logic

## Edge Cases to Consider

1. **Stale files**: Fixed `./hf_upload_staging` path reused across different repos/revisions/num_shards could leave stale files. Users should manually clear before starting a new upload to a different target.

2. **Corrupt shards**: A crash mid-write could leave a corrupt shard that "exists" and gets skipped on resume. Consider adding checksum verification in future.

3. **Path with spaces**: The logged `rm -rf` command now quotes the path to handle working directories with spaces.

## Lessons Learned

1. **Never assume a function is fully synchronous** - even if docs say it's blocking, verify observed behavior
2. **Cleanup of large artifacts should be manual** - especially for multi-hour operations
3. **gitignore ≠ protection from deletion** - gitignore only affects git tracking, not filesystem operations
4. **Best completion detection is remote verification** - use `HfApi.list_repo_files()` to verify uploads, don't trust function return alone

## References

- Commit: `efaa0d6` (fix/upload-staging-cleanup branch)

## Date

2025-12-14
