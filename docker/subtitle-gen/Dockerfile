# Subtitle Generation container - Create .srt files from corrected transcripts
ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="Subtitle Generation - Speaker-prefixed English SRT (workflow-arch.txt Stage 9)"

USER root

# Install subtitle handling dependencies (pinned version)
# BuildKit cache mount speeds up rebuilds
RUN --mount=type=cache,id=pip-cache-subtitle-gen,target=/root/.cache/pip \
    pip install pysrt==1.1.2

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/
COPY scripts/ /app/scripts/

# Copy stage script (changes most frequently)
COPY docker/subtitle-gen/subtitle_gen.py /app/

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "/app/subtitle_gen.py"]
