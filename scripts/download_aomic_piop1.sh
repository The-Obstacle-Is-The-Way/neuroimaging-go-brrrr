#!/usr/bin/env bash
# =============================================================================
# Download AOMIC-PIOP1 from OpenNeuro
# Dataset: ds002785 (Amsterdam Open MRI Collection - PIOP1)
# License: CC0 (Public Domain)
# Subjects: 216 healthy adults
# =============================================================================
set -euo pipefail

DATASET_ID="ds002785"
TARGET_DIR="${1:-data/openneuro/ds002785}"

echo "=============================================="
echo "AOMIC-PIOP1 Dataset Download Script"
echo "Dataset: OpenNeuro $DATASET_ID"
echo "Target:  $TARGET_DIR"
echo "Subjects: 216 healthy adults"
echo "=============================================="

# Check if target directory already has data
if [ -d "$TARGET_DIR" ] && [ "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
    echo ""
    echo "WARNING: Target directory already contains files."
    echo "         Delete or rename it to re-download."
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Create target directory
mkdir -p "$TARGET_DIR"

# =============================================================================
# METHOD 1: AWS S3 (Recommended - No authentication required)
# =============================================================================
download_via_s3() {
    echo ""
    echo "Downloading via AWS S3 (no authentication required)..."
    echo "This downloads the latest snapshot."
    echo ""

    if ! command -v aws &> /dev/null; then
        echo "ERROR: AWS CLI not found."
        echo ""
        echo "Install with:"
        echo "  macOS:  brew install awscli"
        echo "  Linux:  pip install awscli"
        echo "  Or:     https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        echo ""
        return 1
    fi

    echo "Starting download (this may take a while for large datasets)..."
    echo "Command: aws s3 sync --no-sign-request s3://openneuro.org/$DATASET_ID $TARGET_DIR"
    echo ""

    aws s3 sync --no-sign-request "s3://openneuro.org/$DATASET_ID" "$TARGET_DIR"

    echo ""
    echo "Download complete!"
    return 0
}

# =============================================================================
# METHOD 2: OpenNeuro CLI (Deno-based, requires API key)
# =============================================================================
download_via_openneuro_cli() {
    echo ""
    echo "Downloading via OpenNeuro CLI..."
    echo ""

    if ! command -v openneuro &> /dev/null; then
        echo "ERROR: OpenNeuro CLI not found."
        echo ""
        echo "Install with Deno (npm version is deprecated):"
        echo "  1. Install Deno: curl -fsSL https://deno.land/install.sh | sh"
        echo "  2. Install CLI:  deno install -A --global jsr:@openneuro/cli -n openneuro"
        echo "  3. Login:        openneuro login  # requires API key from openneuro.org"
        echo ""
        return 1
    fi

    echo "Starting download..."
    echo "Command: openneuro download $DATASET_ID $TARGET_DIR"
    echo ""
    echo "NOTE: This creates a DataLad dataset. Large files are annexed."
    echo "      Use 'git-annex get <path>' or 'datalad get <path>' to download annexed files."
    echo ""

    openneuro download "$DATASET_ID" "$TARGET_DIR"

    echo ""
    echo "Download complete!"
    return 0
}

# =============================================================================
# METHOD 3: Subset download (for testing)
# =============================================================================
download_subset_s3() {
    echo ""
    echo "Downloading SUBSET via AWS S3 (for testing)..."
    echo "This downloads only root files + first 3 subjects."
    echo ""

    if ! command -v aws &> /dev/null; then
        echo "ERROR: AWS CLI not found."
        return 1
    fi

    # Download root-level files (participants.tsv, dataset_description.json, etc.)
    echo "Downloading root files..."
    aws s3 sync --no-sign-request \
        --exclude "*" \
        --include "*.tsv" \
        --include "*.json" \
        --include "*.txt" \
        --include "README*" \
        "s3://openneuro.org/$DATASET_ID" "$TARGET_DIR"

    # Download first 3 subjects
    echo "Downloading first 3 subjects..."
    for i in 1 2 3; do
        # List subjects and get the i-th one
        SUBJECT=$(aws s3 ls --no-sign-request "s3://openneuro.org/$DATASET_ID/" | grep "sub-" | head -n $i | tail -n 1 | awk '{print $2}' | tr -d '/')
        if [ -n "$SUBJECT" ]; then
            echo "  Downloading $SUBJECT..."
            aws s3 sync --no-sign-request \
                "s3://openneuro.org/$DATASET_ID/$SUBJECT" "$TARGET_DIR/$SUBJECT"
        fi
    done

    echo ""
    echo "Subset download complete!"
    return 0
}

# =============================================================================
# MAIN
# =============================================================================
echo ""
echo "Select download method:"
echo "  1) AWS S3 - Full dataset (recommended, no auth, ~216 subjects)"
echo "  2) AWS S3 - Subset only (for testing, ~3 subjects)"
echo "  3) OpenNeuro CLI (requires Deno + API key)"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1) download_via_s3 ;;
    2) download_subset_s3 ;;
    3) download_via_openneuro_cli ;;
    *) echo "Invalid choice. Exiting."; exit 1 ;;
esac

echo ""
echo "=============================================="
echo "Next steps:"
echo "  1. Validate the download:"
echo "     uv run bids-hub aomic piop1 validate $TARGET_DIR"
echo ""
echo "  2. Inspect the BIDS structure:"
echo "     ls -la $TARGET_DIR"
echo "     cat $TARGET_DIR/participants.tsv | head"
echo ""
echo "  3. Check dataset size:"
echo "     du -sh $TARGET_DIR"
echo ""
echo "  4. Build the HuggingFace dataset:"
echo "     uv run bids-hub aomic piop1 build $TARGET_DIR --dry-run"
echo ""
echo "  5. Get dataset info:"
echo "     uv run bids-hub aomic piop1 info"
echo "=============================================="
