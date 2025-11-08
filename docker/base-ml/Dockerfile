# ML Base Image - SLIM VERSION (Phase 2 Optimization)
# This image inherits from base and adds common ML packages
# PyTorch is PROVIDED BY NATIVE ENVIRONMENT (.bollyenv) for optimal performance
# All GPU stages (asr, diarization, VAD, etc.) should inherit from this image
#
# PHASE 2 CHANGES:
# - Removed PyTorch installation (~2 GB saved per image)
# - PyTorch execution via native .bollyenv environment
# - 60% smaller images, 50% faster builds
# - Requires bootstrap to create .bollyenv with PyTorch

ARG REGISTRY=rajiup
ARG BASE_TAG=cuda
FROM ${REGISTRY}/cp-whisperx-app-base:${BASE_TAG}

LABEL description="ML base with common ML dependencies (PyTorch via native env)"
LABEL version="2.0-slim"
LABEL maintainer="DevOps Team"
LABEL phase="2-optimized"

USER root
WORKDIR /app

# ============================================================================
# PYTORCH REMOVED - NOW PROVIDED BY NATIVE ENVIRONMENT
# ============================================================================
# PyTorch is installed ONCE in .bollyenv via bootstrap.ps1
# Docker containers use native environment for PyTorch execution
# This approach:
#   - Reduces image size by ~2 GB per image
#   - Eliminates PyTorch version conflicts
#   - Enables faster builds (no PyTorch download/install)
#   - Allows GPU-specific optimization (CUDA 11.8/12.1/12.6)
#
# Requirements:
#   1. Run: ./scripts/bootstrap.ps1 (creates .bollyenv with PyTorch)
#   2. Mount: .bollyenv volume in docker-compose.yml
#   3. Set: EXECUTION_MODE=native environment variable
# ============================================================================

# Install common ML packages used across multiple stages
# BuildKit cache mount reuses downloads for transformers (~500MB)
RUN --mount=type=cache,id=pip-cache-base-ml,target=/root/.cache/pip \
    pip install \
    librosa==0.10.1 \
    transformers==4.57.1 \
    huggingface-hub==0.34.0 \
    sentencepiece==0.1.99

USER appuser
WORKDIR /app

# Note: PyTorch verification happens at runtime via stage scripts
# Stages check EXECUTION_MODE and verify native PyTorch availability
