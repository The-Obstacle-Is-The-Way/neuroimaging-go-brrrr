# Issue: AOMIC-PIOP2 (ds002790)

**Status:** Ready for upstream (after PIOP1 complete)
**Difficulty:** ⭐⭐ Easy-Medium (similar to PIOP1)
**Labels:** `enhancement`, `dataset`, `help wanted`

---

## Title

`[Dataset] Add AOMIC-PIOP2 (ds002790) - Amsterdam Multimodal MRI (226 subjects)`

---

## Body

### Prerequisites

Complete [AOMIC-PIOP1](003a_aomic_piop1.md) first - PIOP2 uses the same pattern.

### Dataset Info

| Field | Value |
|-------|-------|
| **Name** | AOMIC-PIOP2 (Population Imaging of Psychology 2) |
| **Source** | [OpenNeuro ds002790](https://openneuro.org/datasets/ds002790) |
| **Paper** | [Snoek et al., Scientific Data 2021](https://www.nature.com/articles/s41597-021-00870-6) |
| **License** | CC0 (Public Domain) |
| **Subjects** | 226 |
| **Format** | BIDS |
| **HuggingFace Target** | `hugging-science/aomic-piop2` |

### Description

AOMIC-PIOP2 is similar to PIOP1 but scanned on updated scanner hardware ("Achieva" vs "Intera"). Contains rich task-based fMRI with different experimental paradigms.

**Data includes:**
- T1-weighted structural MRI
- Diffusion-weighted MRI
- Resting-state fMRI
- Task-based fMRI (movie watching, different tasks than PIOP1)
- Physiological recordings

### Why This Matters

1. **Scanner upgrade validation** - Test reproducibility across hardware
2. **Different tasks** - Complementary to PIOP1
3. **Complete AOMIC** - Third piece of the collection

### Exact Schema

Same as PIOP1 - reuse `get_aomic_piop1_features()` pattern.

### Files to Create

```
src/bids_hub/datasets/aomic_piop2.py       # Dataset module (copy PIOP1, adjust)
scripts/download_aomic_piop2.sh            # Download script
tests/test_aomic_piop2.py                  # Tests
docs/dataset-cards/aomic-piop2.md          # Dataset card (follow arc-aphasia-bids.md pattern)
```

### Implementation Notes

- Nearly identical to PIOP1 implementation
- Can share validation code
- `num_shards=226`

### Acceptance Criteria

- [ ] Download script works
- [ ] Validation passes
- [ ] Build succeeds
- [ ] Tests pass
- [ ] Dataset uploaded to `hugging-science/aomic-piop2`
- [ ] HuggingFace README.md with proper frontmatter, usage examples, and citation
- [ ] `docs/dataset-cards/aomic-piop2.md` added (follow `arc-aphasia-bids.md` pattern)

### Resources

- [OpenNeuro ds002790](https://openneuro.org/datasets/ds002790)
- [AOMIC Website](https://nilab-uva.github.io/AOMIC.github.io/)

### Citation

Same as PIOP1 - Snoek et al., 2021
