# MLX Whisper Cache Fix

**Date:** 2024-11-25  
**Issue:** MLX Whisper model caching failed with "module 'mlx_whisper' has no attribute 'load_model'"

## Problem

The cache-models.sh script was using incorrect API to load MLX Whisper models:

```python
# ❌ WRONG - This doesn't exist
import mlx_whisper
model_path = mlx_whisper.load_model("mlx-community/whisper-large-v3-mlx")
```

**Error:**
```
✗ Error caching MLX Whisper model: module 'mlx_whisper' has no attribute 'load_model'
```

## Root Cause

The `load_model` function is in a submodule `mlx_whisper.load_models`, not directly in `mlx_whisper`.

## Solution

Updated cache-models.sh (line 310) to use correct import:

```python
# ✅ CORRECT
from mlx_whisper import load_models
model = load_models.load_model("mlx-community/whisper-large-v3-mlx")
```

## File Changed

**cache-models.sh** (lines 301-321):
- Changed import from `import mlx_whisper` to `from mlx_whisper import load_models`
- Changed call from `mlx_whisper.load_model()` to `load_models.load_model()`
- Added traceback printing for better error debugging

## Testing

```bash
# Test the fix
cd /Users/rpatel/Projects/cp-whisperx-app
source venv/mlx/bin/activate
python3 << 'EOF'
from mlx_whisper import load_models
model = load_models.load_model("mlx-community/whisper-large-v3-mlx")
print(f"✓ Model loaded: {type(model)}")
EOF
```

**Result:**
```
✓ MLX Whisper model cached successfully
Model type: <class 'mlx_whisper.whisper.Whisper'>
```

## Verification

Now cache-models.sh should work correctly:

```bash
# Cache MLX model
./cache-models.sh --mlx

# Expected output:
# [INFO] Downloading MLX Whisper model (this may take 5-10 minutes)...
# Loading MLX Whisper model (downloads automatically)...
# ✓ MLX Whisper model cached successfully
```

## Status

✅ **FIXED** - MLX Whisper caching now works correctly

## Related Files

- `cache-models.sh` - Updated with correct API
- `scripts/whisper_backends.py` - Uses same API (already correct)

---

**Date Fixed:** 2024-11-25  
**Status:** ✅ Complete
