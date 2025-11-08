# Diarization container - Speaker labeling using PyAnnote
ARG REGISTRY=rajiup
ARG BASE_TAG=cuda
FROM ${REGISTRY}/cp-whisperx-app-base-ml:${BASE_TAG}

LABEL description="PyAnnote Diarization - Speaker labeling (MANDATORY per workflow-arch.txt)"

USER root

# FFmpeg and its libraries are already installed in base-ml:cuda
# PyTorch, numpy, transformers, librosa also available from base-ml:cuda
# Install PyAnnote and dependencies
RUN --mount=type=cache,id=pip-cache-diarization,target=/root/.cache/pip \
    pip install \
    av \
    pyannote.audio==3.4.0 \
    pyannote.core==5.0.0 \
    pyannote.pipeline==3.0.1 \
    pytorch-lightning==2.5.5 \
    torchmetrics==1.8.2

# Install speechbrain separately
RUN --mount=type=cache,id=pip-cache-diarization,target=/root/.cache/pip \
    pip install --no-build-isolation speechbrain==1.0.1

# Install whisperx for integration
RUN --mount=type=cache,id=pip-cache-diarization,target=/root/.cache/pip \
    pip install whisperx==3.7.2

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/
COPY scripts/ /app/scripts/

# Copy stage script (changes most frequently)
COPY docker/diarization/diarization.py /app/

USER appuser
WORKDIR /app

# HuggingFace cache now uses shared volume (set in docker-compose.yml)
# Models downloaded at runtime to /shared-model-and-cache

ENTRYPOINT ["python", "/app/diarization.py"]
