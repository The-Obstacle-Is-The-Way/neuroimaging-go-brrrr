# TODO - Codebase Maintenance

Findings from comprehensive codebase audit (2025-12-08), updated 2025-12-12.

## Warnings (Should-Fix When Possible)

### 1. Upstream Dependency Pin

**Status**: Monitoring
**Priority**: Medium
**Tracking**: [huggingface/datasets#7896](https://github.com/huggingface/datasets/pull/7896)

The project pins `datasets` to git commit `0ec4d87d` due to upstream bug where `embed_table_storage` crashes with SIGKILL on sharded `Sequence(Nifti())` columns.

**Action**: When PR #7896 is merged and released:

1. Update `pyproject.toml` to use released version
2. Remove pandas workaround in `src/bids_hub/core/builder.py` (in `push_dataset_to_hub`)
3. Test uploads still work

### 2. CLI Test Coverage at 60%

**Status**: Open
**Priority**: Low
**File**: `src/bids_hub/cli.py`

Several error handling branches not fully exercised. Core logic is tested elsewhere, but CLI layer could use integration tests.

**Action**: Add tests for CLI error paths (file not found, validation failures).

---

## Suggestions (Nice-to-Have)

### 3. Type Safety in Validation

**File**: `src/bids_hub/validation/base.py`

`subprocess.run` usage is safe (no `shell=True`) but could benefit from explicit type guards or wrapper for external tool execution.

### 4. Performance Optimization (Post-Upstream Fix)

**File**: `src/bids_hub/core/builder.py`

Once upstream PR #7896 merges, remove the pandas roundtrip workaround (lines 185-206) for better performance during uploads.

---

## Current State

| Metric | Value |
|--------|-------|
| Tests | 91 passing |
| Coverage | 81% overall |
| Ruff | 0 issues |
| Mypy | 0 errors |
| Critical Issues | None |

Last audit: 2025-12-13
