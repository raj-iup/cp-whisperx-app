#!/usr/bin/env bash
# Build and push multi-arch images using docker buildx
# Usage:
#   DOCKERHUB_USER=youruser ./scripts/push_multiarch.sh [--skip-base]

set -eu
SELF_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT_DIR=$(cd "$SELF_DIR/.." && pwd)

DOCKERHUB_USER=${DOCKERHUB_USER:-}
if [ -z "$DOCKERHUB_USER" ]; then
  echo "Please set DOCKERHUB_USER environment variable to your Docker Hub username."
  echo "Example: DOCKERHUB_USER=rajiup $0"
  exit 1
fi

SKIP_BASE=false
for arg in "$@"; do
  case "$arg" in
    --skip-base) SKIP_BASE=true ;;
    *) echo "Unknown arg: $arg" ; exit 1 ;;
  esac
done

cd "$ROOT_DIR"

BASE_IMAGE="$DOCKERHUB_USER/cp-whisperx-app-base:latest"
ASR_IMAGE="$DOCKERHUB_USER/cp-whisperx-app-asr:latest"
NER_IMAGE="$DOCKERHUB_USER/cp-whisperx-app-ner:latest"

echo "Ensure you have a builder with QEMU enabled. If not, run:"
echo "  docker buildx create --use --name multiarch-builder --driver docker-container && docker run --rm --privileged multiarch/qemu-user-static --reset -p yes"

if [ "$SKIP_BASE" = false ]; then
  echo "Building + pushing multi-arch base: $BASE_IMAGE"
  docker buildx build --platform linux/amd64,linux/arm64 -f docker/base/Dockerfile -t "$BASE_IMAGE" --push .
else
  echo "--skip-base set; skipping base multi-arch build/push"
fi

echo "Building + pushing multi-arch ASR: $ASR_IMAGE"
docker buildx build --platform linux/amd64,linux/arm64 -f docker/asr/Dockerfile -t "$ASR_IMAGE" --push .

echo "Building + pushing multi-arch NER: $NER_IMAGE"
docker buildx build --platform linux/amd64,linux/arm64 -f docker/ner/Dockerfile -t "$NER_IMAGE" --push .

echo "Multi-arch build/push complete."
