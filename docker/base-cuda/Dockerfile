# CUDA Base Image for cp-whisperx-app pipeline
# Provides CUDA-enabled PyTorch and common ML dependencies
# For Linux/Windows GPU-accelerated execution

# nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 pinned by digest for reproducible builds
# Tag reference: nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04 (2025-11-05)
FROM nvidia/cuda@sha256:f3a7fb39fa3ffbe54da713dd2e93063885e5be2f4586a705c39031b8284d379a

LABEL maintainer="rajiup"
LABEL description="CUDA base image for cp-whisperx-app ML stages"
LABEL cuda.version="12.1.0"
LABEL cudnn.version="8"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CUDA_HOME=/usr/local/cuda \
    LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH \
    PATH=/usr/local/cuda/bin:$PATH

# Install Python 3.11 and system dependencies (minimal set)
# Removed: build-essential (stages can add if needed)
# BuildKit cache mount for apt speeds up rebuilds
RUN --mount=type=cache,id=apt-cache-base-cuda,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib-base-cuda,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3.11-distutils \
    ffmpeg \
    git \
    wget \
    ca-certificates \
    libsndfile1 \
    libsndfile1-dev \
    && apt-get purge -y python3.10* \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Manually install pip using get-pip.py (ensurepip not available in Ubuntu apt python3.11)
# BuildKit cache mount allows pip to cache downloads
RUN --mount=type=cache,id=pip-cache-base-cuda,target=/root/.cache/pip \
    wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    python3 -m pip install --upgrade pip wheel setuptools


# Install common dependencies from shared requirements
# BuildKit cache mount reuses downloads across builds
COPY docker/requirements-common.txt /tmp/
RUN --mount=type=cache,id=pip-cache-base-cuda,target=/root/.cache/pip \
    pip install -r /tmp/requirements-common.txt && \
    rm /tmp/requirements-common.txt

# Install base utilities
RUN --mount=type=cache,id=pip-cache-base-cuda,target=/root/.cache/pip \
    pip install \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    requests>=2.31.0 \
    python-json-logger>=2.0.7

# Note: PyTorch and ML packages are installed in base-ml:cuda
# This keeps the base:cuda image smaller for non-ML stages

# Create directory structure
WORKDIR /app
RUN mkdir -p /app/in /app/out /app/logs /app/temp /app/config /app/shared

# Set Python path
ENV PYTHONPATH=/app:/app/shared

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser
WORKDIR /app

CMD ["/bin/bash"]
