# Native Mode Guide

## Overview

**Native Mode** is the fastest execution mode for CP-WhisperX-App, running the pipeline directly on your host system with full GPU acceleration. Unlike Docker mode, native mode:

- **Fastest performance** - No containerization overhead
- **Direct GPU access** - Full CUDA/MPS utilization
- **Local development** - Best for active development
- **Single environment** - Unified Python virtual environment
- **Easier debugging** - Direct access to Python debugger

## What Native Mode Does

Native mode sets up and runs the complete transcription/subtitle generation pipeline directly on your machine:

1. **Creates Python virtual environment** (`.bollyenv`)
2. **Installs all dependencies** for all pipeline stages
3. **Detects hardware acceleration** (CUDA, MPS, or CPU)
4. **Runs pipeline stages** natively without containers
5. **Provides debugging capabilities** with breakpoints and inspectors

## Quick Start

### Windows

```powershell
# Bootstrap (first time only)
.\scripts\bootstrap.ps1

# Prepare a job
python prepare-job.py input.mkv

# Run pipeline
python pipeline.py
```

### Linux/macOS

```bash
# Bootstrap (first time only)
./scripts/bootstrap.sh

# Prepare a job
python prepare-job.py input.mkv

# Run pipeline
python pipeline.py
```

## Bootstrap Process

The bootstrap script (`scripts/bootstrap.ps1` or `scripts/bootstrap.sh`) performs the following:

### 1. Python Detection
- Searches for Python 3.11+ (`python3` or `python`)
- Validates version compatibility
- Displays warnings if version < 3.11

### 2. Virtual Environment Setup
- Creates `.bollyenv` directory
- Isolates dependencies from system Python
- Updates pip and wheel to latest versions

### 3. Dependency Installation
- Installs from `requirements.txt`
- Downloads ML models on first run
- Configures PyTorch for available hardware

### 4. Hardware Detection
- **CUDA**: Tests NVIDIA GPU availability and CUDA version
- **MPS**: Tests Apple Silicon Metal Performance Shaders (macOS M1/M2/M3)
- **CPU**: Falls back to CPU if no GPU detected

### 5. First-Run Setup
- Downloads Whisper models (~1-3GB depending on size)
- Downloads spaCy language models
- Caches pyannote.audio models (requires HuggingFace token)

## Native Mode vs Docker Mode

| Feature | Native Mode | Docker Mode |
|---------|-------------|-------------|
| **Performance** | ⚡⚡⚡⚡⚡ (fastest) | ⚡⚡⚡⚡ (fast) |
| **Setup Time** | 10-15 minutes | 30-60 minutes |
| **GPU Access** | Direct | Through Docker |
| **Debugging** | Full Python debugger | Limited |
| **Disk Space** | ~5GB | ~20GB |
| **Isolation** | Virtual environment | Full container isolation |
| **Best For** | Development, Production | CI/CD, Reproducibility |
| **Stage Switching** | Instant | Container startup |

## Hardware-Specific Configuration

### CUDA (NVIDIA GPU)

**Requirements:**
- NVIDIA GPU with CUDA Compute Capability 7.0+ (RTX 20xx or newer)
- CUDA 11.8+ or CUDA 12.x
- 6GB+ VRAM recommended (4GB minimum)

**Setup:**
```powershell
# Windows
# Install CUDA Toolkit from NVIDIA
# Install cuDNN
.\scripts\bootstrap.ps1

# Verify
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}')"
```

**Environment Variables:**
```bash
DEVICE=cuda
COMPUTE_TYPE=float16  # Use float16 for faster inference
CUDA_VISIBLE_DEVICES=0  # Select specific GPU
```

### MPS (Apple Silicon)

**Requirements:**
- Apple M1, M1 Pro, M1 Max, M2, M2 Pro, M2 Max, M3, or newer
- macOS 12.3+ (Monterey or later)
- Xcode Command Line Tools

**Setup:**
```bash
# macOS
./scripts/bootstrap.sh

# Verify
python -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"
```

**Environment Variables:**
```bash
DEVICE=mps
PYTORCH_ENABLE_MPS_FALLBACK=1  # Enable CPU fallback for unsupported ops
```

### CPU Fallback

**Any System:**
```bash
# Automatically detected if no GPU available
DEVICE=cpu
COMPUTE_TYPE=float32  # Use float32 for CPU
```

**Performance:** Expect 3-5x slower than GPU for a 2-hour movie.

## Pipeline Execution

### Full Pipeline (Subtitle Generation)

```bash
# Prepare job
python prepare-job.py movie.mkv --tmdb-id 12345

# Run full pipeline with all stages
python pipeline.py

# For Bollywood content (recommended)
python pipeline.py --enable-second-pass --enable-lyrics-detection
```

### Transcribe Only (Faster)

```bash
# Prepare job
python prepare-job.py movie.mkv --transcribe-only

# Run transcription workflow
python pipeline.py --workflow transcribe
```

### Resume After Failure

```bash
# Pipeline automatically resumes from last successful stage
python pipeline.py

# Or use resume script
.\resume-pipeline.ps1   # Windows
./resume-pipeline.sh    # Linux/macOS
```

### Run Specific Stages

```bash
# Run only diarization and ASR stages
python pipeline.py --stages diarization,asr

# Skip stages
python pipeline.py --skip-stages tmdb,ner
```

## Debugging Native Mode

### Debug Mode

Native mode provides powerful debugging capabilities:

```bash
# Set breakpoints in stage scripts
# native/scripts/07_asr.py

import pdb; pdb.set_trace()  # Add breakpoint

# Run with Python debugger
python -m pdb pipeline.py
```

### Debug Scripts

**ASR Debug Mode:**
```powershell
# Windows
.\native\run_asr_debug.ps1

# Linux/macOS
./native/run_asr_debug.sh
```

**Pipeline Debug:**
```powershell
# Windows
.\native\pipeline_debug_asr.ps1

# Linux/macOS
./native/pipeline_debug_asr.sh
```

### Logging

Native mode logs are saved to:
```
logs/YYYYMMDD-HHMMSS-scriptname.log
```

Set log level:
```bash
# Windows
$env:LOG_LEVEL="DEBUG"

# Linux/macOS
export LOG_LEVEL=DEBUG
```

See [Logging Locations](guides/developer/logging-locations.md) for details.

## Advanced Configuration

### Multiple Virtual Environments

For stage-specific dependencies:

```powershell
# Windows
.\native\setup_venvs.ps1

# Linux/macOS
./native/setup_venvs.sh
```

Creates separate venvs:
- `.bollyenv-demux`
- `.bollyenv-vad`
- `.bollyenv-diarization`
- `.bollyenv-asr`
- etc.

### Custom Models

```bash
# Use specific Whisper model
export WHISPER_MODEL=large-v3

# Use custom model path
export WHISPER_MODEL_DIR=/path/to/models

# PyAnnote speaker diarization model
export PYANNOTE_MODEL=pyannote/speaker-diarization-3.1
```

### Memory Configuration

```bash
# Limit batch size for low VRAM
export BATCH_SIZE=8

# Adjust chunk length for ASR
export CHUNK_LENGTH=30

# VAD sensitivity
export VAD_ONSET=0.5
export VAD_OFFSET=0.363
```

## Troubleshooting

### CUDA Not Detected

```powershell
# Check CUDA installation
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(torch.version.cuda)"

# Reinstall PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### MPS Fallback Issues

```bash
# Enable fallback
export PYTORCH_ENABLE_MPS_FALLBACK=1

# Test MPS
python -c "import torch; print(torch.backends.mps.is_built())"
```

### Out of Memory

```bash
# Reduce batch size
export BATCH_SIZE=4

# Use smaller model
export WHISPER_MODEL=medium

# Enable gradient checkpointing
export GRADIENT_CHECKPOINTING=true
```

### Module Not Found

```bash
# Activate virtual environment
# Windows
.\.bollyenv\Scripts\Activate.ps1

# Linux/macOS
source .bollyenv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### HuggingFace Access Token

PyAnnote models require authentication:

```bash
# Set token
export HF_TOKEN=hf_your_token_here

# Or create .env file
echo "HF_TOKEN=hf_your_token_here" > .env

# Accept model license at:
# https://huggingface.co/pyannote/speaker-diarization-3.1
```

See [HuggingFace Gated PyAnnote](architecture/HF-gated-pynote.md) for details.

## Performance Optimization

### Best Practices

1. **Use GPU** - 5-10x faster than CPU
2. **Use float16** - 2x faster on CUDA with minimal quality loss
3. **Batch processing** - Process multiple files in sequence
4. **Model caching** - Models load once and stay in memory
5. **Stage isolation** - Run only needed stages

### Benchmarks (2-hour movie)

| Hardware | Mode | Time | Quality |
|----------|------|------|---------|
| RTX 4090 | CUDA float16 | 12 min transcribe | ⭐⭐⭐⭐⭐ |
| RTX 4090 | CUDA float16 | 45 min subtitle | ⭐⭐⭐⭐⭐ |
| RTX 4090 | CUDA float16 | 58 min Bollywood | ⭐⭐⭐⭐⭐ |
| M1 Max | MPS | 35 min transcribe | ⭐⭐⭐⭐ |
| M1 Max | MPS | 2.5 hr subtitle | ⭐⭐⭐⭐ |
| i7-12700K | CPU | 2 hr transcribe | ⭐⭐⭐⭐ |
| i7-12700K | CPU | 8 hr subtitle | ⭐⭐⭐⭐ |

## Comparison with Docker Mode

### When to Use Native Mode

✅ **Use Native Mode when:**
- Maximum performance is required
- You're actively developing/debugging
- You have a stable local Python environment
- You need quick iteration cycles
- You're processing many files locally

### When to Use Docker Mode

✅ **Use Docker Mode when:**
- Reproducibility is critical
- Running in CI/CD environments
- Deploying to cloud/server environments
- Multiple users need identical environments
- You want complete isolation from host system

## See Also

- [Quick Start Guide](guides/user/quickstart.md) - Getting started
- [Workflow Guide](guides/user/workflow-guide.md) - Pipeline workflows
- [Developer Guide](guides/developer/developer-guide.md) - Development setup
- [Debug Mode Guide](guides/developer/debug-mode.md) - Debugging techniques
- [CUDA Acceleration](guides/hardware/cuda-acceleration.md) - GPU setup
- [MPS Acceleration](guides/hardware/mps-acceleration.md) - Apple Silicon setup

---

**Native mode gives you the fastest possible performance with full control over the execution environment.**
