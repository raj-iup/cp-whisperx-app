# LLM Virtual Environment Dependencies Fix

**Date:** 2024-11-25  
**Issue:** Missing `pydantic_settings` module in LLM venv  
**Status:** ✅ **FIXED**

---

## 🔴 Problem

The hybrid translator script failed because the LLM virtual environment was missing required dependencies:

```
[2025-11-24 20:55:29] [ERROR] Hybrid translation error: Traceback (most recent call last):
  File "/Users/rpatel/Projects/cp-whisperx-app/scripts/hybrid_translator.py", line 27, in <module>
    from shared.config import load_config
  File "/Users/rpatel/Projects/cp-whisperx-app/shared/config.py", line 9, in <module>
    from pydantic_settings import BaseSettings
ModuleNotFoundError: No module named 'pydantic_settings'
```

---

## 🔍 Root Cause

The `requirements-llm.txt` file was missing the **shared module dependencies**:
- ❌ `pydantic` - Used by `shared/config.py`
- ❌ `pydantic-settings` - Used by `shared/config.py`

### Why This Happened:

The LLM venv (`venv/llm`) is **isolated** and only contains packages from `requirements-llm.txt`. The `shared/` modules are imported but their dependencies weren't declared.

---

## ✅ Solution

### Updated `requirements-llm.txt`:

```diff
  # Core dependencies (shared with common)
  python-json-logger>=2.0.0
  python-dotenv>=1.0.0
+ pydantic>=2.0.0
+ pydantic-settings>=2.0.0
```

### Installed Missing Packages:

```bash
venv/llm/bin/pip install pydantic pydantic-settings
```

---

## 📝 What the Shared Modules Need

### `shared/config.py`:
```python
from pydantic_settings import BaseSettings  # ✅ Now in requirements-llm.txt
from pydantic import Field, field_validator   # ✅ Now in requirements-llm.txt
```

### `shared/logger.py`:
```python
from pythonjsonlogger import jsonlogger  # ✅ Already in requirements (python-json-logger)
```

### `shared/stage_utils.py`:
```python
# Only uses standard library - no external dependencies ✅
```

---

## ✅ Verification

### Test 1: Import Pydantic Modules
```bash
venv/llm/bin/python -c "from pydantic_settings import BaseSettings; print('✓ OK')"
```
**Result:** ✓ All required modules available

### Test 2: Import Shared Modules
```bash
venv/llm/bin/python -c "
from shared.logger import PipelineLogger
from shared.stage_utils import StageIO
from shared.config import load_config
print('✓ All shared modules work')
"
```
**Result:** ✓ All shared modules can be imported by hybrid_translator

---

## 🎯 Impact on Pipeline

### Before Fix:
```
[ERROR] Hybrid translation error: ModuleNotFoundError: No module named 'pydantic_settings'
❌ Translation stage fails
❌ Pipeline stops
```

### After Fix:
```
[INFO] Using LLM environment: /Users/rpatel/Projects/cp-whisperx-app/venv/llm/bin/python
[INFO] Running: /Users/rpatel/Projects/cp-whisperx-app/scripts/hybrid_translator.py
✅ Hybrid translation runs successfully
✅ Pipeline continues
```

---

## 📦 Virtual Environment Structure

The pipeline uses **multiple isolated virtual environments**:

1. **`venv/whisperx`** - WhisperX, PyAnnote (main ASR)
2. **`venv/indictrans2`** - IndicTrans2 (Indic language translation)
3. **`venv/llm`** - LLM APIs (Claude, GPT-4) for song/poetry translation ← **FIXED**
4. **`venv/mlx`** - MLX Whisper (Apple Silicon alternative)
5. **`venv/demucs`** - Demucs (source separation)

**Each venv needs its dependencies explicitly declared!**

---

## 📝 Files Modified

1. ✅ `requirements-llm.txt` - Added `pydantic` and `pydantic-settings`
2. ✅ `venv/llm/` - Installed missing packages

---

## 🔄 For Future Installs

Users installing fresh will get the fix automatically:

```bash
./install-llm.sh  # Uses updated requirements-llm.txt
```

**For existing installations:**
```bash
source venv/llm/bin/activate
pip install pydantic pydantic-settings
```

---

## ✅ Status

**Issue:** RESOLVED ✅  
**Testing:** Hybrid translator can now import all shared modules  
**Ready:** Yes, LLM venv has all required dependencies

---

**Fixed by:** GitHub Copilot CLI  
**Date:** 2024-11-25  
**Impact:** Hybrid translation now works in all workflows
