# Issue: AOMIC-ID1000 (ds003097) - Large Scale

**Status:** Ready for upstream (after PIOP1 complete)
**Difficulty:** ⭐⭐⭐ Medium-Hard (large, 928 subjects)
**Labels:** `enhancement`, `dataset`, `help wanted`

---

## Title

`[Dataset] Add AOMIC-ID1000 (ds003097) - Amsterdam Large Population MRI (928 subjects)`

---

## Body

### Prerequisites

Complete [AOMIC-PIOP1](003a_aomic_piop1.md) first - it establishes the pattern for AOMIC datasets.

### Dataset Info

| Field | Value |
|-------|-------|
| **Name** | AOMIC-ID1000 (Individual Differences 1000) |
| **Source** | [OpenNeuro ds003097](https://openneuro.org/datasets/ds003097) |
| **Paper** | [Snoek et al., Scientific Data 2021](https://www.nature.com/articles/s41597-021-00870-6) |
| **License** | CC0 (Public Domain) |
| **Subjects** | 928 |
| **Format** | BIDS |
| **HuggingFace Target** | `hugging-science/aomic-id1000` |

### Description

AOMIC-ID1000 is the **largest** dataset in the Amsterdam Open MRI Collection - a representative sample of the general Dutch population. Contains structural, diffusion, and some functional MRI (less functional than PIOP1/PIOP2, but still includes movie-watching task).

**Data includes:**
- T1-weighted structural MRI
- Diffusion-weighted MRI
- Task fMRI (movie watching - "Mov" paradigm)
- Demographics + psychometrics (extensive battery)

### Why This Matters

1. **Population-representative** - General population, not just students
2. **Large scale** - 928 subjects for robust training
3. **Stress test** - Validates sharding at scale
4. **Individual differences** - Rich psychometric data

### Exact Schema

```python
from datasets import Features, Value
from datasets.features import Nifti, Sequence

def get_aomic_id1000_features() -> Features:
    """AOMIC-ID1000 schema - one row per SUBJECT.

    Note: ID1000 has movie-watching fMRI, included in `bold`.
    Following arc.py pattern for consistency.
    """
    return Features({
        "subject_id": Value("string"),
        # Structural
        "t1w": Nifti(),
        # Diffusion
        "dwi": Sequence(Nifti()),
        # Functional (movie watching task)
        "bold": Sequence(Nifti()),          # *_bold.nii.gz (movie watching)
        # Metadata
        "age": Value("float32"),
        "sex": Value("string"),
        "education_years": Value("float32"),
    })
```

### Implementation Notes

- **Sharding critical**: Use `num_shards=928` to prevent OOM
- **Reuse AOMIC validation**: `src/bids_hub/validation/aomic.py`
- **Download size**: ~53 GB raw data (derivatives are ~355 GB extra, not needed)
- **Storage estimate**: ~200-400 GB on HuggingFace Hub after embedding NIfTIs

### Files to Create

```
src/bids_hub/datasets/aomic_id1000.py      # Dataset module
scripts/download_aomic_id1000.sh           # Download script
tests/test_aomic_id1000.py                 # Tests
docs/dataset-cards/aomic-id1000.md         # Dataset card (follow arc-aphasia-bids.md pattern)
```

### Acceptance Criteria

- [ ] Download script works (warn: ~53 GB raw data download)
- [ ] Validation passes
- [ ] Build with proper sharding succeeds
- [ ] Tests pass
- [ ] Dataset uploaded to `hugging-science/aomic-id1000`
- [ ] HuggingFace README.md with proper frontmatter, usage examples, and citation
- [ ] `docs/dataset-cards/aomic-id1000.md` added (follow `arc-aphasia-bids.md` pattern)

### Resources

- [OpenNeuro ds003097](https://openneuro.org/datasets/ds003097)
- [AOMIC Website](https://nilab-uva.github.io/AOMIC.github.io/)

### Citation

Same as PIOP1 - Snoek et al., 2021
