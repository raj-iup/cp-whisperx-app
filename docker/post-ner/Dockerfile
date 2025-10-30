# Post-ASR NER container - Entity correction & enrichment
FROM rajiup/cp-whisperx-app-base:latest

LABEL description="Post-ASR NER - Entity correction using TMDB metadata (workflow-arch.txt Stage 8)"

USER root

# Install spaCy and NER dependencies
RUN pip install --no-cache-dir \
    spacy>=3.5.0 \
    transformers>=4.30.0 \
    rapidfuzz>=3.0.0

# Download spaCy transformer model
RUN python -m spacy download en_core_web_trf

# Copy scripts and shared modules
COPY scripts/ /app/scripts/
COPY shared/ /app/shared/
COPY docker/post-ner/post_ner.py /app/

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "/app/post_ner.py"]
