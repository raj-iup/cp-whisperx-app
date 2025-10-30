FROM rajiup/cp-whisperx-app-base:latest

LABEL description="PyAnnote VAD - Local voice activity detection with chunking"

USER root
WORKDIR /app

# Install torch and torchaudio versions compatible with pyannote.audio 3.4.0
# Using the same versions as whisperx uses in diarization container
RUN pip install --no-cache-dir \
    torch==2.8.0 \
    torchaudio==2.8.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Install compatible huggingface-hub version (< 1.0 supports use_auth_token)
RUN pip install --no-cache-dir "huggingface-hub>=0.20.0,<1.0"

# Install pyannote.audio 3.4.0 (same as diarization container)
RUN pip install --no-cache-dir \
    "pyannote.audio==3.4.0" \
    "soundfile>=0.12.1" \
    "pytorch-lightning>=2.0.0"

# Copy PyAnnote VAD script and shared modules
COPY docker/pyannote-vad/pyannote_vad.py /app/
COPY shared/ /app/shared/

USER appuser

# Set HuggingFace cache directory
ENV HF_HOME=/app/.cache/huggingface
ENV HF_DATASETS_CACHE=/app/.cache/huggingface/datasets
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers

ENTRYPOINT ["python", "pyannote_vad.py"]
