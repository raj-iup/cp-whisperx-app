# Docker Build Fixes

## Issues Identified

### 1. ✅ FIXED: base-ml:cuda - Python command not found
**Error**: `RUN python -c "import torch..."`
**Cause**: Python 3.11 is installed as `python3`, not `python`
**Fix**: Changed `python` to `python3` in verification command

### 2. ✅ VERIFIED: diarization:cuda - libav library versions
**Status**: Already correct in Dockerfile
**Libraries**: Ubuntu 22.04 ships with libav58 series (libavformat58, libavcodec58, etc.)
**Dockerfile**: Already specifies correct versions

### 3. Build Order Dependencies
**Correct Order**:
1. `base:cpu` - CPU-only base (from python:3.11-slim)
2. `base:cuda` - CUDA base with Python 3.11 (from nvidia/cuda:12.1.0)
3. `base-ml:cuda` - ML base with PyTorch (from base:cuda)
4. All CPU stages (from base:cpu)
5. All CUDA stages (from base-ml:cuda)
6. All CPU fallback stages (from base:cpu or modified Dockerfiles)

## Build Script Status

### ✅ scripts/build-all-images.bat
- Implements correct build order
- Builds base images first
- Stops on base image failure
- Handles CPU and CUDA variants

### ✅ scripts/build-all-images.sh
- Linux/Mac equivalent of build script

### ✅ scripts/pull-all-images.bat
- Pulls all images from Docker registry
- Handles base, CPU, and CUDA variants

### ✅ scripts/pull-all-images.sh
- Linux/Mac equivalent of pull script

## Missing Windows Equivalents

Only one test script missing:
- `scripts/tests/test_macos_mps_subtitle.sh` → Not needed (Mac-specific)

## Next Steps

1. Test base image builds (may take 10-15 minutes each)
2. Verify PyTorch installation in base-ml:cuda
3. Test stage image builds
4. Update documentation

## Build Time Estimates

- base:cpu: ~5-7 minutes
- base:cuda: ~15-20 minutes (Python 3.11 installation + CUDA setup)
- base-ml:cuda: ~10-15 minutes (PyTorch installation)
- Each CPU stage: ~2-5 minutes
- Each CUDA stage: ~3-7 minutes
- **Total estimated time**: 60-90 minutes for all images
