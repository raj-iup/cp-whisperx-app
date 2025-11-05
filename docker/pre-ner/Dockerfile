ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu

LABEL description="Pre-ASR NER - Extract named entities from TMDB for ASR prompt"

USER root
WORKDIR /app

# Install spaCy with pinned version and download model
RUN pip install --no-cache-dir spacy==3.8.7 && \
    python -m spacy download en_core_web_sm

# Copy Pre-NER script (last - changes most frequently)
COPY docker/pre-ner/pre_ner.py /app/

USER appuser

ENTRYPOINT ["python", "pre_ner.py"]
