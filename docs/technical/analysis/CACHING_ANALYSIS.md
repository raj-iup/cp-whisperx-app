# Bollywood Subtitle Pipeline - Data Caching & API Optimization Analysis

**Analysis Date:** 2025-11-14  
**Project:** CP-WhisperX-App

---

## Executive Summary

The Bollywood subtitle generation pipeline makes API calls to **TMDB** and **MusicBrainz**. Currently, there is **partial caching** for TMDB data but significant opportunities exist to expand caching and minimize API calls.

### Current State
- ✅ **TMDB caching**: Implemented (30-day expiry)
- ✅ **Local soundtrack database**: Available for fallback
- ⚠️ **MusicBrainz**: No caching (rate-limited to 1 req/sec)
- ⚠️ **ML models**: Cached but could be optimized
- ❌ **API response caching**: Not persistent across runs

---

## API Call Analysis

### 1. TMDB API (Stage 2)
**Current Implementation:**
- **Script:** `scripts/tmdb_enrichment.py`
- **Cache Location:** `out/tmdb_cache/tmdb_<ID>.json`
- **Cache Duration:** 30 days
- **Status:** ✅ **PARTIALLY IMPLEMENTED**

**API Calls Made:**
```python
# Per movie (3 API calls total):
1. Search movie by title/year     → GET /3/search/movie
2. Get movie credits               → GET /3/movie/{id}/credits
3. Get movie details + external IDs → GET /3/movie/{id}?append_to_response=external_ids,keywords
```

**Data Cached:**
- Movie title, year, TMDB ID, IMDb ID
- Cast names (configurable limit, default 20)
- Crew names (configurable limit, default 10)
- Genres
- Soundtrack data (if available)

**Cache Hit Scenario:**
```
Job 1: Movie A → 3 API calls → Cache created
Job 2: Same Movie A → 0 API calls → Cache hit ✓
Job 3: Same Movie A (31 days later) → 3 API calls → Cache expired
```

**Optimization Opportunities:**
1. ✅ Cache already implemented
2. 📊 Consider longer expiry (movie metadata rarely changes)
3. 🔄 Add cache warming for common Bollywood films
4. 📈 Cache statistics tracking needed

---

### 2. MusicBrainz API (Stage 2)
**Current Implementation:**
- **Script:** `scripts/musicbrainz_client.py`
- **Cache:** ❌ **NOT IMPLEMENTED**
- **Rate Limit:** 1 request/second (enforced)
- **Fallback:** Local database (`config/bollywood_soundtracks.json`)

**API Calls Made:**
```python
# Per movie (1-2 API calls):
1. Search release by movie title/year → rate limited
   └─ Returns: Album ID, tracks, artists, composers, durations
```

**Data Retrieved:**
- Soundtrack album title
- Track titles, artists, composers
- Track durations (in milliseconds)

**Current Flow:**
```
1. Try MusicBrainz API (1 sec rate limit)
2. If found → Cache to local DB (bollywood_soundtracks.json)
3. If not found → Fallback to local DB
4. If still not found → Return empty
```

**🚨 CRITICAL ISSUE:**
- **No persistent API cache** - Same movie queried multiple times
- Rate limit (1 req/sec) slows repeated pipeline runs
- Local DB caching only happens if MusicBrainz succeeds

**Optimization Opportunities:**
1. ❌ **Implement MusicBrainz response cache** (similar to TMDB)
   - Cache location: `out/musicbrainz_cache/mb_<release_id>.json`
   - Expiry: 90 days (music metadata even more static)
2. 📊 **Cache search results by movie title+year**
   - Key: `{title}_{year}` → MusicBrainz release ID
   - Avoids re-searching for same movie
3. 🔄 **Pre-populate local DB** with top Bollywood soundtracks
4. 📈 **Track cache hit rate** for optimization

---

### 3. ML Model Downloads
**Current Implementation:**
- **Cache Location:** `.cache/huggingface/`, `.cache/torch/`
- **Status:** ✅ Models cached after first download

**Models Used:**
```
Silero VAD:        silero_vad (PyTorch)
PyAnnote VAD:      pyannote/segmentation (HuggingFace)
Diarization:       pyannote/speaker-diarization (HuggingFace)
Whisper ASR:       Systran/faster-whisper-large-v3 (HuggingFace)
Alignment:         WAV2VEC2 models (HuggingFace)
```

**Caching Behavior:**
```
First Run:  Download models → Save to .cache/
Next Runs:  Load from .cache/ → No downloads ✓
```

**Optimization Opportunities:**
1. ✅ Already optimized
2. 📦 Consider model quantization for faster loading
3. 💾 Document cache size requirements (~10-20 GB)

---

## Cacheable Data Summary

### High Priority (API Calls)

| Data Type | API | Current Cache | Recommendation | Impact |
|-----------|-----|---------------|----------------|--------|
| **TMDB Movie Metadata** | TMDB | ✅ 30 days | Extend to 90 days | Low API usage |
| **TMDB Cast/Crew** | TMDB | ✅ Included | ✓ Good | Saves 1 API call |
| **TMDB External IDs** | TMDB | ✅ Included | ✓ Good | Saves 1 API call |
| **MusicBrainz Releases** | MusicBrainz | ❌ None | **Implement 90-day cache** | **High - Rate limited** |
| **MusicBrainz Search Results** | MusicBrainz | ❌ None | **Cache title→ID mapping** | **High - Saves searches** |

### Medium Priority (Generated Data)

| Data Type | Source | Current | Recommendation | Benefit |
|-----------|--------|---------|----------------|---------|
| **Bias Terms** | TMDB+NER | ❌ Regenerated | Cache per movie | Faster stage 6-9 |
| **Bias Windows** | Generated | ❌ Regenerated | Cache with config hash | Skip computation |
| **NER Entities** | Extraction | ❌ Regenerated | Cache from Stage 3 | Reuse in Stage 9 |
| **Glossary (Film)** | ML Selection | ❌ Regenerated | Cache per movie+config | Skip ML inference |
| **Lyrics Detection** | Audio Analysis | ❌ Regenerated | Cache per audio file | Skip audio processing |

### Low Priority (Already Optimized)

| Data Type | Current State | Notes |
|-----------|---------------|-------|
| **ML Models** | ✅ Cached in `.cache/` | HuggingFace/PyTorch handle this |
| **VAD Segments** | ✅ Saved to stage dirs | Used for resume capability |
| **Transcription** | ✅ Saved to stage dirs | Core pipeline output |

---

## Recommended Caching Architecture

### 1. Global Cache Structure
```
out/
├── tmdb_cache/              # ✅ Exists
│   └── tmdb_<ID>.json       # Movie metadata
├── musicbrainz_cache/       # ❌ NEW - Implement this
│   ├── releases/
│   │   └── mb_<release_id>.json
│   └── search_cache.json    # title+year → release_id mapping
├── bias_cache/              # ❌ NEW - Optional optimization
│   └── <movie_id>_bias_terms.json
└── glossary_cache/          # ❌ NEW - Optional optimization
    └── <movie_id>_<config_hash>.json
```

### 2. Cache Management Module
**Create:** `shared/cache_manager.py`

```python
class CacheManager:
    """Unified cache manager for API responses and generated data"""
    
    def __init__(self, cache_dir: Path):
        self.tmdb_cache = TMDBCache(cache_dir / "tmdb_cache")
        self.mb_cache = MusicBrainzCache(cache_dir / "musicbrainz_cache")
        self.bias_cache = BiasCache(cache_dir / "bias_cache")
    
    def get_or_fetch(self, cache_type, key, fetch_fn, expiry_days=30):
        """Generic cache-or-fetch pattern"""
        cache = self._get_cache(cache_type)
        data = cache.get(key)
        if data:
            return data
        data = fetch_fn()
        cache.set(key, data, expiry_days)
        return data
```

### 3. Implementation Priority

#### Phase 1: Critical (Immediate)
1. **MusicBrainz API cache** - Eliminates rate limit issues
   - Files: `shared/musicbrainz_cache.py` (new)
   - Update: `scripts/musicbrainz_client.py`
   - Impact: Saves 1-2 API calls per movie (1-2 seconds delay)

#### Phase 2: High Value (Next)
2. **MusicBrainz search cache** - Avoid redundant searches
   - Store: `{title}_{year}` → `release_id` mapping
   - Impact: Eliminates search API call if cached

3. **Extend TMDB cache expiry** - Reduce cache misses
   - Change: 30 days → 90 days
   - Reason: Movie metadata rarely changes

#### Phase 3: Optimization (Future)
4. **Bias terms cache** - Speed up stages 6-9
   - Cache bias terms per movie
   - Invalidate on TMDB data change

5. **Glossary cache** - Skip ML inference
   - Cache with config hash (settings affect output)
   - Significant time savings for repeated runs

---

## Cache Invalidation Strategy

### When to Invalidate

| Cache Type | Invalidate When | Method |
|------------|-----------------|--------|
| TMDB | 30-90 days old | Time-based expiry |
| MusicBrainz | 90 days old | Time-based expiry |
| Bias Terms | TMDB data updated | Checksum/version check |
| Glossary | Config changed | Config hash comparison |
| Lyrics Detection | Audio file changed | File hash/mtime |

### Cache Clearing Commands
```bash
# Clear all caches
./scripts/clear_cache.sh --all

# Clear specific cache
./scripts/clear_cache.sh --tmdb
./scripts/clear_cache.sh --musicbrainz
./scripts/clear_cache.sh --bias

# Clear expired entries only
./scripts/clear_cache.sh --expired
```

---

## Performance Impact Estimation

### Current State (No MusicBrainz Cache)
```
Run 1: Movie A
- TMDB: 3 API calls (~2s)
- MusicBrainz: 1-2 API calls (~1-2s with rate limit)
- Total API time: ~3-4s

Run 2: Movie A (same day)
- TMDB: 0 API calls (cached) ✓
- MusicBrainz: 1-2 API calls (~1-2s) ← WASTED
- Total API time: ~1-2s
```

### With Full Caching
```
Run 1: Movie A
- TMDB: 3 API calls (~2s)
- MusicBrainz: 1-2 API calls (~1-2s)
- Total API time: ~3-4s
- Cache: Created

Run 2: Movie A (same day)
- TMDB: 0 API calls (cached) ✓
- MusicBrainz: 0 API calls (cached) ✓
- Total API time: ~0s ✓
```

### Estimated Savings
- **Per movie (2nd+ run)**: 1-2 seconds
- **For 100 movies**: ~100-200 seconds saved
- **Rate limit avoidance**: No 1-sec delays
- **User experience**: Instant metadata loading

---

## Implementation Checklist

### Immediate (Phase 1)
- [ ] Create `shared/musicbrainz_cache.py` module
- [ ] Implement `MusicBrainzCache` class (similar to `TMDBCache`)
- [ ] Update `scripts/musicbrainz_client.py` to use cache
- [ ] Add cache configuration to `config/.env.pipeline`
- [ ] Test cache hit/miss scenarios

### Near-term (Phase 2)
- [ ] Implement MusicBrainz search result caching
- [ ] Extend TMDB cache expiry to 90 days
- [ ] Add cache statistics to pipeline logs
- [ ] Create cache management utility script

### Future (Phase 3)
- [ ] Implement bias terms caching
- [ ] Implement glossary caching with config hash
- [ ] Add cache warming for popular movies
- [ ] Create cache analytics dashboard

---

## Configuration Examples

### Enable/Disable Caching
```bash
# config/.env.pipeline

# TMDB Cache (already implemented)
TMDB_CACHE_ENABLED=true
TMDB_CACHE_EXPIRY_DAYS=90

# MusicBrainz Cache (to be implemented)
MUSICBRAINZ_CACHE_ENABLED=true
MUSICBRAINZ_CACHE_EXPIRY_DAYS=90

# Bias Terms Cache (optional)
BIAS_CACHE_ENABLED=false

# Glossary Cache (optional)
GLOSSARY_CACHE_ENABLED=false
```

### Cache Directory Configuration
```bash
# Global cache location
CACHE_DIR=./out/cache

# Per-cache locations (optional override)
TMDB_CACHE_DIR=./out/tmdb_cache
MUSICBRAINZ_CACHE_DIR=./out/musicbrainz_cache
```

---

## Monitoring & Metrics

### Cache Performance Metrics
```python
# Log at end of pipeline run
cache_stats = {
    'tmdb': {
        'hits': 1,
        'misses': 0,
        'hit_rate': 100.0,
        'time_saved_seconds': 2.0
    },
    'musicbrainz': {
        'hits': 1,
        'misses': 0,
        'hit_rate': 100.0,
        'time_saved_seconds': 1.5
    },
    'total_api_time': 0.0,
    'cache_time': 0.1
}
```

### Dashboard View (Future)
```
Cache Performance (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TMDB:         98% hit rate (245/250 jobs)
MusicBrainz:  95% hit rate (238/250 jobs)
Time Saved:   ~425 seconds total
API Cost:     $0.00 (free tier)
```

---

## Conclusion

### Summary
The pipeline has **good TMDB caching** but lacks **MusicBrainz caching**, which is critical due to rate limiting. Implementing MusicBrainz caching is the **highest priority** optimization.

### Quick Wins
1. ✅ Add MusicBrainz response cache (90-day expiry)
2. ✅ Add MusicBrainz search cache (title→ID mapping)  
3. ✅ Extend TMDB cache to 90 days

### Expected Impact
- **Eliminate rate limit delays** on repeated runs
- **Instant metadata loading** for cached movies
- **Better user experience** with faster pipeline starts
- **Reduced API load** on external services

### Next Steps
1. Implement `MusicBrainzCache` class
2. Update `musicbrainz_client.py` to use cache
3. Add configuration options
4. Test with real Bollywood movies
5. Monitor cache hit rates

