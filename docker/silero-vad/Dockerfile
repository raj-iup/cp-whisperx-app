ARG REGISTRY=rajiup
ARG BASE_TAG=cuda
FROM ${REGISTRY}/cp-whisperx-app-base-ml:${BASE_TAG}

LABEL description="Silero VAD - Fast voice activity detection for rough speech cuts"

USER root
WORKDIR /app

# PyTorch, numpy, soundfile, scipy, librosa already in base-ml
# No additional dependencies needed for Silero VAD

# Copy Silero VAD script (last - changes most frequently)
COPY docker/silero-vad/silero_vad.py /app/

USER appuser

ENTRYPOINT ["python", "silero_vad.py"]
