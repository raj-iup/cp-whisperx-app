# MLX Acceleration Guide for Apple Silicon

## Overview

This guide explains how to enable **full GPU acceleration** on Apple Silicon (M1, M2, M3) using MLX framework.

## Quick Start

```bash
# 1. Install MLX (one-time)
./install-mlx.sh

# 2. Run bootstrap
./scripts/bootstrap.sh

# 3. Prepare job (auto-detects MLX)
./prepare-job.sh "movie.mp4" --transcribe -s hi

# 4. Run pipeline (auto-uses MLX)
./run-pipeline.sh -j <job-id>
```

**Note**: You can also use the shorter names:
- `./prepare-job.sh` (wrapper for prepare-job.sh)
- `./run-pipeline.sh` (wrapper for run-pipeline.sh)

## Architecture

The pipeline now supports **dual-backend architecture**:

| Device Type | Backend | GPU Acceleration | Performance |
|------------|---------|------------------|-------------|
| **MPS** (Apple Silicon) | MLX-Whisper | ✅ Full GPU | Fast ⚡ |
| **CUDA** (NVIDIA) | WhisperX | ✅ Full GPU | Fast ⚡ |
| **CPU** (Any) | WhisperX | ❌ CPU only | Slower 🐌 |

## Why MLX?

### Problem
- **WhisperX** uses faster-whisper (CTranslate2) backend
- **CTranslate2** only supports: CPU, CUDA
- **CTranslate2** does NOT support: MPS (Apple Silicon)

### Solution
- **MLX** is Apple's ML framework optimized for Apple Silicon
- **MLX-Whisper** is a Whisper implementation using MLX
- **Full MPS GPU acceleration** for transcription

## Installation

### Step 1: Install MLX

```bash
./install-mlx.sh
```

This installs:
- `mlx` - Apple's ML framework
- `mlx-whisper` - Whisper for MLX

### Step 2: Verify Installation

```bash
source .bollyenv/bin/activate
python -c "import mlx; import mlx_whisper; print('✓ MLX ready')"
```

### Step 3: Re-run Bootstrap

```bash
./scripts/bootstrap.sh
```

This will:
- Detect MPS device
- Set `WHISPER_BACKEND=mlx`
- Configure for GPU acceleration

## Usage

### Transcribe Workflow

```bash
# 1. Prepare job (auto-detects MLX backend for MPS)
./prepare-job.sh "movie.mp4" --transcribe --source-language hi

# 2. Run pipeline (auto-uses MLX for MPS)
./run-pipeline.sh -j <job-id>
```

### Translate Workflow

```bash
# 1. Prepare translate job
./prepare-job.sh "movie.mp4" --translate \
  --source-language hi --target-language en

# 2. Run pipeline (IndicTrans2 can use MPS too)
./run-pipeline.sh -j <job-id>
```

## Backend Selection Logic

The pipeline **automatically** selects the appropriate backend:

```python
if device == "mps" and backend == "mlx":
    # Use MLX-Whisper (GPU accelerated on Apple Silicon)
    use_mlx_whisper()
elif device == "cuda":
    # Use WhisperX with CUDA (GPU accelerated on NVIDIA)
    use_whisperx_cuda()
else:
    # Use WhisperX with CPU (works everywhere)
    use_whisperx_cpu()
```

## Configuration

### Hardware Cache (`out/hardware_cache.json`)

After bootstrap with MLX installed:

```json
{
  "gpu_type": "mps",
  "gpu_name": "Apple M1 Pro",
  "gpu_memory_gb": 10.0,
  "recommended_settings": {
    "whisper_model": "large-v3",
    "compute_type": "float16",
    "batch_size": 2,
    "whisper_backend": "mlx"  ← MLX backend
  }
}
```

### Job Configuration (`.job-id.env`)

```bash
# Set by prepare-job
WHISPERX_DEVICE=mps              # MPS device
WHISPER_BACKEND=mlx              # MLX backend
WHISPER_MODEL=large-v3           # Model size
WHISPER_COMPUTE_TYPE=float16     # Precision
BATCH_SIZE=2                     # Batch size
```

## Performance Comparison

### 2-Hour Hindi Movie

| Configuration | Time | Speedup |
|--------------|------|---------|
| **CPU** (Intel i7) | ~120 min | 1x |
| **CPU** (Apple M1 fallback) | ~90 min | 1.3x |
| **MLX** (Apple M1 Pro GPU) | ~15-20 min | 6-8x ⚡ |
| **CUDA** (NVIDIA RTX 3090) | ~10-15 min | 8-12x ⚡ |

*Note: Times are estimates and may vary based on hardware, model size, and batch size.*

## Pipeline Logs

### With MLX (MPS)

```
[INFO] Configured device: mps (from job config)
[INFO] Backend: mlx (from job config)
[INFO] Using MLX-Whisper for MPS acceleration
[INFO] Loading MLX-Whisper model: large-v3
[INFO] Using MPS (Apple Silicon GPU) acceleration
[INFO] Transcription completed: 150 segments
[INFO] ✅ Stage asr: COMPLETED (15.3s)
```

### Without MLX (CPU Fallback)

```
[INFO] Configured device: mps (from job config)
[INFO] Backend: whisperx (from job config)
[WARN] MPS device detected but MLX backend not configured
[WARN] Falling back to CPU (slower performance)
[INFO] Using WhisperX with device: cpu
[INFO] Transcription completed: 150 segments
[INFO] ✅ Stage asr: COMPLETED (90.5s)
```

## Troubleshooting

### Issue: MLX not found

**Symptom:**
```
ModuleNotFoundError: No module named 'mlx'
```

**Solution:**
```bash
./install-mlx.sh
```

### Issue: CPU fallback on MPS

**Symptom:**
```
[WARN] Falling back to CPU (slower performance)
```

**Solution:**
1. Install MLX: `./install-mlx.sh`
2. Re-run bootstrap: `./scripts/bootstrap.sh`
3. Create new job (old jobs have old config)

### Issue: Out of memory on GPU

**Symptom:**
```
RuntimeError: Metal out of memory
```

**Solution:**
Edit job's `.env` file:
```bash
# Reduce batch size
BATCH_SIZE=1

# Or use smaller model
WHISPER_MODEL=medium
```

## Advanced Configuration

### Force CPU (Disable MLX)

Edit job's `.env` before running pipeline:

```bash
WHISPERX_DEVICE=cpu
WHISPER_BACKEND=whisperx
```

### Change Model Size

For faster processing (lower accuracy):
```bash
WHISPER_MODEL=medium  # or small, base, tiny
```

For best accuracy (slower):
```bash
WHISPER_MODEL=large-v3
```

### Adjust Batch Size

For more GPU memory available:
```bash
BATCH_SIZE=4  # Higher = faster but more memory
```

For less GPU memory:
```bash
BATCH_SIZE=1  # Lower = slower but less memory
```

## IndicTrans2 with MPS

IndicTrans2 also supports MPS acceleration:

```bash
# In job .env
INDICTRANS2_DEVICE=mps  # Set by prepare-job
```

Both ASR (WhisperX/MLX) and Translation (IndicTrans2) can use MPS GPU simultaneously!

## Benefits

### With MLX on Apple Silicon

✅ **6-8x faster** than CPU fallback  
✅ **Full GPU utilization** of Apple Silicon  
✅ **Lower power consumption** than CPU  
✅ **Better thermal management** (cooler, quieter)  
✅ **Automatic backend selection** (no manual config)  
✅ **Same accuracy** as other backends  

### Dual-Backend Architecture

✅ **Works on any hardware** (MPS, CUDA, CPU)  
✅ **Automatic optimization** per platform  
✅ **No manual configuration** required  
✅ **Fallback to CPU** if GPU unavailable  

## Summary

1. **Install MLX**: `./install-mlx.sh` (one-time setup)
2. **Run Bootstrap**: `./scripts/bootstrap.sh` (detects MLX)
3. **Use Pipeline**: Normal workflow, auto-uses MLX!

The pipeline now **automatically** uses:
- **MLX-Whisper** for MPS (Apple Silicon) → GPU accelerated ⚡
- **WhisperX** for CUDA (NVIDIA) → GPU accelerated ⚡
- **WhisperX** for CPU (fallback) → Works everywhere ✓

**Result**: Maximum performance on your hardware! 🚀

---

**Last Updated**: November 18, 2025, 16:00 UTC  
**Status**: ✅ MLX Integration Complete
