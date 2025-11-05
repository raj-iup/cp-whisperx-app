# Windows Batch Script Equivalents

This document lists all Windows batch file equivalents created for the shell scripts in the repository.

## Summary of Created Windows Scripts

### Main Scripts Directory

| Shell Script | Windows Batch | Purpose |
|-------------|---------------|---------|
| `scripts/build-all-images.sh` | `scripts/build-all-images.bat` | Build all Docker images with registry tags |
| `scripts/push-all-images.sh` | `scripts/push-all-images.bat` | Push all Docker images to registry |
| `scripts/pull-all-images.sh` | `scripts/pull-all-images.bat` | Pull all Docker images from registry |
| `scripts/build-images.sh` | `scripts/build-images.bat` | Build Docker images (simpler version) |
| `scripts/docker-run.sh` | `scripts/docker-run.bat` | Build and start Docker services |
| `scripts/pipeline-status.sh` | `scripts/pipeline-status.bat` | Show pipeline status and quick reference |
| `scripts/bootstrap.sh` | `scripts/bootstrap.bat` | Bootstrap Python environment |
| `monitor_push.sh` | `monitor-push.bat` | Monitor Docker push progress |

### Native Scripts Directory

| Shell Script | Windows Batch | Purpose |
|-------------|---------------|---------|
| `native/setup_venvs.sh` | `native/setup_venvs.bat` | Create virtual environments for each stage |
| `native/pipeline.sh` | `native/pipeline.bat` | Run native pipeline orchestrator |
| `native/pipeline_debug_asr.sh` | `native/pipeline_debug_asr.bat` | Run pipeline with ASR stage in DEBUG mode |
| `native/run_asr_debug.sh` | `native/run_asr_debug.bat` | Run ASR stage in debug mode |

### Test Scripts

| Shell Script | Windows Batch | Purpose |
|-------------|---------------|---------|
| `scripts/tests/test_macos_mps_subtitle.sh` | `scripts/tests/test_windows_subtitle.bat` | Test subtitle generation (platform-specific) |

## Usage Examples

### Building Docker Images

```batch
REM Build all images with registry tags
scripts\build-all-images.bat

REM Or use the simpler version
scripts\build-images.bat
```

### Pulling from Registry

```batch
REM Make sure you're logged in first (if pulling private images)
docker login

REM Pull all images
scripts\pull-all-images.bat

REM Or use the root wrapper
pull-all-images.bat
```

### Pushing to Registry

```batch
REM Make sure you're logged in first
docker login

REM Push all images
scripts\push-all-images.bat

REM Monitor push progress in another window
monitor-push.bat
```

### Native Pipeline

```batch
REM Setup virtual environments first (one-time)
native\setup_venvs.bat

REM Run the pipeline
native\pipeline.bat in\movie.mp4

REM Run with ASR debug mode
native\pipeline_debug_asr.bat in\movie.mp4

REM Or run just ASR stage in debug
native\run_asr_debug.bat Movie_Name --model base --language en
```

### Pipeline Status

```batch
REM View pipeline status and commands
scripts\pipeline-status.bat
```

### Bootstrap Environment

```batch
REM Setup Python environment
scripts\bootstrap.bat
```

### Running Tests

```batch
REM Run subtitle generation test
scripts\tests\test_windows_subtitle.bat
```

## Key Differences from Shell Scripts

1. **Delayed Expansion**: Windows batch files use `enabledelayedexpansion` for variable expansion in loops
2. **Path Separators**: Uses backslashes (`\`) instead of forward slashes (`/`)
3. **Error Handling**: Uses `errorlevel` checks instead of `$?`
4. **Arrays**: Windows batch uses indexed pseudo-arrays with syntax like `set arr[0]=value`
5. **Colors**: Windows doesn't support ANSI color codes by default, so color output is replaced with text indicators
6. **Command Output**: Uses `findstr` instead of `grep`, `find /c /v ""` instead of `wc -l`

## Environment Variables

Both shell and batch scripts respect the same environment variables:

- `DOCKERHUB_USER`: Docker Hub username/registry (default: `rajiup`)
- `DOCKER_TAG`: Docker image tag (default: `latest`)
- `LOG_LEVEL`: Logging level (e.g., `DEBUG`)
- `PYTHONPATH`: Python module search path
- `PYTORCH_ENABLE_MPS_FALLBACK`: PyTorch MPS fallback setting

## Notes

1. All batch scripts include proper error handling and exit codes
2. Scripts maintain feature parity with shell equivalents
3. Output formatting is simplified for Windows console
4. Registry tagging follows the same format: `${REGISTRY}/cp-whisperx-app-${stage}:${tag}`

## Docker Image Building

The build script creates the following images:

### Base Images
- `rajiup/cp-whisperx-app-base:cpu` - Python 3.11 + CPU libraries
- `rajiup/cp-whisperx-app-base:cuda` - Python 3.11 + CUDA 12.1 + PyTorch

### Stage Images (CPU variants)
- `rajiup/cp-whisperx-app-demux:cpu`
- `rajiup/cp-whisperx-app-tmdb:cpu`
- `rajiup/cp-whisperx-app-pre-ner:cpu`
- `rajiup/cp-whisperx-app-silero-vad:cpu`
- `rajiup/cp-whisperx-app-pyannote-vad:cpu`
- `rajiup/cp-whisperx-app-diarization:cpu`
- `rajiup/cp-whisperx-app-asr:cpu`
- `rajiup/cp-whisperx-app-post-ner:cpu`
- `rajiup/cp-whisperx-app-subtitle-gen:cpu`
- `rajiup/cp-whisperx-app-mux:cpu`
- `rajiup/cp-whisperx-app-second-pass-translation:cpu` (if Dockerfile exists)
- `rajiup/cp-whisperx-app-lyrics-detection:cpu` (if Dockerfile exists)

All images are tagged with the registry prefix for easy pushing to Docker Hub.
