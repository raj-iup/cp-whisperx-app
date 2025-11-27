# Cache System Quick Reference

**CP-WhisperX-App Cache Optimization - User Guide**

---

## What Changed?

The cache system has been optimized to use a **centralized, project-local cache** instead of scattered locations. All ML models and application data now live in predictable locations.

---

## Cache Locations

### Before Optimization (Inconsistent)
```
~/.cache/torch/              ← User home (unpredictable)
~/.cache/huggingface/        ← User home (unpredictable)
shared/model-cache/          ← Legacy (abandoned)
out/tmdb_cache/              ← Application caches
```

### After Optimization (Centralized)
```
.cache/                      ← All ML models here
├── torch/                   ← Whisper, PyTorch models (3-5 GB)
├── huggingface/             ← Transformers, IndicTrans2 (2-10 GB)
└── mlx/                     ← MLX models (macOS only, 1-3 GB)

out/                         ← Application caches
├── tmdb_cache/              ← Movie metadata (< 100 MB)
└── musicbrainz_cache/       ← Music metadata (< 50 MB)

glossary/cache/              ← Translation glossaries (< 10 MB)
```

---

## Quick Commands

### Check Cache Status
```bash
# macOS/Linux
./scripts/cache-manager.sh status

# Windows
.\scripts\cache-manager.ps1 -Action status
```

**Output:**
```
ML Model Caches:
  📦 Torch/Whisper Models
     Size:     3.3G
  🤗 HuggingFace Models
     Size:     16G
  Total ML Cache: 19G

Application Caches:
  🎬 TMDB: 16K
  🎵 MusicBrainz: 16K
```

### Clear Model Caches
```bash
# macOS/Linux
./scripts/cache-manager.sh clear-models

# Windows
.\scripts\cache-manager.ps1 -Action clear-models
```

⚠️ **Warning**: Models will re-download on next pipeline run (may take 10-30 minutes depending on internet speed)

### Clear Application Caches
```bash
# macOS/Linux
./scripts/cache-manager.sh clear-app

# Windows
.\scripts\cache-manager.ps1 -Action clear-app
```

✅ **Safe**: Application caches auto-refresh as needed (90-day expiry)

### Clear All Caches
```bash
# macOS/Linux
./scripts/cache-manager.sh clear-all

# Windows
.\scripts\cache-manager.ps1 -Action clear-all
```

---

## For New Users

### Bootstrap Automatically Sets Up Cache
```bash
# macOS/Linux
./bootstrap.sh

# Windows
.\bootstrap.ps1
```

**What happens:**
1. ✅ Creates `.cache/torch/`, `.cache/huggingface/`, `.cache/mlx/`
2. ✅ Sets `TORCH_HOME`, `HF_HOME`, `MLX_CACHE_DIR` environment variables
3. ✅ Writes cache configuration to `config/hardware_cache.json`
4. ✅ Displays cache paths to user

**You're done!** No manual configuration needed.

---

## For Existing Users

### Option 1: Re-Bootstrap (Recommended)
```bash
# Backup existing cache (optional)
mv .cache .cache.backup

# Re-run bootstrap
./bootstrap.sh --force

# Verify cache location
./scripts/cache-manager.sh status

# After verification, delete backup
rm -rf .cache.backup
```

### Option 2: Migrate Existing Cache
```bash
# Move models from home cache to project cache
mv ~/.cache/torch .cache/ 2>/dev/null || true
mv ~/.cache/huggingface .cache/ 2>/dev/null || true

# Verify
./scripts/cache-manager.sh status
```

### Option 3: Clean Start
```bash
# Clear all caches
./scripts/cache-manager.sh clear-all

# Re-bootstrap
./bootstrap.sh

# Models will download on first pipeline run
```

---

## Disk Space Management

### Check Available Space
```bash
# macOS/Linux
df -h .

# Windows
Get-PSDrive C | Select-Object Used,Free
```

### Free Up Space

**Option 1: Clear old models** (will re-download on next use)
```bash
./scripts/cache-manager.sh clear-models
# Frees: 10-20 GB
```

**Option 2: Use smaller Whisper model**
```bash
# Edit job config before running pipeline
# Change "large-v3" (3GB) to "medium" (1.5GB) or "base" (150MB)
```

**Option 3: Move cache to external drive**
```bash
# macOS/Linux
mv .cache /Volumes/External/cp-whisperx-cache
ln -s /Volumes/External/cp-whisperx-cache .cache

# Windows
Move-Item .cache D:\cp-whisperx-cache
New-Item -ItemType SymbolicLink -Path .cache -Target D:\cp-whisperx-cache
```

---

## Environment Variables

These are set automatically by the system:

| Variable | Value | Purpose |
|----------|-------|---------|
| `TORCH_HOME` | `.cache/torch` | PyTorch model cache |
| `HF_HOME` | `.cache/huggingface` | HuggingFace cache |
| `TRANSFORMERS_CACHE` | `.cache/huggingface` | Transformers-specific |
| `MLX_CACHE_DIR` | `.cache/mlx` | MLX framework cache |

**You don't need to set these manually.** The `environment_manager.py` handles this automatically for all pipeline stages.

---

## Troubleshooting

### Models Downloading Multiple Times

**Symptom**: Same models download repeatedly

**Solution**:
```bash
# Re-run bootstrap to regenerate cache config
./bootstrap.sh --force

# Verify cache paths
cat config/hardware_cache.json | jq .cache
```

### "Permission Denied" Errors

**Solution**:
```bash
# Fix permissions
chmod -R u+w .cache/

# Or recreate cache directories
rm -rf .cache/
./bootstrap.sh --force
```

### Cache in Wrong Location

**Diagnosis**:
```bash
# Check where models actually are
du -sh ~/.cache/torch ~/.cache/huggingface .cache/torch .cache/huggingface 2>/dev/null
```

**Solution**:
```bash
# Move to correct location
mv ~/.cache/torch .cache/ 2>/dev/null || true
mv ~/.cache/huggingface .cache/ 2>/dev/null || true

# Or re-bootstrap
./bootstrap.sh --force
```

### Legacy Cache Warning

If you see:
```
⚠️  Legacy Model Cache (should be empty)
   Location: shared/model-cache/
   Size:     17M
```

**Solution**:
```bash
# Safe to delete - models now in .cache/
rm -rf shared/model-cache/
```

---

## FAQs

### Q: Is `.cache/` safe to delete?

**A:** Yes! It's in `.gitignore` and regenerates automatically. Models will re-download on next use.

### Q: Can I share cache between projects?

**A:** Phase 2 feature (future). Currently each project has its own cache for isolation.

### Q: How much disk space do I need?

**A:** 
- **Minimum**: 10 GB
- **Recommended**: 20 GB
- **With all models**: 30 GB

### Q: Do I need to clear cache regularly?

**A:** No. Models are persistent and reused. Only clear if:
- Running out of disk space
- Models corrupted
- Testing fresh downloads

### Q: What if I use NAS/network storage?

**A:** Phase 3 feature (future). For now, use symlinks:
```bash
mv .cache /mnt/nas/cp-whisperx-cache
ln -s /mnt/nas/cp-whisperx-cache .cache
```

---

## Best Practices

✅ **DO**:
- Let bootstrap manage cache setup automatically
- Use `cache-manager.sh status` to monitor disk usage
- Clear caches only when needed (low disk space)
- Keep `.cache/` in `.gitignore`

❌ **DON'T**:
- Don't commit `.cache/` to git
- Don't manually edit cache files
- Don't assume cache location without checking
- Don't delete cache before long offline periods

---

## Support

**Documentation**:
- `CACHE_ANALYSIS.md` - Technical analysis and design
- `CACHE_OPTIMIZATION_IMPLEMENTATION.md` - Implementation details
- `docs/BOOTSTRAP.md` - Bootstrap guide with cache section
- `docs/TROUBLESHOOTING.md` - Cache troubleshooting

**Commands**:
```bash
# Help for cache manager
./scripts/cache-manager.sh --help

# Help for bootstrap
./bootstrap.sh --help
```

---

**Last Updated**: November 20, 2025  
**Version**: 1.0.0 (Cache Optimization Phase 1)
