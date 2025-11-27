# MLX Installation - Complete Guide

**Last Updated:** 2025-11-19  
**Platform:** macOS (Apple Silicon - M1/M2/M3 only)  
**Status:** ✅ Verified & Documented

---

## Overview

MLX provides **6-8x faster transcription** on Apple Silicon by using Metal Performance Shaders (MPS) for GPU acceleration.

---

## Key Facts

### Virtual Environment

**IMPORTANT:** MLX uses the **SAME** `.bollyenv` virtual environment as the rest of the pipeline.

- ✅ **No separate environment needed**
- ✅ All packages coexist in `.bollyenv`
- ✅ No environment switching required
- ✅ `install-mlx.sh` adds packages to existing `.bollyenv`

### Dependencies

MLX installation adds these packages to `.bollyenv`:
- `mlx` - MLX framework for Apple Silicon
- `mlx-whisper` - Whisper implementation using MLX

### Configuration

After MLX installation, bootstrap updates:
- `out/hardware_cache.json` - Sets GPU type to "mps" and backend to "mlx"

This tells the pipeline to use MLX for GPU acceleration.

---

## Installation Methods

### Method 1: Automatic (Recommended)

```bash
./bootstrap.sh
```

**What happens:**
1. Bootstrap detects Apple Silicon (M1/M2/M3)
2. Automatically installs `mlx-whisper` into `.bollyenv`
3. Creates `out/hardware_cache.json` with MPS/MLX config
4. Pipeline is ready to use GPU acceleration

**Result:** MLX is installed and configured automatically! ✅

---

### Method 2: Manual Installation

Use this if:
- Bootstrap skipped MLX installation
- You want to add MLX to an existing setup
- MLX installation failed during bootstrap

**Steps:**

```bash
# 1. Ensure bootstrap has run first
./bootstrap.sh

# 2. Install MLX manually
./install-mlx.sh

# 3. IMPORTANT: Re-run bootstrap to detect MLX
./bootstrap.sh

# 4. Verify installation
cat out/hardware_cache.json
# Should show: "gpu_type": "mps", "whisper_backend": "mlx"
```

**Why re-run bootstrap?**

Bootstrap detects installed packages and updates `hardware_cache.json`. Without re-running bootstrap, the pipeline won't know MLX is available.

---

## Verification

### Check MLX Installation

```bash
# Activate environment
source .bollyenv/bin/activate

# Test MLX import
python -c "import mlx.core as mx; print('✓ MLX installed')"
python -c "import mlx_whisper; print('✓ MLX-Whisper installed')"
```

### Check Hardware Configuration

```bash
cat out/hardware_cache.json
```

**Expected output:**
```json
{
  "gpu_type": "mps",
  "whisper_backend": "mlx",
  "device": "mps",
  ...
}
```

### Test Transcription

```bash
# Create test job
./prepare-job.sh test.mp4 --transcribe -s hi

# Check job configuration
cat out/YYYY/MM/DD/USER/ID/.env
# Should show: WHISPER_BACKEND=mlx
```

---

## How install-mlx.sh Works

### Script Flow

```
User runs: ./install-mlx.sh
           │
           ├─> Check: Is this macOS? (exit if not)
           │
           ├─> Check: Does .bollyenv exist? (exit if not)
           │
           ├─> Activate: source .bollyenv/bin/activate
           │
           ├─> Install: pip install mlx
           │
           ├─> Install: pip install mlx-whisper
           │
           ├─> Verify: Test imports
           │
           └─> Message: "Re-run ./bootstrap.sh to detect MLX"
```

### What It Does NOT Do

❌ Does NOT create a separate virtual environment  
❌ Does NOT modify Python scripts  
❌ Does NOT update hardware_cache.json (bootstrap does this)  
❌ Does NOT run bootstrap automatically  

### What It DOES Do

✅ Installs `mlx` and `mlx-whisper` into existing `.bollyenv`  
✅ Verifies packages can be imported  
✅ Instructs user to re-run bootstrap  

---

## Impact on Downstream Tasks

### prepare-job.sh / prepare-job.ps1

**Impact:** ✅ None (no changes needed)

The job preparation scripts don't directly use MLX. They:
1. Read `out/hardware_cache.json` to get configuration
2. Create job directory with `.env` file
3. Copy hardware configuration to job's `.env`

MLX is automatically configured if `hardware_cache.json` shows `"whisper_backend": "mlx"`.

### run-pipeline.sh / run-pipeline.ps1

**Impact:** ✅ None (no changes needed)

The pipeline orchestrator scripts don't directly use MLX. They:
1. Call `scripts/run-pipeline.py` with job directory
2. Python script reads job's `.env` file
3. Python script uses MLX if `WHISPER_BACKEND=mlx`

### Python Pipeline (scripts/run-pipeline.py)

**Impact:** ✅ Automatic detection

The Python pipeline:
1. Reads `WHISPER_BACKEND` from job's `.env`
2. If `WHISPER_BACKEND=mlx`, imports `mlx_whisper`
3. Uses MLX for transcription automatically

**No code changes needed** - the pipeline already supports MLX!

---

## Common Scenarios

### Scenario 1: Fresh Install on Apple Silicon

```bash
./bootstrap.sh
# Result: MLX automatically installed and configured ✅
```

### Scenario 2: Existing Setup, Want to Add MLX

```bash
./install-mlx.sh
./bootstrap.sh              # Re-run to detect
# Result: MLX now available ✅
```

### Scenario 3: MLX Failed During Bootstrap

```bash
# Bootstrap ran but MLX install failed
./install-mlx.sh            # Manual install
./bootstrap.sh              # Re-run to detect
# Result: MLX now working ✅
```

### Scenario 4: Already Have Jobs Created

```bash
./install-mlx.sh
./bootstrap.sh              # Updates hardware_cache.json

# Old jobs: Still use old config (CPU or non-MLX)
# New jobs: Will use MLX automatically ✅
```

**Important:** Existing jobs keep their original configuration. Only NEW jobs created after MLX installation will use MLX.

---

## Troubleshooting

### "MLX is only supported on macOS (Apple Silicon)"

**Problem:** Trying to run on non-macOS or Intel Mac

**Solution:** MLX only works on Apple Silicon (M1/M2/M3). Use WhisperX with CUDA on Windows/Linux.

### ".bollyenv virtual environment not found"

**Problem:** Bootstrap hasn't been run yet

**Solution:**
```bash
./bootstrap.sh              # Create environment first
./install-mlx.sh            # Then install MLX
```

### "MLX-Whisper import failed"

**Problem:** Installation incomplete or corrupted

**Solution:**
```bash
source .bollyenv/bin/activate
pip uninstall mlx mlx-whisper -y
pip install mlx mlx-whisper
./bootstrap.sh              # Re-run to detect
```

### "Pipeline still using CPU"

**Problem:** Bootstrap wasn't re-run after MLX installation

**Solution:**
```bash
./bootstrap.sh              # Re-run to update hardware_cache.json

# Verify detection
cat out/hardware_cache.json
# Should show: "whisper_backend": "mlx"
```

### "Old jobs not using MLX"

**Problem:** Jobs created before MLX installation

**Solution:** This is expected! Old jobs keep their original config.

**Options:**
1. Create new jobs (they'll use MLX automatically)
2. Or manually edit old job's `.env` file:
   ```bash
   # Edit: out/YYYY/MM/DD/USER/ID/.env
   WHISPER_BACKEND=mlx
   ```

---

## Performance Comparison

### MacBook Pro M1 Pro (16GB)

| Backend | Model | Time (2hr movie) | Speedup |
|---------|-------|------------------|---------|
| CPU (WhisperX) | large-v3 | ~120 min | 1x |
| MPS (MLX) | large-v3 | ~17 min | 7x faster |

**Recommendation:** Use MLX on Apple Silicon for massive speedup!

---

## Summary

### Key Takeaways

1. **Same Virtual Environment**
   - MLX uses existing `.bollyenv`
   - No separate environment needed

2. **Bootstrap Auto-Installs**
   - Bootstrap detects Apple Silicon
   - Automatically installs MLX

3. **Manual Install Process**
   - Run `./install-mlx.sh`
   - **Must re-run `./bootstrap.sh`** to update config

4. **No Impact on Scripts**
   - Bash/PowerShell scripts unchanged
   - Python pipeline auto-detects MLX
   - Jobs inherit config from hardware_cache.json

5. **Verification Required**
   - Check `out/hardware_cache.json`
   - Should show `"whisper_backend": "mlx"`

### Best Practice

**Let bootstrap handle it automatically!**

Only use `./install-mlx.sh` if:
- Bootstrap failed to install MLX
- You're adding MLX to an existing setup
- You want manual control

---

## Documentation References

- **Setup Guide:** [docs/CORRECT_SETUP_GUIDE.md](CORRECT_SETUP_GUIDE.md)
- **Main README:** [README.md](../README.md)
- **MLX Acceleration:** [docs/MLX_ACCELERATION_GUIDE.md](MLX_ACCELERATION_GUIDE.md)
- **Quick Reference:** [QUICK_REFERENCE.md](../QUICK_REFERENCE.md)

---

**Last Updated:** 2025-11-19  
**Verified On:** macOS 14.x (Apple Silicon)  
**Status:** Production Ready ✅
