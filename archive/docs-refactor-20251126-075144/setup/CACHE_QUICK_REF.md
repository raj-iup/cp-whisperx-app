# Cache-Models Integration - Quick Reference

## Quick Commands

### Bootstrap with Model Caching

```bash
# Recommended for production
./bootstrap.sh --cache-models

# Interactive (prompts user)
./bootstrap.sh

# Skip caching (cache later)
./bootstrap.sh --skip-cache
```

### Manual Model Caching

```bash
# Cache all models (~20GB, 15-25 min)
./cache-models.sh --all

# Cache specific models
./cache-models.sh --indictrans2  # ~2-5GB
./cache-models.sh --nllb         # ~17GB
./cache-models.sh --whisperx     # ~3GB
./cache-models.sh --mlx          # ~3GB (Apple Silicon)
```

### Verify Cache

```bash
# Check cached models
ls .cache/huggingface/hub/ | grep "models--"

# Check cache size
du -sh .cache/huggingface/

# View cache configuration
cat config/hardware_cache.json | grep -A 10 '"cache"'
```

### Test Offline Execution

```bash
# Turn off network
# Run a job
./prepare-job.sh --media in/test.mp4 --workflow transcribe -s hi
./run-pipeline.sh -j <job-id>

# Should work if models are cached! ✅
```

## Cache Locations

| Component | Path | Size |
|-----------|------|------|
| HuggingFace Models | `.cache/huggingface/` | 20-25GB |
| PyTorch Models | `.cache/torch/` | 1-2GB |
| MLX Models | `.cache/mlx/` | 3GB (Apple Silicon) |
| **Total** | `.cache/` | **22-28GB** |

## Environment Variables

Set automatically by `shared/environment_manager.py` for all stages:

```bash
TORCH_HOME=.cache/torch
HF_HOME=.cache/huggingface
TRANSFORMERS_CACHE=.cache/huggingface
MLX_CACHE_DIR=.cache/mlx
```

## Verified Stages

All stages access cache via environment manager:

- ✅ **WhisperX ASR** - Uses `HF_HOME`
- ✅ **MLX Whisper** - Uses `MLX_CACHE_DIR`
- ✅ **IndicTrans2** - Uses `HF_HOME`
- ✅ **NLLB** - Uses `HF_HOME`
- ✅ **PyAnnote VAD** - Uses `TORCH_HOME`
- ✅ **Demucs** - Uses `TORCH_HOME`

## Documentation

| Document | Purpose |
|----------|---------|
| [MODEL_CACHING.md](MODEL_CACHING.md) | User guide for model caching |
| [CACHE_VERIFICATION.md](CACHE_VERIFICATION.md) | Technical verification of cache access |
| [INTEGRATION_SUMMARY.md](INTEGRATION_SUMMARY.md) | Integration summary and status |
| [bootstrap.md](../user-guide/bootstrap.md) | Bootstrap guide with cache info |

## Troubleshooting

### Models Not Cached

```bash
# Check if bootstrap was run
cat config/hardware_cache.json

# Re-run bootstrap
./bootstrap.sh --force --cache-models
```

### Cache Path Not Set

```bash
# Verify hardware_cache.json
cat config/hardware_cache.json | grep '"cache"'

# Should show cache paths
```

### Offline Execution Fails

```bash
# Enable network temporarily
# Cache models
./cache-models.sh --all

# Try offline again
```

## Status

**✅ Integration Complete**
- Bootstrap supports `--cache-models`
- All stages verified to access cache
- Documentation updated
- Ready for production use

**Date:** 2024-11-25
