# ML Base Image - Shared PyTorch and ML dependencies for all GPU stages
# This image inherits from base-cuda and adds PyTorch + common ML packages
# All GPU stages (asr, diarization, VAD, etc.) should inherit from this image

ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cuda

LABEL description="ML base with PyTorch and common ML dependencies"
LABEL version="1.0"
LABEL maintainer="DevOps Team"

USER root
WORKDIR /app

# Install PyTorch ONCE with CUDA 12.1 support
# Using torch 2.1.0 for broad compatibility with pyannote, whisperx, etc.
RUN pip install --no-cache-dir \
    torch==2.1.0 \
    torchaudio==2.1.0 \
    --index-url https://download.pytorch.org/whl/cu121

# Install common ML packages used across multiple stages
RUN pip install --no-cache-dir \
    librosa==0.10.1 \
    transformers==4.57.1 \
    huggingface-hub==0.34.0 \
    sentencepiece==0.1.99

USER appuser
WORKDIR /app

# Verify PyTorch installation (CUDA check will fail during build without GPU)
RUN python -c "import torch; print(f'PyTorch {torch.__version__} installed')" && \
    echo "INFO: PyTorch CUDA check will occur at runtime when GPU is available"
