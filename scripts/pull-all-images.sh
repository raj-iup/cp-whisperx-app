#!/usr/bin/env bash
# Pull all Docker images from registry
# This script pulls base images, CPU stages, and CUDA stages

set -euo pipefail

REGISTRY="${DOCKER_REGISTRY:-rajiup}"
IMAGE_PREFIX="cp-whisperx-app"

echo "========================================"
echo "  Docker Image Pull Script"
echo "========================================"
echo ""
echo "Registry: $REGISTRY"
echo "Image Prefix: $IMAGE_PREFIX"
echo ""

ERROR_COUNT=0
SUCCESS_COUNT=0

# Function to pull image
pull_image() {
    local IMAGE_TAG="$1"
    local FULL_IMAGE="${REGISTRY}/${IMAGE_PREFIX}-${IMAGE_TAG}"
    
    echo ""
    echo "[PULLING] $FULL_IMAGE"
    
    if docker pull "$FULL_IMAGE"; then
        echo "[SUCCESS] $IMAGE_TAG"
        ((SUCCESS_COUNT++)) || true
    else
        echo "[FAILED] $IMAGE_TAG"
        ((ERROR_COUNT++)) || true
    fi
}

echo ""
echo "=== Phase 1: Pulling Base Images ==="
echo ""

pull_image "base:cpu"
pull_image "base:cuda"
pull_image "base-ml:cuda"

echo ""
echo "=== Phase 2: Pulling CPU-Only Stage Images ==="
echo ""

pull_image "demux:cpu"
pull_image "tmdb:cpu"
pull_image "pre-ner:cpu"
pull_image "post-ner:cpu"
pull_image "subtitle-gen:cpu"
pull_image "mux:cpu"

echo ""
echo "=== Phase 3: Pulling GPU Stage Images (CUDA variants) ==="
echo ""

pull_image "silero-vad:cuda"
pull_image "pyannote-vad:cuda"
pull_image "diarization:cuda"
pull_image "asr:cuda"
pull_image "second-pass-translation:cuda"
pull_image "lyrics-detection:cuda"

echo ""
echo "=== Phase 4: Pulling GPU Stage Images (CPU fallback variants) ==="
echo ""

pull_image "silero-vad:cpu"
pull_image "pyannote-vad:cpu"
pull_image "diarization:cpu"
pull_image "asr:cpu"
pull_image "second-pass-translation:cpu"
pull_image "lyrics-detection:cpu"

echo ""
echo "========================================"
echo "  Pull Summary"
echo "========================================"
echo ""
echo "Total images pulled successfully: $SUCCESS_COUNT"
echo "Total images failed: $ERROR_COUNT"
echo ""

if [ $ERROR_COUNT -gt 0 ]; then
    echo "[WARNING] Some images failed to pull. Check the output above."
    exit 1
else
    echo "[SUCCESS] All images pulled successfully!"
    exit 0
fi
