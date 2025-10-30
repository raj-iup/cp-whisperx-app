FROM rajiup/cp-whisperx-app-base:latest

LABEL description="FFmpeg Mux - Embed subtitles into video"

USER root
WORKDIR /app

# Copy mux script
COPY docker/mux/mux.py /app/

USER appuser

ENTRYPOINT ["python", "mux.py"]
