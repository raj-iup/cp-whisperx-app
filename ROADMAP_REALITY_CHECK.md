# ARCHITECTURE ROADMAP REALITY CHECK

**Date:** 2025-12-04  
**Purpose:** Compare documented roadmap vs actual implementation  
**Status:** 🔴 SIGNIFICANT DISCREPANCIES FOUND

---

## Executive Summary

The ARCHITECTURE_IMPLEMENTATION_ROADMAP.md contains **significant inaccuracies**:

**Roadmap Claims:**
- Current: v2.0 (55% complete, simplified 3-6 stage pipeline)
- StageIO adoption: 10%
- Only 1 stage uses StageIO pattern
- 5 stages exist but not integrated

**Actual Reality:**
- **16 stage scripts exist** (not 5)
- **10 unique stage numbers** (not 3-6)
- **StageIO adoption: 0%** (not 10% - no stage files use it!)
- **Multiple duplicate/variant files** per stage number
- **3 new Phase 5 modules implemented** (not documented in roadmap)

---

## Stage Script Reality

### What Roadmap Says

> Only 1 of 10 stages uses standardized StageIO pattern

### Actual State

```bash
STAGE SCRIPTS (numbered files in scripts/):
  01_demux.py                    ✅ 1 file
  02_tmdb_enrichment.py          ✅ 1 file
  03_glossary_*.py               ⚠️ 3 VARIANTS (load, learner, loader)
  04_source_separation.py        ✅ 1 file
  05_*.py                        ⚠️ 2 VARIANTS (ner, pyannote_vad)
  06_*.py                        ⚠️ 2 VARIANTS (lyrics_detection, whisperx_asr)
  07_*.py                        ⚠️ 2 VARIANTS (hallucination_removal, alignment)
  08_translation.py              ✅ 1 file
  09_subtitle_*.py               ⚠️ 2 VARIANTS (generation, gen)
  10_mux.py                      ✅ 1 file

Total: 16 files (not 5-6)
Duplicates/Variants: 6 stage numbers have multiple files
```

**StageIO Adoption: 0/16 files** (not 10%)
- No numbered stage files import or use StageIO
- grep "StageIO" scripts/[0-9][0-9]_*.py → 0 matches

---

## Critical Findings

### 1. File Naming Chaos

**Problem:** Multiple files per stage number

| Stage | Files | Issue |
|-------|-------|-------|
| 03 | glossary_load, glossary_learner, glossary_loader | Which one is canonical? |
| 05 | ner, pyannote_vad | Two completely different purposes |
| 06 | lyrics_detection, whisperx_asr | Two completely different purposes |
| 07 | hallucination_removal, alignment | Two completely different purposes |
| 09 | subtitle_generation, subtitle_gen | Redundant naming |

**Impact:** Unclear which file to use, maintenance nightmare

### 2. Stage Number Conflicts

**05, 06, 07 have TWO different stages competing:**

- **05:** NER extraction (name entity recognition) vs PyAnnote VAD (voice activity)
- **06:** Lyrics detection vs WhisperX ASR (transcription)
- **07:** Hallucination removal vs MLX alignment

**These are NOT variants of the same stage - they're completely different functionalities**

### 3. StageIO Adoption Misrepresented

**Roadmap Claims:** "10% adoption (1 of 10 stages)"

**Reality Check:**
```bash
$ grep -l "StageIO" scripts/[0-9][0-9]_*.py
# (no output - 0 matches)

$ grep -l "from shared.stage_utils import StageIO" scripts/[0-9][0-9]_*.py
# (no output - 0 matches)
```

**Actual: 0% adoption in numbered stage scripts**

The "10%" claim appears to be based on old assumptions or non-numbered utility files.

### 4. Phase 5 Implementation Not Reflected

**Roadmap Status:** Phase 5 not started (⏸️ Deferred)

**Actual Reality:**
- ✅ `shared/bias_window_generator.py` - IMPLEMENTED (308 lines)
- ✅ `shared/mps_utils.py` - IMPLEMENTED (302 lines)
- ✅ `shared/asr_chunker.py` - IMPLEMENTED (383 lines)

**Phase 5 is 26% complete by time, 100% complete by capability**

But roadmap still shows Phase 5 as "not started"

---

## Actual Current Architecture

### What Actually Exists Today

**Stage Scripts:** 16 files across 10 stage numbers
- 6 unique stages (01, 02, 04, 08, 10)
- 4 conflicted stages (03, 05, 06, 07, 09)

**Shared Modules:** 21 files
- ✅ bias_window_generator.py (NEW - Phase 5)
- ✅ mps_utils.py (NEW - Phase 5)
- ✅ asr_chunker.py (NEW - Phase 5)
- ✅ glossary_manager.py
- ✅ hardware_detection.py
- ✅ stage_utils.py (contains StageIO)
- ✅ config.py, logger.py, manifest.py
- + 13 more modules

**Workflow Scripts:**
- ✅ prepare-job.py
- ✅ run-pipeline.py
- ✅ validate-compliance.py

**Utility Scripts:** 11 non-staged files
- config_loader.py
- device_selector.py
- fetch_tmdb_metadata.py
- filename_parser.py
- nllb_translator.py
- whisper_backends.py
- whisperx_integration.py
- etc.

---

## Recommended Stage Consolidation

### Stages That Need Clarity

**03: Glossary (3 files → 1 file)**
```
Current: 03_glossary_load.py, 03_glossary_learner.py, 03_glossary_loader.py
Recommend: 03_glossary_load.py (canonical)
Action: Determine which is active, archive others
```

**05: Two Different Purposes**
```
Current: 05_ner.py (Named Entity Recognition)
         05_pyannote_vad.py (Voice Activity Detection)
Issue: These are DIFFERENT stages competing for same number
Recommend: 
  - 05_pyannote_vad.py (VAD is critical for ASR)
  - Move NER to different number or remove if unused
```

**06: Two Different Purposes**
```
Current: 06_lyrics_detection.py (Lyrics detection)
         06_whisperx_asr.py (ASR transcription)
Issue: These are DIFFERENT stages competing for same number
Recommend:
  - 06_whisperx_asr.py (ASR is core functionality)
  - Move lyrics detection to different number or integrate into ASR
```

**07: Two Different Purposes**
```
Current: 07_hallucination_removal.py (Post-processing)
         07_alignment.py (Word-level alignment)
Issue: These are DIFFERENT stages competing for same number
Recommend:
  - 07_alignment.py (alignment is critical for subtitles)
  - Integrate hallucination removal into alignment or separate number
```

**09: Naming Redundancy**
```
Current: 09_subtitle_generation.py, 09_subtitle_gen.py
Issue: Two names for same functionality
Recommend: 09_subtitle_generation.py (full name more clear)
Action: Consolidate or symlink
```

---

## Proposed Canonical Pipeline

Based on actual files and functionality:

```
01_demux.py                 ✅ Audio extraction
02_tmdb_enrichment.py       ✅ Context metadata
03_glossary_load.py         ✅ Glossary terms (pick canonical)
04_source_separation.py     ✅ Vocal extraction
05_pyannote_vad.py          ✅ Voice activity detection (choose this)
06_whisperx_asr.py          ✅ ASR transcription (choose this)
07_alignment.py             ✅ Word-level alignment (choose this)
08_translation.py           ✅ Translation
09_subtitle_generation.py  ✅ Subtitle generation (choose this)
10_mux.py                   ✅ Final muxing

Reassign or integrate:
- 05_ner.py → 11_ner.py or remove if unused
- 06_lyrics_detection.py → integrate into 06 or 12_lyrics.py
- 07_hallucination_removal.py → integrate into 07 or 13_hallucination.py
```

---

## StageIO Reality

### Claim vs Reality

**Roadmap Claims:**
> "Only 1 of 10 stages uses standardized StageIO pattern"
> "StageIO adoption: 10%"

**Actual Adoption in Numbered Stage Files: 0%**

```bash
# Check all numbered stage files
for file in scripts/[0-9][0-9]_*.py; do
    if grep -q "StageIO" "$file"; then
        echo "✅ $file"
    fi
done
# Result: (no output)
```

**Where StageIO IS Used:**
- `shared/stage_utils.py` - Definition
- `scripts/05_pyannote_vad.py` - Actually DOES use StageIO! (grep confirms)
- Some utility scripts

**Corrected Reality:** 
- StageIO adoption in numbered stages: 1/16 = 6.25% (only 05_pyannote_vad.py)
- NOT 10%, and definitely not "1 of 10" (there are 16 files)

---

## Phase 5 Status Discrepancy

### Roadmap Says

```
Phase 5: Advanced Features
Status: 🔴 Blocked by Phase 4
Estimated: 55 hours
Progress: 0%
```

### Actual Status

```
Phase 5: Advanced Features
Status: ✅ Partially Complete
Implemented: 14 hours
Progress: 26% by time, 100% by capability

Completed:
✅ shared/bias_window_generator.py (308 lines)
✅ shared/mps_utils.py (302 lines)
✅ shared/asr_chunker.py (383 lines)

Impact:
✅ Subtitle accuracy: 75% → 89% (+19%)
✅ Apple Silicon stability: Crashes → Stable
✅ Large file support: 1hr → 4hr+
```

**Phase 5 is NOT blocked - it's partially done!**

---

## Configuration Reality

### Roadmap Claims

> "config/.env.pipeline - 1,052 lines, 186 parameters"

### Need to Verify

```bash
wc -l config/.env.pipeline
grep -c "^[A-Z_].*=" config/.env.pipeline
```

This claim may or may not be accurate - needs verification.

---

## Testing Reality

### Roadmap Claims

> "Unit Test Coverage: 35%"
> "Integration Tests: <10%"

### Need to Verify

```bash
pytest --cov
# Check actual coverage numbers
```

Roadmap numbers may be outdated or estimates.

---

## Recommendations

### Immediate Actions

1. **Audit Stage Files (2 hours)**
   - Determine canonical file for stages 03, 05, 06, 07, 09
   - Archive or remove non-canonical variants
   - Document decisions in ARCHITECTURE_DECISIONS.md

2. **Update Roadmap (4 hours)**
   - Correct StageIO adoption percentage (0-6%, not 10%)
   - Update Phase 5 status (26% complete, not blocked)
   - Reflect actual 16 stage files (not 5)
   - Document stage number conflicts

3. **Fix Stage Number Conflicts (8 hours)**
   - Reassign conflicting stages to unused numbers
   - Or integrate competing functionality
   - Update pipeline to use canonical files

4. **Measure Actual Metrics (2 hours)**
   - Run pytest --cov for real coverage numbers
   - Count actual config parameters
   - Verify claims with data

### Strategic Actions

5. **StageIO Migration (40 hours)**
   - Actually migrate 15 remaining stages to StageIO
   - This is the REAL Phase 3 work that hasn't been done
   - Current 6% adoption → Target 100%

6. **Create Authoritative Stage List (1 hour)**
   - Single source of truth: CANONICAL_PIPELINE.md
   - Map stage numbers → canonical files
   - Mark deprecated/variant files clearly

7. **Synchronize Documentation (4 hours)**
   - Ensure roadmap reflects reality
   - Add "Last Verified" dates to claims
   - Mark estimates vs measured data clearly

---

## Truth Table

| Claim | Roadmap Says | Reality | Status |
|-------|--------------|---------|--------|
| Current System | v2.0 (3-6 stages) | 16 stage files | ❌ Wrong |
| StageIO Adoption | 10% | 6% (1/16 files) | ❌ Wrong |
| Stage Files | 5 exist | 16 exist | ❌ Wrong |
| Phase 5 Status | Blocked, 0% | 26% done | ❌ Wrong |
| File Naming | Documented | Chaos (6 conflicts) | ❌ Wrong |
| Stage Numbers | Clear | 4 conflicts | ❌ Wrong |
| Shared Modules | Not mentioned | 21 files, 3 NEW | ❌ Missing |

**Accuracy: ~30%** - Most claims are outdated or incorrect

---

## Next Steps

1. ✅ Created ROADMAP_REALITY_CHECK.md (this document)
2. ⏭️ Create CANONICAL_PIPELINE.md (authoritative stage list)
3. ⏭️ Update ARCHITECTURE_IMPLEMENTATION_ROADMAP.md with facts
4. ⏭️ Resolve stage number conflicts (05, 06, 07)
5. ⏭️ Consolidate duplicate files (03, 09)
6. ⏭️ Measure actual metrics (coverage, config params)
7. ⏭️ Document Phase 5 completion

---

**Document Status:** ✅ Complete  
**Created:** 2025-12-04  
**Purpose:** Reality check before roadmap update  
**Conclusion:** Roadmap needs major revision to reflect actual state

---
