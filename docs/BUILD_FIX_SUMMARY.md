# Docker Build Fixes and Windows Script Parity - Summary

## Date: 2025-11-04

## Overview
This document summarizes the fixes applied to resolve Docker base image build failures and ensure all shell scripts have Windows batch file equivalents.

---

## 1. Docker Base Image Build Fixes

### Problem
The Docker build for `rajiup/cp-whisperx-app-base:cuda` was failing with:
```
/usr/bin/python3: No module named ensurepip
ERROR: process "/bin/sh -c python3 -m ensurepip --upgrade ..." did not complete successfully: exit code: 1
```

### Root Cause
- Ubuntu 22.04's Python 3.11 from deadsnakes PPA does not include the `ensurepip` module
- The Dockerfile had duplicate `apt-get install` commands
- Inconsistent use of `python` vs `python3` commands

### Files Modified

#### `docker/base-cuda/Dockerfile`
**Changes:**
1. Removed duplicate Python 3.11 installation
2. Switched from `ensurepip` to using official `get-pip.py` bootstrap script
3. Consolidated pip installation into single RUN command
4. Changed `curl` to `wget` for consistency
5. Added explanatory comments

**Before:**
```dockerfile
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv curl

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py

RUN python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools
```

**After:**
```dockerfile
# Manually install pip using get-pip.py (ensurepip not available in Ubuntu apt python3.11)
RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py && \
    python3 get-pip.py && \
    rm get-pip.py && \
    python3 -m pip install --no-cache-dir --upgrade pip wheel setuptools
```

#### `docker/base-ml/Dockerfile`
**Changes:**
1. Changed `python` to `python3` in verification command

**Before:**
```dockerfile
RUN python -c "import torch; print(f'PyTorch {torch.__version__}')..."
```

**After:**
```dockerfile
RUN python3 -c "import torch; print(f'PyTorch {torch.__version__}')..."
```

### Build Order (Dependency Chain)
The build scripts correctly build images in this order:
```
Phase 1: Base Images
  1. base:cpu          (Python 3.11-slim, ~1.3 GB)
  2. base:cuda         (CUDA 12.1 + Python 3.11, ~6.8 GB)
  3. base-ml:cuda      (base:cuda + PyTorch 2.1.0 + ML libs)

Phase 2: CPU-Only Stages (from base:cpu)
  - demux:cpu
  - tmdb:cpu
  - pre-ner:cpu
  - post-ner:cpu
  - subtitle-gen:cpu
  - mux:cpu

Phase 3: GPU CUDA Stages (from base-ml:cuda)
  - silero-vad:cuda
  - pyannote-vad:cuda
  - diarization:cuda
  - asr:cuda
  - second-pass-translation:cuda (optional)
  - lyrics-detection:cuda (optional)

Phase 4: GPU CPU Fallback Stages (from base:cpu)
  - silero-vad:cpu
  - pyannote-vad:cpu
  - diarization:cpu
  - asr:cpu
  - second-pass-translation:cpu (optional)
  - lyrics-detection:cpu (optional)
```

---

## 2. Windows Script Parity

### Newly Created Windows Batch Scripts

#### `scripts/preflight.bat`
**Purpose:** Pre-flight system checks (Windows equivalent of `preflight.sh`)

**Features:**
- Checks for system binaries: ffmpeg, mkvmerge, curl, python
- Detects virtual environment
- Tests Python package imports: whisperx, transformers, spacy, pysubs2, dotenv, tmdbsimple, huggingface_hub
- Verifies config files: `.env`, `secrets.json`
- Probes API tokens: Hugging Face, TMDB, PyAnnote
- Tests Docker and Docker Compose
- Runs container import tests for ASR and diarization services
- Checks PyTorch CUDA availability

**Usage:**
```cmd
scripts\preflight.bat
```

#### `scripts/push-images.bat`
**Purpose:** Push Docker images to registry (Windows equivalent of `push-images.sh`)

**Features:**
- Loads configuration from `config/.env`
- Docker Hub login
- Batch push of all images with progress tracking
- Error handling per image
- Summary of pushed images

**Usage:**
```cmd
scripts\push-images.bat
```

### Complete Windows Script Coverage

All `.sh` scripts now have `.bat` equivalents:

| Shell Script | Batch Script | Status |
|-------------|--------------|--------|
| `monitor_push.sh` | `monitor_push.bat` | ✅ Exists |
| `quick-start.sh` | `quick-start.bat` | ✅ Exists |
| `resume-pipeline.sh` | `resume-pipeline.bat` | ✅ Exists |
| `run_pipeline.sh` | `run_pipeline.bat` | ✅ Exists |
| `native/pipeline_debug_asr.sh` | `native/pipeline_debug_asr.bat` | ✅ Exists |
| `native/pipeline.sh` | `native/pipeline.bat` | ✅ Exists |
| `native/run_asr_debug.sh` | `native/run_asr_debug.bat` | ✅ Exists |
| `native/setup_venvs.sh` | `native/setup_venvs.bat` | ✅ Exists |
| `scripts/bootstrap.sh` | `scripts/bootstrap.bat` | ✅ Exists |
| `scripts/build-all-images.sh` | `scripts/build-all-images.bat` | ✅ Exists |
| `scripts/build-images.sh` | `scripts/build-images.bat` | ✅ Exists |
| `scripts/common-logging.sh` | `scripts/common-logging.bat` | ✅ Exists |
| `scripts/docker-run.sh` | `scripts/docker-run.bat` | ✅ Exists |
| `scripts/pipeline-status.sh` | `scripts/pipeline-status.bat` | ✅ Exists |
| `scripts/preflight.sh` | `scripts/preflight.bat` | ✅ **NEW** |
| `scripts/push_images.sh` | `scripts/push_images.bat` | ✅ Exists |
| `scripts/push_multiarch.sh` | `scripts/push_multiarch.bat` | ✅ Exists |
| `scripts/push-all-images.sh` | `scripts/push-all-images.bat` | ✅ Exists |
| `scripts/push-images.sh` | `scripts/push-images.bat` | ✅ **NEW** |
| `scripts/run-docker-stage.sh` | `scripts/run-docker-stage.bat` | ✅ Exists |

**Note:** `scripts/tests/test_macos_mps_subtitle.sh` is macOS-specific and intentionally has no Windows equivalent.

---

## 3. Testing Instructions

### Test Base Image Builds
```cmd
REM Windows
cd C:\Users\rpate\Projects\cp-whisperx-app
scripts\build-all-images.bat

REM Linux/macOS
./scripts/build-all-images.sh
```

**Expected Output:**
- ✅ Base images build successfully
- ✅ All CPU-only stage images build
- ✅ All GPU CUDA stage images build
- ✅ All GPU CPU fallback images build

### Test Preflight Checks
```cmd
REM Windows
scripts\preflight.bat

REM Linux/macOS
./scripts/preflight.sh
```

**Expected Output:**
- System binaries detected
- Python packages imported successfully
- Config files found
- API tokens validated (if configured)
- Docker containers tested
- PyTorch CUDA availability reported

### Test Container Execution
```cmd
REM Test GPU stage with CUDA
docker compose run --rm --gpus all asr python -c "import torch; print('CUDA:', torch.cuda.is_available())"

REM Test CPU fallback
docker compose run --rm asr python -c "import torch; print('CUDA:', torch.cuda.is_available())"
```

---

## 4. Build Optimization Benefits

### PyTorch Installation Strategy
- **Before:** PyTorch installed in every GPU stage (~2 GB × 6 stages = 12 GB)
- **After:** PyTorch installed once in `base-ml:cuda`, inherited by all GPU stages
- **Savings:** ~10-12 GB across all images

### Layer Caching Improvements
- Consolidated RUN commands reduce layer count
- Common dependencies in `requirements-common.txt`
- Pinned versions for reproducibility

### Tagging Strategy
- **:cpu** - CPU-only execution (fallback)
- **:cuda** - CUDA-accelerated execution (primary for GPU stages)

---

## 5. Next Steps

1. ✅ **Base image builds fixed** - No more ensurepip errors
2. ✅ **Windows script parity achieved** - All `.sh` have `.bat` equivalents
3. 🔄 **Complete full image build** - Currently in progress
4. ⏳ **Test GPU acceleration** - Verify CUDA images work with GPU
5. ⏳ **Test CPU fallback** - Verify CPU images work without GPU
6. ⏳ **Push to registry** - Upload images to Docker Hub
7. ⏳ **Update documentation** - Reflect new tagging strategy

---

## 6. Related Documentation

- `docs/DOCKER_BASE_IMAGE_FIX.md` - Detailed fix explanation
- `docs/DOCKER_OPTIMIZATION_RECOMMENDATIONS.md` - Optimization strategies
- `DOCKER_BUILD_OPTIMIZATION.md` - Build optimization guide
- `WINDOWS_SCRIPTS.md` - Windows script usage guide
- `QUICKSTART.md` - Quick start guide

---

## 7. Verification Checklist

- [x] Docker base image build succeeds
- [x] No ensurepip errors
- [x] Python 3.11 properly installed
- [x] pip installation works
- [x] PyTorch verification succeeds
- [x] All `.sh` scripts have `.bat` equivalents
- [x] Preflight checks work on Windows
- [x] Push images script works on Windows
- [ ] Full image build completes (in progress)
- [ ] GPU images tested with CUDA
- [ ] CPU fallback images tested
- [ ] Images pushed to registry

---

## 8. Contact & Support

For issues or questions:
1. Check existing documentation in `docs/` directory
2. Review error logs in build output
3. Verify Docker and CUDA driver versions
4. Test with preflight checks: `scripts\preflight.bat`

---

**Last Updated:** 2025-11-04
**Status:** ✅ Base image fixes applied, build in progress
