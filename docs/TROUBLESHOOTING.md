# Troubleshooting Guide

**Common issues and solutions**

## Quick Fixes

### Bootstrap Fails
```bash
rm -rf .bollyenv
./scripts/bootstrap.sh
```

### Device Shows CPU Instead of GPU
```bash
cat out/hardware_cache.json | grep gpu_type
rm out/hardware_cache.json
./scripts/bootstrap.sh
```

### Models Fail to Download
```bash
# Check token
cat config/secrets.json | grep HF_TOKEN

# Check disk space
df -h .

# Check cache permissions
ls -la .cache/
```

See [Bootstrap Guide](BOOTSTRAP.md) for detailed troubleshooting.

Return to [Documentation Index](INDEX.md)

---

## WhisperX MPS Device Error

### Symptom
```
ValueError: unsupported device MPS
ValueError: Requested float16 compute type, but the target device or backend do not support efficient float16 computation
```

### Cause
WhisperX uses CTranslate2 backend which **does not support MPS** (Apple Silicon GPU). CTranslate2 only supports CPU and CUDA devices.

### Solution
**This is now handled automatically** (as of 2025-11-08 fix):

The pipeline automatically:
1. Detects MPS device request
2. Falls back to CPU
3. Changes compute type from float16 to int8
4. Logs clear warnings
5. Continues processing

### What You'll See
```
[WARNING] MPS device not supported by CTranslate2 (faster-whisper backend)
[WARNING] Falling back to CPU with int8 compute type for best performance
[INFO] Model loaded successfully on cpu
```

### Performance Impact
- **With automatic fix**: 6-8x real-time (still quite fast)
- **Without GPU**: Same as above (CPU int8)
- **Quality**: No degradation (int8 is production-quality)

### Why This Happens
- CTranslate2 is optimized for CPU and CUDA only
- Apple Silicon (M1/M2/M3) uses MPS, which isn't supported
- Other stages (VAD, diarization) **do** use MPS successfully
- Only WhisperX ASR stage needs CPU fallback

### No Action Needed
The fix is automatic. Just resume your job:
```bash
./resume-pipeline.sh YOUR_JOB_ID
```

### To Minimize Impact
1. Use `medium` model instead of `large-v3` (faster)
2. Close other applications
3. Run overnight for long movies

See [WHISPERX_MPS_LIMITATION.md](../WHISPERX_MPS_LIMITATION.md) for detailed explanation.

