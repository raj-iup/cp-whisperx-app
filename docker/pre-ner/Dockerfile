FROM rajiup/cp-whisperx-app-base:latest

LABEL description="Pre-ASR NER - Extract named entities from TMDB for ASR prompt"

USER root
WORKDIR /app

# Install spaCy and download transformer model
RUN pip install --no-cache-dir spacy && \
    python -m spacy download en_core_web_sm

# Copy Pre-NER script
COPY docker/pre-ner/pre_ner.py /app/

USER appuser

ENTRYPOINT ["python", "pre_ner.py"]
