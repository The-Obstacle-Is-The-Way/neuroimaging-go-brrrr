# Tutorial: Upload ARC Dataset

> **Time**: 30 minutes (excluding upload time)
> **Prerequisites**: Python 3.10+, uv, HuggingFace account

This tutorial walks you through uploading the **ARC (Aphasia Recovery Cohort)** dataset to HuggingFace Hub.

---

## Step 1: Download ARC

Download from OpenNeuro (ds004884) using the OpenNeuro CLI:

```bash
# Install OpenNeuro CLI if needed
npm install -g @openneuro/cli

# Download full dataset (~278GB)
openneuro download ds004884 data/openneuro/ds004884
```

---

## Step 2: Validate Download

Ensure data integrity before uploading:

```bash
uv run bids-hub arc validate data/openneuro/ds004884
```

Note: `bids-hub arc validate` currently performs useful corruption/structure checks, but some
ARC modality-count checks are known to be out-of-sync with the SSOT layout (e.g., lesion masks
live under `derivatives/`). If the integrity checks pass, proceed to the build step and use the
file-table checks in `docs/how-to/validate-before-upload.md` for upload readiness.

---

## Step 3: Build and Upload

Run the build command. Use `--dry-run` first to verify the file table construction.

```bash
# Dry run (safe, no upload)
uv run bids-hub arc build data/openneuro/ds004884 --dry-run

# Full upload (requires authentication)
huggingface-cli login
uv run bids-hub arc build data/openneuro/ds004884 --no-dry-run
```

---

## Step 4: Verify on HuggingFace

Go to your dataset page (e.g., `https://huggingface.co/datasets/hugging-science/arc-aphasia-bids`) and check the viewer. You should see NIfTI files rendered with NiiVue.
