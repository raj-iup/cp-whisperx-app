#!/usr/bin/env bash
set -euo pipefail

# Bootstrap script for cp-whisperx-app
# - creates a Python venv at .bollyenv
# - ensures pip/wheel are up-to-date
# - writes a sensible requirements.txt if missing
# - installs Python dependencies
# - runs a quick MPS/CUDA availability check

VENV_DIR=".bollyenv"
REQ_FILE="requirements.txt"

echo "== cp-whisperx-app bootstrap =="

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN=python3
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN=python
else
  echo "ERROR: Python not found. Please install Python 3.11+." >&2
  exit 1
fi

echo "Using python: $(command -v $PYTHON_BIN)"

echo "Checking Python version (recommended: 3.11+)"
$PYTHON_BIN - <<'PY'
import sys
v = sys.version_info
print(f"Python {v.major}.{v.minor}.{v.micro}")
if v.major < 3 or (v.major == 3 and v.minor < 11):
    print("Warning: Python 3.11+ recommended for best compatibility.")
PY

if [ -d "$VENV_DIR" ]; then
  echo "Found existing virtualenv in $VENV_DIR"
else
  echo "Creating virtualenv in $VENV_DIR"
  $PYTHON_BIN -m venv "$VENV_DIR"
fi

echo "Activating virtualenv"
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Upgrading pip and wheel"
python -m pip install -U pip wheel

if [ ! -f "$REQ_FILE" ]; then
  echo "No $REQ_FILE found — writing recommended requirements.txt"
  cat > "$REQ_FILE" <<'EOF'
torch>=2.3,<3.0
torchaudio>=2.3,<3.0
openai-whisper>=20231117
faster-whisper>=1.0.0
whisperx>=3.1.0
whisper-ctranslate2>=0.4.0
ctranslate2>=4.2.0
pyannote.audio>=3.1.0
huggingface_hub>=0.23.0
librosa>=0.10.1
soundfile>=0.12.1
tmdbsimple>=2.9.1
rich>=13.7.0
python-dotenv>=1.0.0
pysubs2>=1.1.0
spacy>=3.7.0
transformers>=4.30.0
EOF
  echo "Wrote $REQ_FILE"
fi

echo "Installing Python packages from $REQ_FILE (this can take a while)"
python -m pip install -r "$REQ_FILE"

echo "Running quick torch/MPS/CUDA check"
python - <<'PY'
try:
    import torch, sys
    mps = getattr(torch.backends, 'mps', None) and torch.backends.mps.is_available()
    cuda = torch.cuda.is_available()
    print('Torch version:', torch.__version__)
    print('MPS available:', bool(mps))
    print('CUDA available:', bool(cuda))
except Exception as e:
    print('Could not import torch or check devices:', repr(e))
    sys.exit(0)
PY

echo "Bootstrap complete."
echo "Next steps:"
echo "  - Create ./config/.env and ./config/secrets.json (see README.md for format)."
echo "  - Run ./scripts/preflight.sh to validate system deps and tokens."
echo "  - Run the pipeline via: ./run_pipeline.py -h or ./scripts/run.sh (if provided)."

exit 0
