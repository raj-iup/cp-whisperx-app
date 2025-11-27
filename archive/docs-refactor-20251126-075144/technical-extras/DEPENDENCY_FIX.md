# Dependency Fix - pythonjsonlogger Missing

**Date:** 2024-11-25  
**Issue:** ModuleNotFoundError: No module named 'pythonjsonlogger'  
**Status:** ✅ **FIXED**

---

## 🔴 Problem

The `hybrid_translator.py` script failed with:
```
ModuleNotFoundError: No module named 'pythonjsonlogger'
```

**Root Cause:** The `python-json-logger` package (which provides `pythonjsonlogger`) was only specified in `requirements-common.txt`, but **not installed in specialized environments** like:
- `venv/llm` (LLM translation)
- `venv/pyannote` (Voice Activity Detection)
- `venv/demucs` (Source separation)
- `venv/mlx` (MLX Whisper for Apple Silicon)
- `venv/whisperx` (WhisperX transcription)

---

## ✅ Solution

### 1. **Updated All Requirements Files**

Added `python-json-logger>=2.0.0` to all environment requirement files:

- ✅ `requirements-llm.txt`
- ✅ `requirements-pyannote.txt`
- ✅ `requirements-demucs.txt`
- ✅ `requirements-mlx.txt`
- ✅ `requirements-whisperx.txt`

**Note:** Already present in:
- ✅ `requirements-common.txt`
- ✅ `requirements-indictrans2.txt`
- ✅ `requirements-nllb.txt`

### 2. **Installed Missing Dependency**

Ran pip install in all affected environments:
```bash
venv/llm/bin/pip install python-json-logger
venv/pyannote/bin/pip install python-json-logger
venv/demucs/bin/pip install python-json-logger
venv/mlx/bin/pip install python-json-logger
venv/whisperx/bin/pip install python-json-logger
```

---

## ✅ Verification

Tested all environments - **ALL PASS:**

```
demucs         : ✓
mlx            : ✓
whisperx       : ✓
pyannote       : ✓
llm            : ✓
indictrans2    : ✓
nllb           : ✓
```

---

## 📝 Files Modified

1. `requirements-llm.txt` - Added `python-json-logger>=2.0.0`
2. `requirements-pyannote.txt` - Added `python-json-logger>=2.0.0`
3. `requirements-demucs.txt` - Added `python-json-logger>=2.0.0`
4. `requirements-mlx.txt` - Added `python-json-logger>=2.0.0`
5. `requirements-whisperx.txt` - Added `python-json-logger>=2.0.0`

---

## 🎯 Why This Matters

The `shared.logger.PipelineLogger` class is imported by **ALL pipeline scripts**:
- `hybrid_translator.py` (Stage 7: Translation)
- `source_separation.py` (Stage 2: Source Separation)
- ASR scripts (Stage 4: Transcription)
- Subtitle generation scripts (Stage 8)
- And more...

Without `python-json-logger`, **ANY script using PipelineLogger would fail** in specialized environments.

---

## 🔄 Pattern: Core Dependencies

Identified a **pattern** - certain dependencies are **core to all environments**:

```python
# Core dependencies (should be in ALL environment requirement files)
python-json-logger>=2.0.0   # For PipelineLogger
python-dotenv>=1.0.0         # For .env configuration
```

These should be added to **every** `requirements-*.txt` file since:
1. **Logger** - Used by all scripts for logging
2. **Dotenv** - Used by all scripts for configuration

---

## 🚀 Future Prevention

### Recommendation: Add to Bootstrap Scripts

Consider updating `bootstrap.sh` and `bootstrap.ps1` to verify core dependencies are installed in all environments during setup.

### Example Check:
```bash
for env in .venv-*; do
    $env/bin/python -c "from pythonjsonlogger import jsonlogger" || {
        echo "❌ Missing python-json-logger in $env"
        exit 1
    }
done
```

---

## ✅ Status

**Issue:** RESOLVED ✅  
**Testing:** Hybrid translation should now work  
**Ready:** Yes, all environments patched

---

**Fixed by:** GitHub Copilot CLI  
**Date:** 2024-11-25  
**Impact:** All pipeline stages using specialized environments
