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

# Install system dependencies (minimal set)
# Removed: build-essential (not needed in base, stages can add if needed)
# Removed: pkg-config (unused)
# Removed: curl (using wget only)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    ca-certificates \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
RUN pip install --no-cache-dir -U pip wheel

# Install common dependencies from shared requirements
COPY docker/requirements-common.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements-common.txt && \
    rm /tmp/requirements-common.txt

# Install base utilities
RUN pip install --no-cache-dir \
    pydantic>=2.0.0 \
    pydantic-settings>=2.0.0 \
    requests>=2.31.0 \
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
