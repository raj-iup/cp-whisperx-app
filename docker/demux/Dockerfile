ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="FFmpeg Demux - Extract audio from video"

USER root
WORKDIR /app

# No additional dependencies needed - ffmpeg from base

# Copy demux script (last - changes most frequently)
COPY docker/demux/demux.py /app/

USER appuser

ENTRYPOINT ["python", "demux.py"]
