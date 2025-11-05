# Docker Optimization Quick Reference

## Build Order

```bash
# Correct build order (enforced in scripts):
1. base:cpu          # CPU-only base
2. base:cuda         # CUDA base with Python 3.11
3. base-ml:cuda      # ML base with PyTorch ← KEY OPTIMIZATION
4. All other stages  # Inherit from appropriate base
```

## Image Inheritance

### CPU-Only Stages
```dockerfile
FROM rajiup/cp-whisperx-app-base:cpu
# Use for: demux, tmdb, pre-ner, post-ner, subtitle-gen, mux
```

### GPU Stages
```dockerfile
FROM rajiup/cp-whisperx-app-base-ml:cuda
# Use for: asr, diarization, silero-vad, pyannote-vad, second-pass, lyrics
# Already includes: PyTorch 2.1.0, numpy, scipy, librosa, transformers
```

## Common Dependencies

Install these from `requirements-common.txt`:
- numpy==1.24.3
- scipy==1.11.4
- soundfile==0.12.1
- python-dotenv==1.2.1
- tqdm==4.66.0
- rich==14.2.0
- pysubs2==1.8.0

## Version Management

All versions defined in: `docker/versions.txt`

### PyTorch
- Version: 2.1.0+cu121
- Installed: Once in base-ml:cuda
- Compatible with: All GPU stages

### Key Libraries
- whisperx==3.7.2
- pyannote.audio==3.4.0
- transformers==4.57.1
- spacy==3.8.7

## Build Commands

### Build All Images
```bash
# Linux/Mac
./scripts/build-all-images.sh

# Windows
.\scripts\build-all-images.bat
```

### Build Single Stage
```bash
docker build -t rajiup/cp-whisperx-app-STAGE:TAG -f docker/STAGE/Dockerfile .
```

### Check Images
```bash
docker images | grep cp-whisperx-app
```

### Check Sizes
```bash
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep cp-whisperx-app
```

## Layer Ordering Pattern

```dockerfile
FROM base

# 1. System packages (rarely changes)
RUN apt-get update && ...

# 2. Python packages (occasionally changes)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 3. Shared code (occasionally changes)
COPY shared/ /app/shared/

# 4. Stage script (changes most frequently)
COPY docker/stage/script.py /app/
```

## Optimization Results

| Metric | Before | After | Savings |
|--------|--------|-------|---------|
| Build Time | 60 min | 35 min | 42% |
| Total Size | 30 GB | 15 GB | 50% |
| Incremental | 5 min | 30 sec | 90% |
| PyTorch Installs | 6 copies | 1 copy | 83% |

## Troubleshooting

### Build fails with "base-ml not found"
```bash
# Build base-ml first:
docker build -t rajiup/cp-whisperx-app-base-ml:cuda -f docker/base-ml/Dockerfile .
```

### GPU stage fails with PyTorch version conflict
- Check `docker/versions.txt` for correct version
- Rebuild base-ml:cuda with correct PyTorch version
- Rebuild affected GPU stage

### Large image size
- Ensure stage inherits from base-ml (not base:cuda)
- Check for duplicate PyTorch installations
- Use `docker history IMAGE` to inspect layers

### Slow builds
- Check layer ordering (system → python → code)
- Ensure requirements-common.txt is used
- Enable BuildKit: `export DOCKER_BUILDKIT=1`

## File Locations

```
docker/
├── requirements-common.txt    # Shared dependencies
├── versions.txt               # Version management
├── base/                      # CPU base
├── base-cuda/                 # CUDA base
├── base-ml/                   # ML base (NEW!)
├── demux/                     # CPU stages
├── ...
├── asr/                       # GPU stages
└── ...

docs/
├── DOCKER_OPTIMIZATION_RECOMMENDATIONS.md
└── DOCKER_OPTIMIZATION_IMPLEMENTATION.md
```

## Version Update Process

1. Update `docker/versions.txt` FIRST
2. Update `requirements-common.txt` if needed
3. Rebuild base-ml:cuda
4. Rebuild affected stages
5. Test compatibility
6. Commit with changelog

## Adding New Stages

### CPU-Only Stage
```dockerfile
FROM rajiup/cp-whisperx-app-base:cpu
# Install stage-specific packages
# Copy scripts
```

### GPU Stage
```dockerfile
FROM rajiup/cp-whisperx-app-base-ml:cuda
# PyTorch already available!
# Only install stage-specific packages
# Copy scripts
```

## Performance Tips

1. **Use base-ml for GPU stages** - Saves 2.5 GB per stage
2. **Pin all versions** - Prevents surprises
3. **Order layers correctly** - Maximizes cache hits
4. **Use requirements-common.txt** - Shares dependencies
5. **Enable BuildKit** - Faster pip installs

## Maintenance Schedule

- **Monthly:** Check for outdated packages
- **Quarterly:** Review unused dependencies
- **Annually:** Re-evaluate base image choices

## References

- Analysis: `docs/DOCKER_OPTIMIZATION_RECOMMENDATIONS.md`
- Implementation: `docs/DOCKER_OPTIMIZATION_IMPLEMENTATION.md`
- Versions: `docker/versions.txt`
- Build Scripts: `scripts/build-all-images.*`
