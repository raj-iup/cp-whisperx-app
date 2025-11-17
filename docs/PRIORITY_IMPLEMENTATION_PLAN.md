# Priority Implementation Plan
## Soundtrack Enrichment & Pipeline Optimization

**Date**: 2025-11-14  
**Status**: Implementation Ready  
**Estimated Time**: 11-15 hours total

---

## Executive Summary

Based on analysis of the current pipeline state and issues, this document outlines a prioritized implementation plan addressing:

1. **Task 1**: Enable song bias injection by default for Bollywood movies ✅ **ALREADY WORKING**
2. **Task 2**: Fix incorrect ASR path warnings in translation stage ⚠️ **NEEDS FIX**
3. **MUX failure**: SRT codec issue with MP4 container ⚠️ **NEEDS FIX**
4. **Soundtrack Enhancement**: Implement MusicBrainz API integration 🚀 **HIGH IMPACT**
5. **Glossary Consolidation**: Centralize glossary management 📚 **OPTIMIZATION**
6. **Pipeline Architecture**: Best practices review and optimization 🏗️ **FOUNDATION**

---

## Current State Analysis

### ✅ What's Working

**Song Bias Injection** (Stage 7):
- **Status**: ✅ WORKING CORRECTLY
- Successfully loads 6 songs from soundtrack
- Loads 16 bias terms from enrichment data
- Processes all 2762 segments
- **Issue**: Made 0 corrections (phonetic matching disabled - needs `jellyfish`)

**TMDB Integration** (Stage 2):
- ✅ Successfully fetches movie metadata
- ✅ Has soundtrack data from local database
- ✅ IMDb ID available: tt0473367
- ✅ MusicBrainz already fetched data (verified in enrichment.json)

**ASR Output** (Stage 6):
- ✅ Correctly outputting to `06_asr/transcript.json` and `segments.json`
- ✅ 2762 segments successfully transcribed

### ⚠️ What Needs Fixing

**Issue 1: MUX Failure** (Stage 15)
```
ERROR: Could not find tag for codec subrip in stream #2
```
- **Cause**: MP4 container doesn't support SRT subtitles natively
- **Impact**: Pipeline fails at final stage
- **Solution**: Use MOV-TEXT codec for MP4 or change to MKV

**Issue 2: Translation Stage Warning** (Stage 12)
```
WARNING: ASR output not found: .../asr/transcript.json
```
- **Cause**: Looking in wrong path (should be `06_asr/transcript.json`)
- **Impact**: Confusing warning logs (but stage continues correctly)
- **Solution**: Update path in translation script

**Issue 3: Song Bias Corrections Ineffective** (Stage 7)
```
WARNING: jellyfish not installed - phonetic matching disabled
Corrected 0 segments with 0 changes
```
- **Cause**: Missing `jellyfish` library for phonetic matching
- **Impact**: Song lyrics not being corrected despite having bias terms
- **Solution**: Install jellyfish + review matching thresholds

---

## Priority 1: Critical Fixes (2-3 hours)

### Fix 1.1: MUX Subtitle Codec ⚡ HIGH PRIORITY
**Time**: 30 minutes  
**Impact**: Pipeline completion

**Problem**: MP4 doesn't support SRT subtitles
**Solution**: Add MOV-TEXT conversion for MP4

```python
# File: scripts/mux.py

def mux_subtitles(video_path, subtitle_path, output_path):
    """Mux subtitles into video"""
    
    # Detect output format
    output_ext = Path(output_path).suffix.lower()
    
    if output_ext == '.mp4':
        # MP4 requires mov_text codec
        cmd = [
            'ffmpeg', '-i', video_path,
            '-i', subtitle_path,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'mov_text',  # Use mov_text instead of srt
            '-metadata:s:s:0', 'language=eng',
            '-metadata:s:s:0', 'title=English',
            output_path
        ]
    elif output_ext in ['.mkv', '.webm']:
        # MKV/WebM support SRT natively
        cmd = [
            'ffmpeg', '-i', video_path,
            '-i', subtitle_path,
            '-c:v', 'copy',
            '-c:a', 'copy',
            '-c:s', 'srt',
            '-metadata:s:s:0', 'language=eng',
            output_path
        ]
    else:
        # Default fallback
        cmd = [
            'ffmpeg', '-i', video_path,
            '-i', subtitle_path,
            '-c', 'copy',
            output_path
        ]
    
    # Execute
    subprocess.run(cmd, check=True)
```

**Verification**:
```bash
# Test with current job
cd /Users/rpatel/Projects/cp-whisperx-app
python scripts/mux.py
```

---

### Fix 1.2: Translation Stage Path Warning ⚡ MEDIUM PRIORITY
**Time**: 15 minutes  
**Impact**: Clean logs

**Problem**: Looking for `asr/transcript.json` instead of `06_asr/transcript.json`

```python
# File: scripts/translation_refine.py

def load_asr_transcript(output_base: Path):
    """Load ASR transcript"""
    
    # Try multiple paths (for backwards compatibility)
    possible_paths = [
        output_base / "06_asr" / "transcript.json",  # New standard
        output_base / "06_asr" / "segments.json",    # Alternative
        output_base / "asr" / "transcript.json",     # Legacy
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # Not found
    logger.warning(f"ASR transcript not found in any standard location")
    return None
```

---

### Fix 1.3: Enable Jellyfish for Phonetic Matching ⚡ HIGH PRIORITY
**Time**: 15 minutes  
**Impact**: Song bias correction effectiveness

**Problem**: Phonetic matching disabled, 0 corrections made
**Solution**: Install jellyfish and verify

```bash
# Install jellyfish
pip install jellyfish

# Add to requirements.txt
echo "jellyfish>=1.0.0" >> requirements-optional.txt

# Test song bias with jellyfish
cd /Users/rpatel/Projects/cp-whisperx-app
python scripts/song_bias_injection.py
```

**Expected Result**:
- Phonetic matching enabled
- Corrections for song lyrics (artist names, song titles)
- Better subtitle quality for songs

---

## Priority 2: Must-Do Enhancements (4-6 hours)

### Enhancement 2.1: Auto-Enable Song Bias for Bollywood ⚡ HIGH IMPACT
**Time**: 1 hour  
**Impact**: Better lyrics by default

**Current**: Song bias only runs if soundtrack data exists (which it does!)
**Goal**: Auto-detect Bollywood movies and enable song bias

```python
# File: scripts/tmdb_enrichment.py

def is_bollywood_movie(metadata: Dict) -> bool:
    """Detect if movie is Bollywood"""
    
    # Check genres
    genres = metadata.get('genres', [])
    if 'Bollywood' in genres:
        return True
    
    # Check if Hindi/Indian movie
    original_language = metadata.get('original_language', '')
    if original_language in ['hi', 'ta', 'te', 'ml', 'kn', 'bn']:
        return True
    
    # Check production countries
    countries = metadata.get('production_countries', [])
    for country in countries:
        if country.get('iso_3166_1') == 'IN':
            return True
    
    return False

def enrich_movie_metadata(title: str, year: int, api_key: str):
    """Enrich with TMDB data and auto-detect Bollywood"""
    
    # ... existing TMDB fetch code ...
    
    # Auto-detect and mark as Bollywood
    if is_bollywood_movie(tmdb_data):
        enrichment['is_bollywood'] = True
        enrichment['enable_song_bias'] = True
        logger.info("✓ Detected as Bollywood movie - song bias enabled")
    
    return enrichment
```

**Configuration**:
```python
# In shared/config.py

class PipelineConfig(BaseSettings):
    # Song bias settings
    enable_song_bias: bool = Field(default=True, env="ENABLE_SONG_BIAS")
    auto_detect_bollywood: bool = Field(default=True, env="AUTO_DETECT_BOLLYWOOD")
```

---

### Enhancement 2.2: Implement MusicBrainz Integration ⚡ HIGHEST IMPACT
**Time**: 2 hours  
**Impact**: Automatic soundtrack fetching

**Goal**: Fetch soundtracks automatically instead of manual entry

**Step 1**: Install dependency
```bash
pip install musicbrainzngs
echo "musicbrainzngs>=0.7.1" >> requirements.txt
```

**Step 2**: Create MusicBrainz client
```python
# File: shared/musicbrainz_client.py

#!/usr/bin/env python3
"""MusicBrainz API client for soundtrack fetching"""

import musicbrainzngs
import time
from typing import Optional, List, Dict
from pathlib import Path

# Configure client
musicbrainzngs.set_useragent(
    "CP-WhisperX-App",
    "1.0",
    "rpatel@example.com"  # Update with real email
)

class MusicBrainzClient:
    """Client for MusicBrainz API"""
    
    def __init__(self, rate_limit: float = 1.0):
        """
        Initialize client
        
        Args:
            rate_limit: Seconds between requests (default: 1.0)
        """
        self.rate_limit = rate_limit
        self.last_request = 0
    
    def _wait_rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        self.last_request = time.time()
    
    def get_soundtrack(self, imdb_id: str) -> Optional[Dict]:
        """
        Fetch soundtrack for movie using IMDb ID
        
        Args:
            imdb_id: IMDb identifier (e.g., 'tt0473367')
        
        Returns:
            Dict with tracks or None
        """
        try:
            self._wait_rate_limit()
            
            # Search for soundtrack release
            result = musicbrainzngs.browse_releases(
                imdb=imdb_id,
                release_type=['soundtrack'],
                inc=['recordings', 'artist-credits']
            )
            
            if not result.get('release-list'):
                return None
            
            # Get first soundtrack
            release = result['release-list'][0]
            release_id = release['id']
            
            # Get detailed tracks
            self._wait_rate_limit()
            details = musicbrainzngs.get_release_by_id(
                release_id,
                includes=['recordings', 'artist-credits']
            )
            
            # Parse tracks
            tracks = []
            for medium in details['release'].get('medium-list', []):
                for track in medium.get('track-list', []):
                    recording = track.get('recording', {})
                    
                    # Extract title
                    title = recording.get('title', '')
                    
                    # Extract artists
                    artists = []
                    for credit in recording.get('artist-credit', []):
                        if isinstance(credit, dict):
                            artist_name = credit.get('artist', {}).get('name')
                            if artist_name:
                                artists.append(artist_name)
                    
                    tracks.append({
                        'title': title,
                        'artist': ', '.join(artists),
                        'composer': '',  # Not easily extractable
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

**Step 3**: Integrate into TMDB enrichment
```python
# File: scripts/tmdb_enrichment.py

from shared.musicbrainz_client import MusicBrainzClient

def get_soundtrack_for_movie(
    title: str,
    year: Optional[int],
    imdb_id: Optional[str],
    soundtrack_db_path: Path,
    use_musicbrainz: bool = True
) -> List[Dict]:
    """
    Get soundtrack with cascade fallback
    
    Priority:
    1. MusicBrainz API (if IMDb ID available)
    2. Local database
    """
    
    # Load local database
    soundtrack_db = load_local_soundtrack_db(soundtrack_db_path)
    
    # Try MusicBrainz first
    if use_musicbrainz and imdb_id:
        print(f"Querying MusicBrainz for {imdb_id}...")
        
        client = MusicBrainzClient()
        mb_result = client.get_soundtrack(imdb_id)
        
        if mb_result and mb_result['found']:
            tracks = mb_result['tracks']
            print(f"✓ MusicBrainz: Found {len(tracks)} tracks")
            
            # Cache to local database
            cache_key = f"{title} ({year})" if year else title
            soundtrack_db[cache_key] = {
                'title': title,
                'year': year,
                'imdb_id': imdb_id,
                'tracks': tracks,
                'source': 'musicbrainz'
            }
            save_local_soundtrack_db(soundtrack_db, soundtrack_db_path)
            
            return tracks
        else:
            print("✗ MusicBrainz: No soundtrack found")
    
    # Fallback to local database
    tracks = search_local_soundtrack_db(title, year, imdb_id, soundtrack_db)
    if tracks:
        print(f"✓ Local DB: Found {len(tracks)} tracks")
        return tracks
    
    print("✗ No soundtrack found in any source")
    return []
```

**Verification**:
```bash
# Test with existing movie
cd /Users/rpatel/Projects/cp-whisperx-app
python -c "
from shared.musicbrainz_client import MusicBrainzClient
client = MusicBrainzClient()
result = client.get_soundtrack('tt0473367')
print(f'Found: {result}')
"
```

---

### Enhancement 2.3: Centralized Data Loaders ⚡ MEDIUM IMPACT
**Time**: 2 hours  
**Impact**: Code maintainability

**Goal**: Unified data access across all stages

**Already Exists**: `shared/tmdb_loader.py` ✅

**Enhancements Needed**:

1. **Bias Registry** (centralized bias terms)
```python
# File: shared/bias_registry.py (ALREADY EXISTS - ENHANCE IT)

class BiasRegistry:
    """Centralized registry for all bias terms"""
    
    def __init__(self, output_base: Path):
        self.output_base = output_base
        self.tmdb_loader = TMDBLoader(output_base)
        self._cache = {}
    
    def get_song_bias_terms(self) -> List[str]:
        """Get song-specific bias terms from soundtrack"""
        if 'song_bias' in self._cache:
            return self._cache['song_bias']
        
        tmdb_data = self.tmdb_loader.load()
        terms = []
        
        for song in tmdb_data.soundtrack:
            # Add song title
            if song.get('title'):
                terms.append(song['title'])
            
            # Add artists
            if song.get('artist'):
                for artist in song['artist'].split(','):
                    terms.append(artist.strip())
            
            # Add composer
            if song.get('composer'):
                terms.append(song['composer'])
        
        self._cache['song_bias'] = terms
        return terms
    
    def get_cast_bias_terms(self) -> List[str]:
        """Get cast names for bias"""
        if 'cast_bias' in self._cache:
            return self._cache['cast_bias']
        
        tmdb_data = self.tmdb_loader.load()
        self._cache['cast_bias'] = tmdb_data.cast
        return tmdb_data.cast
    
    def get_all_bias_terms(self) -> Dict[str, List[str]]:
        """Get all bias terms organized by type"""
        return {
            'songs': self.get_song_bias_terms(),
            'cast': self.get_cast_bias_terms(),
            'crew': self.tmdb_loader.load().crew
        }
```

2. **Update stages to use centralized loaders**
```python
# File: scripts/song_bias_injection.py

from shared.bias_registry import BiasRegistry

def main():
    # Old way (scattered code):
    # tmdb_file = output_base / "02_tmdb" / "enrichment.json"
    # with open(tmdb_file) as f: ...
    
    # New way (centralized):
    registry = BiasRegistry(output_base)
    bias_terms = registry.get_song_bias_terms()
    
    logger.info(f"Loaded {len(bias_terms)} bias terms from registry")
```

---

## Priority 3: Should-Do Optimizations (4-6 hours)

### Optimization 3.1: Caching Layer ⚡ MEDIUM IMPACT
**Time**: 3 hours  
**Impact**: 2-3x faster re-runs

**Goal**: Cache expensive operations

**Implementation**:
```python
# File: shared/cache_manager.py

#!/usr/bin/env python3
"""Centralized caching for pipeline operations"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any, Dict

class CacheManager:
    """Manage cached data with expiration"""
    
    def __init__(self, cache_dir: Path, default_ttl: int = 2592000):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache storage
            default_ttl: Default time-to-live in seconds (30 days)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = default_ttl
    
    def _get_cache_key(self, namespace: str, key: str) -> str:
        """Generate cache key hash"""
        combined = f"{namespace}:{key}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get(self, namespace: str, key: str) -> Optional[Any]:
        """
        Get cached data
        
        Args:
            namespace: Cache namespace (e.g., 'tmdb', 'musicbrainz')
            key: Cache key (e.g., movie IMDb ID)
        
        Returns:
            Cached data or None if expired/not found
        """
        cache_key = self._get_cache_key(namespace, key)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check expiration
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            ttl = cache_data.get('ttl', self.default_ttl)
            
            if datetime.now() > cached_at + timedelta(seconds=ttl):
                # Expired
                cache_file.unlink()
                return None
            
            return cache_data['data']
        
        except Exception:
            return None
    
    def set(self, namespace: str, key: str, data: Any, ttl: Optional[int] = None):
        """
        Store data in cache
        
        Args:
            namespace: Cache namespace
            key: Cache key
            data: Data to cache
            ttl: Time-to-live in seconds (None = default)
        """
        cache_key = self._get_cache_key(namespace, key)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        cache_data = {
            'namespace': namespace,
            'key': key,
            'data': data,
            'cached_at': datetime.now().isoformat(),
            'ttl': ttl or self.default_ttl
        }
        
        with open(cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
    
    def clear_namespace(self, namespace: str):
        """Clear all cache entries in a namespace"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                if cache_data.get('namespace') == namespace:
                    cache_file.unlink()
            except Exception:
                pass


# Usage in MusicBrainz client
class MusicBrainzClient:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache = CacheManager(cache_dir or Path.home() / ".cache" / "cp-whisperx")
    
    def get_soundtrack(self, imdb_id: str) -> Optional[Dict]:
        # Check cache first
        cached = self.cache.get('musicbrainz', imdb_id)
        if cached:
            return cached
        
        # Fetch from API
        result = self._fetch_from_api(imdb_id)
        
        # Cache result (30 days)
        if result:
            self.cache.set('musicbrainz', imdb_id, result, ttl=2592000)
        
        return result
```

---

### Optimization 3.2: Bias Learning ⚡ LOW PRIORITY
**Time**: 2 hours  
**Impact**: Improves over time

**Goal**: Learn from corrections to improve future runs

**Implementation**:
```python
# File: shared/bias_learning.py

#!/usr/bin/env python3
"""Learn from bias corrections to improve accuracy"""

import json
from pathlib import Path
from typing import Dict, List
from collections import Counter

class BiasLearner:
    """Track and learn from bias corrections"""
    
    def __init__(self, learning_db_path: Path):
        self.db_path = learning_db_path
        self.corrections = self._load_corrections()
    
    def _load_corrections(self) -> Dict:
        """Load correction history"""
        if not self.db_path.exists():
            return {'corrections': [], 'patterns': {}}
        
        with open(self.db_path, 'r') as f:
            return json.load(f)
    
    def record_correction(
        self,
        original: str,
        corrected: str,
        method: str,
        confidence: float
    ):
        """Record a bias correction"""
        self.corrections['corrections'].append({
            'original': original,
            'corrected': corrected,
            'method': method,
            'confidence': confidence
        })
        
        # Update patterns
        key = original.lower()
        if key not in self.corrections['patterns']:
            self.corrections['patterns'][key] = []
        
        self.corrections['patterns'][key].append(corrected)
    
    def get_learned_bias_terms(self) -> List[str]:
        """Get most common corrections as new bias terms"""
        terms = []
        
        for original, corrections in self.corrections['patterns'].items():
            # Find most common correction
            counter = Counter(corrections)
            most_common = counter.most_common(1)[0][0]
            
            if counter[most_common] >= 3:  # Seen 3+ times
                terms.append(most_common)
        
        return terms
    
    def save(self):
        """Save corrections to disk"""
        with open(self.db_path, 'w') as f:
            json.dump(self.corrections, f, indent=2)
```

---

## Priority 4: Glossary Consolidation (4 hours)

### Goal: Centralize all glossary solutions

**Current State**:
- `/glossary/hinglish_master.tsv` - Main glossary
- `/glossary/unified_glossary.tsv` - Unified terms
- `/glossary/glossary_learned/` - Learned corrections
- `shared/glossary.py` - Core loader
- `shared/glossary_advanced.py` - Advanced features
- `shared/glossary_ml.py` - ML-based matching
- `shared/glossary_unified.py` - Unified loader

**Problems**:
- Scattered implementations
- Duplicate code
- Unclear which to use
- Hard to maintain

**Solution**: Consolidate into single unified system

```python
# File: shared/glossary_manager.py

#!/usr/bin/env python3
"""Unified Glossary Management System"""

from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd

class GlossaryManager:
    """Centralized glossary management"""
    
    def __init__(self, glossary_dir: Path):
        """
        Initialize glossary manager
        
        Args:
            glossary_dir: Path to glossary directory
        """
        self.glossary_dir = Path(glossary_dir)
        self.master_glossary = self._load_master()
        self.learned_terms = self._load_learned()
    
    def _load_master(self) -> pd.DataFrame:
        """Load master glossary"""
        master_path = self.glossary_dir / "hinglish_master.tsv"
        
        if not master_path.exists():
            return pd.DataFrame(columns=['incorrect', 'correct', 'category'])
        
        return pd.read_csv(master_path, sep='\t')
    
    def _load_learned(self) -> pd.DataFrame:
        """Load learned corrections"""
        learned_dir = self.glossary_dir / "glossary_learned"
        
        if not learned_dir.exists():
            return pd.DataFrame(columns=['incorrect', 'correct', 'confidence'])
        
        # Combine all learned files
        dfs = []
        for file in learned_dir.glob("*.tsv"):
            df = pd.read_csv(file, sep='\t')
            dfs.append(df)
        
        if not dfs:
            return pd.DataFrame(columns=['incorrect', 'correct', 'confidence'])
        
        return pd.concat(dfs, ignore_index=True)
    
    def get_all_terms(self) -> pd.DataFrame:
        """Get all glossary terms (master + learned)"""
        # Combine master and high-confidence learned
        learned_high_conf = self.learned_terms[
            self.learned_terms['confidence'] >= 0.8
        ]
        
        return pd.concat([self.master_glossary, learned_high_conf], ignore_index=True)
    
    def apply_to_text(self, text: str) -> str:
        """Apply glossary corrections to text"""
        corrected = text
        
        for _, row in self.get_all_terms().iterrows():
            incorrect = row['incorrect']
            correct = row['correct']
            
            # Case-insensitive replacement
            corrected = corrected.replace(incorrect, correct)
        
        return corrected
    
    def add_learned_term(
        self,
        incorrect: str,
        correct: str,
        confidence: float,
        source: str = 'pipeline'
    ):
        """Add a new learned term"""
        new_term = pd.DataFrame([{
            'incorrect': incorrect,
            'correct': correct,
            'confidence': confidence,
            'source': source
        }])
        
        self.learned_terms = pd.concat([self.learned_terms, new_term], ignore_index=True)
        
        # Save to learned directory
        output_file = self.glossary_dir / "glossary_learned" / f"{source}.tsv"
        self.learned_terms.to_csv(output_file, sep='\t', index=False)
```

---

## Implementation Timeline

### Week 1: Critical Fixes + MusicBrainz (6-8 hours)
**Days 1-2**:
- ✅ Fix MUX subtitle codec (30 min)
- ✅ Fix translation path warning (15 min)
- ✅ Install jellyfish for phonetic matching (15 min)
- ✅ Implement MusicBrainz client (2 hours)
- ✅ Integrate MusicBrainz into TMDB stage (1 hour)
- ✅ Test with 5 popular Bollywood movies (1 hour)

**Expected Results**:
- Pipeline completes successfully ✅
- Soundtrack data fetched automatically 🎵
- Song bias corrections working 🎯

### Week 2: Enhancements + Testing (4-6 hours)
**Days 3-4**:
- ✅ Auto-enable song bias for Bollywood (1 hour)
- ✅ Enhance BiasRegistry for centralized access (2 hours)
- ✅ Comprehensive testing with 10+ movies (2 hours)
- ✅ Documentation updates (1 hour)

**Expected Results**:
- Cleaner code architecture 🏗️
- Better bias correction accuracy 📈
- Comprehensive test coverage ✅

### Week 3: Optimizations (Optional) (4-6 hours)
**Days 5-7**:
- ⚡ Implement caching layer (3 hours)
- ⚡ Bias learning system (2 hours)
- ⚡ Glossary consolidation (4 hours)

**Expected Results**:
- 2-3x faster re-runs 🚀
- System learns over time 🧠
- Unified glossary management 📚

---

## Success Metrics

### Phase 1 (Critical Fixes)
- ✅ MUX stage completes successfully
- ✅ No incorrect warnings in logs
- ✅ Song bias makes corrections (> 0 changes)

### Phase 2 (Enhancements)
- 🎯 80%+ of Bollywood movies have soundtrack data
- 🎯 MusicBrainz fetch time < 2s per movie
- 🎯 Song bias correction rate > 10% of song segments

### Phase 3 (Optimizations)
- ⚡ Cache hit rate > 90% for repeat runs
- ⚡ 50%+ reduction in API calls
- 📚 Single glossary interface for all stages

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MusicBrainz rate limits | Low | Medium | 1s delay + caching |
| MusicBrainz incomplete data | Medium | Low | Fallback to local DB |
| Jellyfish compatibility | Low | Low | Optional dependency |
| FFmpeg codec issues | Low | Medium | Multiple format support |
| Breaking existing jobs | Low | High | Backwards compatibility |

---

## Next Steps

### Immediate Actions (Today)
1. Fix MUX codec issue
2. Install jellyfish
3. Test song bias corrections
4. Verify pipeline completion

### This Week
1. Implement MusicBrainz integration
2. Test with 10+ Bollywood movies
3. Measure improvement in subtitle quality
4. Update documentation

### Next Month
1. Add caching layer
2. Implement bias learning
3. Consolidate glossary system
4. Full regression testing

---

## Appendix: Testing Checklist

### Before Implementation
- [x] Pipeline fails at MUX stage
- [x] Translation stage shows incorrect warnings
- [x] Song bias makes 0 corrections
- [x] Soundtrack data from local database only

### After Priority 1 (Critical Fixes)
- [ ] MUX stage completes successfully
- [ ] No incorrect path warnings
- [ ] Song bias makes > 0 corrections
- [ ] Subtitles muxed into video correctly

### After Priority 2 (Enhancements)
- [ ] MusicBrainz fetches soundtrack automatically
- [ ] Soundtrack cached to local database
- [ ] BiasRegistry provides centralized access
- [ ] 5+ test movies processed successfully

### After Priority 3 (Optimizations)
- [ ] Cache reduces API calls by 50%+
- [ ] Bias learning tracks corrections
- [ ] Single glossary interface working
- [ ] Performance improvements measured

---

**End of Implementation Plan**
