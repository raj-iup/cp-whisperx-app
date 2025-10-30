#!/usr/bin/env bash
set -euo pipefail

# Helper to build ASR and NER containers, download NER model, and start services.
# Usage: ./scripts/docker-run.sh [--platform linux/amd64] [--build-only]

PLATFORM=""
BUILD_ONLY=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    --build-only)
      BUILD_ONLY=true
      shift
      ;;
    *)
      echo "Unknown arg: $1" >&2
      exit 1
      ;;
  esac
done

COMPOSE_CMD=(docker compose)

if [ -n "$PLATFORM" ]; then
  echo "Building with platform: $PLATFORM"
  "${COMPOSE_CMD[@]}" build --pull --no-cache --parallel --platform "$PLATFORM"
else
  "${COMPOSE_CMD[@]}" build --pull --no-cache --parallel
fi

# Quick docker daemon health check before continuing
if ! docker info >/dev/null 2>&1; then
  cat <<'EOF'
Docker does not appear to be running or the daemon is unreachable.
On macOS start Docker Desktop and wait until the status says "Docker is running".
You can start it from the command line with:

  open --background -a Docker

Then run `docker info` to verify the daemon is healthy before re-running this script.
EOF
  exit 1
fi

if [ "$BUILD_ONLY" = true ]; then
  echo "Build completed (build-only)."
  exit 0
fi

echo "Starting ASR service (in background)..."
"${COMPOSE_CMD[@]}" up -d asr

echo "Waiting a few seconds for ASR to initialize..."
sleep 5

echo "Downloading spaCy model inside NER container (if needed)..."
"${COMPOSE_CMD[@]}" run --rm ner python -m spacy download en_core_web_trf || true

echo "Bringing up NER (depends_on: asr)..."
"${COMPOSE_CMD[@]}" up -d ner

echo "All done. Use 'docker compose logs -f asr' and 'docker compose logs -f ner' to follow logs."

exit 0
