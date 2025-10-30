# Quick Start Guide - Pipeline Usage

## Prerequisites
- Docker and Docker Compose installed
- HuggingFace token in `config/.env` (for diarization/pyannote models)
- Input video in `in/` directory

## Build the Pipeline

```bash
# Build all containers
docker compose build

# Or build specific containers
docker compose build diarization
docker compose build asr
docker compose build post-ner
docker compose build subtitle-gen
```

## Run the Complete Pipeline

```bash
# Full pipeline with TMDB metadata
python3 pipeline.py \
  -i "in/Movie_Name_2006.mp4" \
  --infer-tmdb-from-filename

# With options
python3 pipeline.py \
  -i "in/Movie_Name_2006.mp4" \
  --infer-tmdb-from-filename \
  --skip-vad              # Skip VAD stages (testing only)
  --skip-diarization      # Skip diarization (not recommended)
```

## Run Individual Stages (Testing)

```bash
# Stage 1: Demux (audio extraction)
docker compose run --rm demux in/movie.mp4

# Stage 3: Pre-NER (entity extraction)
docker compose run --rm pre-ner /app/out/Movie_Name

# Stage 4: Silero VAD
docker compose run --rm silero-vad /app/out/Movie_Name

# Stage 5: PyAnnote VAD
docker compose run --rm pyannote-vad /app/out/Movie_Name

# Stage 6: Diarization (speaker labeling)
docker compose run --rm diarization /app/out/Movie_Name

# Stage 7: ASR (transcription + translation)
docker compose run --rm asr /app/out/Movie_Name

# Stage 8: Post-NER (entity correction)
docker compose run --rm post-ner /app/out/Movie_Name

# Stage 9: Subtitle Generation
docker compose run --rm subtitle-gen /app/out/Movie_Name

# Stage 10: Mux (embed subtitles)
docker compose run --rm mux in/movie.mp4 out/Movie_Name/en_merged/Movie_Name.merged.srt out/Movie_Name/Movie_Name.subs.mp4
```

## Check Outputs

```bash
# View output structure
ls -R out/Movie_Name/

# Expected structure:
# out/Movie_Name/
# ├── audio/audio.wav                      (Stage 1)
# ├── metadata/tmdb.json                   (Stage 2)
# ├── pre_ner/entities.json               (Stage 3)
# ├── vad/
# │   ├── silero_segments.json            (Stage 4)
# │   └── pyannote_refined_segments.json  (Stage 5)
# ├── diarization/
# │   ├── Movie_Name.diarized.json        (Stage 6)
# │   ├── Movie_Name.diarized.txt
# │   └── Movie_Name.diarized.srt
# ├── asr/
# │   ├── Movie_Name.asr.json             (Stage 7)
# │   ├── Movie_Name.asr.txt
# │   └── Movie_Name.asr.meta.json
# ├── post_ner/
# │   ├── Movie_Name.corrected.json       (Stage 8)
# │   └── Movie_Name.corrected.txt
# ├── en_merged/
# │   └── Movie_Name.merged.srt           (Stage 9)
# └── Movie_Name.subs.mp4                 (Stage 10)

# View subtitle file
cat out/Movie_Name/en_merged/Movie_Name.merged.srt

# Check logs
tail -f logs/orchestrator_*.log
```

## Configuration

Edit `config/.env` to customize:

```bash
# Required
HF_TOKEN=hf_xxxxxxxxxxxxx

# Model Selection
WHISPER_MODEL=large-v2          # or large-v3, medium, small
DEVICE=cpu                      # or cuda, mps
COMPUTE_TYPE=int8               # or float16, float32

# Languages
SOURCE_LANG=hi                  # Source audio language
TARGET_LANG=en                  # Target subtitle language

# Diarization
MIN_SPEAKERS=2                  # Optional minimum speakers
MAX_SPEAKERS=10                 # Optional maximum speakers

# Subtitle Options
MERGE_SUBTITLES=true            # Merge consecutive short subtitles
INCLUDE_SPEAKER=true            # Add [SPEAKER_00] prefix
MAX_SUBTITLE_DURATION=7.0       # Max seconds per subtitle
MAX_SUBTITLE_CHARS=84           # Max characters per subtitle
```

## Troubleshooting

### Container fails to build
```bash
# Check Docker logs
docker compose logs <service-name>

# Try rebuilding without cache
docker compose build --no-cache <service-name>
```

### HuggingFace token error
```bash
# Verify token is set
cat config/.env | grep HF_TOKEN

# Test token validity
# Visit: https://huggingface.co/settings/tokens
```

### Out of memory
```bash
# Use smaller model
# In config/.env:
WHISPER_MODEL=medium            # Instead of large-v2
COMPUTE_TYPE=int8               # For lower memory usage

# Or increase Docker memory limit
# Edit docker-compose.yml: mem_limit: 10g
```

### Audio file not found
```bash
# Check demux output
ls -lh out/Movie_Name/audio/

# Verify FFmpeg extraction
docker compose run --rm demux in/movie.mp4
```

## Performance Tips

1. **Use GPU if available:**
   ```bash
   # In config/.env
   DEVICE=cuda
   COMPUTE_TYPE=float16
   ```

2. **Test on short clips first:**
   ```bash
   # Create 5-minute test clip
   ffmpeg -i in/full_movie.mp4 -t 300 -c copy in/test_clip.mp4
   
   # Run pipeline
   python3 pipeline.py -i "in/test_clip.mp4"
   ```

3. **Monitor resource usage:**
   ```bash
   # Watch Docker stats
   docker stats
   ```

## Support

- **Documentation:** See `WORKFLOW_IMPLEMENTATION_COMPLETE.md`
- **Architecture:** See `workflow-arch.txt`
- **Build Summary:** See `BUILD_SUMMARY.md`
- **Logs:** Check `logs/` directory for detailed execution logs
