# Hardware Optimization in prepare-job.py

**Last Updated:** November 4, 2025

## Overview

The `prepare-job.py` script now includes automatic hardware detection and optimization to ensure pipeline jobs are configured optimally for the available system resources.

## Features

### Automatic Hardware Detection

When preparing a job, the script automatically detects:

- **CPU:** Number of cores and threads
- **Memory:** Total RAM available
- **GPU:** Type (CUDA/MPS), model name, and VRAM
- **Device Type:** cuda, mps, or cpu

### Intelligent Parameter Optimization

Based on detected hardware, the script automatically tunes:

1. **Whisper Model Selection**
   - Large models for high-end systems
   - Medium/base models for limited resources
   - Prevents OOM (Out of Memory) errors

2. **Batch Size**
   - Larger batches for systems with more memory/VRAM
   - Conservative batches for limited resources
   - Optimized for throughput vs stability

3. **Compute Type**
   - FP16 for CUDA (faster)
   - FP32 for MPS (compatibility)
   - INT8 for CPU (efficiency)

4. **Chunk Length**
   - Larger chunks for high-memory systems
   - Smaller chunks to avoid OOM on limited systems

5. **Max Speakers**
   - More speakers for powerful systems
   - Fewer speakers for resource-constrained systems

6. **Docker Fallback**
   - Enables CPU fallback for GPU systems
   - Pure CPU mode for CPU-only systems

---

## Hardware Detection Logic

### GPU Detection

```python
detect_hardware_capabilities() 
├── Check for CUDA
│   ├── Available → gpu_type='cuda', get VRAM
│   └── Not available → Check MPS
├── Check for MPS (Apple Silicon)
│   ├── Available → gpu_type='mps', estimate memory
│   └── Not available → gpu_type='cpu'
└── Gather CPU/Memory info
```

### Optimization Decisions

#### Model Selection

| GPU VRAM | Memory | Recommended Model | Reason |
|----------|--------|-------------------|--------|
| ≥10 GB | - | large-v3 | Can handle largest model |
| ≥6 GB | - | medium | Good balance |
| <6 GB | - | base | Limited VRAM |
| None | ≥16 GB | medium | CPU with good RAM |
| None | ≥8 GB | base | Limited RAM |
| None | <8 GB | tiny | Very limited |

#### Batch Size

| Condition | Batch Size | Reason |
|-----------|------------|--------|
| GPU ≥12 GB VRAM | 32 | High VRAM |
| GPU ≥8 GB VRAM | 16 | Moderate VRAM |
| GPU <8 GB VRAM | 8 | Limited VRAM |
| CPU ≥32 GB RAM | 16 | High RAM |
| CPU ≥16 GB RAM | 8 | Moderate RAM |
| CPU <16 GB RAM | 4 | Limited RAM |

#### Compute Type

| Device | Compute Type | Reason |
|--------|--------------|--------|
| CUDA | float16 | FP16 support, faster |
| MPS | float32 | Limited FP16 support |
| CPU | int8 | Quantization efficiency |

#### Chunk Length

| Memory | Chunk Length | Reason |
|--------|--------------|--------|
| ≥32 GB | 30s | Optimal for quality |
| ≥16 GB | 20s | Reduced for stability |
| <16 GB | 10s | Prevent OOM |

---

## Job Configuration File

### Example Output with Comments

The generated `.<job-id>.env` file includes detailed hardware information and optimization decisions:

```bash
# ============================================================================
# CP-WhisperX-App Job Configuration
# Generated: 2025-11-04T02:45:00.000000
# Job ID: 20251104-0001
# ============================================================================

# ============================================================================
# HARDWARE DETECTION & OPTIMIZATION
# ============================================================================
# CPU: 8 cores (16 threads)
# Memory: 32.0 GB RAM
# GPU: NVIDIA GeForce RTX 3080
# GPU Memory: 10.0 GB
# GPU Type: CUDA
#
# RECOMMENDATION: GPU acceleration available
# Docker: Use cuda images with CPU fallback enabled
# ============================================================================

# Hardware-optimized model selection
# GPU has 10.0GB VRAM - can handle large-v3
WHISPER_MODEL=large-v3

# Batch size optimized for available resources
# High VRAM available
BATCH_SIZE=32

# Compute type optimized for device
# CUDA supports FP16 for faster computation
COMPUTE_TYPE=float16

# Chunk length tuned for memory constraints
# High memory - optimal chunk size
CHUNK_LENGTH=30

# Max speakers based on resource availability
# Sufficient resources for complex scenes
MAX_SPEAKERS=10

# GPU fallback enabled for reliability
USE_GPU_FALLBACK=true

# ============================================================================
# RESOURCE MONITORING RECOMMENDATIONS
# ============================================================================
# Monitor GPU memory with: nvidia-smi
# CPU fallback will activate automatically if GPU fails
```

### Low-Resource System Example

```bash
# ============================================================================
# HARDWARE DETECTION & OPTIMIZATION
# ============================================================================
# CPU: 4 cores (4 threads)
# Memory: 8.0 GB RAM
# GPU: Not available
#
# RECOMMENDATION: CPU-only execution
# Docker: Use CPU images only
# WARNING: Processing will be slower without GPU
# ============================================================================

# Hardware-optimized model selection
# System has 8.0GB RAM - base model recommended
WHISPER_MODEL=base

# Batch size optimized for available resources
# Moderate RAM available
BATCH_SIZE=8

# Compute type optimized for device
# CPU benefits from INT8 quantization
COMPUTE_TYPE=int8

# Chunk length tuned for memory constraints
# Moderate memory - reduced chunk size
CHUNK_LENGTH=20

# Max speakers based on resource availability
# Limited resources - reduce diarization complexity
MAX_SPEAKERS=5

# ============================================================================
# RESOURCE MONITORING RECOMMENDATIONS
# ============================================================================
# WARNING: Low memory detected
# - Monitor memory usage during processing
# - Consider processing in smaller chunks
# - Use smaller Whisper model if OOM occurs
#
# CPU-ONLY EXECUTION:
# - Processing will be significantly slower (10-25x)
# - Consider using GPU-enabled system for large files
# - Estimated processing time: base model on CPU
```

---

## Job Definition (job.json)

Hardware information is also saved to `job.json`:

```json
{
  "job_id": "20251104-0001",
  "created_at": "2025-11-04T02:45:00.000000",
  "hardware": {
    "cpu_cores": 8,
    "memory_gb": 32.0,
    "gpu_type": "cuda",
    "gpu_name": "NVIDIA GeForce RTX 3080",
    "optimized_settings": {
      "whisper_model": "large-v3",
      "whisper_model_reason": "GPU has 10.0GB VRAM - can handle large-v3",
      "batch_size": 32,
      "batch_size_reason": "High VRAM available",
      "compute_type": "float16",
      "compute_type_reason": "CUDA supports FP16 for faster computation",
      "chunk_length_s": 30,
      "chunk_length_reason": "High memory - optimal chunk size",
      "max_speakers": 10,
      "max_speakers_reason": "Sufficient resources for complex scenes",
      "use_docker_cpu_fallback": true,
      "docker_recommendation": "Use cuda images with CPU fallback enabled"
    }
  }
}
```

---

## Usage

### Basic Usage (Automatic Optimization)

```bash
# Hardware detection and optimization happens automatically
python prepare-job.py in/movie.mp4
```

**Output:**
```
[INFO] Detecting hardware capabilities...
[INFO] CPU: 8 cores, 16 threads
[INFO] Memory: 32.0 GB
[INFO] GPU: NVIDIA GeForce RTX 3080 (CUDA)
[INFO] GPU Memory: 10.0 GB
[INFO] Applying hardware-optimized settings...
[INFO] Recommended model: large-v3
[INFO] Batch size: 32
[INFO] Compute type: float16
[INFO] Configuration saved with optimization comments
```

### With Native Mode

```bash
# Enable native GPU acceleration
python prepare-job.py in/movie.mp4 --native
```

Automatically sets device to detected GPU type (cuda/mps/cpu).

### Transcribe-Only Workflow

```bash
# Simplified workflow with hardware optimization
python prepare-job.py in/movie.mp4 --transcribe
```

Still applies hardware optimization but skips diarization/subtitles.

---

## Benefits

### 1. Prevents Pipeline Failures

- **OOM Prevention:** Automatically reduces parameters for limited systems
- **Resource Matching:** Ensures settings match hardware capabilities
- **Stability:** Conservative defaults for edge cases

### 2. Optimal Performance

- **GPU Utilization:** Maximizes throughput on high-end systems
- **CPU Efficiency:** Optimizes for CPU-only execution
- **Memory Management:** Balances quality vs stability

### 3. Transparency

- **Clear Documentation:** All decisions explained in comments
- **Reasoning Visible:** Users understand why settings were chosen
- **Easy Adjustment:** Can override if needed

### 4. Platform Agnostic

- Works on Linux, macOS, Windows
- Supports CUDA, MPS, and CPU
- Handles Docker and native execution

---

## Hardware Requirements

### Minimum (Tiny Model)

- **CPU:** 2 cores
- **Memory:** 4 GB RAM
- **GPU:** None (CPU-only)
- **Processing:** Very slow (tiny model)

### Recommended (Base Model)

- **CPU:** 4 cores
- **Memory:** 8 GB RAM
- **GPU:** Optional (significantly faster with GPU)
- **Processing:** Moderate speed

### Optimal (Large Model)

- **CPU:** 8+ cores
- **Memory:** 16+ GB RAM
- **GPU:** NVIDIA GPU with 10+ GB VRAM (or Apple Silicon M1/M2 Max)
- **Processing:** Fast with high quality

---

## Troubleshooting

### Issue: Job still fails with OOM

**Solution:** Override settings in job's `.env` file:
```bash
# Reduce model size
WHISPER_MODEL=base

# Reduce batch size
BATCH_SIZE=4

# Reduce chunk length
CHUNK_LENGTH=10
```

### Issue: GPU not detected

**Check:**
1. PyTorch installed with GPU support
2. CUDA drivers installed (NVIDIA)
3. Run: `python -c "import torch; print(torch.cuda.is_available())"`

### Issue: Optimization too conservative

**Override:** Edit generated `.env` file before running pipeline:
```bash
# Increase batch size if you have more VRAM
BATCH_SIZE=64

# Use larger model if confident
WHISPER_MODEL=large-v3
```

### Issue: Want to disable optimization

**Workaround:** Manually edit `config/.env.pipeline` template to set fixed values. The script will still detect hardware but use your template values.

---

## Dependencies

The hardware detection requires:

```python
import psutil        # For CPU/memory detection
import torch         # For GPU detection
```

**Install:**
```bash
pip install psutil torch
```

---

## Related Documentation

- [prepare-job.py](../prepare-job.py) - Source code
- [CUDA_ACCELERATION_GUIDE.md](../CUDA_ACCELERATION_GUIDE.md) - GPU performance
- [GPU_FALLBACK_GUIDE.md](../GPU_FALLBACK_GUIDE.md) - Automatic fallback
- [DEVICE_SELECTION_GUIDE.md](../DEVICE_SELECTION_GUIDE.md) - Device selection

---

## Future Enhancements

- [ ] Dynamic adjustment during pipeline execution
- [ ] Learning from past runs
- [ ] Cloud GPU resource estimation
- [ ] Cost optimization suggestions
- [ ] Performance profiling integration

---

**Hardware optimization makes pipeline execution more reliable and efficient!** 🚀
