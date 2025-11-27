# Quick Reference Card - Multi-Environment Architecture

## Environment Summary
```
venv/common       → Shared utilities (logging, config, job management)
venv/whisperx     → ASR/transcription (WhisperX, PyTorch, faster-whisper)
venv/mlx          → MPS acceleration (MLX-Whisper for Apple Silicon)
venv/indictrans2  → Translation (IndicTrans2 for Indic languages)
```

## Bootstrap (One-Time Setup)
```bash
# macOS/Linux
./bootstrap.sh

# Windows
.\bootstrap.ps1
```

## Workflow Examples

### 1. Transcribe Only (Audio → Text)
```bash
# Full video
./prepare-job.sh in/movie.mp4 --transcribe -s hi

# With time range (6:00 to 8:30)
./prepare-job.sh in/movie.mp4 --transcribe -s hi \
    --start-time 00:06:00 --end-time 00:08:30 --debug

# Run pipeline
./run-pipeline.sh -j <job-id>

# Output: transcripts/segments.json, transcript_hi.txt
```

### 2. Translate (Text → Translated Text)
```bash
# Single target
./prepare-job.sh in/movie.mp4 --translate -s hi -t en --debug

# Multiple targets (English + Gujarati)
./prepare-job.sh in/movie.mp4 --translate -s hi -t en,gu --debug

# Run pipeline
./run-pipeline.sh -j <job-id>

# Output: transcripts/transcript_en.txt, transcript_gu.txt
```

### 3. Subtitle (Full Workflow: Audio → Text → Subtitles → Video)
```bash
# Single target subtitle
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en --debug

# Multiple subtitle tracks
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en,gu,ta --debug

# With clip range (testing)
./prepare-job.sh in/"Jaane Tu Ya Jaane Na 2008.mp4" \
    --subtitle -s hi -t en,gu \
    --start-time 00:06:00 --end-time 00:08:30 \
    --debug

# Run pipeline
./run-pipeline.sh -j <job-id>

# Output: 
#   subtitles/hi.srt (source)
#   subtitles/en.srt (translated)
#   subtitles/gu.srt (translated)
#   muxed/movie_subtitled.mkv (video with all subtitle tracks)
```

## Language Support

### Source Languages (22 Indic Languages)
```
hi  - Hindi          bn  - Bengali       gu  - Gujarati
ta  - Tamil          te  - Telugu        kn  - Kannada
ml  - Malayalam      mr  - Marathi       pa  - Punjabi
ur  - Urdu           as  - Assamese      or  - Odia
ne  - Nepali         sd  - Sindhi        si  - Sinhala
sa  - Sanskrit       ks  - Kashmiri      doi - Dogri
mni - Manipuri       kok - Konkani       mai - Maithili
sat - Santali
```

### Target Languages (Currently Supported)
```
✅ All 22 Indic languages (Indic → Indic)
✅ English (en)
❌ Other non-Indic languages (Spanish, Arabic, etc.) - requires additional implementation
```

## Hardware Configuration

### Auto-Detected by prepare-job.sh
```
Device: cpu | mps | cuda
Backend: whisperx | mlx
Model: large-v3 (default)
Compute: int8 (cpu) | float16 (cuda) | float16 (mlx) | float32 (mps fallback)
```

### Manual Override (if needed)
Edit job's `.env` file in job directory:
```bash
WHISPERX_DEVICE=cpu          # or mps, cuda
WHISPER_MODEL=large-v3       # or large-v2, medium, small
WHISPER_COMPUTE_TYPE=int8    # or float16, float32
WHISPER_BACKEND=whisperx     # or mlx
BATCH_SIZE=2                 # or 4, 8 (higher = faster but more memory)
```

## Troubleshooting

### Issue: Float16 Error on CPU
```
ValueError: Requested float16 compute type, but the target device or backend do not support efficient float16 computation.
```
**Fixed:** Automatic fallback to int8 (as of Nov 20, 2025)

### Issue: MLX Not Available
```
WARNING: MPS device detected but MLX backend not configured
WARNING: Falling back to CPU (slower performance)
```
**Solution:** Install MLX environment:
```bash
./install-mlx.sh  # macOS only
```

### Issue: IndicTrans2 Model Not Found
```
ERROR: Could not load IndicTrans2 model
```
**Solution:** Install IndicTrans2:
```bash
./install-indictrans2.sh
# Requires HuggingFace authentication
```

### Issue: Transcript Not Found
```
ERROR: Transcript not found: segments.json
ERROR: Run transcribe workflow first!
```
**Solution:** Run transcribe before translate:
```bash
./prepare-job.sh in/movie.mp4 --transcribe -s hi
./run-pipeline.sh -j <job-id>
# Then run translate
./prepare-job.sh in/movie.mp4 --translate -s hi -t en
./run-pipeline.sh -j <job-id>
```

## Debug Mode

### Enable Debug Logging
```bash
# Add --debug flag to any workflow
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en --debug
./run-pipeline.sh -j <job-id>

# Logs location:
# - Job preparation: logs/prepare-job.log
# - Pipeline execution: <job-dir>/logs/pipeline.log
# - Stage-specific: <job-dir>/logs/<stage>.log
```

### Check Logs
```bash
# Main pipeline log
tail -f out/YYYY/MM/DD/USER/NNN/logs/pipeline.log

# Translation log (per language)
tail -f out/YYYY/MM/DD/USER/NNN/logs/indictrans2_translation_en.log

# All logs
ls -la out/YYYY/MM/DD/USER/NNN/logs/
```

## Output Structure
```
out/
└── YYYY/
    └── MM/
        └── DD/
            └── USER/
                └── NNN/               # Job number (1, 2, 3, ...)
                    ├── job.json       # Job configuration
                    ├── manifest.json  # Stage tracking
                    ├── .job-<id>.env  # Environment variables
                    ├── media/
                    │   ├── <original>.mp4
                    │   └── audio.wav  # Extracted audio
                    ├── transcripts/
                    │   ├── segments.json       # Raw WhisperX output
                    │   ├── transcript_hi.txt   # Source language
                    │   ├── transcript_en.txt   # Target language(s)
                    │   └── segments_translated_en.json
                    ├── subtitles/
                    │   ├── hi.srt     # Source subtitle
                    │   ├── en.srt     # Target subtitle(s)
                    │   └── gu.srt
                    ├── muxed/
                    │   └── <filename>_subtitled.mkv  # Video with subtitles
                    └── logs/
                        ├── pipeline.log
                        ├── demux.log
                        ├── asr.log
                        ├── indictrans2_translation_en.log
                        └── indictrans2_translation_gu.log
```

## Performance Tips

### Faster Transcription
1. Use MLX backend on Apple Silicon: `WHISPER_BACKEND=mlx`
2. Use CUDA on NVIDIA GPUs: `WHISPERX_DEVICE=cuda`
3. Increase batch size: `BATCH_SIZE=8` (if memory permits)
4. Use smaller model for testing: `WHISPER_MODEL=medium` or `small`

### Faster Translation
1. Use GPU if available: `INDICTRANS2_DEVICE=mps` or `cuda`
2. Reduce beam search: `INDICTRANS2_NUM_BEAMS=1` (faster but less accurate)
3. Reduce max tokens: `INDICTRANS2_MAX_NEW_TOKENS=64` (for short segments)

### Memory Usage
```
Model Size vs Memory:
- tiny      →  ~1 GB RAM
- base      →  ~1.5 GB RAM
- small     →  ~2 GB RAM
- medium    →  ~5 GB RAM
- large-v2  →  ~10 GB RAM
- large-v3  →  ~10 GB RAM
```

## Common Patterns

### Test with 5-minute clip
```bash
./prepare-job.sh in/movie.mp4 --subtitle -s hi -t en \
    --start-time 00:10:00 --end-time 00:15:00 \
    --debug
```

### Process multiple files (loop)
```bash
for file in in/*.mp4; do
    echo "Processing: $file"
    ./prepare-job.sh "$file" --subtitle -s hi -t en --debug
    ./run-pipeline.sh -j <job-id>
done
```

### Resume failed job
```bash
# Check status
./run-pipeline.sh -j <job-id> --status

# Resume from last completed stage
./run-pipeline.sh -j <job-id> --resume
```

## Environment Variables (Advanced)

### System-Level Configuration
Edit `config/.env.pipeline`:
```bash
WHISPER_MODEL=large-v3
WHISPERX_DEVICE=auto           # auto-detect
WHISPER_BACKEND=auto           # auto-select
BATCH_SIZE=2
INDICTRANS2_DEVICE=auto
```

### Job-Level Override
Edit job's `.job-<id>.env` file:
```bash
# Override just for this job
WHISPER_MODEL=medium
BATCH_SIZE=4
```

## API Keys & Secrets

### HuggingFace (Required for IndicTrans2)
Create `config/secrets.json`:
```json
{
  "hf_token": "hf_..."
}
```

Get token from: https://huggingface.co/settings/tokens

## Verify Setup
```bash
# Check all environments
python tools/verify-multi-env.py

# Test transcription
./prepare-job.sh in/test.mp4 --transcribe -s hi --debug
./run-pipeline.sh -j <job-id>

# Test translation
./prepare-job.sh in/test.mp4 --translate -s hi -t en --debug
./run-pipeline.sh -j <job-id>

# Test subtitle generation
./prepare-job.sh in/test.mp4 --subtitle -s hi -t en --debug
./run-pipeline.sh -j <job-id>
```

## Documentation
- Full Guide: `docs/INDEX.md` (when refactored)
- Architecture: `docs/ARCHITECTURE.md`
- Troubleshooting: `docs/TROUBLESHOOTING.md`
- This Refactor: `COMPREHENSIVE_REFACTOR_PLAN.md`
- Session Fixes: `FIXES_APPLIED_2025-11-20_SESSION2.md`

---

**Last Updated:** November 20, 2025  
**Architecture:** Multi-Environment (4 isolated virtual environments)  
**Status:** ✅ Production Ready
