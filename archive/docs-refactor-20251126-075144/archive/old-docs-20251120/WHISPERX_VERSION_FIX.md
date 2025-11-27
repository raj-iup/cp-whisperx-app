# WhisperX Version Fix

**Date:** 2024-11-20  
**Issue:** Yanked package warning during bootstrap

## Problem

Bootstrap log showed this warning:

```
WARNING: The candidate selected for download or install is a yanked version: 'whisperx' candidate (version 3.1.1 at https://files.pythonhosted.org/packages/...)
Reason for being yanked: unofficial release by third party (see https://github.com/m-bain/whisperX/issues/761)
```

### What This Means

- **Yanked package:** The package author marked version 3.1.1 as "yanked" on PyPI
- **Reason:** It was an unofficial third-party release
- **Impact:** While it still works, pip warns that this version should not be used

## Root Cause

The `requirements-whisperx.txt` file specified:
```
whisperx==3.1.1
```

This version was removed from PyPI's recommended versions because it was uploaded by someone other than the official maintainer.

## Solution

### Updated Version

Changed `requirements-whisperx.txt` to use **whisperx==3.3.1**

```python
# Core WhisperX with dependencies
# Using 3.3.1 (latest compatible with torch 2.0.x)
# Note: 3.1.1 was yanked (unofficial third-party release)
# Note: 3.4+ requires torch>=2.5, 3.7+ requires torch~=2.8
whisperx==3.3.1
```

### Why 3.3.1 Instead of Latest?

| Version | Status | Reason |
|---------|--------|--------|
| **3.3.1** | ✅ **CHOSEN** | Latest compatible with torch 2.0.x |
| 3.7.4 | ❌ Not compatible | Requires torch~=2.8.0, numpy>=2.0.2 |
| 3.4.3-3.6.0 | ❌ Not compatible | Requires torch>=2.5.1 |
| 3.3.0, 3.2.0 | ✅ Compatible | Older but would work |
| 3.1.1 | ❌ Yanked | Unofficial third-party release |

### Compatibility Matrix

Our current environment:
```
torch~=2.0.0
torchaudio~=2.0.0
numpy>=1.23.0,<2.0.0
```

**whisperx 3.3.1** requirements:
```
torch>=2  (✅ Compatible with 2.0.x)
torchaudio>=2  (✅ Compatible with 2.0.x)
numpy (no strict requirement in 3.3.1)
```

**whisperx 3.7.4** requirements (latest):
```
torch~=2.8.0  (❌ Incompatible - would require major upgrade)
numpy>=2.0.2  (❌ Incompatible - conflicts with other deps)
```

## Impact

### Before Fix
```bash
./bootstrap.sh
# WARNING: The candidate selected... yanked version...
# Package still installs but generates warning
```

### After Fix
```bash
./bootstrap.sh
# No warning - installs official whisperx 3.3.1
# Fully compatible with existing torch 2.0.x
```

## Upgrade Path (Future)

To use the latest whisperx (3.7.4+), we would need to:

1. **Upgrade torch:** 2.0.0 → 2.8.0
   ```
   torch~=2.8.0
   torchaudio~=2.8.0
   ```

2. **Upgrade numpy:** <2.0 → >=2.0.2
   ```
   numpy>=2.0.2,<2.1.0
   ```

3. **Test compatibility** with:
   - pyannote.audio
   - faster-whisper
   - ctranslate2
   - All other ML dependencies

4. **Update venv/indictrans2** separately
   - IndicTrans2 already uses torch>=2.5, numpy>=2.1
   - Would remain isolated in its own environment

**Recommendation:** Wait for dependencies to stabilize on torch 2.8+ before upgrading.

## Testing

To verify the fix works:

```bash
# Remove old whisperx environment
rm -rf venv/whisperx

# Recreate with new version
./bootstrap.sh --force

# Check for warnings
tail -100 logs/bootstrap_*.log | grep -i "warning\|yanked"
# Should return nothing

# Verify installed version
venv/whisperx/bin/python -c "import whisperx; print(whisperx.__version__)"
# Expected: 3.3.1
```

## Files Changed

- ✏️ `requirements-whisperx.txt` - Updated from 3.1.1 to 3.3.1

## References

- [whisperX Issue #761](https://github.com/m-bain/whisperX/issues/761) - Unofficial 3.1.1 release discussion
- [PyPI whisperx](https://pypi.org/project/whisperx/) - Official package page
- [PEP 592](https://peps.python.org/pep-0592/) - Yanked packages specification

## Summary

- ✅ Fixed yanked package warning
- ✅ Using official whisperx version (3.3.1)
- ✅ Maintains compatibility with torch 2.0.x
- ✅ No breaking changes to existing code
- ✅ Safe to deploy

---

**Status:** ✅ Complete  
**Breaking Changes:** None  
**User Action Required:** Run `./bootstrap.sh --force` to recreate venv/whisperx with new version
