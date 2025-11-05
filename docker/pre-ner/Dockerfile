ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="Pre-ASR NER - Extract named entities from TMDB for ASR prompt"

USER root
WORKDIR /app

# Install spaCy with pinned version
# Model download moved to runtime (shared cache volume)
# BuildKit cache mount speeds up spaCy downloads
RUN --mount=type=cache,id=pip-cache-pre-ner,target=/root/.cache/pip \
    pip install spacy==3.8.7

# Copy Pre-NER script (last - changes most frequently)
COPY docker/pre-ner/pre_ner.py /app/

USER appuser

ENTRYPOINT ["python", "pre_ner.py"]
