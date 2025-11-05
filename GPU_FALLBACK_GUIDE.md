# GPU Fallback Implementation Guide

**Date:** November 4, 2025  
**Status:** Implementation Complete  
**Feature:** Automatic CPU fallback for GPU stages

## Overview

Implemented automatic GPU-to-CPU fallback for ML stages. If GPU execution fails or is unavailable, the system automatically falls back to CPU execution.

## Architecture

### Image Strategy

Each GPU-capable stage now has **TWO image variants**:

1. **CUDA Variant** (`:cuda` tag)
   - Built from `base:cuda`
   - Uses PyTorch with CUDA support (`cu121`)
   - Requires NVIDIA GPU with CUDA 12.1+
   - Provides 12-25x speedup

2. **CPU Fallback** (`:cpu` tag)
   - Built from `base:cpu`
   - Uses PyTorch with CPU-only support
   - Works on any system
   - Slower but reliable fallback

### Affected Stages

| Stage | CUDA Image | CPU Image | Speedup (CUDA) |
|-------|------------|-----------|----------------|
| silero-vad | :cuda | :cpu | 14x |
| pyannote-vad | :cuda | :cpu | 17x |
| diarization | :cuda | :cpu | 25x |
| asr | :cuda | :cpu | 12x |
| second-pass-translation | :cuda | :cpu | TBD |
| lyrics-detection | :cuda | :cpu | TBD |

**CPU-Only Stages** (no fallback needed):
- demux, tmdb, pre-ner, post-ner, subtitle-gen, mux

---

## Build Process

### Automated CPU Variant Generation

The build scripts automatically create CPU fallback images by:
1. Taking the CUDA Dockerfile
2. Replacing `base:cuda` with `base:cpu`
3. Replacing `cu121` PyTorch index with `cpu`
4. Building as `:cpu` variant

### Build Commands

```bash
# Windows
scripts\build-all-images.bat

# Linux/Mac
./scripts/build-all-images.sh
```

**What Gets Built:**
- Phase 1: Base images (cpu, cuda)
- Phase 2: CPU-only stages (6 images)
- Phase 3: GPU stages with CUDA (4-6 images)
- Phase 4: GPU stages with CPU fallback (4-6 images)

**Total Images:** ~20 images (2 base + 6 CPU-only + 6 CUDA + 6 CPU-fallback)

---

## Usage

### Option 1: Python Script (Recommended)

**Automatic GPU fallback:**
```bash
# Tries GPU first, falls back to CPU automatically
python scripts/run_docker_stage.py asr --movie-dir out/Movie_Name
```

**Force CPU execution:**
```bash
python scripts/run_docker_stage.py asr --movie-dir out/Movie_Name --no-gpu
```

**Explicit GPU attempt:**
```bash
python scripts/run_docker_stage.py asr --movie-dir out/Movie_Name --try-gpu
```

### Option 2: Docker Compose with Profiles

**GPU execution:**
```bash
COMPOSE_PROFILES=gpu docker compose -f docker-compose-fallback.yml up
```

**CPU execution:**
```bash
COMPOSE_PROFILES=cpu docker compose -f docker-compose-fallback.yml up
```

**Default (CPU fallback):**
```bash
docker compose -f docker-compose-fallback.yml up
```

### Option 3: Direct Docker Commands

**Try CUDA:**
```bash
docker run --rm --gpus all \
  -v ./in:/app/in:ro -v ./out:/app/out \
  rajiup/cp-whisperx-app-asr:cuda \
  --movie-dir /app/out/Movie_Name
```

**Fallback to CPU:**
```bash
docker run --rm \
  -v ./in:/app/in:ro -v ./out:/app/out \
  rajiup/cp-whisperx-app-asr:cpu \
  --movie-dir /app/out/Movie_Name
```

---

## Fallback Logic

### Decision Tree

```
Start
  │
  ├─ Is GPU available? (nvidia-smi)
  │  ├─ NO → Use CPU image
  │  └─ YES
  │      │
  │      ├─ Does CUDA image exist?
  │      │  ├─ NO → Use CPU image
  │      │  └─ YES → Try CUDA image
  │      │      │
  │      │      ├─ Success? → Done ✓
  │      │      └─ Failed → Fallback to CPU image
  │
  └─ Run with CPU image
```

### Trigger Conditions

Fallback to CPU occurs when:

1. **GPU Not Available**
   - No NVIDIA GPU detected
   - `nvidia-smi` fails
   - CUDA drivers not installed

2. **Image Not Found**
   - CUDA image not built
   - CUDA image not pulled from registry
   - Image tag mismatch

3. **Execution Failure**
   - Out of GPU memory
   - CUDA initialization error
   - Model loading failure
   - Container crash

4. **User Override**
   - `--no-gpu` flag specified
   - `GPU_AVAILABLE=false` environment variable

---

## File Changes

### New Files Created (5)

1. **`docker-compose-fallback.yml`**
   - Docker Compose with GPU profile support
   - Defines both GPU and CPU variants
   - Uses profiles for conditional execution

2. **`scripts/run_docker_stage.py`**
   - Python script for intelligent fallback
   - Detects GPU availability
   - Manages image selection
   - Handles retry logic

3. **`scripts/run-docker-stage.bat`** (Windows)
   - Batch wrapper for Python script

4. **`scripts/run-docker-stage.sh`** (Linux/Mac)
   - Shell wrapper for Python script

5. **`GPU_FALLBACK_GUIDE.md`** (this file)
   - Complete documentation

### Modified Files (2)

1. **`scripts/build-all-images.bat`**
   - Added Phase 4: CPU fallback variants
   - Automated CPU image generation
   - Updated summary output

2. **`scripts/build-all-images.sh`**
   - Added Phase 4: CPU fallback variants
   - Sed-based Dockerfile modification
   - Updated summary output

---

## Configuration

### Environment Variables

```bash
# Docker registry (default: rajiup)
export DOCKERHUB_USER=myregistry

# GPU tag variant (default: cuda)
export GPU_TAG=cuda

# Force CPU execution
export GPU_AVAILABLE=false

# Config path
export CONFIG_PATH=/app/config/.env
```

### Python Script Options

```bash
--try-gpu       # Try GPU first (default: True)
--no-gpu        # Force CPU execution
--registry      # Docker registry (default: $DOCKERHUB_USER or rajiup)
```

---

## Testing

### Test GPU Availability

```bash
# Check if GPU is available
nvidia-smi

# Check if Docker can access GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
```

### Test Image Existence

```bash
# Check if images exist
docker images | grep "rajiup/cp-whisperx-app"

# Expected to see both :cuda and :cpu for GPU stages
```

### Test Fallback Logic

```bash
# Test with GPU (should use CUDA)
python scripts/run_docker_stage.py silero-vad --movie-dir out/Test

# Test without GPU (should use CPU)
python scripts/run_docker_stage.py silero-vad --movie-dir out/Test --no-gpu

# Test with non-existent CUDA image (should fallback to CPU)
docker rmi rajiup/cp-whisperx-app-silero-vad:cuda
python scripts/run_docker_stage.py silero-vad --movie-dir out/Test
```

### Test Full Pipeline

```bash
# Build test movie directory
mkdir -p out/Test_Movie/{audio,vad,diarization,transcription}

# Run each GPU stage with fallback
for stage in silero-vad pyannote-vad diarization asr; do
    echo "Testing $stage..."
    python scripts/run_docker_stage.py $stage --movie-dir out/Test_Movie
done
```

---

## Performance Comparison

### With GPU (CUDA images)

| Stage | CPU Time | GPU Time | Speedup |
|-------|----------|----------|---------|
| silero-vad | 217s | 15s | 14x |
| pyannote-vad | 687s | 40s | 17x |
| diarization | 5917s | 240s | 25x |
| asr | 2236s | 180s | 12x |
| **Total** | **151 min** | **8 min** | **19x** |

### Without GPU (CPU fallback)

| Stage | CPU Time | Notes |
|-------|----------|-------|
| silero-vad | 217s | Slower but works |
| pyannote-vad | 687s | May need more memory |
| diarization | 5917s | Very slow (98 min) |
| asr | 2236s | May timeout on large files |
| **Total** | **151 min** | Same as pure CPU |

**Conclusion:** GPU provides massive speedup, but CPU fallback ensures pipeline always completes.

---

## Troubleshooting

### GPU Not Detected

**Symptom:** Always uses CPU images

**Solutions:**
1. Install NVIDIA drivers: `nvidia-smi`
2. Install nvidia-docker: `docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi`
3. Check WSL2 (Windows): Enable CUDA in WSL2

### CUDA Image Fails

**Symptom:** CUDA image starts but crashes

**Common Causes:**
- Out of GPU memory → Reduce batch size
- CUDA version mismatch → Use CUDA 12.1 compatible GPU
- Model loading failure → Check HuggingFace token

**Solution:** Script automatically falls back to CPU

### Both Images Fail

**Symptom:** CPU fallback also fails

**Solutions:**
1. Check image exists: `docker images | grep rajiup/cp-whisperx-app`
2. Pull from registry: `docker pull rajiup/cp-whisperx-app-asr:cpu`
3. Rebuild: `scripts\build-all-images.bat`

### Slow CPU Execution

**Symptom:** CPU fallback takes very long

**Solutions:**
1. Install GPU if available (recommended)
2. Use smaller Whisper model: `--model base` instead of `large-v3`
3. Process in chunks with `--start-time` and `--end-time`
4. Increase CPU cores for Docker

---

## Migration Guide

### From Old Setup (CPU-only)

**No changes needed!** Your existing CPU images will continue to work.

### To GPU Setup

1. **Build CUDA images:**
   ```bash
   scripts\build-all-images.bat
   ```

2. **Test GPU access:**
   ```bash
   nvidia-smi
   docker run --rm --gpus all nvidia/cuda:12.1.0-base nvidia-smi
   ```

3. **Run with GPU:**
   ```bash
   python scripts/run_docker_stage.py asr --movie-dir out/Movie
   ```

4. **Automatic fallback:** If GPU fails, script uses CPU automatically

---

## Best Practices

### When to Use GPU

✅ **Use GPU when:**
- NVIDIA GPU available (GTX 1060+ or RTX series)
- Processing long videos (>30 min)
- Need faster turnaround time
- Running multiple jobs
- Using large Whisper models (large-v2, large-v3)

### When to Use CPU Fallback

✅ **Use CPU when:**
- No GPU available
- GPU out of memory
- Testing/debugging
- Processing short clips (<5 min)
- Using small Whisper models (tiny, base)

### Optimization Tips

1. **GPU:** Increase batch size for better GPU utilization
2. **CPU:** Use smaller models to reduce processing time
3. **Both:** Process in chunks for very long videos
4. **Hybrid:** Use GPU for slow stages (diarization, ASR), CPU for fast stages

---

## Future Enhancements

### Planned Features

- [ ] Multi-GPU support (distribute across multiple GPUs)
- [ ] Cloud GPU fallback (AWS, GCP, Azure)
- [ ] Automatic batch size tuning
- [ ] Performance monitoring and statistics
- [ ] Cost optimization (GPU vs CPU based on job size)

### Potential Improvements

- Smart scheduling (queue GPU jobs when GPU available)
- Resource pooling (share GPU across multiple jobs)
- Checkpoint/resume for long-running GPU jobs
- Remote GPU execution (SSH to GPU machine)

---

## Related Documentation

- `CUDA_ACCELERATION_GUIDE.md` - GPU performance benchmarks
- `DOCKER_REFACTORING_SUMMARY.md` - Image tagging strategy
- `docker/README.md` - Docker image documentation
- `DOCKER_BUILD_GUIDE.md` - Build instructions

---

## Summary

**What We Built:**

✅ Dual-variant images for each GPU stage (CUDA + CPU)  
✅ Automated CPU image generation during build  
✅ Python script with intelligent fallback logic  
✅ Docker Compose with profile support  
✅ Comprehensive error handling  
✅ Zero-configuration fallback  

**Benefits:**

🚀 **Speed:** 12-25x faster with GPU  
🛡️ **Reliability:** Always has CPU fallback  
⚙️ **Flexibility:** Manual or automatic GPU selection  
📊 **Visibility:** Clear logging of which variant is used  
🔧 **Maintainability:** Single Dockerfile per stage  

**Ready to Use:** Build images and start using GPU with automatic CPU fallback! 🎉
