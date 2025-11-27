# WhisperX & MLX Model Caching - Enhancement Complete

## Summary

Added automatic model caching for **WhisperX** and **MLX Whisper** models to `cache-models.sh`.

Previously, these models were skipped and would download on first pipeline run. Now they can be pre-cached for reliable offline execution.

## What Was Added

### 1. WhisperX Model Caching

**Model:** `openai/whisper-large-v3` (via faster-whisper)  
**Size:** ~3GB  
**Environment:** `venv/whisperx`

**Implementation:**
- Automatically loads WhisperX model which triggers download
- Caches to: `.cache/huggingface/hub/models--Systran--faster-whisper-large-v3`
- Checks if already cached before downloading

### 2. MLX Whisper Model Caching (Apple Silicon)

**Model:** `mlx-community/whisper-large-v3-mlx`  
**Size:** ~3GB  
**Environment:** `venv/mlx`  
**Platform:** Apple Silicon (M1/M2/M3) only

**Implementation:**
- Uses `mlx_whisper.load_model()` which downloads automatically
- Only runs on `arm64` architecture (Apple Silicon)
- Skipped on Intel/Linux systems

### 3. Updated Command Options

**New options:**
```bash
./cache-models.sh --whisperx    # Cache only WhisperX
./cache-models.sh --mlx         # Cache only MLX Whisper (Apple Silicon)
./cache-models.sh --all         # Cache all models (includes WhisperX + MLX)
```

**Updated help:**
```
MODELS CACHED:
  1. IndicTrans2 Indic→English (ai4bharat/indictrans2-indic-en-1B)
  2. IndicTrans2 Indic→Indic (ai4bharat/indictrans2-indic-indic-1B)  
  3. NLLB-200 3.3B (facebook/nllb-200-3.3B)
  4. WhisperX Large-v3 (openai/whisper-large-v3)
  5. MLX Whisper Large-v3 (mlx-community/whisper-large-v3-mlx) [Apple Silicon only]

TOTAL SIZE: ~20-25GB
```

## Usage

### Cache All Models (Recommended)

```bash
./cache-models.sh --all
```

This will cache:
- ✅ IndicTrans2 (if HF token provided)
- ✅ NLLB (~17GB)
- ✅ WhisperX (~3GB)
- ✅ MLX Whisper (~3GB, Apple Silicon only)

**Total:** ~20-25GB  
**Time:** 10-20 minutes depending on connection

### Cache Individual Models

```bash
# Cache only WhisperX
./cache-models.sh --whisperx

# Cache only MLX Whisper (Apple Silicon)
./cache-models.sh --mlx

# Cache only translation models
./cache-models.sh --indictrans2 --nllb
```

### For Your System (Apple Silicon)

Since you're on Apple Silicon (arm64), run:

```bash
./cache-models.sh --all
```

This will cache:
1. ✅ NLLB (already done)
2. ⏳ IndicTrans2 (run this)
3. ⏳ WhisperX (NEW - will download)
4. ⏳ MLX Whisper (NEW - will download, Apple Silicon optimized)

## Benefits

### Before (Old Behavior)
- ❌ WhisperX downloaded on first pipeline run
- ❌ MLX downloaded on first pipeline run
- ⚠️  Required internet during job execution
- ⚠️  First job had long startup time

### After (New Behavior)
- ✅ WhisperX pre-cached
- ✅ MLX pre-cached
- ✅ **Fully offline execution** possible
- ✅ Fast startup on all jobs

## Technical Details

### WhisperX Caching

**Method:**
```python
import whisperx
model = whisperx.load_model("large-v3", device="cpu", compute_type="int8")
```

**Cache Location:**
```
.cache/huggingface/hub/models--Systran--faster-whisper-large-v3/
```

**Backend:** faster-whisper (CTranslate2)

### MLX Caching

**Method:**
```python
import mlx_whisper
model_path = mlx_whisper.load_model("mlx-community/whisper-large-v3-mlx")
```

**Cache Location:**
```
.cache/huggingface/models--mlx-community--whisper-large-v3-mlx/
```

**Backend:** MLX (Apple Metal acceleration)

### Architecture Detection

Script automatically detects Apple Silicon:
```bash
if [[ "$(uname -m)" == "arm64" ]]; then
    CACHE_MLX=true  # Enable MLX on Apple Silicon
fi
```

## Verification

### Check What's Cached

```bash
ls -la .cache/huggingface/
```

**Expected after `./cache-models.sh --all`:**
```
✅ models--facebook--nllb-200-3.3B/
✅ models--ai4bharat--indictrans2-indic-en-1B/
✅ models--Systran--faster-whisper-large-v3/  (WhisperX)
✅ models--mlx-community--whisper-large-v3-mlx/  (MLX)
```

### Check Cache Size

```bash
du -sh .cache/huggingface/
```

**Expected:** 20-25GB after caching all models

### Test Pipeline Without Internet

```bash
# Disconnect from internet (Wi-Fi off)
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>

# Should work without internet! ✨
```

## Command Reference

| Command | What It Caches | Size | Time |
|---------|----------------|------|------|
| `./cache-models.sh --all` | Everything | ~20-25GB | 10-20 min |
| `./cache-models.sh --indictrans2` | IndicTrans2 only | ~2-5GB | 2-5 min |
| `./cache-models.sh --nllb` | NLLB only | ~17GB | 5-10 min |
| `./cache-models.sh --whisperx` | WhisperX only | ~3GB | 5-10 min |
| `./cache-models.sh --mlx` | MLX Whisper only | ~3GB | 5-10 min |

## Next Steps

Run the complete caching:

```bash
./cache-models.sh --all
```

This will:
1. Check NLLB (already cached ✅)
2. Download IndicTrans2 (~2-5GB, 2-5 min)
3. Download WhisperX (~3GB, 5-10 min) ← NEW
4. Download MLX Whisper (~3GB, 5-10 min) ← NEW

**Total time:** ~15-25 minutes  
**Then:** Fully offline pipeline! 🎉

## Files Modified

- ✅ `cache-models.sh` - Added WhisperX and MLX caching
- ✅ Added `--whisperx` and `--mlx` options
- ✅ Updated help text and documentation
- ✅ Added architecture detection for Apple Silicon

---

**Date:** 2025-11-25  
**Status:** ✅ Complete  
**Ready for:** Offline pipeline execution
