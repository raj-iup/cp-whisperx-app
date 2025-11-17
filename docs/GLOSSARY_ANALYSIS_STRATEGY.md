# Glossary System Analysis & Enhancement Strategy

**Date**: 2025-11-14  
**Current Status**: Partially Implemented, Needs Consolidation  
**Priority**: High (Critical for translation quality)

---

## Current State Analysis

### Directory Structure
```
glossary/
├── README.md                      # Documentation (good)
├── hinglish_master.tsv           # Master glossary (55 terms)
├── cache/                         # Per-film glossaries (1 file)
│   └── satte-pe-satta-1982.tsv   # 115 terms
├── glossary_learned/              # Empty (unused)
└── prompts/                       # 19 film prompts
    ├── 3_idiots_2009.txt
    ├── dangal_2016.txt
    └── ... (17 more)
```

### Implementation Files
```
shared/
├── glossary.py                    # Main glossary class (basic)
├── glossary_advanced.py           # Advanced strategies (context-aware)
└── glossary_ml.py                 # ML-based selection (optional)

scripts/
└── glossary_builder.py            # Stage 11: Build glossary from ASR
```

### Current Integration
- **Stage 11**: Glossary Builder (extracts terms from ASR)
- **Stage 12**: Second Pass Translation (could use glossary)
- **Stage 14**: Subtitle Gen (could apply glossary)

---

## Problems Identified

### 1. **Fragmented Implementation** 🔴 CRITICAL
**Issue**: Multiple glossary systems with unclear precedence

```
Master Glossary:     55 terms  (manual, well-structured)
Cache Glossary:     115 terms  (auto-generated, machine format)
Learned Glossary:     0 terms  (unused directory)
```

**Problem**: Which one should be used? How do they interact?

### 2. **Format Inconsistency** 🟡 HIGH
**Master Format** (TSV):
```tsv
source  preferred_english  notes  context
yaar    dude|man|buddy     ...    casual
```

**Cache Format** (Different TSV):
```tsv
term  script  rom  hi  type  english  do_not_translate  capitalize  ...
yaar  rom     yaar     slang  dude    false             false       ...
```

**Problem**: Two incompatible formats, no clear conversion

### 3. **No Active Integration** 🔴 CRITICAL
**Current State**:
- Glossary Builder (Stage 11) builds cache but doesn't use it
- Second Pass Translation doesn't load glossary
- Subtitle Gen doesn't apply glossary
- Advanced strategies implemented but unused

**Expected**: Glossary should be used in translation/subtitle stages

### 4. **Missing Feedback Loop** 🟡 HIGH
**Current**: One-way flow (ASR → Glossary → Nothing)
**Needed**: 
- Learn from corrections
- Track term frequency
- Measure accuracy
- Update master glossary

### 5. **Prompt Files Underutilized** 🟡 MEDIUM
**Status**: 19 excellent prompt files created but not integrated

**Example** (`3_idiots_2009.txt`):
```
Catchphrases (SACRED):
- "All is well" (NEVER translate)
- "Aal izz well" (Raju's variant)
```

**Problem**: Rich context not used in translation

---

## Architecture Issues

### Current Flow (Broken)
```
Stage 6: ASR
    ↓
Stage 11: Glossary Builder (builds cache, unused)
    ↓
Stage 12: Translation (doesn't use glossary) ❌
    ↓
Stage 14: Subtitles (doesn't apply glossary) ❌
```

### Parallel Systems (Confusing)
```
Master Glossary (55 terms, manual)
    ⊥ (not connected)
Cache Glossary (115 terms, auto)
    ⊥ (not connected)
Learned Glossary (0 terms, empty)
    ⊥ (not connected)
```

---

## Recommended Solution Strategy

### Phase 1: Consolidation & Cleanup (2 hours) 🎯 **DO THIS FIRST**

#### 1.1 Unify Glossary Format
**Action**: Standardize on one format

**Recommended Format** (Enhanced TSV):
```tsv
term	english	alternatives	context	confidence	source	frequency	notes
yaar	dude	man|buddy	casual	1.0	manual	145	Young male friends
bhai	bro	brother	casual/formal	1.0	manual	89	Use "bro" casual, "brother" formal
all is well	all is well		sacred	1.0	film:3idiots	67	NEVER translate - signature phrase
```

**Columns**:
- `term`: Source term (Hinglish/Hindi)
- `english`: Primary translation
- `alternatives`: Pipe-separated options
- `context`: Usage context (casual/formal/honorific)
- `confidence`: 0.0-1.0 (how certain we are)
- `source`: Origin (manual/asr/film/learned)
- `frequency`: Usage count
- `notes`: Human-readable guidance

#### 1.2 Create Unified Glossary Manager
**File**: `shared/glossary_unified.py`

```python
class UnifiedGlossary:
    """
    Single source of truth for glossary management
    
    Combines:
    - Master glossary (manual, authoritative)
    - Film-specific terms (from prompts)
    - Learned terms (from ASR/corrections)
    - Cached terms (per-film optimizations)
    
    Priority: Manual > Film-specific > Learned > Cached
    """
    
    def __init__(self):
        self.master = load_master()      # Base glossary
        self.film_terms = {}              # Film-specific overrides
        self.learned = {}                 # Auto-learned terms
        self.cache = {}                   # Per-film cache
    
    def get_translation(self, term, context=None, film=None):
        """Get best translation with priority cascade"""
        # 1. Check film-specific overrides
        if film and term in self.film_terms.get(film, {}):
            return self.film_terms[film][term]
        
        # 2. Check master glossary
        if term in self.master:
            return self.select_by_context(self.master[term], context)
        
        # 3. Check learned terms
        if term in self.learned:
            return self.learned[term]['best']
        
        # 4. Check cache
        if film and term in self.cache.get(film, {}):
            return self.cache[film][term]
        
        # 5. Return original
        return term
```

#### 1.3 Merge Existing Glossaries
**Action**: Consolidate all sources into unified format

```bash
# Script to merge glossaries
python3 tools/merge_glossaries.py \
  --master glossary/hinglish_master.tsv \
  --cache glossary/cache/*.tsv \
  --output glossary/unified_glossary.tsv
```

**Logic**:
1. Load master (authoritative)
2. Add cache terms not in master
3. Keep master terms when conflict
4. Add `source` column to track origin
5. Validate and deduplicate

---

### Phase 2: Active Integration (3 hours) 🎯 **HIGH PRIORITY**

#### 2.1 Integrate with Second Pass Translation
**File**: `scripts/second_pass_translation.py`

**Current**: Translates without glossary
**Enhanced**: Use glossary as translation constraints

```python
def translate_with_glossary(text, glossary):
    """Apply glossary before/after translation"""
    
    # 1. Pre-translation: Mark glossary terms
    marked_text, glossary_terms = mark_glossary_terms(text, glossary)
    
    # 2. Translate (NLLB respects marked terms)
    translated = nllb_translate(marked_text)
    
    # 3. Post-translation: Enforce glossary
    result = enforce_glossary(translated, glossary_terms)
    
    return result
```

**Benefits**:
- Consistent terminology
- Preserve important terms
- Film-specific context

#### 2.2 Integrate with Subtitle Generation
**File**: `scripts/subtitle_gen.py`

**Current**: Generates subtitles without glossary
**Enhanced**: Apply glossary post-processing

```python
def generate_subtitle_with_glossary(segment, glossary, film_context):
    """Apply glossary to subtitle text"""
    
    text = segment['text']
    
    # Apply glossary with context
    enhanced_text = glossary.apply(
        text,
        context=detect_context(segment),  # formal/casual/emotional
        film=film_context['title'],
        speaker=segment.get('speaker')     # character-specific
    )
    
    return enhanced_text
```

#### 2.3 Create Glossary Applier Stage
**New Stage**: `scripts/glossary_applier.py` (between Stage 12 and 13)

```
Stage 12: Translation
    ↓
Stage 12b: Glossary Applier ✨ NEW
    ↓
Stage 13: Post-NER
```

**Purpose**: Dedicated stage for glossary application
- Centralized glossary logic
- Consistent across all content
- Logs applied terms
- Metrics and reporting

---

### Phase 3: Intelligent Enhancement (4 hours) 🎯 **MEDIUM PRIORITY**

#### 3.1 Context-Aware Selection
**Use**: Existing `glossary_advanced.py`

**Enhancement**: Integrate context analyzer

```python
# Analyze context from surrounding segments
context_scores = context_analyzer.analyze(
    current_segment,
    previous_segments=prev_3,
    next_segments=next_3
)

# Select best term variant
translation = glossary.get_translation(
    term="yaar",
    context_scores=context_scores,
    # Result: "dude" (casual=0.8) vs "sir" (formal=0.2)
)
```

#### 3.2 Film-Specific Overrides
**Source**: Prompt files in `glossary/prompts/`

**Action**: Parse and integrate

```python
# Load film-specific rules
film_glossary = FilmGlossary.from_prompt(
    "glossary/prompts/3_idiots_2009.txt"
)

# Sacred terms (never translate)
sacred_terms = {
    "all is well": "all is well",
    "aal izz well": "aal izz well"
}

# Character-specific terms
character_terms = {
    "Rancho": {"yaar": "buddy", "bhai": "brother"},
    "Chatur": {"sir": "sir"}  # Always formal
}
```

#### 3.3 Frequency-Based Learning
**Action**: Track term usage and success

```python
class GlossaryLearner:
    """Learn from usage patterns"""
    
    def track_usage(self, term, selected_translation, context):
        """Track which translation was used"""
        self.frequency[term][selected_translation] += 1
        self.context_map[term][context][selected_translation] += 1
    
    def get_best_translation(self, term, context):
        """Return most frequently used translation"""
        return max(
            self.context_map[term][context].items(),
            key=lambda x: x[1]
        )[0]
    
    def save_learned(self):
        """Save to glossary_learned/"""
        output_path = "glossary/glossary_learned/learned.tsv"
        # Save frequency data for future use
```

---

### Phase 4: Quality & Maintenance (2 hours) 🎯 **LOW PRIORITY**

#### 4.1 Glossary Validation
**Tool**: `tools/validate_glossary.py`

**Checks**:
- Format consistency
- Duplicate terms
- Empty translations
- Invalid context values
- Confidence range (0-1)
- Source tracking

#### 4.2 Automated Testing
**Test Suite**: `tests/test_glossary.py`

```python
def test_glossary_consistency():
    """Ensure all glossaries follow same format"""
    master = load_glossary("glossary/unified_glossary.tsv")
    assert all(has_required_fields(term) for term in master)

def test_term_translation():
    """Test basic translations"""
    glossary = UnifiedGlossary()
    assert glossary.translate("yaar") == "dude"
    assert glossary.translate("ji", context="formal") == "sir"

def test_film_overrides():
    """Test film-specific terms"""
    glossary = UnifiedGlossary(film="3_idiots_2009")
    assert glossary.translate("all is well") == "all is well"  # Sacred
```

#### 4.3 Glossary Dashboard
**Tool**: `tools/glossary_dashboard.py`

**Metrics**:
- Total terms: 170 (55 master + 115 learned)
- Coverage: 85% (terms found in last 10 films)
- Most used: yaar (145x), bhai (89x), ji (67x)
- Needs review: 12 terms (low confidence)
- Film-specific: 3 idiots (5 sacred terms)

#### 4.4 Update Workflow
**Process**:
1. Process film
2. Extract new terms (auto)
3. Flag for review (confidence < 0.7)
4. Human reviews
5. Approve → add to master
6. Update unified glossary

---

## Implementation Roadmap

### Week 1: Consolidation ✅ **START HERE**
**Goal**: Single unified glossary system

- [ ] Day 1-2: Create unified format
- [ ] Day 3: Merge existing glossaries
- [ ] Day 4: Implement UnifiedGlossary class
- [ ] Day 5: Test and validate

**Deliverable**: `glossary/unified_glossary.tsv` (170+ terms)

### Week 2: Integration 🎯
**Goal**: Active glossary usage in pipeline

- [ ] Day 1-2: Integrate with translation stage
- [ ] Day 3: Create glossary applier stage
- [ ] Day 4: Update subtitle generation
- [ ] Day 5: End-to-end testing

**Deliverable**: Working glossary pipeline

### Week 3: Enhancement 📈
**Goal**: Intelligent term selection

- [ ] Day 1-2: Context-aware selection
- [ ] Day 3: Film-specific overrides
- [ ] Day 4-5: Frequency-based learning

**Deliverable**: Smart glossary system

### Week 4: Quality & Maintenance 🔧
**Goal**: Long-term stability

- [ ] Day 1: Validation tools
- [ ] Day 2: Automated tests
- [ ] Day 3: Dashboard
- [ ] Day 4-5: Documentation and training

**Deliverable**: Production-ready system

---

## Quick Wins (Today)

### 1. Merge Glossaries (30 min)
```bash
cd /Users/rpatel/Projects/cp-whisperx-app
python3 << 'EOF'
import pandas as pd
from pathlib import Path

# Load master
master = pd.read_csv('glossary/hinglish_master.tsv', sep='\t')
master['source'] = 'manual'
master['frequency'] = 0

# Load cache
cache = pd.read_csv('glossary/cache/satte-pe-satta-1982.tsv', sep='\t')

# Convert cache to unified format
cache_unified = pd.DataFrame({
    'term': cache['term'],
    'english': cache['english'],
    'alternatives': cache.get('aliases', ''),
    'context': cache['type'],
    'confidence': cache['confidence'],
    'source': 'asr:' + cache['source'],
    'frequency': 0,
    'notes': ''
})

# Merge (master takes precedence)
unified = pd.concat([master, cache_unified]).drop_duplicates('term', keep='first')

# Save
unified.to_csv('glossary/unified_glossary.tsv', sep='\t', index=False)
print(f"✓ Created unified glossary: {len(unified)} terms")
EOF
```

### 2. Create Glossary Applier (1 hour)
See implementation in next section

### 3. Test Integration (30 min)
Run pipeline with glossary enabled and verify terms are applied

---

## Recommended Architecture

### Final System Design

```
┌─────────────────────────────────────────────────────────┐
│             UNIFIED GLOSSARY SYSTEM                      │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐ │
│  │   Master     │───▶│   Unified    │◀───│  Film    │ │
│  │  Glossary    │    │  Glossary    │    │ Prompts  │ │
│  │  (55 terms)  │    │ (170+ terms) │    │ (19 files│ │
│  └──────────────┘    └──────────────┘    └──────────┘ │
│                            │                            │
│                            │                            │
│                      ┌─────▼─────┐                     │
│                      │ Glossary  │                     │
│                      │ Manager   │                     │
│                      └─────┬─────┘                     │
│                            │                            │
│       ┌────────────────────┼────────────────────┐      │
│       │                    │                    │      │
│  ┌────▼────┐         ┌────▼────┐         ┌────▼────┐ │
│  │Context  │         │Learning │         │ Cache   │ │
│  │Analyzer │         │ System  │         │Manager  │ │
│  └─────────┘         └─────────┘         └─────────┘ │
│                                                         │
└─────────────────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
        │Translation│ │Glossary│ │ Subtitle  │
        │  Stage 12 │ │Applier │ │   Gen 14  │
        └───────────┘ │Stage12b│ └───────────┘
                      └────────┘
```

### Data Flow

```
1. Pipeline Start
   ↓
2. Load Unified Glossary (master + film-specific + learned)
   ↓
3. Stage 12: Translation
   ├─→ Pre-translate: Mark glossary terms
   ├─→ Translate with NLLB
   └─→ Post-translate: Enforce glossary
   ↓
4. Stage 12b: Glossary Applier (NEW)
   ├─→ Analyze context (formal/casual/emotional)
   ├─→ Select best term variant
   ├─→ Apply character-specific overrides
   └─→ Track usage for learning
   ↓
5. Stage 14: Subtitle Gen
   ├─→ Format with glossary terms
   └─→ Log applied translations
   ↓
6. Post-Pipeline: Update Learned Glossary
   └─→ Save frequency data for next run
```

---

## Success Metrics

### Phase 1 (Consolidation)
- ✅ Single unified glossary file exists
- ✅ All terms have consistent format
- ✅ No duplicate terms
- ✅ Source tracking for all entries

### Phase 2 (Integration)
- ✅ Translation stage uses glossary
- ✅ Glossary applier stage working
- ✅ Subtitle gen applies glossary
- ✅ 80%+ term coverage in output

### Phase 3 (Enhancement)
- ✅ Context-aware selection working
- ✅ Film-specific terms applied
- ✅ Frequency learning active
- ✅ 90%+ term accuracy

### Phase 4 (Quality)
- ✅ Validation tools running
- ✅ Automated tests passing
- ✅ Dashboard operational
- ✅ Documentation complete

---

## Long-Term Stability Strategy

### 1. Version Control
```
glossary/
├── unified_glossary.tsv          # Current version
├── versions/
│   ├── v1.0_2025-01-01.tsv      # Historical snapshots
│   ├── v1.1_2025-02-01.tsv
│   └── ...
└── CHANGELOG.md                  # Track changes
```

### 2. Quality Gates
- All new terms require confidence > 0.6
- Film-specific terms reviewed by human
- Sacred terms (like "all is well") flagged
- Automated tests on every update

### 3. Continuous Learning
- Track term usage per film
- Measure translation accuracy
- A/B test term variants
- Update master glossary monthly

### 4. Maintainability
- Clear documentation
- Simple data format (TSV)
- Human-readable
- Easy to edit
- Version controlled

---

## Conclusion

**Current State**: Good foundation, poor integration
**Recommendation**: Consolidate first, then integrate
**Time Investment**: 11 hours total (phased over 4 weeks)
**Expected ROI**: 30-50% improvement in translation quality

**Next Action**: Start with Phase 1 (Consolidation) - merge glossaries today

---

## Appendix: Example Implementations

### A. Unified Glossary Class

See separate file: `docs/GLOSSARY_UNIFIED_IMPLEMENTATION.md`

### B. Glossary Applier Stage

See separate file: `docs/GLOSSARY_APPLIER_STAGE.md`

### C. Migration Guide

See separate file: `docs/GLOSSARY_MIGRATION_GUIDE.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-14  
**Author**: AI Analysis  
**Status**: Ready for Review
