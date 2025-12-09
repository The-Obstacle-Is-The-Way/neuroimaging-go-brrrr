# Phase 5: Verify & Commit

**Complexity**: Verification

---

## Pre-Commit Checklist

### 1. Sync Dependencies

```bash
uv sync --all-extras
```

**Expected**: Clean install with no errors

### 2. Run Tests

```bash
uv run pytest -v
```

**Expected**: All tests pass

### 3. Verify CLI

```bash
uv run bids-hub --help
uv run bids-hub list
uv run bids-hub arc --help
uv run bids-hub arc info
uv run bids-hub isles24 --help
uv run bids-hub isles24 info
```

**Expected**: All commands work, show proper output

### 4. Verify Imports

```bash
python -c "from bids_hub import build_and_push_arc, ValidationResult; print('OK')"
python -c "from bids_hub.cli import app; print('OK')"
python -c "from bids_hub.validation import validate_arc_download; print('OK')"
```

**Expected**: All imports succeed

### 5. Lint Check

```bash
uv run ruff check src/ tests/
```

**Expected**: No errors

### 6. Type Check

```bash
uv run mypy src/
```

**Expected**: No errors (or acceptable warnings)

### 7. Pre-commit Hooks

```bash
uv run pre-commit run --all-files
```

**Expected**: All checks pass

### 8. Verify Download Scripts

```bash
./scripts/download_arc.sh --help 2>&1 | head -3
./scripts/download_isles24.sh 2>&1 | head -3
```

**Expected**: Both scripts are executable and show usage/output

### 9. Verify .gitignore

```bash
git check-ignore data/test.nii.gz && echo "IGNORED" || echo "NOT IGNORED"
git check-ignore openneuro/ds004884 && echo "IGNORED" || echo "NOT IGNORED"
```

**Expected**: Both show "IGNORED"

### 10. Verify File Structure

```bash
# Source package
ls src/bids_hub/
# Expected: __init__.py  cli.py  core  datasets  validation

# Tests
ls tests/
# Expected: __init__.py  test_*.py  validation/

# Scripts
ls scripts/
# Expected: download_arc.sh  download_isles24.sh  visualization

# Root docs (CONTRIBUTING.md was kept from target, not copied)
ls *.md *.cff 2>/dev/null | sort
# Expected: CHANGELOG.md  CITATION.cff  CLAUDE.md  CONTRIBUTING.md  README.md  UPSTREAM_BUG.md
```

---

## Final Structure

```
neuroimaging-go-brrrr/
├── src/
│   └── bids_hub/              # 1,976 lines of production code
│       ├── __init__.py
│       ├── cli.py
│       ├── core/
│       ├── datasets/
│       └── validation/
├── tests/                     # 9 test files
│   ├── __init__.py
│   ├── test_arc.py
│   ├── test_cli_skeleton.py
│   ├── test_core_nifti.py
│   ├── test_isles24.py
│   ├── test_validation.py
│   └── validation/
├── scripts/
│   ├── download_arc.sh        # Robust ARC download
│   ├── download_isles24.sh    # ISLES24 download
│   └── visualization/         # Tobias's notebooks (kept)
├── docs/
│   ├── brainstorming/         # Context (kept)
│   └── specs/                 # These specs
├── _reference_repos/
│   └── bids-hub/              # Reference (kept for now)
├── pyproject.toml             # Updated with all deps + CLI
├── Makefile                   # Updated targets
├── .gitignore                 # Enhanced with BIDS patterns
├── .pre-commit-config.yaml    # Merged with mypy deps
├── CLAUDE.md                  # AI context (from reference)
├── UPSTREAM_BUG.md            # Critical upstream bug docs (from reference)
├── CITATION.cff               # Citation metadata (from reference)
├── CHANGELOG.md               # Version history (from reference)
├── CONTRIBUTING.md            # Contribution guidelines (KEPT from target)
└── README.md                  # Project overview (KEPT from target)
```

---

## Commit

```bash
git add -A
git status

git commit -m "$(cat <<'EOF'
Integrate bids-hub production pipeline

Source integration:
- Add src/bids_hub/ (1,976 lines): complete BIDS→HF upload pipeline
- Add CLI: bids-hub arc/isles24 build/validate/info
- Add comprehensive test suite (9 files)

Configuration updates:
- Replace pyproject.toml with complete config + datasets git pin
- Merge .gitignore with BIDS/NIfTI patterns
- Merge .pre-commit-config.yaml with mypy dependencies
- Update Makefile with aligned targets

Scripts:
- Add download_arc.sh (robust OpenNeuro download)
- Add download_isles24.sh (Zenodo download)
- Delete obsolete push_to_hub_ds004884_full.py
- Keep visualization notebooks (consumption pipeline)

Documentation:
- Add CLAUDE.md, UPSTREAM_BUG.md, CITATION.cff, CHANGELOG.md
- Keep existing README.md, CONTRIBUTING.md (target versions)

Cleanup:
- Delete empty neuroimaging_go_brrrr skeleton
- Delete one-liner download_ds004884.sh

The package name is `bids_hub` (accurate), hosted in
`neuroimaging-go-brrrr` repo (coordination hub).
EOF
)"
```

---

## Push

```bash
# Push to your fork
git push origin feature/bids-hub-integration

# Push to upstream (collaborators can see)
git push upstream feature/bids-hub-integration
```

---

## Post-Integration: Clean Up Reference

After verifying everything works, optionally remove the reference:

```bash
# Only after everything is verified working
rm -rf _reference_repos/
git add -A && git commit -m "Remove reference repos after successful integration"
```

**Recommendation**: Keep `_reference_repos/` for at least a few days in case issues emerge.
