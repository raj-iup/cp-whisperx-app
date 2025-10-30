# Native MPS Pipeline - Quick Start Guide

Complete guide to running the native MPS-optimized speech-to-text pipeline with highest accuracy settings.

## Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3)
- **Python 3.9+** installed
- **FFmpeg** installed (`brew install ffmpeg`)
- **~10GB** free disk space for models
- **TMDB API Key** (optional, for metadata)
- **HuggingFace Token** (optional, for future diarization)

---

## Quick Start (3 Steps)

### 1. Setup Environment

Clone and configure the repository:

```bash
cd /Users/rpatel/Projects/cp-whisperx-app

# Create secrets file
cp config/secrets.example.json config/secrets.json

# Edit secrets (optional but recommended)
# Add your API keys:
# - tmdb_api_key: Get from https://www.themoviedb.org/settings/api
# - hf_token: Get from https://huggingface.co/settings/tokens
nano config/secrets.json
```

**Example secrets.json:**
```json
{
  "hf_token": "hf_xxxxxxxxxxxxxxxxxxxxx",
  "tmdb_api_key": "your_tmdb_api_key_here",
  "pyannote_token": "hf_xxxxxxxxxxxxxxxxxxxxx"
}
```

### 2. Install Dependencies

Create all virtual environments and install dependencies:

```bash
./native/setup_venvs.sh
```

This will:
- Create 10 isolated virtual environments (one per pipeline stage)
- Install all required Python packages
- Takes ~5-10 minutes depending on your internet speed

**Expected output:**
```
======================================================================
MPS Native Pipeline - Virtual Environment Setup
======================================================================
[1/10] Creating venv for demux...
[2/10] Creating venv for tmdb...
...
✓ All virtual environments created successfully
```

### 3. Run Pipeline

Process your video with the highest accuracy settings:

```bash
# Place your video in the 'in' directory
mkdir -p in
cp /path/to/your/video.mp4 in/

# Run pipeline with large-v3 model for maximum accuracy
./native/pipeline.sh "in/your_video.mp4"
```

**For custom model settings**, edit the ASR stage directly:

```bash
# Run with custom parameters (requires manual invocation)
source native/venvs/asr/bin/activate
export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"

python native/scripts/07_asr.py \
    --input "in/your_video.mp4" \
    --movie-dir "out/your_video" \
    --model large-v3 \
    --compute-type float16 \
    --batch-size 8 \
    --language hi
```

---

## Pipeline Configuration

### High Accuracy Configuration (Recommended)

For best results with the **large-v3** model on Apple Silicon:

| Parameter | Value | Description |
|-----------|-------|-------------|
| `--model` | `large-v3` | Highest accuracy Whisper model |
| `--compute-type` | `float16` | Best balance of speed/accuracy on MPS |
| `--batch-size` | `8` | Optimal for 16GB+ RAM |
| `--language` | `auto` or specific code | Auto-detect or specify (e.g., `en`, `hi`, `es`) |

**Environment Variables:**
```bash
export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"
```

### Model Options

| Model | Size | Speed | Accuracy | RAM Required |
|-------|------|-------|----------|--------------|
| `tiny` | 75 MB | Fastest | Lowest | 4 GB |
| `base` | 145 MB | Fast | Good | 4 GB |
| `small` | 465 MB | Medium | Better | 8 GB |
| `medium` | 1.5 GB | Slow | Great | 8 GB |
| `large-v2` | 3 GB | Very Slow | Excellent | 16 GB |
| `large-v3` | 3 GB | Very Slow | **Best** | 16 GB |

### Compute Type Options

| Type | Precision | Speed | Accuracy | Device Support |
|------|-----------|-------|----------|----------------|
| `float32` | Full | Slowest | Highest | CPU, MPS |
| `float16` | Half | **Recommended** | Very High | MPS (Apple Silicon) |
| `int8` | Quantized | Fastest | Good | CPU, MPS |

---

## Pipeline Stages

The pipeline runs 10 sequential stages:

1. **Demux** (12s) - Extract audio from video
2. **TMDB** (1s) - Fetch movie metadata
3. **Pre-NER** (4s) - Extract character names from metadata
4. **Silero-VAD** (45s) - Voice activity detection
5. **Pyannote-VAD** (0.01s) - VAD refinement (simplified)
6. **Diarization** (0.02s) - Speaker identification
7. **ASR** (15-30 min) - Speech-to-text transcription ⏱️
8. **Post-NER** (0s) - Entity correction
9. **Subtitle-Gen** (0s) - Generate SRT subtitles
10. **Mux** (4s) - Embed subtitles in video

**Total Time:** ~20-40 minutes for a 2-hour movie (with large-v3 on CPU fallback)

---

## Usage Examples

### Basic Usage (Auto-detect language)

```bash
./native/pipeline.sh "in/movie.mp4"
```

### Hindi to English (Manual stage run)

For full control over ASR parameters:

```bash
# Run stages 1-6 normally
./native/pipeline.sh "in/hindi_movie.mp4"

# Stop after diarization, then run ASR manually with custom settings
source native/venvs/asr/bin/activate
export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"

python native/scripts/07_asr.py \
    --input "in/hindi_movie.mp4" \
    --movie-dir "out/hindi_movie" \
    --model large-v3 \
    --compute-type float16 \
    --language hi \
    --batch-size 8

# Continue with remaining stages
source native/venvs/post-ner/bin/activate
python native/scripts/08_post_ner.py --input "in/hindi_movie.mp4" --movie-dir "out/hindi_movie"
# ... and so on
```

### Process Multiple Files

```bash
for video in in/*.mp4; do
    ./native/pipeline.sh "$video"
done
```

---

## Output Structure

After completion, your output directory will contain:

```
out/Movie_Name_2024/
├── audio/
│   └── audio.wav                    # 16kHz mono audio
├── metadata/
│   └── tmdb_data.json               # Movie metadata
├── entities/
│   ├── pre_ner.json                 # Character names
│   └── post_ner.json                # Corrected entities
├── vad/
│   ├── silero_segments.json         # Voice activity segments
│   └── pyannote_segments.json       # Refined VAD
├── diarization/
│   └── speaker_segments.json        # Speaker-labeled segments
├── transcription/
│   ├── transcription.json           # Full transcription
│   └── transcription_stats.json     # Statistics
├── subtitles/
│   └── Movie_Name_2024.srt          # Generated subtitles
├── manifest.json                     # Pipeline metadata
├── mux_stats.json                   # Muxing statistics
└── Movie_Name_2024_subtitled.mp4    # 🎬 Final video with subtitles
```

---

## Monitoring Progress

### Real-time Log Monitoring

```bash
# Watch pipeline progress
tail -f logs/pipeline_run_*.log

# Watch specific stage
tail -f logs/asr_*.log
```

### Check Pipeline Status

```bash
# View manifest
cat out/Movie_Name/manifest.json | python3 -m json.tool

# Check which stages completed
cat out/Movie_Name/manifest.json | python3 -m json.tool | grep "status"
```

---

## Troubleshooting

### Virtual Environment Issues

If you encounter dependency conflicts:

```bash
# Remove all venvs and recreate
rm -rf native/venvs
./native/setup_venvs.sh
```

### ASR Running Too Slow

The large-v3 model is compute-intensive. For faster processing:

```bash
# Use medium model (good balance)
python native/scripts/07_asr.py \
    --model medium \
    --compute-type float16 \
    --batch-size 16
```

### Out of Memory

Reduce batch size or use smaller model:

```bash
--batch-size 4    # For 8GB RAM
--batch-size 2    # For 4GB RAM
--model medium    # Smaller model
```

### FFmpeg Not Found

```bash
# Install FFmpeg
brew install ffmpeg

# Verify installation
ffmpeg -version
```

### Python Import Errors

Ensure PYTHONPATH is set:

```bash
export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"
```

---

## Performance Optimization

### For Apple Silicon (M1/M2/M3)

1. **Use float16** for best MPS performance
2. **Increase batch size** if you have 32GB+ RAM
3. **Enable MPS** in device settings (automatically preferred)

```bash
# Optimal settings for M1 Max / M2 Max / M3 Max
--compute-type float16
--batch-size 16
```

### For Limited RAM (8GB)

```bash
--model small
--compute-type int8
--batch-size 4
```

### For Speed Priority

```bash
--model base
--compute-type int8
--batch-size 32
```

---

## Advanced Configuration

### Custom Pipeline Workflow

To run individual stages:

```bash
# Activate stage venv
source native/venvs/STAGE_NAME/bin/activate
export PYTHONPATH="$PWD:$PWD/shared:$PWD/native/utils:$PYTHONPATH"

# Run stage script
python native/scripts/XX_stage_name.py \
    --input "in/video.mp4" \
    --movie-dir "out/video"
```

### Modify ASR Script Defaults

Edit `native/scripts/07_asr.py`:

```python
# Line ~140-145
default_config = {
    'model_name': 'large-v3',      # Change default model
    'compute_type': 'float16',     # Change precision
    'language': 'hi',              # Set default language
    'batch_size': 8                # Set batch size
}
```

### Skip Stages

Comment out unwanted stages in `native/pipeline.sh`:

```bash
stages=(
    "demux:01_demux.py:Audio extraction"
    "tmdb:02_tmdb.py:Metadata fetch"
    # "pre-ner:03_pre_ner.py:Entity extraction"  # Skip this
    "silero-vad:04_silero_vad.py:Coarse VAD"
    # ... rest of stages
)
```

---

## FAQ

**Q: How long does it take to process a 2-hour movie?**  
A: With large-v3: ~30-40 minutes. With base model: ~5-10 minutes.

**Q: Can I use CUDA instead of MPS?**  
A: This is optimized for Apple Silicon MPS. For CUDA, use the Docker pipeline.

**Q: What languages are supported?**  
A: 99+ languages including English, Hindi, Spanish, French, German, Chinese, Japanese, etc.

**Q: Can I run this on Intel Mac or Linux?**  
A: Yes, but MPS acceleration won't be available. It will fall back to CPU.

**Q: How do I improve accuracy?**  
A: Use `--model large-v3` and specify the source language with `--language`.

**Q: Where are the models downloaded?**  
A: `~/.cache/torch/` and `~/.cache/huggingface/`

---

## Next Steps

- **View logs:** Check `logs/` directory for detailed execution logs
- **Customize settings:** Edit stage scripts for fine-tuned control
- **Batch processing:** Create shell scripts to process multiple files
- **Integration:** Use the output JSON/SRT files in your applications

---

## Support

For issues or questions:

1. Check logs in `logs/` directory
2. Review manifest.json for stage status
3. Consult individual stage documentation in `docs/`
4. Check GitHub issues for common problems

---

**Happy transcribing! 🎬🎤✨**
