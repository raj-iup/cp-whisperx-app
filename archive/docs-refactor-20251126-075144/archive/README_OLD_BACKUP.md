# cp-whisperx-app

**AI-powered transcription and translation pipeline for Indian language content**

Transcribe audio/video in 22 Indian languages and translate to English (or other Indian languages) using WhisperX, MLX-Whisper, and IndicTrans2.

> **📖 NEW:** [Correct Setup Guide](docs/CORRECT_SETUP_GUIDE.md) - Authoritative setup instructions  
> **⚠️ Note:** Setup is simple - just run `./bootstrap.sh` (or `.\bootstrap.ps1` on Windows). That's it!

---

## Features

✅ **Transcribe Workflow**: Audio → Text with timestamps  
✅ **Translate Workflow**: Text → English subtitles  
✅ **22 Indian Languages**: Hindi, Tamil, Telugu, Bengali, and more  
✅ **GPU Acceleration**: Full Apple Silicon (MPS) and NVIDIA (CUDA) support  
✅ **MLX Integration**: 6-8x faster on Apple Silicon  
✅ **IndicTrans2**: State-of-the-art Indian language translation  

---

## Quick Start

### 1. Setup

```bash
# Run bootstrap (one-time setup: creates environment, installs dependencies, detects hardware, downloads models)
./bootstrap.sh              # macOS/Linux (auto-installs MLX on Apple Silicon)
.\bootstrap.ps1             # Windows

# Optional: Manual MLX install (Apple Silicon only, if bootstrap skipped it)
./install-mlx.sh            # Installs MLX into existing .bollyenv
./bootstrap.sh              # Re-run to detect MLX and update config
```

**Note:** Bootstrap automatically creates the `.bollyenv` virtual environment and installs all Python dependencies (including MLX-Whisper on Apple Silicon). No need to run `pip install` manually!

### 2. Transcribe (Audio → Text in Source Language)

```bash
# Prepare job
./prepare-job.sh "path/to/video.mp4" --transcribe -s hi

# Run pipeline
./run-pipeline.sh -j <job-id>
```

**Purpose**: Transcribe Indian language audio to text in the **same source language**

**Output**: Transcript text file (JSON) with word-level timestamps in `out/YYYY/MM/DD/[UserID]/[counter]/transcripts/`

**Example**: Hindi audio → Hindi text transcript

---

### 3. Translate (Audio → Source Text → Target Text + Target Subtitle)

```bash
# Prepare job (auto-runs transcribe if needed)
./prepare-job.sh "path/to/video.mp4" --translate -s hi -t en

# Run pipeline (single command does everything!)
./run-pipeline.sh -j <job-id>
```

**Purpose**: Complete workflow - auto-transcribes (if needed), then translates to target language

**Auto-execution**: If transcript doesn't exist, automatically runs transcribe workflow first

**Output**: 
- Source language transcript (auto-generated if needed)
- Target language transcript  
- Target language subtitle (.srt)

**Location**: `out/YYYY/MM/DD/[UserID]/[counter]/subtitles/`

**Example**: Hindi audio → Hindi text (auto) → English text → English .srt

---

### 4. Subtitle (Complete Dual-Subtitle Workflow)

```bash
# Prepare job (generates subtitles in BOTH languages)
./prepare-job.sh "path/to/video.mp4" --subtitle -s hi -t en

# Run pipeline
./run-pipeline.sh -j <job-id>
```

**Purpose**: Complete subtitle workflow with subtitles in **both source and target languages**

**Auto-execution**: Automatically runs transcribe + translate workflows

**Output**:
- Source language transcript
- Target language transcript
- **Source language subtitle (.srt)** ⭐
- **Target language subtitle (.srt)** ⭐

**Example**: Hindi audio → Hindi text → Hindi .srt + English text → English .srt

---

## Supported Languages

**22 Indian Languages**:

Hindi (hi), Tamil (ta), Telugu (te), Bengali (bn), Gujarati (gu), Kannada (kn), Malayalam (ml), Marathi (mr), Punjabi (pa), Urdu (ur), Assamese (as), Odia (or), Nepali (ne), Sindhi (sd), Sinhala (si), Sanskrit (sa), Kashmiri (ks), Dogri (doi), Manipuri (mni), Konkani (kok), Maithili (mai), Santali (sat)

**Target Languages**: English (en) + all 22 Indian languages

---

## Performance

### Apple M1 Pro (2-hour movie)

| Workflow | Time | Speedup |
|----------|------|---------|
| **Transcribe** (with MLX) | ~17 min | 5.6x faster |
| **Translate** (IndicTrans2) | ~5-7 min | 2x faster |

*CPU-only would take ~95 min for transcribe, ~10 min for translate*

---

## Architecture

```
Input (Video/Audio)
    ↓
┌───────────────────┐
│ Transcribe        │  Demux → ASR (MLX/WhisperX) → Align
└───────────────────┘
    ↓
Transcripts (JSON)
    ↓
┌───────────────────┐
│ Translate         │  Extract → IndicTrans2 → Generate
└───────────────────┘
    ↓
Subtitles (.srt, .vtt)
```

### Backend Selection

| Device | Backend | GPU Acceleration |
|--------|---------|------------------|
| Apple Silicon (MPS) | MLX-Whisper | ✅ Full GPU |
| NVIDIA (CUDA) | WhisperX | ✅ Full GPU |
| CPU | WhisperX | ❌ CPU only |

**Automatic**: The pipeline detects your hardware and uses the best backend.

---

## Project Structure

```
cp-whisperx-app/
├── README.md                    # This file
├── prepare-job.sh               # Job preparation wrapper
├── run-pipeline.sh              # Pipeline execution wrapper
├── install-mlx.sh               # MLX installation (Apple Silicon)
├── scripts/
│   ├── bootstrap.sh             # Hardware detection & setup
│   ├── prepare-job.py           # Job preparation logic
│   └── run-pipeline.py          # Pipeline orchestrator
├── shared/                      # Shared utilities (logging, manifest, etc.)
├── tools/                       # IndicTrans2, NER, utilities
├── config/                      # Configuration files
│   ├── .env.pipeline            # Pipeline configuration
│   └── secrets.json             # API tokens (optional)
├── in/                          # Input media files
├── out/                         # Output (transcripts, subtitles, logs)
│   └── YYYY/MM/DD/UserID/counter/  # Date/user/counter structure
│                                   # Job ID: job-YYYYMMDD-UserID-nnnn
└── docs/                        # Documentation
    ├── ARCHITECTURE.md          # Technical architecture
    ├── CONFIGURATION.md         # Configuration guide
    ├── MLX_ACCELERATION_GUIDE.md # MLX setup guide
    └── IMPLEMENTATION_COMPLETE.md # Implementation summary
```

---

## Requirements

### Minimum
- **OS**: macOS 12+ or Linux
- **Python**: 3.9+
- **RAM**: 8GB
- **Storage**: 10GB for models

### Recommended (Apple Silicon)
- **Chip**: M1 Pro/Max/Ultra, M2/M3
- **RAM**: 16GB+ unified memory
- **Storage**: 20GB
- **MLX**: Installed via `./install-mlx.sh`

### Recommended (NVIDIA)
- **GPU**: 8GB+ VRAM
- **CUDA**: 11.0+
- **Drivers**: Latest NVIDIA drivers

---

## Documentation

### User Guides
- **[MLX Acceleration Guide](docs/MLX_ACCELERATION_GUIDE.md)** - Setup MLX for Apple Silicon
- **[IndicTrans2 Workflow Guide](docs/INDICTRANS2_WORKFLOW_README.md)** - Detailed workflow examples
- **[Quick Start](docs/INDICTRANS2_QUICKSTART.md)** - Getting started

### Technical Documentation
- **[Architecture](docs/ARCHITECTURE.md)** - Complete system architecture
- **[Configuration](docs/CONFIGURATION.md)** - Configuration hierarchy
- **[Implementation](docs/IMPLEMENTATION_COMPLETE.md)** - Implementation summary

### Reference
- **[IndicTrans2 Reference](docs/INDICTRANS2_REFERENCE.md)** - API reference
- **[Bug Fixes](docs/BUGFIX_SUMMARY.md)** - Issues and resolutions

---

## Configuration

### Hardware Detection

Bootstrap automatically detects your hardware and creates `out/hardware_cache.json`:

```json
{
  "gpu_type": "mps",
  "gpu_name": "Apple M1 Pro",
  "recommended_settings": {
    "whisper_backend": "mlx",
    "whisper_model": "large-v3",
    "compute_type": "float16",
    "batch_size": 2
  }
}
```

### Job Configuration

Each job gets a `.job-id.env` file with hardware-optimized settings:

```bash
WHISPER_BACKEND=mlx              # Backend: mlx, whisperx
WHISPERX_DEVICE=mps              # Device: mps, cuda, cpu
WHISPER_MODEL=large-v3           # Model size
WHISPER_COMPUTE_TYPE=float16     # Precision
BATCH_SIZE=2                     # Batch size
INDICTRANS2_DEVICE=mps           # Translation device
```

---

## Workflows

### Transcribe Workflow

**Purpose**: Convert audio to text with timestamps

**Stages**:
1. **Demux**: Extract audio from video
2. **ASR**: Transcribe using MLX-Whisper or WhisperX
3. **Align**: Add word-level timestamps

**Output**:
- `transcripts/segments.json` - Segment-level transcripts
- `transcripts/aligned.json` - Word-level aligned transcripts

### Translate Workflow

**Purpose**: Translate text to English subtitles

**Stages**:
1. **Extract**: Load existing transcripts or create new
2. **Translate**: Translate using IndicTrans2
3. **Generate**: Create SRT/VTT subtitle files

**Output**:
- `subtitles/movie.srt` - SRT subtitle file
- `subtitles/movie.vtt` - WebVTT subtitle file

---

## Advanced Usage

### Custom Model Size

Edit job's `.env` file before running pipeline:

```bash
WHISPER_MODEL=medium             # Options: tiny, base, small, medium, large-v2, large-v3
```

### Force CPU (Disable GPU)

```bash
WHISPERX_DEVICE=cpu
WHISPER_BACKEND=whisperx
```

### Batch Size Adjustment

```bash
BATCH_SIZE=1                     # Lower = less memory, slower
BATCH_SIZE=4                     # Higher = more memory, faster
```

---

## Logging & Debugging

### Log Files

All scripts automatically create timestamped log files:

**Bash/PowerShell Scripts:**
- Location: `logs/YYYYMMDD-HHMMSS-scriptname.log`
- Example: `logs/20251119-143045-bootstrap.log`

**Python Pipeline Scripts:**
- Location: `out/YYYY/MM/DD/UserID/JobID/logs/`
- Format: `{stage_num:02d}_{stage_name}_{timestamp}.log`
- Example: `06_asr_20251119_143000.log`

### Enable Debug Mode

**Bash:**
```bash
LOG_LEVEL=DEBUG ./prepare-job.sh movie.mp4 --transcribe -s hi
```

**PowerShell:**
```powershell
$env:LOG_LEVEL="DEBUG"
.\prepare-job.ps1 movie.mp4 -Transcribe -SourceLanguage hi
```

**Pipeline Scripts:**
```bash
# Edit config/.env.pipeline
LOG_LEVEL=DEBUG
```

### View Logs

```bash
# Latest bootstrap log
ls -lt logs/ | head -1

# View specific log
cat logs/20251119-143045-bootstrap.log

# Pipeline logs for a job
ls out/2025/11/19/user01/job-0001/logs/

# Watch logs in real-time
tail -f logs/20251119-143045-bootstrap.log
```

### Log Levels

| Level | Usage | Output |
|-------|-------|--------|
| `DEBUG` | Detailed diagnostics | All messages + debug info |
| `INFO` | General information | Standard progress messages (default) |
| `WARN` | Warnings | Important warnings |
| `ERROR` | Errors | Error messages |

**See also**: [Logging Standards](docs/LOGGING_STANDARDS.md) for detailed logging information

---

## Troubleshooting

### MLX Not Found

```bash
# Install MLX
./install-mlx.sh

# Re-run bootstrap
./bootstrap.sh
```

### Out of Memory

Edit job's `.env` file:

```bash
BATCH_SIZE=1                     # Reduce batch size
WHISPER_MODEL=medium             # Use smaller model
```

### CPU Fallback on MPS

If you see "Falling back to CPU":

1. Install MLX: `./install-mlx.sh`
2. Re-run bootstrap: `./bootstrap.sh`
3. Create new job (old jobs have old config)

### Logging Issues

If logs are not created or verbose output is missing:

1. Check `LOG_LEVEL` environment variable: `echo $LOG_LEVEL`
2. Verify write permissions in `logs/` directory
3. Enable debug mode: `LOG_LEVEL=DEBUG`
4. See [Logging Troubleshooting Guide](docs/LOGGING_TROUBLESHOOTING.md)

---

## Contributing

We welcome contributions! Please see:
- Architecture in `docs/ARCHITECTURE.md`
- Configuration in `docs/CONFIGURATION.md`
- Implementation in `docs/IMPLEMENTATION_COMPLETE.md`

---

## License

See [LICENSE](LICENSE) file for details.

---

## Credits

- **WhisperX**: Fast speech recognition with word-level timestamps
- **MLX**: Apple's ML framework for Apple Silicon
- **IndicTrans2**: State-of-the-art Indian language translation by AI4Bharat
- **PyAnnote**: Speaker diarization

---

## Support

For issues, questions, or feature requests:
- Check documentation in `docs/`
- Review `docs/BUGFIX_SUMMARY.md` for common issues
- See `docs/MLX_ACCELERATION_GUIDE.md` for MLX troubleshooting

---

**Last Updated**: November 18, 2025  
**Version**: 1.0.0  
**Status**: Production Ready 🚀
