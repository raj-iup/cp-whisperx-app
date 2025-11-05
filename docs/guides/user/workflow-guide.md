# CP-WhisperX-App Workflow Guide

## Quick Start

### 1. Transcribe Only (Fast, No Subtitles)

**Best for:** Quick transcription, podcast transcripts, audio-only content

```bash
# Auto-detect and use GPU acceleration if available
python prepare-job.py input.mp4 --transcribe --native
python pipeline.py --job 20251103-0001

# Output: out/2025/11/03/20251103-0001/transcript/transcript.txt
```

**Pipeline Stages:**
- ✅ Audio extraction (demux)
- ✅ Voice activity detection (VAD)
- ✅ Speech-to-text (WhisperX ASR)
- ❌ Speaker diarization (skipped)
- ❌ Entity correction (skipped)
- ❌ Subtitle generation (skipped)
- ❌ Video muxing (skipped)

**Duration:** ~10-15 minutes for 2-hour movie (with GPU)

---

### 2. Full Subtitle Generation (High Quality)

**Best for:** Movie/TV subtitles with speaker labels, professional quality

```bash
# Use GPU acceleration for ML stages
python prepare-job.py input.mp4 --subtitle-gen --native
python pipeline.py --job 20251103-0001

# Output: out/2025/11/03/20251103-0001/output.mp4 (with embedded subtitles)
```

**Pipeline Stages:**
- ✅ Audio extraction
- ✅ TMDB metadata (cast/crew names)
- ✅ Pre-NER (entity extraction)
- ✅ Voice activity detection (2 stages)
- ✅ Speaker diarization
- ✅ Speech-to-text + alignment
- ✅ Second pass translation (15-20% quality boost)
- ✅ Lyrics detection (20-25% improvement for songs)
- ✅ Entity correction
- ✅ Subtitle generation
- ✅ Video muxing

**Duration:** ~30-45 minutes for 2-hour movie (with GPU)

---

### 3. Test with Clip (5 Minutes)

**Best for:** Testing configuration, parameter tuning

```bash
# Process 5-minute clip from 10:00 to 15:00
python prepare-job.py input.mp4 --start-time 00:10:00 --end-time 00:15:00 --native
python pipeline.py --job 20251103-0001
```

**Duration:** ~2-3 minutes for 5-minute clip

---

## Execution Modes

### Native Execution (GPU Accelerated)

```bash
python prepare-job.py input.mp4 --native
```

**Auto-detects:**
- 🍎 **Apple Silicon (M1/M2/M3):** Uses MPS
- 🟢 **NVIDIA GPU:** Uses CUDA  
- ⚪ **No GPU:** Falls back to CPU

**ML Stages Run Natively:**
- Silero VAD (PyTorch)
- Pyannote VAD (PyTorch)
- Diarization (PyTorch)
- WhisperX ASR (PyTorch)
- Second Pass Translation
- Lyrics Detection

**Performance:**
- 3-5x faster than Docker/CPU
- Lower memory usage
- Better GPU utilization

---

### Docker Execution (CPU)

```bash
python prepare-job.py input.mp4  # no --native flag
python pipeline.py --job 20251103-0001
```

**Runs all stages in Docker containers:**
- Consistent environment
- No local dependency conflicts
- Works on any system
- CPU-only execution

**Use when:**
- No GPU available
- Reproducible builds needed
- Docker infrastructure preferred

---

## Workflow Comparison

| Feature | Transcribe | Subtitle-Gen |
|---------|-----------|--------------|
| **Output** | Text file | Video + SRT |
| **Speaker Labels** | ❌ No | ✅ Yes |
| **Entity Correction** | ❌ No | ✅ Yes |
| **TMDB Metadata** | ❌ No | ✅ Yes |
| **Second Pass Translation** | ❌ No | ✅ Yes |
| **Lyrics Detection** | ❌ No | ✅ Yes |
| **Duration (2hr movie)** | 10-15 min | 30-45 min |
| **Quality** | Good | Excellent |

---

## Configuration

### Using Custom Config

```bash
# Create custom config
cp config/.env.pipeline config/.env.custom

# Edit config/.env.custom (change parameters)
vim config/.env.custom

# Use custom config
python prepare-job.py input.mp4 --config config/.env.custom --native
```

---

### Key Parameters to Tune

**For Better Accuracy:**
```bash
# config/.env.custom
WHISPER_TEMPERATURE=0.0,0.2,0.4  # Lower = more conservative
WHISPER_BEAM_SIZE=10              # Higher = more accurate (slower)
WHISPER_NO_SPEECH_THRESHOLD=0.8  # Higher = skip more silence
```

**For Faster Processing:**
```bash
WHISPER_BATCH_SIZE=32            # Higher = faster (needs more memory)
WHISPER_BEAM_SIZE=3              # Lower = faster (less accurate)
```

**For Better Diarization:**
```bash
DIARIZATION_MIN_SPEAKERS=2       # Set if you know speaker count
DIARIZATION_MAX_SPEAKERS=5       # Limit if known
```

---

## Resume Failed Jobs

```bash
# Check job status
python pipeline.py --job 20251103-0001 --status

# Resume from last completed stage
python pipeline.py --job 20251103-0001 --resume

# Resume from specific stage
python pipeline.py --job 20251103-0001 --from-stage asr
```

---

## Debugging

### Enable Debug Logging

```bash
# Set environment variable
export LOG_LEVEL=debug

# Or edit job config after creation
vim jobs/2025/11/03/20251103-0001/.20251103-0001.env
# Change: LOG_LEVEL=debug
```

### Check Logs

```bash
# All logs in job output directory
ls out/2025/11/03/20251103-0001/logs/

# View specific stage log
tail -f out/2025/11/03/20251103-0001/logs/05_pyannote_vad_*.log
```

### Check Manifest

```bash
# View pipeline progress
cat out/2025/11/03/20251103-0001/manifest.json

# Check which stages completed
jq '.stages[] | select(.status=="completed") | .stage' out/2025/11/03/20251103-0001/manifest.json
```

---

## Advanced Usage

### Process Multiple Files

```bash
#!/bin/bash
# batch-process.sh

for file in /media/*.mp4; do
    echo "Processing: $file"
    python prepare-job.py "$file" --native --subtitle-gen
    
    # Get last job ID
    JOB_ID=$(ls -t jobs/2025/11/03/ | head -1)
    
    # Run pipeline
    python pipeline.py --job "$JOB_ID"
done
```

### Custom Output Location

```bash
# Edit config after job creation
vim jobs/2025/11/03/20251103-0001/.20251103-0001.env
# Change: OUTPUT_ROOT=/custom/path/output
```

---

## Troubleshooting

### GPU Not Detected

```bash
# Check PyTorch GPU availability
python3 -c "import torch; print('CUDA:', torch.cuda.is_available()); print('MPS:', torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False)"

# If False, install PyTorch with GPU support
# For Apple Silicon:
pip3 install torch torchvision torchaudio

# For NVIDIA:
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory

```bash
# Reduce batch size
vim config/.env.pipeline
# Change: WHISPER_BATCH_SIZE=8  # (from 16)

# Or use Docker/CPU mode
python prepare-job.py input.mp4  # without --native
```

### Slow Performance

```bash
# Check which device is being used
grep "Device:" out/2025/11/03/20251103-0001/logs/05_pyannote_vad_*.log

# If CPU when GPU available:
python prepare-job.py input.mp4 --native  # force native mode
```

---

## Performance Benchmarks

### 2-Hour Bollywood Movie (Hindi → English)

| Mode | Device | Duration | Quality |
|------|--------|----------|---------|
| Transcribe | MPS (M2) | 12 min | Good |
| Transcribe | CUDA (RTX 4090) | 8 min | Good |
| Transcribe | CPU (Docker) | 45 min | Good |
| Subtitle-Gen | MPS (M2) | 35 min | Excellent |
| Subtitle-Gen | CUDA (RTX 4090) | 22 min | Excellent |
| Subtitle-Gen | CPU (Docker) | 2.5 hours | Excellent |

---

## Best Practices

1. **Test with clips first** (5-10 minutes) to verify config
2. **Use native mode** for production (3-5x faster)
3. **Enable second pass** for translation quality (+15-20%)
4. **Enable lyrics detection** for Bollywood content (+20-25%)
5. **Set speaker count** if known (faster diarization)
6. **Use GPU** for large batches (multiple files)
7. **Check logs** if quality issues
8. **Tune parameters** based on content type

---

## Next Steps

### Planned: Dubbing Workflow

**Coming soon:**
```bash
python prepare-job.py input.mp4 --dubbing --target-lang=hi --voice-clone
```

**Will include:**
- Voice selection/cloning
- Text-to-speech generation
- Audio timing alignment
- Lip-sync optimization
- Mixed audio output

---

## Support

- **Documentation:** `/docs/` directory
- **Examples:** `pipeline_examples.sh`
- **Logs:** Check job output logs directory
- **Manifest:** `manifest.json` for debugging

**For issues:** Check logs first, then manifest.json for stage-specific errors.
