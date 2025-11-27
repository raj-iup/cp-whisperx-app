# Phase 1 Development Standards

**CP-WhisperX-App Phase 1: TMDB + NER Integration**  
**Version:** 1.0  
**Date:** November 24, 2025

---

## 📋 Overview

This document extends the [Developer Guide](DEVELOPER_GUIDE.md) with Phase 1-specific standards for TMDB integration and Named Entity Recognition (NER).

**Phase 1 Goals:**
- TMDB metadata fetching and caching
- NER-based entity extraction and correction
- Auto-generated glossaries from TMDB data
- Pipeline integration with backward compatibility

---

## 🎯 Phase 1 Principles

### 1. Backward Compatibility First

**CRITICAL:** All Phase 1 features must be optional and backward compatible.

```python
# ✅ GOOD - Optional with fallback
if config.get('TMDB_ENABLED', 'false').lower() == 'true':
    tmdb_data = fetch_tmdb_metadata(title, year)
    if tmdb_data:
        glossary = generate_glossary(tmdb_data)
    else:
        logger.warning("TMDB fetch failed, using manual glossary")
        glossary = load_manual_glossary()
else:
    logger.info("TMDB disabled, using manual glossary")
    glossary = load_manual_glossary()

# ❌ BAD - Required, breaks existing workflows
tmdb_data = fetch_tmdb_metadata(title, year)  # Fails if TMDB unavailable
```

### 2. Graceful Degradation

**Phase 1 features must never crash the pipeline.**

```python
# ✅ GOOD - Graceful degradation
def fetch_with_fallback(title, year):
    try:
        data = tmdb_api.fetch(title, year)
        return data
    except APIError as e:
        logger.warning(f"TMDB API failed: {e}, continuing without metadata")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}, continuing without metadata")
        return None

# Usage
tmdb_data = fetch_with_fallback(title, year)
if tmdb_data:
    # Use TMDB data
    use_tmdb_glossary(tmdb_data)
else:
    # Fallback to manual
    use_manual_glossary()
```

### 3. Configuration Over Code

**All Phase 1 settings must be in config/.env.pipeline.**

```bash
# ✅ CORRECT - All settings defined
TMDB_ENABLED=true
TMDB_CACHE_ENABLED=true
TMDB_CACHE_EXPIRY_DAYS=90
TMDB_AUTO_GLOSSARY=true

NER_ENABLED=true
NER_MODEL=en_core_web_sm
NER_CONFIDENCE_THRESHOLD=0.7
```

```python
# ✅ CORRECT - Read via Config class
config = Config(PROJECT_ROOT)
tmdb_enabled = config.get('TMDB_ENABLED', 'false').lower() == 'true'
cache_enabled = config.get('TMDB_CACHE_ENABLED', 'true').lower() == 'true'
cache_expiry = int(config.get('TMDB_CACHE_EXPIRY_DAYS', 90))

# ❌ WRONG - Hardcoded values
cache_expiry = 90  # Don't hardcode!
```

---

## 🔧 TMDB Integration Standards

### API Client Pattern

**Use centralized TMDB client with error handling.**

```python
from shared.tmdb_loader import TMDBLoader, TMDBData
from shared.config import Config

class MyPipelineStage:
    def __init__(self, config: Config, logger: PipelineLogger):
        self.config = config
        self.logger = logger
        
        # Initialize TMDB loader
        self.tmdb_loader = TMDBLoader(
            output_base=Path("out"),
            logger=logger
        )
    
    def process(self, title: str, year: int):
        """Process with TMDB metadata"""
        
        # Check if TMDB is enabled
        if not self.config.get('TMDB_ENABLED', 'false').lower() == 'true':
            self.logger.info("TMDB disabled, skipping metadata fetch")
            return None
        
        # Fetch with retry
        tmdb_data = self._fetch_with_retry(title, year)
        
        if tmdb_data and tmdb_data.found:
            self.logger.info(f"✓ TMDB data fetched: {tmdb_data.title}")
            return tmdb_data
        else:
            self.logger.warning("TMDB data not found, continuing without it")
            return None
    
    def _fetch_with_retry(self, title: str, year: int, max_retries: int = 3):
        """Fetch TMDB data with retry logic"""
        for attempt in range(max_retries):
            try:
                data = self.tmdb_loader.load_tmdb_data(
                    title=title,
                    year=year,
                    cache_enabled=True
                )
                return data
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"TMDB fetch attempt {attempt + 1} failed: {e}")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    self.logger.error(f"All TMDB fetch attempts failed: {e}")
                    return TMDBData.empty()
```

### Caching Standards

**Always use caching for TMDB API calls.**

```python
# ✅ GOOD - Cache-aware fetching
def fetch_tmdb_data(title: str, year: int, cache_dir: Path):
    """Fetch TMDB data with caching"""
    
    # Generate cache key
    cache_key = f"{title}_{year}".lower().replace(' ', '_')
    cache_file = cache_dir / f"{cache_key}.json"
    
    # Check cache first
    if cache_file.exists():
        cache_age_days = (time.time() - cache_file.stat().st_mtime) / 86400
        max_age = int(config.get('TMDB_CACHE_EXPIRY_DAYS', 90))
        
        if cache_age_days < max_age:
            logger.info(f"✓ Cache hit: {cache_file.name} ({cache_age_days:.1f} days old)")
            with open(cache_file, 'r') as f:
                return json.load(f)
        else:
            logger.info(f"Cache expired: {cache_file.name} ({cache_age_days:.1f} days old)")
    
    # Fetch from API
    logger.info(f"Fetching from TMDB API: {title} ({year})")
    data = tmdb_api.fetch(title, year)
    
    # Save to cache
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"✓ Cached: {cache_file.name}")
    return data

# ❌ BAD - No caching (wastes API calls)
data = tmdb_api.fetch(title, year)  # Fetches every time!
```

### Logging Standards

**Log all TMDB operations with timing.**

```python
# ✅ GOOD - Comprehensive logging
logger.info("=" * 60)
logger.info("TMDB METADATA FETCH")
logger.info("=" * 60)
logger.info(f"Title: {title}")
logger.info(f"Year: {year}")
logger.info(f"Cache: {'enabled' if cache_enabled else 'disabled'}")

start_time = time.time()
data = fetch_tmdb_data(title, year)
elapsed = time.time() - start_time

if data:
    logger.info(f"✓ Fetched in {elapsed:.2f}s")
    logger.info(f"  TMDB ID: {data.tmdb_id}")
    logger.info(f"  Cast: {len(data.cast)} members")
    logger.info(f"  Crew: {len(data.crew)} members")
    logger.info(f"  Genres: {', '.join(data.genres)}")
else:
    logger.error(f"✗ Fetch failed after {elapsed:.2f}s")

logger.info("=" * 60)
```

---

## 🤖 NER Integration Standards

### Model Loading Pattern

**Load spaCy models once and reuse.**

```python
# ✅ GOOD - Model singleton pattern
class NERProcessor:
    _model_cache = {}
    
    def __init__(self, model_name: str = "en_core_web_sm", logger=None):
        self.model_name = model_name
        self.logger = logger
        self.nlp = self._load_model()
    
    def _load_model(self):
        """Load spaCy model with caching"""
        if self.model_name in self._model_cache:
            self.logger.info(f"✓ Using cached model: {self.model_name}")
            return self._model_cache[self.model_name]
        
        self.logger.info(f"Loading spaCy model: {self.model_name}")
        try:
            import spacy
            nlp = spacy.load(self.model_name)
            self._model_cache[self.model_name] = nlp
            self.logger.info(f"✓ Model loaded: {self.model_name}")
            return nlp
        except OSError:
            self.logger.error(f"Model not found: {self.model_name}")
            self.logger.error("Run: python -m spacy download en_core_web_sm")
            return None

# ❌ BAD - Reload model every time (slow!)
def extract_entities(text):
    import spacy
    nlp = spacy.load("en_core_web_sm")  # Loads every call!
    return nlp(text).ents
```

### Entity Extraction Pattern

**Extract entities with confidence scoring.**

```python
# ✅ GOOD - Entity extraction with metadata
def extract_entities(self, text: str, min_confidence: float = 0.7):
    """
    Extract named entities from text
    
    Args:
        text: Input text
        min_confidence: Minimum confidence threshold
        
    Returns:
        List of entity dicts with metadata
    """
    if not self.nlp:
        self.logger.warning("NER model not loaded, skipping entity extraction")
        return []
    
    doc = self.nlp(text)
    entities = []
    
    for ent in doc.ents:
        # Filter by entity type
        if ent.label_ not in self.entity_types:
            continue
        
        # Calculate confidence (simplified)
        confidence = 1.0  # spaCy doesn't provide confidence directly
        
        if confidence >= min_confidence:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': confidence
            })
    
    self.logger.debug(f"Extracted {len(entities)} entities from {len(text)} chars")
    return entities
```

### Entity Correction Pattern

**Correct entities using glossary matching.**

```python
# ✅ GOOD - Entity correction with fuzzy matching
def correct_entity(self, entity_text: str, glossary: Dict, threshold: float = 0.8):
    """
    Correct entity using glossary
    
    Args:
        entity_text: Entity text to correct
        glossary: Glossary dict with correct names
        threshold: Fuzzy matching threshold
        
    Returns:
        Corrected text or original if no match
    """
    from difflib import SequenceMatcher
    
    # Exact match first
    if entity_text in glossary:
        self.logger.debug(f"Exact match: '{entity_text}' → '{glossary[entity_text]}'")
        return glossary[entity_text]
    
    # Fuzzy match
    best_match = None
    best_score = 0.0
    
    for glossary_term in glossary.keys():
        score = SequenceMatcher(None, entity_text.lower(), glossary_term.lower()).ratio()
        if score > best_score and score >= threshold:
            best_score = score
            best_match = glossary[glossary_term]
    
    if best_match:
        self.logger.debug(f"Fuzzy match ({best_score:.2f}): '{entity_text}' → '{best_match}'")
        return best_match
    
    self.logger.debug(f"No match found for: '{entity_text}'")
    return entity_text

# Example usage
corrected = ner.correct_entity("moms", {"Bombs": "Bombs"})  # Returns "Bombs"
corrected = ner.correct_entity("Cup pyrites", {"Cuff Parade": "Cuff Parade"})  # Returns "Cuff Parade"
```

---

## 📝 Glossary Generation Standards

### TMDB-to-Glossary Pattern

**Generate glossaries from TMDB metadata.**

```python
# ✅ GOOD - Complete glossary generation
def generate_glossary(tmdb_data: TMDBData) -> Dict[str, Any]:
    """
    Generate glossary from TMDB metadata
    
    Args:
        tmdb_data: TMDB metadata
        
    Returns:
        Glossary dict
    """
    glossary = {
        'movie': tmdb_data.title,
        'year': tmdb_data.year,
        'tmdb_id': tmdb_data.tmdb_id,
        'characters': [],
        'locations': [],
        'generated_at': datetime.now().isoformat()
    }
    
    # Extract character names
    for cast in tmdb_data.cast[:10]:  # Top 10 characters
        character = cast.get('character', '')
        if not character:
            continue
        
        # Generate aliases
        aliases = []
        if ' ' in character:
            # Add first name as alias
            first_name = character.split()[0]
            aliases.append(first_name)
        
        # Add common errors (if known)
        common_errors = generate_common_errors(character)
        
        glossary['characters'].append({
            'name': character,
            'actor': cast['name'],
            'aliases': aliases,
            'common_errors': common_errors
        })
    
    logger.info(f"✓ Generated glossary with {len(glossary['characters'])} characters")
    return glossary

def generate_common_errors(name: str) -> List[str]:
    """Generate common ASR errors for a name"""
    errors = []
    
    # Phonetic errors
    # Example: "Bombs" → "moms", "bonds"
    # This would use phonetic matching library
    
    # For Phase 1, return empty (can enhance in Phase 2)
    return errors
```

### Glossary Format Standards

**Use YAML for glossaries (human-readable).**

```yaml
# ✅ GOOD - Well-structured glossary
movie: Jaane Tu... Ya Jaane Na
year: 2008
tmdb_id: 12345
imdb_id: tt1093370

characters:
  - name: Jai Singh Rathore
    actor: Imran Khan
    aliases:
      - Jai
      - Rathore
    common_errors:
      - Jay
      - Rai
      
  - name: Aditi Mahant
    actor: Genelia D'Souza
    aliases:
      - Aditi
    common_errors:
      - Aarti
      
  - name: Bombs
    actor: Arbaaz Khan
    common_errors:
      - moms
      - bonds

locations:
  - name: Cuff Parade
    common_errors:
      - Cup pyrites
      - Cup Parade

generated_at: 2025-11-24T10:30:00Z
```

---

## 🧪 Testing Standards

### Unit Test Pattern

**Test TMDB and NER modules independently.**

```python
# ✅ GOOD - Comprehensive unit tests
import unittest
from unittest.mock import Mock, patch
from shared.tmdb_loader import TMDBLoader, TMDBData

class TestTMDBLoader(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.loader = TMDBLoader(Path("test_out"), self.logger)
    
    @patch('shared.tmdb_loader.TMDb')
    def test_fetch_movie_success(self, mock_tmdb):
        """Test successful movie fetch"""
        # Setup mock
        mock_tmdb.return_value.search.return_value = [
            Mock(id=12345, title="Test Movie", release_date="2008-01-01")
        ]
        
        # Test
        data = self.loader.load_tmdb_data("Test Movie", 2008)
        
        # Assert
        self.assertIsNotNone(data)
        self.assertEqual(data.title, "Test Movie")
        self.assertEqual(data.year, 2008)
    
    def test_fetch_movie_not_found(self):
        """Test movie not found"""
        data = self.loader.load_tmdb_data("NonExistent Movie", 1900)
        self.assertFalse(data.found)
    
    def test_cache_functionality(self):
        """Test caching works"""
        # First fetch
        data1 = self.loader.load_tmdb_data("Test Movie", 2008, cache_enabled=True)
        
        # Second fetch (should use cache)
        data2 = self.loader.load_tmdb_data("Test Movie", 2008, cache_enabled=True)
        
        # Assert cache was used
        self.assertEqual(data1.tmdb_id, data2.tmdb_id)
```

### Integration Test Pattern

**Test end-to-end Phase 1 workflow.**

```bash
#!/usr/bin/env bash
# test_phase1_integration.sh

set -euo pipefail

echo "========================================="
echo "Phase 1 Integration Test"
echo "========================================="

# Test 1: TMDB fetch
echo ""
echo "Test 1: TMDB Metadata Fetch"
python scripts/fetch_tmdb_metadata.py \
    --title "Jaane Tu Ya Jaane Na" \
    --year 2008 \
    --output test_output/glossary.yaml

if [ -f "test_output/glossary.yaml" ]; then
    echo "✓ Glossary generated successfully"
else
    echo "✗ Glossary generation failed"
    exit 1
fi

# Test 2: NER extraction
echo ""
echo "Test 2: NER Entity Extraction"
echo "I saw moms at Cup pyrites" | \
python scripts/test_ner_correction.py \
    --glossary test_output/glossary.yaml

# Test 3: Pipeline integration
echo ""
echo "Test 3: Pipeline Integration"
./prepare-job.sh \
    --media "in/test_clip.mp4" \
    --workflow transcribe \
    --source-lang hi \
    --tmdb-title "Jaane Tu Ya Jaane Na" \
    --tmdb-year 2008

echo ""
echo "========================================="
echo "✓ All Phase 1 tests passed"
echo "========================================="
```

---

## 📊 Performance Standards

### Response Time Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| TMDB API call | < 2s | With retry |
| TMDB cache hit | < 100ms | Local file read |
| NER entity extraction | < 1s / 1000 words | spaCy processing |
| Glossary generation | < 500ms | From TMDB data |
| Entity correction | < 100ms / entity | Fuzzy matching |

### Memory Standards

**Phase 1 modules should be lightweight.**

```python
# ✅ GOOD - Process in batches
def process_large_text(text: str, batch_size: int = 10000):
    """Process large text in batches to avoid memory issues"""
    results = []
    for i in range(0, len(text), batch_size):
        batch = text[i:i + batch_size]
        batch_results = ner.extract_entities(batch)
        results.extend(batch_results)
    return results

# ❌ BAD - Load everything in memory
def process_large_text(text: str):
    return ner.extract_entities(text)  # May OOM on large texts
```

---

## 📖 Documentation Standards

### Code Documentation

**All Phase 1 modules must have docstrings.**

```python
# ✅ GOOD - Complete documentation
def fetch_tmdb_metadata(
    title: str,
    year: Optional[int] = None,
    cache_enabled: bool = True,
    logger: Optional[PipelineLogger] = None
) -> Optional[TMDBData]:
    """
    Fetch movie metadata from TMDB API with caching
    
    This function queries the TMDB API for movie information including
    cast, crew, genres, and synopsis. Results are cached locally to
    minimize API calls and support offline testing.
    
    Args:
        title: Movie title (e.g., "Jaane Tu Ya Jaane Na")
        year: Release year for better matching (optional)
        cache_enabled: Whether to use local cache (default: True)
        logger: Logger instance (creates default if None)
    
    Returns:
        TMDBData object with movie information, or None if not found
    
    Raises:
        APIError: If TMDB API is unreachable after retries
        ValueError: If title is empty or invalid
    
    Example:
        >>> data = fetch_tmdb_metadata("3 Idiots", 2009)
        >>> print(f"Found: {data.title} with {len(data.cast)} cast members")
        Found: 3 Idiots with 20 cast members
    
    Note:
        Requires TMDB API key in config/secrets.json
        Cache expires after 90 days (configurable)
    """
    # Implementation...
```

### User Documentation

**Create user guides for Phase 1 features.**

Structure:
```
docs/user-guide/features/
├── tmdb-integration.md      # TMDB setup and usage
├── ner-correction.md        # NER entity correction
└── auto-glossary.md         # Auto-glossary generation
```

---

## ✅ Phase 1 Checklist

Before marking Phase 1 complete:

### Code Quality
- [ ] All modules follow standards above
- [ ] Logging is comprehensive and consistent
- [ ] Configuration uses Config class
- [ ] No hardcoded values
- [ ] Error handling is robust
- [ ] Backward compatibility maintained

### Functionality
- [ ] TMDB API integration works
- [ ] Caching reduces API calls
- [ ] NER extracts entities correctly
- [ ] Glossary generation works
- [ ] Entity correction improves accuracy

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing successful
- [ ] Performance targets met
- [ ] Memory usage acceptable

### Documentation
- [ ] Code documented with docstrings
- [ ] User guides created
- [ ] Technical docs updated
- [ ] Examples tested
- [ ] README updated

---

## 🚀 Next Steps

After Phase 1 completion:
1. **Phase 2:** Pipeline integration
2. **Phase 3:** Advanced features (speaker diarization, lyrics DB)
3. **Phase 4:** Documentation and release

---

**Phase 1 Development Standards - Version 1.0**
