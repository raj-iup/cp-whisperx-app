# Glossary System Integration Guide

**Version:** 1.0  
**Date:** 2025-11-28  
**Status:** Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Integration Points](#integration-points)
4. [Stage-by-Stage Integration](#stage-by-stage-integration)
5. [Data Flow](#data-flow)
6. [API Reference](#api-reference)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

---

## Overview

The glossary system provides end-to-end management of terminology for Hinglish subtitle generation. It spans from glossary generation (stage 3) through application in downstream stages (stage 11+).

### Purpose

- **Preserve Hinglish Terms:** Maintain culturally-relevant terms in subtitles
- **Enforce Character Names:** Consistent spelling of character/actor names
- **Cultural Context:** Preserve idioms, slang, and regional expressions
- **Film-Specific Terms:** Include cast, crew, and movie-specific terminology

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                  Glossary System                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Sources                                             │
│     • Master Glossary (hinglish_master.tsv)            │
│     • TMDB Data (cast/crew)                            │
│     • Film-Specific Overrides                          │
│                                                         │
│  2. Generation (Stage 3: glossary_load)                │
│     • UnifiedGlossaryManager                           │
│     • GlossaryCache (TMDB caching)                     │
│     • Priority cascade resolution                      │
│                                                         │
│  3. Application (Stage 11+)                            │
│     • glossary_integration helper                      │
│     • subtitle_gen, translation, etc.                  │
│     • Term enforcement in output                       │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture

### High-Level Architecture

```
┌──────────────────────┐
│   Input Sources      │
├──────────────────────┤
│ • Master Glossary    │
│ • TMDB Enrichment    │
│ • Film Overrides     │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Stage 3: Glossary Load         │
│  (scripts/glossary_builder.py)  │
├─────────────────────────────────┤
│  UnifiedGlossaryManager         │
│  • Load all sources             │
│  • Apply priority cascade       │
│  • Generate film_glossary.tsv   │
│  • Cache TMDB data              │
└─────────────┬───────────────────┘
              │
              ▼
      ┌──────────────┐
      │ Outputs      │
      ├──────────────┤
      │ • film_glossary.tsv (13 cols)
      │ • glossary_snapshot.json
      │ • manifest.json
      └──────┬───────┘
             │
             ▼
┌────────────────────────────────┐
│  Downstream Stages             │
├────────────────────────────────┤
│  • Stage 11: subtitle_gen      │
│  • Stage 8: post_ner (future)  │
│  • Translation (future)        │
│                                │
│  Use: glossary_integration.py  │
│  • load_glossary_for_stage()   │
│  • apply_glossary_to_text()    │
└────────────────────────────────┘
```

### Component Details

#### 1. UnifiedGlossaryManager (Canonical)

**File:** `shared/glossary_manager.py`

**Purpose:** Central glossary management with priority cascade

**Features:**
- Load from multiple sources
- TMDB caching with TTL
- Priority cascade: Film > TMDB > Master > Learned
- Multiple strategies: cascade, frequency, context, ML
- Statistics and snapshot generation

#### 2. Glossary Integration Helper

**File:** `shared/glossary_integration.py`

**Purpose:** Easy integration for downstream stages

**Features:**
- Intelligent glossary loading
- Safe text application
- Error handling
- Backwards compatibility

#### 3. Helper Classes

| Class | File | Purpose |
|-------|------|---------|
| GlossaryCache | `glossary_cache.py` | TMDB caching with TTL |
| GlossaryGenerator | `glossary_generator.py` | Term extraction |
| ContextAnalyzer | `glossary_advanced.py` | Context-aware selection |
| MLTermSelector | `glossary_ml.py` | ML-based selection (Phase 3) |

---

## Integration Points

### 1. Glossary Generation (Stage 3)

**Stage:** glossary_load  
**Script:** `scripts/glossary_builder.py`  
**Purpose:** Generate film-specific glossary

**Inputs:**
- `glossary/hinglish_master.tsv` - Master Hinglish terms
- `02_tmdb/enrichment.json` - TMDB cast/crew data
- `glossary/film_overrides/<title>.tsv` - Film-specific overrides (optional)

**Outputs:**
- `03_glossary_load/film_glossary.tsv` - Complete film glossary (13 columns)
- `03_glossary_load/glossary_snapshot.json` - Snapshot for debugging
- `03_glossary_load/manifest.json` - Execution metadata

**Configuration:**
```bash
# .env.pipeline
GLOSSARY_ENABLE=true
GLOSSARY_CACHE_ENABLE=true
GLOSSARY_CACHE_TTL_DAYS=30
GLOSSARY_MIN_CONFIDENCE=0.6
```

### 2. Glossary Application (Stage 11+)

**Stage:** subtitle_generation  
**Script:** `scripts/subtitle_gen.py`  
**Purpose:** Apply glossary to subtitle text

**Inputs:**
- `06_asr/transcript.json` - ASR transcript
- `03_glossary_load/film_glossary.tsv` - Film glossary (optional)
- `glossary/hinglish_master.tsv` - Master glossary (fallback)

**Outputs:**
- `11_subtitle_generation/subtitles.srt` - Subtitles with enforced terms

**Integration Code:**
```python
from shared.glossary_integration import load_glossary_for_stage

glossary = load_glossary_for_stage(
    stage_io=stage_io,
    config=config,
    logger=logger
)

if glossary:
    text = glossary.apply_to_text(text)
```

---

## Stage-by-Stage Integration

### Stage 3: Glossary Load

**Purpose:** Generate comprehensive film glossary

**Integration Steps:**

1. **Enable Stage:**
   ```bash
   # In .env.pipeline
   GLOSSARY_ENABLE=true
   ```

2. **Configure:**
   ```bash
   GLOSSARY_CACHE_ENABLE=true
   GLOSSARY_CACHE_TTL_DAYS=30
   GLOSSARY_MIN_CONFIDENCE=0.6
   ```

3. **Run Stage:**
   ```bash
   ./run-pipeline.sh --job <job-id> --stages glossary_load
   ```

4. **Verify Output:**
   ```bash
   ls out/<job-id>/03_glossary_load/
   # Should see: film_glossary.tsv, glossary_snapshot.json, manifest.json
   ```

### Stage 11: Subtitle Generation

**Purpose:** Apply glossary to subtitle text

**Integration Steps:**

1. **Verify Stage 3 Ran:**
   ```bash
   ls out/<job-id>/03_glossary_load/film_glossary.tsv
   ```

2. **Run Stage:**
   ```bash
   ./run-pipeline.sh --job <job-id> --stages subtitle_generation
   ```

3. **Check Logs:**
   ```bash
   tail -f logs/<job-id>/11_subtitle_generation.log
   # Look for: "✓ Loaded film-specific glossary: N terms"
   ```

4. **Verify Terms Applied:**
   ```bash
   grep "yaar\|bhai\|dost" out/<job-id>/11_subtitle_generation/subtitles.srt
   # Should preserve Hinglish terms
   ```

### Future Stages

#### Stage 8: Post-NER (Planned)

**Purpose:** Validate entities against glossary

**Integration Pattern:**
```python
from shared.glossary_integration import load_glossary_for_stage

glossary = load_glossary_for_stage(stage_io, config, logger)

if glossary:
    # Validate entity names
    for entity in entities:
        canonical_name = glossary.get_term(entity.text)
        if canonical_name:
            entity.text = canonical_name
```

#### Translation Stage (Planned)

**Purpose:** Pre/post translation glossary hints

**Integration Pattern:**
```python
from shared.glossary_integration import load_glossary_for_stage

glossary = load_glossary_for_stage(stage_io, config, logger)

# Pre-translation: Get bias terms
if glossary:
    bias_terms = glossary.get_bias_terms(max_terms=100)
    # Use in translation model

# Post-translation: Enforce terms
translated_text = translate(source_text)
if glossary:
    translated_text = glossary.apply_to_text(translated_text)
```

---

## Data Flow

### Complete Pipeline Data Flow

```
┌─────────────────────┐
│ Stage 1: Prepare    │
│ • Extract metadata  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 2: TMDB       │
│ • Fetch cast/crew   │
│ Output:             │
│   enrichment.json   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│ Stage 3: Glossary Load          │
│ • Load master glossary          │
│ • Extract TMDB names            │
│ • Apply priority cascade        │
│ Output:                         │
│   film_glossary.tsv (245 terms) │
│   - Master: 82                  │
│   - TMDB: 38                    │
│   - Film: 125                   │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 4-5: Audio    │
│ • Extract audio     │
│ • Detect lyrics     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 6: ASR        │
│ • Transcribe audio  │
│ Output:             │
│   transcript.json   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Stage 7-10: NER     │
│ • Entity extraction │
│ • Scene detection   │
└──────────┬──────────┘
           │
           ▼
┌──────────────────────────────────┐
│ Stage 11: Subtitle Gen           │
│ • Load transcript                │
│ • Load film_glossary.tsv ⭐      │
│ • Apply glossary to dialogue     │
│ Output:                          │
│   subtitles.srt (with terms)    │
└──────────────────────────────────┘
```

### Data Format Details

#### film_glossary.tsv (13 columns)

```
source  preferred_english  notes  context  term  script  romanization  hindi  type  english_options  frequency  confidence  priority
```

**Example:**
```tsv
yaar    friend    casual_term    dialogue    यार    Devanagari    yaar    यार    idiom    friend,buddy,dude    high    0.95    1
Rancho  Rancho    character_name dialogue    रांचो Devanagari    Rancho  रांचो person   Rancho    high    1.0     1
```

#### glossary_snapshot.json

```json
{
  "metadata": {
    "film_title": "3 Idiots",
    "film_year": 2009,
    "generated_at": "2025-11-28T10:30:00Z",
    "total_terms": 245
  },
  "sources": {
    "master": 82,
    "tmdb": 38,
    "film_specific": 125
  },
  "terms": {
    "yaar": {
      "preferred_english": "friend",
      "type": "idiom",
      "confidence": 0.95,
      "source": "master"
    }
  }
}
```

---

## API Reference

### UnifiedGlossaryManager

**Constructor:**
```python
from shared.glossary_manager import UnifiedGlossaryManager

manager = UnifiedGlossaryManager(
    project_root=Path("/path/to/project"),
    film_title="3 Idiots",
    film_year=2009,
    tmdb_enrichment_path=Path("02_tmdb/enrichment.json"),
    enable_cache=True,
    enable_learning=False,
    strategy='cascade',
    logger=logger
)
```

**Methods:**

```python
# Load all glossary sources
stats = manager.load_all_sources()
# Returns: {'total_terms': 245, 'master_terms': 82, ...}

# Get term translation
translation = manager.get_term("yaar", context="casual")
# Returns: "friend"

# Apply to text
text = "Hey yaar, how are you?"
result = manager.apply_to_text(text, context="casual")
# Returns: "Hey friend, how are you?"

# Get bias terms for ASR
bias_terms = manager.get_bias_terms(max_terms=100)
# Returns: ["Rancho", "Farhan", "Raju", ...]

# Save snapshot
manager.save_snapshot(Path("glossary_snapshot.json"))

# Get statistics
stats = manager.get_statistics()
# Returns: detailed statistics dict
```

### Glossary Integration Helper

**load_glossary_for_stage:**
```python
from shared.glossary_integration import load_glossary_for_stage

glossary = load_glossary_for_stage(
    stage_io=stage_io,
    config=config,
    logger=logger,
    project_root=PROJECT_ROOT,
    fallback_to_master=True
)
```

**apply_glossary_to_text:**
```python
from shared.glossary_integration import apply_glossary_to_text

enforced = apply_glossary_to_text(
    text="Some dialogue with yaar",
    glossary=glossary,
    context="casual",
    logger=logger
)
```

**get_glossary_stats:**
```python
from shared.glossary_integration import get_glossary_stats

stats = get_glossary_stats(glossary)
print(f"Terms: {stats.get('total_terms', 0)}")
```

---

## Configuration

### Environment Variables

**File:** `.env.pipeline`

```bash
# === Glossary Configuration ===

# Enable/disable glossary stage
GLOSSARY_ENABLE=true

# TMDB caching
GLOSSARY_CACHE_ENABLE=true
GLOSSARY_CACHE_TTL_DAYS=30

# Term filtering
GLOSSARY_MIN_CONFIDENCE=0.6
GLOSSARY_MAX_TERMS=1000

# Strategy selection
GLOSSARY_STRATEGY=cascade  # cascade|frequency|context|ml

# Paths (relative to project root)
GLOSSARY_MASTER_PATH=glossary/hinglish_master.tsv
GLOSSARY_OVERRIDES_DIR=glossary/film_overrides
GLOSSARY_CACHE_DIR=glossary/cache
```

### Configuration Object

```python
from shared.config import load_config

config = load_config()

# Access glossary settings
enabled = getattr(config, 'glossary_enabled', True)
cache_enabled = getattr(config, 'glossary_cache_enabled', True)
ttl_days = getattr(config, 'glossary_cache_ttl_days', 30)
min_conf = getattr(config, 'glossary_min_confidence', 0.6)
strategy = getattr(config, 'glossary_strategy', 'cascade')
```

---

## Best Practices

### For Glossary Generation

1. **Always Run Stage 2 First:**
   ```bash
   ./run-pipeline.sh --job <id> --stages tmdb,glossary_load
   ```

2. **Use Caching in Production:**
   ```bash
   GLOSSARY_CACHE_ENABLE=true
   GLOSSARY_CACHE_TTL_DAYS=30
   ```

3. **Add Film-Specific Overrides:**
   ```bash
   # Create: glossary/film_overrides/3_Idiots_2009.tsv
   source    preferred_english  notes          context
   chatur    Chatur            character      dialogue
   ICE       Imperial College  university     location
   ```

4. **Monitor Cache Size:**
   ```bash
   du -sh glossary/cache/
   # Clean old caches periodically
   ```

### For Glossary Application

1. **Always Check Glossary Loaded:**
   ```python
   glossary = load_glossary_for_stage(...)
   if glossary is None:
       logger.warning("Glossary not loaded - terms won't be enforced")
   ```

2. **Use Appropriate Context:**
   ```python
   # For dialogue
   result = glossary.apply_to_text(text, context="casual")
   
   # For formal scenes
   result = glossary.apply_to_text(text, context="formal")
   ```

3. **Handle Errors Gracefully:**
   ```python
   try:
       text = apply_glossary_to_text(text, glossary, logger=logger)
   except Exception as e:
       logger.warning(f"Glossary failed: {e}")
       # Continue with original text
   ```

4. **Track Application:**
   ```python
   if glossary:
       stats = get_glossary_stats(glossary)
       logger.info(f"Applied glossary: {stats.get('total_terms')} terms")
   ```

### Performance Tips

1. **Cache TMDB Data:**
   - Reduces API calls
   - Faster subsequent runs
   - Set appropriate TTL

2. **Disable Learning in Production:**
   ```python
   UnifiedGlossaryManager(..., enable_learning=False)
   ```

3. **Use Cascade Strategy:**
   ```python
   UnifiedGlossaryManager(..., strategy='cascade')
   # Fastest, most predictable
   ```

4. **Limit Term Count:**
   ```bash
   GLOSSARY_MAX_TERMS=1000
   # Prevents memory bloat
   ```

---

## Troubleshooting

### Issue: Glossary Not Loading

**Symptoms:**
```
Glossary not loaded - terms will not be enforced
```

**Solutions:**

1. **Check Stage 3 Ran:**
   ```bash
   ls out/<job-id>/03_glossary_load/film_glossary.tsv
   ```

2. **Check Configuration:**
   ```bash
   grep GLOSSARY_ENABLE .env.pipeline
   # Should be: GLOSSARY_ENABLE=true
   ```

3. **Check Master Glossary:**
   ```bash
   ls glossary/hinglish_master.tsv
   ```

4. **Check Logs:**
   ```bash
   tail -f logs/<job-id>/03_glossary_load.log
   tail -f logs/<job-id>/11_subtitle_generation.log
   ```

### Issue: Terms Not Applied

**Symptoms:**
- Glossary loads but terms not enforced
- Hinglish words translated incorrectly

**Solutions:**

1. **Verify Term in Glossary:**
   ```bash
   grep "yaar" out/<job-id>/03_glossary_load/film_glossary.tsv
   ```

2. **Check Confidence Threshold:**
   ```bash
   # Lower threshold if needed
   GLOSSARY_MIN_CONFIDENCE=0.5
   ```

3. **Check Text Format:**
   ```python
   # Ensure text is clean
   text = text.strip()
   text = glossary.apply_to_text(text)
   ```

4. **Enable Debug Logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

### Issue: Cache Problems

**Symptoms:**
```
Failed to load TMDB cache
Cache file corrupted
```

**Solutions:**

1. **Clear Cache:**
   ```bash
   rm -rf glossary/cache/*
   ```

2. **Disable Cache Temporarily:**
   ```bash
   GLOSSARY_CACHE_ENABLE=false
   ```

3. **Check Permissions:**
   ```bash
   ls -la glossary/cache/
   chmod 755 glossary/cache/
   ```

4. **Rebuild Cache:**
   ```bash
   ./run-pipeline.sh --job <id> --stages glossary_load
   ```

### Issue: Performance Slow

**Symptoms:**
- Glossary loading takes too long
- High memory usage

**Solutions:**

1. **Enable Caching:**
   ```bash
   GLOSSARY_CACHE_ENABLE=true
   ```

2. **Limit Terms:**
   ```bash
   GLOSSARY_MAX_TERMS=500
   GLOSSARY_MIN_CONFIDENCE=0.7
   ```

3. **Use Cascade Strategy:**
   ```bash
   GLOSSARY_STRATEGY=cascade
   ```

4. **Monitor Resources:**
   ```bash
   # Check memory
   ps aux | grep glossary_builder
   
   # Check cache size
   du -sh glossary/cache/
   ```

---

## Examples

### Example 1: Basic Integration

```python
#!/usr/bin/env python3
"""
Basic glossary integration example
"""
from pathlib import Path
from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config
from shared.glossary_integration import (
    load_glossary_for_stage,
    apply_glossary_to_text
)

def main():
    # Setup
    stage_io = StageIO(
        stage_name="my_stage",
        job_dir=Path("out/2025/11/28/baseline/1"),
        config_name="my_stage"
    )
    config = load_config()
    logger = get_stage_logger("my_stage")
    
    # Load glossary
    glossary = load_glossary_for_stage(
        stage_io=stage_io,
        config=config,
        logger=logger
    )
    
    # Process text
    text = "Hey yaar, let's go!"
    
    if glossary:
        text = apply_glossary_to_text(text, glossary, logger=logger)
        logger.info(f"Enforced: {text}")
    
    return 0

if __name__ == "__main__":
    exit(main())
```

### Example 2: Advanced Integration

```python
#!/usr/bin/env python3
"""
Advanced glossary integration with statistics
"""
from pathlib import Path
from shared.glossary_manager import UnifiedGlossaryManager
from shared.glossary_integration import get_glossary_stats

def advanced_integration():
    # Direct UnifiedGlossaryManager usage
    manager = UnifiedGlossaryManager(
        project_root=Path.cwd(),
        film_title="3 Idiots",
        film_year=2009,
        enable_cache=True,
        strategy='cascade'
    )
    
    # Load all sources
    stats = manager.load_all_sources()
    print(f"Loaded {stats['total_terms']} terms")
    print(f"  Master: {stats['master_terms']}")
    print(f"  TMDB: {stats['tmdb_terms']}")
    print(f"  Film: {stats['film_terms']}")
    
    # Get specific term
    translation = manager.get_term("yaar", context="casual")
    print(f"yaar → {translation}")
    
    # Apply to multiple texts
    texts = [
        "Hey yaar, how are you?",
        "Rancho is my best dost",
        "Let's go bhai"
    ]
    
    for text in texts:
        enforced = manager.apply_to_text(text, context="casual")
        print(f"Original: {text}")
        print(f"Enforced: {enforced}")
        print()
    
    # Get bias terms for ASR
    bias_terms = manager.get_bias_terms(max_terms=50)
    print(f"Bias terms: {', '.join(bias_terms[:10])}...")
    
    # Save snapshot
    manager.save_snapshot(Path("glossary_snapshot.json"))

if __name__ == "__main__":
    advanced_integration()
```

### Example 3: Custom Stage Integration

```python
#!/usr/bin/env python3
"""
Example: Integrating glossary into a new stage
"""
from pathlib import Path
from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config
from shared.glossary_integration import load_glossary_for_stage

def my_custom_stage():
    # Stage setup
    stage_io = StageIO(...)
    config = load_config()
    logger = get_stage_logger(...)
    
    # Load glossary
    logger.info("Loading glossary for term enforcement...")
    glossary = load_glossary_for_stage(
        stage_io=stage_io,
        config=config,
        logger=logger,
        fallback_to_master=True
    )
    
    if glossary is None:
        logger.warning("Glossary not available - continuing without")
    else:
        logger.info("✓ Glossary loaded successfully")
    
    # Read input data
    input_file = stage_io.get_input_path("data.json", from_stage="previous")
    with open(input_file) as f:
        data = json.load(f)
    
    # Process with glossary
    results = []
    for item in data:
        text = item['text']
        
        # Apply glossary if available
        if glossary:
            try:
                text = glossary.apply_to_text(text)
            except Exception as e:
                logger.warning(f"Glossary application failed: {e}")
        
        results.append({'text': text, ...})
    
    # Write output
    output_file = stage_io.get_output_path("results.json")
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Track glossary usage in config
    if glossary:
        stats = glossary.get_statistics()
        stage_io.set_config({
            'glossary_enabled': True,
            'glossary_terms': stats.get('total_terms', 0)
        })
    
    stage_io.finalize(status="success")

if __name__ == "__main__":
    my_custom_stage()
```

---

## Additional Resources

### Documentation

- **Architecture:** `shared/GLOSSARY_ARCHITECTURE.md`
- **REC-1 Implementation:** `docs/GLOSSARY_BUILDER_REC1_IMPLEMENTATION.md`
- **REC-3 Config Alignment:** `docs/GLOSSARY_CONFIG_ALIGNMENT_REC3.md`
- **REC-4 Docs Update:** `docs/GLOSSARY_BUILDER_DOCS_UPDATE_REC4.md`
- **REC-5 Consolidation:** `docs/GLOSSARY_CLASS_CONSOLIDATION_REC5.md`
- **REC-6 Integration:** `docs/GLOSSARY_DOWNSTREAM_INTEGRATION_REC6.md`
- **User Guide:** `docs/user-guide/glossary-builder.md`

### Source Code

- **Canonical Manager:** `shared/glossary_manager.py`
- **Integration Helper:** `shared/glossary_integration.py`
- **Stage Script:** `scripts/glossary_builder.py`
- **Cache Module:** `shared/glossary_cache.py`
- **Generator:** `shared/glossary_generator.py`

### Support

For issues or questions:
1. Check logs in `logs/<job-id>/`
2. Review manifest in `out/<job-id>/*/manifest.json`
3. Check documentation in `docs/`
4. Review developer standards in `docs/DEVELOPER_STANDARDS.md`

---

**Last Updated:** 2025-11-28  
**Version:** 1.0  
**Status:** Production Ready
