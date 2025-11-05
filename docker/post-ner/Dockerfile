# Post-ASR NER container - Entity correction & enrichment
ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="Post-ASR NER - Entity correction using TMDB metadata (workflow-arch.txt Stage 8)"

USER root

# Install spaCy and NER dependencies with pinned versions
# BuildKit cache mount speeds up large ML package downloads
RUN --mount=type=cache,id=pip-cache-post-ner,target=/root/.cache/pip \
    pip install \
    spacy==3.8.7 \
    transformers==4.57.1 \
    rapidfuzz==3.0.0

# spaCy transformer model download moved to runtime (shared cache volume)

# Copy shared modules (changes occasionally)
COPY shared/ /app/shared/
COPY scripts/ /app/scripts/

# Copy stage script (changes most frequently)
COPY docker/post-ner/post_ner.py /app/

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "/app/post_ner.py"]
