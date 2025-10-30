# Base image for all cp-whisperx-app pipeline containers
# Provides common dependencies and utilities

FROM python:3.11-slim

LABEL maintainer="rajiup"
LABEL description="Base image for cp-whisperx-app pipeline"

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    curl \
    ca-certificates \
    build-essential \
    libsndfile1 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
RUN pip install --no-cache-dir -U pip wheel && \
    pip install --no-cache-dir \
    python-dotenv>=1.0.0 \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    requests>=2.31.0 \
    tqdm>=4.66.0 \
    python-json-logger>=2.0.7

# Create directory structure
WORKDIR /app
RUN mkdir -p /app/in /app/out /app/logs /app/temp /app/config /app/shared

# Set Python path
ENV PYTHONPATH=/app:/app/shared

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser
WORKDIR /app
