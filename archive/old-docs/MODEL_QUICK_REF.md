# Model Management Quick Reference

## Quick Commands

### Check Model Status
```bash
# Check all models
./check-models.sh

# Check specific Whisper models
./check-models.sh --whisper-models base medium large-v3

# With HuggingFace token for PyAnnote models
./check-models.sh --hf-token YOUR_TOKEN
```

### Manual Model Download
```bash
# Download all recommended models
python shared/model_downloader.py

# Download specific Whisper models
python shared/model_downloader.py --whisper-models base large-v3

# With HuggingFace token (for PyAnnote)
python shared/model_downloader.py --hf-token YOUR_TOKEN

# Control parallel downloads (default: 3)
python shared/model_downloader.py --max-workers 5
```

### Bootstrap (Automatic Download)
```bash
# Downloads all models automatically
./scripts/bootstrap.sh
```

## Model Categories

| Category | Models | Authentication |
|----------|--------|----------------|
| **Whisper** | base, medium, large-v2, large-v3 | None |
| **VAD** | silero-vad | None |
| **NER** | en_core_web_trf, en_core_web_sm | None |
| **Diarization** | pyannote/speaker-diarization-3.1<br>pyannote/segmentation-3.0 | HF Token Required |
| **Apple Silicon** | mlx-whisper | None (Mac only) |

## Expected Sizes

| Model | Size | Purpose |
|-------|------|---------|
| Whisper base | ~1.5GB | Fast testing |
| Whisper medium | ~2.0GB | CPU systems |
| Whisper large-v2 | ~2.9GB | High accuracy |
| Whisper large-v3 | ~2.9GB | Best accuracy |
| Silero VAD | ~256MB | Voice detection |
| spaCy trf | ~500MB | NER (best) |
| spaCy sm | ~15MB | NER (fallback) |
| PyAnnote diarization | ~512MB | Speaker ID |
| PyAnnote segmentation | ~256MB | Audio segmentation |

**Total:** ~5-10GB depending on Whisper models chosen

## Cache Locations

```
.cache/
├── torch/hub/              # Whisper & Silero models
│   ├── models--Systran--faster-whisper-base/
│   ├── models--Systran--faster-whisper-large-v3/
│   └── snakers4_silero-vad_master/
└── huggingface/hub/        # PyAnnote models
    ├── models--pyannote--speaker-diarization-3.1/
    └── models--pyannote--segmentation-3.0/
```

spaCy models installed in Python environment (not in .cache)

## Troubleshooting

### Models Not Downloading
```bash
# Check what's missing
./check-models.sh

# Manually download
python shared/model_downloader.py
```

### PyAnnote Models Failing
```bash
# Need HuggingFace token
# 1. Get token from: https://huggingface.co/settings/tokens
# 2. Accept licenses:
#    - https://huggingface.co/pyannote/speaker-diarization-3.1
#    - https://huggingface.co/pyannote/segmentation-3.0
# 3. Add to config/secrets.json:
{
  "HF_TOKEN": "hf_..."
}
# 4. Re-run bootstrap or downloader
```

### Clear Cache
```bash
# Remove all cached models
rm -rf .cache/

# Re-download
./scripts/bootstrap.sh
```

## Integration with Pipeline

Models are automatically used by pipeline stages:
- **ASR stage**: Uses Whisper model (from hardware cache)
- **Silero VAD stage**: Uses silero-vad
- **PyAnnote VAD stage**: Uses pyannote/segmentation-3.0
- **Diarization stage**: Uses pyannote/speaker-diarization-3.1
- **Pre/Post NER stages**: Use spaCy models

No additional configuration needed - models are auto-detected from cache.

## See Also

- [MODEL_MANAGEMENT.md](MODEL_MANAGEMENT.md) - Complete guide
- [IMPLEMENTATION_MODEL_MANAGEMENT.md](IMPLEMENTATION_MODEL_MANAGEMENT.md) - Technical details
- [Bootstrap Guide](../README.md#bootstrap) - Initial setup
