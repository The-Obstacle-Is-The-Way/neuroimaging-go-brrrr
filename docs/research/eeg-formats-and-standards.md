# EEG Formats and Standards Research

> Research compiled: December 2025
> Purpose: Evaluate EEG data formats for integration into `neuroimaging-go-brrrr` pipeline

## Executive Summary

EEG data has a well-established standard through **BIDS-EEG**, mirroring our current NIfTI/BIDS workflow. The recommended formats are **EDF+** (European Data Format) and **BrainVision** (.vhdr/.vmrk/.eeg), with the MNE-Python ecosystem providing excellent tooling for reading, writing, and converting between formats.

**Key Finding**: HuggingFace `datasets` does not have a native `Eeg()` feature type like they do for `Nifti()`. EEG datasets on HuggingFace currently use `Array2D`/`Array3D` or store raw files. This represents a **gap we could fill**.

---

## BIDS-EEG Specification

The Brain Imaging Data Structure (BIDS) was extended to EEG in 2019:

> Pernet, C. R., Appelhoff, S., Gorgolewski, K.J., Flandin, G., Phillips, C., Delorme, A., Oostenveld, R. (2019). EEG-BIDS, an extension to the brain imaging data structure for electroencephalography. *Scientific Data*, 6. doi: [10.1038/s41597-019-0104-8](https://doi.org/10.1038/s41597-019-0104-8)

### Required File Formats

BIDS-EEG **MUST** use one of:

| Format | Extension | Bits | Recommended |
|--------|-----------|------|-------------|
| European Data Format+ | `.edf` | 16 | ✅ Yes |
| BrainVision Core | `.vhdr`/`.vmrk`/`.eeg` | Variable | ✅ Yes |
| EEGLAB | `.set` | Variable | No |
| Biosemi BDF | `.bdf` | 24 | No |

### BIDS-EEG File Structure

```text
sub-01/
├── ses-01/
│   └── eeg/
│       ├── sub-01_ses-01_task-rest_eeg.edf       # Raw EEG data
│       ├── sub-01_ses-01_task-rest_eeg.json      # Recording metadata
│       ├── sub-01_ses-01_task-rest_channels.tsv  # Channel information
│       ├── sub-01_ses-01_task-rest_electrodes.tsv # Electrode positions
│       └── sub-01_ses-01_task-rest_events.tsv    # Event markers
├── sub-01_scans.tsv                              # Session dates
└── sub-01_participants.tsv                       # Demographics
```

### Key Metadata Files

**`_channels.tsv`** (Required columns):
- `name`: Channel name (e.g., "Fp1", "Cz")
- `type`: Channel type (e.g., "EEG", "EOG", "ECG")
- `units`: Measurement units (e.g., "µV")

**`_electrodes.tsv`**:
- `name`: Electrode name
- `x`, `y`, `z`: Position coordinates
- `impedance`: Recording impedance

**`_eeg.json`** (Sidecar):
```json
{
  "TaskName": "rest",
  "SamplingFrequency": 256,
  "PowerLineFrequency": 60,
  "EEGReference": "Cz",
  "SoftwareFilters": {
    "HighPass": {"Cutoff": 0.1},
    "LowPass": {"Cutoff": 100}
  }
}
```

---

## File Format Comparison

### EDF+ (European Data Format Plus)

**Advantages**:
- Widely supported across platforms
- Simple, well-documented format
- Annotation channels for events
- Open standard since 1992

**Disadvantages**:
- 16-bit resolution only
- Cannot store epoched/segmented data natively
- No electrode location storage
- Limited metadata capacity

**Python I/O**:
- Read: `mne.io.read_raw_edf()`
- Write: `pyedflib` or `mne.export.export_raw()` (limited)

### BrainVision Core Data Format

**Advantages**:
- Can store epoched/segmented data
- Variable bit depth
- Adopted by BIDS for EEG and iEEG
- Good metadata support in header

**Disadvantages**:
- Three files required (.vhdr, .vmrk, .eeg)
- Renaming requires editing all three files
- Proprietary origin (Brain Products GmbH)

**Python I/O**:
- Read: `mne.io.read_raw_brainvision()`
- Write: `pybv.write_brainvision()` or `mne.export.export_raw()`

### FIF (Functional Image File)

**Advantages**:
- Native MNE-Python format
- Comprehensive metadata support
- Stores epoched data, source estimates, etc.
- Excellent documentation

**Disadvantages**:
- **Not BIDS-EEG compliant** (only BIDS-MEG)
- MNE ecosystem lock-in
- Conversion may lose precision

**Python I/O**:
- Read: `mne.io.read_raw_fif()`
- Write: `raw.save()`

### Format Recommendation for Our Pipeline

**Primary**: BrainVision Core Data Format
- BIDS-compliant
- Best metadata support
- `pybv` is maintained by BIDS standard team

**Secondary**: EDF+
- Maximum compatibility
- Simpler structure

---

## Comparison: NWB vs BIDS for EEG

| Aspect | BIDS-EEG | NWB |
|--------|----------|-----|
| **Primary Use** | Human neuroimaging | Animal neurophysiology |
| **File Structure** | Directory + naming conventions | Single HDF5 file |
| **EEG Support** | First-class (BIDS-EEG spec) | Limited (iEEG support via DANDI) |
| **Data Storage** | Domain-specific formats (EDF, BrainVision) | Within NWB file (HDF5) |
| **Tooling** | MNE-BIDS, EEGLAB, FieldTrip | PyNWB |
| **Archives** | OpenNeuro, NEMAR | DANDI |

**Recommendation**: Use **BIDS-EEG** for human EEG data (aligns with our existing BIDS workflow).

---

## Key Python Libraries

### Core Libraries

| Library | Purpose | Maintainer |
|---------|---------|------------|
| [MNE-Python](https://mne.tools/) | EEG/MEG analysis | MNE community |
| [MNE-BIDS](https://mne.tools/mne-bids/) | BIDS ↔ MNE conversion | MNE community |
| [pybv](https://github.com/bids-standard/pybv) | BrainVision writing | BIDS standard |
| [pyedflib](https://pyedflib.readthedocs.io/) | EDF/BDF reading/writing | Community |

### Installation

```bash
# Core dependencies for EEG support
uv add mne mne-bids pybv pyedflib
```

---

## HuggingFace Integration Gap

### Current State

HuggingFace `datasets` has:
- `Audio()` feature type for audio files
- `Image()` feature type for images
- `Nifti()` feature type for neuroimaging (NIfTI)
- **No `Eeg()` feature type**

### How EEG is Currently Stored on HuggingFace

Existing EEG datasets use workarounds:

1. **Array2D/Array3D**: Store raw numpy arrays
   ```python
   Features({
       "eeg": Array2D(shape=(None, 64), dtype="float32"),  # (time, channels)
       "label": ClassLabel(...)
   })
   ```

2. **Raw Files**: Store .edf/.fif files as binary
   ```python
   Features({
       "eeg_file": Value("string"),  # Path to .edf file
       "label": ClassLabel(...)
   })
   ```

3. **BIDS-Compliant Folders**: Entire BIDS structure uploaded

### Opportunity

Creating an `Eeg()` feature type for HuggingFace would:
- Enable lazy loading of EEG files (like `Audio()` does)
- Preserve metadata (sampling rate, channels, events)
- Allow filtering/slicing without loading full data
- Match the existing `Nifti()` pattern we're using

---

## Sources

- [BIDS-EEG Specification](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electroencephalography.html)
- [EEG-BIDS Paper (Scientific Data)](https://www.nature.com/articles/s41597-019-0104-8)
- [MNE-Python Documentation](https://mne.tools/stable/index.html)
- [MNE-BIDS Documentation](https://mne.tools/mne-bids/stable/index.html)
- [pybv GitHub](https://github.com/bids-standard/pybv)
- [NWB vs BIDS FAQ](https://nwb.org/faq/comparison_to_other_standards/)
- [Brain Products BIDS Press Release](https://pressrelease.brainproducts.com/bids/)
