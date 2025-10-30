FROM rajiup/cp-whisperx-app-base:latest

LABEL description="TMDB Metadata Fetch - Get movie data for ASR prompt"

USER root
WORKDIR /app

# Install TMDB dependencies
RUN pip install --no-cache-dir tmdbv3api

# Copy TMDB script
COPY docker/tmdb/tmdb.py /app/

USER appuser

ENTRYPOINT ["python", "tmdb.py"]
