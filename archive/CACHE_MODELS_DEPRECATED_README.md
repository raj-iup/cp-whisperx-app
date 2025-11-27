# cache-models.sh - DEPRECATED

**Date Archived**: 2025-11-25  
**Status**: Deprecated - Functionality Integrated into Bootstrap

## Why This File Was Archived

This script has been **fully integrated** into `scripts/bootstrap.sh` to eliminate external dependencies and simplify the bootstrap process.

## What Happened

All model caching functionality from this script has been integrated directly into the bootstrap script as internal functions:

- `is_model_cached()` - Check if model is cached
- `cache_hf_model()` - Cache HuggingFace models
- `cache_whisperx_model()` - Cache WhisperX model
- `cache_mlx_model()` - Cache MLX Whisper model
- `run_model_caching()` - Orchestrate all caching

## How to Cache Models Now

### Old Way (No Longer Works)
```bash
./cache-models.sh --all  # ✗ Script doesn't exist anymore
```

### New Way (Integrated)
```bash
./bootstrap.sh --cache-models  # ✓ All functionality built-in
```

## Benefits of Integration

1. **Single Script**: No need to maintain two separate scripts
2. **No External Deps**: Bootstrap is fully self-contained
3. **Always in Sync**: Functions can't get out of sync
4. **Simpler UX**: Users only need to know about bootstrap

## If You Need the Old Functionality

The old script is preserved here for reference, but you should use the integrated bootstrap functions instead:

```bash
# Instead of:
./cache-models.sh --indictrans2

# Use bootstrap (which caches all or none):
./bootstrap.sh --cache-models

# Or manually cache in specific environment:
source .venv-indictrans2/bin/activate
python3 -c "
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
model = AutoModelForSeq2SeqLM.from_pretrained('ai4bharat/indictrans2-indic-en-1B')
"
```

## Documentation

For complete details, see:
- `docs/BOOTSTRAP_INTEGRATION_SUMMARY.md` - Integration details
- `scripts/bootstrap.sh` - Integrated caching functions
- `README.md` - Updated usage instructions

---

**This file is kept for reference only. Do not use it in production.**
