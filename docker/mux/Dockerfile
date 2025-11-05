ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="FFmpeg Mux - Embed subtitles into video"

USER root
WORKDIR /app

# No additional dependencies needed - ffmpeg from base

# Copy mux script (last - changes most frequently)
COPY docker/mux/mux.py /app/

USER appuser

ENTRYPOINT ["python", "mux.py"]
