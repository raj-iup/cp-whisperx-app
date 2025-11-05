# Docker Base Image Build Fix

## Problem Summary
The Docker base image builds were failing due to missing `ensurepip` module in Python 3.11 installed via apt on Ubuntu 22.04.

### Error Details
```
/usr/bin/python3: No module named ensurepip
```

This occurred during the `base:cuda` image build when trying to bootstrap pip.

## Root Cause
Ubuntu's `python3.11` package from the deadsnakes PPA does not include the `ensurepip` module by default. The `python3.11-venv` package includes it, but we were trying to use `ensurepip` before installing that package properly.

## Solution Applied

### File: `docker/base-cuda/Dockerfile`

**Changed from:**
```dockerfile
# Bootstrap pip using ensurepip
# Install Python 3.11 and venv
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv curl

# Manually install pip using get-pip.py
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

# Upgrade pip, wheel, setuptools
RUN python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools
```

**Changed to:**
```dockerfile
# Set python3.11 as default python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Manually install pip using get-pip.py (ensurepip not available in Ubuntu apt python3.11)
RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools
```

**Key Changes:**
1. Removed duplicate `apt-get install` for `python3.11 python3.11-venv curl`
2. Consolidated pip installation into a single RUN command for better layer caching
3. Used `wget` instead of `curl` (consistent with other system packages installed)
4. Added comment explaining why `ensurepip` is not used

### File: `docker/base-ml/Dockerfile`

**Changed from:**
```dockerfile
RUN python -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Changed to:**
```dockerfile
RUN python3 -c "import torch; print(f'PyTorch {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Key Changes:**
1. Changed `python` to `python3` for consistency (USER is switched to appuser which may not have `python` alias)

## Windows Script Equivalents Created

### 1. `scripts/preflight.bat`
Windows equivalent of `scripts/preflight.sh` for pre-flight system checks.

**Features:**
- System binary checks (ffmpeg, mkvmerge, curl, python)
- Virtual environment detection
- Python package import checks
- Config file verification
- API token probes (HF, TMDB, PyAnnote)
- Docker and container tests
- PyTorch device detection

### 2. `scripts/push-images.bat`
Windows equivalent of `scripts/push-images.sh` for pushing Docker images to registry.

**Features:**
- Docker Hub login
- Batch image push with progress tracking
- Error handling
- Configuration loading from `.env` file

## Build Script Status

The build scripts (`build-all-images.sh` and `build-all-images.bat`) were already properly configured with:
- Phase 1: Build base images in correct order (base:cpu → base:cuda → base-ml:cuda)
- Phase 2: Build CPU-only stages from base:cpu
- Phase 3: Build GPU CUDA stages from base-ml:cuda
- Phase 4: Build GPU CPU fallback stages from base:cpu
- Proper error handling and dependency checking

## Images Build Strategy

### Base Images
1. **base:cpu** - CPU-only base (Python 3.11-slim, ~1.3 GB)
2. **base:cuda** - CUDA base with Python 3.11 (~6.8 GB)
3. **base-ml:cuda** - ML base with PyTorch 2.1.0 + CUDA support (builds on base:cuda)

### CPU-Only Stages (from base:cpu)
- demux:cpu
- tmdb:cpu
- pre-ner:cpu
- post-ner:cpu
- subtitle-gen:cpu
- mux:cpu

### GPU Stages (from base-ml:cuda)
- silero-vad:cuda
- pyannote-vad:cuda
- diarization:cuda
- asr:cuda
- second-pass-translation:cuda (optional)
- lyrics-detection:cuda (optional)

### GPU Fallback Stages (from base:cpu)
- silero-vad:cpu
- pyannote-vad:cpu
- diarization:cpu
- asr:cpu
- second-pass-translation:cpu (optional)
- lyrics-detection:cpu (optional)

## Benefits of the Fix

1. **Eliminates ensurepip dependency**: Uses official `get-pip.py` bootstrap script
2. **Better layer caching**: Consolidated RUN commands reduce layer count
3. **Consistent tooling**: Uses `wget` which is already installed
4. **Clear documentation**: Comments explain why ensurepip is not used
5. **Proper Python alias**: Uses `python3` consistently to avoid ambiguity

## Testing

To test the build:
```bash
# Windows
scripts\build-all-images.bat

# Linux/macOS
./scripts/build-all-images.sh
```

Expected result: All base images build successfully without ensurepip errors.

## Next Steps

1. Complete the full image build (ongoing)
2. Test GPU images with `docker compose run --rm --gpus all asr`
3. Test CPU fallback with `docker compose run --rm asr`
4. Push images to registry with `scripts\push-all-images.bat`

## References

- [Ubuntu Python ensurepip issue](https://askubuntu.com/questions/1469080/ubuntu-23-04-python3-no-module-named-ensurepip)
- [Python get-pip.py documentation](https://pip.pypa.io/en/stable/installation/)
- [Docker best practices for Python](https://docs.docker.com/language/python/build-images/)
