# Performance Guide

**Optimization and tuning tips**

## Hardware Optimization

### GPU Selection
- Apple M1 Pro/Max/Ultra: Excellent for MPS
- NVIDIA RTX 3090/4090: Best CUDA performance
- NVIDIA RTX 3060/3070: Good balance

### Memory Requirements
- Minimum: 8GB RAM
- Recommended: 16GB+ RAM
- GPU: 8GB+ VRAM for large-v3 model

## Model Selection

### Quality vs Speed
- `large-v3`: Best quality, slowest
- `medium`: Good balance
- `small`: Faster, lower quality
- `base`: Fastest, basic quality

## Batch Size Tuning

Adjust in job .env file:
```bash
WHISPER_BATCH_SIZE=16  # Default
# Increase for more VRAM, decrease if OOM
```

_Full performance guide to be expanded_

Return to [Documentation Index](INDEX.md)
