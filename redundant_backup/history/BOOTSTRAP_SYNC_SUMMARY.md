# Bootstrap Script Synchronization Summary

## Changes Made

The **bash bootstrap script** (`scripts/bootstrap.sh`) has been synchronized with the **PowerShell version** (`scripts/bootstrap.ps1`) to ensure feature parity across platforms.

## Added Features to Bash Script

### 1. **NumPy/PyTorch/Torchaudio Version Management** ✅
- **Auto-detects** NumPy 2.x and downgrades to <2.0 (required for torchaudio 2.8.x)
- **Auto-detects** torch/torchaudio 2.9.x and downgrades to 2.8.x (required for PyAnnote 3.x)
- **Validates** version compatibility before continuing
- **Logs** detailed version information

```bash
# Example output:
✓ Versions: numpy 1.26.4 | torch 2.8.0 | torchaudio 2.8.0
→ Compatible with pyannote.audio 3.x
```

### 2. **spaCy Model Download Section** ✅
- **Downloads** `en_core_web_trf` (transformer model, ~500MB) for best NER accuracy
- **Falls back** to `en_core_web_sm` if transformer fails
- **Checks** if already installed to avoid re-downloading
- **Required** for Pre-NER and Post-NER stages

```bash
# Tries transformer model first (best accuracy)
python -m spacy download en_core_web_trf

# Falls back to small model if needed
python -m spacy download en_core_web_sm
```

### 3. **PyAnnote.audio Verification** ✅
- **Tests** actual import to catch compatibility issues
- **Suppresses** known deprecation warnings (speechbrain, pytorch_lightning)
- **Detects** AudioMetaData errors (torchaudio 2.9 compatibility issue)
- **Provides** actionable error messages

```bash
# Example verification:
✓ PyAnnote.audio: Compatible and working
  → speechbrain patch applied successfully
  → torchaudio 2.8.x compatible
```

### 4. **TORCH_HOME Environment Variable** ✅
- **Sets** `TORCH_HOME` to `.cache/torch` in project directory
- **Avoids** `/app/LLM` cache path issues in native mode
- **Creates** directory if missing
- **Persists** for session

```bash
export TORCH_HOME="$PROJECT_ROOT/.cache/torch"
```

### 5. **Directory Structure Alignment** ✅
- **Removed** `jobs/` and `shared-model-and-cache/` from auto-creation
- **Matches** PowerShell version: `in/`, `out/`, `logs/`, `config/`
- **Consistent** across platforms

### 6. **Enhanced Completion Summary** ✅
Updated final output to show all installed components:

```
✅ Environment ready!

What's been set up:
  ✓ Python virtual environment (.bollyenv/)
  ✓ 70+ Python packages installed
  ✓ torch 2.8.x / torchaudio 2.8.x (pyannote compatible)
  ✓ Hardware capabilities detected & cached
  ✓ Required directories created
  ✓ FFmpeg validated
  ✓ ML models pre-downloaded
  ✓ spaCy NER models installed
  ✓ PyAnnote.audio verified working
```

## Platform-Specific Features Retained

### Windows (PowerShell Only)
- **Developer Mode Check**: Detects Windows Developer Mode for symlink support
  - Warns if disabled (affects HuggingFace cache efficiency)
  - Not applicable to Linux/macOS (native symlink support)

### Both Platforms
- All other features are now **identical** between PowerShell and bash versions

## Benefits

### 1. **Prevents Runtime Failures**
- Catches version incompatibilities during bootstrap
- Ensures PyAnnote works before pipeline execution
- Downloads all required models upfront

### 2. **Consistent Experience**
- Windows and Linux/macOS users get same features
- Same validation steps across platforms
- Same error messages and guidance

### 3. **Better Error Handling**
- Clear messages for version conflicts
- Automatic downgrades when needed
- Fallback options for model downloads

### 4. **Time Savings**
- Catches issues during bootstrap (5-10 min) vs pipeline execution (hours)
- Pre-downloads models in parallel
- Validates everything before starting work

## Testing Recommendations

### On Linux/macOS
```bash
# Clean test
rm -rf .bollyenv
./scripts/bootstrap.sh

# Expected: Should complete successfully with all checks passing
```

### On Windows
```powershell
# Clean test
Remove-Item -Recurse -Force .bollyenv
.\scripts\bootstrap.ps1

# Expected: Should complete successfully with all checks passing
```

## Commits

1. **Diarization Device Fix** (`7c359f6`)
   - Fixed device type error
   - Added auto-detection

2. **Bootstrap Sync** (`e22a122`)
   - Synced bash with PowerShell
   - Added 172 lines, removed 37 lines

## Files Changed
- ✅ `scripts/bootstrap.sh` - Updated with all PowerShell features
- ✅ `scripts/bootstrap.ps1` - Reference implementation (unchanged)
- ✅ `scripts/diarization.py` - Device fix from previous commit

## Status
✅ **COMPLETE** - Both bootstrap scripts are now functionally equivalent (minus Windows-specific features)
