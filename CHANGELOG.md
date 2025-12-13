# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-08

### Added

- **ISLES24 Support**: Full support for ISLES 2024 stroke dataset (Zenodo 17652035)
  - `bids-hub isles24 build` - Build and upload ISLES24 to HuggingFace Hub
  - `bids-hub isles24 validate` - Validate ISLES24 downloads
  - `bids-hub isles24 info` - Show dataset information
  - Flattened schema (one row per subject with both Acute and Follow-up sessions)
- **List Command**: `bids-hub list` shows all supported datasets
- **Validation Framework**: Generic `ValidationResult` and `ValidationCheck` classes
- **Download Scripts**: `scripts/download_arc.sh` and `scripts/download_isles24.sh`

### Changed

- **Package Renamed**: `arc-bids` → `bids-hub` (multi-dataset support)
- **CLI Restructured**: Commands now use subcommand groups
  - `arc-bids build` → `bids-hub arc build`
  - `arc-bids validate` → `bids-hub arc validate`
- **Source Reorganized**: Modular structure with subpackages
  - `src/bids_hub/core/` - Generic BIDS→HF utilities
  - `src/bids_hub/datasets/` - Per-dataset modules (arc.py, isles24.py)
  - `src/bids_hub/validation/` - Per-dataset validation (arc.py, isles24.py, base.py)

### Fixed

- Arrow format scalar extraction in validation scripts (#17)
- Upstream `embed_table_storage` crash workaround documented in UPSTREAM_BUG.md

## [0.1.0] - 2025-11-XX

### Added

- Initial release with ARC dataset support
- `arc-bids build` - Build and upload ARC to HuggingFace Hub
- `arc-bids validate` - Validate ARC downloads against Scientific Data paper counts
- Memory-efficient sharded upload with pandas workaround for huggingface/datasets#7894
- Full ARC schema: T1w, T2w, FLAIR, BOLD (multi-run), DWI (multi-run), sbref, lesion masks
- Clinical metadata: age_at_stroke, sex, wab_aq, wab_type

[0.2.0]: https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/The-Obstacle-Is-The-Way/neuroimaging-go-brrrr/releases/tag/v0.1.0
