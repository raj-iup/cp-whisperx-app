# Bootstrap & Model Caching Integration - Complete

## Summary

Integrated `./cache-models.sh` into the bootstrap process to enable automatic model pre-caching during initial setup.

**Before:** Models downloaded on first pipeline run (slow, requires internet)  
**After:** Models can be pre-cached during bootstrap (fast startup, offline-ready)

---

## What Was Changed

### 1. Bootstrap Script Enhanced (`scripts/bootstrap.sh`)

#### New Command Options

```bash
./bootstrap.sh [OPTIONS]

OPTIONS:
  --debug         Enable verbose logging
  --force         Force recreate all environments
  --cache-models  Pre-cache all models after setup (~20GB, 15-25 min)
  --skip-cache    Skip model caching prompt at the end
  --help          Show help message
```

#### Three Caching Modes

**Mode 1: Automatic Caching** (force cache)
```bash
./bootstrap.sh --cache-models
```
- Creates environments
- Automatically caches all models
- No user prompt
- Best for: CI/CD, scripts, automated setup

**Mode 2: Interactive Prompt** (default)
```bash
./bootstrap.sh
```
- Creates environments
- **Prompts user** to cache models
- Shows benefits and size/time estimates
- Best for: Manual setup, first-time users

**Mode 3: Skip Prompt** (defer caching)
```bash
./bootstrap.sh --skip-cache
```
- Creates environments only
- No prompt, no caching
- User can cache later with `./cache-models.sh --all`
- Best for: Quick testing, limited disk space

#### Interactive Prompt

When running `./bootstrap.sh` without options, user sees:

```
╔════════════════════════════════════════════════════╗
║     MODEL CACHING (RECOMMENDED)                    ║
╚════════════════════════════════════════════════════╝

⚠️  IMPORTANT: Models will download on first pipeline run if not cached now.

Pre-caching models enables:
  ✅ Fully offline pipeline execution
  ✅ Faster job startup times
  ✅ Predictable performance

Models to cache (~20-25GB total):
  • IndicTrans2 (Indic→English) - ~2-5GB
  • NLLB-200 (200+ languages) - ~17GB
  • WhisperX Large-v3 - ~3GB
  • MLX Whisper Large-v3 - ~3GB (Apple Silicon optimized)

Time required: 15-25 minutes

Cache models now? [y/N]
```

### 2. Documentation Updated

#### `docs/user-guide/bootstrap.md`

**Added Sections:**
- Updated Quick Start with `--cache-models` option
- New command options documented
- Phase 3: Model Caching section with:
  - Interactive prompt details
  - Benefits explanation
  - Cache location and sizes
  - Manual caching instructions

**Updated Examples:**
```bash
# Basic setup (with prompt)
./bootstrap.sh

# Setup with automatic caching (recommended)
./bootstrap.sh --cache-models

# Force recreate and cache
./bootstrap.sh --force --cache-models

# Skip caching prompt
./bootstrap.sh --skip-cache
```

#### README.md

Updated Quick Start section:
```bash
# 1. Setup (one-time, ~10 minutes)
./bootstrap.sh --cache-models  # ← Now includes model caching

# 2. Generate subtitles
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-lang hi --target-lang en,gu
./run-pipeline.sh -j <job-id>
```

---

## User Workflows

### Workflow 1: First-Time Setup (Recommended)

**For production use with offline capability:**

```bash
# Clone repository
git clone <repo-url>
cd cp-whisperx-app

# Bootstrap with model caching
./bootstrap.sh --cache-models

# Done! Fully offline ready.
```

**Time:** 25-35 minutes  
**Disk:** ~25-30GB  
**Result:** Fully functional, offline-ready pipeline

### Workflow 2: Quick Testing

**For testing or limited disk space:**

```bash
# Bootstrap without caching
./bootstrap.sh --skip-cache

# Test with sample file (models download on demand)
./prepare-job.sh --media in/sample.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>

# Cache later when needed
./cache-models.sh --all
```

### Workflow 3: CI/CD Automation

**For Docker, CI/CD pipelines:**

```bash
# Automated setup
./bootstrap.sh --cache-models --skip-cache

# Or in Dockerfile
RUN ./bootstrap.sh --cache-models
```

---

## Technical Details

### Integration Points

**1. Bootstrap Flow:**
```
bootstrap.sh
├── Parse arguments (--cache-models, --skip-cache)
├── Create 8 environments (~10 min)
├── Verify installations
└── Model Caching Phase:
    ├── If --cache-models: Run cache-models.sh --all
    ├── Else if --skip-cache: Skip
    └── Else: Prompt user (interactive)
```

**2. Caching Integration:**
```bash
# In scripts/bootstrap.sh (lines ~386-470)
if [ "$CACHE_MODELS" = true ]; then
    log_section "MODEL CACHING"
    "$PROJECT_ROOT/cache-models.sh" --all
elif [ "$SKIP_MODEL_CACHE" = false ]; then
    # Show interactive prompt
    read -p "Cache models now? [y/N]"
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        "$PROJECT_ROOT/cache-models.sh" --all
    fi
fi
```

**3. Error Handling:**
- If caching fails, bootstrap still succeeds
- User informed they can retry with `./cache-models.sh --all`
- Pipeline will download models on first run if not cached

### Model Sizes (Actual)

| Model | Size | Download Time | Platform |
|-------|------|---------------|----------|
| **NLLB-200** | 17.6 GB | 5-10 min | All |
| **IndicTrans2** | 2-5 GB | 2-5 min | All |
| **WhisperX** | 3 GB | 5-10 min | All |
| **MLX Whisper** | 3 GB | 5-10 min | Apple Silicon |
| **Total** | 20-25 GB | 15-25 min | - |

### Cache Verification

After bootstrap with caching:

```bash
# Check cache
ls -lh .cache/huggingface/

# Expected output:
models--facebook--nllb-200-3.3B/
models--ai4bharat--indictrans2-indic-en-1B/
models--Systran--faster-whisper-large-v3/
models--mlx-community--whisper-large-v3-mlx/  # Apple Silicon only

# Check size
du -sh .cache/huggingface/
# Expected: 20-25G
```

---

## Benefits

### Before Integration

**Workflow:**
1. Run `./bootstrap.sh` (~10 min)
2. Start first job
3. Wait for model downloads (~20 min, requires internet)
4. Job finally runs

**Issues:**
- ❌ First job very slow (20-30 min overhead)
- ❌ Requires internet during job execution
- ❌ Unpredictable startup time
- ❌ Network errors can fail jobs

### After Integration

**Workflow:**
1. Run `./bootstrap.sh --cache-models` (~25 min)
2. Start job immediately
3. Job runs at full speed

**Benefits:**
- ✅ Fast job startup (no download delay)
- ✅ Fully offline execution
- ✅ Predictable performance
- ✅ Reliable (no network dependency)

---

## Examples

### Example 1: Development Setup

```bash
# Developer wants fast iteration
./bootstrap.sh --skip-cache

# Work on code, test with small files
# Models download on first use

# Later, prepare for production
./cache-models.sh --all
```

### Example 2: Production Deployment

```bash
# Server deployment (no interactive prompts)
./bootstrap.sh --cache-models

# Verify setup
./cache-models.sh --help  # Check available

# Run production jobs
for file in in/*.mp4; do
  ./prepare-job.sh --media "$file" --workflow subtitle -s hi -t en
  ./run-pipeline.sh -j <job-id>
done
```

### Example 3: Docker Container

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install dependencies
RUN apt-get update && apt-get install -y ffmpeg git

# Copy project
COPY . /app
WORKDIR /app

# Bootstrap with model caching
RUN ./bootstrap.sh --cache-models

# Run pipeline
CMD ["./run-pipeline.sh"]
```

---

## Troubleshooting

### Issue 1: Caching Fails

**Symptom:**
```
[ERROR] Failed to cache model: ai4bharat/indictrans2-indic-en-1B
```

**Solution:**
```bash
# Check HF token
cat config/secrets.json | grep hf_token

# Add token if missing
nano config/secrets.json
# Add: "hf_token": "hf_YOUR_TOKEN"

# Retry caching
./cache-models.sh --indictrans2
```

### Issue 2: Out of Disk Space

**Symptom:**
```
OSError: [Errno 28] No space left on device
```

**Solution:**
```bash
# Check available space
df -h .

# Need at least 30GB free

# Skip caching for now
./bootstrap.sh --skip-cache

# Cache individual models later
./cache-models.sh --nllb      # 17GB
./cache-models.sh --whisperx  # 3GB
```

### Issue 3: Slow Download

**Symptom:** Download stuck or very slow

**Solution:**
```bash
# Use HuggingFace mirror (if available)
export HF_ENDPOINT=https://hf-mirror.com

# Or retry later
./bootstrap.sh --skip-cache
./cache-models.sh --all  # Retry when network is better
```

---

## Verification

### Check Bootstrap Completed Successfully

```bash
# All environments should exist
ls -d .venv-*

# Expected:
venv/common
venv/demucs
venv/indictrans2
venv/llm
venv/mlx         # macOS only
venv/nllb
venv/pyannote
venv/whisperx
```

### Check Models Cached

```bash
# Check cache directory
ls .cache/huggingface/

# Should see model directories
# If empty, models not cached (will download on first run)
```

### Test Offline Execution

```bash
# Turn off Wi-Fi
# Run a job
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>

# Should work if models cached!
```

---

## Migration Guide

### Updating Existing Setup

If you already have environments but want to add caching:

```bash
# Option 1: Just cache models
./cache-models.sh --all

# Option 2: Full refresh
./bootstrap.sh --force --cache-models
```

### Updating Documentation

For users updating from older versions:

**Old instructions:**
```bash
./bootstrap.sh
# Models download on first run
```

**New instructions:**
```bash
./bootstrap.sh --cache-models
# Models pre-cached, ready for offline use
```

---

## Files Modified

### Scripts
- ✅ `scripts/bootstrap.sh` - Added caching integration
- ✅ `bootstrap.sh` - Root wrapper (unchanged, forwards to scripts/)

### Documentation
- ✅ `docs/user-guide/bootstrap.md` - Added caching documentation
- ✅ `README.md` - Updated Quick Start
- ✅ `docs/setup/BOOTSTRAP_MODEL_CACHING_INTEGRATION.md` - This file

### Related Files
- ✅ `cache-models.sh` - Enhanced in previous update
- ✅ `docs/setup/MODEL_CACHING.md` - Detailed caching guide
- ✅ `docs/setup/CACHE_MODELS_FIX.md` - Bug fix documentation

---

## Summary

| Feature | Status | Impact |
|---------|--------|--------|
| **Bootstrap Integration** | ✅ Complete | Seamless model caching |
| **Interactive Prompt** | ✅ Complete | User-friendly guidance |
| **Automatic Mode** | ✅ Complete | CI/CD ready |
| **Skip Mode** | ✅ Complete | Flexible for testing |
| **Documentation** | ✅ Complete | Clear instructions |
| **Error Handling** | ✅ Complete | Graceful degradation |

**Result:** Bootstrap now provides a complete, production-ready setup in one command! 🎉

---

**Date:** 2025-11-25  
**Status:** ✅ Complete  
**Ready for:** Production use
