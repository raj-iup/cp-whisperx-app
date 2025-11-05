# CUDA Base Image for cp-whisperx-app pipeline
# Provides CUDA-enabled PyTorch and common ML dependencies
# For Linux/Windows GPU-accelerated execution

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

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
RUN apt-get update && apt-get install -y --no-install-recommends \
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
RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools


# Install common dependencies from shared requirements
COPY docker/requirements-common.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-common.txt && \
    rm /tmp/requirements-common.txt

# Install base utilities
RUN pip install --no-cache-dir \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    requests>=2.31.0 \
    python-json-logger>=2.0.7

# Note: PyTorch and ML packages are installed in base-ml:cuda
# This keeps the base:cuda image smaller for non-ML stages

# Create directory structure
WORKDIR /app
RUN mkdir -p /app/in /app/out /app/logs /app/temp /app/config /app/shared /app/LLM

# Set Python path
ENV PYTHONPATH=/app:/app/shared

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser
WORKDIR /app

CMD ["/bin/bash"]
