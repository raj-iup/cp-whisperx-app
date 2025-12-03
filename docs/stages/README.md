# Pipeline Stages Documentation

**Document Version:** 1.0  
**Date:** December 3, 2025  
**Status:** Active

---

## Overview

This directory contains detailed documentation for each stage of the CP-WhisperX 10-stage modular pipeline (v3.0).

**Pipeline Architecture:** v3.0 (Context-Aware Modular)  
**Total Stages:** 10  
**Current Integration:** 22% (Phase 0 complete)  
**Target:** 100% (Phase 4 complete)

---

## Stage Index

| # | Stage Name | Script | Status | StageIO | Manifest | Docs |
|---|------------|--------|--------|---------|----------|------|
| 01 | Demux | `scripts/01_demux.py` | ⚠️ Legacy | ❌ | ❌ | ⏳ |
| 02 | TMDB Enrichment | `scripts/02_tmdb_enrichment.py` | ✅ Active | ✅ | ✅ | ✅ |
| 03 | Glossary Loader | `scripts/03_glossary_loader.py` | ⚠️ Partial | ❌ | ❌ | ⏳ |
| 04 | Source Separation | `scripts/04_source_separation.py` | ⏳ Planned | ❌ | ❌ | ⏳ |
| 05 | PyAnnote VAD | `scripts/05_pyannote_vad.py` | ⏳ Planned | ❌ | ❌ | ⏳ |
| 06 | WhisperX ASR | `scripts/06_whisperx_asr.py` | ⚠️ Legacy | ❌ | ❌ | ⏳ |
| 07 | MLX Alignment | `scripts/07_mlx_alignment.py` | ⏳ Planned | ❌ | ❌ | ⏳ |
| 08 | Translation | `scripts/08_indictrans2_translation.py` | ⚠️ Legacy | ❌ | ❌ | ⏳ |
| 09 | Subtitle Generation | `scripts/09_subtitle_generation.py` | ⏳ Planned | ❌ | ❌ | ⏳ |
| 10 | Mux | `scripts/10_mux.py` | ⚠️ Legacy | ❌ | ❌ | ⏳ |

**Legend:**
- ✅ **Active** - Fully integrated with StageIO pattern
- ⚠️ **Legacy** - Working but needs migration to StageIO
- ⚠️ **Partial** - Partially implemented, needs completion
- ⏳ **Planned** - Not yet integrated, planned for Phase 3-4

---

## Stage Descriptions

### 01. Demux
**Purpose:** Extract audio from video and compute audio fingerprint  
**Input:** Video file (MP4, MKV, AVI, etc.)  
**Output:** Audio file (WAV/FLAC) + audio metadata  
**Caching:** Audio fingerprint cache for identical media detection

**Key Features:**
- Multi-format support (FFmpeg-based)
- Audio fingerprinting for cache lookup
- Metadata extraction (duration, sample rate, channels)
- Language detection preparation

**Current Status:** ⚠️ Working but needs StageIO migration (Phase 3)

---

### 02. TMDB Enrichment
**Purpose:** Fetch movie/show metadata for cultural context  
**Input:** Media filename or user-provided TMDB ID  
**Output:** Movie metadata (title, year, cast, genres, overview)  
**Caching:** TMDB API responses cached

**Key Features:**
- Automatic movie detection from filename
- Cast and character name extraction
- Genre and context information
- Cultural background for subtitle generation

**Current Status:** ✅ Fully implemented with StageIO pattern  
**Documentation:** See [02_TMDB_INTEGRATION.md](02_TMDB_INTEGRATION.md)

---

### 03. Glossary Loader
**Purpose:** Load and merge custom glossaries with learned terms  
**Input:** User glossaries + learned terms from previous jobs  
**Output:** Merged glossary for ASR/translation context  
**Caching:** Learned glossary cache per movie/genre

**Key Features:**
- User-defined glossary support
- Character name preservation
- Cultural term mapping
- Learned term integration from previous processing
- Frequency-based term prioritization

**Current Status:** ⚠️ Partial implementation, needs StageIO migration (Phase 3)

---

### 04. Source Separation
**Purpose:** Separate dialogue from background music/effects  
**Input:** Audio file  
**Output:** Separated vocal track  
**Caching:** None (processing required)

**Key Features:**
- Demucs-based separation
- Optional (enabled for noisy audio)
- ML-based decision (adaptive quality prediction)
- Improves ASR accuracy on music-heavy content

**Current Status:** ⏳ Planned for Phase 4 integration

---

### 05. PyAnnote VAD (Voice Activity Detection)
**Purpose:** Detect speech segments and perform speaker diarization  
**Input:** Audio file  
**Output:** Speech segments with speaker labels  
**Caching:** None (processing required)

**Key Features:**
- Voice activity detection (VAD)
- Speaker diarization (who spoke when)
- Speech/silence segmentation
- Speaker attribution for subtitles

**Current Status:** ⏳ Planned for Phase 4 integration

---

### 06. WhisperX ASR
**Purpose:** Transcribe audio to text with word-level timestamps  
**Input:** Audio file + speech segments  
**Output:** Transcript with word-level timestamps  
**Caching:** ASR results cache (quality-aware)

**Key Features:**
- WhisperX for high-accuracy ASR
- Multi-language support (100+ languages)
- Word-level timestamp alignment
- Confidence scores per word
- Multi-environment support (CUDA/CPU/MLX)

**Current Status:** ⚠️ Working but needs StageIO migration (Phase 3)

---

### 07. MLX Alignment
**Purpose:** Refine word-level timestamp alignment (Apple Silicon)  
**Input:** Transcript with timestamps  
**Output:** Refined timestamp alignment  
**Caching:** None (fast processing)

**Key Features:**
- MLX-optimized for Apple Silicon
- Sub-100ms timestamp precision
- Fallback to WhisperX alignment on non-MLX systems

**Current Status:** ⏳ Planned for Phase 4 integration

---

### 08. Translation
**Purpose:** Translate transcript to target language(s)  
**Input:** Transcript + glossary + context  
**Output:** Translated text in target language(s)  
**Caching:** Translation memory cache (contextual)

**Key Features:**
- IndicTrans2 for Indic languages (highest quality)
- NLLB-200 for non-Indic languages
- Context-aware translation
- Glossary term preservation
- Cultural adaptation (idioms, formality)
- Temporal consistency

**Current Status:** ⚠️ Working but needs StageIO migration (Phase 3)

---

### 09. Subtitle Generation
**Purpose:** Generate subtitle files with context awareness  
**Input:** Transcript + translation + context metadata  
**Output:** SRT/VTT subtitle files (multiple languages)  
**Caching:** None (fast generation)

**Key Features:**
- Multi-language subtitle generation
- Context-aware formatting
- Timing optimization (±200ms accuracy)
- Speaker attribution in subtitles
- Cultural context adaptation
- Glossary term application

**Current Status:** ⏳ Planned for Phase 4 integration (currently inline in mux)

---

### 10. Mux
**Purpose:** Soft-embed subtitle tracks back into media  
**Input:** Original media + subtitle files  
**Output:** Media with soft-embedded subtitles  
**Caching:** None (final output)

**Key Features:**
- Multi-track soft-embedding (FFmpeg)
- Organized output directory structure
- All subtitle tracks included
- Original quality preservation
- Track naming and language tagging

**Current Status:** ⚠️ Working but needs StageIO migration (Phase 3)

---

## Pipeline Flows

### Subtitle Workflow (Full 10-stage)
```
01_demux → 02_tmdb → 03_glossary_load → 04_source_sep → 05_pyannote_vad 
  → 06_whisperx_asr → 07_alignment → 08_translate → 09_subtitle_gen → 10_mux
```

### Transcribe Workflow (7-stage)
```
01_demux → 02_tmdb (optional) → 03_glossary_load → 04_source_sep (optional) 
  → 05_pyannote_vad → 06_whisperx_asr → 07_alignment
```

### Translate Workflow (8-stage)
```
01_demux → 02_tmdb → 03_glossary_load → 04_source_sep (optional) 
  → 05_pyannote_vad → 06_whisperx_asr → 07_alignment → 08_translate
```

---

## Development Guidelines

### Adding Stage Documentation

**When documenting a stage, include:**
1. **Purpose:** What does this stage do?
2. **Input/Output:** File formats and data structures
3. **Configuration:** Relevant config/.env.pipeline parameters
4. **Caching:** What is cached and why
5. **Dependencies:** Other stages this depends on
6. **Testing:** How to test this stage independently
7. **Performance:** Expected processing time and bottlenecks
8. **Examples:** Sample commands and outputs

**Template:** Create `docs/stages/{NN}_{STAGE_NAME}.md` using this structure.

### Stage Implementation Checklist

When implementing a stage (see `docs/developer/DEVELOPER_STANDARDS.md`):
- [ ] Script named `{NN}_{stage_name}.py`
- [ ] Uses StageIO pattern with manifest tracking
- [ ] Uses dual logging (get_stage_logger())
- [ ] Implements caching where appropriate
- [ ] Tracks all inputs and outputs
- [ ] Writes outputs ONLY to io.stage_dir
- [ ] Has comprehensive error handling
- [ ] Has unit tests (tests/test_{NN}_{stage_name}.py)
- [ ] Has integration tests
- [ ] Has stage documentation (docs/stages/{NN}_{STAGE_NAME}.md)

---

## Migration Status

**Phase 0 (Foundation):** ✅ Complete (Standards, config, hooks)  
**Phase 1 (File Naming):** ⏳ Ready to start (2 weeks)  
**Phase 2 (Testing):** ⏳ Ready to start (3 weeks)  
**Phase 3 (StageIO Migration):** 🔴 Blocked - Migrate 5 active stages (4 weeks)  
**Phase 4 (Stage Integration):** 🔴 Blocked - Complete 10-stage pipeline (8 weeks)  
**Phase 5 (Advanced):** 🔴 Blocked - Caching, ML, monitoring (4 weeks)

**See:** `docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md` for complete migration plan

---

## Testing

**Standard Test Media:**
- Sample 1: `in/Energy Demand in AI.mp4` (English technical)
- Sample 2: `in/test_clips/jaane_tu_test_clip.mp4` (Hinglish Bollywood)

**Test Each Stage:**
```bash
# Unit test
pytest tests/test_{NN}_{stage_name}.py

# Integration test with standard media
./prepare-job.sh --media "in/Energy Demand in AI.mp4" --workflow transcribe
./run-pipeline.sh --job-dir out/$(latest_job)

# Validate quality
python3 tests/validate-quality.py --job-dir out/$(latest_job) --sample sample_01
```

---

## References

- **Architecture:** [ARCHITECTURE_IMPLEMENTATION_ROADMAP.md](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md)
- **Developer Standards:** [DEVELOPER_STANDARDS.md](../developer/DEVELOPER_STANDARDS.md)
- **Workflows:** [workflows.md](../user-guide/workflows.md)
- **Caching:** [caching-ml-optimization.md](../technical/caching-ml-optimization.md)
- **Copilot Instructions:** [copilot-instructions.md](../../.github/copilot-instructions.md)

---

**Document Status:** Active  
**Last Updated:** December 3, 2025  
**Next Review:** After Phase 3 completion
