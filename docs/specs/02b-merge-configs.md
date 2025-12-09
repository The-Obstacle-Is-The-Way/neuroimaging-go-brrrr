# Phase 2b: Merge Configuration Files

**Complexity**: Medium (careful merge)

---

## Overview

These config files need intelligent merging rather than simple copy/replace:

| File | Strategy | Reason |
|------|----------|--------|
| `.gitignore` | **APPEND** | Target is minimal, add BIDS patterns |
| `.pre-commit-config.yaml` | **MERGE** | Target has newer versions, add mypy deps |
| `Makefile` | **MERGE** | Align targets with bids_hub package |

---

## 2b.1 - Merge .gitignore

### Problem

Target `.gitignore` (17 lines) is minimal. Reference (222 lines) has critical BIDS patterns to prevent accidentally committing large datasets.

### Action

**APPEND** these lines to the END of `.gitignore`:

```gitignore
# ============================================
# Neuroimaging / BIDS / NIfTI specific
# ============================================
data/
openneuro/
ds*/
*.nii
*.nii.gz
*.pt
*.npz

# HuggingFace cache
.cache/huggingface/
```

### Command

```bash
cat >> .gitignore << 'EOF'

# ============================================
# Neuroimaging / BIDS / NIfTI specific
# ============================================
data/
openneuro/
ds*/
*.nii
*.nii.gz
*.pt
*.npz

# HuggingFace cache
.cache/huggingface/
EOF
```

### Verification

```bash
# Check patterns were added
grep "*.nii.gz" .gitignore
# Expected: *.nii.gz
```

---

## 2b.2 - Merge .pre-commit-config.yaml

### Problem

Target has NEWER versions but reference has additional mypy dependencies needed for type checking.

| Hook | Target | Reference | Use |
|------|--------|-----------|-----|
| pre-commit-hooks | v6.0.0 | v4.6.0 | **Target** (newer) |
| ruff-pre-commit | v0.14.8 | v0.7.0 | **Target** (newer) |
| mirrors-mypy | v1.19.0 | v1.11.2 | **Target** (newer) |
| mypy additional_dependencies | ❌ missing | ✅ has | **Add from reference** |

### Action

**REPLACE** `.pre-commit-config.yaml` with this merged version:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: check-merge-conflict

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.8
    hooks:
      - id: ruff
        types_or: [python, pyi]
        args: [--fix]
      - id: ruff-format
        types_or: [python, pyi]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.19.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pandas-stubs>=2.0.0
          - types-pyyaml
        args: [--config-file=pyproject.toml, src/]
        pass_filenames: false
```

### Key Additions

- `additional_dependencies: [pandas-stubs>=2.0.0, types-pyyaml]` - Required for mypy to understand pandas types
- `args: [--config-file=pyproject.toml, src/]` - Use pyproject.toml config, check src/
- `pass_filenames: false` - Check all files, not just staged

### Verification

```bash
# Reinstall hooks
uv run pre-commit install

# Run on all files
uv run pre-commit run --all-files
```

---

## 2b.3 - Merge Makefile

### Problem

Target Makefile uses different naming and needs to align with bids_hub package.

| Target | Target Makefile | Reference Makefile | Action |
|--------|-----------------|-------------------|--------|
| `check` | `uv run mypy --strict ...` | (none) | **Remove** (use typecheck) |
| `typecheck` | (none) | `uv run mypy src` | **Add** |
| `test-cov` | `--cov` | `--cov=bids_hub` | **Fix** |
| `pre-commit` | (none) | `uv run pre-commit run --all-files` | **Add** |
| `clean` | Basic | Complete | **Enhance** |

### Action

**REPLACE** `Makefile` with this merged version:

```makefile
.PHONY: help install lint format typecheck test test-cov clean pre-commit all

help:
	@echo "Available targets:"
	@echo "  all         - Run lint, typecheck, and test"
	@echo "  install     - Install dependencies with uv"
	@echo "  lint        - Run ruff linter"
	@echo "  format      - Format code with ruff"
	@echo "  typecheck   - Run mypy type checker"
	@echo "  test        - Run pytest"
	@echo "  test-cov    - Run pytest with coverage"
	@echo "  pre-commit  - Run pre-commit on all files"
	@echo "  clean       - Remove build artifacts"

all: lint typecheck test

install:
	uv sync --all-extras

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run mypy src

test:
	uv run pytest

test-cov:
	uv run pytest --cov=bids_hub --cov-report=term-missing

pre-commit:
	uv run pre-commit run --all-files

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
```

### Key Changes

- `install` uses `--all-extras` (installs dev deps)
- `typecheck` replaces `check` (clearer name)
- `test-cov` uses `--cov=bids_hub` (correct package name)
- `pre-commit` target added
- `clean` is more comprehensive

### Verification

```bash
# Test all targets work
make help
make lint
make typecheck
make test
```

---

## Complete Phase 2b Commands

```bash
# 2b.1 - Append to .gitignore
cat >> .gitignore << 'EOF'

# ============================================
# Neuroimaging / BIDS / NIfTI specific
# ============================================
data/
openneuro/
ds*/
*.nii
*.nii.gz
*.pt
*.npz

# HuggingFace cache
.cache/huggingface/
EOF

# 2b.2 - Replace .pre-commit-config.yaml (use content above)
# 2b.3 - Replace Makefile (use content above)
```

---

## Final Verification

```bash
# All configs valid
make help           # Makefile works
uv run pre-commit run --all-files  # pre-commit works
git check-ignore data/test.nii.gz  # .gitignore pattern works
```
