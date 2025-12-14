# BUG-002: HuggingFace Hub Upload ReadTimeout on Large Files

## Status: WORKAROUND IMPLEMENTED

## Summary

When uploading large parquet shards (500-800MB) to HuggingFace Hub using `huggingface_hub.HfApi.upload_file()`, the upload fails with `ReadTimeout: The read operation timed out` after approximately 10 seconds of server response delay.

## Symptoms

- Upload progresses normally for smaller shards
- Randomly fails on larger shards (typically 500MB+)
- Error: `ReadTimeout: The read operation timed out`
- Failure occurs during HuggingFace's server-side dedup check, not during actual data transfer
- Upload appears to complete (file uploaded) but client times out waiting for confirmation

## Root Cause

HuggingFace Hub's default HTTP timeout configuration uses a **10 second read timeout**:

```python
# From huggingface_hub/utils/_http.py
timeout=httpx.Timeout(constants.DEFAULT_REQUEST_TIMEOUT, write=60.0)
# DEFAULT_REQUEST_TIMEOUT = 10  (seconds)
```

This results in:
```
Session timeout: Timeout(connect=10, read=10, write=60.0, pool=10)
```

When uploading a file, HuggingFace's server performs a dedup check to see if the file already exists. For large files (500MB+), this check can take longer than 10 seconds, causing the client to timeout while waiting for the server's response.

## Environment

- `huggingface_hub` version: 1.2.1
- Python: 3.13
- Platform: macOS Darwin 25.0.0
- File sizes: 20MB - 800MB parquet shards (ARC neuroimaging dataset)

## Upstream Issue

Related: https://github.com/huggingface/datasets/issues/7400

The upstream issue discusses 504 Gateway Timeout, but our investigation found the client-side ReadTimeout occurs first due to the short default timeout.

## Workaround

We implemented a workaround in `src/bids_hub/core/builder.py`:

```python
from huggingface_hub import constants as hf_constants

# Increase timeout to 5 minutes
_HF_UPLOAD_TIMEOUT = 300

# Before creating HfApi
original_timeout = hf_constants.DEFAULT_REQUEST_TIMEOUT
hf_constants.DEFAULT_REQUEST_TIMEOUT = _HF_UPLOAD_TIMEOUT

try:
    api = HfApi(token=token)
    # ... upload logic ...
finally:
    # Restore original timeout
    hf_constants.DEFAULT_REQUEST_TIMEOUT = original_timeout
```

This works because:
1. `DEFAULT_REQUEST_TIMEOUT` is read when the httpx session is created
2. Modifying it before `HfApi()` instantiation affects the session's timeout
3. Wrapping in try/finally ensures cleanup even on failure

## Recommended Upstream Fix

HuggingFace Hub should:

1. **Add `HF_HUB_UPLOAD_TIMEOUT` environment variable** - Similar to existing `HF_HUB_DOWNLOAD_TIMEOUT` and `HF_HUB_ETAG_TIMEOUT`

2. **Increase default read timeout for uploads** - The current 10s is insufficient for large file operations

3. **Add timeout parameter to `upload_file()`** - Allow per-call timeout customization:
   ```python
   api.upload_file(
       path_or_fileobj="large_file.parquet",
       path_in_repo="data/file.parquet",
       repo_id="org/repo",
       timeout=300,  # NEW: per-call timeout
   )
   ```

## Potential PR to huggingface_hub

If contributing upstream, the fix would be in `huggingface_hub/utils/_http.py`:

```python
# Add new constant
DEFAULT_UPLOAD_TIMEOUT = int(os.environ.get("HF_HUB_UPLOAD_TIMEOUT", "300"))

# Modify session creation to use longer timeout for uploads
def get_session_for_upload():
    return _get_session_with_timeout(DEFAULT_UPLOAD_TIMEOUT)
```

## Testing

After implementing the workaround:
- All 97 tests pass
- Upload of 902 shards (ARC dataset, ~200GB total) succeeds without timeout

## References

- Commit: `3849b1a` - fix(upload): increase HuggingFace timeout to prevent ReadTimeout on large shards
- Upstream: https://github.com/huggingface/datasets/issues/7400
- HF Docs: https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables

## Date

2025-12-14
