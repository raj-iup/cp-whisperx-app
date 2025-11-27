# Session Summary: Source Separation Default & Logger Naming

**Date:** 2025-11-21  
**Session:** Source Separation & Logger Fix

---

## 🎯 Objectives

1. **Enable source separation by default** - It was disabled, needs to be always on
2. **Verify logger naming consistency** - All logs should use `[module_name]` format

---

## ✅ Issues Fixed

### Issue 1: Source Separation Disabled by Default

**Problem:**
```
[2025-11-21 12:25:29] [source_separation] [INFO] Source separation is disabled (skipping)
[2025-11-21 12:25:29] [source_separation] [INFO] To enable, set SOURCE_SEPARATION_ENABLED=true
```

Users had to explicitly enable source separation, but it should be on by default for better audio quality.

**Root Cause:**
- `prepare-job.py`: All function signatures had `source_separation: bool = False`
- `prepare-job.sh`: `SOURCE_SEPARATION=""` (empty default)
- Argument parser: `action="store_true"` (defaults to False)

**Solution:**
Changed defaults from False to True everywhere:

1. **Python (`scripts/prepare-job.py`)**:
   ```python
   # Changed in 3 functions:
   def create_job_config(..., source_separation: bool = True, ...)
   def create_env_file(..., source_separation: bool = True, ...)
   def create_manifest(..., source_separation: bool = True, ...)
   
   # Updated argument parser:
   parser.add_argument("--source-separation", action="store_true", default=True)
   parser.add_argument("--no-source-separation", dest="source_separation", 
                       action="store_false")
   ```

2. **Bash (`prepare-job.sh`)**:
   ```bash
   # Changed default:
   SOURCE_SEPARATION="default"  # instead of ""
   
   # Added --no-source-separation handling:
   --no-source-separation)
       SOURCE_SEPARATION="false"
       ;;
   
   # Simplified logic:
   if [ "$SOURCE_SEPARATION" = "default" ]; then
       SOURCE_SEPARATION="true"
   fi
   ```

### Issue 2: Logger Naming Consistency

**Requirement:**
All loggers should use format: `[timestamp] [module_name] [level] message`

**Status:** ✅ Already Working Correctly

Verified that all loggers use `PipelineLogger(module_name="...")` or `get_stage_logger("...")`:
- `shared/logger.py` implements consistent formatting
- Log format: `"[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"`
- All scripts properly initialize loggers with module names

Examples:
- `[source_separation]` - Source separation script
- `[pipeline]` - Main pipeline orchestrator
- `[indictrans2]` - IndicTrans2 translation stages
- `[nllb]` - NLLB translation stages

---

## 📝 Files Modified

### 1. `scripts/prepare-job.py`
**Changes:**
- Line 173: `source_separation: bool = True` (was False)
- Line 240: `source_separation: bool = True` (was False)  
- Line 383: `source_separation: bool = True` (was False)
- Lines 498-508: Added `--no-source-separation` argument
- Line 499: Updated help text to show "[DEFAULT]"

### 2. `prepare-job.sh`
**Changes:**
- Line 63: Updated help text to show "[DEFAULT]"
- Line 64: Added `--no-source-separation` help
- Line 122: Changed `SOURCE_SEPARATION="default"`
- Lines 174-177: Added `--no-source-separation` case
- Lines 324-333: Simplified default logic (removed Indic auto-enable)

---

## 🧪 Testing

### Test 1: Default Behavior (Enabled)
```bash
$ ./prepare-job.sh --media movie.mp4 --workflow subtitle \
    --source-lang hi --target-langs en
```
**Result:** ✅
```
🎵 Source separation: ENABLED (balanced quality)
   Background music will be removed from audio
```
**Config:** `{"enabled": true, "quality": "balanced"}`

### Test 2: Explicit Disable
```bash
$ ./prepare-job.sh --media movie.mp4 --workflow subtitle \
    --source-lang hi --target-langs en --no-source-separation
```
**Result:** ✅
- No "Source separation: ENABLED" message shown
**Config:** `{"enabled": false, "quality": "balanced"}`

### Test 3: Backward Compatible
```bash
$ ./prepare-job.sh --media movie.mp4 --workflow subtitle \
    --source-lang hi --target-langs en --source-separation
```
**Result:** ✅ Still works (flag is now redundant but harmless)

### Test 4: Help Text
```bash
$ ./prepare-job.sh --help | grep -A 2 "source-separation"
```
**Result:** ✅
```
--source-separation         Enable source separation [DEFAULT]
--no-source-separation      Disable source separation
--separation-quality LEVEL  Source separation quality: fast, balanced, quality
```

---

## 📊 Impact Analysis

### For Users
✅ **Better default experience**
- Source separation now enabled by default
- Better audio quality for all transcriptions
- Background music automatically removed
- Can still disable if needed with `--no-source-separation`

✅ **Clearer logging**
- All logs show module name in consistent format
- Easy to identify which component is logging

### For Developers
✅ **Consistent codebase**
- All function signatures use `source_separation: bool = True`
- Bash and Python have matching defaults
- Clear logger naming throughout

✅ **Backward compatible**
- `--source-separation` flag still works
- No breaking changes to existing scripts
- Old jobs continue to work

---

## 🎓 Key Learnings

1. **Default values matter** - Users shouldn't have to enable critical features
2. **Consistency is key** - Bash wrapper and Python script must match
3. **Testing is essential** - Verify both enable and disable paths
4. **Logger naming** - Using `module_name` parameter ensures consistent log formatting

---

## ✅ Verification Checklist

- [x] Source separation enabled by default in Python
- [x] Source separation enabled by default in Bash
- [x] `--no-source-separation` flag works
- [x] Logger naming consistent across all modules
- [x] Backward compatible with `--source-separation`
- [x] Help text updated
- [x] Tested with real job creation
- [x] Job configuration files correct

---

## 📚 Related Documentation

- [Source Separation Feature](../user-guide/features/source-separation.md)
- [Prepare Job Guide](../user-guide/prepare-job.md)
- [Development Process](../PROCESS.md)

---

**Session Status: COMPLETE ✅**  
**All issues resolved and tested successfully**
