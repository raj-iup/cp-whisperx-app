# Soundtrack Enrichment - Implementation Strategy

## Executive Summary

**Recommended Architecture**: **Cascade Fallback System** with 3 tiers

```
Primary Method: MusicBrainz API
    ↓ (if fails)
Fallback 1: Local Database (Manual/Scraped)
    ↓ (if not found)
Fallback 2: Spotify API (Optional)
```

---

## Strategic Analysis

### Decision Matrix

| Method | Ease | Cost | Coverage | Reliability | Maintenance | Score |
|--------|------|------|----------|-------------|-------------|-------|
| **MusicBrainz** | ⭐⭐⭐⭐⭐ | Free | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low | **19/25** |
| **Local DB** | ⭐⭐⭐⭐⭐ | Free | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Medium | **18/25** |
| **Spotify** | ⭐⭐⭐⭐ | Free* | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Low | **18/25** |
| **Web Scraping** | ⭐⭐ | Free | ⭐⭐⭐⭐ | ⭐⭐ | High | **12/25** |
| **Lyrics Alignment** | ⭐ | Free | ⭐⭐ | ⭐⭐⭐ | High | **9/25** |

*Spotify: Free for personal use, requires app registration

---

## Recommended Implementation: Cascade Fallback System

### Architecture Overview

```python
def get_soundtrack_for_movie(
    title: str,
    year: int,
    imdb_id: str,
    config: Config
) -> SoundtrackData:
    """
    Get soundtrack using cascade fallback strategy
    
    Priority Order:
    1. MusicBrainz API (primary)
    2. Local Database (fallback 1)
    3. Spotify API (fallback 2, optional)
    """
    
    # Try MusicBrainz first
    if config.use_musicbrainz:
        result = try_musicbrainz(imdb_id)
        if result.success:
            cache_to_local_db(result)  # Cache for future
            return result
    
    # Fallback to Local Database
    result = try_local_database(title, year, imdb_id)
    if result.success:
        return result
    
    # Optional: Fallback to Spotify
    if config.use_spotify:
        result = try_spotify(title, year)
        if result.success:
            cache_to_local_db(result)  # Cache for future
            return result
    
    # No soundtrack found
    return SoundtrackData.empty()
```

### Why This Approach?

1. **Best of All Worlds**
   - Automatic when possible (MusicBrainz)
   - Reliable fallback (Local DB)
   - Comprehensive coverage (Spotify as last resort)

2. **Resilience**
   - Network failure? Use local DB
   - Rate limits? Fall back to cache
   - API down? Still works

3. **Progressive Enhancement**
   - Start with MusicBrainz only
   - Add local DB entries as needed
   - Enable Spotify later if needed

4. **Cost-Effective**
   - Primary method is free
   - Spotify optional (free tier sufficient)
   - No ongoing costs

---

## Implementation Plan

### Phase 1: Foundation (Week 1)

**Goal**: Implement MusicBrainz + Local DB fallback

#### 1.1 Install Dependencies
```bash
pip install musicbrainzngs
```

#### 1.2 Create MusicBrainz Client
```python
# File: scripts/musicbrainz_client.py

import musicbrainzngs
from typing import Optional, List, Dict
import time

musicbrainzngs.set_useragent("CP-WhisperX-App", "1.0", "contact@example.com")

class MusicBrainzClient:
    """Client for fetching soundtrack data from MusicBrainz"""
    
    def __init__(self):
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    def get_soundtrack(self, imdb_id: str) -> Optional[Dict]:
        """
        Get soundtrack for movie using IMDb ID
        
        Returns:
            Dict with tracks or None if not found
        """
        try:
            self._rate_limit()
            
            # Search for soundtrack album
            result = musicbrainzngs.browse_releases(
                imdb=imdb_id,
                release_type=['soundtrack'],
                inc=['recordings', 'artist-credits']
            )
            
            if not result.get('release-list'):
                return None
            
            # Get first soundtrack release
            release = result['release-list'][0]
            release_id = release['id']
            
            # Get detailed track information
            self._rate_limit()
            details = musicbrainzngs.get_release_by_id(
                release_id,
                includes=['recordings', 'artist-credits']
            )
            
            # Parse tracks
            tracks = []
            for medium in details['release'].get('medium-list', []):
                for track in medium.get('track-list', []):
                    recording = track.get('recording', {})
                    
                    # Get artists
                    artists = []
                    for credit in recording.get('artist-credit', []):
                        if isinstance(credit, dict):
                            artist_name = credit.get('artist', {}).get('name')
                            if artist_name:
                                artists.append(artist_name)
                    
                    tracks.append({
                        'title': recording.get('title', ''),
                        'artist': ', '.join(artists),
                        'composer': '',  # MusicBrainz has this but harder to extract
                        'duration_ms': recording.get('length', 0)
                    })
            
            return {
                'found': True,
                'source': 'musicbrainz',
                'tracks': tracks
            }
            
        except Exception as e:
            print(f"MusicBrainz error: {e}")
            return None
```

#### 1.3 Integrate into TMDB Enrichment
```python
# File: scripts/tmdb_enrichment.py (modifications)

from scripts.musicbrainz_client import MusicBrainzClient

def get_soundtrack_for_movie(
    title: str,
    year: Optional[int],
    imdb_id: Optional[str] = None,
    soundtrack_db: Optional[Dict] = None,
    use_musicbrainz: bool = True
) -> List[Dict[str, str]]:
    """
    Get soundtrack with fallback strategy
    
    Priority:
    1. MusicBrainz (if imdb_id available)
    2. Local database
    """
    
    # Try MusicBrainz first
    if use_musicbrainz and imdb_id:
        logger.info(f"Querying MusicBrainz (IMDb: {imdb_id})")
        
        client = MusicBrainzClient()
        mb_result = client.get_soundtrack(imdb_id)
        
        if mb_result and mb_result['found']:
            tracks = mb_result['tracks']
            logger.info(f"✓ MusicBrainz: Found {len(tracks)} tracks")
            
            # Cache to local database for future use
            if soundtrack_db is not None:
                cache_key = f"{title} ({year})" if year else title
                soundtrack_db[cache_key] = {
                    'title': title,
                    'year': year,
                    'imdb_id': imdb_id,
                    'tracks': tracks,
                    'source': 'musicbrainz',
                    'cached_at': datetime.now().isoformat()
                }
                _save_local_database(soundtrack_db)
            
            return tracks
        else:
            logger.info("✗ MusicBrainz: No soundtrack found")
    
    # Fallback to local database
    if soundtrack_db:
        logger.info("Checking local database...")
        
        # Try multiple matching strategies
        for matcher in [exact_match, fuzzy_match, imdb_match]:
            tracks = matcher(title, year, imdb_id, soundtrack_db)
            if tracks:
                logger.info(f"✓ Local DB: Found {len(tracks)} tracks")
                return tracks
        
        logger.info("✗ Local DB: No soundtrack found")
    
    return []
```

#### 1.4 Add Configuration
```python
# In shared/config.py

class PipelineConfig(BaseSettings):
    # Soundtrack enrichment settings
    use_musicbrainz: bool = Field(default=True, env="USE_MUSICBRAINZ")
    musicbrainz_timeout: int = Field(default=10, env="MUSICBRAINZ_TIMEOUT")
    cache_musicbrainz: bool = Field(default=True, env="CACHE_MUSICBRAINZ")
```

### Phase 2: Testing & Refinement (Week 2)

#### 2.1 Test with Sample Movies
```bash
# Test with known Bollywood movies
python scripts/test_musicbrainz.py

# Expected results:
# - Jaane Tu Ya Jaane Na (2008) - tt0473367 ✓
# - 3 Idiots (2009) - tt1187043 ✓
# - Dangal (2016) - tt5074352 ✓
```

#### 2.2 Build Test Script
```python
# File: scripts/test_musicbrainz.py

#!/usr/bin/env python3
"""Test MusicBrainz integration with popular Bollywood movies"""

from scripts.musicbrainz_client import MusicBrainzClient
import json

TEST_MOVIES = [
    {"title": "Jaane Tu... Ya Jaane Na", "year": 2008, "imdb_id": "tt0473367"},
    {"title": "3 Idiots", "year": 2009, "imdb_id": "tt1187043"},
    {"title": "Dangal", "year": 2016, "imdb_id": "tt5074352"},
    {"title": "PK", "year": 2014, "imdb_id": "tt2338151"},
    {"title": "Baahubali", "year": 2015, "imdb_id": "tt2631186"},
]

def test_musicbrainz():
    client = MusicBrainzClient()
    results = []
    
    for movie in TEST_MOVIES:
        print(f"\nTesting: {movie['title']} ({movie['year']})")
        print(f"  IMDb ID: {movie['imdb_id']}")
        
        soundtrack = client.get_soundtrack(movie['imdb_id'])
        
        if soundtrack and soundtrack['found']:
            tracks = soundtrack['tracks']
            print(f"  ✓ Found {len(tracks)} tracks")
            if tracks:
                print(f"    First track: {tracks[0]['title']} - {tracks[0]['artist']}")
            
            results.append({
                'movie': movie,
                'success': True,
                'track_count': len(tracks)
            })
        else:
            print(f"  ✗ No soundtrack found")
            results.append({
                'movie': movie,
                'success': False,
                'track_count': 0
            })
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    success_count = sum(1 for r in results if r['success'])
    print(f"Success rate: {success_count}/{len(TEST_MOVIES)} ({success_count/len(TEST_MOVIES)*100:.0f}%)")
    
    return results

if __name__ == "__main__":
    results = test_musicbrainz()
    
    # Save results
    with open('musicbrainz_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
```

#### 2.3 Measure Coverage
```bash
# Run test and analyze
python scripts/test_musicbrainz.py

# Expected: 70-80% success rate for popular Bollywood movies
# Missing movies will need manual addition to local DB
```

### Phase 3: Optional Spotify Integration (Week 3+)

**Only implement if MusicBrainz coverage is < 60%**

#### 3.1 Setup Spotify
```bash
pip install spotipy
```

#### 3.2 Register App
1. Go to https://developer.spotify.com/dashboard
2. Create app
3. Get Client ID and Secret
4. Add to `config/secrets.json`

#### 3.3 Implement Spotify Fallback
```python
# File: scripts/spotify_client.py

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

class SpotifyClient:
    def __init__(self, client_id: str, client_secret: str):
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
    
    def get_soundtrack(self, movie_title: str, year: int) -> Optional[Dict]:
        """Search Spotify for soundtrack"""
        query = f'album:"{movie_title}" soundtrack year:{year}'
        
        try:
            results = self.sp.search(q=query, type='album', limit=5)
            albums = results['albums']['items']
            
            if not albums:
                return None
            
            # Get first matching album
            album = albums[0]
            album_id = album['id']
            
            # Get tracks
            album_details = self.sp.album(album_id)
            tracks = []
            
            for item in album_details['tracks']['items']:
                tracks.append({
                    'title': item['name'],
                    'artist': ', '.join([a['name'] for a in item['artists']]),
                    'composer': '',
                    'duration_ms': item['duration_ms']
                })
            
            return {
                'found': True,
                'source': 'spotify',
                'tracks': tracks
            }
            
        except Exception as e:
            print(f"Spotify error: {e}")
            return None
```

---

## Maintenance Strategy

### Weekly Tasks
- **Monitor MusicBrainz**: Check for API changes
- **Update Local DB**: Add movies not found in MusicBrainz
- **Review Logs**: Identify patterns in failures

### Monthly Tasks
- **Coverage Analysis**: Measure MusicBrainz success rate
- **Database Cleanup**: Remove duplicates, fix errors
- **Performance Tuning**: Optimize cache hit rate

### Quarterly Tasks
- **Full Test Suite**: Run on 100+ movies
- **Update Dependencies**: Update musicbrainzngs, spotipy
- **Community Contribution**: Submit missing data to MusicBrainz

---

## Success Metrics

### KPIs to Track

1. **Coverage Rate**
   - Target: 80% of movies have soundtrack
   - Measure: `(movies_with_soundtrack / total_movies) * 100`

2. **Source Distribution**
   - MusicBrainz: 60-70%
   - Local DB: 20-30%
   - Spotify: 5-10%

3. **Cache Hit Rate**
   - Target: 90% after initial run
   - Measure: `(cache_hits / total_requests) * 100`

4. **API Performance**
   - MusicBrainz: < 2s per request
   - Spotify: < 1s per request
   - Local DB: < 0.1s per request

5. **Data Quality**
   - Track completeness: > 95%
   - Artist accuracy: > 90%
   - Title accuracy: > 95%

### Monitoring Dashboard

```python
# File: tools/soundtrack_metrics.py

def generate_metrics_report(output_dir: Path):
    """Generate soundtrack enrichment metrics"""
    
    # Load all job manifests
    jobs = load_all_jobs(output_dir)
    
    metrics = {
        'total_movies': len(jobs),
        'with_soundtrack': 0,
        'source_distribution': {'musicbrainz': 0, 'local': 0, 'spotify': 0},
        'avg_tracks_per_movie': 0,
        'coverage_rate': 0
    }
    
    for job in jobs:
        enrichment = load_enrichment(job)
        if enrichment and enrichment.get('soundtrack'):
            metrics['with_soundtrack'] += 1
            source = enrichment.get('soundtrack_source', 'unknown')
            metrics['source_distribution'][source] = metrics['source_distribution'].get(source, 0) + 1
    
    metrics['coverage_rate'] = (metrics['with_soundtrack'] / metrics['total_movies']) * 100
    
    return metrics
```

---

## Risk Mitigation

### Risk 1: MusicBrainz Rate Limits
**Impact**: Medium  
**Probability**: Low  
**Mitigation**:
- Implement 1-second delay between requests
- Cache all results to local DB
- Use local DB for repeat requests

### Risk 2: API Downtime
**Impact**: Low (has fallback)  
**Probability**: Low  
**Mitigation**:
- Primary fallback to local DB
- Continue processing without soundtrack
- Retry in next run

### Risk 3: Incomplete Data
**Impact**: Medium  
**Probability**: Medium  
**Mitigation**:
- Allow manual additions to local DB
- Community contribution to MusicBrainz
- Spotify as tertiary fallback

### Risk 4: Data Quality Issues
**Impact**: Low  
**Probability**: Medium  
**Mitigation**:
- Validate data format before saving
- Log data quality issues
- Manual review process for corrections

---

## Cost-Benefit Analysis

### Implementation Costs

| Phase | Time | Resources | Risk |
|-------|------|-----------|------|
| Phase 1 (MB + Local) | 2-3 days | 1 developer | Low |
| Phase 2 (Testing) | 1-2 days | 1 developer | Low |
| Phase 3 (Spotify) | 1 day | 1 developer | Low |
| **Total** | **4-6 days** | **1 developer** | **Low** |

### Benefits

| Benefit | Impact | Timeline |
|---------|--------|----------|
| Automatic soundtrack data | High | Immediate |
| Reduced manual entry | High | Week 1 |
| Better ASR accuracy | Medium | Ongoing |
| Improved subtitles | Medium | Ongoing |
| User satisfaction | High | Long-term |

### ROI Estimate

- **Setup Time**: 1 week
- **Manual Entry Saved**: 5-10 min per movie
- **Movies per month**: ~50
- **Time saved**: 4-8 hours/month
- **Payback period**: < 1 month

---

## Recommendation Summary

### ✅ Implement This Strategy

**Primary**: MusicBrainz API
- Free, reliable, good coverage
- 1-second rate limit is acceptable
- Community-maintained data quality

**Fallback 1**: Local Database
- Always available (offline)
- Fast lookups
- Manual curation for gaps

**Fallback 2**: Spotify API (Optional)
- Only if coverage < 60%
- Good for mainstream movies
- Requires credentials

### ❌ Avoid These

**Web Scraping**: 
- Fragile (sites change)
- Legal concerns
- High maintenance
- Use only for one-time DB population

**Lyrics Alignment**:
- Too complex for initial phase
- Requires large lyrics database
- Consider for Phase 2 (after 6 months)

**Multi-language**:
- Add after core system stable
- Not critical for MVP
- Moderate complexity

---

## Next Steps

1. **Week 1**: Implement MusicBrainz + Local DB fallback
2. **Week 2**: Test with 20+ popular Bollywood movies
3. **Week 3**: Measure coverage, decide on Spotify
4. **Week 4**: Documentation and handoff

**Decision Point**: After Week 2
- If coverage > 70%: Ship it! ✅
- If coverage 50-70%: Add Spotify
- If coverage < 50%: Consider hybrid scraping approach

**Success Criteria**:
- ✅ 80% of movies have soundtrack data
- ✅ < 2s average enrichment time
- ✅ Zero manual intervention for popular movies
- ✅ Graceful degradation when APIs fail
