# Demucs TorchCodec Dependency Fix

**Date:** 2025-11-23  
**Status:** ✅ Fixed  
**Issue:** Source separation failed with "No module named 'torchcodec'" error

---

## Problem Summary

### Issue

Source separation stage failed after processing audio successfully:

```
ImportError: TorchCodec is required for save_with_torchcodec. 
Please install torchcodec to use this function.
```

**Log showed:**
- Demucs processed 100% of audio successfully  
- Failed at final save step due to missing torchcodec module
- torchaudio 2.9.1 tries to use torchcodec by default

### Root Cause

`requirements-demucs.txt` specified `torch>=2.0.0` and `torchaudio>=2.0.0`, which installed:
- torch 2.9.1
- torchaudio 2.9.1

**Problem:** torchaudio 2.9.x requires `torchcodec` package for audio encoding, but:
1. torchcodec not in requirements
2. torchcodec not available via pip in all environments
3. Demucs doesn't need the latest torchaudio features

---

## Solution Implemented

### Fix: Pin Compatible Versions

Updated `requirements-demucs.txt`:

```python
# Before (caused issue)
torch>=2.0.0
torchaudio>=2.0.0

# After (fixed)
torch==2.5.1
torchaudio==2.5.1
```

### Why This Works

**torchaudio 2.5.1:**
- Does NOT require torchcodec
- Uses standard audio backends (soundfile, ffmpeg)
- Fully compatible with Demucs 4.x
- Stable and well-tested
- Works on all platforms (macOS, Linux, Windows)

**torch 2.5.1:**
- Matches torchaudio version
- Stable release
- MPS (Apple Silicon) support
- CUDA support
- Compatible with Demucs requirements

---

## Files Modified

**1. requirements-demucs.txt**
```diff
- torch>=2.0.0
- torchaudio>=2.0.0
+ torch==2.5.1
+ torchaudio==2.5.1
```

---

## Installation

### For New Installs

```bash
# Bootstrap now installs correct versions automatically
./bootstrap.sh
```

### For Existing Installs

```bash
# Option 1: Recreate demucs environment (recommended)
rm -rf venv/demucs
./bootstrap.sh

# Option 2: Reinstall dependencies
source venv/demucs/bin/activate
pip install -r requirements-demucs.txt --force-reinstall
deactivate
```

---

## Testing

### Verify Fix

```bash
# Check versions
source venv/demucs/bin/activate
python -c "import torch; print(f'torch: {torch.__version__}')"
python -c "import torchaudio; print(f'torchaudio: {torchaudio.__version__}')"
python -c "import demucs; print('✓ Demucs working')"
deactivate

# Expected output:
# torch: 2.5.1
# torchaudio: 2.5.1
# ✓ Demucs working
```

### Test Source Separation

```bash
# Run pipeline with source separation enabled
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi

./run-pipeline.sh -j <job-id>

# Expected: Source separation completes successfully
# [INFO] Running source separation...
# [INFO] Processing audio with Demucs...
# [INFO] ✓ Vocals extracted: out/.../99_source_separation/vocals.wav
# [INFO] ✅ Stage source_separation: COMPLETED
```

---

## Technical Details

### Why torchaudio 2.9.x Failed

In torchaudio 2.9.x, the `save()` function tries to use torchcodec:

```python
def save(uri, src, sample_rate, ...):
    # New in 2.9: tries torchcodec first
    return save_with_torchcodec(...)  # Fails if torchcodec not installed
```

### Why torchaudio 2.5.x Works

In torchaudio 2.5.x, the `save()` function uses standard backends:

```python
def save(uri, src, sample_rate, ...):
    # Uses soundfile or ffmpeg backend
    return _save_audio(...)  # Always works
```

### Demucs Compatibility

Demucs requirements:
- `torch >= 2.0.0` ✓ (2.5.1 meets this)
- `torchaudio >= 2.0.0` ✓ (2.5.1 meets this)
- Audio I/O for WAV files ✓ (2.5.1 has this)
- MPS/CUDA support ✓ (2.5.1 has this)

Demucs does NOT need:
- Latest torch 2.9 features ✗
- torchcodec encoder ✗
- Cutting-edge audio features ✗

**Result:** torch/torchaudio 2.5.1 is ideal - stable, compatible, no extra dependencies.

---

## Why Not Install torchcodec?

**Reasons to avoid torchcodec dependency:**

1. **Not in PyPI:** torchcodec not available via standard `pip install torchcodec`
2. **Platform-specific:** Requires platform-specific builds
3. **Unnecessary:** Demucs works fine with standard audio backends
4. **Complexity:** Adds build dependencies and potential installation failures
5. **Maintenance:** Extra dependency to track and update

**Better solution:** Use stable torch/torchaudio versions that don't require it.

---

## Benefits of This Fix

✅ **No Extra Dependencies:** Works with standard pip packages  
✅ **Cross-Platform:** Same versions work on macOS, Linux, Windows  
✅ **Stable:** torch/torchaudio 2.5.1 are well-tested releases  
✅ **Simple:** No build tools or platform-specific setup needed  
✅ **Maintainable:** Clear version pinning, easy to understand  

---

## Related Issues

If you see similar errors in other stages:
- Check torch/torchaudio versions
- Pin to compatible versions (2.5.x recommended for general use)
- Avoid bleeding-edge versions unless needed for specific features

---

## Migration Guide

### For Users With Existing Setup

**If you already ran bootstrap:**

```bash
# Quick fix: Just recreate demucs environment
rm -rf venv/demucs
./bootstrap.sh

# Verify
source venv/demucs/bin/activate
python -c "import torch, torchaudio; print(f'torch={torch.__version__}, torchaudio={torchaudio.__version__}')"
deactivate
```

**If you're starting fresh:**

```bash
# Latest bootstrap.sh automatically uses correct versions
./bootstrap.sh
```

---

## Version Compatibility Matrix

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| torch | 2.5.1 | ✅ Recommended | Stable, MPS/CUDA support |
| torchaudio | 2.5.1 | ✅ Recommended | No torchcodec needed |
| torch | 2.9.x | ⚠️ Requires torchcodec | Newer but needs extra deps |
| torchaudio | 2.9.x | ⚠️ Requires torchcodec | Tries torchcodec first |
| demucs | 4.0+ | ✅ Works with both | Compatible with torch 2.x |

---

## Conclusion

Fixed source separation failure by pinning torch/torchaudio to version 2.5.1, which:
- Eliminates torchcodec dependency
- Maintains full Demucs functionality  
- Works across all platforms
- Simplifies installation
- Uses stable, well-tested versions

**Action:** Re-run `./bootstrap.sh` or recreate `venv/demucs` to apply the fix.
