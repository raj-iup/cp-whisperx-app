# ASR Stage Refactoring Plan

**Date:** 2025-12-04  
**Status:** 📋 Analysis Complete  
**Impact:** CRITICAL (largest subsystem)  
**Complexity:** High

---

## 🚨 Critical Discovery

### The Real ASR System Size:
```
Stage 06 (06_whisperx_asr.py):        140 LOC (thin wrapper)
Helper (whisperx_integration.py):   1697 LOC (MASSIVE)
─────────────────────────────────────────────────
TOTAL ASR SYSTEM:                   1837 LOC ⚠️
```

**Comparison:**
- **Translation Stage:** 1045 LOC
- **ASR System:** 1837 LOC (**76% LARGER!**)

### Verdict: **ASR is the MOST COMPLEX subsystem**

---

## 📊 Complexity Breakdown

### whisperx_integration.py Components (1697 LOC):

| Component | Est. LOC | Responsibility |
|-----------|----------|----------------|
| **Model Management** | 200 | Model loading, caching |
| **Backend Abstraction** | 300 | MLX/WhisperX/CUDA switching |
| **Bias Prompting** | 400 | Global/chunked/hybrid strategies |
| **Chunking System** | 300 | Large file handling |
| **Transcription Core** | 300 | Actual ASR execution |
| **Post-Processing** | 200 | Filtering, quality checks |

### Problems Identified:

1. **God Object:** WhisperXProcessor class does EVERYTHING
2. **Mixed Concerns:** Model management + transcription + filtering
3. **Backend Complexity:** 3 different backends (MLX/WhisperX/CUDA)
4. **Bias Complexity:** 3 different strategies
5. **Chunking Complexity:** Large file handling mixed with ASR
6. **Testing Difficulty:** Can't test components independently

---

## 💡 Refactoring Options

### Option 1: Split into Multiple Stages (RADICAL)

**New Architecture:**
```
06a: ASR Model Prep (~200 LOC, common venv)
     ↓
06b: Bias Window Gen (~300 LOC, common venv)  
     ↓
06c: WhisperX ASR (~500 LOC, mlx/whisperx venv)
     ↓
06d: ASR Post-Process (~200 LOC, common venv)
```

**Pros:**
- Maximum separation of concerns
- Granular error isolation
- Can skip stages (e.g., no bias)
- Better resource management

**Cons:**
- Major workflow disruption
- More I/O overhead
- Requires renumbering ALL subsequent stages
- Higher migration complexity

---

### Option 2: Keep Stage, Split Helper Module (MODERATE)

**New Architecture:**
```
Stage 06: WhisperX ASR (140 LOC wrapper)
          ↓ uses
scripts/whisperx/ (MODULE)
├── model_manager.py       (~200 LOC)
├── backend_abstraction.py (~300 LOC)
├── bias_prompting.py      (~400 LOC)
├── chunking.py            (~300 LOC)
├── transcription.py       (~300 LOC)
└── postprocessing.py      (~200 LOC)
```

**Pros:**
- Better code organization
- Easier to test components
- No workflow disruption
- Gradual migration path

**Cons:**
- Still loads everything
- Less granular error isolation
- Can't skip processing steps
- Doesn't optimize resources

---

### Option 3: Hybrid Approach (BALANCED) ⭐

**New Architecture:**
```
06: ASR Preparation (NEW)
    - Model selection
    - Bias window generation
    - Execution planning
    (~400 LOC, common venv)
    ↓
07: WhisperX Transcription (RENAMED)
    - Core ASR execution
    - Backend management  
    - Chunking for large files
    (~800 LOC, mlx/whisperx venv)
    ↓
08: ASR Post-Processing (NEW)
    - Confidence filtering
    - Quality checks
    - Format conversion
    (~300 LOC, common venv)
```

**PLUS:** Modularize the transcription helper

**Pros:**
- Balance between granularity and practicality
- Some separation of concerns
- Better error isolation
- Module split improves maintainability

**Cons:**
- Requires renumbering subsequent stages
- Moderate workflow disruption
- Some migration effort

---

## 🎯 Recommendation

### Immediate (This Session): **Option 2 - Module Split**

**Reasoning:**
1. **Lower Risk:** No workflow disruption
2. **Immediate Value:** Better code organization
3. **Learn First:** Understand ASR complexity before major refactoring
4. **Test Baseline:** Get E2E metrics with current architecture
5. **Warm-up:** Practice refactoring on Translation first

**Implementation:**
```bash
# Create module structure
mkdir -p scripts/whisperx
touch scripts/whisperx/__init__.py

# Split whisperx_integration.py into:
scripts/whisperx/
├── __init__.py
├── model_manager.py       # Model loading, device selection
├── backend_abstraction.py # MLX/WhisperX/CUDA abstraction
├── bias_prompting.py      # All bias strategies
├── chunking.py            # Large file handling
├── transcription.py       # Core ASR logic
└── postprocessing.py      # Filtering and quality
```

---

### Future (Phase 5): **Option 3 - Hybrid Split**

After baseline metrics and Translation refactoring:
1. Create Stage 06 (Prep)
2. Rename current Stage 06 → Stage 07 (Transcription)
3. Create Stage 08 (Post-processing)
4. Renumber subsequent stages

---

## 📋 Implementation Priority

### Recommended Refactoring Order:

**Priority 1: Translation Stage** (FIRST)
- Cleaner split (2 models with clear boundaries)
- Lower complexity
- Good warm-up exercise
- Immediate value

**Priority 2: ASR Module Split** (SECOND)  
- Organize whisperx_integration.py code
- Maintain single stage boundary
- Better testability
- Low risk

**Priority 3: ASR Stage Split** (LATER - Phase 5)
- After baseline metrics
- After Translation refactoring lessons
- More informed decisions

**Priority 4: TMDBStage** (OPTIONAL)
- Only if time permits
- Lower priority (548 LOC is manageable)

---

## 🗺️ Complete Refactoring Roadmap

### Session 1 (NEXT): Translation Stage Refactoring
**Estimated:** 3-4 hours
- Complete E2E Test 1
- Analyze results
- Refactor Translation: 10 → 10,11a,11b,11c
- Renumber: 11→12, 12→13
- Test & validate

### Session 2: ASR Module Split
**Estimated:** 3-4 hours
- Create scripts/whisperx/ module
- Extract 6 components
- Update imports
- Test & validate
- Measure improvement

### Session 3: E2E Testing Round 2
**Estimated:** 2-3 hours
- Re-run all E2E tests
- Performance comparison
- Quality validation
- Update metrics

### Session 4 (Phase 5): ASR Stage Split
**Estimated:** 4-5 hours (future)
- Create stages 06, 07, 08
- Renumber subsequent stages
- Update workflows
- Full testing

---

## 📊 Comparative Analysis

### Stage Complexity Rankings:

| Rank | Subsystem | LOC | Complexity | Priority |
|------|-----------|-----|------------|----------|
| 🥇 | **ASR System** | **1837** | Very High | 1 |
| 🥈 | **Translation** | **1045** | High | 1 |
| 🥉 | **TMDB** | 548 | Medium | 3 |
| 4 | Source Sep | 441 | Medium | - |
| 5 | Mux | 356 | Medium | - |

### Refactoring Impact:

| Stage | Current | After Refactoring | Improvement |
|-------|---------|-------------------|-------------|
| Translation | 1 stage (1045 LOC) | 4 stages (~250 LOC ea) | ✅ 76% reduction |
| ASR | 1 stage (1837 LOC) | 3 stages (~600 LOC ea) | ✅ 67% reduction |

---

## ⚖️ Decision Framework

### Question: Should we refactor ASR now or later?

**Factors to Consider:**

**For NOW:**
- Highest complexity system
- Biggest impact on maintainability
- Will inform future refactoring

**For LATER:**
- More complex than Translation
- Need baseline metrics first
- Learn from Translation refactoring

### Recommended Decision: **LATER (after Translation)**

**Timeline:**
1. **Today:** Complete E2E Test 1, analyze
2. **Next Session:** Refactor Translation stage
3. **Following Session:** Split ASR helper module
4. **Phase 5:** Full ASR stage split

---

## 🎁 Expected Benefits

### After Module Split (Option 2):
- ✅ Better code organization
- ✅ Easier testing (unit tests per module)
- ✅ Clearer responsibilities
- ✅ Better documentation
- ✅ Easier debugging
- ~0% Performance impact (same runtime)

### After Stage Split (Option 3 - Future):
- ✅ Granular error isolation
- ✅ Resource optimization (only load what's needed)
- ✅ Better monitoring per component
- ✅ Can skip stages (e.g., no bias)
- ✅ Future parallel execution
- ✅ Easier integration testing

---

## 📝 Action Items

### Immediate (Today):
- [x] Analyze ASR complexity ✅
- [x] Create refactoring plan ✅
- [ ] Complete E2E Test 1
- [ ] Analyze Test 1 results
- [ ] **DECISION POINT:** Start Translation refactoring?

### Short-term (Next 1-2 Sessions):
- [ ] Refactor Translation stage
- [ ] Split ASR helper module
- [ ] Re-run E2E tests
- [ ] Performance validation

### Medium-term (Phase 5):
- [ ] Split ASR into 3 stages
- [ ] Renumber pipeline stages
- [ ] Full integration testing
- [ ] Update all documentation

---

## 🔗 Related Files

**Analysis:**
- `TRANSLATION_STAGE_REFACTORING_PLAN.md`
- `IMPLEMENTATION_TRACKER.md`

**ASR System:**
- `scripts/06_whisperx_asr.py` (140 LOC wrapper)
- `scripts/whisperx_integration.py` (1697 LOC - TO BE SPLIT)

**Configuration:**
- `shared/stage_dependencies.py`
- `shared/stage_order.py`
- `requirements/requirements-whisperx.txt`
- `requirements/requirements-mlx.txt`

**Virtual Environments:**
- `venv/whisperx/` (WhisperX backend)
- `venv/mlx/` (MLX backend for Apple Silicon)

---

**Status:** 📋 Analysis Complete  
**Next Step:** Complete E2E Test 1, then decide on refactoring order  
**Recommendation:** Translation FIRST, ASR SECOND  
**Confidence:** HIGH (clear path forward)

**Last Updated:** 2025-12-04 04:55 UTC
