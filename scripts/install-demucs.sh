#!/usr/bin/env bash
# Install Demucs environment for source separation
# Creates isolated venv to avoid PyTorch version conflicts

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="venv/demucs"

echo "🎵 Installing Demucs Environment for Source Separation"
echo "========================================================"
echo ""

# Check if virtual environment exists
if [ -d "$VENV_DIR" ]; then
    echo "⚠️  Virtual environment already exists: $VENV_DIR"
    read -p "Do you want to recreate it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🗑️  Removing existing environment..."
        rm -rf "$VENV_DIR"
    else
        echo "✅ Keeping existing environment"
        exit 0
    fi
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv "$VENV_DIR"

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install PyTorch with MPS support (for Apple Silicon)
echo "🔥 Installing PyTorch with MPS support..."
if [[ $(uname -m) == 'arm64' ]]; then
    echo "   Detected Apple Silicon - installing with MPS support"
    pip install torch torchaudio
else
    echo "   Installing standard PyTorch"
    pip install torch torchaudio
fi

# Install requirements
echo "📚 Installing Demucs and dependencies..."
pip install -r requirements-demucs.txt

# Verify installation
echo ""
echo "✅ Verifying installation..."
python3 << 'EOF'
import sys
import torch
import demucs

print(f"✓ Python: {sys.version.split()[0]}")
print(f"✓ PyTorch: {torch.__version__}")
print(f"✓ Demucs: {demucs.__version__}")
print(f"✓ MPS Available: {torch.backends.mps.is_available()}")
print(f"✓ MPS Built: {torch.backends.mps.is_built()}")

# Test demucs import
from demucs.pretrained import get_model
print(f"✓ Demucs models accessible")
EOF

echo ""
echo "========================================================"
echo "✅ Demucs environment installed successfully!"
echo ""
echo "To activate this environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To test source separation:"
echo "  ./test-source-separation.sh"
echo ""
