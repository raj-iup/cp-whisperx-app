# Model Management Guide

This guide explains how to manage ML models in CP-WhisperX-App.

## Overview

The pipeline uses several ML models:
- **Whisper Models**: Speech recognition (base, medium, large-v2, large-v3)
- **Silero VAD**: Voice activity detection
- **PyAnnote Models**: Speaker diarization and segmentation
- **spaCy Models**: Named entity recognition
- **MLX-Whisper**: Apple Silicon GPU acceleration (optional)

## Model Download During Bootstrap

All required models are automatically downloaded during bootstrap:

```bash
./scripts/bootstrap.sh
```

The bootstrap process:
1. Detects your hardware capabilities
2. Downloads optimal Whisper model for your system
3. Downloads all supporting models (VAD, NER, etc.)
4. Reports download status and cache size
5. Uses parallel downloads for 30-40% faster installation

### Model Cache Location

Models are cached in `.cache/`:
- `.cache/torch/hub/` - Whisper and Silero models
- `.cache/huggingface/hub/` - PyAnnote models
- System Python packages - spaCy models

## Checking Model Status

Check what models are installed and their sizes:

```bash
# Linux/macOS
./check-models.sh

# Windows
.\check-models.ps1
```

**Example Output:**
```
======================================================================
  ML MODEL STATUS CHECK
======================================================================
  Cache directory: /path/to/.cache
  Check time: 2025-11-16 23:12:30
  ✓ HuggingFace token available
  Checking Whisper models: base, large-v3

======================================================================
  MODEL STATUS
======================================================================

  Whisper Models:
  ✓ base                                     Cached (1.5GB)
  ✓ large-v3                                 Cached (2.9GB)

  VAD Models:
  ✓ silero-vad                               Cached (256MB)

  NER Models:
  ✓ en_core_web_trf                          Installed (v3.7.0)
  ✓ en_core_web_sm                           Installed (v3.7.0)

  Diarization Models:
  ✓ pyannote/speaker-diarization-3.1         Cached (512MB)
  ✓ pyannote/segmentation-3.0                Cached (256MB)

  Apple Silicon Acceleration:
  ✓ mlx-whisper                              Installed (v0.4.0)

  Total cache size: 5.4GB

======================================================================
  SUMMARY
======================================================================
  Total models checked: 8
  ✓ Cached/Installed: 8
  ✗ Missing: 0
```

## Advanced Options

### Check Specific Models

```bash
./check-models.sh --whisper-models base medium large-v3
```

### Provide HuggingFace Token

```bash
./check-models.sh --hf-token your_token_here
```

Or add to `config/secrets.json`:
```json
{
  "HF_TOKEN": "your_huggingface_token"
}
```

### Check for Updates (Future Feature)

```bash
./check-models.sh --check-updates
```

## Manual Model Download

If you need to download models manually:

```bash
# Activate virtual environment
source .bollyenv/bin/activate  # Linux/macOS
.bollyenv\Scripts\Activate.ps1  # Windows

# Download specific Whisper models
python shared/model_downloader.py --whisper-models base large-v3

# With HuggingFace token (for PyAnnote)
python shared/model_downloader.py --hf-token YOUR_TOKEN

# Control parallel downloads
python shared/model_downloader.py --max-workers 5
```

## Model Selection by Hardware

Bootstrap automatically selects optimal models based on your hardware:

| Hardware | Whisper Model | Batch Size | Notes |
|----------|---------------|------------|-------|
| Apple Silicon (M1/M2/M3) | large-v3 | 24 | Uses MPS acceleration |
| NVIDIA GPU (8GB+) | large-v3 | 16 | CUDA acceleration |
| NVIDIA GPU (4GB) | large-v2 | 8 | Balanced performance |
| CPU (Modern) | medium | 4 | Best CPU tradeoff |
| CPU (Limited) | base | 2 | Fast but less accurate |

These settings are saved to `config/.env.pipeline` and can be overridden.

## Whisper Model Comparison

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| base | 1.5GB | Fast | Good | Testing, drafts |
| medium | 2.0GB | Medium | Better | CPU systems |
| large-v2 | 2.9GB | Slow | Excellent | General use |
| large-v3 | 2.9GB | Slow | Best | Production quality |

## PyAnnote Models (Require HuggingFace Token)

To download PyAnnote models for speaker diarization:

1. Create account at https://huggingface.co
2. Get token from https://huggingface.co/settings/tokens
3. Accept model licenses:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0
4. Add token to `config/secrets.json`:
   ```json
   {
     "HF_TOKEN": "hf_..."
   }
   ```
5. Re-run bootstrap or model downloader

## Troubleshooting

### Models Not Downloading

**Issue:** Bootstrap reports model download failures

**Solutions:**
1. Check internet connection
2. Verify disk space (need ~10GB free)
3. For PyAnnote: Add HuggingFace token
4. Run model checker to see what's missing:
   ```bash
   ./check-models.sh
   ```

### Cache Taking Too Much Space

**Issue:** `.cache/` directory is very large

**Solutions:**
1. Check what's cached:
   ```bash
   ./check-models.sh
   ```
2. Remove unused models manually:
   ```bash
   rm -rf .cache/torch/hub/models--Systran--faster-whisper-medium
   ```
3. Keep only models you use:
   - Base model: for testing
   - Your hardware's recommended model: for production

### Model Version Issues

**Issue:** Pipeline fails with model compatibility errors

**Solutions:**
1. Re-run bootstrap to update models:
   ```bash
   ./scripts/bootstrap.sh
   ```
2. Check model status:
   ```bash
   ./check-models.sh
   ```
3. Manually clear cache and re-download:
   ```bash
   rm -rf .cache/
   ./scripts/bootstrap.sh
   ```

## On-Demand Model Downloads

If a model is missing, the pipeline will attempt to download it on first use. However, this:
- Delays pipeline execution
- May fail if no internet connection
- Doesn't show progress during pipeline run

**Best Practice:** Always run bootstrap first to pre-download all models.

## Model Update Strategy

Models are downloaded from latest available versions. To update:

1. Check current status:
   ```bash
   ./check-models.sh
   ```

2. Clear cache (optional):
   ```bash
   rm -rf .cache/
   ```

3. Re-run bootstrap:
   ```bash
   ./scripts/bootstrap.sh
   ```

## Performance Impact

Model choice affects pipeline performance:

**Example: 2-hour movie on Apple M1 Max**
- base model: ~45 minutes
- medium model: ~75 minutes
- large-v3 model: ~120 minutes

**Accuracy improvement:** large-v3 has ~15% better word error rate than base.

**Recommendation:** Use large-v3 for production, base for testing.

## Disk Space Requirements

Minimum disk space needed:

| Configuration | Space Required |
|---------------|----------------|
| Base setup | ~3GB |
| Recommended | ~6GB |
| Full (all models) | ~10GB |

Plus space for:
- Input video files
- Output subtitles/videos
- Processing temp files

## See Also

- [Bootstrap Guide](../README.md#bootstrap)
- [Hardware Detection](../README.md#hardware-detection)
- [Pipeline Configuration](../README.md#configuration)
