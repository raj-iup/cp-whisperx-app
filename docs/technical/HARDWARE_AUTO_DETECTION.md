# Hardware Auto-Detection & Configuration

**Question**: Does bootstrap auto-detect hardware capabilities and inject tuned parameters for MPS/CUDA/CPU optimization?

**Answer**: ✅ **YES** - Hardware settings are automatically detected and written to config file!

---

## How It Works (Updated Flow)

### 1. Hardware Detection
`shared/hardware_detection.py` detects:
- **CPU**: Cores, threads, brand
- **Memory**: Total, available
- **GPU Type**: 
  - `cuda` (NVIDIA with PyTorch support)
  - `mps` (Apple Silicon M1/M2/M3/M4)
  - `cpu` (fallback)
- **GPU Memory**: Available VRAM/unified memory
- **Compute Capability**: For CUDA GPUs
- **PyTorch Compatibility**: full/legacy/incompatible

### 2. Optimal Settings Calculation
`calculate_optimal_settings()` recommends:
- **Whisper Model**: large-v3 for GPU, medium for CPU
- **Batch Size**: Based on GPU memory (1-32)
- **Compute Type**: float16/float32/int8
- **Device**: mps/cuda/cpu
- **Performance Profile**: high-accuracy/balanced/fast

### 3. Auto-Configuration to Config File ✨ NEW
`update_pipeline_config()` writes to `config/.env.pipeline`:
1. **DEVICE=** mps/cuda/cpu
2. **BATCH_SIZE=** 1-32 (GPU memory based)
3. **WHISPER_MODEL=** large-v3/medium/base
4. **WHISPER_COMPUTE_TYPE=** float16/int8
5. **Stage Devices**: SILERO_DEVICE, PYANNOTE_DEVICE, DIARIZATION_DEVICE, WHISPERX_DEVICE

### 4. Bootstrap Execution
`scripts/bootstrap.sh`:
1. Runs hardware detection
2. Config file auto-updated
3. MPS environment variables set (if macOS)
4. User informed of updates

### 5. Job Preparation
`prepare-job.sh`:
1. Copies `config/.env.pipeline` to job directory
2. Job gets hardware-optimized configuration
3. No need for environment variable passing

### 6. Runtime Execution
Pipeline stages:
1. Read device from job config file
2. Use optimized batch sizes
3. Falls back gracefully if needed

---

## What Gets Auto-Configured

### ✅ Config File Updates

**Config file: `config/.env.pipeline`** is automatically updated with:

```bash
# Global device setting
DEVICE=mps                    # Auto-detected (mps/cuda/cpu)

# ASR settings
BATCH_SIZE=8                  # Optimized for GPU memory
WHISPER_MODEL=large-v3        # Best model for your hardware
WHISPER_COMPUTE_TYPE=float16  # Optimal precision
WHISPERX_DEVICE=mps          # ASR stage device

# VAD settings
SILERO_DEVICE=mps            # Silero VAD device
PYANNOTE_DEVICE=mps          # PyAnnote VAD device

# Diarization settings
DIARIZATION_DEVICE=mps       # Diarization device
```

### ✅ MPS Environment Variables (macOS)

**If Apple Silicon detected**, bootstrap also sets:
```bash
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0  # Prevents memory fragmentation
PYTORCH_ENABLE_MPS_FALLBACK=0         # Fail fast instead of silent CPU fallback
MPS_ALLOC_MAX_SIZE_MB=4096            # 4GB max allocation per chunk
```

### ✅ Batch Size Optimization

| Hardware | GPU Memory | Batch Size | Model |
|----------|-----------|------------|--------|
| M3 Max (48GB) | 24GB | 16 | large-v3 |
| M3 Pro (18GB) | 10GB | 8 | large-v3 |
| M3 Base (16GB) | 8GB | 8 | large-v3 |
| RTX 4090 (24GB) | 24GB | 32 | large-v3 |
| RTX 3080 (10GB) | 10GB | 16 | large-v3 |
| CPU Only | N/A | 1 | medium |

### ✅ MPS Environment Variables (macOS)

**Automatically set on Apple Silicon**:
```bash
PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0  # Prevents memory fragmentation
PYTORCH_ENABLE_MPS_FALLBACK=0         # Fail fast instead of silent CPU fallback
MPS_ALLOC_MAX_SIZE_MB=4096            # 4GB max allocation per chunk
```

---

## How Pipeline Uses Auto-Detected Settings

### Config File is Source of Truth

**All stages read from job config** (copied from `config/.env.pipeline`):

```python
# Job config loaded by pipeline orchestrator
job_config = load_env_file(f"{job_dir}/.env")

# Device extracted from config
device = job_config.get('WHISPERX_DEVICE', 'cpu')
batch_size = int(job_config.get('BATCH_SIZE', 16))
model = job_config.get('WHISPER_MODEL', 'large-v3')
```

### Stage-Specific Device Selection

Each ML stage reads its device from config:

**ASR (whisperx_integration.py)**:
```python
device = os.getenv('WHISPERX_DEVICE', 'cpu')  # From job config
batch_size = int(os.getenv('BATCH_SIZE', 16))
```

**Diarization (diarization.py)**:
```python
device = os.getenv('DIARIZATION_DEVICE', 'cpu')
```

**VAD (pyannote_vad_chunker.py)**:
```python
device = os.getenv('PYANNOTE_DEVICE', 'cpu')  # or SILERO_DEVICE
```

### MPS Batch Size Optimization

**whisperx_integration.py**:
```python
from mps_utils import optimize_batch_size_for_mps

# Apply MPS-specific optimization
batch_size = optimize_batch_size_for_mps(batch_size, device, model)
# → MPS: Reduces 16 → 8 for stability
# → CUDA: Keeps 16-32 (stable)
# → CPU: Reduces to 1
```

---

## User Override Mechanism

### Editing Config File (Recommended)

**Simply edit `config/.env.pipeline`**:

```bash
# Force CPU for all stages
DEVICE=cpu

# Force specific device per stage
WHISPERX_DEVICE=cpu          # ASR on CPU
DIARIZATION_DEVICE=mps       # Diarization on MPS
SILERO_DEVICE=cuda           # VAD on CUDA

# Adjust batch size
BATCH_SIZE=4                 # Smaller batches (more stable)
BATCH_SIZE=16                # Larger batches (faster)

# Change model
WHISPER_MODEL=medium         # Faster but less accurate
WHISPER_MODEL=large-v3       # Best accuracy

# Change compute type
WHISPER_COMPUTE_TYPE=int8    # CPU optimization
WHISPER_COMPUTE_TYPE=float16 # GPU optimization
```

**Changes persist** and apply to all future jobs!

### Temporary Override (Environment Variable)

```bash
# One-time override for this run only
WHISPERX_DEVICE=cpu ./run_pipeline.sh --job my-job --stages asr
```

### Priority Order

1. **Environment variable** (highest): `WHISPERX_DEVICE=cpu`
2. **Job config file**: `{job_dir}/.env` (copied from config/.env.pipeline)
3. **Global config**: `config/.env.pipeline` (auto-updated by hardware detection)
4. **Hardcoded default** (lowest): `cpu`

---

## Decision Tree

```
┌─────────────────────────────────────┐
│ Run bootstrap.sh                    │
└─────────────────┬───────────────────┘
                  │
                  ▼
┌─────────────────────────────────────┐
│ Hardware Detection                  │
│ (shared/hardware_detection.py)     │
└─────────────────┬───────────────────┘
                  │
                  ▼
         ┌────────┴────────┐
         │ macOS?          │
         └────┬────────┬───┘
              │        │
          YES │        │ NO
              │        │
              ▼        ▼
    ┌─────────────┐  ┌──────────────┐
    │ Apple       │  │ NVIDIA GPU?  │
    │ Silicon?    │  └──────┬───────┘
    └─────┬───────┘         │
          │            YES  │  NO
      YES │  NO            │  │
          │  │             ▼  ▼
          ▼  ▼         ┌──────────┐
    ┌─────────────┐   │   CPU    │
    │    MPS      │   │  device  │
    │   device    │   │ batch=1  │
    │ + MPS env   │   └──────────┘
    │ batch=8-16  │   
    └─────────────┘   
          │             │
          └──────┬──────┘
                 │
                 ▼
    ┌─────────────────────────────┐
    │ Export DEVICE_OVERRIDE      │
    │ Set recommended batch size  │
    └─────────────┬───────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ Pipeline uses settings      │
    │ - All stages auto-configured│
    │ - User can override         │
    └─────────────────────────────┘
```

---

## Example: Bootstrap Output

### Apple Silicon M3 Max

```bash
$ ./scripts/bootstrap.sh

════════════════════════════════════════════════════════════
 HARDWARE DETECTION & CACHING
════════════════════════════════════════════════════════════
Detecting hardware capabilities...
  ✓ CPU: 10 cores (10 threads)
  ✓ RAM: 48.0 GB total, 32.5 GB available
  ✓ Apple Silicon: Apple M1 Pro
  ✓ Unified Memory: ~24.0 GB available for GPU
  ✓ PyTorch MPS: Available
  ✓ Hardware cache saved: out/hardware_cache.json
  ✓ Updated pipeline config: config/.env.pipeline
    • DEVICE=mps
    • BATCH_SIZE=16
    • WHISPERX_DEVICE=mps
    • WHISPER_MODEL=large-v3
    • WHISPER_COMPUTE_TYPE=float16

✓ Hardware detection complete
  → Hardware cache: out/hardware_cache.json
  → Pipeline config: config/.env.pipeline (auto-updated)
  → Settings applied: DEVICE, BATCH_SIZE, WHISPER_MODEL, etc.
  → You can manually override settings in config/.env.pipeline if needed

════════════════════════════════════════════════════════════
 MPS OPTIMIZATION
════════════════════════════════════════════════════════════
Configuring MPS environment variables for Apple Silicon...
  ✓ PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0 (prevents fragmentation)
  ✓ PYTORCH_ENABLE_MPS_FALLBACK=0 (fail fast on errors)
  ✓ MPS_ALLOC_MAX_SIZE_MB=4096 (4GB max allocation)
✓ MPS environment optimized for stability
```

### NVIDIA RTX 4090

```bash
$ ./scripts/bootstrap.sh

════════════════════════════════════════════════════════════
 HARDWARE DETECTION & CACHING
════════════════════════════════════════════════════════════
Detecting hardware capabilities...
  ✓ CPU: 16 cores (32 threads)
  ✓ RAM: 64.0 GB total, 48.2 GB available
  ✓ NVIDIA GPU: NVIDIA GeForce RTX 4090
  ✓ VRAM: 24.0 GB
  ✓ CUDA Version: 12.1
  ✓ Compute Capability: 8.9
  ✓ Hardware cache saved: out/hardware_cache.json
  ✓ Updated pipeline config: config/.env.pipeline
    • DEVICE=cuda
    • BATCH_SIZE=32
    • WHISPERX_DEVICE=cuda
    • WHISPER_MODEL=large-v3
    • WHISPER_COMPUTE_TYPE=float16

✓ Hardware detection complete
  → Hardware cache: out/hardware_cache.json
  → Pipeline config: config/.env.pipeline (auto-updated)
  → Settings applied: DEVICE, BATCH_SIZE, WHISPER_MODEL, etc.
```

### CPU Only

```bash
$ ./scripts/bootstrap.sh

════════════════════════════════════════════════════════════
 HARDWARE DETECTION & CACHING
════════════════════════════════════════════════════════════
Detecting hardware capabilities...
  ✓ CPU: 8 cores (16 threads)
  ✓ RAM: 16.0 GB total, 8.5 GB available
  ✓ GPU: Not available (CPU mode)
  ✓ Hardware cache saved: out/hardware_cache.json
  ✓ Updated pipeline config: config/.env.pipeline
    • DEVICE=cpu
    • BATCH_SIZE=1
    • WHISPERX_DEVICE=cpu
    • WHISPER_MODEL=medium
    • WHISPER_COMPUTE_TYPE=int8

✓ Hardware detection complete
  → Hardware cache: out/hardware_cache.json
  → Pipeline config: config/.env.pipeline (auto-updated)
  → Settings applied: DEVICE, BATCH_SIZE, WHISPER_MODEL, etc.
```

---

## Verification

### Check Auto-Detected Settings

```bash
# View updated config file
cat config/.env.pipeline | grep "^DEVICE=\|^BATCH_SIZE=\|^WHISPER"

# View hardware cache
cat out/hardware_cache.json | python3 -m json.tool

# View recommended settings from cache
python3 -c "
import json
with open('out/hardware_cache.json') as f:
    hw = json.load(f)
settings = hw.get('recommended_settings', {})
print(f\"Device: {hw.get('gpu_type')}\")
print(f\"Batch: {settings.get('batch_size')}\")
print(f\"Model: {settings.get('whisper_model')}\")
print(f\"Compute: {settings.get('compute_type')}\")
"
```

### Check Pipeline Usage

```bash
# Run ASR and check what device is actually used
./run_pipeline.sh --job test --stages asr

# Verify device from logs
grep "device.*mps\|cuda\|cpu" out/*/logs/07_asr*.log

# Verify batch size from logs
grep "batch.*size" out/*/logs/07_asr*.log

# Verify config was copied to job
cat out/*/test/.env | grep "DEVICE\|BATCH_SIZE"
```

### Test Configuration Override

```bash
# Edit config to force CPU
sed -i.bak 's/^DEVICE=.*/DEVICE=cpu/' config/.env.pipeline

# Run bootstrap again (won't override your manual change)
# Actually, it WILL override. To prevent:
# 1. Edit config/.env.pipeline AFTER running bootstrap
# 2. OR comment out the lines you want to keep manual

# Better: Edit after bootstrap, or use per-stage override
```

---

## Summary

### ✅ YES - Bootstrap Auto-Detects and Writes to Config!

**What's Auto-Detected**:
- ✅ Hardware type (MPS/CUDA/CPU)
- ✅ GPU memory
- ✅ Optimal device
- ✅ Recommended batch size
- ✅ Best Whisper model
- ✅ Compute type (float16/int8)

**What's Auto-Written to `config/.env.pipeline`**:
- ✅ `DEVICE=mps/cuda/cpu`
- ✅ `BATCH_SIZE=1-32`
- ✅ `WHISPER_MODEL=large-v3/medium/base`
- ✅ `WHISPER_COMPUTE_TYPE=float16/int8`
- ✅ `WHISPERX_DEVICE=mps/cuda/cpu`
- ✅ `SILERO_DEVICE`, `PYANNOTE_DEVICE`, `DIARIZATION_DEVICE`

**What Happens at Runtime**:
- ✅ `prepare-job.sh` copies config to job directory
- ✅ Pipeline stages read from job config file
- ✅ MPS batch sizes further optimized by mps_utils
- ✅ Graceful fallback if device unavailable

**User Control**:
- ✅ Edit `config/.env.pipeline` anytime (changes persist)
- ✅ Per-stage device override
- ✅ Temporary env var override
- ✅ Re-run bootstrap to re-detect and update

**Integration with Workflow**:
```
Bootstrap (once)
  ├─> Detect hardware
  ├─> Calculate optimal settings  
  └─> Write to config/.env.pipeline ✨

Prepare Job (per job)
  └─> Copy config/.env.pipeline to job/.env ✨

Pipeline Execution (runtime)
  └─> Read settings from job/.env ✨
      ├─> Device selection
      ├─> Batch size
      ├─> Model selection
      └─> MPS optimization (if needed)
```

**Key Benefit**: Config file is the single source of truth, no environment variable juggling!

---

**Result**: The pipeline automatically adapts to your hardware and persists settings in config file for consistent, optimized performance!

