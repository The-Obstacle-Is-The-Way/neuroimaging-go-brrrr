# TODO: Add t2w_acquisition Breakdown Validation

**Date:** 2025-12-14
**Status:** Superseded by bug fix
**See:** `docs/bugs/arc-t2w-multi-run-data-loss.md`

## Original Problem

We discovered HuggingFace had **222** SPACE samples but OpenNeuro (source of truth) has **223**.

## Root Cause Identified

The discrepancy is NOT a validation issue - it's a **schema design flaw**. See `docs/bugs/arc-t2w-multi-run-data-loss.md` for full details.

**TL;DR:** One session (`sub-M2105/ses-964`) has 2 T2w files. The current code sets `t2w=None` when there are multiple files, causing that session to be excluded from SPACE sample counts.

## Resolution

This TODO is superseded by the schema fix documented in the bug doc. Once structural modalities are changed to `Sequence(Nifti())`, the validation will naturally pass because all 223 SPACE samples will have T2w data.

## Still Useful: Add Breakdown Validation

After the schema fix, we should still add `t2w_acquisition` breakdown validation to `validate_arc_hf()`:

```python
# Add to ARC_HF_EXPECTED_COUNTS
"space_2x_count": 115,
"space_no_accel_count": 108,
"turbo_spin_echo_count": 5,
```

This would catch any future regressions in the t2w_acquisition distribution.
