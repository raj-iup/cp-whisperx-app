FROM rajiup/cp-whisperx-app-base:latest

LABEL description="WhisperX ASR - Automatic Speech Recognition with translation"

USER root
WORKDIR /app

# Install compatible torch versions (2.2.1 for pyannote compatibility)
RUN pip install --no-cache-dir \
    "numpy>=1.24.0,<2.0.0" \
    torch==2.2.1 \
    torchaudio==2.2.1 \
    --index-url https://download.pytorch.org/whl/cpu

# Install WhisperX and dependencies
RUN pip install --no-cache-dir \
    git+https://github.com/m-bain/whisperX.git \
    faster-whisper \
    transformers \
    ctranslate2 \
    soundfile>=0.12.1 \
    scipy>=1.10.0 \
    tqdm

# Install translation models
RUN pip install --no-cache-dir \
    sentencepiece \
    sacremoses

# Copy scripts and shared modules
COPY scripts/ /app/scripts/
COPY shared/ /app/shared/
COPY docker/asr/whisperx_asr.py /app/

USER appuser
WORKDIR /app

ENTRYPOINT ["python", "/app/whisperx_asr.py"]
