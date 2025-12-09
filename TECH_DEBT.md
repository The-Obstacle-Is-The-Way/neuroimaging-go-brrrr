# Tech Debt

Issues found during codebase audit. Priority: P0 (critical) > P1 (high) > P2 (medium) > P3 (low).

---

## P1: Silent Failures / Inappropriate Graceful Degradation

### 1. `isles24.py:119-120` - Phenotype parse errors logged at WARNING, not raised

```python
except Exception as e:
    logger.warning("Error reading phenotype file %s: %s", xlsx_file, e)
    continue
```

**Problem**: If every phenotype XLSX fails to parse (e.g., openpyxl not installed, corrupt files), the pipeline silently produces `None` metadata for all subjects with no indication of systematic failure. User sees successful build but gets garbage data.

**Fix**: Track failure count. If >50% of phenotype files fail, raise an exception or emit a loud summary warning at the end of `build_isles24_file_table()`.

---

### 2. `arc.py:101-102` and `arc.py:107-108` - Missing subjects silently skipped

```python
if not subject_dir.exists():
    continue
...
if not session_dirs:
    continue
```

**Problem**: If `participants.tsv` lists 230 subjects but only 10 exist on disk (incomplete download), the function silently returns 10 rows with no warning. User might push an incomplete dataset to HuggingFace.

**Fix**: Log a summary at the end: `"Built file table with {n} sessions from {m} subjects (participants.tsv lists {total})"`

---

### 3. `validation/isles24.py:87-88` - Missing phenotype directory marked as PASS

```python
passed=True,  # Not a failure, may be optional
details="phenotype/ directory not found (skipping check)",
```

**Problem**: If phenotype dir is missing due to incomplete extraction, validation reports PASS. This is incorrect - the check should warn or be clearly labeled as "SKIP" rather than "PASS".

**Fix**: Return a separate status (e.g., `passed=None` or add a `skipped` field) or change to `passed=False` with a `severity="warning"` field.

---

## P2: Type Issues

### 4. `builder.py:114` - `Any` type in function signature

```python
def push_dataset_to_hub(
    ds: Dataset,
    config: DatasetBuilderConfig,
    embed_external_files: bool = True,
    **push_kwargs: Any,  # <-- Untyped
) -> None:
```

**Problem**: `**push_kwargs` swallows any arguments without type checking. If caller passes a typo like `privaet=True` instead of `private=True`, it silently gets passed to `push_to_hub()` where it's also ignored.

**Fix**: Either:
- Define explicit optional parameters (`private: bool = False`, `num_shards: int | None = None`)
- Or use `TypedDict` for allowed kwargs

---

## P2: Dead Code / Unused Exports

### 5. `validation/arc.py:51-68` - Backward compatibility aliases never tested

```python
# Backward compatibility aliases - preserve old API
EXPECTED_COUNTS = {...}
REQUIRED_BIDS_FILES = [...]
```

**Problem**: These are exported in `__all__` but there are no tests verifying they match `ARC_VALIDATION_CONFIG`. They could drift out of sync.

**Fix**: Either remove (breaking change) or add a test asserting `EXPECTED_COUNTS["subjects"] == ARC_VALIDATION_CONFIG.expected_counts["subjects"]`.

---

### 6. `validation/__init__.py` - Exports not used in tests

The following are exported but never imported in any test:
- `DatasetValidationConfig`
- `validate_dataset`
- `verify_md5`
- `check_count`
- `check_zero_byte_files`

**Problem**: If these break, tests won't catch it.

**Fix**: Either add import tests or remove from public API.

---

## P2: Incomplete Implementation

### 7. `builder.py:48` - `config` parameter unused

```python
def build_hf_dataset(
    config: DatasetBuilderConfig,  # Reserved for future path resolution
    file_table: pd.DataFrame,
    features: Features,
) -> Dataset:
```

**Problem**: Docstring says "will be used in future versions for resolving relative file paths" but it's been shipped without that feature. API is locked.

**Fix**: Either implement relative path resolution or document that `file_table` must contain absolute paths (currently undocumented requirement).

---

### 8. `builder.py:230-231` - `dataset_info.json` warning with no actionable guidance

```python
else:
    logger.warning("dataset_info.json was not generated.")
```

**Problem**: If this happens, the uploaded dataset may be unusable, but we only emit a warning and continue. User has no idea what went wrong or how to fix.

**Fix**: Either raise an exception or add actionable guidance in the warning message.

---

## P3: Minor Issues

### 9. Docstring says "CSV files" but code uses XLSX

`isles24.py:137`:
```python
- phenotype/sub-strokeXXXX/ses-01/ and ses-02/: CSV files
```

But the code at line 102 uses:
```python
for xlsx_file in ses_dir.glob("*.xlsx"):
```

**Fix**: Update docstring to say "XLSX files".

---

### 10. `validation/base.py:154` - MD5 uses weak hash

```python
hash_md5 = hashlib.md5()
```

**Problem**: MD5 is cryptographically broken. While fine for integrity checks, some security scanners flag it.

**Fix**: Consider SHA-256 for new code. MD5 is acceptable here since it's only for integrity, not security.

---

## Not Tech Debt (Acceptable)

The following were reviewed and deemed acceptable:

- **Git-pinned `datasets` dependency**: Documented workaround for upstream bug. Has TODO tracking.
- **Pandas round-trip workaround in `push_dataset_to_hub`**: Documented workaround for upstream bug.
- **`ignore_missing_imports = true` in mypy**: Necessary for HuggingFace libraries without stubs.
- **Test fixtures duplicate `_create_minimal_nifti()`**: Minor duplication, not worth abstracting.

---

## Policy: Research Notebooks (`scripts/visualization/`)

### Decision: Do NOT lint or type-check research notebooks

The `scripts/visualization/*.ipynb` files are explicitly excluded from linting via `pyproject.toml`:

```toml
[tool.ruff]
extend-exclude = ["*.ipynb"]
```

**This is intentional and aligned with 2025 industry best practices.**

### Rationale

1. **Research notebooks serve a different purpose than production code.**
   As [Martin Fowler notes](https://martinfowler.com/articles/productize-data-sci-notebooks.html), "Data science ideas do need to move out of notebooks and into production, but trying to deploy notebooks as a code artifact breaks a multitude of good software practices." Our notebooks are exploratory tools, not production artifacts.

2. **The tension between speed and quality is well-documented.**
   Per [Sonar's analysis](https://www.sonarsource.com/blog/is-clean-code-the-solution-to-jupyter-notebook-code-quality/), "The tension between speed and code quality is a persistent issue in Data Science. The need to move fast and iterate quickly may come at the cost of code quality." For research/visualization notebooks, speed wins.

3. **Data scientists are not traditional developers.**
   [Industry guidance](https://www.sonarsource.com/blog/is-clean-code-the-solution-to-jupyter-notebook-code-quality/) recognizes: "Data Scientists are using notebooks as a tool to model, test, and express ideas. Coding is just a necessary requirement to achieve this. Prototyping should ideally be a fast, creative process."

4. **Google/DeepMind practice**: Based on [public repository analysis](https://arxiv.org/html/2507.18833v1), even major research orgs don't strictly lint research notebooks. Their notebooks focus on reproducibility (random seeds, clear outputs) rather than code style.

5. **2025 tooling recommendations**: [Modern guidance](https://johal.in/pylint-vs-flake8-linting-strategies-in-python-projects-2025/) suggests "Flake8 for rapid prototyping, Pylint for production hardening." Our notebooks are prototyping; our `src/` is production.

### What We DO Enforce for Notebooks

- **Reproducibility**: Set random seeds where applicable
- **Clear outputs**: Notebooks should run top-to-bottom
- **No secrets**: Never commit API keys or credentials

### When to Promote Notebook Code to `src/`

If notebook code becomes:
- Reused across multiple notebooks
- Part of the data pipeline
- Needed by other team members

Then extract it to `src/bids_hub/` with full typing, linting, and tests.

### References

- [Martin Fowler: Don't put notebooks into production](https://martinfowler.com/articles/productize-data-sci-notebooks.html)
- [Sonar: Is Clean Code the solution to Jupyter notebook quality?](https://www.sonarsource.com/blog/is-clean-code-the-solution-to-jupyter-notebook-code-quality/)
- [2025 Linting Strategies](https://johal.in/pylint-vs-flake8-linting-strategies-in-python-projects-2025/)
- [Jupyter Ecosystem Study (2025)](https://arxiv.org/html/2507.18833v1)
- [Google Cloud: Jupyter Notebook Best Practices](https://cloud.google.com/blog/products/ai-machine-learning/best-practices-that-can-improve-the-life-of-any-developer-using-jupyter-notebooks)
