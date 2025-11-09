# Bootstrap Guide

**Complete guide to environment setup and hardware detection**

---

## Overview

The bootstrap script (`bootstrap.sh` / `bootstrap.ps1`) is a **one-time setup** that prepares your system for running the CP-WhisperX-App pipeline. It handles all environment configuration, dependency installation, and hardware detection automatically.

---

## What Bootstrap Does

### 1. Virtual Environment Setup
- Creates isolated Python environment (`.bollyenv`)
- Installs specific Python package versions
- Prevents conflicts with system Python
- Makes environment portable and reproducible

### 2. Dependency Installation
- Installs PyTorch with platform-specific optimizations
- Installs WhisperX and all ML libraries
- Installs FFmpeg for audio processing
- Installs spaCy NER models
- Total installation size: ~5-8GB

### 3. Hardware Detection
- Detects CPU cores and threads
- Detects available RAM
- Detects GPU (MPS, CUDA, or none)
- Measures GPU memory (if available)
- Calculates optimal settings
- Caches results for 1 hour

### 4. Cache Directory Setup
- Creates `.cache/torch` for PyTorch models
- Creates `.cache/huggingface` for HF models
- Sets `TORCH_HOME` environment variable
- Sets `HF_HOME` environment variable
- Ensures proper permissions

### 5. Model Pre-Download (Optional)
- Pre-downloads Whisper models
- Pre-downloads PyAnnote models
- Pre-downloads spaCy models
- Saves time on first pipeline run

---

## Running Bootstrap

### macOS / Linux

```bash
# From project root
./scripts/bootstrap.sh

# Expected duration: 10-20 minutes
# (Depends on internet speed and disk performance)
```

### Windows

```powershell
# From project root
.\scripts\bootstrap.ps1

# Expected duration: 10-20 minutes
```

---

## Bootstrap Output Explained

### Phase 1: Python Environment
```
✓ Python 3.11.13 detected
✓ Creating virtual environment in .bollyenv
✓ Activating virtual environment
✓ Upgrading pip, setuptools, and wheel
```

### Phase 2: Dependencies
```
✓ Using optimized requirements: requirements-macos-pinned.txt
✓ Installing PyTorch 2.5.1 with MPS support
✓ Installing WhisperX 3.1.5
✓ Installing PyAnnote Audio 3.3.2
✓ Installing spaCy 3.7.6
...
✓ All dependencies installed successfully
```

### Phase 3: Hardware Detection
```
✓ Detecting hardware capabilities...
  CPU: 10 cores (10 threads)
  RAM: 16.0 GB
  GPU: Apple M1 Pro (MPS)
  GPU Memory: 10.0 GB
  
✓ Performance profile: high-quality-bollywood
✓ Recommended settings:
  - Model: large-v3
  - Batch size: 2
  - Compute type: float16
  - Device: mps
  
✓ Hardware cache saved: out/hardware_cache.json
```

### Phase 4: Cache Setup
```
✓ Setting up model cache directories
  TORCH_HOME: /path/to/project/.cache/torch
  HF_HOME: /path/to/project/.cache/huggingface
✓ Cache directories created
```

### Phase 5: Model Download (Optional)
```
✓ Pre-downloading models (this may take a while)...
  → Whisper large-v3 model (2.9 GB)
  → PyAnnote VAD model (0.5 GB)
  → PyAnnote diarization model (0.8 GB)
  → spaCy en_core_web_trf (0.6 GB)
✓ Models cached successfully
```

---

## Hardware Detection Details

### What Gets Detected

```json
{
  "detected_at": "2025-11-08T15:43:28Z",
  "platform": "Darwin",
  "cpu_cores": 10,
  "cpu_threads": 10,
  "cpu_brand": "arm",
  "memory_gb": 16.0,
  "gpu_available": true,
  "gpu_type": "mps",
  "gpu_name": "Apple M1 Pro",
  "gpu_memory_gb": 10.0,
  "recommended_settings": {
    "whisper_model": "large-v3",
    "batch_size": 2,
    "compute_type": "float16",
    "performance_profile": "high-quality-bollywood"
  }
}
```

### Performance Profiles

**high-quality-bollywood** (GPU with 8GB+ VRAM)
- Model: `large-v3`
- Batch size: 2-4
- Compute type: `float16`
- Max speakers: 15
- Estimated speedup: 12-15x vs CPU

**balanced** (GPU with 4-8GB VRAM)
- Model: `large-v2`
- Batch size: 1-2
- Compute type: `float16`
- Max speakers: 10
- Estimated speedup: 8-10x vs CPU

**cpu-optimized** (No GPU)
- Model: `base` or `small`
- Batch size: 1
- Compute type: `int8`
- Max speakers: 5
- Processing time: Slow (real-time or slower)

### Cache Validity

Hardware cache (`out/hardware_cache.json`) is valid for **1 hour**. After that:
- Bootstrap automatically refreshes it
- Prepare-job checks and updates if stale
- Ensures settings match current hardware

---

## Platform-Specific Notes

### macOS (Apple Silicon)

**Optimizations:**
- Uses MPS (Metal Performance Shaders) for GPU
- Optimized PyTorch builds for M1/M2/M3
- Native ARM64 binaries (faster)
- Pinned dependencies for stability

**Caveats:**
- Some models not fully optimized for MPS yet
- Fallback to CPU for unsupported operations
- First run may be slower (JIT compilation)

**Requirements:**
- macOS 12.3+ (for MPS support)
- Xcode Command Line Tools
- 16GB+ RAM recommended

### Windows (NVIDIA / CPU)

**Optimizations:**
- CUDA support if NVIDIA GPU detected
- cuDNN acceleration for neural networks
- Native Windows paths and permissions

**Caveats:**
- CUDA requires NVIDIA GPU with compute capability 6.1+
- CUDA Toolkit 11.8+ must be installed separately
- Windows Defender may slow initial install

**Requirements:**
- Windows 10/11 (64-bit)
- NVIDIA GPU (optional, recommended)
- Visual C++ Redistributables

### Linux (Docker / Native)

**Optimizations:**
- Docker containers for isolation
- CUDA support in GPU containers
- Native builds also supported

**Caveats:**
- Docker mode is default (not native)
- Requires Docker and docker-compose
- GPU pass-through needs nvidia-docker

**Requirements:**
- Ubuntu 20.04+ or equivalent
- Docker 20.10+ (for Docker mode)
- NVIDIA Container Toolkit (for GPU)

---

## Troubleshooting Bootstrap

### Python Version Issues

```bash
# Check Python version
python3 --version

# Should be 3.11.0 or higher
# If not, install Python 3.11+

# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv

# Windows
# Download from python.org
```

### Virtual Environment Fails

```bash
# Error: "No module named 'venv'"
# Solution: Install python3-venv

# Ubuntu/Debian
sudo apt install python3.11-venv

# macOS (usually included)
# Windows (usually included)
```

### Dependency Installation Fails

```bash
# Error: "Failed building wheel for X"
# Solution: Install build tools

# macOS
xcode-select --install

# Ubuntu/Debian
sudo apt install build-essential python3-dev

# Windows
# Install Visual Studio Build Tools
```

### Hardware Detection Shows Wrong GPU

```bash
# Check actual GPU
# macOS
system_profiler SPDisplaysDataType | grep Chipset

# Linux
lspci | grep -i vga

# Windows
wmic path win32_VideoController get name

# If detection is wrong:
rm out/hardware_cache.json
./scripts/bootstrap.sh
```

### Permission Errors

```bash
# Fix permissions on cache directories
chmod 755 .cache/
chmod 755 .cache/torch
chmod 755 .cache/huggingface

# Fix permissions on output directory
chmod 755 out/

# Fix permissions on bootstrap script
chmod +x scripts/bootstrap.sh
```

### Network/Download Issues

```bash
# Error: "Failed to download X"
# Solutions:

# 1. Check internet connection
ping google.com

# 2. Use different mirror (PyPI)
pip install --index-url https://pypi.org/simple/ package-name

# 3. Download models manually
# See Model Download section below
```

### Disk Space Issues

```bash
# Check available space
df -h .

# Bootstrap needs:
# - 5-8 GB for dependencies
# - 5-10 GB for models (optional)
# - Total: ~15 GB minimum

# Clean up if needed
rm -rf .bollyenv
rm -rf .cache/
```

---

## Manual Model Download

If automatic download fails, download models manually:

### Whisper Models

```bash
# Activate environment
source .bollyenv/bin/activate  # macOS/Linux
.bollyenv\Scripts\activate     # Windows

# Download specific model
python -c "import whisperx; whisperx.load_model('large-v3', device='cpu', download_root='.cache/torch')"
```

### PyAnnote Models

```bash
# Set HF token
export HF_TOKEN="your-token-here"

# Download VAD model
python -c "from pyannote.audio import Pipeline; Pipeline.from_pretrained('pyannote/voice-activity-detection', use_auth_token='$HF_TOKEN', cache_dir='.cache/huggingface')"

# Download diarization model
python -c "from pyannote.audio import Pipeline; Pipeline.from_pretrained('pyannote/speaker-diarization-3.1', use_auth_token='$HF_TOKEN', cache_dir='.cache/huggingface')"
```

### spaCy Models

```bash
# Download English NER model
python -m spacy download en_core_web_trf

# Or download manually
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_trf-3.7.3/en_core_web_trf-3.7.3-py3-none-any.whl
```

---

## Re-running Bootstrap

Bootstrap is safe to run multiple times:

```bash
# Full clean reinstall
rm -rf .bollyenv
rm -rf .cache/
rm out/hardware_cache.json
./scripts/bootstrap.sh

# Update dependencies only
source .bollyenv/bin/activate
pip install -U -r requirements.txt

# Refresh hardware detection only
rm out/hardware_cache.json
python shared/hardware_detection.py --no-cache
```

---

## Verifying Bootstrap Success

### Check Virtual Environment

```bash
# Activate environment
source .bollyenv/bin/activate  # macOS/Linux
.bollyenv\Scripts\activate     # Windows

# Verify Python
which python3
# Should show: /path/to/project/.bollyenv/bin/python3

# Check installed packages
pip list | grep -i whisper
pip list | grep -i pyannote
pip list | grep -i torch
```

### Check Hardware Detection

```bash
# View hardware cache
cat out/hardware_cache.json

# Should show:
# - Your CPU info
# - Your RAM amount
# - Your GPU (if available)
# - Recommended settings
```

### Check Cache Directories

```bash
# Verify directories exist
ls -la .cache/
# Should show: torch/ and huggingface/

# Check permissions
ls -ld .cache/torch .cache/huggingface
# Should be readable/writable
```

### Test PyTorch

```bash
source .bollyenv/bin/activate

python3 << 'EOF'
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"MPS available: {torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False}")
EOF

# Should show your PyTorch version and GPU availability
```

---

## Next Steps After Bootstrap

1. **Configure API Keys**: Create `config/secrets.json`
2. **Prepare First Job**: Run `./prepare-job.sh in/movie.mp4`
3. **Run Pipeline**: Run `./run_pipeline.sh --job JOB_ID`

See [Quick Start Guide](QUICKSTART.md) for complete walkthrough.

---

## Bootstrap Architecture

```
bootstrap.sh/ps1
    ↓
1. Create .bollyenv (venv)
    ↓
2. Install dependencies
    ↓
3. Detect hardware → out/hardware_cache.json
    ↓
4. Create cache dirs
    ├── .cache/torch (TORCH_HOME)
    └── .cache/huggingface (HF_HOME)
    ↓
5. Pre-download models (optional)
    ↓
✓ Ready to prepare jobs
```

---

## Related Documentation

- [Quick Start Guide](QUICKSTART.md) - Get running quickly
- [Architecture Overview](ARCHITECTURE.md) - System design
- [Configuration Guide](CONFIGURATION.md) - Settings and options
- [Troubleshooting](TROUBLESHOOTING.md) - Fix common issues

---

Return to [Documentation Index](INDEX.md)
