# Job-Based Pipeline Orchestration

## Overview

The CP-WhisperX-App pipeline now implements a robust job-based orchestration system that provides:

- **Unique Job IDs** for tracking and auditing
- **Hierarchical directory structure** for outputs and logs
- **Job-specific environment files** for reproducibility
- **Comprehensive manifests** for each stage
- **Resume capability** after failures

## Job ID Generation

### Format
Job IDs follow the format: `YYYYMMDD-NNN`

Example: `20251030-001`

- `YYYYMMDD`: Current date (year, month, day)
- `NNN`: Sequential number (001, 002, 003, etc.)

### Implementation
The job ID is automatically generated when the pipeline starts:
1. Checks existing jobs for the current date
2. Finds the highest sequence number
3. Generates next sequential ID
4. Stores in job-specific `.env` file

## Directory Structure

### Output Directory: `out/`
```
out/
└── [Year]/          # e.g., 2025
    └── [Month]/     # e.g., 10
        └── [Day]/   # e.g., 30
            └── [UserID]/  # e.g., 1
                └── [JobID]/    # e.g., 20251030-001
                    ├── job.env              # Copy of job environment file
                    ├── job_info.json        # Job metadata
                    ├── manifest.json        # Pipeline manifest
                    ├── audio/               # Stage 1: Demux output
                    ├── metadata/            # Stage 2: TMDB output
                    ├── entities/            # Stage 3: Pre-NER output
                    ├── prompts/             # NER-enhanced prompts
                    │   └── ner_enhanced_prompt.txt
                    ├── vad/                 # Stage 4-5: VAD outputs
                    ├── diarization/         # Stage 6: Diarization output
                    ├── transcription/       # Stage 7: ASR output
                    ├── subtitles/           # Stage 9: Subtitle output
                    └── final_output.mp4     # Stage 10: Final video
```

### Log Directory: `logs/`
```
logs/
└── [Year]/          # e.g., 2025
    └── [Month]/     # e.g., 10
        └── [Day]/   # e.g., 30
            └── [UserID]/  # e.g., 1
                └── [JobID]/    # e.g., 20251030-001
                    ├── orchestrator_20251030_154430.log
                    ├── demux.log
                    ├── tmdb.log
                    ├── pre_ner.log
                    ├── silero_vad.log
                    ├── pyannote_vad.log
                    ├── diarization.log
                    ├── asr.log
                    ├── post_ner.log
                    ├── subtitle_gen.log
                    └── mux.log
```

## Configuration Management

### Base Configuration File
Location: `config/.env`

This is the template configuration with default values.

### Job-Specific Configuration
Location: `config/.env.job_[JobID]`

Created automatically when a job starts:
1. Copies `config/.env` 
2. Updates with job-specific values:
   - `JOB_ID`: Unique job identifier
   - `USER_ID`: User identifier (default: 1)
   - `OUTPUT_ROOT`: Job-specific output path
   - `LOG_ROOT`: Job-specific log path

### Job Environment Backup
Location: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/job.env`

A copy of the job-specific environment file is stored in the output directory for:
- Reproducibility
- Auditing
- Reference

### Key Configuration Parameters

```bash
# Job Configuration
JOB_ID=                    # Auto-generated: YYYYMMDD-NNN
USER_ID=1                  # User identifier (default: 1)

# Logging
LOG_LEVEL=info            # Options: debug, info, warning, error, critical

# WhisperX Model
WHISPER_MODEL=large-v3    # Options: tiny, base, small, medium, large, large-v2, large-v3

# Languages
SRC_LANG=hi               # Source language (default: Hindi)
TGT_LANG=en               # Target language (default: English)
```

## Pipeline Execution

### Starting a Pipeline

```bash
# Basic usage (uses default config and user_id=1)
python pipeline.py input_video.mp4

# With custom config
python pipeline.py input_video.mp4 config/.env

# With custom user ID
python pipeline.py input_video.mp4 config/.env 2
```

### What Happens

1. **Job Creation**
   - Generates unique Job ID
   - Creates directory structure
   - Copies and updates environment file
   - Creates job_info.json

2. **Pipeline Execution**
   - Each stage uses job-specific environment
   - Updates manifest after each stage
   - Logs to job-specific directory

3. **Completion**
   - Finalizes manifest
   - Cleans up temporary job env file (backup retained in output)

## Manifest Structure

### Pipeline Manifest (`manifest.json`)

Located at: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/manifest.json`

```json
{
  "version": "1.0.0",
  "created_at": "2025-10-30T15:44:30.123456",
  "job_id": "20251030-001",
  "user_id": 1,
  "job_env_file": "config/.env.job_20251030-001",
  "input": {
    "file": "in/movie.mp4",
    "title": "Movie Name",
    "year": 2023
  },
  "output_dir": "out/2025/10/30/1/20251030-001",
  "stages": {
    "demux": {
      "job_id": "20251030-001",
      "user_id": 1,
      "stage_number": 1,
      "stage_name": "demux",
      "job_env_file": "config/.env.job_20251030-001",
      "status": "success",
      "started_at": "2025-10-30T15:44:35.123456",
      "completed_at": "2025-10-30T15:45:12.789012",
      "duration_seconds": 37.665556,
      "input_files": [
        {
          "key": "video",
          "path": "/absolute/path/to/in/movie.mp4",
          "exists": true,
          "size_bytes": 1234567890,
          "description": "Input video file"
        }
      ],
      "outputs": {
        "audio": {
          "path": "/absolute/path/to/out/2025/10/30/1/20251030-001/audio/audio.wav",
          "exists": true,
          "size_bytes": 123456789,
          "description": "Extracted 16kHz mono audio"
        }
      },
      "metadata": {
        "sample_rate": 16000,
        "channels": 1,
        "duration": 3600.5
      }
    }
  },
  "pipeline": {
    "status": "completed",
    "current_stage": null,
    "completed_stages": ["demux", "tmdb", "pre_ner", "silero_vad", "pyannote_vad", "diarization", "asr", "post_ner", "subtitle_gen", "mux"],
    "failed_stages": []
  },
  "timing": {
    "started_at": "2025-10-30T15:44:30.123456",
    "completed_at": "2025-10-30T17:30:45.678901",
    "total_seconds": 6375.555445
  }
}
```

### Stage Manifest Fields

Each stage in the manifest includes:

- **job_id**: Unique job identifier
- **user_id**: User identifier
- **stage_number**: Stage sequence (1-10)
- **stage_name**: Stage identifier
- **job_env_file**: Path to job-specific environment file
- **status**: Stage status (running, success, failed, skipped)
- **timing**: Start, end, and duration
- **input_files**: List of input files with metadata
- **outputs**: Dictionary of output files with metadata
- **metadata**: Stage-specific metadata

## Stage 7: ASR with NER-Enhanced Prompts

### Prompt Priority

The ASR stage (Stage 7) uses the following priority for initial prompts:

1. **NER-Enhanced Prompt** (PRIORITY 1)
   - Location: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/prompts/ner_enhanced_prompt.txt`
   - Generated by: Stage 3 (PRE_NER)
   - Contains: Entities extracted from TMDB metadata

2. **Combined Prompt** (PRIORITY 2)
   - Location: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/[MovieName].combined.initial_prompt.txt`
   - Fallback if NER-enhanced prompt not found

3. **Initial Prompt** (PRIORITY 3)
   - Location: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/[MovieName].initial_prompt.txt`
   - Basic prompt file

4. **Pre-NER Entities** (PRIORITY 4)
   - Location: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/pre_ner/entities.json`
   - Builds prompt from extracted entities

### Implementation

```python
def load_initial_prompt(movie_dir: Path, logger: PipelineLogger) -> str:
    # PRIORITY 1: NER-enhanced prompt from pre_ner stage
    ner_enhanced_prompt = movie_dir / "prompts" / "ner_enhanced_prompt.txt"
    if ner_enhanced_prompt.exists():
        with open(ner_enhanced_prompt) as f:
            prompt = f.read().strip()
        logger.info(f"Loaded NER-enhanced prompt: {len(prompt)} chars")
        return prompt
    
    # ... fallback to other sources
```

## Docker Compose Integration

### Job-Specific Environment

The orchestrator passes the job-specific environment file to Docker containers:

```bash
docker compose run --rm \
  -e CONFIG_PATH=/app/config/.env.job_20251030-001 \
  asr /app/out/2025/10/30/1/20251030-001
```

### Environment Variable

All Docker services support `CONFIG_PATH` environment variable:

```yaml
environment:
  - CONFIG_PATH=${CONFIG_PATH:-/app/config/.env}
```

## Resume Capability

The pipeline can resume from a previous run:

1. Checks if `manifest.json` exists
2. Reads completed stages
3. Skips already completed stages
4. Continues from next stage

```
📋 RESUMING FROM PREVIOUS RUN
   Completed: demux, tmdb, pre_ner, silero_vad
   Skipped: none
```

## Multi-User Support

Different users can run pipelines simultaneously:

```bash
# User 1
python pipeline.py movie1.mp4 config/.env 1

# User 2
python pipeline.py movie2.mp4 config/.env 2
```

Outputs are isolated by user ID:
- `out/2025/10/30/1/20251030-001/`
- `out/2025/10/30/2/20251030-002/`

## Job Information File

Location: `out/[Year]/[Month]/[Day]/[UserID]/[JobID]/job_info.json`

```json
{
  "job_id": "20251030-001",
  "user_id": 1,
  "created_at": "2025-10-30T15:44:30.123456",
  "output_dir": "out/2025/10/30/1/20251030-001",
  "log_dir": "logs/2025/10/30/1/20251030-001",
  "env_file": "config/.env.job_20251030-001",
  "env_backup": "out/2025/10/30/1/20251030-001/job.env"
}
```

## Best Practices

1. **Always specify user_id** when running multiple concurrent pipelines
2. **Keep job.env backup** for reproducing results
3. **Check manifest.json** to verify stage completion
4. **Use appropriate log level** (debug for troubleshooting, info for production)
5. **Archive completed jobs** to manage disk space
6. **Reference job_id** when reporting issues

## Troubleshooting

### Find a specific job's output
```bash
find out/ -name "20251030-001"
```

### Check job status
```bash
cat out/2025/10/30/1/20251030-001/manifest.json | grep -A 5 '"pipeline"'
```

### View job logs
```bash
ls logs/2025/10/30/1/20251030-001/
tail -f logs/2025/10/30/1/20251030-001/orchestrator_*.log
```

### Verify job configuration
```bash
cat out/2025/10/30/1/20251030-001/job.env
```

## API Reference

### JobManager Class

Located in: `shared/job_manager.py`

```python
from job_manager import JobManager

# Initialize
job_mgr = JobManager(
    config_dir=Path("config"),
    output_root=Path("out"),
    log_root=Path("logs")
)

# Create job
job_info = job_mgr.create_job(user_id=1)

# Get paths
output_dir = job_mgr.get_job_output_dir()
log_dir = job_mgr.get_job_log_dir()
env_file = job_mgr.get_job_env_path()

# Cleanup
job_mgr.cleanup_job_env()
```

### StageManifest Class

Located in: `shared/manifest.py`

```python
from manifest import StageManifest

# Use as context manager
with StageManifest("asr", movie_dir, logger, job_id, user_id, job_env_file) as manifest:
    # Add inputs
    manifest.add_input("audio", audio_file, "16kHz mono audio")
    
    # Add outputs
    manifest.add_output("transcript", transcript_file, "WhisperX transcript")
    
    # Add metadata
    manifest.add_metadata("model", "large-v3")
    manifest.add_metadata("language", "hi")
    
    # Automatic success on exit
```

## Migration from Old Structure

Old structure:
```
out/
└── Movie_Name_2023/
    └── ...
```

New structure:
```
out/
└── 2025/
    └── 10/
        └── 30/
            └── 1/
                └── 20251030-001/
                    └── ...
```

The new structure provides:
- Better organization by date
- Multi-user support
- Unique job tracking
- Easier archival and cleanup
