# Docker Image Management Scripts

This document describes the Docker image management scripts for pulling, building, and pushing CP-WhisperX-App container images.

## Available Scripts

### 1. Pull All Images

Pull all Docker images from the registry (Docker Hub or private registry).

**Windows:**
```batch
pull-all-images.bat
```

**Linux/macOS:**
```bash
./pull-all-images.sh
```

**What it does:**
- Pulls base images (CPU and CUDA variants)
- Pulls CPU-only stage images
- Pulls GPU stage images (CUDA variants)
- Pulls GPU stage images (CPU fallback variants)
- Reports success/failure count

**When to use:**
- Setting up a new development environment
- Updating to latest images from registry
- Deploying to production servers
- After someone else pushed updated images

### 2. Build All Images

Build all Docker images locally with proper tagging.

**Windows:**
```batch
scripts\build-all-images.bat
```

**Linux/macOS:**
```bash
./scripts/build-all-images.sh
```

**What it does:**
- Builds base images first (base:cpu, base:cuda, base-ml:cuda)
- Builds CPU-only stage images
- Builds GPU stage images (CUDA variants)
- Builds GPU stage images (CPU fallback variants)
- Tags all images with registry prefix

**Build order (optimized for caching):**
1. Phase 1: Base images
   - `base:cpu` - Python 3.11 slim with common utilities
   - `base:cuda` - NVIDIA CUDA 12.1 with Python 3.11
   - `base-ml:cuda` - CUDA base + PyTorch + ML libraries

2. Phase 2: CPU-only stages
   - demux, tmdb, pre-ner, post-ner, subtitle-gen, mux

3. Phase 3: GPU stages (CUDA variants)
   - silero-vad, pyannote-vad, diarization, asr, second-pass-translation, lyrics-detection

4. Phase 4: GPU stages (CPU fallback variants)
   - Same as Phase 3 but tagged with `:cpu`

### 3. Push All Images

Push all Docker images to the registry.

**Windows:**
```batch
scripts\push-all-images.bat
```

**Linux/macOS:**
```bash
./scripts/push-all-images.sh
```

**What it does:**
- Pushes all built images to Docker registry
- Maintains same order as build script
- Reports success/failure count

**Prerequisites:**
```bash
# Login to Docker Hub
docker login

# Or login to private registry
docker login registry.example.com
```

## Image Naming Convention

All images follow this pattern:
```
${REGISTRY}/cp-whisperx-app-${STAGE}:${TAG}
```

**Examples:**
```
rajiup/cp-whisperx-app-base:cpu
rajiup/cp-whisperx-app-base:cuda
rajiup/cp-whisperx-app-base-ml:cuda
rajiup/cp-whisperx-app-demux:cpu
rajiup/cp-whisperx-app-asr:cuda
rajiup/cp-whisperx-app-asr:cpu
```

## Environment Variables

You can customize the registry and tags:

```bash
# Windows
set DOCKER_REGISTRY=myregistry
set DOCKER_TAG=v1.0

# Linux/macOS
export DOCKER_REGISTRY=myregistry
export DOCKER_TAG=v1.0
```

**Default values:**
- `DOCKER_REGISTRY`: `rajiup`
- `DOCKER_TAG`: `latest` (but scripts use `cpu` or `cuda` explicitly)

## Image Sizes (Approximate)

| Image Type | Size | Description |
|------------|------|-------------|
| base:cpu | ~1.5 GB | Python + FFmpeg + basic tools |
| base:cuda | ~8 GB | CUDA runtime + Python |
| base-ml:cuda | ~12 GB | CUDA + PyTorch + ML libraries |
| Stage (CPU) | +50-200 MB | Base + stage-specific code |
| Stage (CUDA) | +100-500 MB | ML base + stage models |

## Workflow Examples

### Initial Setup (Developer)
```bash
# Clone repository
git clone <repo-url>
cd cp-whisperx-app

# Pull all images from registry (fastest)
./pull-all-images.sh

# Or build locally (if you want latest code)
./scripts/build-all-images.sh
```

### Making Changes
```bash
# Make code changes to a stage
vim docker/asr/whisperx_integration.py

# Rebuild just that stage
docker build -t rajiup/cp-whisperx-app-asr:cuda docker/asr

# Test the change
docker-compose up asr

# If good, rebuild all and push
./scripts/build-all-images.sh
./scripts/push-all-images.sh
```

### Production Deployment
```bash
# On production server
./pull-all-images.sh

# Start services
docker-compose up -d

# Or use Docker Swarm/Kubernetes with these images
```

### CI/CD Pipeline
```yaml
# Example GitHub Actions
steps:
  - name: Build images
    run: ./scripts/build-all-images.sh
  
  - name: Push images
    run: ./scripts/push-all-images.sh
```

## Troubleshooting

### Pull Failures
```bash
# Check Docker login
docker login

# Verify image exists
docker search rajiup/cp-whisperx-app

# Try pulling specific image
docker pull rajiup/cp-whisperx-app-base:cpu
```

### Build Failures
```bash
# Check Docker daemon
docker info

# Clean build cache
docker builder prune -a

# Build with verbose output
docker build --progress=plain -t test docker/base
```

### Disk Space Issues
```bash
# Remove unused images
docker image prune -a

# Check disk usage
docker system df

# Remove all stopped containers and images
docker system prune -a
```

## Performance Tips

1. **Use Layer Caching**: Don't modify base images frequently
2. **Multi-stage Builds**: Already implemented in ML stages
3. **BuildKit**: Enable for faster builds
   ```bash
   export DOCKER_BUILDKIT=1
   ```
4. **Parallel Builds**: Build independent stages in parallel (advanced)

## Related Documentation

- [WINDOWS_SCRIPTS.md](../WINDOWS_SCRIPTS.md) - Windows batch equivalents
- [DOCKER_BUILD_OPTIMIZATION.md](../DOCKER_BUILD_OPTIMIZATION.md) - Build optimization guide
- [docker/README.md](../docker/README.md) - Docker architecture
- [QUICKSTART.md](../QUICKSTART.md) - Getting started guide

## Support

For issues with:
- **Image pulls**: Check registry credentials and network
- **Image builds**: Check Dockerfile syntax and dependencies
- **Image pushes**: Verify registry permissions
- **Runtime issues**: See main documentation and logs
