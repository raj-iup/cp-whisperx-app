# Quick Fix Reference Guide

This guide provides quick solutions to common issues found in log files.

## Common Log File Locations

```
out/YYYY/MM/DD/N/JOBID/logs/
├── 00_orchestrator_YYYYMMDD_HHMMSS.log
├── 06_diarization_YYYYMMDD_HHMMSS.log
├── 07_asr_YYYYMMDD_HHMMSS.log
├── 09_second_pass_translation_YYYYMMDD_HHMMSS.log
└── [other stages...]
```

## Quick Issue Identification

### 1. Diarization Errors

**Symptom**: "list indices must be integers or slices, not str"  
**Log**: `06_diarization_*.log`  
**Fix**: Parameter order in `whisperx.assign_word_speakers()`  
**Status**: ✓ Fixed in current version

### 2. ASR CPU Warnings

**Symptom**: "CPU does not efficiently support float16"  
**Log**: `07_asr_*.log`  
**Fix**: Automatic conversion to int8 (expected behavior)  
**Status**: ✓ Changed to INFO level

### 3. Translation Backend Errors

**Symptom**: "Unknown backend: nllb"  
**Log**: `09_second_pass_translation_*.log`  
**Fix**: Use "nllb200" or rely on automatic aliasing  
**Status**: ✓ Alias support added

### 4. Torchaudio Warnings

**Symptom**: Hundreds of "torchaudio._backend/utils.py:213" warnings  
**Log**: `00_orchestrator_*.log`  
**Fix**: Warning filters added to VAD scripts  
**Status**: ✓ Filters applied

## Debugging Workflow

1. **Check orchestrator log first**
   ```bash
   tail -100 out/YYYY/MM/DD/N/JOBID/logs/00_orchestrator_*.log
   ```

2. **Identify failed stage**
   - Look for "STAGE X/Y: STAGE_NAME"
   - Check for "ERROR" or "FAILED" markers

3. **Review stage-specific log**
   ```bash
   cat out/YYYY/MM/DD/N/JOBID/logs/##_stage_name_*.log
   ```

4. **Check for known issues** (see above)

5. **Verify fix status**
   ```bash
   grep -n "PATTERN" scripts/script_name.py
   ```

## Environment Validation

Quick checks to verify configuration:

```bash
# Check Python version
python3 --version  # Should be 3.11+

# Check key dependencies
python3 -c "import whisperx; print(whisperx.__version__)"
python3 -c "import torch; print(torch.__version__)"

# Check device availability
python3 -c "import torch; print('MPS:', torch.backends.mps.is_available())"
python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Validate config
cat out/YYYY/MM/DD/N/JOBID/.JOBID.env | grep -E "DEVICE|BACKEND|COMPUTE"
```

## Stage-Specific Fixes

### ASR Stage
- Always use `WHISPER_COMPUTE_TYPE=int8` for CPU
- Use `WHISPER_COMPUTE_TYPE=float16` for GPU (CUDA/MPS)
- Backend auto-detection works well, but can override with `WHISPER_BACKEND=whisperx`

### Diarization Stage  
- Requires `HF_TOKEN` environment variable
- MPS (Apple Silicon) works well
- CPU is very slow (hours for long audio)

### Translation Stage
- Backend options: `opus-mt`, `mbart50`, `nllb`, `nllb200`
- `nllb` and `nllb200` are aliases (both work)
- MPS supported for all backends

## Log Analysis Tips

### Finding Errors
```bash
# Get all errors from a log
grep -n "ERROR" logfile.log

# Get errors with context
grep -B 3 -A 3 "ERROR" logfile.log

# Count warnings by type
grep "WARNING" logfile.log | sort | uniq -c | sort -rn
```

### Performance Analysis
```bash
# Find stage durations
grep "completed in" logs/00_orchestrator_*.log

# Find slow stages (>5 minutes)
grep "completed in" logs/00_orchestrator_*.log | awk '$5 > 300'
```

### Device Usage Verification
```bash
# Check which device was used per stage
grep -h "Device:" logs/*.log
grep -h "Active device:" logs/*.log
grep -h "moved to" logs/*.log
```

## Common Pitfalls

1. **Using float16 on CPU**
   - Symptom: Warnings about compute type
   - Solution: Let automatic conversion handle it (now INFO level)

2. **Missing HF_TOKEN**
   - Symptom: 401 errors from Hugging Face
   - Solution: Set HF_TOKEN in environment or config

3. **Case sensitivity in backend names**
   - Symptom: Unknown backend errors
   - Solution: Use lowercase names (now handled automatically)

4. **Subprocess warnings**
   - Symptom: Warnings appear in orchestrator but not stage logs
   - Solution: Filter warnings in subprocess scripts (now done)

## Getting Help

If you encounter an issue not covered here:

1. Check the full implementation guide: `LOG_FIXES_IMPLEMENTATION.md`
2. Review recent commits for related fixes
3. Check if issue persists in latest code
4. Collect full log context (not just error line)

---

Last Updated: 2025-11-13  
Corresponding Fixes: See LOG_FIXES_IMPLEMENTATION.md
