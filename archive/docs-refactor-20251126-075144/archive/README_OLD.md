# cp-whisperx-app

**AI-powered transcription and translation pipeline for Indian language content**

Transcribe audio/video in 22 Indian languages and translate to English (or other Indian languages) using WhisperX, MLX-Whisper, and IndicTrans2 with multi-environment architecture for optimal performance and compatibility.

---

## 🚀 Features

✅ **Multi-Environment Architecture**: 4 isolated Python environments prevent dependency conflicts  
✅ **Transcribe Workflow**: Audio → Text with word-level timestamps  
✅ **Translate Workflow**: Text → English subtitles with IndicTrans2  
✅ **22 Indian Languages**: Hindi, Tamil, Telugu, Bengali, and more  
✅ **GPU Acceleration**: Apple Silicon (MPS), NVIDIA (CUDA), or CPU  
✅ **MLX Integration**: 6-8x faster transcription on Apple Silicon  
✅ **IndicTrans2**: 90% faster translation for Indic languages  
✅ **Windows Native**: Full PowerShell support with identical functionality  

---

## 📋 Quick Reference

### Installation

**macOS / Linux**:
```bash
git clone <repository-url>
cd cp-whisperx-app
./bootstrap.sh
```

**Windows**:
```powershell
git clone <repository-url>
cd cp-whisperx-app
.\bootstrap.ps1
```

### Workflows

**Transcribe** (Audio → Text in same language):
```bash
# Unix/macOS
./prepare-job.sh "movie.mp4" --transcribe -s hi
./run-pipeline.sh -j <job-id>

# Windows
.\prepare-job.ps1 "movie.mp4" -Transcribe -SourceLanguage hi
.\run-pipeline.ps1 -JobId <job-id>
```

**Translate** (Text → English subtitles):
```bash
# Unix/macOS
./prepare-job.sh "movie.mp4" --translate -s hi -t en
./run-pipeline.sh -j <job-id>

# Windows
.\prepare-job.ps1 "movie.mp4" -Translate -SourceLanguage hi -TargetLanguage en
.\run-pipeline.ps1 -JobId <job-id>
```

**Subtitle** (Both source + target subtitles):
```bash
# Unix/macOS
./prepare-job.sh "movie.mp4" --subtitle -s hi -t en,gu
./run-pipeline.sh -j <job-id>

# Windows
.\prepare-job.ps1 "movie.mp4" -Subtitle -SourceLanguage hi -TargetLanguage en,gu
.\run-pipeline.ps1 -JobId <job-id>
```

### Troubleshooting

**Check environment status**:
```bash
# Unix/macOS
ls -la .venv-*
cat config/hardware_cache.json | jq .

# Windows
Get-ChildItem -Directory .venv-*
Get-Content config\hardware_cache.json | ConvertFrom-Json
```

**View logs**:
```bash
# Bootstrap logs
ls -la logs/

# Pipeline logs
ls -la out/YYYY/MM/DD/[UserID]/[counter]/logs/
```

**Rebuild environments**:
```bash
# Unix/macOS
rm -rf .venv-*
./bootstrap.sh

# Windows
Remove-Item .venv-* -Recurse -Force
.\bootstrap.ps1
```

### Important Notes

❌ **Don't use these** (deprecated):
- `install-mlx.sh`
- `install-indictrans2.sh`

✅ **Use this instead**:
- `./bootstrap.sh` or `.\bootstrap.ps1`

Bootstrap automatically creates all 4 environments and handles MLX and IndicTrans2.

---

## 🎯 Quick Start

### Prerequisites

- **Python 3.11+** (3.10 or 3.12 also supported)
- **FFmpeg** (for media processing)
- **10-20 GB** disk space (for ML models)
- **macOS/Linux** or **Windows 10/11**
- **Optional**: NVIDIA GPU (CUDA), or Apple Silicon (M1/M2/M3)

### Installation

#### macOS / Linux

```bash
# Clone repository
git clone <repository-url>
cd cp-whisperx-app

# Run bootstrap (creates all 4 virtual environments)
./bootstrap.sh

# This automatically:
# ✓ Creates venv/common, venv/whisperx, venv/mlx, venv/indictrans2
# ✓ Installs all dependencies in isolated environments
# ✓ Detects hardware (CPU/MPS/CUDA) and optimizes settings
# ✓ Downloads ML models (WhisperX, PyAnnote, IndicTrans2)
# ✓ Configures logging infrastructure
```

#### Windows

```powershell
# Clone repository
git clone <repository-url>
cd cp-whisperx-app

# Run bootstrap (creates all 4 virtual environments)
.\bootstrap.ps1

# This automatically:
# ✓ Creates venv/common, venv/whisperx, venv/mlx, venv/indictrans2
# ✓ Installs all dependencies in isolated environments
# ✓ Detects hardware (CPU/CUDA) and optimizes settings
# ✓ Downloads ML models
# ✓ Configures logging infrastructure
```

### First Run

#### macOS/Linux
```bash
# Prepare a transcription job (Hindi audio → Hindi text)
./prepare-job.sh "movie.mp4" --transcribe -s hi

# Run the pipeline with the generated job ID
./run-pipeline.sh -j <job-id>

# Example: Full subtitle workflow (Hindi audio → Hindi + English subtitles)
./prepare-job.sh "movie.mp4" --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>
```

#### Windows
```powershell
# Prepare a transcription job (Hindi audio → Hindi text)
.\prepare-job.ps1 "movie.mp4" -Transcribe -SourceLanguage hi

# Run the pipeline with the generated job ID
.\run-pipeline.ps1 -JobId <job-id>

# Example: Full subtitle workflow (Hindi audio → Hindi + English subtitles)
.\prepare-job.ps1 "movie.mp4" -Subtitle -SourceLanguage hi -TargetLanguage en
.\run-pipeline.ps1 -JobId <job-id>
```

**Note**: No need to run `install-mlx.sh` or `install-indictrans2.sh` separately - these are deprecated and automatically handled by `bootstrap.sh`/`bootstrap.ps1`.

---

## 🏗️ Multi-Environment Architecture

### Why Multiple Environments?

Different ML frameworks have conflicting dependency requirements:

- **WhisperX** requires `torch==2.0.x`, `numpy<2.0`
- **IndicTrans2** requires `torch>=2.5.0`, `numpy>=2.1.0`, `transformers>=4.51.0`
- **MLX-Whisper** requires Apple Silicon-specific packages

Single environment = dependency hell. Multi-environment = clean separation.

### The Four Environments

#### 1. `venv/mlx` (Apple Silicon Only)
**Purpose**: GPU-accelerated transcription using Metal Performance Shaders  
**Used for**: ASR (Automatic Speech Recognition) stage  
**Device**: MPS (Apple Silicon M1/M2/M3)  
**Speed**: 6-8x faster than CPU, 2-4x faster than WhisperX  
**Dependencies**: `mlx`, `mlx-whisper`, `numpy<2.0`

**When it runs**:
- Apple Silicon Mac detected
- ASR stage in transcribe workflow
- Automatically selected by pipeline

#### 2. `venv/whisperx`
**Purpose**: Standard transcription with word-level alignment  
**Used for**: demux, asr (fallback), alignment, export stages  
**Device**: CUDA (NVIDIA) or CPU  
**Dependencies**: `whisperx==3.1.1`, `torch==2.0.x`, `numpy<2.0`

**When it runs**:
- Non-Apple Silicon systems
- MLX not available
- Alignment stage (word-level timestamps)

#### 3. `venv/indictrans2`
**Purpose**: High-quality Indic language translation  
**Used for**: Translation stages for 22 Indian languages  
**Device**: MPS, CUDA, or CPU  
**Dependencies**: `transformers>=4.51.0`, `torch>=2.5.0`, `numpy>=2.1.0`, `IndicTransToolkit`

**When it runs**:
- Source language is Indic (hi, ta, te, bn, gu, kn, ml, mr, pa, ur, etc.)
- Translation or subtitle workflow
- 90% faster than Whisper for translation

#### 4. `venv/common`
**Purpose**: Lightweight utilities without heavy ML dependencies  
**Used for**: Subtitle generation, video muxing, file operations  
**Device**: CPU  
**Dependencies**: `ffmpeg-python`, `python-dotenv`, `pydantic`

**When it runs**:
- Subtitle generation stages
- Video muxing (combining video + subtitles)
- File management operations

### Environment Selection

The pipeline **automatically** selects the correct environment for each stage:

```
Transcribe Workflow (Hindi audio → Hindi text):
  demux           → venv/whisperx    (audio extraction)
  asr             → venv/mlx         (transcription, if Apple Silicon)
  asr (fallback)  → venv/whisperx    (transcription, other systems)
  alignment       → venv/whisperx    (word timestamps)
  export          → venv/whisperx    (save transcript)

Translate Workflow (Hindi text → English subtitle):
  load_transcript → venv/indictrans2 (load segments)
  translation     → venv/indictrans2 (translate to English)
  subtitle_gen    → venv/common      (create .srt file)
```

### Checking Environments

```bash
# Check status of all environments
./bootstrap.sh --check

# Expected output:
# ✓ mlx (Python 3.11.7)
#   Path: venv/mlx
#   MLX environment for Apple Silicon GPU-accelerated transcription
#
# ✓ whisperx (Python 3.11.7)
#   Path: venv/whisperx
#   WhisperX ASR environment with CUDA/CPU backend
#
# ✓ indictrans2 (Python 3.11.7)
#   Path: venv/indictrans2
#   IndicTrans2 translation environment
#
# ✓ common (Python 3.11.7)
#   Path: venv/common
#   Common utilities environment without ML dependencies
```

---

## 🔄 Workflows

### 1. Transcribe Workflow

**Purpose**: Convert audio to text in the **same source language**

```bash
# macOS/Linux
./prepare-job.sh "movie.mp4" --transcribe -s hi

# Windows
.\prepare-job.ps1 "movie.mp4" -Workflow transcribe -SourceLanguage hi
```

**Stages**:
1. **demux** (`venv/whisperx`): Extract audio from video
2. **asr** (`venv/mlx` or `venv/whisperx`): Transcribe audio to text
3. **alignment** (`venv/whisperx`): Generate word-level timestamps
4. **export_transcript** (`venv/whisperx`): Save segments.json

**Output**: `out/YYYY/MM/DD/[UserID]/[counter]/transcripts/segments.json`

**Example**: Hindi audio → Hindi text with timestamps

### 2. Translate Workflow

**Purpose**: Translate existing transcript to target language

```bash
# macOS/Linux
./prepare-job.sh "movie.mp4" --translate -s hi -t en

# Windows
.\prepare-job.ps1 "movie.mp4" -Workflow translate -SourceLanguage hi -TargetLanguage en
```

**Auto-Transcribe**: If transcript doesn't exist, automatically runs transcribe workflow first

**Stages**:
1. **load_transcript** (`venv/indictrans2`): Load segments.json
2. **indictrans2_translation** (`venv/indictrans2`): Translate to English
3. **subtitle_generation** (`venv/common`): Create .srt subtitle file

**Output**: `out/YYYY/MM/DD/[UserID]/[counter]/subtitles/english.srt`

**Example**: Hindi transcript → English text + English .srt

### 3. Subtitle Workflow

**Purpose**: Generate subtitles in **both** source and target languages

```bash
# macOS/Linux
./prepare-job.sh "movie.mp4" --subtitle -s hi -t en

# Windows
.\prepare-job.ps1 "movie.mp4" -Workflow subtitle -SourceLanguage hi -TargetLanguage en
```

**Complete Pipeline**: Auto-runs transcribe + translate + dual subtitles

**Stages**:
1. Auto-transcribe (if needed)
2. IndicTrans2 translation
3. **subtitle_generation_source** (`venv/common`): Hindi .srt
4. **subtitle_generation_target** (`venv/common`): English .srt
5. **mux** (`venv/common`): Combine video + dual subtitles

**Output**: 
- `out/.../subtitles/hindi.srt`
- `out/.../subtitles/english.srt`
- `out/.../video_with_subtitles.mkv`

---

## 🪟 Windows Support

Full native Windows support with PowerShell scripts that mirror Bash functionality.

### Bootstrap (Setup)

```powershell
# Create all 4 virtual environments
.\bootstrap.ps1

# Check specific environment
.\bootstrap.ps1 -Env whisperx

# Check all environments
.\bootstrap.ps1 -Check

# Clean all environments
.\bootstrap.ps1 -Clean
```

### Prepare Job

```powershell
# Transcribe workflow
.\prepare-job.ps1 "C:\Videos\movie.mp4" -Workflow transcribe -SourceLanguage hi

# Translate workflow
.\prepare-job.ps1 "C:\Videos\movie.mp4" -Workflow translate -SourceLanguage hi -TargetLanguage en

# Subtitle workflow
.\prepare-job.ps1 "C:\Videos\movie.mp4" -Workflow subtitle -SourceLanguage hi -TargetLanguage en

# With time range
.\prepare-job.ps1 "movie.mp4" -Workflow transcribe -SourceLanguage hi -StartTime "00:10:00" -EndTime "00:15:00"

# Debug mode
.\prepare-job.ps1 "movie.mp4" -Workflow transcribe -SourceLanguage hi -Debug
```

### Run Pipeline

```powershell
# Run pipeline for job
.\run-pipeline.ps1 -JobId <job-id>

# Check job status
.\run-pipeline.ps1 -JobId <job-id> -Status

# Resume failed job
.\run-pipeline.ps1 -JobId <job-id> -Resume
```

### Windows-Specific Notes

1. **Developer Mode** (Recommended):
   - Enables symlinks for HuggingFace cache
   - Settings → Privacy & security → For developers → Developer Mode ON
   - Saves 5-10 GB disk space

2. **CUDA Support**:
   - Automatically detected by bootstrap
   - Requires NVIDIA GPU + CUDA 11.8 or 12.1
   - Bootstrap configures optimal batch sizes

3. **Path Handling**:
   - Use backslashes or forward slashes: `C:\Videos\movie.mp4` or `C:/Videos/movie.mp4`
   - Spaces in paths supported: `"C:\My Videos\movie.mp4"`

---

## 📊 Logging

All scripts use **unified logging format** with automatic timestamped log files.

### Logging Format

```
[YYYY-MM-DD HH:MM:SS] [LEVEL] message
```

**Levels**: DEBUG, INFO, WARN, ERROR, SUCCESS

### Log Locations

```bash
logs/
├── YYYYMMDD-HHMMSS-bootstrap.log       # Bootstrap execution
├── YYYYMMDD-HHMMSS-prepare-job.log     # Job preparation
└── YYYYMMDD-HHMMSS-run-pipeline.log    # Pipeline execution

out/YYYY/MM/DD/[UserID]/[counter]/logs/
├── pipeline.log                         # Complete pipeline log
├── demux.log                            # Audio extraction
├── asr.log                              # Transcription
├── alignment.log                        # Word alignment
├── translation.log                      # IndicTrans2 translation
└── subtitle_gen.log                     # Subtitle generation
```

### Viewing Logs

```bash
# Latest bootstrap log
ls -lt logs/2025*-bootstrap.log | head -1 | xargs cat

# Job-specific logs
cat out/2025/11/19/rpatel/0001/logs/pipeline.log

# Filter for errors
grep "\[ERROR\]" out/*/*/rpatel/*/logs/pipeline.log

# Filter for environment usage
grep "Using environment" out/*/*/rpatel/*/logs/pipeline.log
```

### Log Levels

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
./prepare-job.sh movie.mp4 --transcribe -s hi --debug

# Custom log file location
export LOG_FILE=/custom/path/my.log
./bootstrap.sh
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. "Environment not found" Error

**Symptom**:
```
[ERROR] venv/mlx virtual environment not found
[INFO] Please run ./bootstrap.sh first
```

**Solution**:
```bash
# Run bootstrap to create all environments
./bootstrap.sh

# Or create specific environment
./bootstrap.sh --env mlx
```

#### 2. MLX Not Working on Apple Silicon

**Symptom**:
```
[WARN] MLX not available, falling back to WhisperX
```

**Diagnosis**:
```bash
# Check if MLX environment exists
./bootstrap.sh --check

# Verify MLX installation
source venv/mlx/bin/activate
python -c "import mlx.core as mx; print(mx.array([1,2,3]))"
deactivate
```

**Solution**:
```bash
# Re-create MLX environment
./bootstrap.sh --env mlx

# Or full re-bootstrap
./bootstrap.sh
```

#### 3. IndicTrans2 Authentication Error

**Symptom**:
```
[ERROR] 401 Unauthorized - gated model access required
```

**Solution**:
```bash
# 1. Request model access
open https://huggingface.co/ai4bharat/indictrans2-indic-en-1B
# Click "Agree and access repository"

# 2. Authenticate
source venv/indictrans2/bin/activate
huggingface-cli login
deactivate

# 3. Verify
./bootstrap.sh --env indictrans2
```

#### 4. Dependency Conflicts

**Symptom**:
```
ERROR: Cannot install torch 2.0.0 and torch 2.5.0
```

**Explanation**: You're likely activating the wrong environment manually.

**Solution**: Let the scripts handle environment activation automatically:

```bash
# ❌ DON'T manually activate environments
source venv/whisperx/bin/activate
./run-pipeline.sh -j <job-id>

# ✅ DO let scripts auto-select environments
./run-pipeline.sh -j <job-id>
```

#### 5. "jq not found" (macOS/Linux)

**Solution**:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq

# CentOS/RHEL
sudo yum install jq
```

#### 6. FFmpeg Not Found

**Solution**:
```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Windows
# Download from: https://ffmpeg.org/download.html
# Add to PATH
```

### Checking System Health

```bash
# 1. Check all environments
./bootstrap.sh --check

# 2. Check hardware detection
cat config/hardware_cache.json | jq .

# 3. Verify Python packages
source venv/mlx/bin/activate && pip list | grep mlx && deactivate
source venv/whisperx/bin/activate && pip list | grep whisperx && deactivate
source venv/indictrans2/bin/activate && pip list | grep transformers && deactivate

# 4. Check logs
tail -50 logs/*-bootstrap.log
```

### Getting Help

1. **Check logs** in `logs/` directory
2. **Review job logs** in `out/YYYY/MM/DD/[UserID]/[counter]/logs/`
3. **Enable debug mode**: Add `--debug` flag
4. **Verify hardware**: Check `config/hardware_cache.json`
5. **Re-run bootstrap**: `./bootstrap.sh` often fixes environment issues

---

## ⚙️ Advanced Configuration

### Hardware Detection

Bootstrap automatically detects hardware and creates `config/hardware_cache.json`:

```json
{
  "hardware": {
    "platform": "darwin",
    "has_cuda": false,
    "has_mps": true,
    "has_mlx": true
  },
  "environments": {
    "mlx": { ... },
    "whisperx": { ... },
    "indictrans2": { ... },
    "common": { ... }
  }
}
```

### Manual Configuration

Edit `config/.env.pipeline` to override defaults:

```bash
# Device selection (auto, mps, cuda, cpu)
DEVICE=auto

# Batch sizes
BATCH_SIZE_ASR=8
BATCH_SIZE_TRANSLATION=16

# Whisper model size
WHISPER_MODEL=large-v3

# IndicTrans2 settings
INDICTRANS2_ENABLED=true
INDICTRANS2_NUM_BEAMS=4

# Logging
LOG_LEVEL=INFO
```

### Environment Management

```bash
# Create specific environment
./bootstrap.sh --env mlx

# Rebuild all environments
./bootstrap.sh --clean
./bootstrap.sh

# Update single environment
rm -rf venv/whisperx
./bootstrap.sh --env whisperx
```

### Supported Languages

**Indic Languages** (IndicTrans2 optimized):
```
hi  - Hindi          ta  - Tamil         te  - Telugu
bn  - Bengali        gu  - Gujarati      kn  - Kannada
ml  - Malayalam      mr  - Marathi       pa  - Punjabi
ur  - Urdu           as  - Assamese      or  - Odia
ne  - Nepali         sd  - Sindhi        si  - Sinhala
sa  - Sanskrit       ks  - Kashmiri      doi - Dogri
mni - Manipuri       kok - Konkani       mai - Maithili
sat - Santali
```

**Other Languages** (WhisperX fallback):
All 100+ languages supported by Whisper

---

## 📚 Documentation

- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet
- **[LOGGING_ANALYSIS_REPORT.md](LOGGING_ANALYSIS_REPORT.md)** - Logging architecture
- **[multi_env_summary.md](multi_env_summary.md)** - Multi-environment design
- **[CHANGELOG.md](CHANGELOG.md)** - Version history

---

## 🙏 Acknowledgments

- **WhisperX**: Accurate speech recognition with word-level timestamps
- **MLX**: Apple Silicon GPU acceleration framework
- **IndicTrans2**: State-of-the-art Indic language translation by AI4Bharat
- **PyAnnote**: Speaker diarization and VAD

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file

---

## 🆘 Support

**Issues**: Check [Troubleshooting](#troubleshooting) section  
**Logs**: Always available in `logs/` and job output directories  
**Debug Mode**: Add `--debug` flag for verbose logging  

**Quick Commands**:
```bash
# Check system health
./bootstrap.sh --check

# View latest bootstrap log
ls -lt logs/*-bootstrap.log | head -1 | xargs tail -50

# Check job status
./run-pipeline.sh -j <job-id> --status
```

---

**Happy transcribing! 🎬✨**
