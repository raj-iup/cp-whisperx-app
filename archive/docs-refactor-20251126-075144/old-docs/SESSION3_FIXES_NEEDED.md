# Session 3 - Critical Fixes Required

**Date**: November 26, 2025  
**Status**: 🔧 IN PROGRESS

## Issues Found

### 1. Test Script Issues ✅ FIXED
- **Issue**: grep -P not available on macOS
- **Issue**: Job ID extraction failing with sed
- **Issue**: Path extraction has extra whitespace
- **Fix**: Replace sed with awk for macOS compatibility
- **Status**: ✅ Fixed in test-glossary-quickstart.sh

### 2. Target Language Missing ⚠️ CRITICAL
- **Error**: `KeyError: 'target_language'` in hybrid_translation stage
- **Root Cause**: job.json has `target_languages` (array) but code expects `target_language` (string)
- **Location**: Line 1765-1768 in run-pipeline.py already handles this correctly
- **Real Issue**: Code at line 1822 uses `target_lang` variable which might be None
- **Fix Needed**: Ensure target_lang is always set before use

### 3. Recursive Function Call ⚠️  
- **Error**: `RecursionError: maximum recursion depth exceeded` in `_get_target_language`
- **Location**: Line 247 in run-pipeline.py calls itself
- **Status**: NEEDS INVESTIGATION - function looks correct at line 252-269

### 4. Stage Directory Issues
- **Issue**: Both `09_hybrid_translation` and `09_translation` exist
- **Issue**: Stage 03_glossary_load is correct but shows as disabled
- **Root Cause**: prepare-job creates 09_translation, pipeline creates 09_hybrid_translation
- **Fix Needed**: Remove duplicate directory creation

### 5. TMDB Glossary Always Disabled
- **Issue**: Logs show "Glossary system is disabled (skipping)" 
- **Root Cause**: GLOSSARY_CACHE_ENABLED check at line 805
- **Location**: _stage_glossary_load() in run-pipeline.py
- **Status**: Checking environment variable setting

### 6. Subtitle Generation Error
- **Error**: `shutil.move() source and destination are the same file`
- **Location**: subtitle_generation stage
- **Fix Needed**: Check if source != destination before moving

### 7. Warnings in Logs
- **WARNING**: TMDB enrichment completed but no output file found
- **WARNING**: CPU device does not support float16 efficiently (auto-adjusted to int8)
- **WARNING**: PyAnnote model version mismatch
- **Status**: Non-critical but should be addressed

## Fix Priority

### P0 - Critical (Blocks Pipeline)
1. ✅ Fix test script job ID extraction
2. ⚠️  Fix target_language KeyError
3. ⚠️  Fix recursive function call
4. ⚠️  Fix subtitle same-file move error

### P1 - High (Affects Quality)
5. Fix TMDB glossary disabled issue
6. Remove duplicate translation directories
7. Fix TMDB output file warning

### P2 - Medium (Warnings)
8. Fix float16/int8 warning (informational)
9. Fix PyAnnote version warning (informational)

## Detailed Fix Plan

### Fix 1: Test Script ✅ DONE
```bash
# Changed from:
ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job created:" | sed 's/.*Job created: //' | awk '{print $1}')

# To (macOS compatible):
ACTUAL_JOB_ID=$(echo "$PREP_OUTPUT" | grep "Job created:" | awk '{print $3}')
```

### Fix 2: Target Language ERROR
**File**: scripts/run-pipeline.py:1765-1772

**Current Code**:
```python
target_lang = self._get_target_language()
if not target_lang:
    target_langs = self.job_config.get("target_languages", [])
    target_lang = target_langs[0] if target_langs else None

if not target_lang:
    raise ValueError("No target language specified in job config")
```

**Issue**: This code looks correct! Need to find actual error location.

**Action**: Search for other places where target_language is accessed directly.

### Fix 3: Recursive Call Investigation
**File**: scripts/run-pipeline.py:252

**Current Code**:
```python
def _get_target_language(self) -> Optional[str]:
    """Get target language from job config"""
    # Try singular form first (legacy)
    target_lang = self.job_config.get("target_language")
    if target_lang:
        return target_lang
    
    # Try plural form (new format)
    target_langs = self.job_config.get("target_languages", [])
    if target_langs:
        return target_langs[0]
    
    return None
```

**Issue**: No recursive call visible! Error says line 247 but function is at 252.

**Hypothesis**: There might be a backup file or different version being executed.

**Action**: Check for .pyc files or search for other definitions.

### Fix 4: Duplicate Translation Directories
**File**: scripts/prepare-job.py (stage directory creation)

**Current**:
```python
stage_dirs = [
    "09_translation",      # Created by prepare-job
    ...
]
```

**Pipeline creates**:
```python
output_dir = self._stage_path("translation")  # Creates 09_hybrid_translation
```

**Fix**: Update prepare-job.py to create directories matching actual stage names.

### Fix 5: Glossary Disabled Issue
**File**: scripts/run-pipeline.py:805

**Current Check**:
```python
glossary_enabled = self.env_config.get("GLOSSARY_CACHE_ENABLED", "true").lower() == "true"
```

**Issue**: Job-specific .env file sets `GLOSSARY_CACHE_ENABLED=false` for baseline test.

**Status**: WORKING AS DESIGNED! Test script intentionally disables it for baseline.

**Action**: Ensure glossary test enables it correctly.

### Fix 6: Subtitle Same-File Error
**File**: scripts/run-pipeline.py (subtitle_generation stage)

**Error**:
```
PosixPath('.../Jaane Tu Ya Jaane Na.en.srt') and PosixPath('.../Jaane Tu Ya Jaane Na.en.srt') are the same file
```

**Action**: Need to find subtitle_generation code and add source != destination check.

## Implementation Steps

1. ✅ Fix test script (DONE)
2. Search for target_language KeyError source
3. Search for recursive call source (check for backup files)
4. Find and fix subtitle_generation same-file error
5. Update stage directory creation logic
6. Test full pipeline with fixes

## Testing Checklist

After fixes:
- [ ] Test script extracts job ID correctly
- [ ] Baseline test completes without errors
- [ ] Glossary test loads glossary correctly
- [ ] No recursive errors
- [ ] Subtitles generate correctly
- [ ] Cache test works

## Status

**Current**: Fixing test script and investigating critical errors  
**Next**: Find and fix target_language and recursive errors  
**Blocker**: Need to locate exact source of errors in logs

---

**Last Updated**: 2025-11-26  
**Progress**: 20% (test script fixed, investigating pipeline errors)
