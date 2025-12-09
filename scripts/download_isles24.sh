#!/usr/bin/env bash
# scripts/download_isles24.sh
# Download ISLES24 from Zenodo
# Requires: curl, 7z (p7zip)
#
# Usage:
#   ./scripts/download_isles24.sh [target_dir]

set -euo pipefail

ZENODO_RECORD="17652035"
ZENODO_URL="https://zenodo.org/records/${ZENODO_RECORD}/files/train.7z"
TARGET_DIR="${1:-data/zenodo/isles24}"

echo "=== ISLES24 Download ==="
echo "Source: Zenodo record ${ZENODO_RECORD}"
echo "Target: ${TARGET_DIR}"
echo ""

mkdir -p "${TARGET_DIR}"

echo "Downloading train.7z (~99GB)..."
curl -L -C - -o "${TARGET_DIR}/train.7z" "${ZENODO_URL}"

echo "Extracting..."
7z x "${TARGET_DIR}/train.7z" -o"${TARGET_DIR}/" -y

echo ""
echo "=== Download Complete ==="
echo "Validate with:"
echo "  bids-hub isles24 validate ${TARGET_DIR}/train"
