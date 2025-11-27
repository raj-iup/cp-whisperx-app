# Comprehensive Improvement Implementation Plan

**Document Version:** 1.0  
**Date:** November 24, 2025  
**Status:** Planning Phase

---

## 📋 Executive Summary

This plan integrates findings from the [Key Features Analysis](../How_Key_Features_Improve_Speech_Transcription_Translation_Accuracy.md) and TMDB research to enhance the CP-WhisperX-App pipeline from production-ready to research-grade quality.

**Goal:** Implement NER, Glossary, TMDB, Enhanced Lyrics Detection, and Speaker Diarization while maintaining backward compatibility with existing multi-environment bootstrap, job preparation, and pipeline execution systems.

**Timeline:** 6-8 weeks (phased rollout)  
**Impact:** 15-20% improvement in subtitle quality, 95%+ entity accuracy, automated glossary generation

---

## 🎯 Strategic Objectives

### Quality Improvements
1. **Character Name Accuracy:** 80% → 95%+ (via NER + TMDB)
2. **Location Accuracy:** 70% → 90%+ (via glossary + NER)
3. **Entity Preservation:** 60% → 95%+ (via NER in translation)
4. **Song Lyrics Quality:** 70% → 95%+ (via official lyrics integration)
5. **Overall WER:** ~15% → <12% (via combined enhancements)

### Automation Goals
1. **Eliminate manual glossary creation** (via TMDB auto-generation)
2. **Automated entity correction** (via NER post-processing)
3. **Smart speaker-to-character mapping** (via PyAnnote + TMDB)
4. **Context-aware translation** (via TMDB metadata)

### System Integration
1. **Backward compatible** with existing workflows
2. **Multi-environment support** (macOS, Linux, Windows PowerShell)
3. **Seamless bootstrap integration** (auto-install new dependencies)
4. **Pipeline-aware** (optional features via flags)

---

## 📊 Current State Assessment

### ✅ Already Implemented (Production-Ready)

| Feature | Status | Location | Notes |
|---------|--------|----------|-------|
| **Anti-Hallucination** | ✅ Production | `scripts/whisperx_translate_comparator.py` | condition_on_previous_text=False, compression ratio filtering |
| **Lyrics Detection** | ✅ Production | `scripts/lyrics_detection.py` | Basic detection, marks song segments |
| **VAD Diarization** | ✅ Production | PyAnnote integration | Speech/silence segmentation |
| **Source Separation** | ✅ Production | Demucs integration | Optional vocals/music separation |
| **Hinglish Detection** | ✅ Production | Word-level language tagging | Post-transcription analysis |
| **Hybrid Translation** | ✅ Production | `scripts/hybrid_subtitle_merger.py` | WhisperX + IndICTrans2 combo |
| **Glossary System** | ✅ Infrastructure | `glossary/` directory | TSV format, per-film prompts |
| **Multi-Environment** | ✅ Production | `bootstrap.sh`, 7 venvs | Isolated dependency management |

### ⚠️ Partially Implemented (Needs Enhancement)

| Feature | Status | Gap | Priority |
|---------|--------|-----|----------|
| **NER** | ❌ Missing | No entity recognition/correction | **P1** |
| **Speaker Diarization** | ⚠️ Basic | Only VAD, no "who spoke" | **P2** |
| **Language Diarization** | ⚠️ Post-hoc | Not used during transcription | **P3** |
| **Glossary Population** | ⚠️ Manual | No auto-generation | **P1** |
| **Lyrics Database** | ❌ Missing | No official lyrics integration | **P2** |
| **TMDB Integration** | ❌ Missing | No metadata fetching | **P1** |

---

## 🏗️ Implementation Architecture

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Add TMDB + NER infrastructure without disrupting existing pipeline

```
Current Pipeline:
  bootstrap.sh → prepare-job.sh → run-pipeline.sh
  
Enhanced Pipeline:
  bootstrap.sh (+ NER/TMDB deps) → 
  prepare-job.sh (+ TMDB fetch) → 
  run-pipeline.sh (+ NER correction, optional)
```

### Phase 2: Integration (Weeks 3-4)
**Goal:** Integrate NER + TMDB into transcription/translation stages

```
Transcription Stage:
  WhisperX ASR → [NEW: NER Correction] → [NEW: TMDB Entity Validation] → Output
  
Translation Stage:
  Source Text → [NEW: Entity Marking] → IndICTrans2/NLLB → [NEW: Entity Preservation] → Target Text
```

### Phase 3: Advanced Features (Weeks 5-6)
**Goal:** Add speaker diarization, lyrics database, enhanced hybrid

```
Advanced Pipeline:
  Audio → [NEW: Speaker Diarization] → Transcription → 
  [NEW: Character Mapping via TMDB] → 
  Translation → 
  [NEW: Speaker-labeled Subtitles]
  
Lyrics Enhancement:
  Song Detection → [NEW: Audio Fingerprinting] → 
  [NEW: TMDB Soundtrack Match] → 
  [NEW: Official Lyrics Fetch] → 
  Replace ASR Lyrics
```

### Phase 4: Refinement & Documentation (Weeks 7-8)
**Goal:** Polish, test, document all features

---

## 🔧 Technical Implementation Details

### 1. TMDB Integration (Priority 1)

#### 1.1 New Dependencies

**Add to `requirements-common.txt`:**
```python
# TMDB Integration
tmdbv3api>=1.9.0
requests>=2.31.0
cachetools>=5.3.0

# NER Support
spacy>=3.7.0
en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl
```

**Bootstrap Integration:**
```bash
# In scripts/bootstrap.sh - common environment section
echo "Installing TMDB and NER libraries..."
pip install tmdbv3api spacy
python -m spacy download en_core_web_sm
```

#### 1.2 Configuration

**Add to `config/.env.pipeline`:**
```bash
# TMDB Configuration
TMDB_ENABLED=true
TMDB_API_KEY=your_api_key_here
TMDB_CACHE_DIR=cache/tmdb
TMDB_AUTO_FETCH=true

# NER Configuration
NER_ENABLED=true
NER_MODEL=en_core_web_sm
NER_CORRECTION_MODE=post_processing  # or: inline
NER_CONFIDENCE_THRESHOLD=0.7
```

**Add to `config/secrets.json`:**
```json
{
  "tmdb_api_key": "YOUR_TMDB_API_KEY_HERE",
  "lyrics_api_key": "OPTIONAL_LYRICS_API_KEY"
}
```

#### 1.3 New Modules

**Create `shared/tmdb_client.py`:**
```python
"""
TMDB API Client
Fetches movie metadata for glossary generation and context
"""

from tmdbv3api import TMDb, Movie, Search
from pathlib import Path
import json
from typing import Dict, Optional, List
from cachetools import TTLCache
import logging

logger = logging.getLogger(__name__)

class TMDBClient:
    """Client for TMDB API with caching"""
    
    def __init__(self, api_key: str, cache_dir: Path):
        self.tmdb = TMDb()
        self.tmdb.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache (1 hour TTL)
        self._cache = TTLCache(maxsize=100, ttl=3600)
    
    def search_movie(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """Search for movie by title and optional year"""
        cache_key = f"{title}_{year}"
        
        if cache_key in self._cache:
            logger.debug(f"Cache hit for: {cache_key}")
            return self._cache[cache_key]
        
        # Check disk cache
        cache_file = self.cache_dir / f"{cache_key.replace(' ', '_')}.json"
        if cache_file.exists():
            logger.debug(f"Disk cache hit: {cache_file}")
            with open(cache_file) as f:
                data = json.load(f)
                self._cache[cache_key] = data
                return data
        
        # Fetch from TMDB
        logger.info(f"Fetching from TMDB: {title} ({year})")
        search = Search()
        results = search.movies(title)
        
        if year:
            results = [r for r in results if r.release_date and 
                      r.release_date.startswith(str(year))]
        
        if not results:
            logger.warning(f"No TMDB results for: {title} ({year})")
            return None
        
        # Get full movie details
        movie = Movie()
        movie_id = results[0].id
        
        movie_data = {
            'id': movie_id,
            'title': results[0].title,
            'original_title': results[0].original_title,
            'release_date': results[0].release_date,
            'year': results[0].release_date[:4] if results[0].release_date else None,
            'overview': results[0].overview,
            'genres': [g['name'] for g in results[0].genres] if hasattr(results[0], 'genres') else [],
            'cast': self._get_cast(movie_id),
            'crew': self._get_crew(movie_id),
            'production_countries': [c['name'] for c in results[0].production_countries] if hasattr(results[0], 'production_countries') else [],
            'spoken_languages': [l['name'] for l in results[0].spoken_languages] if hasattr(results[0], 'spoken_languages') else [],
        }
        
        # Cache results
        self._cache[cache_key] = movie_data
        with open(cache_file, 'w') as f:
            json.dump(movie_data, f, indent=2)
        
        logger.info(f"Cached TMDB data: {cache_file}")
        return movie_data
    
    def _get_cast(self, movie_id: int) -> List[Dict]:
        """Get cast information"""
        movie = Movie()
        credits = movie.credits(movie_id)
        
        cast_list = []
        for member in credits.get('cast', [])[:20]:  # Top 20 cast
            cast_list.append({
                'character': member.get('character', ''),
                'actor': member.get('name', ''),
                'order': member.get('order', 999),
                'gender': member.get('gender', 0)  # 0=unknown, 1=female, 2=male
            })
        
        return cast_list
    
    def _get_crew(self, movie_id: int) -> List[Dict]:
        """Get key crew information"""
        movie = Movie()
        credits = movie.credits(movie_id)
        
        # Filter for director, writer, music
        key_roles = ['Director', 'Writer', 'Screenplay', 'Music']
        crew_list = []
        
        for member in credits.get('crew', []):
            if member.get('job') in key_roles:
                crew_list.append({
                    'name': member.get('name', ''),
                    'job': member.get('job', '')
                })
        
        return crew_list
    
    def get_soundtrack_info(self, movie_id: int) -> Optional[List[str]]:
        """Get soundtrack information if available"""
        # Note: TMDB doesn't always have soundtrack data
        # This would need integration with MusicBrainz or other API
        logger.warning("Soundtrack API not yet implemented")
        return None
```

**Create `shared/ner_corrector.py`:**
```python
"""
Named Entity Recognition and Correction
Post-processes transcripts to fix entity errors using glossary
"""

import spacy
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import logging

logger = logging.getLogger(__name__)

class NERCorrector:
    """Entity recognition and correction"""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize NER model"""
        try:
            self.nlp = spacy.load(model_name)
            logger.info(f"Loaded spaCy model: {model_name}")
        except OSError:
            logger.error(f"spaCy model not found: {model_name}")
            logger.error("Run: python -m spacy download en_core_web_sm")
            raise
        
        # Entity correction maps (populated from glossary)
        self.character_map = {}
        self.location_map = {}
        self.error_map = {}
    
    def load_glossary(self, glossary: Dict):
        """Load glossary data for corrections"""
        logger.info("Loading glossary for NER corrections")
        
        # Build character name map
        for char in glossary.get('characters', []):
            name = char['name']
            self.character_map[name.lower()] = name
            
            # Add aliases
            for alias in char.get('aliases', []):
                self.character_map[alias.lower()] = name
            
            # Add common errors
            for error in char.get('common_errors', []):
                self.error_map[error.lower()] = name
        
        # Build location map
        for loc in glossary.get('locations', []):
            name = loc['name']
            self.location_map[name.lower()] = name
            
            # Add common errors
            for error in loc.get('common_errors', []):
                self.error_map[error.lower()] = name
        
        logger.info(f"Loaded {len(self.character_map)} character names, "
                   f"{len(self.location_map)} locations, "
                   f"{len(self.error_map)} error corrections")
    
    def correct_text(self, text: str) -> Tuple[str, List[Dict]]:
        """
        Correct entity errors in text
        
        Returns:
            (corrected_text, corrections_made)
        """
        corrections = []
        corrected = text
        
        # First pass: Known error corrections
        for error, correct in self.error_map.items():
            pattern = r'\b' + re.escape(error) + r'\b'
            matches = list(re.finditer(pattern, corrected, re.IGNORECASE))
            
            for match in reversed(matches):  # Reverse to maintain positions
                start, end = match.span()
                original = corrected[start:end]
                
                # Preserve original capitalization style
                if original[0].isupper():
                    replacement = correct
                else:
                    replacement = correct.lower()
                
                corrected = corrected[:start] + replacement + corrected[end:]
                
                corrections.append({
                    'type': 'known_error',
                    'original': original,
                    'corrected': replacement,
                    'position': start
                })
        
        # Second pass: NER-based corrections
        doc = self.nlp(corrected)
        
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                # Check if this person name is in our character map
                canonical = self.character_map.get(ent.text.lower())
                if canonical and canonical != ent.text:
                    # Found a better version
                    corrections.append({
                        'type': 'ner_person',
                        'original': ent.text,
                        'corrected': canonical,
                        'position': ent.start_char,
                        'entity_type': ent.label_
                    })
            
            elif ent.label_ in ['GPE', 'LOC']:
                # Check locations
                canonical = self.location_map.get(ent.text.lower())
                if canonical and canonical != ent.text:
                    corrections.append({
                        'type': 'ner_location',
                        'original': ent.text,
                        'corrected': canonical,
                        'position': ent.start_char,
                        'entity_type': ent.label_
                    })
        
        # Apply NER corrections
        for corr in reversed(sorted(corrections, key=lambda x: x['position'])):
            if corr['type'].startswith('ner_'):
                start = corr['position']
                end = start + len(corr['original'])
                corrected = corrected[:start] + corr['corrected'] + corrected[end:]
        
        if corrections:
            logger.info(f"Made {len(corrections)} entity corrections")
            for corr in corrections:
                logger.debug(f"  {corr['original']} → {corr['corrected']}")
        
        return corrected, corrections
    
    def tag_entities(self, text: str) -> List[Dict]:
        """
        Tag entities in text without correction
        Useful for translation stage to mark entities for preservation
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return entities
```

**Create `shared/glossary_generator.py`:**
```python
"""
Automatic Glossary Generation from TMDB
"""

import yaml
from pathlib import Path
from typing import Dict, Optional
import logging
import re

logger = logging.getLogger(__name__)

class GlossaryGenerator:
    """Generate glossaries from TMDB metadata"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_from_tmdb(self, tmdb_data: Dict, 
                          known_locations: Optional[List[str]] = None) -> Path:
        """
        Generate glossary YAML from TMDB movie data
        
        Args:
            tmdb_data: Movie metadata from TMDB
            known_locations: Additional location names (e.g., from plot)
        
        Returns:
            Path to generated glossary file
        """
        movie_title = tmdb_data['title']
        year = tmdb_data.get('year', 'unknown')
        
        logger.info(f"Generating glossary for: {movie_title} ({year})")
        
        glossary = {
            'movie': movie_title,
            'original_title': tmdb_data.get('original_title', movie_title),
            'year': year,
            'tmdb_id': tmdb_data['id'],
            'genres': tmdb_data.get('genres', []),
            'countries': tmdb_data.get('production_countries', []),
            'languages': tmdb_data.get('spoken_languages', []),
            'overview': tmdb_data.get('overview', ''),
            'characters': [],
            'locations': [],
            'context': self._infer_context(tmdb_data)
        }
        
        # Add characters from cast
        for cast_member in tmdb_data.get('cast', []):
            character_name = cast_member['character']
            
            if not character_name or character_name == 'Unknown':
                continue
            
            # Parse character name and aliases
            # e.g., "Jai Singh Rathore" → name="Jai Singh Rathore", aliases=["Jai", "Rathore"]
            aliases = self._extract_aliases(character_name)
            
            character = {
                'name': character_name,
                'actor': cast_member['actor'],
                'aliases': aliases,
                'order': cast_member['order'],
                'common_errors': []  # Populated manually or via ML later
            }
            
            glossary['characters'].append(character)
        
        # Add locations if provided
        if known_locations:
            for loc in known_locations:
                glossary['locations'].append({
                    'name': loc,
                    'type': 'unknown',
                    'common_errors': []
                })
        
        # Infer locations from plot/overview (basic)
        inferred_locations = self._extract_locations_from_text(
            tmdb_data.get('overview', '')
        )
        for loc in inferred_locations:
            if not any(l['name'] == loc for l in glossary['locations']):
                glossary['locations'].append({
                    'name': loc,
                    'type': 'inferred',
                    'source': 'overview'
                })
        
        # Save glossary
        filename = self._slugify(movie_title) + f"_{year}.yaml"
        output_path = self.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(glossary, f, default_flow_style=False, 
                     allow_unicode=True, sort_keys=False)
        
        logger.info(f"Generated glossary: {output_path}")
        logger.info(f"  Characters: {len(glossary['characters'])}")
        logger.info(f"  Locations: {len(glossary['locations'])}")
        
        return output_path
    
    def _extract_aliases(self, character_name: str) -> List[str]:
        """Extract aliases from character name"""
        aliases = []
        
        # Remove parenthetical notes
        name_clean = re.sub(r'\([^)]+\)', '', character_name).strip()
        
        # Split multi-word names
        parts = name_clean.split()
        if len(parts) > 1:
            # First name
            aliases.append(parts[0])
            # Last name
            aliases.append(parts[-1])
            # Full name
            if name_clean != character_name:
                aliases.append(name_clean)
        
        return aliases
    
    def _extract_locations_from_text(self, text: str) -> List[str]:
        """Basic location extraction from text"""
        # Simple pattern matching for common location markers
        locations = []
        
        # Cities pattern
        city_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b(?=\s+(?:city|City))'
        cities = re.findall(city_pattern, text)
        locations.extend(cities)
        
        # Country pattern
        country_pattern = r'\b(India|Mumbai|Delhi|Bangalore|Hyderabad|Chennai|Kolkata)\b'
        countries = re.findall(country_pattern, text)
        locations.extend(countries)
        
        return list(set(locations))
    
    def _infer_context(self, tmdb_data: Dict) -> Dict:
        """Infer translation context from metadata"""
        genres = [g.lower() for g in tmdb_data.get('genres', [])]
        
        context = {
            'tone': 'neutral',
            'formality': 'medium',
            'audience': 'general'
        }
        
        # Adjust based on genre
        if 'comedy' in genres:
            context['tone'] = 'casual'
            context['formality'] = 'low'
        elif 'romance' in genres:
            context['tone'] = 'expressive'
        elif 'action' in genres:
            context['tone'] = 'terse'
        
        # Adjust based on overview keywords
        overview = tmdb_data.get('overview', '').lower()
        if any(word in overview for word in ['youth', 'college', 'friends']):
            context['audience'] = 'youth'
            context['formality'] = 'low'
        elif any(word in overview for word in ['family', 'children']):
            context['audience'] = 'family'
        
        return context
    
    def _slugify(self, text: str) -> str:
        """Convert text to filename-safe slug"""
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[-\s]+', '_', text)
        return text
```

#### 1.4 Bootstrap Integration

**Update `scripts/bootstrap.sh`:**

```bash
# In install_common_environment() function, add:

echo "  Installing TMDB and NER support..."
pip install tmdbv3api>=1.9.0 \
            requests>=2.31.0 \
            cachetools>=5.3.0 \
            spacy>=3.7.0 \
            pyyaml>=6.0

# Download spaCy model
python -m spacy download en_core_web_sm

echo "  ✓ TMDB and NER libraries installed"
```

**Add environment check:**

```bash
check_tmdb_setup() {
    echo "Checking TMDB setup..."
    
    # Check if API key configured
    if ! grep -q "TMDB_API_KEY" config/.env.pipeline 2>/dev/null; then
        echo "⚠️  TMDB API key not configured"
        echo "   Get free key: https://www.themoviedb.org/settings/api"
        echo "   Add to config/.env.pipeline: TMDB_API_KEY=your_key"
    else
        echo "✓ TMDB configuration found"
    fi
    
    # Check if spaCy model downloaded
    if python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
        echo "✓ spaCy NER model installed"
    else
        echo "⚠️  spaCy model not found, downloading..."
        python -m spacy download en_core_web_sm
    fi
}
```

#### 1.5 Prepare-Job Integration

**Update `prepare-job.sh`:**

```bash
# Add new options
TMDB_FETCH=true
TMDB_TITLE=""
TMDB_YEAR=""

# Add option parsing
--tmdb-title)
    TMDB_TITLE="$2"
    shift 2
    ;;
--tmdb-year)
    TMDB_YEAR="$2"
    shift 2
    ;;
--no-tmdb)
    TMDB_FETCH=false
    shift
    ;;

# After creating job directory, add:
if [[ "$TMDB_FETCH" == "true" ]]; then
    echo "Fetching TMDB metadata..."
    
    # Extract title from filename if not provided
    if [[ -z "$TMDB_TITLE" ]]; then
        TMDB_TITLE=$(basename "$INPUT_MEDIA" | sed 's/\.[^.]*$//')
        echo "  Auto-detected title: $TMDB_TITLE"
    fi
    
    # Fetch and generate glossary
    python scripts/fetch_tmdb_metadata.py \
        --title "$TMDB_TITLE" \
        --year "$TMDB_YEAR" \
        --output "$JOB_DIR/glossary.yaml" \
        --cache-dir "cache/tmdb"
    
    if [[ $? -eq 0 ]]; then
        echo "  ✓ Generated glossary from TMDB: $JOB_DIR/glossary.yaml"
        # Add to job config
        echo "GLOSSARY_FILE=$JOB_DIR/glossary.yaml" >> "$JOB_DIR/config.env"
    else
        echo "  ⚠️  TMDB fetch failed, continuing without glossary"
    fi
fi
```

**Create `scripts/fetch_tmdb_metadata.py`:**

```python
#!/usr/bin/env python3
"""
Fetch TMDB metadata and generate glossary
Called by prepare-job.sh
"""

import argparse
import sys
from pathlib import Path
import os

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.tmdb_client import TMDBClient
from shared.glossary_generator import GlossaryGenerator
from shared.logger import setup_logger

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Fetch TMDB metadata')
    parser.add_argument('--title', required=True, help='Movie title')
    parser.add_argument('--year', type=int, help='Release year')
    parser.add_argument('--output', required=True, help='Output glossary file')
    parser.add_argument('--cache-dir', default='cache/tmdb', help='Cache directory')
    
    args = parser.parse_args()
    
    # Get API key
    api_key = os.getenv('TMDB_API_KEY')
    if not api_key:
        logger.error("TMDB_API_KEY not set in environment")
        logger.error("Get free key: https://www.themoviedb.org/settings/api")
        sys.exit(1)
    
    try:
        # Fetch from TMDB
        logger.info(f"Searching TMDB for: {args.title} ({args.year})")
        client = TMDBClient(api_key, Path(args.cache_dir))
        tmdb_data = client.search_movie(args.title, args.year)
        
        if not tmdb_data:
            logger.error(f"Movie not found on TMDB: {args.title}")
            sys.exit(1)
        
        logger.info(f"Found: {tmdb_data['title']} ({tmdb_data['year']})")
        logger.info(f"Cast: {len(tmdb_data['cast'])} members")
        
        # Generate glossary
        generator = GlossaryGenerator(Path(args.output).parent)
        glossary_file = generator.generate_from_tmdb(tmdb_data)
        
        # Move to output location
        if glossary_file != Path(args.output):
            import shutil
            shutil.move(str(glossary_file), args.output)
        
        logger.info(f"✓ Glossary saved: {args.output}")
        
    except Exception as e:
        logger.error(f"Failed to fetch TMDB data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

### 2. NER Post-Processing (Priority 1)

#### 2.1 Pipeline Integration

**Create `scripts/ner_post_processor.py`:**

```python
#!/usr/bin/env python3
"""
NER Post-Processor
Corrects entity errors in transcripts using glossary
"""

import argparse
import sys
from pathlib import Path
import srt

sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.ner_corrector import NERCorrector
from shared.logger import setup_logger
import yaml

logger = setup_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description='NER-based entity correction')
    parser.add_argument('--input', required=True, help='Input SRT file')
    parser.add_argument('--output', required=True, help='Output SRT file')
    parser.add_argument('--glossary', required=True, help='Glossary YAML file')
    parser.add_argument('--report', help='Corrections report file')
    
    args = parser.parse_args()
    
    # Load glossary
    logger.info(f"Loading glossary: {args.glossary}")
    with open(args.glossary) as f:
        glossary = yaml.safe_load(f)
    
    # Initialize NER corrector
    corrector = NERCorrector()
    corrector.load_glossary(glossary)
    
    # Load subtitles
    logger.info(f"Processing: {args.input}")
    with open(args.input, encoding='utf-8') as f:
        subtitles = list(srt.parse(f.read()))
    
    # Correct each subtitle
    all_corrections = []
    for sub in subtitles:
        corrected_text, corrections = corrector.correct_text(sub.content)
        
        if corrections:
            all_corrections.extend([
                {**c, 'subtitle_index': sub.index, 'timestamp': str(sub.start)}
                for c in corrections
            ])
            sub.content = corrected_text
    
    # Write corrected subtitles
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(srt.compose(subtitles))
    
    logger.info(f"✓ Corrected subtitles saved: {output_path}")
    logger.info(f"  Made {len(all_corrections)} entity corrections")
    
    # Write report
    if args.report and all_corrections:
        with open(args.report, 'w') as f:
            import json
            json.dump(all_corrections, f, indent=2)
        logger.info(f"  Corrections report: {args.report}")

if __name__ == '__main__':
    main()
```

#### 2.2 Pipeline Stage Addition

**Update `run-pipeline.sh`:**

```bash
# Add new stage after transcription
run_ner_correction() {
    local job_dir="$1"
    local stage="ner_correction"
    
    if ! should_run_stage "$job_dir" "$stage"; then
        return 0
    fi
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║  Stage: NER Entity Correction                              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    
    # Check if NER is enabled
    if [[ "$(get_config "$job_dir" "NER_ENABLED")" != "true" ]]; then
        echo "NER correction disabled, skipping..."
        mark_stage_complete "$job_dir" "$stage" "skipped"
        return 0
    fi
    
    # Check if glossary exists
    local glossary_file="$(get_config "$job_dir" "GLOSSARY_FILE")"
    if [[ -z "$glossary_file" ]] || [[ ! -f "$glossary_file" ]]; then
        echo "⚠️  No glossary found, skipping NER correction"
        mark_stage_complete "$job_dir" "$stage" "skipped"
        return 0
    fi
    
    echo "Using glossary: $glossary_file"
    
    # Find source language subtitle file
    local source_lang="$(get_config "$job_dir" "SOURCE_LANGUAGE")"
    local subtitle_dir="$job_dir/subtitles"
    local source_srt="$subtitle_dir/*.${source_lang}.srt"
    
    if [[ ! -f $source_srt ]]; then
        echo "⚠️  Source subtitle not found: $source_srt"
        mark_stage_complete "$job_dir" "$stage" "failed"
        return 1
    fi
    
    # Run NER correction
    local output_srt="${source_srt%.srt}.ner-corrected.srt"
    local report_file="$job_dir/ner_corrections.json"
    
    activate_venv "common"
    python scripts/ner_post_processor.py \
        --input "$source_srt" \
        --output "$output_srt" \
        --glossary "$glossary_file" \
        --report "$report_file"
    
    if [[ $? -eq 0 ]]; then
        echo "✓ NER correction complete"
        # Replace original with corrected version
        mv "$output_srt" "$source_srt"
        mark_stage_complete "$job_dir" "$stage" "success"
    else
        echo "❌ NER correction failed"
        mark_stage_complete "$job_dir" "$stage" "failed"
        return 1
    fi
}

# Add to pipeline execution order
# In main execution flow, after transcription:
run_ner_correction "$JOB_DIR" || handle_error "NER correction failed"
```

---

### 3. Enhanced Hybrid Translation (Priority 2)

**Update `scripts/hybrid_subtitle_merger_v2.py`** to integrate NER:

```python
# In merge_translations() function, add:

# Load glossary if available
glossary = None
if glossary_file and Path(glossary_file).exists():
    with open(glossary_file) as f:
        glossary = yaml.safe_load(f)
    
    # Initialize NER corrector
    ner = NERCorrector()
    ner.load_glossary(glossary)
    
    # Correct entity errors in both translations before merging
    print("Applying NER corrections...")
    for sub in whisperx_subs:
        corrected, _ = ner.correct_text(sub.content)
        sub.content = corrected
    
    for sub in indictrans2_subs:
        corrected, _ = ner.correct_text(sub.content)
        sub.content = corrected
```

---

### 4. Speaker Diarization (Priority 3)

**Add PyAnnote speaker diarization:**

```bash
# In install_pyannote() in bootstrap.sh:
pip install pyannote.audio>=3.0.0
```

**Create `scripts/speaker_diarization.py`:**

```python
#!/usr/bin/env python3
"""
Speaker Diarization
Identifies "who spoke when" using PyAnnote
"""

from pyannote.audio import Pipeline
from pathlib import Path
import json

def diarize_speakers(audio_file: Path, auth_token: str) -> dict:
    """Run speaker diarization"""
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        use_auth_token=auth_token
    )
    
    diarization = pipeline(str(audio_file))
    
    # Convert to JSON-serializable format
    segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        segments.append({
            'speaker': speaker,
            'start': turn.start,
            'end': turn.end
        })
    
    return {'segments': segments}
```

---

### 5. Documentation Refactoring (Priority 4)

#### New Documentation Structure:

```
docs/
├── INDEX.md (updated)
├── QUICKSTART.md (updated)
├── COMPREHENSIVE_IMPROVEMENT_PLAN.md (this file)
│
├── user-guide/
│   ├── workflows.md (updated with TMDB/NER)
│   ├── glossary-management.md (NEW)
│   ├── entity-correction.md (NEW)
│   └── speaker-diarization.md (NEW)
│
├── technical/
│   ├── tmdb-integration.md (NEW)
│   ├── ner-pipeline.md (NEW)
│   ├── glossary-generation.md (NEW)
│   └── speaker-mapping.md (NEW)
│
└── reference/
    ├── tmdb-api.md (NEW)
    ├── configuration-reference.md (updated)
    └── pipeline-stages.md (updated)
```

---

## 📅 Implementation Timeline

### Week 1-2: Foundation (TMDB + NER)
- [ ] Day 1-2: Add dependencies, update bootstrap
- [ ] Day 3-4: Implement TMDB client and caching
- [ ] Day 5-6: Implement NER corrector
- [ ] Day 7-8: Implement glossary generator
- [ ] Day 9-10: Integration testing
- [ ] Day 11-14: Documentation

**Deliverables:**
- ✅ TMDB API integration working
- ✅ Auto-generated glossaries
- ✅ NER post-processing functional
- ✅ prepare-job.sh updated
- ✅ Basic documentation

### Week 3-4: Pipeline Integration
- [ ] Day 15-17: Update run-pipeline.sh
- [ ] Day 18-20: Add NER stage to pipeline
- [ ] Day 21-23: Enhanced hybrid merger
- [ ] Day 24-26: End-to-end testing
- [ ] Day 27-28: Bug fixes

**Deliverables:**
- ✅ NER integrated into pipeline
- ✅ Hybrid v3 with NER support
- ✅ Pipeline runs with optional TMDB/NER
- ✅ Backward compatibility maintained

### Week 5-6: Advanced Features
- [ ] Day 29-32: Speaker diarization
- [ ] Day 33-35: Character mapping
- [ ] Day 36-38: Lyrics database integration
- [ ] Day 39-42: Testing and refinement

**Deliverables:**
- ✅ Speaker diarization working
- ✅ TMDB character mapping
- ✅ Optional lyrics database fetch
- ✅ Advanced features documented

### Week 7-8: Polish & Documentation
- [ ] Day 43-45: Complete documentation
- [ ] Day 46-48: User guide updates
- [ ] Day 49-51: Tutorial videos/examples
- [ ] Day 52-56: Final testing and QA

**Deliverables:**
- ✅ Complete documentation set
- ✅ Updated README and guides
- ✅ Example workflows
- ✅ Release notes

---

## 🧪 Testing Strategy

### Unit Tests
- TMDB API client (with mocked responses)
- NER corrector (with test cases)
- Glossary generator (verify output format)

### Integration Tests
- Full pipeline run with TMDB enabled
- NER correction on sample subtitles
- Hybrid merger with glossary

### Regression Tests
- Existing workflows still work
- Backward compatibility verified
- Performance benchmarks

### Test Cases
1. **"Jaane Tu Ya Jaane Na" (2008)**
   - Character names: Bombs, Jai, Aditi
   - Locations: Cuff Parade, Church Gate
   - Expected: 95%+ entity accuracy

2. **Generic Hindi Movie**
   - No TMDB data available
   - Should fallback gracefully
   - Manual glossary still works

3. **English Content**
   - NER should still work
   - TMDB for Hollywood movies
   - Verify multi-language support

---

## 📊 Success Metrics

### Quality Metrics
- **Character Name Accuracy:** 80% → 95%+ ✓
- **Location Accuracy:** 70% → 90%+ ✓
- **Entity Preservation in Translation:** 60% → 95%+ ✓
- **Overall WER:** ~15% → <12% ✓

### Automation Metrics
- **Glossary Generation Time:** Manual (hours) → Auto (<5 min) ✓
- **Entity Correction:** Manual review → Automatic ✓
- **TMDB Cache Hit Rate:** >80% after initial fetch ✓

### System Metrics
- **Pipeline Runtime:** No significant increase (<10% overhead)
- **Memory Usage:** Within limits (no more than 2GB additional)
- **Compatibility:** 100% backward compatible

---

## 🚨 Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| TMDB API rate limits | Medium | Aggressive caching, fallback to manual |
| NER model accuracy | High | Glossary-based correction, manual review flag |
| Performance degradation | Medium | Optional features, parallel processing |
| Dependency conflicts | Low | Existing multi-venv system handles this |

### Process Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Timeline slip | Medium | Phased rollout, MVP first |
| Breaking changes | High | Extensive testing, feature flags |
| Documentation lag | Medium | Doc-as-you-code, templates ready |

---

## 🔄 Rollout Strategy

### Phase 1: Alpha (Internal Testing)
- Week 1-4 deliverables
- Test on 5-10 movies
- Gather feedback
- Fix critical bugs

### Phase 2: Beta (Limited Release)
- Week 5-6 deliverables
- Release to early adopters
- Document edge cases
- Refine features

### Phase 3: Production
- Week 7-8 deliverables
- Full release
- Monitor metrics
- Iterative improvements

---

## 📝 Configuration Examples

### Minimal Setup (TMDB Only)
```bash
# config/.env.pipeline
TMDB_ENABLED=true
TMDB_API_KEY=your_key_here
NER_ENABLED=false
```

### Full Setup (All Features)
```bash
# config/.env.pipeline
TMDB_ENABLED=true
TMDB_API_KEY=your_key_here
TMDB_AUTO_FETCH=true

NER_ENABLED=true
NER_MODEL=en_core_web_sm
NER_CORRECTION_MODE=post_processing

SPEAKER_DIARIZATION_ENABLED=true
PYANNOTE_AUTH_TOKEN=your_hf_token

LYRICS_DATABASE_ENABLED=true
LYRICS_API_KEY=optional_key
```

### Usage Examples

**Basic with TMDB:**
```bash
./prepare-job.sh \
    --media "Jaane Tu Ya Jaane Na (2008).mp4" \
    --workflow subtitle \
    --source-lang hi \
    --target-langs en \
    --tmdb-year 2008

./run-pipeline.sh -j <job-id>
```

**Advanced with all features:**
```bash
./prepare-job.sh \
    --media "movie.mp4" \
    --workflow subtitle \
    --source-lang hi \
    --target-langs en,gu \
    --tmdb-title "Jaane Tu Ya Jaane Na" \
    --tmdb-year 2008 \
    --enable-ner \
    --enable-speaker-diarization \
    --enable-lyrics-database

./run-pipeline.sh -j <job-id>
```

---

## 🎓 Training & Onboarding

### For Developers
1. Read this comprehensive plan
2. Review TMDB API documentation
3. Understand NER pipeline
4. Run test cases locally
5. Contribute to testing

### For Users
1. Quick Start guide (updated)
2. TMDB setup tutorial
3. Glossary management guide
4. Troubleshooting new features

---

## 🔗 References

1. [TMDB API Documentation](https://developer.themoviedb.org/docs)
2. [spaCy NER Guide](https://spacy.io/usage/linguistic-features#named-entities)
3. [PyAnnote Speaker Diarization](https://github.com/pyannote/pyannote-audio)
4. [Key Features Analysis](../How_Key_Features_Improve_Speech_Transcription_Translation_Accuracy.md)

---

## ✅ Acceptance Criteria

### Phase 1 Complete When:
- [ ] TMDB API integration works
- [ ] Glossaries auto-generated from TMDB
- [ ] NER correction improves entity accuracy
- [ ] prepare-job.sh supports TMDB flags
- [ ] Documentation updated

### Phase 2 Complete When:
- [ ] Pipeline runs with NER stage
- [ ] Hybrid merger uses NER
- [ ] Backward compatibility verified
- [ ] Tests pass

### Phase 3 Complete When:
- [ ] Speaker diarization working
- [ ] Character mapping functional
- [ ] All features documented

### Final Release When:
- [ ] All success metrics met
- [ ] Documentation complete
- [ ] User feedback incorporated
- [ ] Production-ready

---

## 🎯 Next Steps

1. **Review and Approve Plan** (You)
2. **Get TMDB API Key** (5 minutes)
3. **Start Implementation** (Week 1)
4. **Test on Sample Movie** (Week 2)
5. **Iterate Based on Results**

**Ready to start? Let's begin with Phase 1!**

---

*Last Updated: November 24, 2025*  
*Author: AI Assistant*  
*Status: Awaiting Approval*
