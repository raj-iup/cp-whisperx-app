# AD-014 Quick Reference - Cache Integration

**Status:** ✅ Production Ready | **Version:** 1.0 | **Updated:** 2025-12-08

## 🎯 What It Does

**70-80% faster subtitle workflow** by caching baseline generation (demux, VAD, ASR, alignment).

## 🚀 Quick Start

### First Run (Generate & Cache)
```bash
./prepare-job.sh --media movie.mp4 --workflow subtitle -s hi -t en
./run-pipeline.sh -j job-XXXXX
# → Generates baseline, stores in cache (~8 min for 5min media)
```

### Second Run (Use Cache)
```bash
./prepare-job.sh --media movie.mp4 --workflow subtitle -s hi -t en
./run-pipeline.sh -j job-XXXXX
# → Restores from cache, skips stages 01-07 (~2 min for 5min media)
```

### Force Regeneration
```bash
./prepare-job.sh --media movie.mp4 --workflow subtitle -s hi -t en --no-cache
```

## 📊 Cache Management

```bash
# View stats
python3 tools/manage-cache.py stats

# List cached media
python3 tools/manage-cache.py list

# Check if file is cached
python3 tools/manage-cache.py verify movie.mp4

# Clear specific cache
python3 tools/manage-cache.py clear {media_id}

# Clear all cache
python3 tools/manage-cache.py clear --all
```

## ⚙️ Configuration

**Location:** `config/.env.pipeline`

```bash
ENABLE_CACHING=true                # Master switch
CACHE_ROOT=~/.cp-whisperx/cache   # Cache location
CACHE_TTL_DAYS=90                 # Expiration (days)
CACHE_MAX_SIZE_GB=50              # Max size
```

## 🏗️ Architecture

### Cached Stages (Phase 1 - 70-80% of time)
- Stage 01: Demux (extract audio)
- Stage 05: PyAnnote VAD
- Stage 06: WhisperX ASR
- Stage 07: Alignment

### Always-Run Stages (Phase 2+3)
- Stage 08: Lyrics Detection
- Stage 09: Hallucination Removal
- Stage 10: Translation
- Stage 11: Subtitle Generation
- Stage 12: Mux

## 📦 Components

**Core Modules:**
- `shared/media_identity.py` - Content-based media ID
- `shared/cache_manager.py` - Store/retrieve artifacts
- `shared/workflow_cache.py` - Workflow integration
- `shared/baseline_cache_orchestrator.py` - High-level coordination

**Tools:**
- `tools/manage-cache.py` - CLI management

**Pipeline:**
- `scripts/run-pipeline.py` - Integrated cache checks

## 🔑 Key Concepts

### Media Identity
- Content-based hash (SHA256 of audio samples)
- Stable across filename/format changes
- Computed from beginning, middle, end samples

### Cache Structure
```
~/.cp-whisperx/cache/
└── media/{media_id}/
    └── baseline/
        ├── audio.wav
        ├── segments.json
        ├── aligned.json
        ├── vad.json
        └── metadata.json
```

## ⏱️ Performance

| Media Length | First Run | Cached Run | Saved |
|-------------|-----------|------------|-------|
| 5 min       | 8 min     | 2 min      | 75%   |
| 15 min      | 20 min    | 5 min      | 75%   |
| 60 min      | 80 min    | 20 min     | 75%   |

## 🔧 Developer Usage

### Check for Cache
```python
from shared.baseline_cache_orchestrator import BaselineCacheOrchestrator

orchestrator = BaselineCacheOrchestrator(job_dir)
if orchestrator.try_restore_from_cache(media_file):
    logger.info("✅ Using cached baseline")
    # Skip stages 01-07
else:
    # Generate baseline
    run_baseline_stages()
    orchestrator.store_baseline_to_cache(media_file)
```

### Compute Media ID
```python
from shared.media_identity import compute_media_id

media_id = compute_media_id(Path("movie.mp4"))
# Returns: SHA256 hash (64 characters)
```

### Manual Cache Operations
```python
from shared.cache_manager import MediaCacheManager

cache_mgr = MediaCacheManager()

# Check cache
if cache_mgr.has_baseline(media_id):
    baseline = cache_mgr.get_baseline(media_id)
    
# Store baseline
cache_mgr.store_baseline(media_id, baseline_artifacts)

# Clear cache
cache_mgr.clear_baseline(media_id)
```

## 🐛 Troubleshooting

**Cache not used?**
1. Check `ENABLE_CACHING=true` in config
2. Verify: `python3 tools/manage-cache.py verify file.mp4`
3. Check logs for cache errors

**Cache too large?**
1. Reduce `CACHE_MAX_SIZE_GB` in config
2. Clear old entries: `python3 tools/manage-cache.py clear {media_id}`

**Restoration failing?**
1. Check integrity: `python3 tools/manage-cache.py info {media_id}`
2. Clear and regenerate: `--no-cache` flag

## 📚 Documentation

- **Complete Guide:** `docs/AD014_CACHE_INTEGRATION.md`
- **Implementation:** `AD014_IMPLEMENTATION_COMPLETE.md`
- **Architecture:** `ARCHITECTURE.md` § AD-014

## ✅ Checklist

**Before committing code that uses cache:**
- [ ] Import from `shared.baseline_cache_orchestrator`
- [ ] Check cache before generating baseline
- [ ] Store baseline after generation
- [ ] Handle cache failures gracefully
- [ ] Log cache hit/miss
- [ ] Test with `--no-cache` flag

**Configuration changes:**
- [ ] Update `.env.pipeline` if needed
- [ ] Document new parameters
- [ ] Test with cache enabled/disabled

---

**Quick Commands:**

```bash
# Stats
python3 tools/manage-cache.py stats

# Verify
python3 tools/manage-cache.py verify movie.mp4

# Clear
python3 tools/manage-cache.py clear {media_id}

# Force regen
./prepare-job.sh --media movie.mp4 --workflow subtitle -s hi -t en --no-cache
```

---

**Status:** ✅ Production Ready  
**Last Updated:** 2025-12-08
