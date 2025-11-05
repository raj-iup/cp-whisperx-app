#!/bin/bash
# Build all Docker images for cp-whisperx-app pipeline
# New Tagging Strategy:
# - CPU-Only Stages: :cpu tag (built from base:cpu)
# - GPU Stages: :cuda tag (built from base:cuda)

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
echo -e "Tagging Strategy:"
echo -e "  CPU-Only Stages: :cpu (from base:cpu)"
echo -e "  GPU Stages: :cuda (from base:cuda)"
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
echo -e "${YELLOW}[INFO] Building base images in dependency order:${NC}"
echo -e "${YELLOW}[INFO]   1. base:cpu - CPU-only base${NC}"
echo -e "${YELLOW}[INFO]   2. base:cuda - CUDA base with Python 3.11${NC}"
echo -e "${YELLOW}[INFO]   3. base-ml:cuda - ML base with PyTorch (inherits from base:cuda)${NC}"
echo -e "${YELLOW}[INFO] All other images will reference these base images${NC}"
echo ""

# Build CPU base
echo -e "${YELLOW}Building base:cpu (required by all CPU-only and fallback stages)${NC}"
if ! build_image "base" "cpu" "docker/base/Dockerfile"; then
    FAILED_BUILDS+=("base:cpu")
    echo -e "${RED}[ERROR] base:cpu build failed!${NC}"
    echo -e "${RED}[ERROR] Cannot proceed - all CPU stages require base:cpu${NC}"
    echo -e "${RED}[ERROR] Required by: demux, tmdb, pre-ner, post-ner, subtitle-gen, mux${NC}"
    echo -e "${RED}[ERROR] Also required for GPU stage CPU fallbacks${NC}"
    exit 1
fi
echo ""

# Build CUDA base
echo -e "${YELLOW}Building base:cuda (required by base-ml and all GPU CUDA stages)${NC}"
if ! build_image "base" "cuda" "docker/base-cuda/Dockerfile"; then
    FAILED_BUILDS+=("base:cuda")
    echo -e "${RED}[ERROR] base:cuda build failed!${NC}"
    echo -e "${RED}[ERROR] Cannot proceed - base-ml:cuda requires base:cuda${NC}"
    echo -e "${RED}[ERROR] Required by: base-ml, and all GPU CUDA stages${NC}"
    exit 1
fi
echo ""

# Build ML base (depends on base:cuda)
echo -e "${YELLOW}Building base-ml:cuda (ML base with PyTorch - required by all GPU stages)${NC}"
echo -e "${YELLOW}[INFO] This image includes PyTorch 2.1.0 + common ML packages${NC}"
echo -e "${YELLOW}[INFO] Saves 10-15 GB by installing PyTorch once instead of per-stage${NC}"
if ! build_image "base-ml" "cuda" "docker/base-ml/Dockerfile"; then
    FAILED_BUILDS+=("base-ml:cuda")
    echo -e "${RED}[ERROR] base-ml:cuda build failed!${NC}"
    echo -e "${RED}[ERROR] Cannot proceed - all GPU stages require base-ml:cuda${NC}"
    echo -e "${RED}[ERROR] Required by: silero-vad, pyannote-vad, diarization, asr, etc.${NC}"
    exit 1
fi
echo ""

echo -e "${GREEN}[SUCCESS] All base images built successfully!${NC}"
echo -e "${YELLOW}[INFO] Subsequent GPU stage builds will inherit PyTorch from base-ml${NC}"
echo ""

echo -e "${BLUE}=== Phase 2: Building CPU-Only Stages ===${NC}"
echo -e "(demux, tmdb, pre-ner, post-ner, subtitle-gen, mux)"
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

echo -e "${BLUE}=== Phase 3: Building GPU Stages (CUDA variants) ===${NC}"
echo -e "(silero-vad, pyannote-vad, diarization, asr, and optional stages)"
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
        build_image "${stage}" "cuda" "docker/${stage}/Dockerfile" || FAILED_BUILDS+=("${stage}:cuda")
        echo ""
    else
        echo -e "${YELLOW}⚠ Skipping ${stage} - Dockerfile not found${NC}"
        echo ""
    fi
done

echo -e "${BLUE}=== Phase 4: Building GPU Stages (CPU fallback variants) ===${NC}"
echo -e "(Same stages with CPU-only PyTorch for fallback)"
echo ""

for stage in "${GPU_STAGES[@]}"; do
    if [ -f "docker/${stage}/Dockerfile.cpu" ]; then
        build_image "${stage}" "cpu" "docker/${stage}/Dockerfile.cpu" || FAILED_BUILDS+=("${stage}:cpu")
        echo ""
    elif [ -f "docker/${stage}/Dockerfile" ]; then
        echo -e "${YELLOW}Building CPU fallback for ${stage}${NC}"
        # Build CPU variant by modifying Dockerfile on-the-fly
        # Replace base-ml:cuda with base:cpu and remove CUDA-specific installs
        sed -e 's/FROM rajiup\/cp-whisperx-app-base-ml:cuda/FROM rajiup\/cp-whisperx-app-base:cpu/' \
            -e 's/FROM rajiup\/cp-whisperx-app-base:cuda/FROM rajiup\/cp-whisperx-app-base:cpu/' \
            -e 's/--index-url https:\/\/download.pytorch.org\/whl\/cu121/--index-url https:\/\/download.pytorch.org\/whl\/cpu/' \
            "docker/${stage}/Dockerfile" | \
            docker build -t "${REGISTRY}/${REPO_NAME}-${stage}:cpu" -f - .
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Built: ${REGISTRY}/${REPO_NAME}-${stage}:cpu (fallback)${NC}"
        else
            echo -e "${RED}✗ Failed: ${REGISTRY}/${REPO_NAME}-${stage}:cpu${NC}"
            FAILED_BUILDS+=("${stage}:cpu")
        fi
        echo ""
    else
        echo -e "${YELLOW}⚠ Skipping ${stage}:cpu - Dockerfile not found${NC}"
        echo ""
    fi
done

# Summary
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Build Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ${#FAILED_BUILDS[@]} -eq 0 ]; then
    echo -e "${GREEN}✓ All images built successfully!${NC}"
    echo ""
    echo -e "Image Summary:"
    echo -e "  Base images: base:cpu, base:cuda, base-ml:cuda"
    echo -e "  CPU-only stages (6): demux, tmdb, pre-ner, post-ner, subtitle-gen, mux"
    echo -e "  GPU stages with fallback (4-6):"
    echo -e "    - silero-vad:cuda + silero-vad:cpu"
    echo -e "    - pyannote-vad:cuda + pyannote-vad:cpu"
    echo -e "    - diarization:cuda + diarization:cpu"
    echo -e "    - asr:cuda + asr:cpu"
    echo -e "    - [optional] second-pass-translation:cuda + :cpu"
    echo -e "    - [optional] lyrics-detection:cuda + :cpu"
    echo ""
    echo -e "${GREEN}Optimization Results:${NC}"
    echo -e "  ✓ PyTorch installed ONCE in base-ml:cuda"
    echo -e "  ✓ All GPU stages inherit from base-ml (saves 10-15 GB)"
    echo -e "  ✓ Common dependencies shared via requirements-common.txt"
    echo -e "  ✓ All versions pinned for reproducibility"
    echo ""
    echo -e "Total images: $(docker images | grep "${REGISTRY}/${REPO_NAME}" | wc -l)"
    echo ""
    echo -e "${GREEN}Next steps:${NC}"
    echo -e "  1. Test GPU images: docker compose run --rm --gpus all asr"
    echo -e "  2. Test CPU fallback: docker compose run --rm asr"
    echo -e "  3. Push to registry: ${BLUE}./scripts/push-all-images.sh${NC}"
else
    echo -e "${RED}✗ Failed builds:${NC}"
    for failed in "${FAILED_BUILDS[@]}"; do
        echo -e "${RED}  - ${failed}${NC}"
    done
    echo ""
    exit 1
fi

echo ""
