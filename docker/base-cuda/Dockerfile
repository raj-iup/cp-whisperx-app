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

# Install Python 3.11 and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    ffmpeg \
    git \
    wget \
    curl \
    ca-certificates \
    build-essential \
    libsndfile1 \
    libsndfile1-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set python3.11 as default python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Upgrade pip and install common Python packages
RUN python3 -m pip install --upgrade pip wheel setuptools && \
    pip install --no-cache-dir \
    python-dotenv>=1.0.0 \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    requests>=2.31.0 \
    tqdm>=4.66.0 \
    python-json-logger>=2.0.7

# Install PyTorch with CUDA support
RUN pip install --no-cache-dir \
    torch==2.1.0+cu121 \
    torchaudio==2.1.0+cu121 \
    --index-url https://download.pytorch.org/whl/cu121

# Install common ML packages
RUN pip install --no-cache-dir \
    numpy>=1.24.0 \
    scipy>=1.11.0 \
    scikit-learn>=1.3.0 \
    pandas>=2.0.0 \
    soundfile>=0.12.1

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
