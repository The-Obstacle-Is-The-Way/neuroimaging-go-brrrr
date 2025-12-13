# EEG Foundation Models Landscape

> Research compiled: December 2025
> Purpose: Survey EEG foundation models for context on the ML ecosystem

## Executive Summary

EEG foundation models are an **emerging field** (2024-2025), with several large-scale pretrained models now available:

| Model | Pretraining Scale | Key Innovation | Status |
|-------|-------------------|----------------|--------|
| **REVE** | 25,000 subjects, 60k hours | 4D positional encoding | State-of-the-art |
| **EEGPT** | Large-scale | Autoregressive pretraining | Published |
| **LCM** | Large-scale | Temporal+spectral attention | arXiv 2025 |
| **EEGFormer** | Compound EEG | Transferable representations | ICLR 2024 |

**Key Insight**: These models benefit from standardized datasets on HuggingFace Hub. Our EEG pipeline would enable easier consumption of these foundation models.

---

## Why Foundation Models Matter for Our Pipeline

Foundation models like REVE and EEGPT are trained on **massive aggregated EEG datasets**. Making more EEG data available on HuggingFace Hub in a standardized format:

1. **Enables fine-tuning** on downstream tasks
2. **Facilitates benchmarking** across models
3. **Reduces preprocessing burden** for researchers
4. **Aligns with the NIfTI pattern** we've already established

---

## Major EEG Foundation Models

### 1. REVE (2025)

**Representation for EEG with Versatile Embeddings**

| Property | Value |
|----------|-------|
| **Paper** | [arXiv:2510.21585](https://arxiv.org/abs/2510.21585) |
| **Scale** | 25,000 subjects, 60,000+ hours |
| **Datasets** | 92 datasets |
| **Architecture** | Transformer with 4D positional encoding |
| **Pretraining** | Masked autoencoding |

**Key Innovation**: Novel 4D positional encoding that handles arbitrary electrode arrangements and variable-length recordings.

**Downstream Tasks** (State-of-the-art on 10 tasks):
- Motor imagery classification
- Seizure detection
- Sleep staging
- Cognitive load estimation
- Emotion recognition

**Quote from paper**:
> "REVE achieves state-of-the-art results on 10 downstream EEG tasks... with strong generalization even with little to no fine-tuning."

---

### 2. EEGPT (2024)

**EEG Generalist Pretrained Transformer**

| Property | Value |
|----------|-------|
| **Paper** | [arXiv](https://arxiv.org/abs/2401.10278) |
| **Architecture** | Autoregressive transformer |
| **Key Feature** | Local spatio-temporal embedding |

**Approach**: Unlike models that learn from raw waveforms, EEGPT uses high-SNR feature representations for self-supervised learning.

**Key Innovations**:
- Masking + spatio-temporal alignment
- Universal electrode mapping (cross-device compatibility)
- Noise interference reduction

---

### 3. Large Cognition Model (LCM) (2025)

**Towards Pretrained EEG Foundation Model**

| Property | Value |
|----------|-------|
| **Paper** | [arXiv:2502.17464](https://arxiv.org/html/2502.17464v1) |
| **Architecture** | Transformer with temporal + spectral attention |
| **Applications** | Cognitive state decoding, disease classification, neurofeedback |

**Key Innovation**: Integrates both **temporal attention** (time-domain patterns) and **spectral attention** (frequency-domain features like alpha, beta rhythms).

---

### 4. EEGFormer (2024)

**Transferable and Interpretable Large-Scale EEG Foundation Model**

| Property | Value |
|----------|-------|
| **Paper** | [arXiv:2401.10278](https://arxiv.org/abs/2401.10278) |
| **Venue** | ICLR 2024 |
| **Training** | Self-supervised on compound EEG data |
| **Key Feature** | Interpretability via self-supervised learning |

**Evaluation**: Demonstrated transferable anomaly detection with interpretable attention patterns.

---

### 5. Other Notable Models

| Model | Year | Focus | Reference |
|-------|------|-------|-----------|
| **ALFEE** | 2025 | Adaptive large foundation model | arXiv |
| **Large Brain Model** | 2024 | Generic BCI representations | ICLR |
| **CBraMod** | 2024 | Criss-cross brain architecture | arXiv |
| **UniEEG** | 2025 | Electrode-wise time-frequency pretraining | arXiv |

---

## Key Challenges in EEG Foundation Models

### 1. Low Signal-to-Noise Ratio

EEG signals have inherently low SNR compared to images or text:
- Muscle artifacts (EMG)
- Eye movement artifacts (EOG)
- Line noise (50/60 Hz)
- Electrode drift

**Implication**: Preprocessing quality dramatically affects model performance.

### 2. Inter-Subject Variability

Brain anatomy and physiology vary across individuals:
- Skull thickness affects signal conduction
- Brain folding patterns differ
- Individual alpha frequency varies (8-13 Hz range)

**Implication**: Models need subject-adaptation or robust pretraining.

### 3. Montage Heterogeneity

Different EEG systems use different:
- Number of channels (8 to 256)
- Electrode positions
- Reference schemes
- Sampling rates

**Implication**: Foundation models need electrode-agnostic architectures (like REVE's 4D encoding).

### 4. Recording Format Variability

Data comes in many formats:
- EDF, BDF, BrainVision, FIF, SET, CNT, etc.

**Implication**: Standardization pipelines (like `neuroimaging-go-brrrr`) are essential.

---

## Review Papers

### "A Simple Review of EEG Foundation Models" (2025)

**Reference**: [arXiv:2504.20069](https://arxiv.org/abs/2504.20069)

Examines 14 EEG foundation models:

| Aspect | Finding |
|--------|---------|
| **Typical Scale** | Hundreds to ~15,000 subjects |
| **Max Duration** | 27,062 hours |
| **Common Strategy** | Masked reconstruction |
| **Architecture** | Transformer-based |

### "Foundation Models for EEG Decoding" (2025)

**Reference**: [PubMed 41145005](https://pubmed.ncbi.nlm.nih.gov/41145005/)

Current progress and prospective research directions.

### "Brain Foundation Models: A Survey" (2025)

**Reference**: [arXiv:2503.00580](https://arxiv.org/html/2503.00580v1)

Broader survey covering neural signal processing across modalities.

---

## Implications for neuroimaging-go-brrrr

### 1. Data Format Standardization is Critical

Foundation models benefit from:
- Consistent preprocessing
- Standardized channel layouts
- Metadata preservation (sampling rate, electrode positions)

**Our role**: Provide standardized BIDS-EEG → HuggingFace conversion.

### 2. Schema Design Should Support ML

Our HuggingFace schema should include:
- Raw EEG data (Array2D or custom type)
- Sampling frequency
- Channel names and positions
- Event markers
- Subject metadata (age, sex for bias analysis)

### 3. Consider Preprocessing Options

Many foundation models expect:
- Standardized reference (e.g., average reference)
- Band-pass filtering (0.5-100 Hz typical)
- Notch filtering (50/60 Hz)
- Artifact rejection

**Question**: Should we store raw only, or also preprocessed versions?

### 4. Enable Foundation Model Fine-tuning

Design data loaders that work with:
- PyTorch DataLoader
- HuggingFace Trainer
- Common preprocessing pipelines

---

## Model Availability

| Model | Weights Available | Code Available |
|-------|-------------------|----------------|
| REVE | Unknown | GitHub (pending) |
| EEGPT | HuggingFace (model hub) | GitHub |
| LCM | Unknown | Unknown |
| EEGFormer | Unknown | GitHub |

**Note**: Unlike NLP/CV, EEG foundation model weights are not as widely shared. This is an area of active development.

---

## Future Directions

### 1. Unified Benchmarks

Need standardized evaluation suites (like GLUE for NLP):
- MOABB provides this for BCI
- No equivalent for clinical EEG

### 2. Cross-Dataset Pretraining

Aggregating data across:
- OpenNeuro + NEMAR
- PhysioNet
- TUH Corpus
- Institutional data

### 3. Multimodal Models

Combining EEG with:
- fMRI (temporal resolution of EEG + spatial resolution of fMRI)
- Audio (for speech decoding)
- Video (for event alignment)

---

## Sources

- [REVE Paper (arXiv:2510.21585)](https://arxiv.org/abs/2510.21585)
- [Large Cognition Model (arXiv:2502.17464)](https://arxiv.org/html/2502.17464v1)
- [EEGFormer (arXiv:2401.10278)](https://arxiv.org/abs/2401.10278)
- [EEG Foundation Models Review (arXiv:2504.20069)](https://arxiv.org/abs/2504.20069)
- [Brain Foundation Models Survey (arXiv:2503.00580)](https://arxiv.org/html/2503.00580v1)
- [Foundation Models for EEG Decoding (PubMed)](https://pubmed.ncbi.nlm.nih.gov/41145005/)
- [HuggingFace Daily Papers - EEG](https://huggingface.co/papers?q=EEG+foundation+models)
