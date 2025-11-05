ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base-ml:cuda

LABEL description="Lyrics Detection - Identify musical segments"

USER root
WORKDIR /app

# librosa, numpy, scipy, soundfile already in base-ml
# No additional dependencies needed

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/

# Copy stage script (changes most frequently)
COPY docker/lyrics-detection/lyrics_detection.py /app/

USER appuser

ENTRYPOINT ["python", "/app/lyrics_detection.py"]
