# Chris Rorden Lab & EEG Landscape for Aphasia/Stroke

> Research compiled: December 2025
> Purpose: Evaluate potential EEG datasets from Chris Rorden's lab and related collaborators for future integration into `neuroimaging-go-brrrr`

## Executive Summary

**Key Finding**: Chris Rorden's published datasets are currently **MRI-focused**, not EEG. However, his lab (McCausland Center for Brain Imaging) and the C-STAR collaboration are actively collecting EEG data that may become publicly available in the future.

| Resource | Modality | Status | EEG Available |
|----------|----------|--------|---------------|
| ARC Dataset (ds004884) | MRI | Public (OpenNeuro) | No |
| ABC@UofSC Repository | Multimodal | Partial public | Yes (not on OpenNeuro) |
| C-STAR Research Data | MRI + EEG | Research use | Not public |

**Implication**: There is no direct "EEG version of ARC" currently available. This represents both a limitation (no ready dataset) and an opportunity (our pipeline could support future releases).

---

## Chris Rorden's Current Focus

### Recent Publications (2024-2025)

Chris Rorden is Managing Director of the McCausland Center for Brain Imaging at the University of South Carolina. Recent work focuses on:

| Publication | Year | Focus | Modality |
|-------------|------|-------|----------|
| [MRIcroGL: voxel-based visualization](https://www.nature.com/articles/s41592-025-02763-7) | 2025 | Visualization tool | MRI |
| Mapping Post-Stroke Cerebellar Atrophy | 2025 | Lesion location | MRI |
| [Stroke Outcome Optimization Project](https://www.nature.com/articles/s41597-024-03667-5) | 2024 | Acute stroke | MRI |
| [Aphasia Recovery Cohort](https://www.nature.com/articles/s41597-024-03819-7) | 2024 | Chronic aphasia | MRI |

**Note**: His tool development (dcm2niix, MRIcroGL, etc.) is NIfTI/MRI-focused. No EEG-specific tools found.

### Lab Affiliations

| Role | Organization |
|------|--------------|
| Managing Director | McCausland Center for Brain Imaging (MCBI) |
| SmartState Endowed Chair | Brain Imaging, University of South Carolina |
| Principal Investigator | C-STAR (Center for the Study of Aphasia Recovery) |

---

## Available Datasets from Rorden Lab

### 1. Aphasia Recovery Cohort (ARC) - ds004884

The dataset we already support in `neuroimaging-go-brrrr`.

| Property | Value |
|----------|-------|
| **OpenNeuro ID** | [ds004884](https://openneuro.org/datasets/ds004884/versions/1.0.1) |
| **DOI** | 10.18112/openneuro.ds004884.v1.0.1 |
| **Subjects** | 230 chronic stroke survivors with aphasia |
| **Sessions** | 902 sessions |
| **Modalities** | T1w, T2w, FLAIR, DWI, fMRI, resting-state fMRI |
| **EEG** | **Not included** |
| **Format** | BIDS |
| **License** | CC0 |

**Why no EEG?**: The ARC dataset predates widespread BIDS-EEG adoption and was collected at sites with MRI infrastructure. EEG would require additional equipment and protocols.

### 2. Aging Brain Cohort (ABC@UofSC)

A newer multimodal dataset from the same lab, **includes EEG**.

| Property | Value |
|----------|-------|
| **Repository** | [abc.sc.edu](https://abc.sc.edu/) |
| **Paper** | [PMC12172904](https://pmc.ncbi.nlm.nih.gov/articles/PMC12172904/) |
| **Target N** | 800 cross-sectional, 200 longitudinal |
| **Age Range** | 20-80 years |
| **Focus** | Healthy aging (not stroke/aphasia) |
| **EEG** | **Yes** - resting-state EEG |
| **Other Modalities** | MRI, blood work, genetics, cognitive tests |
| **OpenNeuro** | **Not currently available** |

**Key Quote from paper**:
> "Data collected from the current study are stored primarily...in the ABC@UofSC Repository. This repository leverages the Research Electronic Data Capture (REDCap) system..."

**Limitations for our pipeline**:
1. Not stroke/aphasia focused (healthy aging)
2. EEG data stored separately from main repository
3. Not yet on OpenNeuro
4. May require data use agreement

**Potential**: If ABC releases BIDS-formatted EEG data to OpenNeuro, it would be an excellent candidate for our pipeline as it comes from the same trusted lab.

### 3. Stroke Outcome Optimization Project

| Property | Value |
|----------|-------|
| **Paper** | [Scientific Data 11, 839 (2024)](https://www.nature.com/articles/s41597-024-03667-5) |
| **Subjects** | 1,715 acute stroke patients |
| **Focus** | Acute ischemic stroke |
| **Modalities** | Clinical MRI |
| **EEG** | **Not included** |

---

## C-STAR: Center for the Study of Aphasia Recovery

### Overview

C-STAR is an NIH P50-funded center studying aphasia recovery, involving:

| Investigator | Role | Institution |
|--------------|------|-------------|
| Julius Fridriksson | Director | USC |
| Argye Hillis | Co-PI | Johns Hopkins |
| Chris Rorden | Co-PI | USC |
| Leonardo Bonilha | Co-PI | MUSC |
| Greg Hickok | Co-PI | UC Irvine |

### EEG Research at C-STAR

While C-STAR doesn't have a public EEG dataset, they conduct EEG research:

#### Vocal Auditory Feedback Studies

From [PMC10101924](https://pmc.ncbi.nlm.nih.gov/articles/PMC10101924/):
> "Individuals with post-stroke aphasia and matched neurotypical control subjects vocalized speech vowel sounds...while brain activity was recorded using electroencephalography (EEG)."

- 34 stroke subjects, 46 controls
- 64-channel EEG
- Event-related potentials (ERPs)
- Time-frequency analyses (theta, gamma bands)

#### Picture Naming Studies

From [PMC5835213](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5835213/):
> "A pilot study using high-density electroencephalography (EEG) and source analysis tracked and compared the spatiotemporal dynamics of cognitive processing between correct and incorrect responses made by two individuals with post-stroke aphasia during a picture naming task."

**Dataset Availability**: These appear to be research datasets not publicly released.

---

## EEG Aphasia/Stroke Datasets: Current Landscape

### Gap Analysis

| Dataset Type | OpenNeuro/NEMAR | Notes |
|--------------|-----------------|-------|
| MRI Stroke/Aphasia | Yes (ARC, ISLES24, etc.) | Well-supported |
| EEG Motor Imagery (Stroke) | Yes (Figshare) | BCI rehabilitation focus |
| **EEG Aphasia/Stroke** | **No** | Gap identified |
| EEG Language (Healthy) | Yes | Reading, speech decoding |

### Available Language-Related EEG Datasets

These are NOT aphasia/stroke but may be relevant for language processing research:

| Dataset | Description | Subjects | Link |
|---------|-------------|----------|------|
| ds005383 (TMNRED) | Chinese reading task | 30 | [NEMAR](https://nemar.org/dataexplorer/detail?dataset_id=ds005383) |
| ds006104 | Speech decoding (phoneme) | ~20 | [NEMAR](https://nemar.org/dataexplorer/detail?dataset_id=ds006104) |
| ds004771 | Python reading task (ERP) | Unknown | OpenNeuro |

### Motor Imagery Stroke EEG

The closest EEG + stroke datasets focus on **motor rehabilitation**, not language:

| Dataset | Paper | Focus | Format |
|---------|-------|-------|--------|
| MI-BCI Acute Stroke | [Scientific Data 2024](https://www.nature.com/articles/s41597-023-02787-8) | Motor imagery BCI | BIDS (Figshare) |
| Lower Limb MI EEG | [Scientific Data 2025](https://www.nature.com/articles/s41597-025-04826-y) | Lower limb rehabilitation | BIDS (Figshare) |

---

## Temple University Hospital (TUH) EEG Corpus

### Why TUH is Different

The user mentioned Temple University's EEG corpus. Key differences from Rorden lab work:

| Aspect | TUH Corpus | Rorden Lab (ARC/ABC) |
|--------|------------|----------------------|
| **Focus** | Clinical EEG (epilepsy, abnormalities) | Research (aphasia, aging) |
| **Scale** | 30,000+ recordings | Hundreds of subjects |
| **Access** | Requires agreement, internal server | OpenNeuro (CC0) |
| **Collaboration** | Limited open-source engagement | Active open-source (BIDS, tools) |
| **Aphasia Data** | Incidental (not focus) | Primary focus |

**Recommendation**: While TUH is valuable, the licensing and collaboration model differs significantly from the open-science approach we follow with Rorden lab datasets. Prioritize datasets with open licenses and BIDS compliance.

---

## Future Opportunities

### 1. ABC@UofSC EEG Release

**Probability**: Medium
**Timeline**: Unknown

If the ABC study releases BIDS-formatted resting-state EEG to OpenNeuro:
- Would be from trusted lab
- 800 subjects (when complete)
- Would establish EEG precedent
- Not aphasia-focused but still valuable

### 2. C-STAR EEG Dataset

**Probability**: Low (near-term), Medium (long-term)
**Timeline**: Unknown

A dedicated aphasia EEG dataset from C-STAR would be ideal:
- Directly relevant to ARC population
- Same PIs and protocols
- Would fill the EEG aphasia gap

### 3. External Aphasia EEG Datasets

Monitor for new releases on:
- OpenNeuro (search: EEG + language + stroke)
- NEMAR (EEG-specific)
- Figshare (supplementary datasets)
- Scientific Data publications

---

## Implications for `neuroimaging-go-brrrr`

### Current Strategy

1. **Continue MRI focus**: ARC, ISLES24 remain priority
2. **Build EEG infrastructure**: Prepare for future datasets
3. **Monitor ABC**: Watch for OpenNeuro release
4. **Generic EEG support**: Design for any BIDS-EEG dataset

### Recommended First EEG Datasets

Given the absence of Rorden-lab EEG datasets, prioritize:

| Priority | Dataset | Rationale |
|----------|---------|-----------|
| 1 | PhysioNet Motor Imagery | Classic benchmark, 109 subjects |
| 2 | ds005383 (TMNRED) | Language-related, BIDS, recent |
| 3 | ds006104 (Speech decoding) | Speech/language focus, BIDS |
| 4 | ABC@UofSC (when available) | Same lab, high trust |

---

## Sources

### Chris Rorden Publications
- [MRIcroGL: Nature Methods 2025](https://www.nature.com/articles/s41592-025-02763-7)
- [ResearchGate Profile](https://www.researchgate.net/profile/Chris-Rorden)
- [GitHub: neurolabusc](https://github.com/neurolabusc)
- [GitHub: rordenlab](https://github.com/rordenlab)

### Datasets
- [Aphasia Recovery Cohort (OpenNeuro)](https://openneuro.org/datasets/ds004884/versions/1.0.1)
- [ABC@UofSC Repository](https://abc.sc.edu/)
- [ABC Paper (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12172904/)

### C-STAR & Related
- [C-STAR Website](https://cstar.sc.edu/)
- [McCausland Center](https://www.mccauslandcenter.sc.edu/)
- [EEG Vocal Feedback Study (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10101924/)
- [Pre-articulatory EEG Study (PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5835213/)

### EEG Datasets
- [NEMAR ds005383 (TMNRED)](https://nemar.org/dataexplorer/detail?dataset_id=ds005383)
- [NEMAR ds006104 (Speech decoding)](https://nemar.org/dataexplorer/detail?dataset_id=ds006104)
- [MI-BCI Acute Stroke Paper](https://www.nature.com/articles/s41597-023-02787-8)
