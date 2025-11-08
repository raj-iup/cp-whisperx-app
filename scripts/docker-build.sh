#!/usr/bin/env bash
# CP-WhisperX-App Docker Build Script (Phase 2)
# Consolidated Docker image builder - builds only images needed for execution mode
#
# PHASE 2 FEATURES:
# - Mode-aware building (native, docker-cpu, docker-gpu)
# - Minimal image builds for native mode (default)
# - Full image builds for Docker-based execution
# - BuildKit cache optimization
# - Parallel builds where possible

set -euo pipefail

# Load common logging
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common-logging.sh"

# Default parameters
MODE="native"
REGISTRY="rajiup"
NO_PUSH=false
PARALLEL=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --mode|-m)
            MODE="$2"
            shift 2
            ;;
        --registry|-r)
            REGISTRY="$2"
            shift 2
            ;;
        --no-push)
            NO_PUSH=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--mode native|docker-cpu|docker-gpu] [--registry REGISTRY] [--no-push] [--parallel]"
            exit 1
            ;;
    esac
done

# Validate mode
if [[ ! "$MODE" =~ ^(native|docker-cpu|docker-gpu)$ ]]; then
    log_error "Invalid mode: $MODE"
    log_info "Valid modes: native, docker-cpu, docker-gpu"
    exit 1
fi

log_section "CP-WHISPERX-APP DOCKER BUILD (PHASE 2)"
log_info "Mode: $MODE"
log_info "Registry: $REGISTRY"
echo ""

# ============================================================================
# Enable Docker BuildKit for better performance
# ============================================================================
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

log_info "Docker BuildKit: ENABLED"
echo ""

# ============================================================================
# Build Strategy based on Mode
# ============================================================================

declare -a IMAGES=()

if [[ "$MODE" == "native" ]]; then
    log_section "NATIVE MODE BUILD"
    log_info "Building minimal Docker images for FFmpeg operations only..."
    log_info "ML execution will use native .bollyenv environment"
    echo ""
    
    # Native mode only needs:
    # 1. base (CPU-only, minimal)
    # 2. demux (FFmpeg audio extraction)
    # 3. mux (FFmpeg video/subtitle muxing)
    
    IMAGES=(
        "base:cpu:docker/base/Dockerfile:."
        "demux:cpu:docker/demux/Dockerfile:.:REGISTRY=$REGISTRY"
        "mux:cpu:docker/mux/Dockerfile:.:REGISTRY=$REGISTRY"
    )
    
    log_info "Images to build: 3 (base, demux, mux)"
    log_info "Estimated size: ~2 GB total"
    log_info "Estimated time: 2-5 minutes"
    echo ""
    
elif [[ "$MODE" == "docker-cpu" ]]; then
    log_section "DOCKER CPU MODE BUILD"
    log_info "Building all images with CPU-only support..."
    echo ""
    
    # CPU mode builds all stages but without CUDA
    IMAGES=(
        "base:cpu:docker/base/Dockerfile:."
        "base-ml:cpu:docker/base-ml/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cpu"
        "demux:cpu:docker/demux/Dockerfile:.:REGISTRY=$REGISTRY"
        "mux:cpu:docker/mux/Dockerfile:.:REGISTRY=$REGISTRY"
        "asr:cpu:docker/asr/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cpu"
        "diarization:cpu:docker/diarization/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cpu"
        "pyannote-vad:cpu:docker/pyannote-vad/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cpu"
        "subtitle-gen:cpu:docker/subtitle-gen/Dockerfile:.:REGISTRY=$REGISTRY"
        "tmdb:cpu:docker/tmdb/Dockerfile:.:REGISTRY=$REGISTRY"
        "pre-ner:cpu:docker/pre-ner/Dockerfile:.:REGISTRY=$REGISTRY"
        "post-ner:cpu:docker/post-ner/Dockerfile:.:REGISTRY=$REGISTRY"
    )
    
    log_info "Images to build: 11 (all stages, CPU-only)"
    log_info "Estimated size: ~15 GB total"
    log_info "Estimated time: 10-20 minutes"
    echo ""
    
elif [[ "$MODE" == "docker-gpu" ]]; then
    log_section "DOCKER GPU MODE BUILD"
    log_info "Building all images with CUDA GPU support..."
    echo ""
    
    # GPU mode builds all stages with CUDA support
    IMAGES=(
        "base:cpu:docker/base/Dockerfile:."
        "base:cuda:docker/base-cuda/Dockerfile:."
        "base-ml:cuda:docker/base-ml/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
        "demux:cuda:docker/demux/Dockerfile:.:REGISTRY=$REGISTRY"
        "mux:cuda:docker/mux/Dockerfile:.:REGISTRY=$REGISTRY"
        "asr:cuda:docker/asr/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
        "diarization:cuda:docker/diarization/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
        "pyannote-vad:cuda:docker/pyannote-vad/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
        "silero-vad:cuda:docker/silero-vad/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
        "lyrics-detection:cuda:docker/lyrics-detection/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
        "subtitle-gen:cuda:docker/subtitle-gen/Dockerfile:.:REGISTRY=$REGISTRY"
        "tmdb:cuda:docker/tmdb/Dockerfile:.:REGISTRY=$REGISTRY"
        "pre-ner:cuda:docker/pre-ner/Dockerfile:.:REGISTRY=$REGISTRY"
        "post-ner:cuda:docker/post-ner/Dockerfile:.:REGISTRY=$REGISTRY"
        "second-pass-translation:cuda:docker/second-pass-translation/Dockerfile:.:REGISTRY=$REGISTRY BASE_TAG=cuda"
    )
    
    log_info "Images to build: 15 (all stages, CUDA-enabled)"
    log_info "Estimated size: ~20 GB total (slim, no PyTorch in images)"
    log_info "Estimated time: 15-30 minutes"
    echo ""
fi

# ============================================================================
# Build Images
# ============================================================================
log_section "BUILDING IMAGES"
echo ""

declare -a BUILT_IMAGES=()
declare -a FAILED_IMAGES=()
START_TIME=$(date +%s)

for img_spec in "${IMAGES[@]}"; do
    IFS=: read -r name tag dockerfile context build_args <<< "$img_spec"
    
    IMAGE_NAME="$REGISTRY/cp-whisperx-app-$name:$tag"
    log_info "Building: $IMAGE_NAME"
    log_info "  Dockerfile: $dockerfile"
    
    # Build docker command
    docker_cmd="docker build -t $IMAGE_NAME -f $dockerfile"
    
    # Add build args if specified
    if [[ -n "${build_args:-}" ]]; then
        IFS=',' read -ra ARGS <<< "$build_args"
        for arg in "${ARGS[@]}"; do
            docker_cmd="$docker_cmd --build-arg $arg"
        done
    fi
    
    docker_cmd="$docker_cmd $context"
    
    echo "  Command: $docker_cmd" | log_color "gray"
    echo ""
    
    if eval "$docker_cmd"; then
        log_success "Built: $IMAGE_NAME"
        BUILT_IMAGES+=("$IMAGE_NAME")
    else
        log_error "Failed: $IMAGE_NAME"
        FAILED_IMAGES+=("$IMAGE_NAME")
    fi
    
    echo ""
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# ============================================================================
# Summary
# ============================================================================
log_section "BUILD SUMMARY"
log_info "Duration: $DURATION seconds"
log_info "Successfully built: ${#BUILT_IMAGES[@]} images"

if [[ ${#BUILT_IMAGES[@]} -gt 0 ]]; then
    echo ""
    echo "Built Images:" | log_color "green"
    for img in "${BUILT_IMAGES[@]}"; do
        echo "  ✓ $img" | log_color "green"
    done
fi

if [[ ${#FAILED_IMAGES[@]} -gt 0 ]]; then
    echo ""
    echo "Failed Images:" | log_color "red"
    for img in "${FAILED_IMAGES[@]}"; do
        echo "  ✗ $img" | log_color "red"
    done
    echo ""
    log_error "Some images failed to build"
    exit 1
fi

# ============================================================================
# Push Images (Optional)
# ============================================================================
if [[ "$NO_PUSH" == "false" ]]; then
    echo ""
    log_section "PUSHING IMAGES"
    log_info "Pushing built images to registry..."
    echo ""
    
    for img in "${BUILT_IMAGES[@]}"; do
        log_info "Pushing: $img"
        
        if docker push "$img"; then
            log_success "Pushed: $img"
        else
            log_warn "Could not push: $img"
        fi
        
        echo ""
    done
fi

# ============================================================================
# Final Summary
# ============================================================================
echo ""
log_section "DOCKER BUILD COMPLETE"

if [[ "$MODE" == "native" ]]; then
    log_info "Native mode images built successfully"
    log_info "ML execution will use native .bollyenv environment"
    log_info "Next steps:"
    log_info "  1. Run: ./prepare-job.sh <input_media>"
    log_info "  2. Run: ./run_pipeline.sh -j <job-id>"
elif [[ "$MODE" == "docker-cpu" ]]; then
    log_info "Docker CPU mode images built successfully"
    log_info "All stages will run in Docker containers (CPU-only)"
    log_info "Next steps:"
    log_info "  1. Run: ./prepare-job.sh <input_media>"
    log_info "  2. Run: ./run_pipeline.sh -j <job-id> -m docker-cpu"
elif [[ "$MODE" == "docker-gpu" ]]; then
    log_info "Docker GPU mode images built successfully"
    log_info "All stages will run in Docker containers (CUDA-enabled)"
    log_info "Next steps:"
    log_info "  1. Run: ./prepare-job.sh <input_media>"
    log_info "  2. Run: ./run_pipeline.sh -j <job-id> -m docker-gpu"
fi

echo ""
log_info "Total images: ${#BUILT_IMAGES[@]}"
log_info "Build time: $DURATION seconds"
echo ""

exit 0
