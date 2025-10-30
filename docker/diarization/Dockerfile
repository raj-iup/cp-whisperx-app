# Diarization container - Speaker labeling using PyAnnote
FROM rajiup/cp-whisperx-app-base:latest

LABEL description="PyAnnote Diarization - Speaker labeling (MANDATORY per workflow-arch.txt)"

USER root

# Install additional system dependencies for PyAV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

# Install torch and torchaudio with specific compatible versions
# Using torch 2.0.1 + torchaudio 2.0.2 for compatibility with pyannote.audio 3.1
RUN pip install --no-cache-dir \
    torch==2.0.1 \
    torchaudio==2.0.2 \
    --index-url https://download.pytorch.org/whl/cpu

# Pre-install av and other dependencies
RUN pip install --no-cache-dir av "numpy>=1.24.0,<2.0.0"

# Install PyAnnote dependencies (excluding those already installed)
RUN pip install --no-cache-dir \
    "pyannote.audio==3.1.1" \
    "pytorch-lightning>=2.0.0"

# Install speechbrain separately (it has complex dependencies)
RUN pip install --no-cache-dir --no-build-isolation "speechbrain>=0.5.0"

# Install whisperx
RUN pip install --no-cache-dir whisperx

# Copy scripts and shared modules
COPY scripts/ /app/scripts/
COPY shared/ /app/shared/
COPY docker/diarization/diarization.py /app/

USER appuser
WORKDIR /app

# Set HuggingFace cache directory
ENV HF_HOME=/app/.cache/huggingface
ENV HF_DATASETS_CACHE=/app/.cache/huggingface/datasets
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers

ENTRYPOINT ["python", "/app/diarization.py"]
