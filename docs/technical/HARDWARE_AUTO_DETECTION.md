# Hardware Auto-Detection & Configuration

**Question**: Does bootstrap auto-detect hardware capabilities and inject tuned parameters for MPS/CUDA/CPU optimization?

**Answer**: ✅ **YES** - Now it does!

---

## How It Works

### 1. Hardware Detection (Existing)
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

### 2. Optimal Settings Calculation (Existing)
`calculate_optimal_settings()` recommends:
- **Whisper Model**: large-v3 for GPU, medium for CPU
- **Batch Size**: Based on GPU memory (1-32)
- **Compute Type**: float16/float32/int8
- **Performance Profile**: high-accuracy/balanced/fast

### 3. Auto-Configuration (NEW! ✅)
`scripts/bootstrap.sh` now:
1. Runs hardware detection
2. Reads `out/hardware_cache.json`
3. **Extracts `gpu_type`** → Exports `DEVICE_OVERRIDE`
4. **Extracts `batch_size`** → Logs recommendation
5. Configures MPS environment vars (if macOS)

---

## What Gets Auto-Configured

### ✅ Device Selection

**macOS Apple Silicon (M1/M2/M3/M4)**:
```bash
→ Auto-detected device: mps
→ DEVICE_OVERRIDE=mps
→ MPS environment optimized for stability
  ✓ PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
  ✓ PYTORCH_ENABLE_MPS_FALLBACK=0
  ✓ MPS_ALLOC_MAX_SIZE_MB=4096
```

**NVIDIA GPU (CUDA)**:
```bash
→ Auto-detected device: cuda
→ DEVICE_OVERRIDE=cuda
→ Batch size: 16-32 (based on VRAM)
```

**CPU Only**:
```bash
→ Auto-detected device: cpu
→ DEVICE_OVERRIDE=cpu
→ Batch size: 1 (CPU optimized)
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

### Runtime Device Selection

Each ML stage uses **device_selector.py**:

```python
from device_selector import select_device

# Reads DEVICE_OVERRIDE from environment (set by bootstrap)
device, did_fallback = select_device("auto")
# → Returns: "mps" (on Apple Silicon)
# → Returns: "cuda" (on NVIDIA)
# → Returns: "cpu" (fallback)
```

### MPS Batch Size Optimization

**whisperx_integration.py**:
```python
from mps_utils import optimize_batch_size_for_mps

# Starts with detected batch size
batch_size = optimize_batch_size_for_mps(batch_size, device, 'large')
# → MPS: Reduces 16 → 8 for stability
# → CUDA: Keeps 16-32 (stable)
# → CPU: Reduces to 1
```

### Stage-Specific Optimization

All ML stages benefit:

**ASR (whisperx_integration.py)**:
- Device: Auto-detected (mps/cuda/cpu)
- Batch size: MPS-optimized
- Chunking: Auto-enabled for MPS
- Memory cleanup: After each chunk

**Diarization (diarization.py)**:
- Device: Auto-detected
- Memory logging: Before/after
- Memory cleanup: Always

**VAD (pyannote_vad_chunker.py)**:
- Device: Auto-detected
- Memory cleanup: Per chunk

---

## User Override Mechanism

### Option 1: Config File Override

**config/.env.pipeline**:
```bash
# Override auto-detected device
DEVICE_OVERRIDE=cpu          # Force CPU (testing)
DEVICE_OVERRIDE=mps          # Force MPS
DEVICE_OVERRIDE=cuda         # Force CUDA

# Override batch size
ASR_BATCH_SIZE=4            # Smaller batches (more stable)
ASR_BATCH_SIZE=16           # Larger batches (faster)

# Per-stage overrides
WHISPERX_DEVICE=cpu         # ASR on CPU
DIARIZATION_DEVICE=mps      # Diarization on MPS
```

### Option 2: Environment Variable

```bash
# One-time override
export DEVICE_OVERRIDE=cpu
./run_pipeline.sh --job my-job --stages all
```

### Priority Order

1. **Stage-specific** env var (highest): `WHISPERX_DEVICE`
2. **Global override** env var: `DEVICE_OVERRIDE`
3. **Config file** setting: `DEVICE=`
4. **Auto-detected** by bootstrap (default)

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
✓ Hardware detection complete
  Hardware cache saved (valid for 1 hour)
  → Auto-detected device: mps
  → DEVICE_OVERRIDE=mps
  → Recommended batch size: 16
  → Set ASR_BATCH_SIZE=16 in config/.env.pipeline if needed
  → Override any auto-detected setting in config/.env.pipeline

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
✓ Hardware detection complete
  Hardware cache saved (valid for 1 hour)
  → Auto-detected device: cuda
  → DEVICE_OVERRIDE=cuda
  → Recommended batch size: 32
  → Set ASR_BATCH_SIZE=32 in config/.env.pipeline if needed
  → Override any auto-detected setting in config/.env.pipeline
```

### CPU Only

```bash
$ ./scripts/bootstrap.sh

════════════════════════════════════════════════════════════
 HARDWARE DETECTION & CACHING
════════════════════════════════════════════════════════════
Detecting hardware capabilities...
✓ Hardware detection complete
  Hardware cache saved (valid for 1 hour)
  → Auto-detected device: cpu
  → DEVICE_OVERRIDE=cpu
  → Recommended batch size: 1
  → Set ASR_BATCH_SIZE=1 in config/.env.pipeline if needed
  → Override any auto-detected setting in config/.env.pipeline
```

---

## Verification

### Check Auto-Detected Settings

```bash
# View hardware cache
cat out/hardware_cache.json | python3 -m json.tool

# Check environment
echo $DEVICE_OVERRIDE

# View recommended settings
python3 -c "
import json
with open('out/hardware_cache.json') as f:
    hw = json.load(f)
settings = hw.get('recommended_settings', {})
print(f\"Device: {hw.get('gpu_type')}\")
print(f\"Batch Size: {settings.get('batch_size')}\")
print(f\"Model: {settings.get('whisper_model')}\")
"
```

### Check Pipeline Usage

```bash
# Run ASR and check logs
./run_pipeline.sh --job test --stages asr

# Verify device used
grep "device.*mps\|cuda\|cpu" out/*/logs/07_asr*.log

# Verify batch size
grep "batch.*size" out/*/logs/07_asr*.log

# Verify MPS optimization
grep "MPS optimization" out/*/logs/07_asr*.log
```

---

## Summary

### ✅ YES - Bootstrap Auto-Detects and Configures!

**What's Auto-Detected**:
- ✅ Hardware type (MPS/CUDA/CPU)
- ✅ GPU memory
- ✅ Optimal device
- ✅ Recommended batch size
- ✅ MPS environment vars (macOS)

**What's Auto-Configured**:
- ✅ `DEVICE_OVERRIDE` exported
- ✅ MPS stability env vars set
- ✅ Batch size recommendation logged
- ✅ All ML stages use detected settings

**What's User-Controllable**:
- ✅ Override in config/.env.pipeline
- ✅ Override with env vars
- ✅ Stage-specific overrides
- ✅ Clear logging of all settings

**Integration with Documents**:
- ✅ MPS_STABILITY_IMPLEMENTATION.md - Environment setup implemented
- ✅ MPS_IMPLEMENTATION_STATUS.md - Auto-detection working
- ✅ BIAS_IMPLEMENTATION_STRATEGY.md - Device-aware bias prompting
- ✅ MPS_IMPLEMENTATION_COMPLETE.md - Full optimization active

---

**Result**: The pipeline automatically adapts to your hardware for optimal performance!
