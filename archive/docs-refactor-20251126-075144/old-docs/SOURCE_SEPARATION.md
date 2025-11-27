# Source Separation Setup

## Overview

Source separation extracts vocals from audio by removing background music, resulting in cleaner speech for transcription. This improves transcription accuracy significantly for content with background music.

## Dedicated Environment

Source separation runs in its own isolated virtual environment (`venv/demucs`) to avoid PyTorch version conflicts with other pipeline components.

### Why a Separate Environment?

- **Demucs** requires specific PyTorch versions
- Isolated from WhisperX, IndicTrans2, and other ML dependencies
- Prevents package conflicts
- Allows independent updates

## Installation

```bash
# Install the Demucs environment
./install-demucs.sh
```

This will:
1. Create `venv/demucs` virtual environment
2. Install PyTorch with MPS support (for Apple Silicon)
3. Install Demucs 4.0+ with all dependencies
4. Verify MPS availability

## Configuration

### Enable Source Separation

When preparing a job:

```bash
# Enable with default (balanced) quality
./prepare-job.sh --source-separation

# Or specify quality level
./prepare-job.sh --source-separation --source-separation-quality quality
```

### Quality Presets

- **`fast`**: MDX model with MP3 output - fastest, lower quality
- **`balanced`** (default): HT-Demucs model - good balance of speed and quality
- **`quality`**: HT-Demucs model - best quality, slower

### In job.json

```json
{
  "source_separation": {
    "enabled": true,
    "quality": "balanced"
  }
}
```

## Hardware Acceleration

### Apple Silicon (MPS)

Demucs automatically uses MPS when available:
- Much faster than CPU (7-8x speedup)
- Best quality with HT-Demucs model
- Typical processing time: ~2 minutes for 10-minute audio

### CPU Fallback

If MPS is not available, demucs uses CPU:
- Slower but still functional
- Estimated time: ~10-15 minutes for 10-minute audio

## Models

### HT-Demucs (Hybrid Transformer)
- **Best quality** - Latest hybrid transformer model
- Default for `balanced` and `quality` presets
- Excellent vocal separation
- ~2-3 minutes per 10min audio on MPS

### MDX Extra Q
- **Faster processing** - Used in `fast` preset
- Good quality for most use cases  
- Requires `diffq` package (auto-installed)
- ~1-2 minutes per 10min audio on MPS

## Usage in Pipeline

Source separation runs automatically when enabled:

```bash
# Full pipeline with source separation
./run-pipeline.sh --workflow subtitle --source-lang hi --target-lang en \
  --input "movie.mp4" --source-separation
```

The pipeline will:
1. Extract audio (demux stage)
2. **Separate vocals** (source_separation stage) 
3. Continue with VAD, ASR, etc. using vocals-only audio

## Output

Source separation creates:
- `vocals.wav` - Extracted vocals (used for transcription)
- `accompaniment.wav` - Background music (saved for reference)
- `audio.wav` - Copy of vocals for downstream stages

Output location: `out/{date}/{user}/{job}/99_source_separation/`

## Troubleshooting

### "Demucs not found"
```bash
# Reinstall demucs environment
./install-demucs.sh
```

### "MPS not available"
Check PyTorch installation:
```bash
source venv/demucs/bin/activate
python3 -c "import torch; print(f'MPS: {torch.backends.mps.is_available()}')"
```

### Slow processing
- Ensure MPS is being used (check logs)
- Try `fast` quality preset
- Consider shorter audio clips for testing

### Out of memory
- Use `fast` quality preset
- Process shorter clips
- Falls back to CPU automatically

## Technical Details

### Environment Mapping

Defined in `config/hardware_cache.json`:
```json
{
  "environments": {
    "demucs": {
      "path": "venv/demucs",
      "purpose": "Demucs audio source separation",
      "stages": ["source_separation"],
      "enabled": true
    }
  },
  "stage_to_environment_mapping": {
    "source_separation": "demucs"
  }
}
```

### Stage Script

Location: `scripts/source_separation.py`

Key features:
- Auto-detects hardware (MPS/CUDA/CPU)
- Quality-based model selection
- Proper error handling and logging
- StageIO integration

## Best Practices

1. **Always enable for music-heavy content** (movies, songs, performances)
2. **Use `balanced` quality** for most use cases
3. **Test with short clips first** to verify setup
4. **Monitor MPS usage** in Activity Monitor
5. **Keep environment isolated** - don't mix with other venvs

## Performance Expectations

| Audio Length | Quality | Hardware | Time |
|--------------|---------|----------|------|
| 10 minutes   | fast    | MPS      | ~1-2 min |
| 10 minutes   | balanced| MPS      | ~2-3 min |
| 10 minutes   | quality | MPS      | ~3-4 min |
| 10 minutes   | balanced| CPU      | ~10-15 min |

*Times are approximate and vary by system*

## See Also

- [Developer Guide](DEVELOPER_GUIDE.md) - Virtual environment management
- [User Guide](user-guide/README.md) - Pipeline usage
- [Demucs GitHub](https://github.com/facebookresearch/demucs) - Official documentation
