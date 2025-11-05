# Base image for all cp-whisperx-app pipeline containers
# Provides common dependencies and utilities

# python:3.11-slim pinned by digest for reproducible builds
# Tag reference: python:3.11-slim (2025-11-05)
FROM python@sha256:fa9b525a0be0c5ae5e6f2209f4be6fdc5a15a36fed0222144d98ac0d08f876d4

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
# BuildKit cache mount for apt speeds up rebuilds
RUN --mount=type=cache,id=apt-cache-base-cpu,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib-base-cpu,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    ca-certificates \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
# BuildKit cache mount for pip dramatically speeds up rebuilds
RUN --mount=type=cache,id=pip-cache-base-cpu,target=/root/.cache/pip \
    pip install -U pip wheel

# Install common dependencies from shared requirements
# BuildKit cache mount allows pip to reuse downloads across builds
COPY docker/requirements-common.txt /tmp/
RUN --mount=type=cache,id=pip-cache-base-cpu,target=/root/.cache/pip \
    pip install -r /tmp/requirements-common.txt && \
    rm /tmp/requirements-common.txt

# Install base utilities
RUN --mount=type=cache,id=pip-cache-base-cpu,target=/root/.cache/pip \
    pip install \
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
