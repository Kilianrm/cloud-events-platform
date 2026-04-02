#!/bin/bash
set -e  # Stop on error

# ----------------------
# Configuration
# ----------------------
LAYER_NAME="pyjwt_layer"
LAYER_DIR="$(pwd)"
PYTHON_DIR="$LAYER_DIR/python"
ZIP_FILE="$LAYER_DIR/${LAYER_NAME}.zip"
REQ_FILE="$LAYER_DIR/requirements.txt"
TEMP_INSTALL="$LAYER_DIR/temp_install"
VENV_DIR="$LAYER_DIR/venv_layer"

echo "🚀 Building Lambda layer: $LAYER_NAME"
echo "Requirements: $REQ_FILE"
echo ""

# ----------------------
# Check if ZIP exists
# ----------------------
if [ -f "$ZIP_FILE" ]; then
    echo "🚀 ZIP already exists, skipping build: $ZIP_FILE"
    exit 0
fi

# ----------------------
# Clean previous builds
# ----------------------
echo "🧹 Cleaning previous build artifacts..."
rm -rf  "$ZIP_FILE" 

# ----------------------
# Create virtual environment
# ----------------------
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# ----------------------
# Install dependencies into temporary folder
# ----------------------
mkdir -p "$TEMP_INSTALL"
echo "📦 Installing dependencies from $REQ_FILE..."
pip install --upgrade pip
pip install -r "$REQ_FILE" -t "$TEMP_INSTALL"

# ----------------------
# Copy required packages to python/
# ----------------------
mkdir -p "$PYTHON_DIR"
echo "📂 Copying necessary packages to $PYTHON_DIR ..."

# Copy main PyJWT package
cp -r "$TEMP_INSTALL/jwt" "$PYTHON_DIR/"

# Optionally copy cryptography if using RSA/ECDSA algorithms
if [ -d "$TEMP_INSTALL/cryptography" ]; then
    cp -r "$TEMP_INSTALL/cryptography" "$PYTHON_DIR/"
fi

# ----------------------
# Generate ZIP
# ----------------------
echo "📦 Creating ZIP file..."
cd "$LAYER_DIR"
zip -r9 "$ZIP_FILE" python | tee /dev/stderr

# ----------------------
# Clean up
# ----------------------
echo "🧹 Cleaning temporary files..."
deactivate
rm -rf "$PYTHON_DIR" "$TEMP_INSTALL" "$VENV_DIR"

echo "🎉 Lambda layer created successfully: $ZIP_FILE"