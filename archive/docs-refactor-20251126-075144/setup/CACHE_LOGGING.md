# Pipeline Cache Logging

**Date:** 2024-11-25  
**Feature:** Cache utilization reporting in pipeline logs

---

## Overview

The pipeline now logs cache configuration and usage information to help users verify that models are being loaded from local cache rather than downloading from the internet.

---

## What Gets Logged

### 1. Cache Configuration (Always Logged)

At pipeline startup, the following is logged:

```
📦 Model cache configuration:
  HuggingFace cache: .cache/huggingface (4 models cached)
  PyTorch cache: .cache/torch
  MLX cache: .cache/mlx
```

This shows:
- Cache directories being used
- Number of models cached in HuggingFace hub
- Status of all cache locations

### 2. Cache Paths (Debug Mode Only)

When running with `--debug`, each stage execution logs cache paths:

```
[CACHE] Using local cache directories:
[CACHE]   TORCH_HOME=.cache/torch
[CACHE]   HF_HOME=.cache/huggingface
[CACHE]   MLX_CACHE_DIR=.cache/mlx
```

This confirms environment variables are set correctly for each subprocess.

---

## How to Check Cache Usage

### Standard Mode

```bash
# Run pipeline normally
./run-pipeline.sh -j <job-id>

# Check log for cache info
cat out/<job-dir>/logs/pipeline.log | grep -A 5 "Model cache"
```

**Expected Output:**
```
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (4 models cached)
[INFO]   PyTorch cache: .cache/torch
[INFO]   MLX cache: .cache/mlx
```

### Debug Mode

```bash
# Run pipeline with debug logging
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi --debug
./run-pipeline.sh -j <job-id>

# Check log for detailed cache info
cat out/<job-dir>/logs/pipeline.log | grep -i cache
```

**Expected Output:**
```
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (4 models cached)
[INFO]   PyTorch cache: .cache/torch
[INFO]   MLX cache: .cache/mlx
[CACHE] Using local cache directories:
[CACHE]   TORCH_HOME=.cache/torch
[CACHE]   HF_HOME=.cache/huggingface
[CACHE]   MLX_CACHE_DIR=.cache/mlx
```

---

## Verifying Offline Execution

### Test 1: Check Cache Count

```bash
# Before running pipeline
ls .cache/huggingface/hub/ | grep "^models--" | wc -l
# Should show: 3-4 models

# Run pipeline
./run-pipeline.sh -j <job-id>

# Check log
grep "models cached" out/<job-dir>/logs/pipeline.log
# Should show: "4 models cached" or similar
```

### Test 2: Monitor Network Activity

```bash
# Turn off Wi-Fi/network
# Run pipeline
./run-pipeline.sh -j <job-id>

# Check if it completes successfully
# If models are cached: ✅ Success
# If not cached: ❌ Network error
```

### Test 3: Check for Download Messages

```bash
# Run pipeline
./run-pipeline.sh -j <job-id>

# Check for download activity
grep -i "download" out/<job-dir>/logs/pipeline.log

# If using cache: No "downloading" messages
# If not cached: Will show download progress
```

---

## Cache Status Messages

### ✅ Good (Models Cached)

```
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (4 models cached)
```

**Meaning:** 4 models found in cache, pipeline will use them

### ⚠️ Warning (Empty Cache)

```
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (empty)
```

**Meaning:** No models cached, will download on first use

**Action:** Run `./cache-models.sh --all` to pre-cache models

### ❌ Error (Cache Not Found)

```
[WARNING]   HuggingFace cache not found: .cache/huggingface
```

**Meaning:** Cache directory doesn't exist

**Action:** 
1. Run `./bootstrap.sh` to create cache directories
2. OR manually create: `mkdir -p .cache/huggingface`

---

## Implementation Details

### Files Modified

1. **shared/environment_manager.py** (lines 189-218)
   - Added cache path logging in debug mode
   - Logs when DEBUG_MODE=true

2. **scripts/run-pipeline.py** (lines 110-137)
   - Added cache configuration logging
   - Shows number of cached models
   - Always logs at startup

### Environment Variables Set

For every stage execution, these are automatically set:

```python
env["TORCH_HOME"] = ".cache/torch"
env["HF_HOME"] = ".cache/huggingface"
env["TRANSFORMERS_CACHE"] = ".cache/huggingface"
env["MLX_CACHE_DIR"] = ".cache/mlx"
```

### Debug Mode Activation

```bash
# Method 1: Via prepare-job
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi --debug

# Method 2: Manually edit job.json
# Set "debug": true in out/<job-dir>/job.json

# Method 3: Set environment variable
export DEBUG_MODE=true
./run-pipeline.sh -j <job-id>
```

---

## Examples

### Example 1: First Run (No Cache)

```bash
# Fresh bootstrap, no models cached
./bootstrap.sh --skip-cache

# Run pipeline
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>
```

**Log Output:**
```
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (empty)
[INFO] Loading WhisperX model...
Downloading model files: 100%|████████| 3.09G/3.09G [05:32<00:00, 9.83MB/s]
```

### Example 2: With Pre-cached Models

```bash
# Bootstrap with model caching
./bootstrap.sh --cache-models

# Run pipeline
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>
```

**Log Output:**
```
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (4 models cached)
[INFO] Loading WhisperX model...
[INFO] Model loaded from cache
```

### Example 3: Debug Mode

```bash
# Run with debug logging
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi --debug
./run-pipeline.sh -j <job-id>
```

**Log Output:**
```
[INFO] 🐛 DEBUG MODE ENABLED - Verbose logging active
[INFO] 📦 Model cache configuration:
[INFO]   HuggingFace cache: .cache/huggingface (4 models cached)
[INFO]   PyTorch cache: .cache/torch
[INFO]   MLX cache: .cache/mlx
[CACHE] Using local cache directories:
[CACHE]   TORCH_HOME=.cache/torch
[CACHE]   HF_HOME=.cache/huggingface
[CACHE]   MLX_CACHE_DIR=.cache/mlx
```

---

## Troubleshooting

### Cache Not Showing Up

**Issue:** Log shows "empty" even though models are cached

**Check:**
```bash
# Verify models exist
ls .cache/huggingface/hub/ | grep "^models--"

# Check permissions
ls -la .cache/huggingface/hub/
```

**Fix:** Ensure cache directory structure is correct

### Cache Path Not Set

**Issue:** Models downloading despite cache existing

**Check:**
```bash
# Run in debug mode
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi --debug
./run-pipeline.sh -j <job-id>

# Check if [CACHE] lines appear
grep "\[CACHE\]" out/<job-dir>/logs/pipeline.log
```

**Fix:** Verify hardware_cache.json exists:
```bash
cat config/hardware_cache.json | grep -A 10 '"cache"'
```

### Wrong Cache Location

**Issue:** Models cached in ~/.cache instead of .cache/

**Check:**
```bash
# Check environment variables in log
grep "HF_HOME\|TORCH_HOME" out/<job-dir>/logs/pipeline.log
```

**Fix:** Re-run bootstrap to recreate hardware_cache.json:
```bash
./bootstrap.sh --force
```

---

## Benefits

### For Users

- ✅ **Visibility:** Can see if cache is being used
- ✅ **Debugging:** Easy to diagnose cache issues
- ✅ **Verification:** Confirm offline execution works

### For Developers

- ✅ **Transparency:** Clear logging of cache paths
- ✅ **Debugging:** Track cache configuration per stage
- ✅ **Monitoring:** Count cached models at startup

---

## Summary

**Feature:** Pipeline now logs cache configuration and usage

**When Logged:**
- Cache configuration: Always (at startup)
- Cache paths: Debug mode only (per stage)

**How to Use:**
```bash
# Standard: See cache status
./run-pipeline.sh -j <job-id>
cat out/<job-dir>/logs/pipeline.log | grep "cache"

# Debug: See detailed cache info
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi --debug
./run-pipeline.sh -j <job-id>
cat out/<job-dir>/logs/pipeline.log | grep -i cache
```

**Files Modified:**
- `shared/environment_manager.py` - Added debug cache logging
- `scripts/run-pipeline.py` - Added startup cache info

---

**Date:** 2024-11-25  
**Status:** ✅ Implemented  
**Feature:** Cache logging for better visibility and debugging
