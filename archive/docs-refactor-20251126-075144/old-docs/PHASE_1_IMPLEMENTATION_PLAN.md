# Phase 1 Implementation Plan

**Date:** November 24, 2025  
**Status:** Ready to Implement  
**Timeline:** Weeks 1-2

---

## 📋 Current Status Assessment

### ✅ Already in Place

1. **TMDB API Key**: Available in `config/secrets.json`
2. **Existing Infrastructure**:
   - `shared/tmdb_loader.py` - TMDB data loader
   - `shared/tmdb_cache.py` - TMDB caching
   - `scripts/tmdb.py` - TMDB script
   - `scripts/tmdb_enrichment.py` - TMDB enrichment
   - `scripts/ner_extraction.py` - NER processor
   - `scripts/glossary_builder.py` - Glossary builder
   - `shared/glossary*.py` - Multiple glossary utilities
3. **Configuration**: TMDB/NER stages defined in `config/.env.pipeline`

### ⚠️ Gaps Identified

1. **Dependencies**: NER/TMDB packages not in `requirements-common.txt`
2. **Bootstrap Integration**: Dependencies not installed during bootstrap
3. **CLI Tool Missing**: No `scripts/fetch_tmdb_metadata.py` for manual testing
4. **Documentation**: Development standards need Phase 1-specific guidelines
5. **Integration**: Scripts exist but may need updates for pipeline integration
6. **Testing**: No test suite for Phase 1 components

---

## 🎯 Phase 1 Objectives

### Week 1: Dependencies & Core Modules

**Deliverables:**
1. ✅ Add dependencies to `requirements-common.txt`
2. ✅ Update `bootstrap.sh` to install NER/TMDB packages
3. ✅ Create `scripts/fetch_tmdb_metadata.py` CLI tool
4. ✅ Review and update `shared/tmdb_client.py` (or use existing tmdb_loader.py)
5. ✅ Review and update `shared/ner_corrector.py`
6. ✅ Review and update `shared/glossary_generator.py`
7. ✅ Update development standards documentation

### Week 2: Integration & Testing

**Deliverables:**
1. ✅ Update `prepare-job.sh` for TMDB integration
2. ✅ Create/update `scripts/ner_post_processor.py`
3. ✅ Integration testing with sample media
4. ✅ Documentation updates
5. ✅ Add logging standards compliance

---

## 📦 Dependencies to Add

### Python Packages (requirements-common.txt)

```txt
# TMDB Integration (Phase 1)
tmdbv3api>=1.9.0

# Named Entity Recognition (Phase 1)
spacy>=3.7.0
en-core-web-sm @ https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0-py3-none-any.whl

# Caching & Utilities
cachetools>=5.3.0
```

### Bootstrap Integration

Update `bootstrap.sh` to include:

```bash
# Install spaCy language model
echo "📥 Downloading spaCy English model..."
python -m spacy download en_core_web_sm

# Verify TMDB API key
if ! grep -q "tmdb_api_key" config/secrets.json; then
    echo "⚠️  WARNING: TMDB API key not found in config/secrets.json"
    echo "   Get your free key at: https://www.themoviedb.org/signup"
fi
```

---

## 🔧 Core Modules to Implement/Review

### 1. `shared/tmdb_client.py`

**Status:** Use existing `shared/tmdb_loader.py` or enhance

**Key Features:**
- API client wrapper
- Rate limiting
- Error handling
- Cache integration
- Retry logic

**Example Interface:**
```python
from shared.tmdb_loader import TMDBLoader, TMDBData

loader = TMDBLoader(output_base=Path("out"), logger=logger)
data = loader.load_tmdb_data(
    title="Jaane Tu Ya Jaane Na",
    year=2008,
    cache_enabled=True
)
```

### 2. `shared/ner_corrector.py`

**Status:** Use/enhance existing `scripts/ner_extraction.py`

**Key Features:**
- Load spaCy models
- Extract entities from text
- Match against glossary
- Correct common errors
- Entity frequency analysis

**Example Interface:**
```python
from shared.ner_corrector import NERCorrector

corrector = NERCorrector(
    model_name="en_core_web_sm",
    glossary_data=tmdb_data,
    logger=logger
)

corrected = corrector.correct_text(
    text="I saw moms at Cup pyrites",
    confidence_threshold=0.7
)
# Returns: "I saw Bombs at Cuff Parade"
```

### 3. `shared/glossary_generator.py`

**Status:** Use existing `scripts/glossary_builder.py` or create new

**Key Features:**
- Generate glossary from TMDB data
- Extract character names with aliases
- Extract location names
- Include common errors
- Export to YAML format

**Example Interface:**
```python
from shared.glossary_generator import GlossaryGenerator

generator = GlossaryGenerator(logger=logger)
glossary = generator.from_tmdb_data(
    tmdb_data=data,
    include_aliases=True,
    include_common_errors=True
)
generator.save_yaml(glossary, output_path)
```

---

## 🛠️ Scripts to Create/Update

### 1. `scripts/fetch_tmdb_metadata.py`

**Purpose:** CLI tool for testing TMDB integration

**Usage:**
```bash
python scripts/fetch_tmdb_metadata.py \
    --title "Jaane Tu Ya Jaane Na" \
    --year 2008 \
    --output test_glossary.yaml \
    --cache-dir cache/tmdb
```

**Features:**
- Command-line interface
- JSON/YAML output
- Cache support
- Error reporting
- Verbose mode

### 2. `scripts/ner_post_processor.py`

**Purpose:** Pipeline stage for NER correction

**Usage:**
```bash
python scripts/ner_post_processor.py \
    --input transcripts/segments.json \
    --glossary glossary.yaml \
    --output transcripts/segments_corrected.json
```

**Features:**
- Read ASR output
- Apply NER correction
- Use TMDB glossary
- Generate correction report
- Log all changes

---

## 🔄 Pipeline Integration Points

### 1. Bootstrap (`bootstrap.sh`)

**Changes:**
- Add TMDB/NER packages to common venv
- Download spaCy model
- Verify TMDB API key

### 2. Prepare Job (`prepare-job.sh`)

**Changes:**
- Add `--tmdb-title` and `--tmdb-year` options
- Fetch TMDB metadata if enabled
- Generate glossary from TMDB
- Save to job directory

### 3. Run Pipeline (`run-pipeline.sh`)

**Changes:**
- Add optional NER correction stage
- Use TMDB glossary during ASR
- Apply entity correction post-ASR
- Generate NER report

---

## 📝 Configuration Updates

### config/.env.pipeline

**Ensure these sections are complete:**

```bash
# ============================================================
# [PHASE 1] TMDB INTEGRATION SETTINGS
# ============================================================
TMDB_ENABLED=true
TMDB_API_KEY_SOURCE=secrets.json  # Read from secrets
TMDB_CACHE_ENABLED=true
TMDB_CACHE_DIR=cache/tmdb
TMDB_CACHE_EXPIRY_DAYS=90
TMDB_LANGUAGE=en-US
TMDB_AUTO_GLOSSARY=true  # Auto-generate glossary

# ============================================================
# [PHASE 1] NER SETTINGS
# ============================================================
NER_ENABLED=true
NER_MODEL=en_core_web_sm  # spaCy model
NER_DEVICE=cpu
NER_CONFIDENCE_THRESHOLD=0.7
NER_ENTITY_TYPES=PERSON,ORG,GPE,LOC,FAC
NER_CORRECTION_ENABLED=true
NER_TMDB_MATCHING=true

# ============================================================
# [PHASE 1] GLOSSARY AUTO-GENERATION
# ============================================================
GLOSSARY_AUTO_GENERATE=true
GLOSSARY_SOURCE=tmdb  # tmdb, manual, or both
GLOSSARY_INCLUDE_ALIASES=true
GLOSSARY_INCLUDE_COMMON_ERRORS=true
GLOSSARY_OUTPUT_FORMAT=yaml
```

---

## 🧪 Testing Strategy

### Unit Tests

**Test Files:**
- `tests/test_tmdb_client.py`
- `tests/test_ner_corrector.py`
- `tests/test_glossary_generator.py`

**Test Cases:**
- TMDB API connectivity
- Cache functionality
- NER entity extraction
- Glossary generation
- Error handling

### Integration Tests

**Test Scenario 1: TMDB Fetch**
```bash
# Test TMDB metadata fetch
python scripts/fetch_tmdb_metadata.py \
    --title "Jaane Tu Ya Jaane Na" \
    --year 2008 \
    --output test_output/glossary.yaml
```

**Expected Output:**
- metadata.json with cast/crew
- glossary.yaml with character names
- Cache file created

**Test Scenario 2: NER Correction**
```bash
# Test NER correction on sample text
echo "I saw moms at the Cup pyrites" | \
python scripts/ner_post_processor.py \
    --glossary test_output/glossary.yaml
```

**Expected Output:**
- Corrected text: "I saw Bombs at the Cuff Parade"
- Correction report

**Test Scenario 3: End-to-End Pipeline**
```bash
# Test full pipeline with Phase 1 features
./prepare-job.sh \
    --media "in/jaane-tu-clip.mp4" \
    --workflow subtitle \
    --source-lang hi \
    --target-langs en \
    --tmdb-title "Jaane Tu Ya Jaane Na" \
    --tmdb-year 2008

./run-pipeline.sh -j <job-id>
```

**Expected Outputs:**
- TMDB metadata fetched
- Glossary auto-generated
- NER corrections applied
- Improved character name accuracy

---

## 📊 Success Metrics

### Quantitative Metrics

1. **Character Name Accuracy:** Current 80% → Target 90%+
2. **Entity Preservation:** Current 60% → Target 85%+
3. **Manual Glossary Time:** Current 2-3 hours → Target <5 minutes
4. **API Response Time:** <1 second (with cache)
5. **Pipeline Overhead:** <10% additional time

### Qualitative Metrics

1. ✅ TMDB glossary auto-generated successfully
2. ✅ NER corrects "moms" → "Bombs"
3. ✅ NER corrects "Cup pyrites" → "Cuff Parade"
4. ✅ Backward compatible (old jobs still work)
5. ✅ Logging is clear and informative

---

## 📖 Documentation Updates Required

### 1. Developer Guide Enhancement

**File:** `docs/DEVELOPER_GUIDE.md`

**Add Sections:**
- Phase 1 implementation guidelines
- TMDB integration patterns
- NER correction patterns
- Glossary generation workflow

### 2. User Guide Updates

**Files to Create/Update:**
- `docs/user-guide/features/tmdb-integration.md`
- `docs/user-guide/features/ner-correction.md`
- `docs/user-guide/features/auto-glossary.md`

### 3. Technical Documentation

**Files to Create/Update:**
- `docs/technical/tmdb-api-integration.md`
- `docs/technical/ner-pipeline.md`
- `docs/technical/phase-1-architecture.md`

---

## 🚨 Development Standards for Phase 1

### Logging Requirements

**All Phase 1 modules must:**
1. Use `PipelineLogger` with module name
2. Log configuration at start
3. Log TMDB API calls
4. Log NER corrections
5. Log cache hits/misses
6. Include timing information

**Example:**
```python
logger.info("=" * 60)
logger.info("TMDB METADATA FETCH")
logger.info("=" * 60)
logger.info(f"Title: {title}")
logger.info(f"Year: {year}")
logger.info(f"Cache: {'enabled' if cache_enabled else 'disabled'}")

start_time = time.time()
data = fetch_tmdb_data(title, year)
elapsed = time.time() - start_time

logger.info(f"✓ Fetched in {elapsed:.2f}s")
logger.info(f"  Cast: {len(data.cast)} members")
logger.info(f"  Crew: {len(data.crew)} members")
```

### Configuration Standards

**All Phase 1 parameters must:**
1. Be defined in `config/.env.pipeline`
2. Have sensible defaults
3. Be read via `Config` class (not `os.environ`)
4. Be validated before use
5. Be logged at module start

### Error Handling Standards

**All Phase 1 modules must:**
1. Handle API failures gracefully
2. Provide fallback behavior
3. Never crash the pipeline
4. Log errors with context
5. Include retry logic for transient errors

**Example:**
```python
def fetch_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except APIError as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.error(f"All retries failed: {e}")
                return None
```

### Multi-Environment Compliance

**Phase 1 code must:**
1. Work with existing `venv/common` environment
2. Not introduce dependency conflicts
3. Use `EnvironmentManager` for any new environments
4. Test on macOS, Linux, and Windows (WSL/PowerShell)

---

## 🔄 Implementation Workflow

### Day 1-2: Setup & Dependencies
- [ ] Add dependencies to `requirements-common.txt`
- [ ] Update `bootstrap.sh`
- [ ] Test bootstrap on clean environment
- [ ] Verify spaCy model download

### Day 3-5: Core Modules
- [ ] Review/update `shared/tmdb_loader.py`
- [ ] Create `shared/ner_corrector.py` (or adapt ner_extraction.py)
- [ ] Create `shared/glossary_generator.py` (or adapt glossary_builder.py)
- [ ] Unit tests for each module

### Day 6-7: CLI Tool
- [ ] Create `scripts/fetch_tmdb_metadata.py`
- [ ] Test TMDB fetch on sample movies
- [ ] Test glossary generation
- [ ] Document usage

### Day 8-9: Pipeline Integration
- [ ] Update `prepare-job.sh` for TMDB
- [ ] Create/update `scripts/ner_post_processor.py`
- [ ] Test pipeline with Phase 1 features
- [ ] Verify backward compatibility

### Day 10-12: Testing & Documentation
- [ ] End-to-end testing
- [ ] Performance testing
- [ ] Update all documentation
- [ ] Create user guide examples

### Day 13-14: Review & Polish
- [ ] Code review
- [ ] Documentation review
- [ ] Final testing
- [ ] Prepare for Phase 2

---

## 📋 Checklist Before Moving to Phase 2

### Code Quality
- [ ] All modules follow development standards
- [ ] Logging is consistent and informative
- [ ] Configuration uses Config class
- [ ] No hardcoded values
- [ ] Error handling is robust

### Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Tested on sample media
- [ ] Backward compatibility verified
- [ ] Performance acceptable (<10% overhead)

### Documentation
- [ ] Developer guide updated
- [ ] User guides created
- [ ] Technical docs complete
- [ ] Examples tested
- [ ] INDEX.md updated

### Integration
- [ ] Bootstrap installs dependencies
- [ ] prepare-job.sh works with TMDB
- [ ] run-pipeline.sh includes NER stage
- [ ] Old jobs still work
- [ ] Configuration is clear

---

## 🎯 Next Steps

1. **Review this plan** with team/stakeholders
2. **Verify TMDB API key** is working
3. **Start with dependencies** (Day 1-2)
4. **Follow daily workflow** systematically
5. **Test frequently** during implementation
6. **Document immediately** after each module
7. **Commit regularly** with clear messages

---

**Ready to begin Phase 1 implementation! 🚀**
