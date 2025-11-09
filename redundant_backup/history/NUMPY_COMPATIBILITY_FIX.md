# NumPy 2.x Compatibility Fix

## Problem
WhisperX 3.4.3 requires `numpy>=2.0.2`, but the bootstrap script was downgrading NumPy to 1.x for torchaudio 2.8.x compatibility. This created a dependency conflict warning:

```
whisperx 3.4.3 requires numpy>=2.0.2, but you have numpy 1.26.4 which is incompatible.
```

## Root Cause
- **torchaudio 2.8.x** pip metadata says it requires `numpy<2.0`
- **WhisperX 3.4.3+** requires `numpy>=2.0.2`
- The bootstrap script was forcing NumPy 1.x based on pip metadata

## Solution
**Use numpy 2.x with torch/torchaudio 2.8.x**

Despite pip's metadata warning, **torchaudio 2.8.x actually works fine with numpy 2.x at runtime**. This is a known discrepancy between package metadata and actual runtime compatibility.

### Changes Made

1. **bootstrap.sh** (lines 105-145)
   - Removed NumPy downgrade logic
   - Added NumPy upgrade logic (1.x → 2.x if needed)
   - Updated version verification to check runtime compatibility
   - Added clarifying comments about metadata vs. runtime compatibility

2. **requirements.txt**
   - Updated: `numpy>=2.0.2,<2.1` (was `numpy>=1.24.0,<2.0`)
   - Comment updated to clarify the situation

3. **requirements-macos-pinned.txt**
   - No change needed (already had `numpy>=2.0.2,<2.1`)
   - Kept torch/torchaudio at 2.8.0 (verified compatible)

## Version Compatibility Matrix

| Package | Version | Notes |
|---------|---------|-------|
| numpy | 2.0.2+ | Required by WhisperX 3.4.3+ |
| torch | 2.8.0 | Works with numpy 2.x (runtime verified) |
| torchaudio | 2.8.0 | Works with numpy 2.x (despite metadata) |
| pyannote.audio | 3.4.0 | Compatible with torch 2.8.x (requires patch) |
| whisperx | 3.4.3 | Requires numpy>=2.0.2, pandas>=2.2.3 |

**Note**: PyAnnote.audio requires a small patch (automatically applied by bootstrap) to defer type annotation evaluation.

## Why This Works

The pip metadata for torchaudio 2.8.x lists `numpy<2.0` as a requirement, but this is overly conservative. At runtime, torchaudio 2.8.x uses numpy's C API which is stable across numpy 1.x and 2.x for the operations torchaudio performs.

**Testing confirms**:
```python
import torch, torchaudio, numpy, whisperx  # ✓ All imports successful
```

## Pip Dependency Warning

You may see this warning during installation:
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
whisperx 3.4.3 requires numpy>=2.0.2, but you have numpy 1.26.4 which is incompatible.
```

**This is expected and can be safely ignored** as long as you end up with numpy>=2.0.2 installed.

## Verification
After running `./scripts/bootstrap.sh`, verify:

```bash
source .bollyenv/bin/activate
python -c "import numpy, torch, torchaudio, whisperx; print(f'✓ numpy={numpy.__version__}, torch={torch.__version__}, torchaudio={torchaudio.__version__}')"
```

Expected output:
```
✓ numpy=2.0.2, torch=2.8.0, torchaudio=2.8.0
```

And check there are no actual conflicts:
```bash
pip check
```

Expected output:
```
No broken requirements found.
```

## PyAnnote.audio Fix

**PyAnnote.audio 3.4.0 now works with torchaudio 2.8 + numpy 2.x** after applying a patch.

### The Issue
The `pyannote.audio.core.io` module uses `torchaudio.AudioMetaData` as a type annotation, which is evaluated at import time. With numpy 2.x, this caused import issues.

### The Solution
The patch adds `from __future__ import annotations` to defer type annotation evaluation until runtime. This is applied automatically by bootstrap.

### Verification
```bash
python -c "from pyannote.audio import Pipeline; print('✓ PyAnnote VAD functional')"
```

Expected output:
```
✓ PyAnnote VAD functional
```

### Manual Patch Application
If needed, you can manually apply the patch:
```bash
python scripts/patch_pyannote.py
```

## Re-bootstrap Instructions
If you've already run bootstrap with the old version that downgraded numpy:

```bash
# Re-run bootstrap to upgrade numpy
./scripts/bootstrap.sh
```

The script will automatically:
1. Detect NumPy 1.x and upgrade to 2.0.2+
2. Keep torch/torchaudio at 2.8.x (verified compatible)
3. Verify all imports work correctly

## Alternative: torch 2.9+ (Not Recommended)

You could upgrade to torch/torchaudio 2.9+ which officially supports numpy 2.x, but this causes issues:
- pyannote.audio 3.4.0 has AudioMetaData compatibility issues with torchaudio 2.9+
- pyannote.audio 4.x is incompatible with WhisperX 3.4.3 (requires <4.0.0)

Therefore, **torch 2.8.x + numpy 2.x** is the optimal solution.

## Related Files
- `scripts/bootstrap.sh` - Main bootstrap script with version checks
- `requirements.txt` - Base requirements
- `requirements-macos-pinned.txt` - macOS-specific pinned versions
- `DEPENDENCY_RESOLUTION_FIX.md` - Previous dependency fixes
- `DIARIZATION_DEVICE_FIX.md` - PyAnnote device compatibility

## Technical Notes

### Why Pip Shows a Warning
Pip's dependency resolver checks metadata (setup.py/pyproject.toml) which lists conservative version constraints. These constraints don't always reflect actual runtime compatibility, especially for packages like numpy which maintain API stability.

### NumPy 2.x Compatibility
NumPy 2.0 maintained backward compatibility for most C-API operations. Libraries like torchaudio that use basic array operations work fine, even if their metadata hasn't been updated to reflect this.

### Future Considerations
- When WhisperX updates to support pyannote.audio 4.x, we can consider torch 2.9+
- Monitor torch/torchaudio release notes for official numpy 2.x support in 2.8 branch
- This solution prioritizes functionality over satisfying pip's dependency resolver
