# Hardware Detection & Configuration Flow

This document describes the complete hardware detection and auto-configuration flow in cp-whisperx-app.

## Overview

The system automatically detects your hardware capabilities and configures optimal settings for maximum performance and stability. The configuration flows from **bootstrap** → **config/.env.pipeline** → **job-specific .env file** → **runtime stages**.

## Configuration Flow

### 1. Hardware Detection (Bootstrap Phase)

**Location:** `shared/hardware_detection.py`

**When:** During `./scripts/bootstrap.sh`

**What it does:**
- Detects CPU cores, threads, and memory
- Detects GPU type (CUDA, MPS, or CPU-only)
- Measures GPU memory (VRAM for CUDA, unified memory for MPS)
- Calculates optimal batch sizes based on GPU memory
- Determines best Whisper model for available resources
- Calculates optimal compute type (int8, float16, float32)

**Outputs:**
- `out/hardware_cache.json` - Cached hardware information (1-hour validity)
- Updates to `config/.env.pipeline` with detected settings

**Example Hardware Cache:**
```json
{
  "detected_at": "2025-11-13T18:30:00",
  "platform": "Darwin",
  "cpu_cores": 10,
  "cpu_threads": 10,
  "memory_gb": 32.0,
  "gpu_available": true,
  "gpu_type": "mps",
  "gpu_name": "Apple M2 Max",
  "gpu_memory_gb": 16.0,
  "recommended_settings": {
    "whisper_model": "large-v3",
    "batch_size": 8,
    "compute_type": "float16",
    "device_whisperx": "mps",
    "device_diarization": "mps"
  }
}
```

---

### 2. Auto-Configuration (Bootstrap Script)

**Location:** `scripts/bootstrap.sh`

**When:** During initial setup (`./scripts/bootstrap.sh`)

**What it does:**
- Runs hardware detection (`python shared/hardware_detection.py --no-cache`)
- Reads hardware cache and extracts recommended settings
- Exports `DEVICE_OVERRIDE` environment variable with detected device
- Logs recommended batch size and Whisper model
- **For macOS/MPS:** Sets MPS environment variables for stability:
  - `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` (prevents memory fragmentation)
  - `PYTORCH_ENABLE_MPS_FALLBACK=0` (fail fast instead of silent CPU fallback)
  - `MPS_ALLOC_MAX_SIZE_MB=4096` (4GB max allocation)

**Updates config/.env.pipeline with:**
```bash
DEVICE=mps
BATCH_SIZE=8
WHISPERX_DEVICE=mps
WHISPER_MODEL=large-v3
WHISPER_COMPUTE_TYPE=float16
SILERO_DEVICE=mps
PYANNOTE_DEVICE=mps
DIARIZATION_DEVICE=mps

# MPS ENVIRONMENT VARIABLES (Apple Silicon)
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
PYTORCH_ENABLE_MPS_FALLBACK=0
MPS_ALLOC_MAX_SIZE_MB=4096
```

**Console Output:**
```
[INFO] DEVICE_OVERRIDE=mps
[INFO] Recommended batch size: 8 (saved to config/.env.pipeline)
[INFO] Recommended Whisper model: large-v3 (saved to config/.env.pipeline)
[INFO] Apple Silicon (MPS) detected - configuring environment...
  ✓ PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 (prevents fragmentation)
  ✓ PYTORCH_ENABLE_MPS_FALLBACK=0 (fail fast on errors)
  ✓ MPS_ALLOC_MAX_SIZE_MB=4096 (4GB max allocation)
```

---

### 3. Job Preparation (Prepare-Job Script)

**Location:** `scripts/prepare-job.py`

**When:** When preparing a new job (`./prepare-job.sh /path/to/movie.mp4`)

**What it does:**
- Reads hardware cache (`out/hardware_cache.json`)
- Copies `config/.env.pipeline` as the base template
- Creates job-specific directory structure:
  ```
  out/YYYY/MM/DD/<user-id>/<job-id>/
    ├── .env.<job-id>        # Job-specific config (inherits from .env.pipeline)
    ├── job.json              # Job metadata
    ├── logs/                 # Job logs
    └── [stage outputs]/      # Stage-specific outputs
  ```
- Customizes `.env.<job-id>` with:
  - Job ID, title, year (parsed from filename)
  - Input/output paths
  - Workflow mode (transcribe vs subtitle-gen)
  - Stage enable/disable flags
  - **Inherits all hardware-optimized settings from config/.env.pipeline**

**Job Configuration File Example:**
```bash
# ============================================================================
# CP-WhisperX-App Job Configuration
# Generated: 2025-11-13T18:35:00
# Job ID: 20251113_183500_abc123
# ============================================================================

# ============================================================================
# HARDWARE DETECTION & OPTIMIZATION
# ============================================================================
# CPU: 10 cores (10 threads)
# Memory: 32.0 GB RAM
# GPU: Apple M2 Max
# GPU Memory: 16.0 GB
# GPU Type: MPS
#
# RECOMMENDATION: GPU acceleration available
# ============================================================================

JOB_ID=20251113_183500_abc123
TITLE="Dil Chahta Hai"
YEAR=2001
IN_ROOT=/path/to/dil_chahta_hai_2001.mp4
OUTPUT_ROOT=out/2025/11/13/1/20251113_183500_abc123
LOG_ROOT=out/2025/11/13/1/20251113_183500_abc123/logs

# Hardware-optimized model selection
# GPU has 16.0GB - perfect for large-v3 Hinglish accuracy
WHISPER_MODEL=large-v3

# Batch size optimized for available resources
# Auto-calculated for 16.0GB VRAM + large-v3 model
BATCH_SIZE=8

# Compute type optimized for device
# GPU supports efficient float16 for best quality
WHISPER_COMPUTE_TYPE=float16

# Device configuration (inherited from config/.env.pipeline)
DEVICE=mps
WHISPERX_DEVICE=mps
SILERO_DEVICE=mps
PYANNOTE_DEVICE=mps
DIARIZATION_DEVICE=mps

# MPS environment variables (inherited from config/.env.pipeline)
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
PYTORCH_ENABLE_MPS_FALLBACK=0
MPS_ALLOC_MAX_SIZE_MB=4096
```

---

### 4. Runtime Integration (Pipeline Execution)

**Location:** `scripts/device_selector.py` + ML stage scripts

**When:** During pipeline execution (`./run_pipeline.sh -j <job-id>`)

**What it does:**
- Each ML stage reads device configuration from job's `.env.<job-id>` file
- `device_selector.py` provides graceful fallback:
  - **Priority:** MPS → CUDA → CPU
  - If MPS fails, automatically retries on CPU
  - If CUDA fails, automatically retries on CPU
- MPS batch sizes are auto-optimized by pipeline orchestrator for stability
- Runtime device validation ensures compatibility

**Stage Device Selection:**
```python
# All ML stages use device_selector.py
from scripts.device_selector import select_whisperx_device

# Read DEVICE from job environment (set by prepare-job)
requested_device = os.getenv('WHISPERX_DEVICE', 'cpu')

# Select device with automatic fallback
device, compute_type, did_fallback = select_whisperx_device(requested_device)

if did_fallback:
    logger.warning(f"Requested device {requested_device} not available, using {device}")

# Use selected device
model = load_whisper_model(device=device, compute_type=compute_type)
```

---

## Hardware Profiles & Recommendations

### High-End GPU (12GB+ VRAM)
- **GPU:** RTX 3090, 4090, A100, M2/M3 Max
- **Whisper Model:** large-v3 (best Hinglish accuracy)
- **Compute Type:** float16
- **Batch Size:** 12-16
- **Speedup:** 15-20x vs CPU

### Mid-High GPU (8-12GB VRAM)
- **GPU:** RTX 3070, 4070, M1/M2 Pro
- **Whisper Model:** large-v3
- **Compute Type:** float16
- **Batch Size:** 6-8
- **Speedup:** 12-15x vs CPU

### Mid-Range GPU (6-8GB VRAM)
- **GPU:** RTX 3060, 4060, M1/M2 Base
- **Whisper Model:** large-v3 (with batch_size=1)
- **Compute Type:** float16
- **Batch Size:** 1-2
- **Speedup:** 10-12x vs CPU

### Entry GPU (4-6GB VRAM)
- **GPU:** RTX 3050, GTX 1650
- **Whisper Model:** medium
- **Compute Type:** float16
- **Batch Size:** 1
- **Speedup:** 8-10x vs CPU

### CPU-Only (16GB+ RAM)
- **Whisper Model:** large-v3 (slow but accurate)
- **Compute Type:** int8 (quantized for speed)
- **Batch Size:** 1-2 (if 16+ CPU cores)
- **Speedup:** 1x (baseline)

### CPU-Only (8-16GB RAM)
- **Whisper Model:** medium
- **Compute Type:** int8
- **Batch Size:** 1
- **Speedup:** 1x (baseline)

---

## Manual Override

You can manually override any settings in `config/.env.pipeline` after bootstrap:

```bash
# Edit global pipeline config
nano config/.env.pipeline

# Change device (mps, cuda, cpu)
DEVICE=cpu

# Change Whisper model (tiny, base, small, medium, large-v3)
WHISPER_MODEL=medium

# Change batch size (1-32)
BATCH_SIZE=4

# Change compute type (int8, float16, float32)
WHISPER_COMPUTE_TYPE=int8
```

**Note:** Changes to `config/.env.pipeline` will affect all future jobs but NOT existing jobs.

To override an existing job:
```bash
# Edit job-specific config
nano out/2025/11/13/1/<job-id>/.env.<job-id>

# Make your changes
DEVICE=cpu
BATCH_SIZE=1
```

---

## Troubleshooting

### "MPS device not available" error
- **Cause:** PyTorch doesn't have MPS support or running on non-Apple Silicon
- **Solution:** System will automatically fall back to CPU
- **Verify:** Check `config/.env.pipeline` shows `DEVICE=cpu`

### "Out of memory" error on MPS
- **Cause:** Batch size too large for available unified memory
- **Solution:** Hardware detection automatically sets conservative batch sizes
- **Manual fix:** Reduce `BATCH_SIZE` in job config to 1

### GPU detected but not used
- **Cause:** PyTorch is CPU-only build
- **Detection:** Bootstrap will show "PyTorch: CPU-only build"
- **Solution:** Install CUDA-enabled PyTorch:
  ```bash
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
  ```

### Legacy GPU (CC 5.0-6.9)
- **Example:** GTX 980 Ti, GTX 1060
- **Issue:** PyTorch 2.x doesn't support compute capability < 7.0
- **Detection:** Bootstrap shows "Legacy GPU (CC 5.5)"
- **Solution:** Install PyTorch 1.13 (not recommended, limited support)

---

## Summary

The configuration flow ensures optimal performance automatically:

1. **Bootstrap** detects hardware → saves to `out/hardware_cache.json` and `config/.env.pipeline`
2. **Prepare-job** copies `config/.env.pipeline` → customizes for job → saves to `.env.<job-id>`
3. **Runtime** reads `.env.<job-id>` → uses `device_selector.py` for graceful fallback
4. **Result:** Maximum performance with automatic optimization and stability

All hardware-tuned parameters flow from bootstrap through to runtime execution, with no manual intervention required.
