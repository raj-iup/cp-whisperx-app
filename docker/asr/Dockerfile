ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base-ml:cuda

LABEL description="WhisperX ASR - Automatic Speech Recognition with translation"

USER root
WORKDIR /app

# PyTorch, numpy, transformers, librosa already in base-ml
# Install WhisperX and ASR-specific dependencies
RUN --mount=type=cache,id=pip-cache-asr,target=/root/.cache/pip \
    pip install \
    whisperx==3.7.2 \
    faster-whisper==1.2.0 \
    ctranslate2==4.6.0

# Install translation models
RUN --mount=type=cache,id=pip-cache-asr,target=/root/.cache/pip \
    pip install sacremoses

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/
COPY scripts/ /app/scripts/

# Copy stage script (changes most frequently)
COPY docker/asr/whisperx_asr.py /app/

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "/app/whisperx_asr.py"]
