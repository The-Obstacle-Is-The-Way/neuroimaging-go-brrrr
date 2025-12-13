# EEG Datasets Catalog

> Research compiled: December 2025
> Purpose: Identify candidate EEG datasets for integration into `neuroimaging-go-brrrr`

## Executive Summary

There are **hundreds of publicly available EEG datasets** across multiple repositories. The largest repositories are:

| Repository | Datasets | Format | Primary Focus |
|------------|----------|--------|---------------|
| **OpenNeuro** | 60+ EEG | BIDS | Research neuroimaging |
| **NEMAR** | ~200 | BIDS | M/EEG archive |
| **TUH Corpus** | 30,000+ recordings | EDF | Clinical EEG |
| **PhysioNet** | Varies | EDF | Physiological signals |
| **MOABB** | 30+ | Various | BCI benchmarks |

**Recommended First Target**: OpenNeuro datasets (already BIDS-compliant, aligns with our current workflow).

---

## Priority Datasets for Implementation

### Tier 1: High-Value BIDS Datasets

#### 1. EEG Motor Movement/Imagery Dataset (PhysioBank)

| Property | Value |
|----------|-------|
| **Source** | [PhysioNet](https://physionet.org/content/eegmmidb/1.0.0/) |
| **Subjects** | 109 |
| **Tasks** | Eyes open/closed, motor execution/imagery |
| **Channels** | 64 |
| **Format** | EDF (convertible to BIDS) |
| **License** | Open |
| **Use Case** | BCI, motor imagery decoding |

**Why**: Classic benchmark dataset, widely used in EEG research and foundation model pretraining.

#### 2. Healthy Brain Network (HBN)

| Property | Value |
|----------|-------|
| **Source** | [Child Mind Institute](http://fcon_1000.projects.nitrc.org/indi/cmi_healthy_brain_network/) |
| **Subjects** | 1,000+ |
| **Tasks** | Rest, task EEG |
| **Channels** | 128 |
| **Format** | BIDS |
| **License** | CC0 |
| **Use Case** | Developmental neuroscience |

**Why**: Large-scale, well-curated, pediatric focus (unique).

#### 3. Temple University Hospital (TUH) EEG Corpus

| Property | Value |
|----------|-------|
| **Source** | [TUH](https://isip.piconepress.com/projects/tuh_eeg/) |
| **Recordings** | 30,000+ |
| **Variants** | TUEG, TUAB, TUAR, TUEP, TUEV, TUSZ, TUSL |
| **Format** | EDF |
| **License** | Research use |
| **Use Case** | Clinical EEG, seizure detection, abnormality detection |

**Why**: Largest clinical EEG corpus, critical for medical AI.

#### 4. LEMON (Leipzig Mind-Brain-Body)

| Property | Value |
|----------|-------|
| **Source** | [Max Planck Institute](https://www.nitrc.org/projects/mpi_lemon/) |
| **Subjects** | 228 (young: 154, elderly: 74) |
| **Tasks** | Rest |
| **Channels** | 62 |
| **Format** | BIDS |
| **License** | CC BY |
| **Use Case** | Aging, lifespan neuroscience |

**Why**: Cross-sectional age groups, multimodal (EEG + MRI).

---

## Repository Deep Dives

### OpenNeuro

**URL**: [openneuro.org](https://openneuro.org/)

OpenNeuro is the primary repository for BIDS-formatted neuroimaging data, including EEG.

#### Notable EEG Datasets on OpenNeuro

| Dataset ID | Description | Subjects | Size |
|------------|-------------|----------|------|
| ds003490 | EEG resting state | 43 | ~2 GB |
| ds003505 | EEG during RSVP | 50 | ~3 GB |
| ds003420 | EEG/MEG perceptual task | 19 | ~5 GB |
| ds003768 | EEG during sleep + fMRI | 33 | ~8 GB |
| ds004186 | EEG visual working memory | 24 | ~2 GB |

**Access Pattern**:
```bash
# Using openneuro-py
pip install openneuro-py
openneuro download --dataset ds003490 /data/openneuro/
```

### NEMAR (NeuroElectroMagnetic Archive)

**URL**: [nemar.org](https://nemar.org/)

NEMAR is specifically designed for M/EEG data sharing, built on OpenNeuro infrastructure.

#### Features

- ~200 BIDS-formatted M/EEG experiments
- Integrated compute resources via Brainlife.io
- Optimized for electrophysiology data

### PhysioNet

**URL**: [physionet.org](https://physionet.org/)

Primary repository for physiological signal data.

#### Notable EEG Datasets

| Dataset | Description | License |
|---------|-------------|---------|
| eegmmidb | Motor movement/imagery | Open |
| chb-mit | Seizure detection | Open |
| siena-scalp-eeg | Epilepsy | Open |
| sleep-edfx | Sleep staging | Open |

### MOABB (Mother of All BCI Benchmarks)

**URL**: [moabb.neurotechx.com](https://moabb.neurotechx.com/)

Curated collection of BCI datasets with standardized evaluation.

```python
import moabb
from moabb.datasets import BNCI2014001

dataset = BNCI2014001()
dataset.download()  # Automatic download
```

---

## Dataset Categories

### By Application

#### Brain-Computer Interfaces (BCI)

| Dataset | Task | Subjects | Notes |
|---------|------|----------|-------|
| BNCI2014-001 | Motor imagery | 9 | 4-class |
| BNCI2014-002 | Motor imagery | 14 | 2-class |
| PhysioNet MI | Motor imagery | 109 | 64-channel |
| GigaDB MI | Motor imagery | 52 | Korean cohort |

#### Clinical EEG

| Dataset | Condition | Size | Notes |
|---------|-----------|------|-------|
| TUH Abnormal | Various abnormalities | 2,993 | Binary classification |
| TUH Seizure | Epilepsy | 4,597 | Seizure detection |
| CHB-MIT | Epilepsy | 23 | Pediatric |
| Siena Scalp | Epilepsy | 14 | Adult |

#### Sleep

| Dataset | Stages | Subjects | Notes |
|---------|--------|----------|-------|
| Sleep-EDF | 5-class | 197 | Gold standard |
| SHHS | 5-class | 5,804 | Large-scale |
| MASS | 5-class | 200 | Montreal |

#### Cognitive/Affective

| Dataset | Task | Subjects | Notes |
|---------|------|----------|-------|
| DEAP | Emotion | 32 | Music videos |
| SEED | Emotion | 15 | Movie clips |
| DREAMER | Emotion | 23 | Movie clips |

---

## Dataset Selection Criteria

For `neuroimaging-go-brrrr` integration, prioritize datasets that:

1. **Already BIDS-compliant** (or easily convertible)
2. **Open license** (CC0, CC BY, or equivalent)
3. **Sufficient size** (20+ subjects)
4. **Research relevance** (high citation, benchmark status)
5. **Good metadata** (demographics, task descriptions)

### Recommended Implementation Order

| Priority | Dataset | Rationale |
|----------|---------|-----------|
| 1 | PhysioNet Motor Imagery | Classic benchmark, 109 subjects |
| 2 | OpenNeuro ds003490 | BIDS-native, resting state |
| 3 | LEMON | Large, well-documented, age diversity |
| 4 | TUH Abnormal | Clinical relevance |

---

## Data Size Estimates

| Dataset | Raw Size | Compressed | Notes |
|---------|----------|------------|-------|
| PhysioNet MI (109 subj) | ~5 GB | ~2 GB | EDF |
| OpenNeuro ds003490 | ~2 GB | ~1 GB | BIDS |
| LEMON EEG | ~15 GB | ~6 GB | BIDS |
| TUH Abnormal | ~35 GB | ~15 GB | EDF |

**Note**: EEG datasets are generally much smaller than NIfTI datasets due to lower dimensionality (channels × time vs. 3D/4D volumes).

---

## Existing HuggingFace EEG Datasets

Several EEG datasets already exist on HuggingFace:

| Dataset | Description | Format |
|---------|-------------|--------|
| [Haitao999/things-eeg](https://huggingface.co/datasets/Haitao999/things-eeg) | Visual perception | float16 arrays |
| [MaRez10/EEG_Pain_Perception](https://huggingface.co/datasets/MaRez10/EEG_Pain_Perception) | Pain perception | BIDS-compliant |
| [DavidVivancos/MindBigData2023_MNIST-8B](https://huggingface.co/datasets/DavidVivancos/MindBigData2023_MNIST-8B) | Digit imagery | 128 channels |
| [neurofusion/eeg-restingstate](https://huggingface.co/datasets/neurofusion/eeg-restingstate) | Resting state | Preprocessed |

---

## Download Scripts

### OpenNeuro (via openneuro-py)

```bash
#!/bin/bash
pip install openneuro-py

# Download specific dataset
openneuro download --dataset ds003490 \
    --target_dir /data/openneuro/ds003490

# Download with filtering
openneuro download --dataset ds003490 \
    --include sub-0*/eeg/ \
    --target_dir /data/openneuro/ds003490
```

### PhysioNet (via wget)

```bash
#!/bin/bash
# EEG Motor Movement/Imagery Dataset
wget -r -N -c -np \
    https://physionet.org/files/eegmmidb/1.0.0/ \
    -P /data/physionet/
```

### MOABB (via Python)

```python
import moabb
from moabb.datasets import BNCI2014001, PhysionetMI

# Download BCI Competition IV 2a
dataset = BNCI2014001()
dataset.download()

# Download PhysioNet Motor Imagery
dataset = PhysionetMI()
dataset.download()
```

---

## Sources

- [OpenLists/ElectrophysiologyData](https://github.com/openlists/ElectrophysiologyData) - Comprehensive list
- [OpenNeuro](https://openneuro.org/) - BIDS repository
- [NEMAR](https://nemar.org/) - M/EEG archive
- [PhysioNet](https://physionet.org/) - Physiological signals
- [TUH EEG Corpus](https://isip.piconepress.com/projects/tuh_eeg/) - Clinical EEG
- [MOABB](https://moabb.neurotechx.com/) - BCI benchmarks
- [FieldTrip Open Data FAQ](https://www.fieldtriptoolbox.org/faq/other/open_data/)
