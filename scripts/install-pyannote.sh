#!/bin/bash
# install-pyannote.sh - Setup PyAnnote VAD environment
set -e

echo "╔══════════════════════════════════════════════════════════════════════╗"
echo "║         PyAnnote VAD Environment Setup                              ║"
echo "╚══════════════════════════════════════════════════════════════════════╝"
echo

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "✗ Python 3 not found. Please install Python 3.11 or later."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"

# Set virtual environment path
VENV_DIR="venv/pyannote"

# Check if environment already exists
if [ -d "$VENV_DIR" ]; then
    echo
    read -p "PyAnnote environment already exists. Recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing environment."
        exit 0
    fi
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Creating PyAnnote virtual environment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 -m venv "$VENV_DIR"

echo "✓ Virtual environment created"
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Installing dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Activate environment and install packages
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install PyTorch first (for Apple Silicon)
echo
echo "Installing PyTorch..."
if [[ $(uname -m) == "arm64" ]]; then
    echo "Detected Apple Silicon - installing with MPS support"
    pip install torch torchvision torchaudio
else
    echo "Installing standard PyTorch"
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install PyAnnote and dependencies
echo
echo "Installing PyAnnote..."
pip install -r requirements-pyannote.txt

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Verifying installation..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test import
python3 << 'PYEOF'
import sys
print("Testing PyAnnote imports...")

try:
    import pyannote.audio
    print(f"  ✓ pyannote.audio {pyannote.audio.__version__}")
except Exception as e:
    print(f"  ✗ Failed to import pyannote.audio: {e}")
    sys.exit(1)

try:
    from pyannote.audio import Model
    print(f"  ✓ pyannote.audio.Model")
except Exception as e:
    print(f"  ✗ Failed to import Model: {e}")
    sys.exit(1)

try:
    import torch
    print(f"  ✓ torch {torch.__version__}")
    if torch.backends.mps.is_available():
        print(f"  ✓ MPS (Apple Silicon GPU) available")
    elif torch.cuda.is_available():
        print(f"  ✓ CUDA available")
    else:
        print(f"  ℹ CPU only")
except Exception as e:
    print(f"  ✗ Failed to import torch: {e}")
    sys.exit(1)

print("\n✓ All imports successful!")
PYEOF

if [ $? -eq 0 ]; then
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✓ PyAnnote VAD environment setup complete!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "Environment: $VENV_DIR"
    echo "Python: $VENV_DIR/bin/python"
    echo
    echo "Next steps:"
    echo "  1. Ensure HuggingFace token is configured"
    echo "  2. Run a test job to validate PyAnnote VAD"
    echo
else
    echo
    echo "✗ Installation failed. Please check errors above."
    exit 1
fi
