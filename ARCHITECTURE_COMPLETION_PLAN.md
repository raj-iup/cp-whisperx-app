# Architecture Completion Plan - v3.0 Final Push

**Date:** 2025-12-04  
**Status:** 🎯 EXECUTION READY  
**Goal:** Complete v3.0 architecture in 3 days (24 work hours)  
**Current State:** 95% complete → Target: 100%

---

## Executive Summary

The architecture is **95% complete** but documentation is severely outdated. This plan will:

1. ✅ Audit and consolidate all code (8 hours)
2. ✅ Rewrite architecture documentation (6 hours)
3. ✅ Test all workflows end-to-end (6 hours)
4. ✅ Clean up artifacts and align standards (4 hours)

**Total Effort:** 24 hours (3 days)  
**Result:** Production-ready v3.0 architecture with accurate documentation

---

## Current State Analysis

### What's Actually Done (95%)

✅ **StageIO Pattern:** 93.75% adoption (15/16 files) → Will be 100%  
✅ **Stage Files:** 16 exist across all 10 stages  
✅ **Shared Modules:** 21 modules including 3 Phase 5 modules  
✅ **Phase 5 Features:** Context-aware modules implemented  
✅ **Code Quality:** 100% compliance  
✅ **Multi-Environment:** MLX/CUDA/CPU routing works

### What Needs Fixing (5%)

⏭️ **File Consolidation:** 16 files → 10 canonical (6 duplicates/variants)  
⏭️ **Stage Conflicts:** Resolve numbers 05, 06, 07 (2 files each)  
⏭️ **Documentation:** Rewrite roadmap, update standards  
⏭️ **Testing:** End-to-end workflow validation  
⏭️ **Cleanup:** Archive deprecated files

---

## Phase 1: Code Audit & Consolidation (8 hours)

### Task 1.1: Resolve Stage Conflicts (4 hours)

**Issue:** Stages 05, 06, 07 each have 2 different purposes

#### Stage 05: NER vs PyAnnote VAD
```bash
Current:
  05_ner.py (Named Entity Recognition)
  05_pyannote_vad.py (Voice Activity Detection)

Decision: Keep 05_pyannote_vad.py (critical), move NER to 11_ner.py

Actions:
  git mv scripts/05_ner.py scripts/11_ner.py
  Update references in pipeline
  
Reason: VAD is critical for ASR, NER is optional/experimental
```

#### Stage 06: Lyrics vs WhisperX ASR
```bash
Current:
  06_lyrics_detection.py
  06_whisperx_asr.py (ASR transcription)

Decision: Keep 06_whisperx_asr.py (core), move lyrics to 12_lyrics_detection.py

Actions:
  git mv scripts/06_lyrics_detection.py scripts/12_lyrics_detection.py
  
Reason: ASR is core functionality, lyrics is optional
```

#### Stage 07: Hallucination vs Alignment
```bash
Current:
  07_hallucination_removal.py
  07_alignment.py (Word-level timing)

Decision: Keep 07_alignment.py (critical), move hallucination to 13_hallucination_removal.py

Actions:
  git mv scripts/07_hallucination_removal.py scripts/13_hallucination_removal.py
  
Reason: Alignment needed for subtitles, hallucination is post-processing
```

### Task 1.2: Consolidate Duplicates (2 hours)

#### Stage 03: Glossary (3 files → 1 file)
```bash
Current:
  03_glossary_load.py
  03_glossary_loader.py
  03_glossary_learner.py

Actions:
  1. Compare all 3 files
  2. Pick canonical: 03_glossary_load.py
  3. Archive others:
     mkdir -p archive/stage_variants/
     git mv scripts/03_glossary_loader.py archive/stage_variants/
     git mv scripts/03_glossary_learner.py archive/stage_variants/
  4. Ensure canonical has StageIO
```

#### Stage 09: Subtitle Generation (2 files → 1 file)
```bash
Current:
  09_subtitle_generation.py
  09_subtitle_gen.py

Actions:
  1. Compare files
  2. Pick canonical: 09_subtitle_generation.py (full name)
  3. Archive:
     git mv scripts/09_subtitle_gen.py archive/stage_variants/
```

### Task 1.3: Create CANONICAL_PIPELINE.md (2 hours)

Document the authoritative pipeline:

```markdown
# Canonical Pipeline Definition v3.0

## Core Pipeline (10 stages - Always in this order)

01. **01_demux.py** - Audio extraction from media
02. **02_tmdb_enrichment.py** - Context metadata (subtitle workflow only)
03. **03_glossary_load.py** - Load glossary terms
04. **04_source_separation.py** - Vocal extraction (optional)
05. **05_pyannote_vad.py** - Voice activity detection
06. **06_whisperx_asr.py** - ASR transcription (CRITICAL)
07. **07_alignment.py** - Word-level timing
08. **08_translation.py** - Translation (translate/subtitle workflows)
09. **09_subtitle_generation.py** - Subtitle generation (subtitle workflow)
10. **10_mux.py** - Final muxing (subtitle workflow)

## Optional Stages (11+)

11. **11_ner.py** - Named entity recognition (experimental)
12. **12_lyrics_detection.py** - Lyrics detection (experimental)
13. **13_hallucination_removal.py** - Post-processing (experimental)

## Workflow Execution

**Transcribe:** 01 → 03 → 04? → 05 → 06 → 07  
**Translate:** 01 → 03 → 04? → 05 → 06 → 07 → 08  
**Subtitle:** 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10

## Archived Files (Do Not Use)

- archive/stage_variants/03_glossary_loader.py
- archive/stage_variants/03_glossary_learner.py
- archive/stage_variants/09_subtitle_gen.py
```

**Deliverable:** Clean 10-stage pipeline + 3 optional

---

## Phase 2: Documentation Rewrite (6 hours)

### Task 2.1: Rewrite ARCHITECTURE_IMPLEMENTATION_ROADMAP.md (3 hours)

**Change Log:**

| Section | Old Claim | New Reality | Change |
|---------|-----------|-------------|--------|
| Version | v2.0 (55%) | v2.9 (95%) | +40% |
| StageIO | 10% adoption | 100% adoption | +90% |
| Stage Files | 5 exist | 10 canonical | +5 |
| Phase 3 | In Progress | 100% Complete | Done |
| Phase 5 | Blocked, 0% | 26% Complete | Started |

**New Structure:**
```markdown
# Architecture Implementation Roadmap v4.0

**Current:** v2.9 (95% complete)  
**Target:** v3.0 (100% complete)  
**Timeline:** 3 days

## What's Done

✅ All 10 core stages implemented  
✅ 100% StageIO adoption  
✅ 21 shared modules (including Phase 5)  
✅ Phase 5: Context-aware modules (3/3 critical)  
✅ Code quality: 100% compliance

## What's Left

⏭️ Testing: End-to-end workflows (6h)  
⏭️ Documentation: Final alignment (4h)  
⏭️ Cleanup: Archive deprecated files (2h)

**Total Remaining:** 12 hours
```

### Task 2.2: Update DEVELOPER_STANDARDS.md (1 hour)

Add sections:
- § 1.8 Canonical Pipeline (stage list)
- § 1.9 Context-Aware Modules (Phase 5)

```markdown
## § 1.8 Canonical Pipeline

All stages MUST use canonical files from CANONICAL_PIPELINE.md:

Core: 01-10 (numbered)  
Optional: 11+ (numbered)  
Archived: archive/stage_variants/ (DO NOT USE)

## § 1.9 Context-Aware Modules (Phase 5)

Available:
- shared/bias_window_generator.py - ASR prompting (+58% char accuracy)
- shared/mps_utils.py - Apple Silicon optimization
- shared/asr_chunker.py - Large file processing (4hr+ support)

When to use:
- Bias windows: Subtitle workflow with glossary
- MPS utils: Always on Apple Silicon (automatic)
- ASR chunker: Files >1 hour or memory constrained
```

### Task 2.3: Update copilot-instructions.md (1 hour)

Add to checklist:
```markdown
**CANONICAL PIPELINE compliance:**
- [ ] Uses canonical file (see CANONICAL_PIPELINE.md)
- [ ] Not referencing archived files
- [ ] Stage number matches purpose
```

Add summary sections:
- § 1.8 Canonical Pipeline (brief)
- § 1.9 Context-Aware Modules (brief)

### Task 2.4: Update User Documentation (1 hour)

**Files to update:**
- docs/user-guide/workflows.md - Add canonical stages
- docs/user-guide/installation.md - Update if needed
- README.md - Update version to v2.9→v3.0

---

## Phase 3: End-to-End Testing (6 hours)

### Task 3.1: Test Transcribe Workflow (2 hours)

**Sample 1: English Technical**
```bash
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

# Expected:
# - 07_alignment/transcript.txt
# - ASR WER ≤5%
# - Time <3 minutes

# Validation:
python3 tests/integration/validate_transcribe.py
```

**Sample 2: Hinglish Bollywood**
```bash
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow transcribe \
  --source-language hi

# Expected:
# - 07_alignment/transcript.txt (Hindi)
# - ASR WER ≤15%
# - Character names correct
```

### Task 3.2: Test Translate Workflow (2 hours)

```bash
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow translate \
  --source-language hi \
  --target-language en

# Expected:
# - 08_translation/transcript_en.txt
# - Translation BLEU ≥90%
# - Glossary terms preserved
```

### Task 3.3: Test Subtitle Workflow (2 hours)

```bash
./prepare-job.sh \
  --media "in/test_clips/jaane_tu_test_clip.mp4" \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es

# Expected:
# - 10_mux/{media}.mkv with soft-embedded subtitles
# - Multiple tracks (hi, en, gu, ta, es)
# - Quality ≥88%

# Validation:
ffprobe -show_streams out/.../10_mux/*/output.mkv
```

**Deliverable:** `tests/integration/WORKFLOW_TEST_REPORT.md`

---

## Phase 4: Cleanup & Alignment (4 hours)

### Task 4.1: Remove Deprecated Artifacts (1 hour)

```bash
# Create cleanup script
./scripts/cleanup_deprecated.sh

# Actions:
# 1. Archive stage variants
mkdir -p archive/stage_variants/
mv scripts/{variants} archive/stage_variants/

# 2. Archive obsolete docs
mkdir -p archive/docs_obsolete/
mv docs/PHASE*.md archive/docs_obsolete/
mv PHASE*.md archive/docs_obsolete/

# 3. Clean __pycache__
find . -name "__pycache__" -type d -exec rm -rf {} +

# 4. Remove .bak files
find scripts -name "*.bak*" -delete

# 5. Clean old logs
find logs -mtime +30 -delete
```

### Task 4.2: Update .gitignore (30 min)

Add:
```
archive/
*.bak*
*.tmp
out/*/
__pycache__/
```

### Task 4.3: Verify Documentation Alignment (1.5 hours)

```python
# Create verification script
python3 scripts/verify_docs.py

# Checks:
# 1. No references to deprecated files
# 2. Phase 5 modules documented
# 3. StageIO claims accurate (100%)
# 4. Canonical pipeline referenced correctly
```

### Task 4.4: Final Checklist (1 hour)

```markdown
# v3.0 Completion Checklist

## Code
- [ ] 10 canonical core stages
- [ ] 100% StageIO adoption
- [ ] No duplicate stage files
- [ ] Optional stages moved to 11+
- [ ] Deprecated files archived

## Documentation
- [ ] CANONICAL_PIPELINE.md created
- [ ] Roadmap v4.0 complete
- [ ] DEVELOPER_STANDARDS.md updated
- [ ] copilot-instructions.md updated
- [ ] No deprecated references

## Testing
- [ ] Transcribe tested (2 samples)
- [ ] Translate tested
- [ ] Subtitle tested
- [ ] Quality targets met
- [ ] Test report complete

## Cleanup
- [ ] Artifacts archived
- [ ] __pycache__ cleaned
- [ ] .bak files removed
- [ ] .gitignore updated

## Verification
- [ ] verify_docs.py passes
- [ ] validate-compliance.py passes
- [ ] All tests pass

## Sign-off
- [ ] Ready for v3.0 release
```

---

## Timeline

**Day 1 (8 hours):**
- Phase 1: Code consolidation (8h)

**Day 2 (8 hours):**
- Phase 2: Documentation (6h)
- Phase 3: Testing start (2h)

**Day 3 (8 hours):**
- Phase 3: Testing complete (4h)
- Phase 4: Cleanup (4h)

**Total:** 24 hours

---

## Success Criteria

✅ StageIO: 100% (10/10 core stages)  
✅ Canonical Pipeline: Documented and enforced  
✅ All workflows: Tested and passing  
✅ Quality targets: Met (90% ASR, 88% subtitles)  
✅ Documentation: 100% accurate and aligned  
✅ Repository: Clean, no deprecated files

---

## Deliverables

### Code
1. 10 canonical core stage files (01-10)
2. 3 optional stage files (11-13)
3. Clean scripts/ directory (no variants)

### Documentation
1. CANONICAL_PIPELINE.md
2. ARCHITECTURE_IMPLEMENTATION_ROADMAP.md v4.0
3. DEVELOPER_STANDARDS.md (§1.8, §1.9)
4. copilot-instructions.md (§1.8, §1.9)
5. ARCHITECTURE_COMPLETION_PLAN.md (this doc)

### Testing
1. Integration test suite
2. Workflow test report
3. Quality metrics validation

### Cleanup
1. archive/stage_variants/ (deprecated files)
2. archive/docs_obsolete/ (historical docs)
3. Clean logs and cache

---

## Post-Completion Actions

### Immediate
1. Tag v3.0 release
2. Update README.md
3. Announce to team

### Week 1
4. User beta testing
5. Bug fixes
6. Performance tuning

### Month 1
7. Production deployment
8. Monitor metrics
9. Phase 6 planning (optional)

---

## Conclusion

This plan completes v3.0 architecture in **3 days**:

**95% → 100%** completion  
**Clean codebase** with 10 canonical stages  
**Accurate documentation** reflecting reality  
**Tested workflows** meeting quality targets  
**Production-ready** architecture

After completion, CP-WhisperX will have:
- ✅ World-class context-aware subtitle generation
- ✅ Production-ready reliability and performance
- ✅ Comprehensive documentation and testing
- ✅ Clean, maintainable codebase

**Let's finish strong! 🚀**

---

**Status:** ✅ Ready for Execution  
**Created:** 2025-12-04  
**Owner:** Development Team  
**Next Action:** Begin Phase 1
