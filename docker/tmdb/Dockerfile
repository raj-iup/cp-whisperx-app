ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="TMDB Metadata Fetch - Get movie data for ASR prompt"

USER root
WORKDIR /app

# Install TMDB dependencies (from versions.txt: tmdbv3api==1.9.0)
# BuildKit cache mount speeds up rebuilds
RUN --mount=type=cache,id=pip-cache-tmdb,target=/root/.cache/pip \
    pip install tmdbv3api==1.9.0

# Copy TMDB script (last - changes most frequently)
COPY docker/tmdb/tmdb.py /app/

USER appuser

ENTRYPOINT ["python", "tmdb.py"]
