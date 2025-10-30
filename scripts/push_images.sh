#!/usr/bin/env bash
# Push base + service images to Docker Hub (single-arch)
# Usage:
#   DOCKERHUB_USER=youruser ./scripts/push_images.sh [--no-push] [--skip-base]
# Options:
#   --no-push    : build locally but don't push (useful for testing)
#   --skip-base  : skip building/pushing base image

set -eu
SELF_DIR=$(cd "$(dirname "$0")" && pwd)
ROOT_DIR=$(cd "$SELF_DIR/.." && pwd)

DOCKERHUB_USER=${DOCKERHUB_USER:-}
if [ -z "$DOCKERHUB_USER" ]; then
  echo "Please set DOCKERHUB_USER environment variable to your Docker Hub username."
  echo "Example: DOCKERHUB_USER=rajiup $0"
  exit 1
fi

NO_PUSH=false
SKIP_BASE=false
for arg in "$@"; do
  case "$arg" in
    --no-push) NO_PUSH=true ;;
    --skip-base) SKIP_BASE=true ;;
    *) echo "Unknown arg: $arg" ; exit 1 ;;
  esac
done

cd "$ROOT_DIR"

BASE_IMAGE="$DOCKERHUB_USER/cp-whisperx-app-base:latest"
ASR_IMAGE="$DOCKERHUB_USER/cp-whisperx-app-asr:latest"
NER_IMAGE="$DOCKERHUB_USER/cp-whisperx-app-ner:latest"

if [ "$SKIP_BASE" = false ]; then
  echo "Building base image: $BASE_IMAGE"
  docker build -f docker/base/Dockerfile -t "$BASE_IMAGE" .
  if [ "$NO_PUSH" = false ]; then
    echo "Pushing base image: $BASE_IMAGE"
    docker push "$BASE_IMAGE"
  else
    echo "--no-push set; skipping push of base image"
  fi
else
  echo "--skip-base set; skipping base build/push"
fi

echo "Building ASR image: $ASR_IMAGE"
docker build -f docker/asr/Dockerfile -t "$ASR_IMAGE" .
if [ "$NO_PUSH" = false ]; then
  echo "Pushing ASR image: $ASR_IMAGE"
  docker push "$ASR_IMAGE"
else
  echo "--no-push set; skipping push of ASR image"
fi

echo "Building NER image: $NER_IMAGE"
docker build -f docker/ner/Dockerfile -t "$NER_IMAGE" .
if [ "$NO_PUSH" = false ]; then
  echo "Pushing NER image: $NER_IMAGE"
  docker push "$NER_IMAGE"
else
  echo "--no-push set; skipping push of NER image"
fi

echo "All done."
