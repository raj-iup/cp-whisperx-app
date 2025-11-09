# CP-WhisperX-App vs IMPROVEMENT-PLAN.md - Gap Analysis
**Date**: November 9, 2025  
**Status**: Current Implementation Analysis

---

## Executive Summary

The **CP-WhisperX-App** project implements approximately **85-90%** of the improvement plan's vision with strong fundamentals in pipeline architecture, VAD/ASR/diarization, and automation. The main gaps are in:
1. **Glossary/terminology management** (human-editable TSV system)
2. **Human-in-the-loop QA workflow** (reviewer tools)
3. **Advanced post-editing rules** (context-aware NLG)
4. **Per-film memory/prompts** (catchphrase tracking)

---

## Implementation Status by Section

### ✅ Step 1: Goals & Success Criteria (95% COMPLETE)

**Implemented**:
- ✅ Subtitle readability targets configured
  - `SUBTITLE_MAX_LINE_LENGTH=42`
  - `SUBTITLE_MAX_LINES=2`
  - `SUBTITLE_MAX_DURATION=7.0`
- ✅ Quality metrics tracking in logs
- ✅ Performance optimization (GPU acceleration, MPS support)

**Gaps**:
- ⚠️ CPS (characters per second) target not enforced at 15 (cap 17)
- ⚠️ MER (Mixed Error Rate) not actively measured
- ⚠️ No JSON metrics config file as specified

**Evidence**:
```python
# shared/config.py (lines 124-130)
subtitle_max_line_length: int = Field(default=42)
subtitle_max_lines: int = Field(default=2)
subtitle_max_duration: float = Field(default=7.0)
subtitle_merge_short: bool = Field(default=True)
```

---

### ✅ Step 2: Film Curation (80% COMPLETE)

**Implemented**:
- ✅ TMDB integration for metadata (`docker/tmdb/`)
- ✅ Job-based organization (`out/YYYY/MM/DD/USER/JOBID/`)
- ✅ Supports 1990s & 2000s Bollywood films

**Gaps**:
- ⚠️ No curated film catalog YAML
- ⚠️ No per-film notes/prompts system
- ⚠️ Manual job creation (no batch processing)

**Recommendation**:
Create `config/film_catalog.yaml`:
```yaml
catalog:
  - title: "Jaane Tu Ya Jaane Na"
    year: 2008
    tmdb_id: 12345
    notes: "Friend-group colloquialisms; Mumbai urban youth"
    prompts_file: "glossary/prompts/jaane_tu.txt"
```

---

### ✅ Step 3: Data Acquisition & Preparation (100% COMPLETE) ⭐

**Implemented**:
- ✅ `docker/demux/demux.py` - Audio extraction
  ```python
  '-ar', '16000',  # 16kHz sample rate
  '-ac', '1',      # Mono
  '-c:a', 'pcm_s16le'
  ```
- ✅ Loudness normalization optional
- ✅ Mono downmix
- ✅ Multiple format support

**Perfect alignment with plan!**

---

### ✅ Step 4: Pipeline Overview (95% COMPLETE)

**Implemented**:
- ✅ 12-stage pipeline (exceeds plan's requirements)
  1. Demux
  2. TMDB metadata
  3. Pre-ASR NER
  4. Silero VAD
  5. PyAnnote VAD
  6. Diarization
  7. ASR (WhisperX)
  8. Second-pass translation ⭐ (bonus)
  9. Lyrics detection ⭐ (bonus)
  10. Post-NER
  11. Subtitle generation
  12. Mux

**Gaps**:
- ⚠️ No explicit "fast path" vs "polish path" toggle
- ⚠️ Word alignment part of ASR (not separate explicit stage)

**Evidence**: `scripts/pipeline.py` orchestrates all stages with native/Docker execution

---

### ✅ Step 5: Implementation Details (90% COMPLETE)

#### 5.1 VAD (100% COMPLETE) ⭐
**Implemented**:
- ✅ Silero VAD (`docker/silero-vad/`)
- ✅ PyAnnote VAD (`docker/pyannote-vad/`)
- ✅ Configurable thresholds
- ✅ Both stages can be toggled

**Perfect implementation!**

```python
# Config from .env
SILERO_THRESHOLD=0.6
SILERO_MIN_SPEECH_DURATION_MS=250
SILERO_MIN_SILENCE_DURATION_MS=300
PYANNOTE_ONSET=0.5
PYANNOTE_OFFSET=0.5
```

#### 5.2 Diarization (95% COMPLETE)
**Implemented**:
- ✅ PyAnnote diarization (`docker/diarization/`)
- ✅ Auto speaker mapping from TMDB cast
- ✅ Configurable min/max speakers
- ✅ **FIX APPLIED**: Dict format handling (Nov 9, 2025)

**Gaps**:
- ⚠️ No explicit "escalation rule" for overlap detection
- ⚠️ Manual speaker map via `SPEAKER_MAP` env var (not per-film config)

#### 5.3 ASR + Translate (100% COMPLETE) ⭐
**Implemented**:
- ✅ WhisperX with `task=translate` mode
- ✅ Large-v3 model support
- ✅ Initial prompts supported via `WHISPER_INITIAL_PROMPT`
- ✅ Comprehensive Whisper parameters:
  ```python
  whisper_temperature: "0.0,0.2,0.4,0.6,0.8,1.0"
  whisper_beam_size: 5
  whisper_patience: 1.0
  whisper_length_penalty: 1.0
  ```

**Perfect implementation!**

#### 5.4 Word Alignment (100% COMPLETE) ⭐
**Implemented**:
- ✅ WhisperX aligner integrated
- ✅ `WHISPERX_ALIGN_EXTEND=2.0`
- ✅ `WHISPERX_ALIGN_FROM_PREV=true`

#### 5.5 Context-Aware Post-Editing (60% COMPLETE)
**Implemented**:
- ✅ Post-NER entity correction (`docker/post-ner/`)
- ✅ TMDB character matching
- ✅ **BONUS**: Second-pass translation with NLLB
- ✅ **BONUS**: Lyrics detection

**Gaps**: ⚠️⚠️⚠️
- ❌ **No glossary system** (Hinglish→English TSV)
- ❌ No per-film memory/catchphrase tracking
- ❌ No honorifics mapping (ji → sir/ma'am)
- ❌ No slang_map configuration
- ❌ No italics_for_songs toggle (hardcoded?)

**CRITICAL GAP**: This is the biggest missing piece!

#### 5.6 Subtitle Formatting (85% COMPLETE)
**Implemented**:
- ✅ Max 2 lines, 42 chars/line
- ✅ Speaker labels formatted `[Speaker Name]`
- ✅ Subtitle merging for short gaps
- ✅ Duration limits

**Gaps**:
- ⚠️ No CPS enforcement (15 target, 17 cap)
- ⚠️ No italics for songs (or unclear if implemented)
- ⚠️ No `[SFX]` bracket formatting

#### 5.7 QA Metrics (40% COMPLETE)
**Implemented**:
- ✅ Comprehensive logging
- ✅ Segment statistics
- ✅ Duration tracking

**Gaps**: ⚠️⚠️
- ❌ No WER/MER calculation
- ❌ No CPS violation detection
- ❌ No terminology coverage tracking
- ❌ No QC reports generated

---

### ✅ Step 6: Tech Stack (100% COMPLETE) ⭐

**Implemented**:
- ✅ ffmpeg (demux, mux)
- ✅ Silero VAD
- ✅ pyannote.audio (VAD + diarization)
- ✅ WhisperX (ASR + alignment)
- ✅ spaCy (NER)
- ✅ transformers (NLLB, lyrics detection)
- ✅ Docker containerization
- ✅ Native Python execution (macOS MPS, Windows)

**Perfect alignment!**

---

### ✅ Step 7: Orchestration & Config (90% COMPLETE)

**Implemented**:
- ✅ Environment-based configuration (`.env` files)
- ✅ Toggleable stages via config
- ✅ Job-specific config per run
- ✅ Hardware detection & optimization

**Gaps**:
- ⚠️ Config is `.env` format, not YAML (different from plan)
- ⚠️ No `config/pipeline.yaml` (uses `.env` instead)

**Evidence**: Per-job config at `.{JOB_ID}.env`

---

### ❌ Step 8: Hinglish→English Glossary (0% COMPLETE) ⚠️⚠️⚠️

**CRITICAL GAP**:
- ❌ **No glossary system implemented**
- ❌ No `glossary/hinglish_master.tsv`
- ❌ No per-film prompt files
- ❌ No terminology enforcement

**Impact**: 
- Translations may be inconsistent
- Hinglish terms (yaar, bhai, jugaad) not standardized
- Honorifics (ji) not handled
- No context-aware term selection

**Recommendation**:
```
glossary/
├─ hinglish_master.tsv
├─ prompts/
│  ├─ jaane_tu_2008.txt
│  ├─ dil_chahta_hai_2001.txt
│  └─ rangeela_1995.txt
└─ README.md
```

---

### ⚠️ Step 9: Example Commands (80% COMPLETE)

**Implemented**:
- ✅ Shell scripts: `run_pipeline.sh`, `resume-pipeline.sh`, `prepare-job.sh`
- ✅ Python orchestrator: `scripts/pipeline.py`
- ✅ Docker & native execution modes

**Gaps**:
- ⚠️ No glossary apply commands
- ⚠️ No terminology linter
- ⚠️ No explicit one-liner "fast path" demo

---

### ❌ Step 10: Human-in-the-Loop QA (20% COMPLETE) ⚠️⚠️

**Implemented**:
- ✅ Manual review possible (output files accessible)
- ✅ Resume capability for corrections

**Gaps**: ⚠️⚠️
- ❌ No reviewer checklist
- ❌ No QA workflow tools
- ❌ No linguist pass instructions
- ❌ No subtitle editor guidelines
- ❌ No spot-check automation

**Recommendation**: Create `tools/qa_review.py` with:
- CPS violation highlighter
- Terminology consistency checker
- Timing visualization
- Diff viewer for corrections

---

### ⚠️ Step 11: Rollout Plan (70% COMPLETE)

**Implemented**:
- ✅ Job-based workflow supports pilot films
- ✅ Per-job configuration
- ✅ Resume capability for iteration

**Gaps**:
- ⚠️ No documented pilot plan
- ⚠️ No Makefile for QC commands
- ⚠️ No maintenance procedures

---

### ✅ Step 12: Risks & Mitigations (85% COMPLETE)

**Implemented**:
- ✅ Overlap handling via diarization
- ✅ Multiple VAD approaches (Silero + PyAnnote)
- ✅ GPU optimization (MPS, CUDA)
- ✅ Retry logic and error handling

**Gaps**:
- ⚠️ Over-literal translations (no glossary to mitigate)
- ⚠️ Name/term drift (no terminology linter)

---

### ✅ Step 13: Deliverables (85% COMPLETE)

**Implemented**:
```
✅ config/ (env-based, not YAML)
✅ scripts/ (orchestration, prepare-job, etc.)
✅ docker/ (all 12 stages)
✅ shared/ (common utilities)
✅ out/ (job outputs with SRT files)
✅ README.md, DOCUMENTATION_STATUS.md
```

**Gaps**:
```
❌ glossary/ (missing entirely)
❌ tools/term_lint.py
❌ tools/check_cps.py
⚠️ No qc.json reports
```

---

### ⚠️ Step 14: Appendix (90% COMPLETE)

**Implemented**:
- ✅ CPS target configurable (not enforced at 15/17)
- ✅ Max line width: 42 chars ✓
- ✅ Max lines: 2 ✓
- ✅ VAD: Silero + PyAnnote ✓
- ✅ ASR: WhisperX large-v3 translate mode ✓
- ✅ Diarization: PyAnnote ✓

**Gaps**:
- ⚠️ No explicit "fast path" one-liner
- ⚠️ No env toggle documentation in main README

---

## Priority Gap Summary

### 🔴 CRITICAL (Must Have)
1. **Glossary System** (Step 8) - 0% complete
   - Hinglish→English terminology TSV
   - Per-film prompts
   - Glossary application in post-editing
   - **Estimated effort**: 2-3 days

2. **CPS Enforcement** (Step 5.6) - Missing
   - Calculate CPS for each subtitle
   - Flag violations > 17
   - Auto-reflow if possible
   - **Estimated effort**: 1 day

3. **QA Metrics & Reports** (Step 5.7) - 40% complete
   - WER/MER calculation
   - CPS violation report
   - Terminology coverage
   - Export qc.json
   - **Estimated effort**: 2 days

### 🟡 HIGH PRIORITY (Should Have)
4. **Human QA Workflow** (Step 10) - 20% complete
   - Reviewer checklist
   - QA review tools
   - Correction workflow
   - **Estimated effort**: 3-4 days

5. **Per-Film Configuration** (Step 2) - Missing
   - Film catalog YAML
   - Per-film prompts/notes
   - Memory system for catchphrases
   - **Estimated effort**: 1-2 days

6. **Advanced Post-Editing** (Step 5.5) - 60% complete
   - Honorifics mapping
   - Slang map
   - Context-aware rules
   - **Estimated effort**: 2-3 days

### 🟢 MEDIUM PRIORITY (Nice to Have)
7. **YAML Config Migration** (Step 7)
   - Convert .env to pipeline.yaml
   - **Estimated effort**: 1 day

8. **QA Tools** (Steps 9, 10, 13)
   - term_lint.py
   - check_cps.py
   - QA review interface
   - **Estimated effort**: 2-3 days

9. **Documentation**
   - Rollout plan
   - Pilot film guide
   - Maintenance procedures
   - **Estimated effort**: 1-2 days

---

## Strengths of Current Implementation

1. **Excellent Pipeline Architecture** ⭐
   - 12 stages vs 9 in plan (includes bonus features)
   - Clean separation of concerns
   - Resume capability
   - Native + Docker execution

2. **Advanced Features Beyond Plan** ⭐
   - Second-pass translation (NLLB)
   - Lyrics detection for songs
   - Hardware auto-detection
   - MPS (Apple Silicon) support
   - Comprehensive logging

3. **Production-Ready Infrastructure** ⭐
   - Docker containerization
   - Environment-based config
   - Error handling and retries
   - Job-based organization
   - Manifest tracking

4. **Strong VAD/ASR/Diarization** ⭐
   - Silero + PyAnnote VAD
   - WhisperX with alignment
   - PyAnnote diarization
   - TMDB auto-mapping

---

## Recommended Implementation Roadmap

### Phase 1: Core Gaps (1-2 weeks)
**Priority: Critical functionality**

Week 1:
- [ ] Day 1-3: Implement glossary system
  - Create `glossary/hinglish_master.tsv`
  - Add glossary loader to post-editing
  - Apply term substitution in subtitle-gen
  
- [ ] Day 4-5: Add CPS enforcement
  - Calculate CPS in subtitle-gen
  - Add CPS violation detection
  - Implement auto-reflow logic

Week 2:
- [ ] Day 6-8: QA metrics & reports
  - Add WER/MER calculation
  - Generate qc.json reports
  - Terminology coverage tracking

- [ ] Day 9-10: Testing & validation
  - Test on pilot films
  - Validate metrics
  - Fix bugs

### Phase 2: QA Workflow (1 week)
- [ ] Create reviewer tools
- [ ] Document QA procedures
- [ ] Build correction workflow
- [ ] Test with human reviewers

### Phase 3: Advanced Features (1 week)
- [ ] Per-film configuration system
- [ ] Advanced post-editing rules
- [ ] Context-aware terminology

### Phase 4: Polish (3-5 days)
- [ ] Documentation
- [ ] YAML config migration (optional)
- [ ] One-liner demos
- [ ] Rollout guide

---

## Code Snippets for Gap Filling

### 1. Glossary System

**Create**: `shared/glossary.py`
```python
import pandas as pd
from pathlib import Path

class HinglishGlossary:
    def __init__(self, tsv_path: Path):
        self.df = pd.read_csv(tsv_path, sep='\t')
        self.term_map = {}
        for _, row in self.df.iterrows():
            options = row['preferred_english'].split('|')
            self.term_map[row['source']] = {
                'options': options,
                'notes': row.get('notes', '')
            }
    
    def apply(self, text: str, context: str = "") -> str:
        """Apply glossary terms to text"""
        for source, data in self.term_map.items():
            if source in text:
                # Use first option for now (can add context logic)
                replacement = data['options'][0]
                text = text.replace(source, replacement)
        return text
```

**Update**: `docker/subtitle-gen/subtitle_gen.py`
```python
from glossary import HinglishGlossary

# After loading segments
if config.get('glossary_enabled', True):
    glossary_path = Path('/app/glossary/hinglish_master.tsv')
    if glossary_path.exists():
        glossary = HinglishGlossary(glossary_path)
        for seg in segments:
            seg['text'] = glossary.apply(seg['text'])
```

### 2. CPS Enforcement

**Update**: `docker/subtitle-gen/subtitle_gen.py`
```python
def calculate_cps(text: str, duration: float) -> float:
    """Calculate characters per second"""
    char_count = len(text.replace('\n', ''))
    return char_count / max(duration, 0.001)

def check_cps_violations(segments, target=15, cap=17):
    """Check for CPS violations"""
    violations = []
    for i, seg in enumerate(segments):
        duration = seg['end'] - seg['start']
        cps = calculate_cps(seg['text'], duration)
        if cps > cap:
            violations.append({
                'index': i,
                'cps': round(cps, 2),
                'severity': 'critical'
            })
        elif cps > target:
            violations.append({
                'index': i,
                'cps': round(cps, 2),
                'severity': 'warning'
            })
    return violations
```

### 3. QC Report Generation

**Create**: `tools/generate_qc_report.py`
```python
import json
from pathlib import Path

def generate_qc_report(job_dir: Path) -> dict:
    """Generate QC report for a job"""
    report = {
        'job_id': job_dir.name,
        'timestamp': datetime.now().isoformat(),
        'metrics': {},
        'violations': {},
        'summary': {}
    }
    
    # Load subtitle file
    srt_files = list(job_dir.glob('en_merged/*.srt'))
    if srt_files:
        # Calculate metrics
        report['metrics']['subtitle_count'] = count_subtitles(srt_files[0])
        report['metrics']['avg_cps'] = calculate_avg_cps(srt_files[0])
        report['violations']['cps'] = check_cps_violations(srt_files[0])
        report['violations']['line_width'] = check_line_width(srt_files[0])
    
    # Save report
    qc_file = job_dir / 'qc_report.json'
    with open(qc_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report
```

---

## Conclusion

**Overall Assessment**: **85-90% Complete** 🎯

The **CP-WhisperX-App** project has excellent foundations with a robust pipeline architecture that exceeds the improvement plan in many areas (12 stages vs 9, bonus features like NLLB translation and lyrics detection). 

**The primary gaps are**:
1. ❌ **Glossary/terminology system** (critical for Hinglish)
2. ⚠️ **CPS enforcement** (readability requirement)
3. ⚠️ **QA metrics & reports** (quality assurance)
4. ⚠️ **Human QA workflow** (review process)

**Estimated effort to reach 100%**: 3-4 weeks of focused development

**Recommendation**: Prioritize Phase 1 (glossary + CPS + QA metrics) for immediate production readiness. The system is already usable for 1990s/2000s Bollywood films, but these additions will significantly improve output quality and consistency.

---

**Analysis Date**: November 9, 2025  
**Analyst**: Pipeline Architecture Review  
**Next Review**: After Phase 1 implementation
