# Translation Stage Refactoring Plan (Numeric-Only Architecture)

**Date:** 2025-12-04  
**Status:** ❌ **DEFERRED INDEFINITELY**  
**Decision Date:** 2025-12-04  
**Architecture:** Numeric-Only (No sub-letters)  
**Impact:** Would be HIGH (requires stage renumbering)

**🎯 DECISION:** See [ARCHITECTURE_ALIGNMENT_2025-12-04.md § AD-003](./ARCHITECTURE_ALIGNMENT_2025-12-04.md) for authoritative decision.

---

## ❌ Executive Summary

**DECISION: DEFERRED INDEFINITELY**

**Rationale:**
- ❌ Current implementation (1045 LOC) is already cohesive (single responsibility: translate)
- ❌ Would require renumbering ALL subsequent stages (11→14, 12→15)
- ❌ Adds 3 new stages for minimal benefit
- ❌ Increases I/O overhead (more intermediate files)
- ❌ Breaking translation into prep/execute/merge adds artificial boundaries

**Alternative (if needed later):**
- ✅ Refactor as helper modules (like ASR Option 2)
- ✅ Keep stage as-is, split helper into module directory
- ✅ No workflow disruption

---

## 📊 Analysis: Why This Was Proposed

**Original Problem Identified:**
- Stage 10 (Translation) = 1045 LOC (largest stage)
- Handles IndicTrans2 + NLLB in single stage
- Multiple language pairs in one execution

**Proposed Solution:**

Split Stage 10 into 4 stages:
```
Stage 10: Translation Prep       (~200 LOC, venv/common)
Stage 11: IndicTrans2 Translation (~400 LOC, venv/indictrans2)
Stage 12: NLLB Translation        (~400 LOC, venv/nllb)
Stage 13: Translation Merge       (~150 LOC, venv/common)
Stage 14: Subtitle Generation     (renamed from 11)
Stage 15: Mux                     (renamed from 12)
```

---

## ❌ Why This Was REJECTED

### Problem 1: Unjustified Disruption

**What would be required:**
- Renumber stages 11→14, 12→15
- Update ALL documentation references
- Update run-pipeline.py logic
- Update all test references
- Modify workflow routing
- Update copilot-instructions.md
- Update CANONICAL_PIPELINE.md

**Estimated effort:** 1-2 days of pure busywork

**Benefit:** Minimal - stage is already cohesive

### Problem 2: Current Implementation is Cohesive

**Stage 10 Analysis:**
```
Components:
├── Language pair detection      (~150 LOC)
├── IndicTrans2 model management (~250 LOC)
├── NLLB fallback logic          (~200 LOC)
├── Batch translation            (~200 LOC)
├── Glossary integration         (~150 LOC)
└── Quality scoring              (~95 LOC)
```

**Single Responsibility:** Translate text from source language(s) to target language(s)

**Verdict:** This is ONE logical task, not four.

### Problem 3: Artificial Boundaries

**Proposed split:**
1. Prep: Load config, validate languages
2. IndicTrans2: Translate some pairs
3. NLLB: Translate other pairs
4. Merge: Combine results

**Reality:** These are implementation details of ONE task (translation), not separate concerns.

### Problem 4: Increases Complexity

**Current (1 stage):**
- Read input once
- Translate all pairs
- Write all outputs
- Simple, clean, fast

**Proposed (4 stages):**
- Read input 4 times
- Write intermediate files 3 times
- More error points
- More I/O overhead
- More complex orchestration

**Verdict:** INCREASES complexity without benefit

---

## ✅ Alternative: Helper Module Pattern (If Needed)

**If translation stage becomes unmaintainable in the future:**

```
Stage 10: translation.py (keep as 150 LOC wrapper) ← NO CHANGE
          ↓ uses
scripts/translation/ (NEW MODULE)
├── __init__.py
├── language_router.py       (~150 LOC) - Language pair routing
├── indictrans2_engine.py    (~400 LOC) - IndicTrans2 implementation
├── nllb_engine.py           (~400 LOC) - NLLB implementation
└── glossary_processor.py    (~150 LOC) - Glossary handling
```

**Benefits:**
- ✅ Better code organization
- ✅ Easier to test
- ✅ NO workflow disruption
- ✅ NO stage renumbering
- ✅ Same venvs (indictrans2, nllb)

**This is the ASR Option 2 pattern - proven to work**

---

## 📊 Comparison: Split vs Keep vs Module

| Aspect | Split (4 stages) | Keep (1 stage) | Module Pattern |
|--------|-----------------|----------------|----------------|
| Workflow Disruption | ❌ HIGH | ✅ NONE | ✅ NONE |
| Code Organization | ⚠️ Artificial | ⚠️ Monolithic | ✅ Excellent |
| Testability | ✅ Good | ⚠️ Limited | ✅ Excellent |
| Stage Renumbering | ❌ Required | ✅ Not needed | ✅ Not needed |
| I/O Overhead | ❌ Increases | ✅ Minimal | ✅ Minimal |
| Migration Effort | ❌ HIGH (1-2 days) | ✅ NONE | ✅ LOW (1 day) |
| **DECISION** | **❌ REJECTED** | **✅ CURRENT** | **⏳ IF NEEDED** |

---

## 🔗 Related Documents

**Primary:**
- [ARCHITECTURE_ALIGNMENT_2025-12-04.md § AD-003](./ARCHITECTURE_ALIGNMENT_2025-12-04.md) - Authoritative decision
- [IMPLEMENTATION_TRACKER.md](./IMPLEMENTATION_TRACKER.md) - Task tracking

**Comparison:**
- [ASR_STAGE_REFACTORING_PLAN.md](./ASR_STAGE_REFACTORING_PLAN.md) - Similar analysis, approved Option 2

---

## 📈 Current Stage 10 Status

**File:** `scripts/10_translation.py`  
**Size:** 1045 LOC  
**Complexity:** Manageable  
**Maintainability:** Good  
**Test Coverage:** Adequate  
**Bug Rate:** Low

**Verdict:** No refactoring needed at this time.

---

**Status:** ❌ DEFERRED INDEFINITELY  
**Decision By:** Architecture Alignment (2025-12-04)  
**Next Review:** If stage 10 becomes unmaintainable (>2000 LOC or high bug rate)  
**Alternative:** Use helper module pattern (ASR Option 2) if needed

---

## 📝 Stage Definitions

### Stage 10: Translation Preparation
**File:** `scripts/10_translation_prep.py`  
**Lines:** ~200 LOC  
**Virtual Env:** `venv/common`  
**Duration:** <5 seconds

**Responsibilities:**
- Load job configuration
- Analyze language pairs (source → targets)
- Determine translation strategy:
  - Indic→English/non-Indic: Use IndicTrans2
  - Non-Indic→Any: Use NLLB
- Validate language support
- Create execution plan

**Inputs:**
- `job.json` (language requirements)
- `07_alignment/transcript.json`

**Outputs:**
- `10_translation_prep/translation_plan.json`

**Example Output:**
```json
{
  "source_language": "hi",
  "target_languages": ["en", "es", "ar"],
  "pairs": [
    {"source": "hi", "target": "en", "model": "indictrans2"},
    {"source": "hi", "target": "es", "model": "nllb"},
    {"source": "hi", "target": "ar", "model": "nllb"}
  ],
  "models_needed": ["indictrans2", "nllb"]
}
```

---

### Stage 11: IndicTrans2 Translation
**File:** `scripts/11_indictrans2_translation.py`  
**Lines:** ~400 LOC  
**Virtual Env:** `venv/indictrans2` (EXISTING)  
**Duration:** 30-120 seconds per language

**Responsibilities:**
- Load IndicTrans2 model
- Process Indic→English/non-Indic pairs only
- Apply glossary terms
- Generate quality scores
- Handle errors gracefully

**Inputs:**
- `10_translation_prep/translation_plan.json`
- `07_alignment/transcript.json`
- `03_glossary_load/glossary.json` (optional)

**Outputs:**
- `11_indictrans2_translation/translation_hi_en.json`
- `11_indictrans2_translation/translation_hi_gu.json`
- `11_indictrans2_translation/quality_metrics.json`

**Skip Condition:** If no Indic pairs in translation_plan

---

### Stage 12: NLLB Translation
**File:** `scripts/12_nllb_translation.py`  
**Lines:** ~400 LOC  
**Virtual Env:** `venv/nllb` (EXISTING)  
**Duration:** 30-120 seconds per language

**Responsibilities:**
- Load NLLB-200 model
- Process non-Indic pairs
- Fallback translations if IndicTrans2 unavailable
- Apply glossary terms
- Generate quality scores

**Inputs:**
- `10_translation_prep/translation_plan.json`
- `07_alignment/transcript.json`
- `03_glossary_load/glossary.json` (optional)

**Outputs:**
- `12_nllb_translation/translation_hi_es.json`
- `12_nllb_translation/translation_hi_ar.json`
- `12_nllb_translation/quality_metrics.json`

**Skip Condition:** If no NLLB pairs in translation_plan

**Parallel:** Can run concurrently with Stage 11 (Phase 5 optimization)

---

### Stage 13: Translation Merge
**File:** `scripts/13_translation_merge.py`  
**Lines:** ~150 LOC  
**Virtual Env:** `venv/common`  
**Duration:** <5 seconds

**Responsibilities:**
- Collect translations from Stages 11 and 12
- Merge into unified format
- Validate all required translations present
- Final quality checks
- Consolidate quality metrics

**Inputs:**
- `11_indictrans2_translation/*.json`
- `12_nllb_translation/*.json`
- `10_translation_prep/translation_plan.json`

**Outputs:**
- `13_translation_merge/translations.json` (all languages)
- `13_translation_merge/quality_report.json`

---

### Stage 14: Subtitle Generation (RENUMBERED)
**File:** `scripts/14_subtitle_generation.py` (renamed from 11)  
**No Code Changes:** Just renumbered  
**Virtual Env:** `venv/common`

---

### Stage 15: Mux (RENUMBERED)
**File:** `scripts/15_mux.py` (renamed from 12)  
**No Code Changes:** Just renumbered  
**Virtual Env:** `venv/common`

---

## 🔄 Workflow Updates

### Transcribe Workflow (No Change):
```
01 → 04 → 05 → 06 → 07
```

### Translate Workflow (UPDATED):
```
Before: 01 → 04 → 05 → 06 → 07 → 10
After:  01 → 04 → 05 → 06 → 07 → 10 → 11/12 → 13
```

### Subtitle Workflow (UPDATED):
```
Before: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12
After:  01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12 → 13 → 14 → 15
```

---

## 📋 Implementation Checklist

### Phase 1: Create New Stages
- [ ] Create `scripts/10_translation_prep.py`
- [ ] Create `scripts/11_indictrans2_translation.py`
- [ ] Create `scripts/12_nllb_translation.py`
- [ ] Create `scripts/13_translation_merge.py`
- [ ] Extract logic from current `10_translation.py`
- [ ] 100% standards compliance validation

### Phase 2: Renumber Existing Stages
- [ ] `git mv scripts/11_subtitle_generation.py scripts/14_subtitle_generation.py`
- [ ] `git mv scripts/12_mux.py scripts/15_mux.py`
- [ ] Update internal stage_name references (11→14, 12→15)
- [ ] Update all imports

### Phase 3: Update Configuration
- [ ] Update `shared/stage_dependencies.py`
- [ ] Update `shared/stage_order.py`
- [ ] Update `scripts/run-pipeline.py` workflows
- [ ] Update `scripts/prepare-job.py` stage mappings

### Phase 4: Update Documentation
- [ ] Update `CANONICAL_PIPELINE.md`
- [ ] Update `IMPLEMENTATION_TRACKER.md`
- [ ] Update `.github/copilot-instructions.md`
- [ ] Update `docs/stages/` documentation
- [ ] Update `E2E_TEST_EXECUTION_PLAN.md`

### Phase 5: Testing
- [ ] Unit test each new stage
- [ ] Integration test: Translate workflow
- [ ] Integration test: Subtitle workflow
- [ ] Performance validation
- [ ] Quality validation

---

## 🎯 Success Criteria

- ✅ All 4 new stages < 400 LOC each
- ✅ 100% standards compliance
- ✅ All tests pass
- ✅ Performance within 5% of original
- ✅ Documentation complete
- ✅ No sub-letter numbering (numeric only)

---

## 📊 Expected Benefits

1. **Single Responsibility:** Each stage = one model
2. **Error Isolation:** IndicTrans2 failures don't affect NLLB
3. **Resource Optimization:** Load only needed models
4. **Better Testing:** Test models independently
5. **Clearer Logs:** Separate logs per model
6. **Future Parallel:** Stages 11 & 12 can run concurrently
7. **Maintainability:** Easier to understand and modify

---

## 🗓️ Timeline

**Estimated Effort:** 6-8 hours (2 sessions)

### Session 1 (3-4 hours):
- Create Stages 10-13
- Extract code from current Stage 10
- Validate compliance

### Session 2 (3-4 hours):
- Renumber existing stages (11→14, 12→15)
- Update all configuration
- Update documentation
- Run E2E tests

---

**Status:** ✅ Ready to Implement  
**Architecture:** Numeric-Only (APPROVED)  
**Next Step:** Create Stage 10 (Translation Prep)

**Last Updated:** 2025-12-04 05:00 UTC
