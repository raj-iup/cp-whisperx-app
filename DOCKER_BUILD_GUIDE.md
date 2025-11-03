# Docker Build and Registry Guide

## Overview

This guide covers building, tagging, and pushing all Docker images to the registry.

**Time Estimate:** 2-4 hours total
- Building images: 30-90 minutes
- Pushing to registry: 30-120 minutes (depending on upload speed)

## Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Hub account** 
3. **Logged in** to Docker Hub: `docker login`
4. **Disk space**: ~20GB free
5. **Internet**: Good bandwidth for pushing images

## Quick Start

```bash
# 1. Build all images
./scripts/build-all-images.sh

# 2. Test locally (optional)
docker-compose up demux

# 3. Push to registry
./scripts/push-all-images.sh
```

## Image Architecture

### Base Images
- **base:cpu** - Python 3.11 + CPU libraries
- **base:cuda** - Python 3.11 + CUDA 12.1 + PyTorch

### Stage Images  

**CPU-Only Stages:**
- demux:latest
- tmdb:latest
- pre-ner:latest
- post-ner:latest
- subtitle-gen:latest
- mux:latest

**GPU Stages** (support both CPU and CUDA):
- silero-vad:latest
- pyannote-vad:latest
- diarization:latest
- asr:latest
- second-pass-translation:latest
- lyrics-detection:latest

## Manual Build Commands

If you prefer manual control:

```bash
# Set registry
export DOCKERHUB_USER="rajiup"

# Build base images
docker build -t $DOCKERHUB_USER/cp-whisperx-app-base:cpu -f docker/base/Dockerfile .
docker build -t $DOCKERHUB_USER/cp-whisperx-app-base:cuda -f docker/base-cuda/Dockerfile .

# Build stage images (example)
docker build -t $DOCKERHUB_USER/cp-whisperx-app-demux:latest -f docker/demux/Dockerfile .
docker build -t $DOCKERHUB_USER/cp-whisperx-app-asr:latest -f docker/asr/Dockerfile .

# Push to registry
docker push $DOCKERHUB_USER/cp-whisperx-app-base:cpu
docker push $DOCKERHUB_USER/cp-whisperx-app-base:cuda
docker push $DOCKERHUB_USER/cp-whisperx-app-demux:latest
docker push $DOCKERHUB_USER/cp-whisperx-app-asr:latest
```

## Testing Images

```bash
# Test CPU base
docker run --rm rajiup/cp-whisperx-app-base:cpu python --version

# Test CUDA base (requires NVIDIA GPU)
docker run --rm --gpus all rajiup/cp-whisperx-app-base:cuda nvidia-smi

# Test stage image
docker-compose run --rm demux --help
```

## Troubleshooting

### Build Failures

**Out of disk space:**
```bash
docker system prune -a
```

**Network timeout:**
```bash
# Increase timeout
export DOCKER_CLIENT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300
```

### Push Failures

**Not logged in:**
```bash
docker login
```

**Rate limited:**
- Wait 6 hours or upgrade Docker Hub plan

## Registry Configuration

Images are configured to pull from:
- Registry: `rajiup` (or `$DOCKERHUB_USER`)
- Repository: `cp-whisperx-app-{stage}`
- Tag: `latest` or `cpu`/`cuda`

Update `docker-compose.yml` to use registry images:
```yaml
services:
  demux:
    image: "${DOCKERHUB_USER:-rajiup}/cp-whisperx-app-demux:latest"
    # No build context needed when pulling from registry
```

## Image Sizes

Approximate sizes:
- base:cpu - 1.5GB
- base:cuda - 4.5GB
- CPU stages - 1.8-2.2GB each
- GPU stages - 2.5-5GB each

Total: ~15-20GB for all images

## Next Steps

After building and pushing:
1. Update docker-compose.yml to remove build contexts
2. Test on Linux/Windows with CUDA
3. Verify GPU passthrough works
4. Document GPU requirements

## Advanced: Multi-Architecture Builds

For ARM64 support (future):
```bash
docker buildx create --name multiarch --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t rajiup/cp-whisperx-app-base:cpu \
  --push \
  -f docker/base/Dockerfile .
```
