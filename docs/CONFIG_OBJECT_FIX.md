# Config Object Type Fix

**Date:** October 29, 2025  
**Status:** ✅ **FIXED**

---

## Issue

Pipeline error:
```
[ERROR] TMDB enrichment failed: 'Config' object has no attribute 'load_secrets'
```

**Cause:** Using wrong method to access secrets from Config object

---

## Root Cause Analysis

### Two Different Config Classes

**1. `shared/config.py` - PipelineConfig (Pydantic)**
```python
class PipelineConfig(BaseSettings):
    def load_secrets(self) -> dict:  # Returns dict
        secrets_file = Path(self.secrets_path)
        if secrets_file.exists():
            with open(secrets_file, 'r') as f:
                return json.load(f)
        return {}
```

**2. `scripts/config_loader.py` - Config (Custom)**
```python
class Config:
    def _load_secrets(self):  # Private, called in __init__
        with open(self.secrets_file) as f:
            self._secrets = json.load(f)
    
    def get_secret(self, key: str) -> str:  # Public method
        if key not in self._secrets:
            raise KeyError(f"Secret '{key}' not found")
        return self._secrets[key]
```

**Issue:** 
- `run_pipeline_arch.py` uses `scripts.config_loader.Config`
- We tried to call `config.load_secrets()` (doesn't exist)
- Should use `config.get_secret()` instead

---

## Fixes Applied

### Fix 1: Use Correct Config Method

**File:** `run_pipeline_arch.py` (Lines 180-194)

**Before:**
```python
if not tmdb_api_key:
    secrets = config.load_secrets()  # ❌ Method doesn't exist
    tmdb_api_key = secrets.get("tmdb_api_key")
```

**After:**
```python
if not tmdb_api_key:
    try:
        tmdb_api_key = config.get_secret("tmdb_api_key")
    except KeyError:
        try:
            tmdb_api_key = config.get_secret("TMDB_API_KEY")
        except KeyError:
            pass
```

---

### Fix 2: Correct Project Root Detection

**File:** `scripts/config_loader.py` (Line 23)

**Before:**
```python
# Goes up 3 levels: scripts/ -> cp-whisperx-app/ -> Projects/ -> /Users/rpatel/
project_root = Path(__file__).parent.parent.parent
# Result: /Users/rpatel/Projects/config/.env ❌
```

**After:**
```python
# Goes up 1 level: scripts/ -> cp-whisperx-app/
project_root = Path(__file__).parent.parent
# Result: /Users/rpatel/Projects/cp-whisperx-app/config/.env ✅
```

---

## Config API Reference

### `scripts.config_loader.Config`

**Loading:**
```python
from scripts.config_loader import Config

config = Config()
# Automatically loads both .env and secrets.json
```

**Get Config Value:**
```python
value = config.get("KEY_NAME", default=None)
# Returns from config/.env
```

**Get Secret:**
```python
secret = config.get_secret("secret_name")
# Returns from config/secrets.json
# Raises KeyError if not found
```

---

## Testing

### Test Config Loading
```bash
python3 << 'PYEOF'
from scripts.config_loader import Config

config = Config()

# Test TMDB API key
api_key = config.get_secret("tmdb_api_key")
print(f"✅ TMDB API Key: {api_key[:10]}...")

# Test HF token
hf_token = config.get_secret("hf_token")
print(f"✅ HF Token: {hf_token[:10]}...")
PYEOF
```

**Expected Output:**
```
✅ TMDB API Key: ea32848e3a...
✅ HF Token: hf_yKUtvKh...
```

---

## Expected Pipeline Behavior

### Stage 2: TMDB (Fixed)

```
[INFO] Era detected: 2000s
[INFO] Searching TMDB for: Jaane Tu Ya Jaane Na (2006)
[INFO] TMDB enriched: 20 cast, 10 crew
[INFO] TMDB metadata saved: out/Movie/metadata/tmdb_data.json
[INFO] ✓ TMDB stage complete
```

### What Changed

**Before:**
- ❌ AttributeError: 'Config' object has no attribute 'load_secrets'
- ❌ TMDB stage fails

**After:**
- ✅ Correctly calls `config.get_secret()`
- ✅ Successfully loads TMDB API key
- ✅ TMDB enrichment works

---

## Config Class Comparison

| Feature | shared/config.py | scripts/config_loader.py |
|---------|------------------|-------------------------|
| **Type** | Pydantic BaseSettings | Custom class |
| **Used By** | Containers | Orchestrator |
| **Secrets Method** | `load_secrets()` → dict | `get_secret(key)` → str |
| **Secrets Loading** | On-demand | Automatic in `__init__` |
| **Config Access** | `config.get(key)` | `config.get(key)` |
| **Secrets Access** | `secrets = load_secrets()` | `config.get_secret(key)` |

---

## Summary

✅ **Correct method used** - `get_secret()` instead of `load_secrets()`  
✅ **Project root fixed** - Correct path detection  
✅ **API key loading** - Successfully retrieves from secrets.json  
✅ **Error handling** - Try/except for both key variants  

**Status:** Config loading fully operational

---

**Fixed:** October 29, 2025  
**Ready for:** Full pipeline execution
