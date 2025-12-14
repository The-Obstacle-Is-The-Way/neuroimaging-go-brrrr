# Schema Specification

> Dataset schemas for supported datasets.

---

## ARC Schema

**Rows:** One per session (902 total)

```python
Features({
    # Identifiers
    "subject_id": Value("string"),
    "session_id": Value("string"),

    # Structural imaging (single file per session)
    "t1w": Nifti(),
    "t2w": Nifti(),
    "t2w_acquisition": Value("string"),  # space_2x, space_no_accel, turbo_spin_echo
    "flair": Nifti(),

    # Functional imaging (multi-run support)
    "bold_naming40": Sequence(Nifti()),  # Naming task
    "bold_rest": Sequence(Nifti()),      # Resting state

    # Diffusion imaging (multi-run support)
    "dwi": Sequence(Nifti()),
    "dwi_bvals": Sequence(Value("string")),
    "dwi_bvecs": Sequence(Value("string")),
    "sbref": Sequence(Nifti()),

    # Derivatives (single file per session)
    "lesion": Nifti(),

    # Demographics
    "age_at_stroke": Value("float32"),
    "sex": Value("string"),
    "race": Value("string"),
    "wab_aq": Value("float32"),
    "wab_days": Value("float32"),
    "wab_type": Value("string"),
})
```

---

## ISLES24 Schema

**Rows:** One per subject (149 total). Flattens `ses-01` (Acute) and `ses-02` (Follow-up) into a single row.

```python
Features({
    "subject_id": Value("string"),

    # Acute Session (ses-01)
    "ncct": Nifti(),  # Non-contrast CT
    "cta": Nifti(),   # CT Angiography
    "ctp": Nifti(),   # CT Perfusion (4D)

    # Perfusion Maps (Derivatives, NCCT-space)
    "tmax": Nifti(),
    "mtt": Nifti(),
    "cbf": Nifti(),
    "cbv": Nifti(),

    # Follow-up Session (ses-02)
    "dwi": Nifti(),
    "adc": Nifti(),

    # Masks
    "lesion_mask": Nifti(),      # Final infarct segmentation (Ground Truth)
    "lvo_mask": Nifti(),         # Large Vessel Occlusion mask
    "cow_segmentation": Nifti(), # Circle of Willis segmentation

    # Metadata
    "age": Value("float32"),
    "sex": Value("string"),
    "nihss_admission": Value("float32"),
    "mrs_admission": Value("float32"),
    "mrs_3month": Value("float32"),
})
```
