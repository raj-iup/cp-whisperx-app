# Caching - Quick Reference

## Quick Commands

```bash
# View cache statistics
./tools/cache-manager.sh --stats

# Clear expired entries (90+ days old)
./tools/cache-manager.sh --clear-expired

# Clear all caches
./tools/cache-manager.sh --clear-all

# Clear specific cache
./tools/cache-manager.sh --clear-tmdb
./tools/cache-manager.sh --clear-musicbrainz
```

## Configuration

Edit `config/.env.pipeline`:

```bash
# Enable/disable caching
TMDB_CACHE_ENABLED=true
MUSICBRAINZ_CACHE_ENABLED=true

# Adjust expiry (days)
TMDB_CACHE_EXPIRY_DAYS=90
MUSICBRAINZ_CACHE_EXPIRY_DAYS=90
```

## Cache Locations

- **TMDB:** `out/tmdb_cache/tmdb_<ID>.json`
- **MusicBrainz:** `out/musicbrainz_cache/releases/mb_<ID>.json`
- **Search Cache:** `out/musicbrainz_cache/search_cache.json`

## Performance

**Before:** 1-2s delay on repeated movie runs (MusicBrainz rate limit)  
**After:** <0.1s (instant cache hit) ✅

## Troubleshooting

**Cache not working?**
- Check `TMDB_CACHE_ENABLED=true` in config
- Check `MUSICBRAINZ_CACHE_ENABLED=true` in config
- Verify cache directories exist: `ls -la out/*/cache`

**Clear specific movie cache:**
```bash
# Find TMDB ID from logs
./tools/cache-manager.sh --clear-tmdb --id 14467
```

**Storage issues:**
```bash
# Check cache size
du -sh out/tmdb_cache out/musicbrainz_cache

# Remove old entries
./tools/cache-manager.sh --clear-expired
```

---

📖 **Full docs:** `CACHING_IMPLEMENTATION_COMPLETE.md`
