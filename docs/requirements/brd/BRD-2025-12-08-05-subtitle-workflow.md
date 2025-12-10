# BRD: Multi-Phase Subtitle Workflow with Learning

**ID:** BRD-2025-12-08-05  
**Created:** 2025-12-08  
**Status:** Approved  
**Priority:** High  
**Target Release:** v3.1

---

## Business Objective

**Problem Statement:**
Current subtitle workflow processes media from scratch every time:
- Wastes 15-20 minutes on subsequent runs
- No reuse of ASR/alignment between iterations
- Lost knowledge from manual corrections
- No quality baseline tracking
- Iterative refinement not supported

**Proposed Solution:**
Three-phase subtitle workflow with intelligent caching:

**Phase 1: BASELINE GENERATION** (First run only, 15-20 min)
- Run ASR, alignment, VAD, diarization
- Store baseline in cache

**Phase 2: GLOSSARY REFINEMENT** (3-6 min per iteration)
- Load cached baseline
- Apply updated glossary
- Regenerate subtitles

**Phase 3: TRANSLATION REFRESH** (2-4 min per language)
- Load cached baseline + glossary results
- Retranslate specific languages
- Regenerate subtitles

---

## Stakeholder Requirements

### Primary Stakeholders
- **Role:** Content Creators
  - **Need:** Fast iterative subtitle refinement
  - **Expected Outcome:** 
    - First run: 15-20 min
    - Subsequent runs: 3-6 min (80% faster)
    - Preserve manual glossary corrections

---

## Success Criteria

### Quantifiable Metrics
- [ ] First run: ≤20 minutes (baseline generation)
- [ ] Glossary updates: ≤6 minutes (reuse baseline)
- [ ] Translation refresh: ≤4 minutes per language
- [ ] Cache hit rate: >90% for repeated media

### Qualitative Measures
- [ ] User-friendly: Automatic cache detection
- [ ] Quality tracking: Baseline metrics stored
- [ ] Knowledge retention: Manual corrections preserved

---

## Scope

### In Scope
- Compute media_id (hash of audio content)
- Cache baseline artifacts (ASR, alignment, VAD)
- Cache glossary-applied results
- Detect and reuse cached artifacts
- Track quality metrics over iterations

### Out of Scope
- Video content caching (only audio/text)
- Distributed caching (single machine only)
- Cloud storage integration

---

## Dependencies

### Internal Dependencies
- Cache management system
- Media identity computation (audio fingerprinting)
- Quality metrics tracking

### External Dependencies
- Sufficient disk space for cache (~500MB per movie)

---

## Related Documents

- **TRD:** [TRD-2025-12-08-05-subtitle-workflow.md](../../trd/TRD-2025-12-08-05-subtitle-workflow.md)
- **Architectural Decision:** ARCHITECTURE.md § AD-014

---

## Approval

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | Ravi Patel | 2025-12-08 | ✅ Approved |

---

**Status:** Approved (Pending Implementation)
