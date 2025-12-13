# MNE Ecosystem Overview

> Research compiled: December 2025
> Purpose: Understand the MNE-Python ecosystem for EEG/MEG support in `neuroimaging-go-brrrr`

## Executive Summary

**MNE-Python** is the de facto standard for EEG/MEG analysis in Python, with:
- 10+ years of active development
- BSD-3-Clause license (permissive)
- Extensive format support (20+ EEG file formats)
- First-class BIDS integration via **MNE-BIDS**

This is the equivalent of `nibabel` for NIfTI in the EEG world.

---

## MNE-Python Core

### Overview

| Property | Value |
|----------|-------|
| **Package** | `mne` |
| **Current Version** | 1.11.0 (Dec 2025) |
| **License** | BSD-3-Clause |
| **GitHub** | [mne-tools/mne-python](https://github.com/mne-tools/mne-python) |
| **Documentation** | [mne.tools](https://mne.tools/stable/index.html) |

### Supported Modalities

- **EEG** (Electroencephalography) ✅
- **MEG** (Magnetoencephalography) ✅
- **sEEG** (Stereo-EEG / depth electrodes) ✅
- **ECoG** (Electrocorticography) ✅
- **fNIRS** (Functional near-infrared spectroscopy) ✅

### Core Data Structures

```python
import mne

# Raw continuous data
raw = mne.io.read_raw_edf("data.edf", preload=True)
# Shape: (n_channels, n_times)

# Epoched data (segmented around events)
epochs = mne.Epochs(raw, events, tmin=-0.2, tmax=0.5)
# Shape: (n_epochs, n_channels, n_times)

# Averaged evoked response
evoked = epochs.average()
# Shape: (n_channels, n_times)

# Source estimates (localized brain activity)
stc = mne.minimum_norm.apply_inverse(evoked, inverse_operator)
# Shape: (n_vertices, n_times)
```

---

## Supported File Formats

### EEG Formats

| Format | Function | Notes |
|--------|----------|-------|
| **EDF/EDF+** | `mne.io.read_raw_edf()` | ✅ BIDS recommended |
| **BrainVision** | `mne.io.read_raw_brainvision()` | ✅ BIDS recommended |
| **EEGLAB .set** | `mne.io.read_raw_eeglab()` | Popular MATLAB format |
| **Biosemi BDF** | `mne.io.read_raw_bdf()` | 24-bit EDF variant |
| **Neuroscan CNT** | `mne.io.read_raw_cnt()` | Legacy format |
| **EGI** | `mne.io.read_raw_egi()` | NetStation format |
| **Nihon Kohden** | `mne.io.read_raw_nihon()` | Clinical EEG |
| **Persyst** | `mne.io.read_raw_persyst()` | Clinical EEG |
| **Micromed** | `mne.io.read_raw_micromed()` | Clinical EEG |

### MEG Formats

| Format | Function | Notes |
|--------|----------|-------|
| **FIF** | `mne.io.read_raw_fif()` | Native MNE/Elekta |
| **CTF** | `mne.io.read_raw_ctf()` | CTF systems |
| **BTi/4D** | `mne.io.read_raw_bti()` | BTi/4D Neuroimaging |
| **KIT** | `mne.io.read_raw_kit()` | KIT/Yokogawa |

### Writing Formats

```python
# Export to BrainVision (BIDS-compliant)
mne.export.export_raw("output.vhdr", raw, fmt="brainvision")

# Export to EDF
mne.export.export_raw("output.edf", raw, fmt="edf")

# Save as FIF (native MNE)
raw.save("output_raw.fif")
```

---

## MNE-BIDS

### Overview

| Property | Value |
|----------|-------|
| **Package** | `mne-bids` |
| **Current Version** | 0.17.0 |
| **GitHub** | [mne-tools/mne-bids](https://github.com/mne-tools/mne-bids) |
| **Documentation** | [mne.tools/mne-bids](https://mne.tools/mne-bids/stable/index.html) |

### Key Functions

```python
import mne_bids

# Convert any EEG file to BIDS format
mne_bids.write_raw_bids(
    raw,                          # MNE Raw object
    bids_path,                    # BIDSPath object
    format="BrainVision",         # Output format
    overwrite=True
)

# Read BIDS dataset directly
raw = mne_bids.read_raw_bids(bids_path)

# Validate BIDS dataset
mne_bids.validate_bids(bids_root)
```

### BIDSPath

```python
from mne_bids import BIDSPath

bids_path = BIDSPath(
    subject="01",
    session="01",
    task="rest",
    datatype="eeg",
    root="/data/bids"
)
# /data/bids/sub-01/ses-01/eeg/sub-01_ses-01_task-rest_eeg.edf
```

### Automatic Format Conversion

MNE-BIDS can convert non-BIDS formats to BIDS-compliant formats:

```python
# Read proprietary format
raw = mne.io.read_raw_nihon("nihon_kohden_file.eeg")

# Convert to BrainVision format during BIDS write
mne_bids.write_raw_bids(
    raw,
    bids_path,
    format="BrainVision"  # Converts from Nihon Kohden to BrainVision
)
```

---

## Related Tools in MNE Ecosystem

### pybv (BrainVision Writer)

```python
import pybv

pybv.write_brainvision(
    data=numpy_array,           # (n_channels, n_times)
    sfreq=256,                  # Sampling frequency
    ch_names=["Fp1", "Cz"],     # Channel names
    fname_base="output",
    folder_out="./output",
    events=[(100, 0, "stimulus")]  # (sample, duration, description)
)
```

### pyedflib (EDF Reader/Writer)

```python
import pyedflib

# Write EDF file
with pyedflib.EdfWriter("output.edf", n_channels=64) as f:
    f.setSignalHeaders(channel_headers)
    f.writeSamples(data)
```

### mne-bids-pipeline

Automated analysis pipeline for BIDS datasets:

```bash
# Run standardized preprocessing pipeline
mne_bids_pipeline --config=config.py
```

---

## Integration Strategy for neuroimaging-go-brrrr

### Parallel to NIfTI Pipeline

| NIfTI Pipeline | EEG Pipeline |
|----------------|--------------|
| `nibabel.load()` | `mne.io.read_raw_*()` |
| `datasets.Nifti()` | Custom `Eeg()` or `Array2D` |
| BIDS (NIfTI) | BIDS-EEG |
| OpenNeuro | OpenNeuro + NEMAR |

### Proposed Core Dependencies

```toml
[project.optional-dependencies]
eeg = [
    "mne>=1.11.0",
    "mne-bids>=0.17.0",
    "pybv>=0.8.0",
    "pyedflib>=0.1.36",
]
```

### Data Flow (Proposed)

```text
BIDS-EEG Dataset (Local)
        │
        ▼ read_raw_bids() / custom reader
mne.io.Raw object
        │
        ▼ extract_metadata() + raw.get_data()
pandas DataFrame (paths + metadata) + numpy arrays
        │
        ▼ build_hf_dataset()
datasets.Dataset with Array2D or custom Eeg() features
        │
        ▼ push_dataset_to_hub()
HuggingFace Hub
```

---

## Code Examples

### Reading BIDS-EEG Dataset

```python
from mne_bids import BIDSPath, read_raw_bids

bids_root = "/data/openneuro/ds003490"  # BIDS-EEG dataset

# Get all subjects
subjects = mne_bids.get_entity_vals(bids_root, "subject")

for sub in subjects:
    bids_path = BIDSPath(
        subject=sub,
        task="rest",
        datatype="eeg",
        root=bids_root
    )

    # Read raw EEG data
    raw = read_raw_bids(bids_path)

    # Access metadata
    print(f"Channels: {raw.ch_names}")
    print(f"Sample rate: {raw.info['sfreq']} Hz")
    print(f"Duration: {raw.times[-1]:.1f} s")

    # Get data as numpy array
    data, times = raw.get_data(return_times=True)
    # data shape: (n_channels, n_times)
```

### Converting to HuggingFace Dataset

```python
import mne
from mne_bids import read_raw_bids, BIDSPath
from datasets import Dataset, Features, Value, Array2D

def build_eeg_dataset(bids_root: str) -> Dataset:
    """Build HuggingFace dataset from BIDS-EEG."""

    subjects = mne_bids.get_entity_vals(bids_root, "subject")

    records = []
    for sub in subjects:
        bids_path = BIDSPath(
            subject=sub,
            task="rest",
            datatype="eeg",
            root=bids_root
        )

        raw = read_raw_bids(bids_path, verbose=False)
        data = raw.get_data()  # (n_channels, n_times)

        records.append({
            "subject_id": f"sub-{sub}",
            "eeg": data.T,  # (n_times, n_channels) for Array2D
            "sfreq": raw.info["sfreq"],
            "ch_names": raw.ch_names,
            "duration_sec": raw.times[-1],
        })

    features = Features({
        "subject_id": Value("string"),
        "eeg": Array2D(shape=(None, len(raw.ch_names)), dtype="float32"),
        "sfreq": Value("float32"),
        "ch_names": Sequence(Value("string")),
        "duration_sec": Value("float32"),
    })

    return Dataset.from_list(records, features=features)
```

---

## Sources

- [MNE-Python Documentation](https://mne.tools/stable/index.html)
- [MNE-Python GitHub](https://github.com/mne-tools/mne-python)
- [MNE-BIDS Documentation](https://mne.tools/mne-bids/stable/index.html)
- [MNE-BIDS GitHub](https://github.com/mne-tools/mne-bids)
- [pybv GitHub](https://github.com/bids-standard/pybv)
- [pyedflib Documentation](https://pyedflib.readthedocs.io/)
- [MNE Tutorial: Importing EEG Data](https://mne.tools/stable/auto_tutorials/io/20_reading_eeg_data.html)
- [MNE-BIDS: Convert EEG to BIDS](https://mne.tools/mne-bids/stable/auto_examples/convert_eeg_to_bids.html)
