# Stage 7: ASR - Debug Mode Guide

## Quick Reference: Run ASR in Debug Mode

### Basic Debug Command

```bash
# Set environment variable for DEBUG level logging
export LOG_LEVEL=DEBUG

# Run ASR stage with debug logging
python native/scripts/07_asr.py \
  --input "in/your_movie.mp4" \
  --movie-dir "out/Movie_Name_Year" \
  --model base \
  --language en
```

### Full Debug Command with All Options

```bash
# Run with maximum verbosity
LOG_LEVEL=DEBUG python -u native/scripts/07_asr.py \
  --input "in/Jaane_Tu_Ya_Jaane_Na_2008.mp4" \
  --movie-dir "out/Jaane_Tu_Ya_Jaane_Na_2008" \
  --model base \
  --language hi \
  --batch-size 16 \
  --compute-type float32 2>&1 | tee asr_debug.log
```

**Options explained:**
- `LOG_LEVEL=DEBUG` - Enable debug-level logging
- `python -u` - Unbuffered output (see logs in real-time)
- `2>&1` - Capture both stdout and stderr
- `| tee asr_debug.log` - Save output to file while displaying

---

## Debug Levels

### 1. **INFO Level (Default)**
Shows high-level progress:
```bash
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"
```

Output:
```
[2025-10-30 01:30:00] [native.asr.Movie_2008] [INFO] Running Faster-Whisper ASR on cpu
[2025-10-30 01:30:10] [native.asr.Movie_2008] [INFO] Model: base
[2025-10-30 01:30:15] [native.asr.Movie_2008] [INFO] Loaded 1234 speaker segments
```

### 2. **DEBUG Level (Detailed)**
Shows everything including function calls, parameters, and timing:

```bash
LOG_LEVEL=DEBUG python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"
```

Output:
```
[2025-10-30 01:30:00] [native.asr.Movie_2008] [DEBUG] [main:126] Logger initialized: native.asr.Movie_2008
[2025-10-30 01:30:00] [native.asr.Movie_2008] [DEBUG] [main:147] Input audio: out/Movie_2008/audio/audio.wav
[2025-10-30 01:30:01] [native.asr.Movie_2008] [DEBUG] [run_asr:53] Configuration: {'model_name': 'base', ...}
[2025-10-30 01:30:05] [native.asr.Movie_2008] [DEBUG] [process:89] Processing batch 1/45
```

---

## Monitoring Options

### 1. **Real-time Console Output**
```bash
python -u native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"
```

### 2. **Save to Log File**
```bash
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" > asr_output.log 2>&1
```

### 3. **Both Console + File**
```bash
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" 2>&1 | tee asr_output.log
```

### 4. **Watch Progress in Another Terminal**
Terminal 1 (run script):
```bash
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"
```

Terminal 2 (watch logs):
```bash
tail -f logs/asr_*.log
```

---

## Log File Locations

### Automatic Logs
All stages automatically create timestamped log files:

```
logs/
├── asr_Movie_2008_20251030_013000.log    # Full debug logs
├── demux_Movie_2008_20251030_012000.log
├── diarization_Movie_2008_20251030_012500.log
└── ...
```

### Finding Latest ASR Log
```bash
# View latest ASR log
ls -t logs/asr_*.log | head -1 | xargs cat

# Follow latest ASR log in real-time
ls -t logs/asr_*.log | head -1 | xargs tail -f
```

---

## Common Debug Scenarios

### Scenario 1: Script Hangs/Freezes

**Problem:** Script appears stuck with no output

**Debug:**
```bash
# Run with verbose output
LOG_LEVEL=DEBUG python -u native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" \
  --batch-size 8  # Reduce batch size
```

**Check:**
- Monitor CPU/GPU usage: `top` or `htop`
- Check memory: `free -h` (Linux) or `vm_stat` (macOS)
- Watch log file: `tail -f logs/asr_*.log`

### Scenario 2: Out of Memory

**Problem:** Process killed or OOM errors

**Solutions:**
```bash
# Use smaller model
--model tiny  # or base (instead of large)

# Reduce batch size
--batch-size 4  # Default is 16

# Use lower precision
--compute-type int8  # Instead of float32
```

### Scenario 3: Poor Transcription Quality

**Debug:**
```bash
# Try larger model with debug output
LOG_LEVEL=DEBUG python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" \
  --model large-v3 \
  --language hi  # Specify language explicitly
```

### Scenario 4: Wrong Language Detected

**Debug:**
```bash
# Force specific language
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" \
  --language hi  # Hindi
  # --language en  # English
  # --language es  # Spanish
```

---

## Performance Monitoring

### Enable All Debug Output + Timing
```bash
time LOG_LEVEL=DEBUG python -u native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" 2>&1 | tee asr_debug.log
```

Output includes:
- Total runtime via `time` command
- Per-stage timing in logs
- Segment processing time
- Memory usage (if available)

### Monitor System Resources During Run

**Terminal 1:** Run ASR
```bash
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"
```

**Terminal 2:** Monitor resources
```bash
# macOS
while true; do
  clear
  echo "=== Process Info ==="
  ps aux | grep "07_asr.py" | grep -v grep
  echo -e "\n=== Memory ==="
  vm_stat | head -5
  sleep 5
done

# Linux
watch -n 5 'ps aux | grep "07_asr.py" && free -h'
```

---

## Troubleshooting with Debug Mode

### Check Prerequisites
```bash
# Verify audio file exists
ls -lh out/Movie_2008/audio/audio.wav

# Check diarization output
ls -lh out/Movie_2008/diarization/speaker_segments.json
cat out/Movie_2008/diarization/speaker_segments.json | jq '.segments | length'

# Verify secrets file (if needed)
cat config/secrets.json | jq .HF_TOKEN
```

### Test with Minimal Example
```bash
# Run on small model with tiny audio (for testing)
LOG_LEVEL=DEBUG python native/scripts/07_asr.py \
  --input "in/short_clip.mp4" \
  --movie-dir "out/Test_Clip" \
  --model tiny \
  --batch-size 4
```

### Python Debug Mode
```bash
# Run with Python warnings enabled
python -W all native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"

# Run with Python debugger
python -m pdb native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008"
```

---

## Log Analysis

### Extract Key Information

```bash
# Count segments processed
grep "Transcribed segments" logs/asr_*.log | tail -1

# Find errors
grep -i "error\|exception\|failed" logs/asr_*.log

# Check performance
grep "Processing time\|duration" logs/asr_*.log

# View language detection
grep "Language" logs/asr_*.log
```

### Analyze Segment Processing
```bash
# Show all segment information
LOG_LEVEL=DEBUG python native/scripts/07_asr.py ... 2>&1 | grep "segment"

# Count words transcribed
cat out/Movie_2008/transcription/transcript.json | jq '.statistics.total_words'

# View sample transcription
head -20 out/Movie_2008/transcription/transcript.txt
```

---

## Interactive Debug Session

### Method 1: IPython/Jupyter

```python
# Create debug script: debug_asr.py
import sys
sys.path.insert(0, 'native/utils')
from simplified_asr_wrapper import SimplifiedASR
from native_logger import NativePipelineLogger
from pathlib import Path

logger = NativePipelineLogger('asr_debug', 'Test_Movie', log_level='DEBUG')

# Initialize ASR
asr = SimplifiedASR(
    model_name='base',
    device='cpu',
    compute_type='float32',
    language='en',
    logger=logger
)

# Test on audio
audio_file = Path('out/Movie_2008/audio/audio.wav')
result, stats = asr.process(audio_file, speaker_segments=None, batch_size=8)

# Inspect results
print(f"Language: {stats['language']}")
print(f"Segments: {stats['num_segments']}")
print(f"Words: {stats['total_words']}")
```

Run:
```bash
ipython -i debug_asr.py
```

### Method 2: Code Inspection

Add breakpoints in the code:
```python
# In native/scripts/07_asr.py, add:
import pdb; pdb.set_trace()  # Breakpoint here
```

Then run:
```bash
python native/scripts/07_asr.py --input "in/movie.mp4" --movie-dir "out/Movie_2008"
```

---

## Output Verification

### Check Generated Files
```bash
# List all outputs
ls -lh out/Movie_2008/transcription/

# Expected files:
# - transcript.json (full transcription)
# - transcript.txt (human-readable)
```

### Validate Transcript Quality
```bash
# Count segments
cat out/Movie_2008/transcription/transcript.json | jq '.segments | length'

# View first 5 segments
cat out/Movie_2008/transcription/transcript.json | jq '.segments[0:5]'

# Check for empty transcriptions
cat out/Movie_2008/transcription/transcript.json | jq '.segments[] | select(.text == "")'

# View statistics
cat out/Movie_2008/transcription/transcript.json | jq '.statistics'
```

### Sample Output Inspection
```bash
# View text transcript
cat out/Movie_2008/transcription/transcript.txt | head -20

# Search for specific speaker
grep "SPEAKER_00" out/Movie_2008/transcription/transcript.txt | head -5

# Check timestamp range
head -1 out/Movie_2008/transcription/transcript.txt
tail -1 out/Movie_2008/transcription/transcript.txt
```

---

## Best Practices

### 1. **Start Small**
- Test with `--model tiny` first
- Use small audio clip if possible
- Verify setup before full run

### 2. **Monitor First Run**
```bash
# Watch output in real-time
LOG_LEVEL=DEBUG python -u native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" 2>&1 | tee asr.log
```

### 3. **Save All Logs**
Always use `tee` or redirect to save output:
```bash
python native/scripts/07_asr.py ... 2>&1 | tee asr_run_$(date +%Y%m%d_%H%M%S).log
```

### 4. **Check Prerequisites**
Before running, verify:
```bash
# Audio exists
[ -f "out/Movie_2008/audio/audio.wav" ] && echo "Audio OK" || echo "Audio MISSING"

# Diarization exists
[ -f "out/Movie_2008/diarization/speaker_segments.json" ] && echo "Diarization OK" || echo "Diarization MISSING"

# Output directory writable
touch "out/Movie_2008/transcription/test.txt" && rm "out/Movie_2008/transcription/test.txt" && echo "Output OK"
```

---

## Quick Debug Commands

### Complete Debug Run (Recommended)
```bash
# Full debug with all features enabled
time LOG_LEVEL=DEBUG python -u native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" \
  --model base \
  --language auto \
  --batch-size 16 \
  --compute-type float32 2>&1 | tee logs/asr_debug_$(date +%Y%m%d_%H%M%S).log
```

### Fast Test Run (Tiny Model)
```bash
# Quick test with smallest model
LOG_LEVEL=DEBUG python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" \
  --model tiny \
  --batch-size 32
```

### Production Run with Logging
```bash
# Production run with monitoring
python native/scripts/07_asr.py \
  --input "in/movie.mp4" \
  --movie-dir "out/Movie_2008" \
  --model large-v3 \
  --language hi 2>&1 | tee logs/asr_production.log
```

---

## Example: Complete Debug Session

```bash
# 1. Set up environment
cd /path/to/cp-whisperx-app
export LOG_LEVEL=DEBUG

# 2. Verify prerequisites
echo "Checking prerequisites..."
ls -lh out/Jaane_Tu_Ya_Jaane_Na_2008/audio/audio.wav
ls -lh out/Jaane_Tu_Ya_Jaane_Na_2008/diarization/speaker_segments.json

# 3. Run with full debug
echo "Starting ASR with debug mode..."
time python -u native/scripts/07_asr.py \
  --input "in/Jaane_Tu_Ya_Jaane_Na_2008.mp4" \
  --movie-dir "out/Jaane_Tu_Ya_Jaane_Na_2008" \
  --model base \
  --language hi \
  --batch-size 16 \
  --compute-type float32 2>&1 | tee logs/asr_debug_session.log

# 4. Verify output
echo "Checking outputs..."
ls -lh out/Jaane_Tu_Ya_Jaane_Na_2008/transcription/
cat out/Jaane_Tu_Ya_Jaane_Na_2008/transcription/transcript.json | jq '.statistics'

# 5. Review logs
echo "Analyzing logs..."
grep -i "error" logs/asr_debug_session.log
grep "Language\|segments\|words" logs/asr_debug_session.log

# 6. Sample output
echo "Sample transcription:"
head -10 out/Jaane_Tu_Ya_Jaane_Na_2008/transcription/transcript.txt
```

---

## Environment Variables

```bash
# Debug level logging
export LOG_LEVEL=DEBUG

# Custom log directory
export LOG_DIR=custom_logs

# Python unbuffered output
export PYTHONUNBUFFERED=1

# Show warnings
export PYTHONWARNINGS=default

# Combine all
LOG_LEVEL=DEBUG PYTHONUNBUFFERED=1 python native/scripts/07_asr.py ...
```

---

## Summary

**To run ASR in debug mode, use:**

```bash
LOG_LEVEL=DEBUG python -u native/scripts/07_asr.py \
  --input "in/your_movie.mp4" \
  --movie-dir "out/Your_Movie_2008" \
  --model base \
  --language en 2>&1 | tee asr_debug.log
```

**Key points:**
- `LOG_LEVEL=DEBUG` - Maximum verbosity
- `python -u` - Unbuffered output (real-time)
- `2>&1 | tee` - Save output while viewing
- All logs saved to `logs/asr_*.log`
- Check output in `out/Movie_Name/transcription/`

**Next steps after ASR:**
- Stage 8: Post-NER (entity correction)
- Stage 9: Subtitle Generation (SRT)
- Stage 10: Mux (embed subtitles)
