# Issue: AOMIC-PIOP1 (ds002785) - Recommended First

**Status:** Ready for upstream
**Difficulty:** ⭐⭐ Easy-Medium (smallest AOMIC, good tracer bullet)
**Labels:** `enhancement`, `good first issue`, `dataset`

---

## Title

`[Dataset] Add AOMIC-PIOP1 (ds002785) - Amsterdam Multimodal MRI (216 subjects)`

---

## Body

### Dataset Info

| Field | Value |
|-------|-------|
| **Name** | AOMIC-PIOP1 (Population Imaging of Psychology 1) |
| **Source** | [OpenNeuro ds002785](https://openneuro.org/datasets/ds002785) |
| **Paper** | [Snoek et al., Scientific Data 2021](https://www.nature.com/articles/s41597-021-00870-6) |
| **License** | CC0 (Public Domain) |
| **Subjects** | 216 |
| **Format** | BIDS |
| **HuggingFace Target** | `hugging-science/aomic-piop1` |

### Description

AOMIC-PIOP1 is part of the Amsterdam Open MRI Collection - multimodal 3T MRI with detailed demographics and psychometric variables. This is the **smallest** of the 3 AOMIC datasets, making it ideal as a "tracer bullet" before tackling the larger ones.

**Data includes:**
- T1-weighted structural MRI
- Diffusion-weighted MRI
- Resting-state fMRI
- Task-based fMRI (emotion, working memory, faces, etc.)
- Physiological recordings (cardiac, respiratory)
- Demographics + psychometrics

### Why This Matters

1. **Tracer bullet** - Smallest AOMIC, test the pattern before ID1000 (928 subjects)
2. **Rich multimodal** - Structural + diffusion + fMRI
3. **Task fMRI** - Valuable for cognitive neuroscience
4. **Proves pipeline** - Tests Sequence(Nifti()) for multiple runs

### Exact Schema

```python
from datasets import Features, Value
from datasets.features import Nifti, Sequence

def get_aomic_piop1_features() -> Features:
    """AOMIC-PIOP1 schema - one row per SUBJECT.

    Note: Following arc.py pattern, we use a single `bold` list for ALL
    functional runs (rest + tasks). Task info is in the filename (e.g.,
    _task-rest_, _task-workingmemory_). Separation can be done downstream.
    """
    return Features({
        "subject_id": Value("string"),
        # Structural
        "t1w": Nifti(),
        # Diffusion
        "dwi": Sequence(Nifti()),           # May have multiple runs
        # Functional (all runs: rest + tasks)
        "bold": Sequence(Nifti()),          # All BOLD runs (*_bold.nii.gz)
        # Metadata from participants.tsv
        "age": Value("float32"),
        "sex": Value("string"),
        "handedness": Value("string"),      # Verify column name (hand vs handedness)
    })
```

> **Implementation Note:** Verify `participants.tsv` column names. BIDS uses
> `handedness` but some datasets use `hand`. Check actual file during implementation.

### Directory Structure

```
ds002785/
├── participants.tsv
├── dataset_description.json
└── sub-XXXX/
    ├── anat/
    │   └── sub-XXXX_T1w.nii.gz
    ├── dwi/
    │   ├── sub-XXXX_dwi.nii.gz
    │   ├── sub-XXXX_dwi.bval
    │   └── sub-XXXX_dwi.bvec
    └── func/
        ├── sub-XXXX_task-rest_bold.nii.gz
        ├── sub-XXXX_task-workingmemory_bold.nii.gz
        ├── sub-XXXX_task-faces_bold.nii.gz
        └── ... (multiple tasks)
```

### Files to Create

```
src/bids_hub/datasets/aomic_piop1.py       # Dataset module
src/bids_hub/validation/aomic.py           # Shared AOMIC validation
scripts/download_aomic_piop1.sh            # Download script
tests/test_aomic_piop1.py                  # Tests
docs/dataset-cards/aomic-piop1.md          # Dataset card (follow arc-aphasia-bids.md pattern)
```

### Implementation Steps

1. **Create download script** (`scripts/download_aomic_piop1.sh`)
   ```bash
   aws s3 sync --no-sign-request s3://openneuro.org/ds002785 "$TARGET_DIR"
   ```

2. **Create dataset module** (`src/bids_hub/datasets/aomic_piop1.py`)
   - Implement `build_aomic_piop1_file_table()` - walk sub-*/anat/, dwi/, func/
   - Implement `get_aomic_piop1_features()` - schema above
   - Use `find_all_niftis()` for Sequence features (multiple runs)

3. **Add CLI commands** (in `cli.py`)
   ```python
   @aomic.command()
   def piop1():
       """AOMIC-PIOP1 dataset commands."""
   ```

4. **Add validation** (`src/bids_hub/validation/aomic.py`)
   - Check participants.tsv exists
   - Check T1w exists per subject
   - Report available modalities

5. **Upload to HuggingFace**
   ```bash
   uv run bids-hub aomic piop1 build /path/to/ds002785 \
       --hf-repo hugging-science/aomic-piop1 --no-dry-run
   ```
   - Use `num_shards=216` (one per subject)

### Acceptance Criteria

- [ ] Download script works
- [ ] `uv run bids-hub aomic piop1 validate <path>` passes
- [ ] `uv run bids-hub aomic piop1 build <path> --dry-run` succeeds
- [ ] Tests pass
- [ ] Dataset uploaded to `hugging-science/aomic-piop1`
- [ ] HuggingFace README.md with proper frontmatter, usage examples, and citation
- [ ] `docs/dataset-cards/aomic-piop1.md` added (follow `arc-aphasia-bids.md` pattern)

### Resources

- [OpenNeuro ds002785](https://openneuro.org/datasets/ds002785)
- [AOMIC Website](https://nilab-uva.github.io/AOMIC.github.io/)
- [Scientific Data Paper](https://www.nature.com/articles/s41597-021-00870-6)

### Citation

```bibtex
@article{snoek2021aomic,
  title={The Amsterdam Open MRI Collection, a set of multimodal MRI datasets for individual difference analyses},
  author={Snoek, Lukas and van der Miesen, Maite M and others},
  journal={Scientific Data},
  volume={8},
  number={1},
  pages={85},
  year={2021}
}
```

---

## Related Issues

After this is complete, tackle:
- AOMIC-ID1000 (ds003097) - 928 subjects
- AOMIC-PIOP2 (ds002790) - 226 subjects
