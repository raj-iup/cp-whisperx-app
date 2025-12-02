#!/usr/bin/env bash
set -euo pipefail
# Creates/updates venv and installs demucs and optionally torch for mps

VENV_DIR="${1:-venv/demucs}"
DEVICE="${2:-cpu}"  # 'mps' or 'cpu' recommended

echo "[bootstrap] Using venv path: ${VENV_DIR} device: ${DEVICE}"

python -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel

# Optional: install torch for mps if requested (best-effort; may require different index/wheels)
if [[ "${DEVICE}" == "mps" ]]; then
  echo "[bootstrap] Attempting to install torch (MPS) best-effort"
  # Note: On Apple Silicon, recommend using official wheels; CI should cache them to avoid timeouts
  # try install torch; if it fails, continue to install demucs and warn
  if ! "${VENV_DIR}/bin/python" -m pip install --upgrade torch; then
    echo "[bootstrap][warning] torch MPS install failed; continue with demucs only; you may need to install torch wheel manually for MPS"
  fi
fi

# Install demucs
echo "[bootstrap] Installing demucs into ${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade demucs

echo "[bootstrap] Demucs installed. Verify:"
"${VENV_DIR}/bin/python" -c "import demucs; print('Demucs version:', demucs.__version__)"
echo "[bootstrap] Bootstrap complete"
