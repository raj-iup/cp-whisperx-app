# Subtitle Workflow Integration Plan

**Created:** 2025-12-04  
**Status:** 🎯 ACTIVE  
**Priority:** CRITICAL - Mandatory features for subtitle workflow

---

## Problem Statement

Lyrics detection and hallucination removal are **MANDATORY** features for the subtitle workflow but were incorrectly categorized as "optional" stages (12, 13) during conflict resolution.

**Current State:**
- ✅ `12_lyrics_detection.py` exists (moved from 06)
- ✅ `13_hallucination_removal.py` exists (moved from 07)
- ❌ NOT integrated into subtitle workflow
- ❌ Subtitle workflow skips these critical steps

**Impact:**
- ❌ Song lyrics get translated (should be marked/skipped)
- ❌ ASR hallucinations remain in subtitles
- ❌ Poor subtitle quality for Bollywood content
- ❌ Fails to meet 88% quality target

---

## Correct Architecture

### Subtitle Workflow Pipeline (12 stages)

```
01_demux              → Extract audio
02_tmdb               → Fetch movie metadata
03_glossary_load      → Load character names
04_source_separation  → Separate dialogue (optional)
05_pyannote_vad       → Speech detection + diarization
06_whisperx_asr       → Transcribe with timestamps
07_alignment          → Refine word alignment
08_lyrics_detection   → 🆕 Mark song/lyrics segments (MANDATORY for subtitle)
09_hallucination_removal → 🆕 Clean ASR artifacts (MANDATORY for subtitle)
10_translation        → Multi-language translation
11_subtitle_generation → Generate SRT/VTT files
12_mux                → Embed subtitles in video
```

### Why These Are Mandatory

**Lyrics Detection (Stage 08):**
- Bollywood movies have 4-8 song sequences
- Lyrics should NOT be translated literally
- Need special handling (original + transliteration)
- Cultural significance of songs
- Timing needs adjustment (songs have different pacing)

**Hallucination Removal (Stage 09):**
- WhisperX hallucinates: "Thanks for watching", "Subscribe", repeated phrases
- Background music causes artifacts
- Silence generates nonsense text
- Critical for subtitle quality (88% target)

---

## Implementation Plan

### Phase 1: Restructure Stages (2 hours)

#### Task 1.1: Renumber Stages (1 hour)

**Current → New Mapping:**
```
01_demux.py              → 01_demux.py              (no change)
02_tmdb_enrichment.py    → 02_tmdb_enrichment.py   (no change)
03_glossary_load.py      → 03_glossary_load.py     (no change)
04_source_separation.py  → 04_source_separation.py (no change)
05_pyannote_vad.py       → 05_pyannote_vad.py      (no change)
06_whisperx_asr.py       → 06_whisperx_asr.py      (no change)
07_alignment.py          → 07_alignment.py         (no change)
08_translation.py        → 10_translation.py       (RENUMBER)
09_subtitle_generation.py → 11_subtitle_generation.py (RENUMBER)
10_mux.py                → 12_mux.py               (RENUMBER)
12_lyrics_detection.py   → 08_lyrics_detection.py  (INSERT)
13_hallucination_removal.py → 09_hallucination_removal.py (INSERT)
```

**Actions:**
```bash
# Backup first
git add -A && git commit -m "Pre-integration checkpoint"

# Rename in correct order (avoid conflicts)
git mv scripts/10_mux.py scripts/12_mux.py
git mv scripts/09_subtitle_generation.py scripts/11_subtitle_generation.py
git mv scripts/08_translation.py scripts/10_translation.py
git mv scripts/12_lyrics_detection.py scripts/08_lyrics_detection.py
git mv scripts/13_hallucination_removal.py scripts/09_hallucination_removal.py

# Verify
ls -1 scripts/*_*.py
```

#### Task 1.2: Update Stage Internal References (30 min)

**Update each renamed file:**

**File: `scripts/08_lyrics_detection.py`**
```python
# Change stage name reference
def run_stage(job_dir: Path, stage_name: str = "08_lyrics_detection") -> int:
    io = StageIO("08_lyrics_detection", job_dir, enable_manifest=True)
```

**File: `scripts/09_hallucination_removal.py`**
```python
# Change stage name reference
def run_stage(job_dir: Path, stage_name: str = "09_hallucination_removal") -> int:
    io = StageIO("09_hallucination_removal", job_dir, enable_manifest=True)
```

**File: `scripts/10_translation.py`** (if exists, or update 08_translation.py)
```python
# Change stage name reference
def run_stage(job_dir: Path, stage_name: str = "10_translation") -> int:
    io = StageIO("10_translation", job_dir, enable_manifest=True)
```

**File: `scripts/11_subtitle_generation.py`**
```python
# Change stage name reference
def run_stage(job_dir: Path, stage_name: str = "11_subtitle_generation") -> int:
    io = StageIO("11_subtitle_generation", job_dir, enable_manifest=True)
```

**File: `scripts/12_mux.py`**
```python
# Change stage name reference
def run_stage(job_dir: Path, stage_name: str = "12_mux") -> int:
    io = StageIO("12_mux", job_dir, enable_manifest=True)
```

#### Task 1.3: Update run-pipeline.py (30 min)

**Update all stage references:**

1. Update import statements
2. Update stage execution order
3. Update subtitle workflow stage list
4. Update config checks

```python
def run_subtitle_workflow(self) -> bool:
    """
    Execute subtitle workflow stages (12-stage pipeline):
    1. demux → 2. tmdb → 3. glossary → 4. source_sep → 5. vad
    6. asr → 7. alignment → 8. lyrics_detection → 9. hallucination_removal
    10. translation → 11. subtitle_gen → 12. mux
    """
    # ... implementation with all 12 stages
```

---

### Phase 2: Update Configuration (1 hour)

#### Task 2.1: Update config/.env.pipeline (30 min)

**Update stage number references:**
```bash
# Old (INCORRECT)
STAGE_06_LYRICS_ENABLED=true         # Wrong stage number
STAGE_07_HALLUCINATION_ENABLED=true  # Wrong stage number
STAGE_08_TRANSLATION_ENABLED=true    # Wrong stage number
STAGE_09_SUBTITLE_ENABLED=true       # Wrong stage number
STAGE_10_MUX_ENABLED=true            # Wrong stage number

# New (CORRECT)
STAGE_08_LYRICS_ENABLED=true         # Lyrics detection (MANDATORY for subtitle)
STAGE_09_HALLUCINATION_ENABLED=true  # Hallucination removal (MANDATORY for subtitle)
STAGE_10_TRANSLATION_ENABLED=true    # Translation
STAGE_11_SUBTITLE_ENABLED=true       # Subtitle generation
STAGE_12_MUX_ENABLED=true            # Mux subtitles
```

**Add workflow-specific enforcement:**
```bash
# Subtitle Workflow - Mandatory Stages
# These stages CANNOT be disabled in subtitle workflow
SUBTITLE_WORKFLOW_MANDATORY_LYRICS=true       # Force lyrics detection
SUBTITLE_WORKFLOW_MANDATORY_HALLUCINATION=true # Force hallucination removal
```

#### Task 2.2: Update Documentation (30 min)

**Files to update:**
- `docs/user-guide/workflows.md` - Update subtitle workflow pipeline
- `docs/developer/DEVELOPER_STANDARDS.md` - Update canonical pipeline
- `.github/copilot-instructions.md` - Update § 1.5 subtitle workflow
- `IMPLEMENTATION_TRACKER.md` - Update completion status

---

### Phase 3: Integration Testing (2 hours)

#### Task 3.1: Unit Test Each Stage (30 min)

```bash
# Test lyrics detection
python3 scripts/08_lyrics_detection.py <job_dir>

# Test hallucination removal
python3 scripts/09_hallucination_removal.py <job_dir>

# Verify outputs exist and are valid
```

#### Task 3.2: Integration Test - Subtitle Workflow (1.5 hours)

**Test with Bollywood sample:**
```bash
# Prepare job
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es

# Run full pipeline
./run-pipeline.sh --job-dir out/LATEST

# Verify all 12 stages executed
# Verify lyrics marked correctly
# Verify hallucinations removed
# Verify subtitle quality ≥88%
```

**Quality Checks:**
1. Verify song sequences marked with lyrics flag
2. Verify hallucinations removed (no "Thanks for watching", etc.)
3. Verify subtitle timing accurate (±200ms)
4. Verify all target languages generated
5. Verify muxed video has all subtitle tracks

---

### Phase 4: Update Documentation (1 hour)

#### Task 4.1: Update CANONICAL_PIPELINE.md

```markdown
## Core 12-Stage Subtitle Pipeline

**Stages 01-07:** Universal (all workflows)
- 01_demux, 02_tmdb, 03_glossary_load, 04_source_separation
- 05_pyannote_vad, 06_whisperx_asr, 07_alignment

**Stages 08-09:** Subtitle Workflow MANDATORY
- 08_lyrics_detection - Mark song/lyrics segments
- 09_hallucination_removal - Clean ASR artifacts

**Stages 10-12:** Subtitle Workflow Only
- 10_translation - Multi-language translation
- 11_subtitle_generation - Generate SRT/VTT
- 12_mux - Embed subtitles in video

**Optional Stages:**
- 11_ner (Named Entity Recognition) - Experimental
```

#### Task 4.2: Update Workflow Documentation

**Update copilot-instructions.md § 1.5:**
```markdown
### 1. Subtitle Workflow
**Purpose:** Generate context-aware multilingual subtitles for Bollywood/Indic media

**Pipeline:** demux → tmdb → glossary_load → source_sep → pyannote_vad 
→ whisperx_asr → alignment → **lyrics_detection** → **hallucination_removal** 
→ translate → subtitle_gen → mux

**Mandatory Features:**
- ✅ Lyrics detection (stage 08) - Cannot be disabled
- ✅ Hallucination removal (stage 09) - Cannot be disabled
```

---

## Timeline

| Phase | Tasks | Duration | Assignee | Status |
|-------|-------|----------|----------|--------|
| 1. Restructure Stages | 1.1-1.3 | 2 hours | Dev | ⏳ Not Started |
| 2. Configuration | 2.1-2.2 | 1 hour | Dev | ⏳ Not Started |
| 3. Testing | 3.1-3.2 | 2 hours | Dev | ⏳ Not Started |
| 4. Documentation | 4.1-4.2 | 1 hour | Dev | ⏳ Not Started |
| **TOTAL** | | **6 hours** | | **0%** |

---

## Success Criteria

- [ ] All stages renumbered correctly (01-12)
- [ ] Lyrics detection integrated at stage 08
- [ ] Hallucination removal integrated at stage 09
- [ ] Subtitle workflow executes all 12 stages
- [ ] Config updated with correct stage numbers
- [ ] Documentation updated (all files)
- [ ] Integration test passes with jaane_tu sample
- [ ] Subtitle quality ≥88%
- [ ] Lyrics correctly marked
- [ ] Hallucinations removed
- [ ] All target languages generated

---

## Notes

**Key Design Decisions:**

1. **Why after alignment?**
   - Need word-level timestamps before lyrics detection
   - Hallucination removal benefits from aligned text
   
2. **Why before translation?**
   - Don't translate lyrics (or translate specially)
   - Don't waste translation on hallucinations
   
3. **Why mandatory?**
   - Bollywood content ALWAYS has songs
   - WhisperX ALWAYS produces some hallucinations
   - Quality target (88%) impossible without these

**Optional Stages:**
- Stage 11_ner (Named Entity Recognition) - Remains optional/experimental
- Not needed for subtitle workflow

---

**Status:** Ready for implementation  
**Priority:** CRITICAL  
**Estimated Time:** 6 hours  
**Blocking:** v3.0 completion
