# Docker Tagging Strategy Refactoring

**Date:** November 4, 2025  
**Status:** Refactoring Complete - Ready for Build

## Summary

Refactored Docker image tagging strategy to use explicit `:cpu` and `:cuda` tags instead of `:latest`, with clear separation between CPU-only and GPU-accelerated stages.

## Changes Made

### 1. Docker Compose Configuration

**File:** `docker-compose.yml`

**Changed:**
- **CPU-Only Stages:** Now use `:cpu` tag explicitly
  - demux:cpu
  - tmdb:cpu
  - pre-ner:cpu
  - post-ner:cpu
  - subtitle-gen:cpu
  - mux:cpu

- **GPU Stages:** Now use `:cuda` tag explicitly
  - silero-vad:cuda
  - pyannote-vad:cuda
  - diarization:cuda
  - asr:cuda

**Result:** Clear separation of CPU-only vs GPU-capable images

---

### 2. CPU-Only Stage Dockerfiles

**Changed Base Image:** `FROM rajiup/cp-whisperx-app-base:latest` → `FROM rajiup/cp-whisperx-app-base:cpu`

**Files Updated:**
- ✅ `docker/demux/Dockerfile`
- ✅ `docker/tmdb/Dockerfile`
- ✅ `docker/pre-ner/Dockerfile`
- ✅ `docker/post-ner/Dockerfile`
- ✅ `docker/subtitle-gen/Dockerfile`
- ✅ `docker/mux/Dockerfile`

**Result:** All CPU-only stages explicitly built from `base:cpu`

---

### 3. GPU Stage Dockerfiles

**Changed Base Image:** `FROM rajiup/cp-whisperx-app-base:latest` → `FROM rajiup/cp-whisperx-app-base:cuda`

**Changed PyTorch Index:** 
```dockerfile
# OLD
--index-url https://download.pytorch.org/whl/cpu

# NEW
--index-url https://download.pytorch.org/whl/cu121
```

**Files Updated:**
- ✅ `docker/silero-vad/Dockerfile`
  - Base: cuda
  - PyTorch: cu121

- ✅ `docker/pyannote-vad/Dockerfile`
  - Base: cuda
  - PyTorch: cu121

- ✅ `docker/diarization/Dockerfile`
  - Base: cuda
  - PyTorch: cu121

- ✅ `docker/asr/Dockerfile`
  - Base: cuda
  - PyTorch: cu121

- ✅ `docker/second-pass-translation/Dockerfile`
  - Base: cuda (optional stage)

- ✅ `docker/lyrics-detection/Dockerfile`
  - Base: cuda (optional stage)

**Result:** All GPU stages built from `base:cuda` with CUDA-enabled PyTorch

---

### 4. Build Scripts

**Files Updated:**
- ✅ `scripts/build-all-images.bat` (Windows)
- ✅ `scripts/build-all-images.sh` (Linux/Mac)

**Changes:**
- Removed `:latest` tag from base image build
- Phase 2: Build CPU-only stages with `:cpu` tag
- Phase 3: Build GPU stages with `:cuda` tag (using CUDA PyTorch)
- Updated summary output to show tagging strategy
- Clearer phase descriptions

**Old Behavior:**
```batch
Phase 1: Build base:cpu and base:cuda
Phase 2: Build CPU stages with :cpu
Phase 3: Build GPU stages with :cpu (wrong!)
Phase 4: Note about CUDA (not implemented)
```

**New Behavior:**
```batch
Phase 1: Build base:cpu and base:cuda
Phase 2: Build CPU-only stages with :cpu
Phase 3: Build GPU stages with :cuda
```

---

## Tag Strategy Overview

### Base Images

| Image | Tag | Base | Purpose |
|-------|-----|------|---------|
| cp-whisperx-app-base | cpu | python:3.11-slim | CPU-only foundation |
| cp-whisperx-app-base | cuda | nvidia/cuda:12.1.0-cudnn8 | GPU foundation with CUDA 12.1 |

### CPU-Only Stages (6)

All built from `base:cpu`, no GPU support needed:

| Stage | Tag | PyTorch | Purpose |
|-------|-----|---------|---------|
| demux | cpu | N/A | FFmpeg audio extraction |
| tmdb | cpu | N/A | TMDB API metadata |
| pre-ner | cpu | N/A | spaCy entity extraction |
| post-ner | cpu | N/A | spaCy entity correction |
| subtitle-gen | cpu | N/A | SRT generation |
| mux | cpu | N/A | FFmpeg video muxing |

### GPU Stages (4-6)

All built from `base:cuda` with CUDA PyTorch:

| Stage | Tag | PyTorch | CUDA Benefit |
|-------|-----|---------|--------------|
| silero-vad | cuda | cu121 | 14x speedup |
| pyannote-vad | cuda | cu121 | 17x speedup |
| diarization | cuda | cu121 | 25x speedup |
| asr | cuda | cu121 | 12x speedup |
| second-pass-translation | cuda | cu121 | Optional |
| lyrics-detection | cuda | cu121 | Optional |

---

## Build Command

```bash
# Windows
scripts\build-all-images.bat

# Linux/Mac
./scripts/build-all-images.sh
```

**What Gets Built:**
- `rajiup/cp-whisperx-app-base:cpu` (1.34 GB)
- `rajiup/cp-whisperx-app-base:cuda` (13.9 GB)
- 6 CPU-only stage images with `:cpu` tag (~1.3-1.8 GB each)
- 4-6 GPU stage images with `:cuda` tag (~1.5-3 GB each)

**Total Size:** ~25-30 GB for all images

---

## Usage Examples

### CPU-Only Pipeline (No GPU)
```bash
# All stages use :cpu images
docker compose run --rm demux in/movie.mp4
docker compose run --rm tmdb "Movie Title" 2024
# ... etc
```

### GPU-Accelerated Pipeline (With NVIDIA GPU)
```bash
# GPU stages use :cuda images with GPU passthrough
docker compose run --rm --gpus all asr out/Movie_Name
docker compose run --rm --gpus all diarization out/Movie_Name
```

### Full Pipeline
```bash
# docker-compose.yml configured with correct tags
python pipeline.py -i in/movie.mp4
```

---

## Verification

### Check Built Images
```bash
docker images | grep "rajiup/cp-whisperx-app"
```

**Expected Output:**
```
rajiup/cp-whisperx-app-base         cpu
rajiup/cp-whisperx-app-base         cuda
rajiup/cp-whisperx-app-demux        cpu
rajiup/cp-whisperx-app-tmdb         cpu
rajiup/cp-whisperx-app-pre-ner      cpu
rajiup/cp-whisperx-app-silero-vad   cuda
rajiup/cp-whisperx-app-pyannote-vad cuda
rajiup/cp-whisperx-app-diarization  cuda
rajiup/cp-whisperx-app-asr          cuda
rajiup/cp-whisperx-app-post-ner     cpu
rajiup/cp-whisperx-app-subtitle-gen cpu
rajiup/cp-whisperx-app-mux          cpu
```

### Test GPU Access (CUDA Images)
```bash
# Test if CUDA image can access GPU
docker run --rm --gpus all rajiup/cp-whisperx-app-asr:cuda python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Expected:** `CUDA available: True`

---

## Breaking Changes

⚠️ **Important:** This is a breaking change from previous tagging strategy.

### What Changed
- **OLD:** All images used `:cpu` or `:latest` tags
- **NEW:** CPU-only stages use `:cpu`, GPU stages use `:cuda`

### Migration Required
If you have existing scripts or docker-compose files that reference image tags:

1. **Update CPU-only stage references:**
   - Keep `:cpu` tag (no change needed)

2. **Update GPU stage references:**
   - Change from `:cpu` to `:cuda`
   - Example: `asr:cpu` → `asr:cuda`

3. **Remove `:latest` references:**
   - Change to explicit `:cpu` or `:cuda`

---

## Benefits of New Strategy

1. **Clear Intent:** Tag explicitly shows if image supports GPU
2. **No Ambiguity:** No more `:latest` confusion
3. **Correct PyTorch:** CUDA images have CUDA PyTorch, not CPU
4. **Better Performance:** GPU stages now actually use GPU
5. **Explicit Dependencies:** Base image relationship is clear
6. **Easier Debugging:** Tag tells you what to expect

---

## Files Modified

### Configuration Files (2)
- ✅ `docker-compose.yml` - Updated all image tags

### Dockerfiles (12)
- ✅ `docker/demux/Dockerfile`
- ✅ `docker/tmdb/Dockerfile`
- ✅ `docker/pre-ner/Dockerfile`
- ✅ `docker/post-ner/Dockerfile`
- ✅ `docker/subtitle-gen/Dockerfile`
- ✅ `docker/mux/Dockerfile`
- ✅ `docker/silero-vad/Dockerfile`
- ✅ `docker/pyannote-vad/Dockerfile`
- ✅ `docker/diarization/Dockerfile`
- ✅ `docker/asr/Dockerfile`
- ✅ `docker/second-pass-translation/Dockerfile`
- ✅ `docker/lyrics-detection/Dockerfile`

### Build Scripts (2)
- ✅ `scripts/build-all-images.bat`
- ✅ `scripts/build-all-images.sh`

**Total Files Modified:** 16 files

---

## Next Steps

1. ✅ **Refactoring Complete** - No code changes needed
2. ⏳ **Build Images** - Run build script
3. ⏳ **Test Locally** - Verify images work
4. ⏳ **Push to Registry** - Upload to Docker Hub
5. ⏳ **Update Documentation** - Document new tags

---

## Testing Plan

### Pre-Build Checks
```bash
# Verify Dockerfiles reference correct base images
grep -r "FROM rajiup/cp-whisperx-app-base" docker/

# Should show:
# - CPU stages: base:cpu
# - GPU stages: base:cuda
```

### Post-Build Checks
```bash
# 1. Verify all images built
docker images | grep "rajiup/cp-whisperx-app"

# 2. Check CPU image (should NOT have CUDA)
docker run --rm rajiup/cp-whisperx-app-demux:cpu python -c "import sys; print(sys.version)"

# 3. Check CUDA image (should have CUDA)
docker run --rm --gpus all rajiup/cp-whisperx-app-asr:cuda nvidia-smi

# 4. Test pipeline stage
docker compose run --rm demux in/test.mp4
```

---

## Troubleshooting

### Build Fails: "base:cpu not found"
**Solution:** Build base images first
```bash
docker build -t rajiup/cp-whisperx-app-base:cpu -f docker/base/Dockerfile .
```

### Build Fails: "base:cuda not found"
**Solution:** Build CUDA base first
```bash
docker build -t rajiup/cp-whisperx-app-base:cuda -f docker/base-cuda/Dockerfile .
```

### Runtime Error: "CUDA not available"
**Solution:** 
1. Ensure using `:cuda` tag
2. Add `--gpus all` flag
3. Verify NVIDIA Docker runtime installed

### Wrong PyTorch Version
**Solution:** Check Dockerfile uses correct index URL
- CPU: `--index-url https://download.pytorch.org/whl/cpu`
- CUDA: `--index-url https://download.pytorch.org/whl/cu121`

---

## Related Documentation

- `docker/README.md` - Complete Docker image documentation
- `DOCKER_BUILD_GUIDE.md` - Build instructions
- `CUDA_ACCELERATION_GUIDE.md` - GPU performance info
- `BUILD_STATUS.md` - Current build progress

---

**Refactoring Status:** ✅ Complete  
**Code Status:** ✅ Ready for Build  
**Build Status:** ⏳ Pending Execution
