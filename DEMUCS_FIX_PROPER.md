# Demucs Detection Fix - Proper Solution

**Date:** 2025-12-05 17:30 UTC  
**Issue:** Bootstrap-installed Demucs not detected  
**Root Cause:** Shell command check ran in wrong environment  
**Solution:** Use Python import check instead

---

## Problem Analysis

### Original Issue
```
[WARNING] Demucs is not installed
[INFO] Demucs not found. Installing...
[INFO] ✓ Demucs installed successfully
```

**Expected:** No warning (Demucs already installed by bootstrap)  
**Actual:** False positive warning → unnecessary re-install attempt

---

## Root Cause

### Original Check (WRONG)
```python
def check_demucs_installed() -> bool:
    """Check if Demucs is installed"""
    try:
        result = subprocess.run(
            ["demucs", "--help"],  # ❌ Shell command
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
```

**Problem:**
- Shell commands run in **parent environment** (not venv)
- Stage script runs in `demucs` venv (per job config)
- Check runs before venv activation OR in wrong environment
- Returns False even though Demucs IS installed in venv

---

## Solution

### New Check (CORRECT)
```python
def check_demucs_installed() -> bool:
    """Check if Demucs is installed in the current Python environment"""
    try:
        import demucs  # ✅ Python import
        return True
    except ImportError:
        return False
```

**Benefits:**
1. Checks **current Python environment** (respects venv)
2. Works correctly when stage runs in demucs venv
3. No false positives
4. Simpler and more reliable

---

## Verification

### Before Fix
```bash
$ venv/demucs/bin/python -c "import demucs; print('installed')"
installed  # ✅ Demucs IS installed

$ # But check returns False (shell command issue)
```

### After Fix
```bash
$ venv/demucs/bin/python -c "
from scripts.source_separation import check_demucs_installed
print(check_demucs_installed())
"
True  # ✅ Correctly detected
```

---

## Impact

### Previous Behavior (2 commits)
1. **Commit `e601440`** - Reduced log noise (WARNING → INFO)
   - Symptom fix: Made logs less alarming
   - Did NOT fix root cause

### Current Behavior (This commit)
2. **Commit `cf451df`** - Fixed detection logic
   - Root cause fix: Check now works correctly
   - Bootstrap-installed Demucs correctly detected
   - No false warnings or unnecessary installs

---

## Expected Results

### First Run (Clean Bootstrap)
```
✅ No Demucs warnings
✅ No auto-install attempts
✅ Demucs already available from bootstrap
✅ Stage runs immediately
```

### First Run (No Bootstrap)
```
ℹ️  Demucs not found. Installing...
✅ Demucs installed successfully
✅ Stage continues normally
```

---

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| `e601440` | Symptom | Changed WARNING → INFO (cosmetic) |
| `cf451df` | Root Cause | Fixed check logic (functional) |

**Recommendation:** This is the proper fix. The previous commit can be kept for better UX (INFO level when installing).

---

**Status:** ✅ RESOLVED  
**Test:** Re-run Test 1 to verify clean logs (no Demucs warnings)
