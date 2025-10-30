#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.bollyenv"
SECRETS_PATH="$ROOT_DIR/config/secrets.json"
ENV_PATH="$ROOT_DIR/config/.env"

echo "== cp-whisperx-app preflight =="
echo "Root: $ROOT_DIR"

echo "-- checking system binaries --"
for bin in ffmpeg mkvmerge curl python3; do
  if command -v "$bin" >/dev/null 2>&1; then
    printf "%-10s: %s\n" "$bin" "$(command -v $bin)"
  else
    printf "%-10s: MISSING\n" "$bin"
  fi
done

echo "\n-- virtualenv --"
if [ -d "$VENV_DIR" ]; then
  echo "Found venv: $VENV_DIR"
  # shellcheck source=/dev/null
  source "$VENV_DIR/bin/activate"
else
  echo "No virtualenv found at $VENV_DIR — run scripts/bootstrap.sh first"
fi

echo "\n-- python packages (quick import checks) --"
PY_IMPORTS=(whisperx transformers spacy pysubs2 dotenv tmdbsimple huggingface_hub)
# We skip attempting a host import of pyannote.audio because diarization is containerized by default.
# Instead we perform an in-container import test later. This avoids flagging macOS/arm wheel ABI
# incompatibilities as host errors.
for pkg in "${PY_IMPORTS[@]}"; do
  python - <<PY
import importlib, sys
pkg = "$pkg"
try:
  importlib.import_module(pkg)
  print(f"OK: {pkg}")
except Exception as e:
  msg = repr(e)
  print(f"MISSING or ERROR: {pkg} -> {msg}")
PY
done

echo
echo 'Note: `pyannote.audio` is intentionally NOT import-checked on the host.'
echo 'It is tested inside the `diarization` container below; use containerized diarization on macOS (recommended).'

echo "\n-- config files --"
if [ -f "$ENV_PATH" ]; then
  echo "Found .env at $ENV_PATH"
else
  echo "Missing: $ENV_PATH"
fi
if [ -f "$SECRETS_PATH" ]; then
  echo "Found secrets.json at $SECRETS_PATH"
else
  echo "Missing: $SECRETS_PATH"
fi

echo "\n-- token probes (if present) --"
HF_TOKEN=""
TMDB_KEY=""
PYANNOTE_TOKEN=""
if [ -f "$SECRETS_PATH" ]; then
  HF_TOKEN=$(python - <<PY
import json,sys
try:
    j=json.load(open('$SECRETS_PATH'))
    print(j.get('hf_token',''))
except Exception:
    print('')
PY
)
  TMDB_KEY=$(python - <<PY
import json,sys
try:
    j=json.load(open('$SECRETS_PATH'))
    print(j.get('tmdb_api_key',''))
except Exception:
    print('')
PY
)
  PYANNOTE_TOKEN=$(python - <<PY
import json,sys
try:
    j=json.load(open('$SECRETS_PATH'))
    print(j.get('pyannote_token',''))
except Exception:
    print('')
PY
)
fi

if [ -n "$HF_TOKEN" ]; then
  echo "Probing Hugging Face whoami-v2..."
  resp=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HF_TOKEN" https://huggingface.co/api/whoami-v2 || echo "000")
  echo "HF whoami response code: $resp"
else
  echo "HF token: missing"
fi

if [ -n "$TMDB_KEY" ]; then
  echo "Probing TMDB search (sample query 'Deewar')..."
  resp=$(curl -s -o /dev/null -w "%{http_code}" "https://api.themoviedb.org/3/search/movie?api_key=$TMDB_KEY&query=Deewar" || echo "000")
  echo "TMDB response code: $resp"
else
  echo "TMDB key: missing"
fi

if [ -n "$PYANNOTE_TOKEN" ]; then
  echo "Probing pyannote token with whoami-v2..."
  resp=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $PYANNOTE_TOKEN" https://huggingface.co/api/whoami-v2 || echo "000")
  echo "pyannote whoami response code: $resp"
else
  echo "pyannote token: missing"
fi

echo "\n-- docker / container quick tests --"
if command -v docker >/dev/null 2>&1; then
  echo "docker: $(docker --version)"
  if docker compose version >/dev/null 2>&1; then
    echo "docker compose: OK"
    # Run quick python check inside ASR service to ensure container python works and volumes mount
    set +e
    echo "Running quick python check in 'asr' service..."
    docker compose run --rm -T asr python -c 'print("ASR container python OK")'
    rc_asr=$?
    if [ $rc_asr -eq 0 ]; then
      echo "ASR container python: OK"
    else
      echo "ASR container python: FAILED (exit code $rc_asr)"
    fi

    # Run pyannote.audio import test inside the diarization service (pyannote moved to diarization image)
    echo "Running pyannote.audio import test in 'diarization' service..."
    docker compose run --rm -T diarization python - <<'PY'
import sys
try:
    import pyannote.audio as pa
    print('pyannote OK', getattr(pa, '__version__', 'unknown'))
    sys.exit(0)
except Exception as e:
    print('pyannote ERROR:', e)
    sys.exit(2)
PY
    rc_pyannote=$?
    if [ $rc_pyannote -eq 0 ]; then
      echo "pyannote.audio (in container): OK"
    else
      echo "pyannote.audio (in container): FAILED (exit code $rc_pyannote)"
      echo "Hint: If this fails, confirm the diarization image has correct pyannote/torchaudio wheels or run diarization inside the provided container environment."
    fi
    set -e
  else
    echo "docker compose: NOT FOUND"
  fi
else
  echo "docker: MISSING"
fi

echo "\n-- quick torch device check --"
python - <<PY
import sys
try:
    import torch
    mps = getattr(torch.backends,'mps',None) and torch.backends.mps.is_available()
    cuda = torch.cuda.is_available()
    print('Torch:', torch.__version__)
    print('MPS available:', bool(mps))
    print('CUDA available:', bool(cuda))
except Exception as e:
    print('Torch not available or error:', repr(e))
PY

echo "\nPreflight finished. Review any MISSING/ERROR lines above and fix before running the full pipeline."

exit 0
