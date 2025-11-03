FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for audio processing
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY docker/lyrics-detection/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared utilities
COPY shared/ /app/shared/

# Copy stage script
COPY docker/lyrics-detection/lyrics_detection.py /app/

# Set entrypoint
ENTRYPOINT ["python", "/app/lyrics_detection.py"]
