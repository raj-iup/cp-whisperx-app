# cp-whisperx-app — Context-aware Hindi→English subtitles

Short: a context-aware pipeline that produces high-quality English subtitles from Hindi/Hinglish Bollywood films.

This repository implements a production-oriented pipeline (WhisperX + diarization + NER + two-pass merge) with **Docker-first architecture** for compatibility. See `whisper-app-master-prompt.txt` for the authoritative spec.

## Architecture

**Pipeline Status:** ✅ Fully implemented (12 stages)

The pipeline uses **separate Docker containers** for ASR, diarization, and NER to avoid dependency conflicts:
- **ASR container**: WhisperX with torch 2.2.1 (compatible with pyannote)
- **Diarization container**: pyannote.audio 3.4.0 with torch 2.2.1
- **NER container**: spaCy with NumPy 1.26

## Quick layout
- `in/` — put input media files here
- `out/<MovieName>/` — per-title outputs (prompts, asr, bias windows, en_merged/*.srt, manifest.json)
- `logs/YYYYMMDD_HHMMSS/` — timestamped run logs and manifests
- `config/.env` — all tunables (the code reads this file)
- `config/secrets.json` — secrets (HF token, TMDB API key, pyannote token)
- `scripts/` — Python pipeline modules (ASR, diarization, NER, etc.)
- `docker/` — Dockerfiles for ASR, diarization, and NER services
- `run_pipeline.py` — main pipeline orchestrator

## Bootstrap (Docker recommended)

### 1. Install prerequisites

macOS:
```bash
brew install ffmpeg mkvtoolnix docker
open --background -a Docker  # Start Docker Desktop
```

Linux:
```bash
sudo apt-get install ffmpeg mkvtoolnix docker docker-compose
```

### 2. Configure secrets

Create `./config/secrets.json`:
```json
{
  "hf_token": "<HUGGING_FACE_TOKEN>",
  "tmdb_api_key": "<TMDB_API_KEY>",
  "pyannote_token": "<PYANNOTE_HF_TOKEN>"
}
```

**Getting tokens:**
- HF token: https://huggingface.co/settings/tokens (Read access)
- TMDB API: https://www.themoviedb.org/settings/api
- Pyannote: Same as HF token, but requires accepting license at https://huggingface.co/pyannote/speaker-diarization

### 3. Build Docker containers

```bash
docker compose build
```

This builds three containers:
- `asr`: WhisperX for transcription + translation
- `diarization`: pyannote.audio for speaker diarization
- `ner`: spaCy for named entity recognition

### 4. Run preflight checks

```bash
chmod +x scripts/preflight.sh
./scripts/preflight.sh
```

Validates:
- System binaries (ffmpeg, mkvmerge)
- Docker containers
- API tokens
- Python modules in containers

## Running the pipeline

### Basic usage

```bash
python3 ./run_pipeline.py -i "in/Movie.mkv" --infer-tmdb-from-filename
```

### Options

- `-i, --input`: Input video file path
- `--infer-tmdb-from-filename`: Extract movie info from filename and enrich with TMDB
- `--two-pass-merge`: Enable translation refinement (enabled by default via config)
- `--prep-prompt`: Only prepare prompts, don't run ASR

### Configuration

Edit `./config/.env` to control:
- `CLIP_VIDEO=true` / `CLIP_MINUTES=5` — Clip first N minutes for testing
- `WINDOW_SECONDS=45` / `STRIDE_SECONDS=15` — Bias window settings
- `SECOND_PASS_ENABLED=true` — Translation refinement
- `DEVICE_DIARIZATION=` — Empty to skip diarization, or "CPU"
- `NER_ENABLED=false` — Enable/disable NER
- `SRC_LANG=hi` / `TGT_LANG=en` — Source and target languages

## Pipeline stages

## Pipeline stages

The pipeline executes 12 stages:

1. **Filename parsing** — Extract title and year from filename
2. **Era detection** — Load era-specific lexicon (1950s-2020s) with names, places, terms
3. **TMDB enrichment** — Fetch cast/crew from TMDB API (optional)
4. **Prompt assembly** — Combine filename, era, and TMDB data into initial prompts
5. **Video clipping** — Optional: clip first N minutes for testing
6. **Bias window creation** — Generate rolling 45s windows with context-aware term lists
7. **WhisperX ASR** — Transcription + translation in Docker container
8. **Diarization** — Speaker separation with pyannote.audio in Docker container (optional)
9. **Translation refinement** — Two-pass merge to improve English quality (optional)
10. **NER extraction** — Named entity recognition with spaCy in Docker container (optional)
11. **SRT generation** — Create final subtitle file with proper formatting
12. **Video muxing** — Embed subtitles in MP4 (mov_text) or MKV fallback

## Output structure

```
out/<MovieName>/
├── <name>.initial_prompt.txt           # Basic title/year prompt
├── <name>.combined.initial_prompt.txt  # Full prompt with era + TMDB
├── <name>.combined.initial_prompt.md   # YAML + prompt markdown
├── bias/
│   └── bias.window.NNNN.json           # Per-window bias terms
├── asr/
│   └── <name>.asr.json                 # WhisperX output with alignments
├── <name>.rttm                         # Diarization output (if enabled)
├── diarization_stats.json              # Speaker statistics (if enabled)
├── entities_spacy.json                 # NER results (if enabled)
├── en_merged/
│   └── <name>.merged.srt               # Final subtitles
├── <name>.subs.mp4                     # Video with embedded subtitles
└── manifest.json                       # Run metadata

logs/YYYYMMDD_HHMMSS/
├── manifest.json                       # Global manifest
└── pipeline.log                        # Execution log
```

## Docker architecture

### Why Docker?

The pipeline components have conflicting dependencies:
- WhisperX uses pyannote.audio which requires specific torch/torchaudio versions
- spaCy NER requires NumPy 1.26 vs WhisperX requiring NumPy 2.x
- On macOS, torch/torchaudio binary compatibility issues

Docker containers solve this by isolating each component.

### Container details

**ASR container** (`docker/asr/`):
- Base: Python 3.11
- Torch: 2.2.1 (CPU, compatible with pyannote)
- Key packages: whisperx, transformers, faster-whisper
- Handles: Transcription, translation, alignment

**Diarization container** (`docker/diarization/`):
- Base: Python 3.11
- Torch: 2.2.1 + torchaudio 2.2.1
- Key packages: pyannote.audio 3.4.0, speechbrain
- Handles: Speaker diarization, speaker assignment

**NER container** (`docker/ner/`):
- Base: Python 3.11
- NumPy: 1.26 (required by spaCy)
- Key packages: spaCy, en_core_web_trf
- Handles: Named entity recognition, canonicalization

### Container execution

The pipeline automatically:
1. Creates Python scripts for each stage
2. Mounts the output directory to containers
3. Executes scripts inside appropriate containers
4. Reads results back to host

No manual container management needed!

## Troubleshooting

### Docker daemon not running
```bash
# macOS
open --background -a Docker
docker info  # Verify it's running

# Linux
sudo systemctl start docker
```

### Container build failures
```bash
# Rebuild without cache
docker compose build --no-cache

# Check disk space
docker system df
docker system prune -a  # Clean up if needed
```

### ASR/Diarization torchaudio errors
This is resolved in the current setup. Both containers use torch 2.2.1 which is compatible with pyannote.audio 3.4.0.

### TMDB not finding movies
- Check API key in `config/secrets.json`
- Try exact title from TMDB website
- Year helps narrow results: `--infer-tmdb-from-filename`

### Clipped video for testing
Default config clips first 5 minutes. Edit `config/.env`:
```bash
CLIP_VIDEO=false  # Process full video
# or
CLIP_MINUTES=10   # Clip first 10 minutes
```

## Development

### Local development (without Docker)

For development on the host (not recommended for production):

```bash
./scripts/bootstrap.sh  # Creates .bollyenv
source .bollyenv/bin/activate
```

**Note:** On macOS, you'll encounter torch/torchaudio incompatibilities with pyannote. Use Docker for reliable execution.

### Adding new pipeline stages

1. Create module in `scripts/` (e.g., `scripts/new_stage.py`)
2. Import in `run_pipeline.py`
3. Add execution logic in main pipeline flow
4. Update manifest builder to track the stage
5. Update this README

### Modifying container dependencies

1. Edit `requirements-asr.txt`, `requirements-diarization.txt`, or `requirements-ner.txt`
2. Rebuild container: `docker compose build <service>`
3. Test: `docker compose run --rm <service> python -c "import module"`

## Advanced configuration

### Bias windowing

Controls context-aware prompt injection:
```bash
WINDOW_SECONDS=45    # Window size
STRIDE_SECONDS=15    # Overlap between windows
BIAS_TOPK=10        # Top N terms per window
BIAS_DECAY=0.9      # Decay factor (future use)
```

### Translation backends

```bash
SECOND_PASS_BACKEND=opus-mt  # Fast, good quality
# Also supports: mbart50, nllb200
```

### Device selection

```bash
DEVICE_WHISPERX=CPU        # Always CPU in Docker
DEVICE_DIARIZATION=        # Empty = skip, "CPU" = enable
DEVICE_SECOND_PASS=CPU
DEVICE_SPACY=CPU
```

## Prior art and references

- WhisperX: https://github.com/m-bain/whisperX
- pyannote.audio: https://github.com/pyannote/pyannote-audio
- spaCy: https://spacy.io/
- TMDB API: https://www.themoviedb.org/documentation/api

## License

See LICENSE file for details.

---

**Last updated:** 2025-10-28  
**Pipeline version:** 1.0.0  
**Status:** Production-ready with Docker containers
`pyannote.audio` on the host. Host-side instructions and conda/mamba examples have been removed from this
README to reduce confusion and keep the documentation focused on the container workflow.

---------------------------------
- Start Docker Desktop (macOS) or ensure the Docker daemon/service is running.
  On macOS you can start Docker Desktop from the Applications folder or from the command line:

```bash
open --background -a Docker
# wait until Docker reports it's running, then verify:
docker info
```

- If you are on Apple Silicon and want to run amd64 images use the `--platform linux/amd64` flag when building,
  but note that using amd64 images on Apple Silicon will run under emulation and may increase build/run time.

- If you see an error like "Could not open requirements file" during build it usually means the Docker
  build context did not include the repository root. The provided `docker-compose.yml` uses the repo root
  as the build context so pinned `requirements-*.txt` are available to the Dockerfile.

Security & notes
- Do not commit `config/secrets.json` to the repo. If secret files accidentally were committed, rotate tokens immediately and remove them from git history.
- The project reads `./config/.env` — do not use shell-exported env vars as the source of truth.

## Security notes

- Do not commit `config/secrets.json` to the repo. If secret files accidentally were committed, rotate tokens immediately and remove them from git history.
- Add `config/secrets.json` to `.gitignore`
- The project reads `./config/.env` — do not use shell-exported env vars as the source of truth.

## CI/CD and Docker Registry (Optional)

### GitHub Actions

The repository includes scripts for building and pushing Docker images. For CI/CD:

1. Add GitHub secrets:
   - `DOCKERHUB_USERNAME` — your Docker Hub username
   - `DOCKERHUB_TOKEN` — Docker Hub access token with push permissions

2. GitHub Actions will build and push images with cache layers

### Manual Docker image publishing

Build and push to your own registry:

```bash
# Login to Docker Hub
docker login

# Build all containers
docker compose build

# Tag and push
docker tag rajiup/cp-whisperx-app-asr:latest <YOUR_USER>/cp-whisperx-app-asr:latest
docker push <YOUR_USER>/cp-whisperx-app-asr:latest

# Repeat for diarization and ner containers
```

For multi-arch images (amd64 + arm64):
```bash
docker buildx build --platform linux/amd64,linux/arm64 \
  -f docker/asr/Dockerfile \
  -t <YOUR_USER>/cp-whisperx-app-asr:latest --push .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and test with Docker
4. Update README if adding new features
5. Submit pull request

## Support

- Issues: Open a GitHub issue
- Documentation: See `whisper-app-master-prompt.txt` for detailed spec
- Logs: Check `logs/YYYYMMDD_HHMMSS/pipeline.log` for debugging
