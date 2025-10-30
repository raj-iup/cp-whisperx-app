FROM rajiup/cp-whisperx-app-base:latest

LABEL description="Silero VAD - Fast voice activity detection for rough speech cuts"

USER root
WORKDIR /app

# Install PyTorch for CPU and Silero VAD dependencies
RUN pip install --no-cache-dir \
    torch>=2.0.0 \
    torchaudio>=2.0.0 \
    numpy>=1.24.0 \
    soundfile>=0.12.1 \
    packaging>=21.0 \
    scipy>=1.10.0

# Copy Silero VAD script
COPY docker/silero-vad/silero_vad.py /app/

USER appuser

ENTRYPOINT ["python", "silero_vad.py"]
