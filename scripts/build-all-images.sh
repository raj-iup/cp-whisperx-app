#!/bin/bash
# Build all Docker images for cp-whisperx-app pipeline
# Creates both CPU and CUDA variants for ML stages

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKERHUB_USER:-rajiup}"
REPO_NAME="cp-whisperx-app"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}CP-WhisperX-App Docker Image Builder${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Registry: ${GREEN}${REGISTRY}${NC}"
echo -e "Repository: ${GREEN}${REPO_NAME}${NC}"
echo ""

# Function to build image
build_image() {
    local stage=$1
    local variant=$2
    local dockerfile=$3
    local tag="${REGISTRY}/${REPO_NAME}-${stage}:${variant}"
    
    echo -e "${YELLOW}Building: ${tag}${NC}"
    
    if docker build -t "${tag}" -f "${dockerfile}" . ; then
        echo -e "${GREEN}✓ Built: ${tag}${NC}"
        return 0
    else
        echo -e "${RED}✗ Failed: ${tag}${NC}"
        return 1
    fi
}

# Track failures
FAILED_BUILDS=()

echo -e "${BLUE}=== Phase 1: Building Base Images ===${NC}"
echo ""

# Build CPU base
build_image "base" "cpu" "docker/base/Dockerfile" || FAILED_BUILDS+=("base:cpu")
echo ""

# Build CUDA base
build_image "base" "cuda" "docker/base-cuda/Dockerfile" || FAILED_BUILDS+=("base:cuda")
echo ""

echo -e "${BLUE}=== Phase 2: Building CPU-Only Stages ===${NC}"
echo ""

CPU_STAGES=(
    "demux"
    "tmdb"
    "pre-ner"
    "post-ner"
    "subtitle-gen"
    "mux"
)

for stage in "${CPU_STAGES[@]}"; do
    build_image "${stage}" "cpu" "docker/${stage}/Dockerfile" || FAILED_BUILDS+=("${stage}:cpu")
    echo ""
done

echo -e "${BLUE}=== Phase 3: Building GPU Stages (CPU variants) ===${NC}"
echo ""

GPU_STAGES=(
    "silero-vad"
    "pyannote-vad"
    "diarization"
    "asr"
    "second-pass-translation"
    "lyrics-detection"
)

for stage in "${GPU_STAGES[@]}"; do
    # Check if Dockerfile exists
    if [ -f "docker/${stage}/Dockerfile" ]; then
        build_image "${stage}" "cpu" "docker/${stage}/Dockerfile" || FAILED_BUILDS+=("${stage}:cpu")
        echo ""
    else
        echo -e "${YELLOW}⚠ Skipping ${stage} - Dockerfile not found${NC}"
        echo ""
    fi
done

echo -e "${BLUE}=== Phase 4: Building GPU Stages (CUDA variants) ===${NC}"
echo ""

# Note: CUDA variants would need separate Dockerfiles that use base-cuda
# For now, we'll tag the CPU versions and document the need for CUDA-specific builds
echo -e "${YELLOW}Note: CUDA variants require CUDA-specific Dockerfiles${NC}"
echo -e "${YELLOW}Current images work with --gpus all flag${NC}"
echo ""

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Build Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ${#FAILED_BUILDS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All images built successfully!${NC}"
    echo ""
    echo -e "Total images: $(docker images | grep "${REGISTRY}/${REPO_NAME}" | wc -l)"
else
    echo -e "${RED}✗ Failed builds:${NC}"
    for failed in "${FAILED_BUILDS[@]}"; do
        echo -e "${RED}  - ${failed}${NC}"
    done
    echo ""
    exit 1
fi

echo ""
echo -e "${GREEN}Next steps:${NC}"
echo -e "  1. Test images locally"
echo -e "  2. Run: ${BLUE}./scripts/push-all-images.sh${NC}"
echo ""
