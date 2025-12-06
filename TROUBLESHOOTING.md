# Troubleshooting Guide - CP-WhisperX-App

**Version:** 1.0  
**Created:** 2025-12-05  
**Status:** Active  
**Audience:** Users & Developers

This guide helps diagnose and resolve common issues with the CP-WhisperX pipeline.

---

## Quick Diagnostics

### Check System Status

```bash
# Check virtual environments
ls -la venv/

# Check logs
tail -100 logs/99_pipeline_*.log

# Check job status
cat out/YYYY/MM/DD/user/N/manifest.json
```

### Common Error Patterns

```bash
# Find errors in logs
grep -i "error\|failed\|exception" out/*/job-*/logs/*.log

# Check stage completion
ls -la out/*/job-*/*/manifest.json

# Check disk space
df -h
```

---

## Common Issues

### 1. Pipeline Stops During Processing

**Symptoms:**
- Pipeline starts but doesn't complete
- Log ends abruptly without error
- Process disappears from `ps aux`

**Likely Causes:**
1. **Out of Memory** (most common)
2. **Process killed by system**
3. **Hardware acceleration failure** (MPS/CUDA)
4. **Model download interrupted**

**Solutions:**

#### A. Check Memory Usage
```bash
# Monitor memory during run
while true; do
  ps aux | grep python | awk '{print $2, $4, $11}' | head -5
  sleep 5
done
```

**Fix:** Reduce batch size or model size
```bash
# In config/.env.pipeline
WHISPERX_BATCH_SIZE=1  # Reduce from 2
WHISPERX_MODEL=base    # Use smaller model
```

#### B. Check System Logs
```bash
# macOS
log show --predicate 'eventMessage contains "killed"' --last 1h

# Linux
dmesg | grep -i kill
journalctl -xe
```

#### C. Disable Hardware Acceleration
```bash
# Force CPU mode
WHISPERX_DEVICE=cpu
PYANNOTE_DEVICE=cpu
DEMUCS_DEVICE=cpu
```

#### D. Check Model Cache
```bash
# Verify models downloaded
ls -lh .cache/huggingface/
ls -lh .cache/torch/

# Clear and re-download
rm -rf .cache/huggingface/*
```

---

### 2. Source Separation Hangs

**Symptoms:**
- Demucs stage starts but never completes
- Log shows "Processing audio with Demucs..." then stops
- High CPU/Memory usage

**Likely Causes:**
1. **File too large** (>30 minutes)
2. **MPS device issue** (Apple Silicon)
3. **Memory exhaustion**

**Solutions:**

#### A. Disable Source Separation
```bash
# Edit job's .env.pipeline
SOURCE_SEPARATION_ENABLED=false
```

#### B. Use CPU for Demucs
```bash
# Force CPU (slower but stable)
DEMUCS_DEVICE=cpu
```

#### C. Lower Quality Preset
```bash
# Use faster preset
SOURCE_SEPARATION_QUALITY=fast  # Instead of "quality"
```

#### D. Process Shorter Clips
```bash
# Use media processing mode
./prepare-job.sh \
  --media file.mp4 \
  --workflow transcribe \
  --start-time 00:00:00 \
  --end-time 00:05:00
```

---

### 3. ASR/Transcription Errors

**Symptoms:**
- "No segments found"
- "Transcription failed"
- Empty transcript files

**Likely Causes:**
1. **VAD failed to detect speech**
2. **Audio file corrupted**
3. **Language mismatch**
4. **Model loading failed**

**Solutions:**

#### A. Check VAD Output
```bash
cat out/*/job-*/05_pyannote_vad/speech_segments.json
# Should contain segments array
```

**Fix:** Adjust VAD settings
```bash
PYANNOTE_MIN_DURATION=0.5  # Detect shorter segments
PYANNOTE_THRESHOLD=0.3     # Lower threshold
```

#### B. Verify Audio
```bash
ffprobe out/*/job-*/01_demux/audio.wav
# Check: duration, sample_rate, channels
```

#### C. Check Language Detection
```bash
# Look for detected language in logs
grep "detected language" out/*/job-*/logs/*.log
```

**Fix:** Specify language explicitly
```bash
./prepare-job.sh --media file.mp4 --source-language en
```

#### D. Test with Smaller Model
```bash
WHISPERX_MODEL=base  # Instead of large-v3
```

---

### 4. Alignment Failures

**Symptoms:**
- "Alignment failed"
- "No word timestamps"
- MLX segfault errors

**Likely Causes:**
1. **MLX subprocess failure** (hybrid architecture)
2. **Language not supported** for alignment
3. **Audio-text mismatch**

**Solutions:**

#### A. Check Backend Configuration
```bash
# Should use hybrid architecture (AD-008)
WHISPER_BACKEND=mlx           # For transcription
ALIGNMENT_BACKEND=whisperx    # For alignment (subprocess)
```

#### B. Verify Subprocess Timeout
```bash
# Increase if alignment is slow
ALIGNMENT_TIMEOUT=600  # 10 minutes
```

#### C. Check Alignment Support
Languages with alignment models:
- ✅ English (en)
- ✅ French (fr)
- ✅ German (de)
- ✅ Spanish (es)
- ✅ Italian (it)
- ✅ Japanese (ja)
- ✅ Chinese (zh)
- ✅ Dutch (nl)
- ✅ Ukrainian (uk)
- ✅ Portuguese (pt)
- ⚠️ Hindi, Tamil, etc. (limited support)

**Fix:** Skip alignment if not critical
```bash
# Pipeline will use segment-level timestamps
# Word-level timestamps optional
```

---

### 5. Translation Errors

**Symptoms:**
- "Translation failed"
- "IndicTrans2 not available"
- Empty translation files

**Likely Causes:**
1. **Wrong model for language pair**
2. **Model not installed**
3. **Memory exhaustion**

**Solutions:**

#### A. Check Language Pair
IndicTrans2 requirements:
- ✅ Source: Indian language (hi, ta, te, gu, kn, ml, bn, mr, pa)
- ✅ Target: Any language

**Fix:** Use correct workflow
```bash
# English → Hindi: Use transcribe (not translate)
./prepare-job.sh --media file.mp4 --workflow transcribe -s en

# Hindi → English: Use translate
./prepare-job.sh --media file.mp4 --workflow translate -s hi -t en
```

#### B. Verify Model Installation
```bash
# IndicTrans2 environment
source venv/indictrans2/bin/activate
python -c "import indictrans2; print('OK')"

# NLLB environment
source venv/nllb/bin/activate
python -c "import transformers; print('OK')"
```

#### C. Use Fallback Model
```bash
# Use NLLB for all translations
TRANSLATION_MODEL=nllb
```

---

### 6. Subtitle Generation Issues

**Symptoms:**
- No subtitle files generated
- Empty .vtt files
- Formatting errors

**Likely Causes:**
1. **Missing translation output**
2. **Character encoding issues**
3. **Invalid timestamps**

**Solutions:**

#### A. Verify Translation Output
```bash
ls -lh out/*/job-*/10_translation/
# Should contain: translation_*.json for each target language
```

#### B. Check Subtitle Stage Log
```bash
cat out/*/job-*/11_subtitle_generation/stage.log
```

#### C. Validate Timestamps
```bash
# Segments should have start/end times
cat out/*/job-*/07_alignment/alignment_segments.json | jq '.segments[0]'
```

---

### 7. Virtual Environment Errors

**Symptoms:**
- "ModuleNotFoundError"
- "No module named 'whisperx'"
- Import errors

**Likely Causes:**
1. **Wrong venv activated**
2. **Missing dependencies**
3. **venv corrupted**

**Solutions:**

#### A. Re-run Bootstrap
```bash
./bootstrap.sh
# Wait for all 8 environments to complete (20-30 minutes)
```

#### B. Verify Environments
```bash
# Check all venvs exist
ls -la venv/
# Should have: common, whisperx, pyannote, demucs, indictrans2, nllb, llm, mlx
```

#### C. Test Individual Environment
```bash
# Test WhisperX
source venv/whisperx/bin/activate
python -c "import whisperx; print('OK')"

# Test PyAnnote
source venv/pyannote/bin/activate
python -c "import pyannote.audio; print('OK')"
```

---

### 8. File Naming Issues

**Symptoms:**
- "File not found" errors
- Hidden files (leading dot)
- Export stage failures

**Status:** ✅ Fixed in v3.0 (commit 4e3de9e)

**Old Pattern (Wrong):**
```
.segments.json
-English.srt
.transcript.txt
```

**New Pattern (Correct):**
```
asr_segments.json
asr_english_subtitles.srt
asr_transcript.txt
```

**If using old jobs:**
```bash
# Re-run with v3.0
./run-pipeline.sh out/YYYY/MM/DD/user/N
```

---

### 9. Performance Issues

**Symptoms:**
- Processing takes too long
- High memory usage
- System slowdown

**Solutions:**

#### A. Enable Hardware Acceleration
```bash
# Check device availability
python3 -c "import torch; print(torch.backends.mps.is_available())"  # macOS
python3 -c "import torch; print(torch.cuda.is_available())"          # NVIDIA

# Configure
WHISPERX_DEVICE=mps    # Apple Silicon
WHISPERX_DEVICE=cuda   # NVIDIA GPU
WHISPERX_DEVICE=cpu    # CPU only
```

#### B. Use Smaller Models
```bash
WHISPERX_MODEL=base      # Fastest, lower accuracy
WHISPERX_MODEL=small     # Good balance
WHISPERX_MODEL=medium    # Better accuracy
WHISPERX_MODEL=large-v3  # Best accuracy, slowest
```

#### C. Adjust Batch Size
```bash
WHISPERX_BATCH_SIZE=4   # Higher = faster but more memory
WHISPERX_BATCH_SIZE=1   # Lower = slower but less memory
```

#### D. Disable Optional Stages
```bash
SOURCE_SEPARATION_ENABLED=false  # Skip Demucs
LYRICS_DETECTION_ENABLED=false   # Skip lyrics detection
```

---

### 10. Permission Errors

**Symptoms:**
- "Permission denied"
- "Cannot write to directory"

**Solutions:**

#### A. Check Permissions
```bash
ls -la out/
ls -la logs/
ls -la .cache/
```

#### B. Fix Ownership
```bash
sudo chown -R $(whoami) out/ logs/ .cache/
```

#### C. Check Disk Space
```bash
df -h
du -sh out/
du -sh .cache/
```

---

## Advanced Debugging

### Enable Debug Mode

```bash
# In job's .env.pipeline
DEBUG=true
LOG_LEVEL=DEBUG

# Re-run
./run-pipeline.sh out/YYYY/MM/DD/user/N
```

### Verbose Logging

```bash
# Check all stage logs
for log in out/*/job-*/*/stage.log; do
  echo "=== $log ==="
  tail -20 "$log"
done
```

### Test Individual Stages

```bash
# Test demux
python3 scripts/01_demux.py out/YYYY/MM/DD/user/N

# Test ASR
python3 scripts/06_whisperx_asr.py out/YYYY/MM/DD/user/N

# Test alignment
python3 scripts/07_alignment.py out/YYYY/MM/DD/user/N
```

### Profile Performance

```bash
# Install profiling tools
pip install py-spy

# Profile pipeline
py-spy record -o profile.svg -- ./run-pipeline.sh out/YYYY/MM/DD/user/N
```

---

## Getting Help

### Collect Diagnostic Info

```bash
# Create support bundle
tar -czf debug-bundle.tar.gz \
  out/YYYY/MM/DD/user/N/logs/ \
  out/YYYY/MM/DD/user/N/manifest.json \
  out/YYYY/MM/DD/user/N/job.json \
  out/YYYY/MM/DD/user/N/.job-*.env
```

### Check Documentation

- **Architecture:** `docs/technical/architecture.md`
- **Developer Standards:** `docs/developer/DEVELOPER_STANDARDS.md`
- **Workflows:** `docs/user-guide/workflows.md`
- **Configuration:** `docs/user-guide/configuration.md`

### Report Issues

Include:
1. System info (OS, Python version, hardware)
2. Job configuration (job.json)
3. Error logs (relevant stage logs)
4. Steps to reproduce
5. Expected vs actual behavior

---

## Prevention

### Best Practices

1. **Start Small:** Test with short clips (1-5 minutes) first
2. **Monitor Resources:** Watch memory/CPU during runs
3. **Use Standard Test Media:** Validate changes with known samples
4. **Check Logs Early:** Don't wait for completion to review logs
5. **Keep Environments Updated:** Re-run bootstrap.sh periodically

### Pre-flight Checklist

Before running a large job:

- [ ] Virtual environments installed (`ls venv/`)
- [ ] Sufficient disk space (10GB+ free)
- [ ] Sufficient memory (8GB+ available)
- [ ] Input media accessible and valid
- [ ] Configuration reviewed (`job.json`)
- [ ] Test run on short clip successful

---

## Status Indicators

### Pipeline Status

```bash
# Check manifest
cat out/*/job-*/manifest.json | jq '.status'
# Values: prepared, running, completed, failed
```

### Stage Status

```bash
# Check stage completion
ls -la out/*/job-*/*/manifest.json
# Each stage should have manifest.json if completed
```

### Log Indicators

- ✅ `COMPLETED` - Stage finished successfully
- ❌ `FAILED` - Stage encountered error
- ⚠️ `WARNING` - Non-critical issue
- ℹ️ `INFO` - Progress information

---

## Quick Fixes Reference

| Issue | Quick Fix |
|-------|-----------|
| Out of memory | Reduce batch size, use smaller model |
| Demucs hangs | Set `SOURCE_SEPARATION_ENABLED=false` |
| No transcription | Check VAD output, specify language |
| Alignment fails | Verify hybrid architecture (AD-008) |
| Translation fails | Check language pair, use NLLB fallback |
| Slow processing | Enable hardware acceleration (MPS/CUDA) |
| Module not found | Re-run bootstrap.sh |
| Permission denied | Fix ownership, check disk space |

---

**Last Updated:** 2025-12-05  
**Version:** 1.0  
**Status:** Active Reference
