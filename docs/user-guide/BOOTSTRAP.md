# Bootstrap Guide

**CP-WhisperX-App** - Environment Setup & Installation

---

## Overview

The bootstrap process creates **5 isolated Python virtual environments**, each optimized for specific tasks. This multi-environment architecture prevents dependency conflicts and allows independent upgrades.

### Environments Created

| Environment | Purpose | Key Dependencies | Platform |
|-------------|---------|------------------|----------|
| `venv/common` | Core utilities | ffmpeg-python, pydantic, logging | All |
| `venv/whisperx` | ASR transcription | whisperx 3.7.4, torch 2.8.0 | All |
| `venv/mlx` | macOS acceleration | mlx-whisper | macOS only |
| `venv/indictrans2` | Indic→English, Indic→Indic | IndicTransToolkit, torch 2.5+ | All |
| `venv/nllb` | 200+ languages | transformers, NLLB model | All |

---

## Prerequisites

### 1. System Requirements

**macOS** (Apple Silicon or Intel):
```bash
# Check architecture
uname -m  # arm64 (Apple Silicon) or x86_64 (Intel)

# Python 3.11+ required
python3 --version  # Should be 3.11.x or later
```

**Linux** (Ubuntu/Debian):
```bash
# Python 3.11+
python3 --version

# Optional: CUDA for GPU acceleration
nvidia-smi  # Check for NVIDIA GPU
```

**Windows**:
```powershell
# Python 3.11+
python --version

# Optional: CUDA for GPU acceleration
nvidia-smi  # Check for NVIDIA GPU
```

### 2. FFmpeg Installation

FFmpeg is required for audio/video processing.

**macOS**:
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt update && sudo apt install -y ffmpeg
```

**Windows**:
- Download from https://ffmpeg.org/download.html
- Add to PATH environment variable

**Verify**:
```bash
ffmpeg -version
```

### 3. Disk Space

- **Minimum**: 10 GB free space
- **Recommended**: 20 GB (for model caching)
- Model downloads: ~5-8 GB (first run only)

---

## Quick Start

### macOS/Linux

```bash
# Navigate to project root
cd /path/to/cp-whisperx-app

# Run bootstrap (creates environments only)
./bootstrap.sh

# OR run with model caching (recommended for offline use)
./bootstrap.sh --cache-models

# OR run with debug output
./bootstrap.sh --debug
```

**Recommended for production:**
```bash
./bootstrap.sh --cache-models
```
This will:
1. Create all 8 environments (~10 min)
2. Pre-cache all models (~15-25 min)
3. Enable fully offline pipeline execution

### Windows (PowerShell)

```powershell
# Navigate to project root
cd C:\path\to\cp-whisperx-app

# Run bootstrap (normal mode)
.\bootstrap.ps1

# OR run with debug output
.\bootstrap.ps1 -Debug
```

**Note:** Model caching on Windows should be done separately:
```powershell
.\cache-models.sh --all
```

---

## Command Options

### macOS/Linux (`bootstrap.sh`)

```bash
./bootstrap.sh [OPTIONS]

OPTIONS:
  --debug         Enable verbose logging (shows pip install details)
  --force         Force recreate all environments (deletes existing)
  --cache-models  Pre-cache all models after setup (~20GB, 15-25 min)
  --skip-cache    Skip model caching prompt at the end
  --help          Show help message
```

**Examples:**
```bash
# Basic setup
./bootstrap.sh

# Setup with model caching (recommended)
./bootstrap.sh --cache-models

# Force recreate everything
./bootstrap.sh --force

# Recreate and cache models
./bootstrap.sh --force --cache-models

# Silent mode (no caching prompt)
./bootstrap.sh --skip-cache
```

### Windows (`bootstrap.ps1`)

```powershell
.\bootstrap.ps1 [OPTIONS]

OPTIONS:
  -Debug       Enable verbose logging (shows pip install details)
  -Force       Force recreate all environments (deletes existing)
  -Help        Show help message
```

---

## What Happens During Bootstrap

### Phase 1: Hardware Detection

```
[INFO] Platform: Darwin (arm64)
[INFO] Detected: Apple Silicon (M1/M2/M3) with MPS + MLX
```

- Detects CPU architecture (x86_64 vs arm64)
- Checks for NVIDIA GPU (CUDA support)
- Identifies Apple Silicon (MPS/MLX support)
- Sets optimal compute type based on hardware

### Phase 2: Environment Creation

For each environment:

1. **Create virtual environment**
   ```bash
   python3 -m venv .venv-<name>
   ```

2. **Upgrade pip/setuptools**
   ```bash
   pip install --upgrade pip setuptools wheel
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements-<name>.txt
   ```

4. **Verify installation**
   - Checks critical imports
   - Validates versions

### Phase 3: Model Caching (Optional but Recommended)

**New in v2.0:** Bootstrap can now pre-cache all models for offline execution.

**Interactive Prompt** (default behavior):
```
⚠️  IMPORTANT: Models will download on first pipeline run if not cached now.

Pre-caching models enables:
  ✅ Fully offline pipeline execution
  ✅ Faster job startup times
  ✅ Predictable performance

Models to cache (~20-25GB total):
  • IndicTrans2 (Indic→English) - ~2-5GB
  • NLLB-200 (200+ languages) - ~17GB
  • WhisperX Large-v3 - ~3GB
  • MLX Whisper Large-v3 - ~3GB (Apple Silicon only)

Time required: 15-25 minutes

Cache models now? [y/N]
```

**Automatic Caching:**
```bash
./bootstrap.sh --cache-models
```

**Skip Prompt:**
```bash
./bootstrap.sh --skip-cache  # Don't ask, cache later
```

**Manual Caching (after bootstrap):**
```bash
./cache-models.sh --all
```

**Models Cached:**
- **WhisperX Large-v3**: ~3 GB (transcription)
- **MLX Whisper**: ~3 GB (Apple Silicon optimized transcription)
- **IndicTrans2**: ~2-5 GB (Indic language translation)
- **NLLB-200**: ~17 GB (200+ language translation)

**Cache Location:** `.cache/huggingface/`

**Benefits:**
- ✅ **Offline execution**: No internet needed after caching
- ✅ **Fast startup**: Models pre-loaded
- ✅ **Predictable**: No unexpected download delays
- ✅ **Reliable**: Jobs won't fail due to network issues

---

## Cache Directory Structure

Bootstrap creates a centralized cache directory for all ML models and application data.

### ML Model Cache (`.cache/`)

After bootstrap, all ML models are cached locally in the project directory:

```
.cache/
├── torch/              # Whisper models, VAD models (3-5 GB per model)
├── huggingface/        # Transformer models for translation (2-10 GB)
└── mlx/                # MLX-specific models (Apple Silicon only, 1-3 GB)
```

**Benefits**:
- ✅ **Project-isolated**: No conflicts with other projects
- ✅ **Shared across environments**: All virtual environments use same cache
- ✅ **Predictable location**: Easy to backup or migrate
- ✅ **Faster subsequent runs**: Models download once, used by all workflows

**Cache Environment Variables** (set automatically):
- `TORCH_HOME=.cache/torch`
- `HF_HOME=.cache/huggingface`
- `TRANSFORMERS_CACHE=.cache/huggingface`
- `MLX_CACHE_DIR=.cache/mlx`

### Application Caches

Additional caches for metadata and translation aids:

| Cache | Location | Purpose | Size |
|-------|----------|---------|------|
| TMDB | `out/tmdb_cache/` | Movie/TV metadata | < 100 MB |
| MusicBrainz | `out/musicbrainz_cache/` | Music metadata | < 50 MB |
| Glossary | `glossary/cache/` | Translation glossaries | < 10 MB |

**Note**: Application caches have 90-day expiry and auto-refresh.

### Cache Management

**Centralized Cache Access:**
All pipeline stages automatically access cached models via `shared/environment_manager.py`. No per-stage configuration needed!

View cache status:
```bash
# macOS/Linux
./scripts/cache-manager.sh status

# Windows
.\scripts\cache-manager.ps1 -Action status
```

**Verify cache configuration:**
```bash
# Check cache paths
cat config/hardware_cache.json | grep -A 10 '"cache"'

# List cached models
ls -lh .cache/huggingface/hub/ | grep "models--"

# Check total size
du -sh .cache/huggingface/
```

**Test offline execution:**
```bash
# Turn off Wi-Fi/network
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>
# Should work if models are cached! ✅
```

Clear model caches (will re-download on next use):
```bash
# macOS/Linux
./scripts/cache-manager.sh clear-models

# Windows
.\scripts\cache-manager.ps1 -Action clear-models
```

Clear application caches:
```bash
# macOS/Linux
./scripts/cache-manager.sh clear-app

# Windows
.\scripts\cache-manager.ps1 -Action clear-app
```

**Tip**: The `.cache/` directory is in `.gitignore` and safe to delete anytime to free disk space. Models will automatically re-download on next pipeline run.

**📚 See also:** [Cache Verification Guide](../setup/CACHE_VERIFICATION.md) - Detailed verification that all stages access the cache correctly.

---

## Environment Details

### venv/common (Core Utilities)

**Purpose**: Job management, logging, FFmpeg wrappers, configuration

**Key Packages**:
- `ffmpeg-python` - Audio/video processing
- `pydantic` - Configuration validation
- `python-json-logger` - Structured logging

**Size**: ~50 MB  
**Install Time**: ~30 seconds

---

### venv/whisperx (ASR)

**Purpose**: Automatic speech recognition with word-level timestamps

**Key Packages**:
- `whisperx==3.7.4` - ASR engine
- `torch~=2.8.0` - PyTorch framework
- `faster-whisper>=1.1.1` - CTranslate2 backend

**Size**: ~3.5 GB  
**Install Time**: 2-5 minutes

**Hardware Support**:
- ✅ CPU (all platforms)
- ✅ CUDA (NVIDIA GPUs)
- ✅ MPS (Apple Silicon/Intel Mac)

---

### venv/mlx (macOS Acceleration)

**Purpose**: Ultra-fast ASR on Apple Silicon using MLX

**Key Packages**:
- `mlx-whisper` - MLX-optimized Whisper
- `mlx>=0.28.0` - Apple's ML framework

**Size**: ~800 MB  
**Install Time**: 1-2 minutes  
**Platform**: **macOS only** (M1/M2/M3 chips)

**Note**: Windows/Linux skip this environment automatically.

---

### venv/indictrans2 (Indic Translation)

**Purpose**: High-quality translation for 22 Indian languages

**Key Packages**:
- `IndicTransToolkit>=1.0.0` - Translation toolkit
- `torch>=2.5.0` - PyTorch (newer version)
- `transformers>=4.51.0` - Hugging Face models

**Size**: ~2.5 GB  
**Install Time**: 2-4 minutes

**Models** (auto-downloaded on first use):
- `ai4bharat/indictrans2-en-indic-1B` - Indic→English
- `ai4bharat/indictrans2-indic-indic-1B` - Indic→Indic

---

### venv/nllb (Universal Translation)

**Purpose**: Translation for 200+ non-Indic languages

**Key Packages**:
- `transformers>=4.51.0` - Hugging Face models
- `torch>=2.5.0` - PyTorch
- `sentencepiece>=0.2.0` - Tokenization

**Size**: ~2 GB  
**Install Time**: 2-4 minutes

**Model** (auto-downloaded on first use):
- `facebook/nllb-200-distilled-600M` - 200+ language translation

---

## Troubleshooting

### Issue: "Command not found: python3"

**Solution**:
```bash
# macOS/Linux
which python3
brew install python@3.11  # macOS
sudo apt install python3.11  # Linux

# Windows
python --version  # Use 'python' instead of 'python3'
```

---

### Issue: "Permission denied: ./bootstrap.sh"

**Solution**:
```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

---

### Issue: Bootstrap hangs during pip install

**Symptoms**: No output for 5+ minutes during package installation

**Solution**:
```bash
# Cancel (Ctrl+C) and re-run with debug mode
./bootstrap.sh --debug

# This shows real-time pip progress
```

---

### Issue: "No space left on device"

**Solution**:
```bash
# Check disk space
df -h

# Clear pip cache
pip cache purge

# Clear Hugging Face cache (if needed)
rm -rf ~/.cache/huggingface/
```

---

### Issue: MLX environment fails on non-macOS

**This is expected!** MLX is macOS-only. Bootstrap will skip `venv/mlx` on Windows/Linux automatically.

---

### Issue: CUDA not detected despite having NVIDIA GPU

**Solution**:
```bash
# Verify CUDA installation
nvidia-smi
nvcc --version

# If missing, install CUDA Toolkit
# https://developer.nvidia.com/cuda-downloads

# Re-run bootstrap
./bootstrap.sh --force
```

---

## Verification

### Check Environments

```bash
# macOS/Linux
ls -la .venv-*

# Expected output:
# venv/common/
# venv/whisperx/
# venv/mlx/       (macOS only)
# venv/indictrans2/
# venv/nllb/
```

### Test Environment Activation

```bash
# Test venv/common
source venv/common/bin/activate
python -c "import ffmpeg; print('✓ Common OK')"
deactivate

# Test venv/whisperx
source venv/whisperx/bin/activate
python -c "import whisperx; print('✓ WhisperX OK')"
deactivate

# Test venv/indictrans2
source venv/indictrans2/bin/activate
python -c "from IndicTransToolkit import IndicProcessor; print('✓ IndicTrans2 OK')"
deactivate

# Test venv/nllb
source venv/nllb/bin/activate
python -c "from transformers import AutoTokenizer; print('✓ NLLB OK')"
deactivate
```

---

## Logs

Bootstrap creates detailed logs:

```bash
# Location
logs/bootstrap_YYYYMMDD_HHMMSS.log

# View latest log
ls -t logs/bootstrap_*.log | head -1 | xargs cat

# Debug mode logs include:
# - Full pip install output
# - Package version details
# - Hardware detection details
```

---

## Maintenance

### Update Environments

```bash
# Force recreate all environments (deletes and rebuilds)
./bootstrap.sh --force

# This is recommended when:
# - Updating to new WhisperX version
# - Resolving dependency conflicts
# - After major system updates
```

### Selective Rebuild

```bash
# Delete specific environment
rm -rf venv/whisperx

# Re-run bootstrap (only rebuilds missing environments)
./bootstrap.sh
```

### Clear Model Cache

```bash
# Free up disk space by clearing downloaded models
rm -rf ~/.cache/huggingface/

# Models will re-download on next pipeline run
```

---

## Next Steps

After successful bootstrap:

1. **[Prepare Your First Job](PREPARE_JOB.md)** - Learn the `prepare-job.sh` command
2. **[Run a Workflow](WORKFLOWS.md)** - Execute transcribe/translate/subtitle
3. **[Architecture Overview](ARCHITECTURE.md)** - Understand the system design

---

**Last Updated**: November 20, 2025  
**Version**: 2.0.0
