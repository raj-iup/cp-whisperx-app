# Subtitle Generation container - Create .srt files from corrected transcripts
FROM rajiup/cp-whisperx-app-base:latest

LABEL description="Subtitle Generation - Speaker-prefixed English SRT (workflow-arch.txt Stage 9)"

USER root

# Install subtitle handling dependencies
RUN pip install --no-cache-dir pysrt>=1.1.2

# Copy scripts and shared modules
COPY scripts/ /app/scripts/
COPY shared/ /app/shared/
COPY docker/subtitle-gen/subtitle_gen.py /app/

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "/app/subtitle_gen.py"]
