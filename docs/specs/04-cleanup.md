# Phase 4: Delete Obsolete + Copy Scripts

**Complexity**: Trivial (delete + copy)

---

## 4.1 Delete Obsolete Files

### Empty Skeleton Package

```bash
rm -rf src/neuroimaging_go_brrrr/
```

**Why**: Empty `__init__.py`. The real package is now `src/bids_hub/`.

### Broken Toy Script

```bash
rm scripts/push_to_hub_ds004884_full.py
```

**Why**: 42-line script that:
- Uses wrong API (`load_dataset("bids", ...)` doesn't exist)
- Has no validation
- Has no error handling
- Replaced by `bids-hub arc build`

### One-liner Download Script

```bash
rm scripts/download_ds004884.sh
```

**Why**: Single `aws s3 sync` command. Replaced by robust `download_arc.sh`.

---

## 4.2 Copy Robust Download Scripts

### ARC Download Script

```bash
cp _reference_repos/bids-hub/scripts/download_arc.sh scripts/
chmod +x scripts/download_arc.sh
```

**Why**: Complete 6KB script with:
- Usage documentation
- Proper AWS CLI handling
- Progress output
- Error handling

### ISLES24 Download Script

```bash
cp _reference_repos/bids-hub/scripts/download_isles24.sh scripts/
chmod +x scripts/download_isles24.sh
```

**Why**: Zenodo download script for ISLES24 dataset.

---

## Files to KEEP (No Changes)

### Visualization Notebooks

```
scripts/visualization/
├── ArcAphasiaBids.ipynb
├── ArcAphasiaBidsLoadData.ipynb
└── data/.gitkeep
```

**Why**: Tobias's consumption pipeline demos. Different purpose than production pipeline.

---

## Complete Phase 4 Commands

```bash
# 4.1 Delete obsolete files
rm -rf src/neuroimaging_go_brrrr/
rm scripts/push_to_hub_ds004884_full.py
rm scripts/download_ds004884.sh

# 4.2 Copy robust download scripts
cp _reference_repos/bids-hub/scripts/download_arc.sh scripts/
cp _reference_repos/bids-hub/scripts/download_isles24.sh scripts/
chmod +x scripts/download_*.sh
```

---

## Verification

```bash
# src/ should only have bids_hub
ls src/
# Expected: bids_hub

# scripts/ should have visualization/ + download scripts
ls scripts/
# Expected: download_arc.sh  download_isles24.sh  visualization

# Download scripts should be executable
./scripts/download_arc.sh --help 2>&1 | head -5
# Expected: Usage information

# Verify download_isles24.sh exists and is executable
test -x scripts/download_isles24.sh && echo "OK" || echo "NOT EXECUTABLE"
```
