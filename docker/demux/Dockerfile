FROM rajiup/cp-whisperx-app-base:latest

LABEL description="FFmpeg Demux - Extract audio from video"

USER root
WORKDIR /app

# Copy demux script
COPY docker/demux/demux.py /app/

USER appuser

ENTRYPOINT ["python", "demux.py"]
