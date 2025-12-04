# Translation Stage Refactoring Plan

**Date:** 2025-12-04  
**Status:** 📋 Planning Complete  
**Impact:** High (splits largest stage)  
**Complexity:** Medium

---

## 🎯 Objective

Refactor Stage 10 (Translation - 1045 LOC) into 4 smaller, focused stages to improve:
- Single Responsibility Principle adherence
- Testability and maintainability
- Error isolation
- Resource optimization
- Future parallel execution capability

---

## 📊 Current State Analysis

### Stage 10: Translation (1045 LOC)
**File:** `scripts/10_translation.py`  
**Virtual Env:** Uses both `indictrans2` and `nllb`  
**Responsibilities:** (Too many!)
1. Model management (IndicTrans2 + NLLB)
2. Language routing logic
3. Translation execution
4. Post-processing
5. Multi-language coordination

### Problems Identified:
1. **Complexity:** 1045 LOC (2.5x larger than next stage)
2. **Mixed Concerns:** Two different translation models in one stage
3. **Resource Waste:** Loads both models even if only one needed
4. **Testing Difficulty:** Hard to test IndicTrans2 vs NLLB independently
5. **Error Handling:** Failures in one model affect the other
6. **Logging Confusion:** Mixed logs from two models

---

## 🏗️ Proposed Architecture

### New Stage Structure:

```
Current: 10 (Translation) → 11 (Subtitle Gen) → 12 (Mux)

Proposed: 10 (Prep) → 11a (IndicTrans2) → 11b (NLLB) → 11c (Merge) → 12 (Subtitle Gen) → 13 (Mux)
```

---

## 📝 Stage Definitions

### Stage 10: Translation Preparation
**File:** `scripts/10_translation_prep.py`  
**Lines:** ~200 LOC  
**Virtual Env:** `venv/common` (lightweight)  
**Duration:** <5 seconds

**Responsibilities:**
- Load job configuration and language requirements
- Analyze source and target language pairs
- Determine optimal translation strategy per pair
  - Indic→English/non-Indic: Use IndicTrans2
  - Non-Indic→Indic: Use NLLB
  - Non-Indic→Non-Indic: Use NLLB
- Create translation execution plan
- Validate language support
- Write routing manifest

**Inputs:**
- `job.json` (language requirements)
- `07_alignment/transcript.json` (source transcript)

**Outputs:**
- `10_translation_prep/translation_plan.json`
```json
{
  "pairs": [
    {"source": "hi", "target": "en", "model": "indictrans2", "priority": 1},
    {"source": "hi", "target": "es", "model": "nllb", "priority": 2}
  ],
  "models_needed": ["indictrans2", "nllb"],
  "estimated_duration": 180
}
```

**StageIO Integration:** ✅ Yes  
**Manifest Tracking:** ✅ Yes

---

### Stage 11a: IndicTrans2 Translation
**File:** `scripts/11a_indictrans2_translation.py`  
**Lines:** ~400 LOC  
**Virtual Env:** `venv/indictrans2` (EXISTING)  
**Duration:** 30-120 seconds (per language pair)

**Responsibilities:**
- Load IndicTrans2 model (if needed per plan)
- Process Indic→English/non-Indic translations only
- Apply glossary terms and context
- Generate quality scores
- Handle model-specific errors
- Write translation results

**Inputs:**
- `10_translation_prep/translation_plan.json`
- `07_alignment/transcript.json`
- `03_glossary_load/glossary.json` (optional)

**Outputs:**
- `11a_indictrans2_translation/translation_hi_en.json`
- `11a_indictrans2_translation/translation_hi_gu.json`
- `11a_indictrans2_translation/quality_metrics.json`

**Skip Condition:** If translation_plan says no IndicTrans2 pairs needed

**StageIO Integration:** ✅ Yes  
**Manifest Tracking:** ✅ Yes  
**Model Caching:** ✅ Yes (HuggingFace cache)

---

### Stage 11b: NLLB Translation
**File:** `scripts/11b_nllb_translation.py`  
**Lines:** ~400 LOC  
**Virtual Env:** `venv/nllb` (EXISTING)  
**Duration:** 30-120 seconds (per language pair)

**Responsibilities:**
- Load NLLB-200 model (if needed per plan)
- Process non-Indic translations
- Process fallback translations
- Apply glossary terms and context
- Generate quality scores
- Handle model-specific errors
- Write translation results

**Inputs:**
- `10_translation_prep/translation_plan.json`
- `07_alignment/transcript.json`
- `03_glossary_load/glossary.json` (optional)

**Outputs:**
- `11b_nllb_translation/translation_hi_es.json`
- `11b_nllb_translation/translation_hi_ar.json`
- `11b_nllb_translation/quality_metrics.json`

**Skip Condition:** If translation_plan says no NLLB pairs needed

**StageIO Integration:** ✅ Yes  
**Manifest Tracking:** ✅ Yes  
**Model Caching:** ✅ Yes (HuggingFace cache)

---

### Stage 11c: Translation Merge
**File:** `scripts/11c_translation_merge.py`  
**Lines:** ~150 LOC  
**Virtual Env:** `venv/common` (lightweight)  
**Duration:** <5 seconds

**Responsibilities:**
- Collect translations from 11a and 11b
- Merge results into unified format
- Validate all required translations present
- Perform final quality checks
- Generate consolidated quality report
- Create unified output for subtitle generation

**Inputs:**
- `11a_indictrans2_translation/*.json`
- `11b_nllb_translation/*.json`
- `10_translation_prep/translation_plan.json`

**Outputs:**
- `11c_translation_merge/translations.json` (all languages)
- `11c_translation_merge/quality_report.json`

**StageIO Integration:** ✅ Yes  
**Manifest Tracking:** ✅ Yes

---

### Stage 12: Subtitle Generation (RENUMBERED)
**File:** `scripts/12_subtitle_generation.py` (renamed from 11)  
**No Changes:** Just renumbered  
**Virtual Env:** `venv/common`

---

### Stage 13: Mux (RENUMBERED)
**File:** `scripts/13_mux.py` (renamed from 12)  
**No Changes:** Just renumbered  
**Virtual Env:** `venv/common`

---

## 🔄 Workflow Updates

### Transcribe Workflow (No Change)
```
01_demux → 04_source_sep → 05_pyannote → 06_whisperx → 07_alignment
```

### Translate Workflow (UPDATED)
```
Before: 01 → 04 → 05 → 06 → 07 → 10 (translation)
After:  01 → 04 → 05 → 06 → 07 → 10 (prep) → 11a/11b (parallel) → 11c (merge)
```

### Subtitle Workflow (UPDATED)
```
Before: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 12
After:  01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11a/11b → 11c → 12 → 13
```

---

## 📋 Implementation Checklist

### Phase 1: Preparation ✅
- [x] Analyze current translation stage
- [x] Identify split points
- [x] Verify venvs exist (indictrans2, nllb)
- [x] Verify requirements files exist
- [x] Design new architecture
- [ ] Document refactoring plan (this file)

### Phase 2: Create New Stages
- [ ] Create `scripts/10_translation_prep.py`
- [ ] Create `scripts/11a_indictrans2_translation.py`
- [ ] Create `scripts/11b_nllb_translation.py`
- [ ] Create `scripts/11c_translation_merge.py`

### Phase 3: Refactor Existing Code
- [ ] Extract routing logic → 10_translation_prep.py
- [ ] Extract IndicTrans2 code → 11a_indictrans2_translation.py
- [ ] Extract NLLB code → 11b_nllb_translation.py
- [ ] Extract merge logic → 11c_translation_merge.py

### Phase 4: Renumber Stages
- [ ] Rename `11_subtitle_generation.py` → `12_subtitle_generation.py`
- [ ] Rename `12_mux.py` → `13_mux.py`
- [ ] Update all imports and references

### Phase 5: Update Configuration
- [ ] Update `shared/stage_dependencies.py`
- [ ] Update workflow definitions in `run-pipeline.py`
- [ ] Update stage environment mapping in `prepare-job.py`
- [ ] Update `CANONICAL_PIPELINE.md`

### Phase 6: Testing
- [ ] Unit test each new stage
- [ ] Integration test: Translate workflow
- [ ] Integration test: Subtitle workflow
- [ ] Performance comparison (before/after)

### Phase 7: Documentation
- [ ] Update `IMPLEMENTATION_TRACKER.md`
- [ ] Update `docs/stages/` documentation
- [ ] Update `copilot-instructions.md`
- [ ] Update architecture diagrams
- [ ] Create migration guide

---

## 🎁 Benefits

### 1. Single Responsibility
Each stage has one clear job, easier to understand and maintain

### 2. Better Error Isolation
IndicTrans2 failures don't affect NLLB and vice versa

### 3. Resource Optimization
Only load models that are actually needed per translation plan

### 4. Improved Testability
Test IndicTrans2 and NLLB independently with targeted test cases

### 5. Clearer Logging
Each model's performance and issues logged separately

### 6. Future Parallelization
11a and 11b can run in parallel (Phase 5 optimization)

### 7. Better Monitoring
Track per-model performance, quality, and errors independently

### 8. Easier Debugging
Narrow down issues to specific translation model

---

## ⚠️ Risks & Mitigation

### Risk 1: Increased I/O
**Impact:** More file reads/writes between stages  
**Mitigation:** Minimal - translation plans and results are small JSON files

### Risk 2: Complexity Perception
**Impact:** More stages might seem more complex  
**Mitigation:** Better documentation, clearer separation of concerns

### Risk 3: Migration Effort
**Impact:** Need to update multiple files  
**Mitigation:** Systematic checklist, thorough testing

### Risk 4: Performance Regression
**Impact:** Additional stage overhead  
**Mitigation:** Measure before/after, optimize if needed

---

## 📊 Success Criteria

- ✅ All 4 new stages < 400 LOC each
- ✅ 100% standards compliance maintained
- ✅ All tests pass (unit + integration)
- ✅ Performance within 5% of original
- ✅ Error handling improved (better isolation)
- ✅ Documentation complete and consistent

---

## 🗓️ Timeline

**Estimated Effort:** 8-12 hours  
**Recommended Approach:** Incremental (1-2 stages per session)

### Session 1 (2-3 hours):
- Create Stage 10 (Prep)
- Create Stage 11a (IndicTrans2)

### Session 2 (2-3 hours):
- Create Stage 11b (NLLB)
- Create Stage 11c (Merge)

### Session 3 (2-3 hours):
- Renumber existing stages
- Update configuration and workflows

### Session 4 (2-3 hours):
- Testing and validation
- Documentation updates

---

## 📎 Related Files

**Core Implementation:**
- `scripts/10_translation.py` (current - to be split)
- `scripts/11_subtitle_generation.py` (to be renumbered)
- `scripts/12_mux.py` (to be renumbered)

**Configuration:**
- `shared/stage_dependencies.py`
- `shared/stage_order.py`
- `scripts/run-pipeline.py`
- `scripts/prepare-job.py`

**Virtual Environments:**
- `venv/indictrans2/` (existing)
- `venv/nllb/` (existing)
- `requirements/requirements-indictrans2.txt` (existing)
- `requirements/requirements-nllb.txt` (existing)

**Documentation:**
- `IMPLEMENTATION_TRACKER.md`
- `CANONICAL_PIPELINE.md`
- `docs/stages/10_translation.md`
- `.github/copilot-instructions.md`

---

**Status:** 📋 Ready to Implement  
**Next Step:** Create Stage 10 (Translation Prep)  
**Priority:** High (improves architecture significantly)  
**Complexity:** Medium (systematic refactoring)

**Last Updated:** 2025-12-04 04:50 UTC
