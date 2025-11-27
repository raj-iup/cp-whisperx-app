# Multi-Environment Architecture

## Overview

This project uses **multiple isolated Python virtual environments** to resolve dependency conflicts between WhisperX and IndicTrans2. Each environment has its own set of dependencies that don't conflict with others.

## The Dependency Conflict Problem

### Before Multi-Environment Solution

**WhisperX Requirements:**
- `numpy >= 2.0.2, < 2.1`
- `torch ~= 2.0.0`
- `torchaudio ~= 2.0.0`

**IndicTrans2 Requirements:**
- `numpy >= 2.1.0`
- `torch >= 2.5.0`
- `transformers >= 4.51.0`

These requirements are **mutually exclusive** - you cannot satisfy both in a single environment. Previously, pip would install the newer versions and warn that WhisperX is incompatible.

### Solution: Isolated Environments

We create **three separate virtual environments**, each with compatible dependencies:

1. **whisperx** - For transcription stages
2. **indictrans2** - For translation stages
3. **common** - For utility stages (no ML dependencies)

## Architecture

### Environment Structure

```
cp-whisperx-app/
├── venv/whisperx/          # WhisperX environment
│   ├── bin/python           # Python 3.11 with torch 2.0
│   └── lib/                 # numpy < 2.1, whisperx 3.1.1
├── venv/indictrans2/       # IndicTrans2 environment
│   ├── bin/python           # Python 3.11 with torch 2.5+
│   └── lib/                 # numpy >= 2.1, transformers 4.51+
├── venv/common/            # Common utilities environment
│   ├── bin/python           # Python 3.11 (no ML libs)
│   └── lib/                 # ffmpeg-python, pydantic
└── config/
    └── hardware_cache.json  # Environment configuration
```

### Stage-to-Environment Mapping

Each pipeline stage runs in a specific environment:

| Stage | Environment | Why |
|-------|------------|-----|
| `demux` | whisperx | Needs WhisperX audio processing |
| `asr` | whisperx | Needs WhisperX ASR models |
| `alignment` | whisperx | Needs WhisperX alignment |
| `export_transcript` | whisperx | Needs WhisperX data structures |
| `load_transcript` | indictrans2 | Prepares for translation |
| `indictrans2_translation_*` | indictrans2 | Needs IndicTrans2 models |
| `subtitle_generation_*` | common | Simple text processing |
| `mux` | common | FFmpeg video processing |

### Workflow-to-Environment Mapping

Different workflows use different combinations:

- **transcribe**: `[whisperx]`
- **translate**: `[indictrans2, common]`
- **subtitle**: `[whisperx, indictrans2, common]`

## Setup

### Initial Setup

```bash
# Install all environments
./bootstrap.sh

# Or install individually
./bootstrap.sh --env whisperx
./bootstrap.sh --env indictrans2
./bootstrap.sh --env common
```

### Check Status

```bash
# Check all environments
./bootstrap.sh --check

# Check specific environment
python shared/environment_manager.py check --env whisperx
```

### Clean and Rebuild

```bash
# Remove all environments
./bootstrap.sh --clean

# Rebuild
./bootstrap.sh
```

## How It Works

### 1. Hardware Cache Configuration

The `config/hardware_cache.json` file defines:

```json
{
  "environments": {
    "whisperx": {
      "name": "whisperx",
      "path": "venv/whisperx",
      "stages": ["demux", "asr", "alignment", "export_transcript"],
      "requirements_file": "requirements-whisperx.txt"
    },
    ...
  },
  "stage_to_environment_mapping": {
    "demux": "whisperx",
    "asr": "whisperx",
    ...
  }
}
```

### 2. Job Configuration

When you run `prepare-job.sh`, it reads the hardware cache and includes environment information in the job config:

```json
{
  "job_id": "job-20251119-rpatel-0001",
  "workflow": "subtitle",
  "environments": {
    "whisperx": "venv/whisperx",
    "indictrans2": "venv/indictrans2",
    "common": "venv/common"
  },
  "stage_environments": {
    "demux": "whisperx",
    "asr": "whisperx",
    "indictrans2_translation_en": "indictrans2",
    ...
  }
}
```

### 3. Pipeline Execution

The pipeline orchestrator (`run-pipeline.py`):

1. Loads the job configuration
2. For each stage:
   - Determines required environment from `stage_environments`
   - Activates that environment
   - Runs the stage
   - Deactivates the environment
3. Switches environments seamlessly between stages

### Example: Subtitle Workflow

```
Stage 1: demux
  → Activate venv/whisperx
  → Run audio extraction
  → Deactivate

Stage 2: asr
  → Activate venv/whisperx
  → Run transcription
  → Deactivate

Stage 3: indictrans2_translation_en
  → Activate venv/indictrans2
  → Run translation
  → Deactivate

Stage 4: subtitle_generation_en
  → Activate venv/common
  → Generate SRT file
  → Deactivate

Stage 5: mux
  → Activate venv/common
  → Embed subtitles in video
  → Deactivate
```

## Environment Details

### WhisperX Environment

**Purpose:** Speech-to-text transcription with word-level timestamps

**Key Dependencies:**
- WhisperX 3.1.1
- PyTorch 2.0.x (compatible with MLX)
- NumPy < 2.0
- MLX-Whisper (Apple Silicon acceleration)

**Stages:** `demux`, `asr`, `alignment`, `export_transcript`

**Requirements File:** `requirements-whisperx.txt`

### IndicTrans2 Environment

**Purpose:** Indian language translation with state-of-the-art models

**Key Dependencies:**
- IndicTransToolkit latest
- PyTorch 2.5+
- Transformers 4.51+
- NumPy 2.1+

**Stages:** `load_transcript`, `indictrans2_translation_*`

**Requirements File:** `requirements-indictrans2.txt`

### Common Environment

**Purpose:** Lightweight utilities without ML dependencies

**Key Dependencies:**
- FFmpeg-python (video processing)
- Pydantic (configuration)
- Python-dotenv (environment variables)

**Stages:** `subtitle_generation_*`, `mux`

**Requirements File:** `requirements-common.txt`

## Usage Examples

### Running a Job

```bash
# Prepare job (validates environments)
./prepare-job.sh movie.mp4 --subtitle -s hi -t en,gu

# Run pipeline (switches environments automatically)
./run-pipeline.sh -j job-20251119-rpatel-0001
```

The pipeline automatically:
1. Checks which environments are needed
2. Validates they're installed
3. Switches between them per stage
4. Logs environment switches

### Environment Management in Code

```python
from shared.environment_manager import EnvironmentManager

# Create manager
manager = EnvironmentManager()

# Get environment for a stage
env_name = manager.get_environment_for_stage("asr")
# Returns: "whisperx"

# Get Python executable
python_exe = manager.get_python_executable("whisperx")
# Returns: Path("venv/whisperx/bin/python")

# Run command in environment
manager.run_in_environment(
    "indictrans2",
    ["python", "-m", "scripts.translate", "input.json"],
    capture_output=True
)

# Validate workflow environments
valid, missing = manager.validate_environments_for_workflow("subtitle")
if not valid:
    print(f"Missing: {missing}")
```

## Troubleshooting

### Environment Not Found

```bash
# Check which environments are installed
./bootstrap.sh --check

# Install missing environment
./bootstrap.sh --env <env-name>
```

### Dependency Conflicts Within Environment

```bash
# Rebuild specific environment
./bootstrap.sh --clean
./bootstrap.sh --env <env-name>
```

### Pipeline Stage Fails

Check the logs - they show which environment was used:

```
[INFO] Running stage 'asr' in environment 'whisperx'
[INFO] Python: venv/whisperx/bin/python
```

## Benefits

1. **No Dependency Conflicts**: Each environment has compatible versions
2. **Isolation**: Problems in one environment don't affect others
3. **Flexibility**: Easy to update one environment independently
4. **Clarity**: Clear mapping of stages to environments
5. **Maintainability**: Easy to add new environments for new features

## Migration from Single Environment

If you have the old `.bollyenv`:

```bash
# 1. Remove old environment
rm -rf .bollyenv

# 2. Setup new environments
./bootstrap.sh

# 3. Run jobs as before - pipeline handles environments automatically
./prepare-job.sh movie.mp4 --subtitle -s hi -t en
./run-pipeline.sh -j <job-id>
```

No changes needed to your workflow - the pipeline automatically uses the right environment for each stage!

## Adding New Environments

To add a new environment:

1. Add to `config/hardware_cache.json`:
```json
{
  "environments": {
    "my_new_env": {
      "name": "my_new_env",
      "path": ".venv-my_new_env",
      "stages": ["my_stage"],
      "requirements_file": "requirements-my_new_env.txt"
    }
  }
}
```

2. Create `requirements-my_new_env.txt`

3. Add stage mapping:
```json
{
  "stage_to_environment_mapping": {
    "my_stage": "my_new_env"
  }
}
```

4. Install:
```bash
./bootstrap.sh --env my_new_env
```

## Files

- `bootstrap.sh` - Environment setup script
- `config/hardware_cache.json` - Environment configuration
- `shared/environment_manager.py` - Python environment manager
- `requirements-whisperx.txt` - WhisperX dependencies
- `requirements-indictrans2.txt` - IndicTrans2 dependencies
- `requirements-common.txt` - Common utilities dependencies
