# Docker Build Fix and Windows Script Equivalents - Summary

## Date: 2025-11-04

## Changes Made

### 1. Fixed CUDA Base Image Build Issue

**Problem**: The CUDA base image build was failing with "No module named pip" error.

**Root Cause**: Python 3.11 installed from deadsnakes PPA doesn't include pip by default.

**Solution**: Updated `docker/base-cuda/Dockerfile` to:
- Remove `python3.11-distutils` and `python3-pip` (not needed/compatible)
- Add `python3.11-venv` package
- Use `python3 -m ensurepip --upgrade` to bootstrap pip
- Then upgrade pip, wheel, and setuptools

**Files Modified**:
- `docker/base-cuda/Dockerfile` - Lines 21-46

### 2. Added Windows Script Equivalents

Created Windows batch (.bat) equivalents for all shell scripts to ensure Windows compatibility:

**New Files Created**:
1. `scripts/common-logging.bat` - Logging functions for Windows batch scripts
2. `scripts/push_images.bat` - Push images to Docker Hub (Windows version)
3. `scripts/push_multiarch.bat` - Build and push multi-arch images (Windows version)

**Existing Windows Scripts** (already present):
- `scripts/bootstrap.bat`
- `scripts/build-all-images.bat`
- `scripts/build-images.bat`
- `scripts/docker-run.bat`
- `scripts/pipeline-status.bat`
- `scripts/push-all-images.bat`
- `scripts/run-docker-stage.bat`

### 3. Implemented Registry Tag Support

Updated all Dockerfiles to use ARG for registry configuration, allowing flexible registry selection:

**Pattern Applied**:
```dockerfile
ARG REGISTRY=rajiup
FROM ${REGISTRY}/cp-whisperx-app-base:cpu
```

**Files Modified**:
- `docker/base/Dockerfile` - No change needed (base image)
- `docker/base-cuda/Dockerfile` - No change needed (base image)
- `docker/base-ml/Dockerfile` - Added ARG REGISTRY
- `docker/demux/Dockerfile` - Added ARG REGISTRY
- `docker/tmdb/Dockerfile` - Added ARG REGISTRY
- `docker/pre-ner/Dockerfile` - Added ARG REGISTRY
- `docker/post-ner/Dockerfile` - Added ARG REGISTRY
- `docker/subtitle-gen/Dockerfile` - Added ARG REGISTRY
- `docker/mux/Dockerfile` - Added ARG REGISTRY
- `docker/silero-vad/Dockerfile` - Added ARG REGISTRY
- `docker/pyannote-vad/Dockerfile` - Added ARG REGISTRY
- `docker/diarization/Dockerfile` - Added ARG REGISTRY
- `docker/asr/Dockerfile` - Added ARG REGISTRY
- `docker/second-pass-translation/Dockerfile` - Added ARG REGISTRY
- `docker/lyrics-detection/Dockerfile` - Added ARG REGISTRY

### 4. Updated Build Scripts to Pass Registry Argument

Updated `scripts/build-all-images.bat` to pass `--build-arg REGISTRY=%REGISTRY%` to all docker build commands.

**Impact**: Users can now override the registry by setting DOCKERHUB_USER environment variable.

### 5. Optimized Base Images

**Key Optimization**: Removed PyTorch and ML packages from `base-cuda` image.

**Rationale**:
- PyTorch is ~2GB and only needed for ML stages
- Moving PyTorch to `base-ml:cuda` saves significant space
- Non-ML stages can use lighter `base:cuda` if needed in future

**Build Hierarchy**:
```
base:cpu (Python 3.11-slim + FFmpeg + basic utils)
  ├── demux:cpu
  ├── tmdb:cpu
  ├── pre-ner:cpu
  ├── post-ner:cpu
  ├── subtitle-gen:cpu
  ├── mux:cpu
  └── [CPU fallback variants of GPU stages]

base:cuda (CUDA 12.1 + Python 3.11 + basic utils)
  └── base-ml:cuda (+ PyTorch 2.1.0 + ML packages)
      ├── silero-vad:cuda
      ├── pyannote-vad:cuda
      ├── diarization:cuda
      ├── asr:cuda
      ├── second-pass-translation:cuda
      └── lyrics-detection:cuda
```

## Docker Image Tagging Strategy

### CPU-Only Stages (tag: `:cpu`)
Built from `base:cpu`:
- demux:cpu
- tmdb:cpu
- pre-ner:cpu
- post-ner:cpu
- subtitle-gen:cpu
- mux:cpu

### GPU Stages (tag: `:cuda`)
Built from `base-ml:cuda`:
- silero-vad:cuda
- pyannote-vad:cuda
- diarization:cuda
- asr:cuda
- second-pass-translation:cuda
- lyrics-detection:cuda

### CPU Fallback Variants (tag: `:cpu`)
Same stages as GPU but built with CPU-only base for fallback:
- silero-vad:cpu
- pyannote-vad:cpu
- diarization:cpu
- asr:cpu
- second-pass-translation:cpu
- lyrics-detection:cpu

## Build Order

The `build-all-images.bat` script builds in this order:

1. **Phase 1**: Base Images
   - base:cpu (CRITICAL - required for all CPU stages)
   - base:cuda (CRITICAL - required for base-ml)
   - base-ml:cuda (CRITICAL - required for all GPU stages)

2. **Phase 2**: CPU-Only Stages
   - All 6 CPU-only stages in parallel

3. **Phase 3**: GPU Stages (CUDA variants)
   - All GPU stages with CUDA support

4. **Phase 4**: GPU Stages (CPU fallback variants)
   - CPU fallback versions for GPU stages

## Usage

### Building Images

```bash
# Windows
scripts\build-all-images.bat

# Set custom registry
set DOCKERHUB_USER=myuser
scripts\build-all-images.bat

# Linux/Mac
scripts/build-all-images.sh
export DOCKERHUB_USER=myuser
scripts/build-all-images.sh
```

### Pushing Images

```bash
# Windows
set DOCKERHUB_USER=rajiup
scripts\push_images.bat

# With options
scripts\push_images.bat --no-push        # Build only, don't push
scripts\push_images.bat --skip-base      # Skip base images

# Linux/Mac
export DOCKERHUB_USER=rajiup
scripts/push_images.sh
```

### Multi-Arch Build

```bash
# Windows
set DOCKERHUB_USER=rajiup
scripts\push_multiarch.bat

# Linux/Mac
export DOCKERHUB_USER=rajiup
scripts/push_multiarch.sh
```

## Testing

To verify the fix works:

1. Build base images:
   ```bash
   scripts\build-all-images.bat
   ```

2. Check that all base images built successfully:
   - base:cpu should complete
   - base:cuda should complete (previously failed)
   - base-ml:cuda should complete

3. Verify CUDA functionality in container:
   ```bash
   docker run --rm rajiup/cp-whisperx-app-base:cuda python -c "import sys; print(sys.version)"
   docker run --rm rajiup/cp-whisperx-app-base-ml:cuda python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA available: {torch.cuda.is_available()}')"
   ```

## Notes

- All shell scripts now have Windows batch equivalents
- Registry can be customized via DOCKERHUB_USER environment variable
- Base images are built first to minimize overall build time
- CPU fallback variants are automatically generated from CUDA Dockerfiles
- Build script stops immediately if any base image fails (critical path)

## Next Steps

1. Test the build with: `scripts\build-all-images.bat`
2. Verify all images are tagged correctly
3. Test GPU stages with `docker compose run --rm --gpus all asr`
4. Test CPU fallback with `docker compose run --rm asr`
5. Push to registry when ready: `scripts\push-all-images.bat`
