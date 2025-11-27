# Model Caching for Pipeline Reliability

## Overview

**✅ Bootstrap script NOW supports automatic model pre-caching!**

The pipeline uses HuggingFace models that are automatically downloaded to `.cache/huggingface/` on first use. You can pre-cache these models during bootstrap or separately to enable fully offline execution.

### Why Pre-Cache Models?

**Without Pre-Caching:**
❌ First job execution requires internet  
❌ Can fail if HuggingFace is down  
❌ Slow first run (downloads 2-5GB per model)  
❌ May hit rate limits during download

**With Pre-Caching:**
✅ Fully offline pipeline execution  
✅ Faster job startup times  
✅ Predictable performance  
✅ No network dependency during jobs

## Quick Start

### Option 1: Bootstrap with Model Caching (Recommended)

```bash
# One-time setup with automatic model caching
./bootstrap.sh --cache-models
```

This creates all environments AND pre-caches models (~25-35 minutes total).

### Option 2: Bootstrap with Interactive Prompt (Default)

```bash
# Bootstrap with user prompt
./bootstrap.sh
# You'll be asked if you want to cache models
```

### Option 3: Cache Models Separately

```bash
# Bootstrap without caching
./bootstrap.sh --skip-cache

# Cache models later
./cache-models.sh --all
```

## How It Works

## How It Works

### Architecture

The pipeline uses a centralized **Environment Manager** (`shared/environment_manager.py`) that ensures all stages have access to cached models:

```python
# Environment Manager automatically sets cache paths for ALL stages
env["TORCH_HOME"] = ".cache/torch"
env["HF_HOME"] = ".cache/huggingface"
env["TRANSFORMERS_CACHE"] = ".cache/huggingface"
env["MLX_CACHE_DIR"] = ".cache/mlx"
```

### Cache Configuration

Bootstrap creates `config/hardware_cache.json` with cache settings:

```json
{
  "cache": {
    "base_dir": ".cache",
    "torch_home": ".cache/torch",
    "hf_home": ".cache/huggingface",
    "mlx_home": ".cache/mlx"
  }
}
```

### Stage Access to Models

All pipeline stages automatically access cached models:

| Stage | Models Used | Cache Location |
|-------|-------------|----------------|
| **ASR (WhisperX)** | whisper-large-v3 | `.cache/huggingface/hub/` |
| **ASR (MLX)** | whisper-large-v3-mlx | `.cache/huggingface/hub/` |
| **Translation (IndicTrans2)** | indictrans2-indic-en-1B | `.cache/huggingface/hub/` |
| **Translation (NLLB)** | nllb-200-3.3B | `.cache/huggingface/hub/` |
| **VAD (PyAnnote)** | pyannote models | `.cache/torch/` |

**✅ All stages use the centralized cache - no additional configuration needed!**

## Model Caching Script

I've created a dedicated script: **`cache-models.sh`**

### Usage

```bash
# Cache all models (~15-20GB total, 10-30 minutes)
./cache-models.sh --all

# Cache only IndicTrans2 (~4GB, fastest)
./cache-models.sh --indictrans2

# Cache only NLLB (~7GB)
./cache-models.sh --nllb

# Show help
./cache-models.sh --help
```

### What It Caches

1. **IndicTrans2 Indic→English** (~2GB)
   - Model: `ai4bharat/indictrans2-indic-en-1B`
   - Used for: Hindi/Indic → English translation

2. **IndicTrans2 Indic→Indic** (~2GB, optional)
   - Model: `ai4bharat/indictrans2-indic-indic-1B`  
   - Used for: Hindi → Tamil, Gujarati → Bengali, etc.

3. **NLLB-200** (~7GB)
   - Model: `facebook/nllb-200-3.3B`
   - Used for: Non-Indic language translation

4. **WhisperX** (~3GB)
   - Model: `openai/whisper-large-v3`
   - Note: Auto-cached on first transcription

5. **LLM Models** (API-based)
   - Anthropic Claude, OpenAI GPT
   - No local caching needed (API calls)

### Cache Location

All models cached in:
```
.cache/huggingface/hub/
├── models--ai4bharat_*indictrans2-indic-en-1B/
├── models--ai4bharat_*indictrans2-indic-indic-1B/
├── models--facebook_*nllb-200-3.3B/
└── models--openai_*whisper-large-v3/
```

## Recommended Workflow

### Option 1: Pre-cache Everything (Recommended for Production)

```bash
# 1. Bootstrap with automatic model caching
./bootstrap.sh --cache-models

# 2. Run jobs immediately (fast, no downloads)
./prepare-job.sh --media in/movie.mp4 --workflow subtitle -s hi -t en
./run-pipeline.sh -j <job-id>
```

**Time:** ~25-35 minutes (one-time setup)  
**Disk:** ~30GB  
**Result:** Fully offline-ready pipeline

### Option 2: Interactive Setup (Recommended for First-Time Users)

```bash
# 1. Bootstrap (will prompt for caching)
./bootstrap.sh

# You'll see:
# ⚠️  IMPORTANT: Models will download on first pipeline run if not cached now.
# 
# Cache models now? [y/N]

# 2. Choose 'y' to cache, or 'N' to skip
```

### Option 3: Cache on Demand (For Testing)

```bash
# 1. Bootstrap without caching
./bootstrap.sh --skip-cache

# 2. Run job (downloads models on first run)
./run-pipeline.sh -j <job-id>
# ⚠️  First run: slow (downloads ~20GB)
# ✓  Subsequent runs: fast (uses cache)

# 3. Or cache manually later
./cache-models.sh --all
```

### Option 4: Selective Caching

```bash
# Only cache IndicTrans2 (fastest, most common)
./cache-models.sh --indictrans2

# Only cache NLLB (for non-Indic languages)
./cache-models.sh --nllb

# Only cache WhisperX
./cache-models.sh --whisperx

# Only cache MLX (Apple Silicon)
./cache-models.sh --mlx
```

## Verification

### Check if Models are Cached

```bash
# List cached models
ls -lh .cache/huggingface/hub/

# Expected output (if all models cached):
# models--ai4bharat--indictrans2-indic-en-1B/
# models--facebook--nllb-200-3.3B/
# models--Systran--faster-whisper-large-v3/
# models--mlx-community--whisper-large-v3-mlx/  # Apple Silicon only

# Check total cache size
du -sh .cache/huggingface/
# Expected: 20-25GB
```

### Test Offline Execution

```bash
# Turn off Wi-Fi/network
# Run a job
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>

# Should work perfectly if models are cached! ✅
```

### Check Cache Configuration

```bash
# View cache settings
cat config/hardware_cache.json | grep -A 10 '"cache"'

# Output should show:
# "cache": {
#   "base_dir": ".cache",
#   "torch_home": ".cache/torch",
#   "hf_home": ".cache/huggingface",
#   "mlx_home": ".cache/mlx"
# }
```

## Summary

### Bootstrap Integration Status

**✅ COMPLETE** - Bootstrap script now fully supports model pre-caching!

**Bootstrap Options:**
- `./bootstrap.sh --cache-models` - Automatic caching
- `./bootstrap.sh` - Interactive prompt (default)
- `./bootstrap.sh --skip-cache` - Skip caching

**Cache Script:**
- `./cache-models.sh --all` - Cache all models
- `./cache-models.sh --indictrans2` - Cache only IndicTrans2
- `./cache-models.sh --nllb` - Cache only NLLB
- `./cache-models.sh --whisperx` - Cache only WhisperX
- `./cache-models.sh --mlx` - Cache only MLX (Apple Silicon)

**Cache Access:**
- ✅ Centralized via `shared/environment_manager.py`
- ✅ All pipeline stages automatically use cached models
- ✅ No per-stage configuration needed
- ✅ Works offline after initial caching

### Key Files

**Scripts:**
- `cache-models.sh` - Model pre-caching script
- `scripts/bootstrap.sh` - Main bootstrap (with caching integration)
- `scripts/bootstrap.ps1` - PowerShell bootstrap (shows caching instructions)
- `shared/environment_manager.py` - Sets cache env vars for all stages

**Configuration:**
- `config/hardware_cache.json` - Cache paths and environment mapping
- `.cache/huggingface/` - HuggingFace models cache
- `.cache/torch/` - PyTorch models cache
- `.cache/mlx/` - MLX models cache (Apple Silicon)

**Documentation:**
- `docs/setup/MODEL_CACHING.md` - This guide
- `docs/setup/BOOTSTRAP_MODEL_CACHING_INTEGRATION.md` - Integration details
- `docs/user-guide/bootstrap.md` - Bootstrap guide
- `README.md` - Quick start with caching

---

**Recommendation:**  
Run `./bootstrap.sh --cache-models` for production setups to enable fully offline execution.

**Files Updated:**
- ✅ `cache-models.sh` - Model pre-caching script
- ✅ `scripts/bootstrap.sh` - Integrated with model caching
- ✅ `scripts/bootstrap.ps1` - Shows caching instructions
- ✅ `shared/environment_manager.py` - Sets cache paths automatically
- ✅ `docs/setup/MODEL_CACHING.md` - Updated documentation
- ✅ `README.md` - Updated quick start

---

**Status:** ✅ Fully Integrated  
**Tested:** ✅ All stages access models from `.cache/huggingface/`  
**Ready for:** Production use
