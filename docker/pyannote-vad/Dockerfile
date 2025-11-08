ARG REGISTRY=rajiup
ARG BASE_TAG=cuda
FROM ${REGISTRY}/cp-whisperx-app-base-ml:${BASE_TAG}

LABEL description="PyAnnote VAD - Local voice activity detection with chunking"

USER root
WORKDIR /app

# PyTorch, numpy, soundfile, transformers, huggingface-hub already in base-ml
# Install pyannote.audio and dependencies
RUN --mount=type=cache,id=pip-cache-pyannote-vad,target=/root/.cache/pip \
    pip install \
    pyannote.audio==3.4.0 \
    pyannote.core==5.0.0 \
    pytorch-lightning==2.5.5

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/

# Copy stage script (changes most frequently)
COPY docker/pyannote-vad/pyannote_vad.py /app/

USER appuser

# HuggingFace cache now uses shared volume (set in docker-compose.yml)
# Models downloaded at runtime to /shared-model-and-cache

ENTRYPOINT ["python", "pyannote_vad.py"]
