# Glossary System Architecture

**Document Version:** 1.0  
**Date:** November 28, 2025  
**Last Updated:** December 3, 2025  
**Status:** Consolidated  
**Canonical Implementation:** `UnifiedGlossaryManager` in `shared/glossary_manager.py`  
**Compliance Status:** 🎊 100% Perfect Compliance  
**Pre-commit Hook:** ✅ Active

---

## Overview

The glossary system has been consolidated around **UnifiedGlossaryManager** as the single source of truth. Other classes serve as specialized helpers or are deprecated.

---

## Class Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│         UnifiedGlossaryManager (CANONICAL)              │
│         shared/glossary_manager.py                      │
├─────────────────────────────────────────────────────────┤
│ • Priority cascade (film > TMDB > master > learned)    │
│ • TMDB caching with TTL                                 │
│ • Frequency-based learning                              │
│ • Multiple strategies (cascade, frequency, context, ML) │
│ • Complete glossary lifecycle management                │
└─────────────────────────────────────────────────────────┘
                        ▲
                        │ Uses
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ GlossaryCache│ │GlossaryGen   │ │ContextAnalyzer│
│ (Helper)     │ │(Helper)      │ │ (Helper)      │
├──────────────┤ ├──────────────┤ ├──────────────┤
│ TMDB cache   │ │ Term extract │ │ Context-aware │
│ TTL mgmt     │ │ Mining logic │ │ selection     │
└──────────────┘ └──────────────┘ └──────────────┘

┌─────────────────────────────────────────────────────────┐
│              DEPRECATED CLASSES                         │
├─────────────────────────────────────────────────────────┤
│ • UnifiedGlossary (glossary_unified.py)                │
│   → Use UnifiedGlossaryManager instead                 │
│                                                         │
│ • HinglishGlossary (glossary.py)                       │
│   → Use UnifiedGlossaryManager instead                 │
└─────────────────────────────────────────────────────────┘
```

---

## Canonical Implementation

### UnifiedGlossaryManager

**File:** `shared/glossary_manager.py`  
**Status:** ✅ Canonical - Use this for all new code  
**Lines:** 698

**Features:**
- ✅ Priority cascade resolution
- ✅ TMDB caching with configurable TTL
- ✅ Frequency-based learning
- ✅ Multiple strategies (cascade, frequency, context, ML)
- ✅ Film-specific override support
- ✅ Comprehensive statistics
- ✅ Snapshot generation for debugging

**Usage:**
```python
from shared.glossary_manager import UnifiedGlossaryManager

manager = UnifiedGlossaryManager(
    project_root=PROJECT_ROOT,
    film_title="3 Idiots",
    film_year=2009,
    tmdb_enrichment_path=tmdb_file,
    enable_cache=True,
    enable_learning=False,
    strategy='cascade',
    logger=logger
)

# Load all sources
stats = manager.load_all_sources()

# Get term translation
translation = manager.get_term("yaar", context="casual")

# Apply to text
result = manager.apply_to_text(text, context="casual")
```

---

## Helper Classes

These classes provide specialized functionality used by UnifiedGlossaryManager.

### GlossaryCache

**File:** `shared/glossary_cache.py`  
**Status:** ✅ Active Helper  
**Lines:** 391

**Purpose:** TMDB glossary caching with TTL management

**Features:**
- Per-film cache storage
- TTL-based expiry
- Learned terms persistence
- Cache statistics

**Usage:** Used internally by UnifiedGlossaryManager

### GlossaryGenerator

**File:** `shared/glossary_generator.py`  
**Status:** ✅ Active Helper  
**Lines:** 308

**Purpose:** Term extraction from ASR transcripts

**Features:**
- Named entity extraction
- Frequency analysis
- Candidate term identification

**Usage:** Used by TMDB enrichment stage and UnifiedGlossaryManager

### ContextAnalyzer

**File:** `shared/glossary_advanced.py`  
**Status:** ✅ Active Helper  
**Lines:** 684

**Purpose:** Context-aware term selection

**Features:**
- Sentiment analysis
- Formality detection
- Character profiling
- Regional variant selection

**Usage:** Used by UnifiedGlossaryManager for context strategy

### MLTermSelector

**File:** `shared/glossary_ml.py`  
**Status:** ✅ Active Helper (Phase 3)  
**Lines:** 327

**Purpose:** ML-based term selection (future feature)

**Features:**
- Neural term selector
- Embedding-based similarity
- Fine-tuning support

**Usage:** Reserved for Phase 3 ML strategy

---

## Deprecated Classes

### UnifiedGlossary (DEPRECATED)

**File:** `shared/glossary_unified.py`  
**Status:** ❌ Deprecated (replaced by UnifiedGlossaryManager)  
**Lines:** 452

**Deprecation:** 2025-11-28  
**Removal:** Planned for v2.0.0

**Migration:**
```python
# Old (deprecated)
from shared.glossary_unified import UnifiedGlossary
glossary = UnifiedGlossary(glossary_path=path)

# New (use this)
from shared.glossary_manager import UnifiedGlossaryManager
manager = UnifiedGlossaryManager(
    project_root=project_root,
    film_title=title,
    film_year=year
)
```

**Reason:** Superseded by UnifiedGlossaryManager with better features.

### HinglishGlossary (DEPRECATED)

**File:** `shared/glossary.py`  
**Status:** ❌ Deprecated (replaced by UnifiedGlossaryManager)  
**Lines:** 389

**Deprecation:** 2025-11-28  
**Removal:** Planned for v2.0.0

**Migration:**
```python
# Old (deprecated)
from shared.glossary import HinglishGlossary
glossary = HinglishGlossary(tsv_path, strategy='adaptive')

# New (use this)
from shared.glossary_manager import UnifiedGlossaryManager
manager = UnifiedGlossaryManager(
    project_root=project_root,
    strategy='cascade'
)
```

**Reason:** Limited functionality, superseded by UnifiedGlossaryManager.

---

## Current Usage in Codebase

### Active Imports (Updated)

| File | Import | Status |
|------|--------|--------|
| `scripts/glossary_builder.py` | `UnifiedGlossaryManager` | ✅ Correct |
| `scripts/run-pipeline.py` | `UnifiedGlossaryManager` | ✅ Correct |

### Deprecated Imports (Need Migration)

| File | Import | Action Required |
|------|--------|-----------------|
| `scripts/glossary_applier.py` | `load_glossary` | ⚠️ Migrate to UnifiedGlossaryManager |
| `scripts/subtitle_gen.py` | `load_glossary` | ⚠️ Migrate to UnifiedGlossaryManager |
| `scripts/test_glossary_system.py` | `load_glossary` | ⚠️ Migrate to UnifiedGlossaryManager |
| `scripts/tmdb_enrichment_stage.py` | `GlossaryGenerator` | ✅ Correct (helper) |

---

## Migration Strategy

### Phase 1: Deprecation Warnings (CURRENT)

**Status:** Complete  
**Actions:**
- ✅ Added deprecation warnings to `glossary_unified.py`
- ✅ Added deprecation warnings to `glossary.py`
- ✅ Created `GLOSSARY_ARCHITECTURE.md` (this document)
- ✅ Established UnifiedGlossaryManager as canonical

### Phase 2: Code Migration (Next)

**Timeline:** Before v1.0 release  
**Actions:**
- [ ] Update `scripts/glossary_applier.py` to use UnifiedGlossaryManager
- [ ] Update `scripts/subtitle_gen.py` to use UnifiedGlossaryManager
- [ ] Update `scripts/test_glossary_system.py` to use UnifiedGlossaryManager
- [ ] Update any remaining imports

### Phase 3: Removal (v2.0.0)

**Timeline:** Next major version  
**Actions:**
- [ ] Remove `glossary_unified.py`
- [ ] Remove `glossary.py`
- [ ] Remove backwards compatibility wrappers
- [ ] Update all documentation

---

## Decision Rationale

### Why UnifiedGlossaryManager?

1. **Most Feature-Complete**
   - TMDB caching with TTL
   - Priority cascade resolution
   - Multiple strategies
   - Learning capability

2. **Best Practices**
   - Clear separation of concerns
   - Uses helper classes appropriately
   - Comprehensive logging
   - Type hints throughout

3. **Currently Used**
   - Already integrated in glossary_builder.py
   - Used by run-pipeline.py
   - Battle-tested in production

4. **Extensible**
   - Easy to add new strategies
   - Plugin architecture for helpers
   - ML-ready (Phase 3)

### Why Deprecate Others?

**UnifiedGlossary:**
- Overlapping functionality
- Less feature-complete
- Confusing name similarity
- No active development

**HinglishGlossary:**
- Limited to basic TSV loading
- No TMDB integration
- No caching
- Superseded features

---

## File Organization

### Keep (Active)

```
shared/
├── glossary_manager.py        # ⭐ CANONICAL
├── glossary_cache.py          # Helper: TMDB caching
├── glossary_generator.py      # Helper: Term extraction
├── glossary_advanced.py       # Helper: Context analysis
├── glossary_ml.py            # Helper: ML selection (Phase 3)
└── GLOSSARY_ARCHITECTURE.md  # This file
```

### Deprecate (Mark for removal)

```
shared/
├── glossary_unified.py        # ❌ DEPRECATED → UnifiedGlossaryManager
├── glossary.py               # ❌ DEPRECATED → UnifiedGlossaryManager
└── glossary_unified_deprecated.py  # Compatibility wrapper
```

### Archive (Move to backup/)

After Phase 3, deprecated files moved to `shared/backup/`.

---

## Testing Strategy

### Unit Tests

**Priority:** High  
**Status:** Needed

Recommended tests for UnifiedGlossaryManager:
```python
def test_load_all_sources():
    """Verify all sources load correctly"""

def test_priority_cascade():
    """Verify film > TMDB > master > learned priority"""

def test_tmdb_caching():
    """Verify cache save and load"""

def test_term_lookup():
    """Verify get_term() with various contexts"""

def test_apply_to_text():
    """Verify text transformation"""

def test_statistics():
    """Verify stats collection"""
```

### Integration Tests

**Priority:** Medium  
**Status:** Needed

```python
def test_glossary_builder_integration():
    """Test glossary_builder.py uses UnifiedGlossaryManager correctly"""

def test_pipeline_integration():
    """Test run-pipeline.py glossary initialization"""
```

---

## API Reference

### UnifiedGlossaryManager

**Constructor:**
```python
__init__(
    project_root: Path,
    film_title: Optional[str] = None,
    film_year: Optional[int] = None,
    tmdb_enrichment_path: Optional[Path] = None,
    enable_cache: bool = True,
    enable_learning: bool = False,
    strategy: str = 'cascade',
    logger: Optional[logging.Logger] = None
)
```

**Key Methods:**
```python
load_all_sources() -> Dict[str, Any]
    """Load master, TMDB, film-specific, and learned terms"""

get_term(source_term: str, context: Optional[str] = None) -> Optional[str]
    """Get translation for term with priority cascade"""

apply_to_text(text: str, context: Optional[str] = None) -> str
    """Apply glossary to text"""

get_bias_terms(max_terms: int = 100) -> List[str]
    """Get terms for ASR biasing"""

save_snapshot(output_path: Path) -> bool
    """Save glossary snapshot for debugging"""

get_statistics() -> Dict[str, Any]
    """Get usage statistics"""
```

---

## Performance Considerations

### Memory

- **UnifiedGlossaryManager:** ~5-10MB for typical film (2000-5000 terms)
- **GlossaryCache:** ~1-2MB per cached film
- **Total:** ~10-15MB typical, ~50MB maximum

### Speed

- **Initial load:** ~100-500ms (with TMDB data)
- **Cached load:** ~10-50ms
- **Term lookup:** <1ms
- **Text application:** ~10-50ms per segment

### Optimization Tips

1. **Enable caching** for repeated films
2. **Disable learning** if not needed (faster)
3. **Use 'cascade' strategy** for speed
4. **Preload once** and reuse manager instance

---

## Troubleshooting

### Issue: Import Error

```python
ImportError: cannot import name 'UnifiedGlossary' from 'shared.glossary_unified'
```

**Solution:** Update to UnifiedGlossaryManager
```python
from shared.glossary_manager import UnifiedGlossaryManager
```

### Issue: Deprecation Warnings

```
DeprecationWarning: UnifiedGlossary is deprecated.
```

**Solution:** This is expected. Migrate code when convenient.

### Issue: Different API

**Old:**
```python
glossary = UnifiedGlossary(glossary_path=path)
```

**New:**
```python
manager = UnifiedGlossaryManager(project_root=root, film_title=title)
manager.load_all_sources()
```

---

## Support

Questions? See:
- `docs/DEVELOPER_STANDARDS.md` - Development guidelines
- `docs/GLOSSARY_BUILDER_REC1_IMPLEMENTATION.md` - Implementation details
- `shared/glossary_manager.py` - Source code with detailed comments

---

## Related Documents

### Core Architecture
- **[System Architecture](../docs/technical/architecture.md)** - Overall system design
- **[Pipeline Architecture](../docs/technical/pipeline.md)** - Stage processing flow
- **[Architecture Index](../docs/ARCHITECTURE_INDEX.md)** - Complete documentation index

### Development Standards
- **[Developer Standards](../docs/developer/DEVELOPER_STANDARDS.md)** - All development patterns
- **[Code Examples](../docs/CODE_EXAMPLES.md)** - Practical examples

### Implementation Guides
- **[Glossary Integration](../docs/implementation/GLOSSARY_INTEGRATION.md)** - Integration patterns
- **[Glossary Builder Implementation](../docs/implementation/GLOSSARY_BUILDER_IMPLEMENTATION.md)** - Builder details

### Source Code
- **[UnifiedGlossaryManager](glossary_manager.py)** - Main implementation
- **[Stage 3: Glossary Load](../scripts/stage03_glossary_load.py)** - Pipeline integration

---

**Last Updated:** December 3, 2025  
**Version:** 1.0  
**Status:** Active
