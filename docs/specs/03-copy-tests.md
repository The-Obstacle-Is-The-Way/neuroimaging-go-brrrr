# Phase 3: Copy Tests

**Complexity**: Trivial (file copy + minor cleanup)

---

## Current tests/ in neuroimaging-go-brrrr

```
tests/
├── conftest.py      # Empty
└── test_smoke.py    # Basic smoke test (504 bytes) - will be replaced
```

## Source tests/ from bids-hub

```
tests/
├── __init__.py
├── test_arc.py           # ARC dataset tests
├── test_cli_skeleton.py  # CLI structure tests
├── test_core_nifti.py    # Core NIfTI handling tests
├── test_isles24.py       # ISLES24 dataset tests
├── test_validation.py    # Validation framework tests
└── validation/
    ├── __init__.py
    ├── test_base.py      # Base validation tests
    └── test_isles24.py   # ISLES24 validation tests
```

---

## Commands

```bash
# Remove existing empty tests
rm -rf tests/

# Copy complete test suite
cp -r _reference_repos/bids-hub/tests .

# Verify
ls -la tests/
```

---

## Expected Result

9 test files with comprehensive coverage:
- Synthetic BIDS fixtures (minimal NIfTI files)
- Mocked `push_to_hub` for dry-run tests
- Validation against paper/challenge expectations

---

## Verification

```bash
# Run tests (after Phase 2 pyproject.toml update)
uv run pytest -v

# Expected: All tests pass
```
