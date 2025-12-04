# Architecture Implementation Roadmap

**Document Version:** 3.2  
**Date:** 2025-12-04  
**Status:** ✅ Active Development  
**Current System:** v2.9 (95% Complete - Final Sprint toward v3.0)  
**Target System:** v3.0 (Context-Aware Modular 12-Stage Pipeline)  
**Overall v2.0→v3.0 Progress:** 95% (21 weeks / ~250 hours invested)  
**Current Sprint Progress:** 21% (5/24 hours - completing final pieces)

**Key Updates in v3.2 (December 4, 2025):**
- ✅ **12-Stage Pipeline**: Lyrics detection (08) and hallucination removal (09) integrated as MANDATORY
- ✅ **Output Structure**: Legacy directories removed, stage-based architecture enforced
- ✅ **Stage Order**: Corrected and documented in shared/stage_order.py
- ✅ **Documentation**: 27 inconsistencies identified and being fixed

**Key Updates in v3.1 (December 3, 2025):**
- 🐛 **Bug Fixes Applied**: Source language, TMDB, StageManifest, script paths
- 🐛 **TMDB Workflow-Aware**: Only enabled for subtitle workflow (movies/TV)
- 🐛 **Transcribe Enhanced**: Auto-detects language when not specified
- 🐛 **StageManifest Complete**: add_intermediate() method implemented

**Key Updates Since v2.0:**
- ✅ Code quality: 100% compliance achieved
- ✅ Configuration: Cleaned and standardized (179 parameters)
- ✅ Documentation: File naming and job preparation flow documented
- ✅ Pre-commit hook: Active and enforcing standards
- 🆕 **Testing Infrastructure**: Standardized test media samples defined
- 🆕 **Context-Aware Workflows**: Enhanced accuracy requirements
- 🆕 **Caching & ML Optimization**: Intelligent performance improvement

---

## 📋 Quick Navigation

- [Executive Summary](#executive-summary) - High-level overview and goals
- [Testing Infrastructure](#testing-infrastructure) - Standard test samples and workflows
- [Core Workflows](#core-workflows) - Subtitle, Transcribe, Translate workflows
- [Current State](#current-state-analysis) - What exists today
- [Target Architecture](#target-architecture) - Where we're going
- [Phase 0: Foundation](#phase-0-foundation--complete) - ✅ COMPLETE
- [Phase 1: File Naming](#phase-1-file-naming--standards) - 🟡 Ready to start
- [Phase 2: Testing](#phase-2-testing-infrastructure) - 🟡 Ready to start
- [Phase 3: StageIO Migration](#phase-3-stageio-migration) - 🔴 Blocked by Phase 1-2
- [Phase 4: Stage Integration](#phase-4-stage-integration) - 🔴 Blocked by Phase 3
- [Phase 5: Advanced Features](#phase-5-advanced-features) - 🔴 Blocked by Phase 4
- [Success Metrics](#success-metrics) - How we measure progress
- [Risk Management](#risk-management) - Identified risks and mitigations

---

## Executive Summary

### Mission

Transform CP-WhisperX-App from a simplified 3-6 stage pipeline (v2.0) to a **context-aware, caching-enabled, fully modular 12-stage architecture (v3.0)** with 95%+ code-documentation alignment, comprehensive testing using standardized test media, and production-ready reliability with intelligent performance optimization.

### The Problem

**Current State (v2.9 - Final Sprint):**
- ✅ Works well for all three workflows (transcribe, translate, subtitle)
- ✅ **ALL 12 stages now use standardized StageIO pattern** (100% adoption achieved)
- ✅ **Full manifest tracking** across all stages (data lineage complete)
- ✅ **Standardized test media samples** defined (Sample 1: English, Sample 2: Hinglish)
- ✅ **Context-aware subtitle generation** with cultural terms, character names, speaker attribution
- ✅ **Lyrics detection and hallucination removal** integrated as mandatory subtitle stages
- ⚠️ **Caching and ML optimization** - Planned in Phase 5 (not yet implemented)
- ⚠️ **Stage enable/disable per job** - Partially implemented
- ⚠️ **Advanced monitoring** - Basic implementation, needs enhancement

**Business Impact:**
- 40% slower development due to inconsistent patterns
- Difficult to debug without data lineage
- Hard to add new stages due to tight coupling
- Limited error recovery and monitoring
- No baseline for quality comparison
- Repetitive processing of similar media without optimization

### The Solution

**5-Phase Transformation (21 weeks, 250 hours):**

```
Phase 0 (✅ DONE):  Foundation - Standards, config, pre-commit hooks
Phase 1 (2 weeks):  File Naming - Rename scripts to match standards
Phase 2 (3 weeks):  Testing - Build test suite with standardized media
Phase 3 (4 weeks):  StageIO - Migrate 5 active stages to pattern
Phase 4 (8 weeks):  Integration - Add 2 mandatory stages (lyrics, hallucination), full 12-stage pipeline
Phase 5 (4 weeks):  Advanced - Caching, ML optimization, monitoring
```

### Expected ROI

**Investment:** 250 hours (~6.25 person-weeks)

**Returns:**
- 40% faster feature development
- 60% reduction in debugging time
- 80% fewer integration issues
- 90% better testability
- 50% faster processing on repeated similar media (caching)
- 30% improved subtitle accuracy (context-aware generation)
- **Break-even:** 3-4 months

---

## Testing Infrastructure

### Standard Test Media Samples

**Purpose:** Establish reproducible testing baseline with diverse use cases.

#### Sample 1: English Technical Content
**File:** `in/Energy Demand in AI.mp4`  
**Size:** ~14 MB  
**Duration:** Short clip (~2-5 minutes)  
**Language:** English  
**Use Case:** Technical/Educational content  
**Workflows:** Transcribe, Translate

**Characteristics:**
- Clear English audio
- Technical terminology (AI, energy, demand)
- Good for testing ASR accuracy on technical content
- Ideal for English-to-Indic translation testing
- Minimal background noise

**Test Scenarios:**
1. **Transcribe Workflow**: English → English transcript
   - Expected: High accuracy (>95%)
   - Tests: ASR, alignment, technical term handling
   
2. **Translate Workflow**: English → Hindi/Gujarati/Spanish
   - Expected: Accurate technical translation
   - Tests: Translation accuracy, term preservation

#### Sample 2: Hinglish Bollywood Content
**File:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Size:** ~28 MB  
**Duration:** Short clip  
**Language:** Hindi/Hinglish (mixed)  
**Use Case:** Entertainment content with code-mixing  
**Workflows:** Subtitle, Transcribe, Translate

**Characteristics:**
- Mixed Hindi-English (Hinglish)
- Typical Bollywood dialogue patterns
- Background music possible
- Multiple speakers
- Emotional/casual speech
- Real-world subtitle generation challenge

**Test Scenarios:**
1. **Subtitle Workflow**: Hindi/Hinglish → Multiple subtitle tracks
   - Expected: Context-aware Hindi, English, Gujarati, Tamil subtitles
   - Output: Soft-embedded in new subdirectory
   - Tests: Full pipeline, glossary application, context awareness
   
2. **Transcribe Workflow**: Hindi → Hindi transcript
   - Expected: Accurate Hindi/Hinglish transcription
   - Tests: Indic language ASR, code-mixing handling
   
3. **Translate Workflow**: Hindi → English/Spanish/Chinese/Arabic
   - Expected: Natural target language output
   - Tests: Cross-language translation, idiom handling

### Test Media Organization

```
in/
├── Energy Demand in AI.mp4          # Sample 1: English technical
├── test_clips/
│   └── jaane_tu_test_clip.mp4       # Sample 2: Hinglish Bollywood
└── test_media_index.json            # Metadata about test samples
```

**test_media_index.json:**
```json
{
  "test_samples": [
    {
      "id": "sample_01",
      "file": "Energy Demand in AI.mp4",
      "language": "en",
      "type": "technical",
      "duration_estimate": "2-5 min",
      "workflows": ["transcribe", "translate"],
      "quality_baseline": {
        "asr_accuracy": 0.95,
        "translation_fluency": 0.90
      }
    },
    {
      "id": "sample_02",
      "file": "test_clips/jaane_tu_test_clip.mp4",
      "language": "hi-Hinglish",
      "type": "entertainment",
      "duration_estimate": "1-3 min",
      "workflows": ["subtitle", "transcribe", "translate"],
      "quality_baseline": {
        "asr_accuracy": 0.85,
        "subtitle_quality": 0.88,
        "context_awareness": 0.80
      }
    }
  ]
}
```

---

## Core Workflows

### 1. Subtitle Workflow (Context-Aware, Highest Accuracy)

**Purpose:** Generate context-aware, high-accuracy multilingual subtitles for Bollywood/Indic media with soft-embedding.

**Input:** Indic/Hinglish movie/TV media source  
**Output:** Original media + soft-embedded subtitle tracks in dedicated subdirectory
**TMDB:** ✅ Enabled (fetches cast, crew, character names) 🆕 v3.1

**Pipeline Flow:**
```
Input Media (e.g., jaane_tu_test_clip.mp4, Bollywood movie)
    ↓
01_demux          → Extract audio
    ↓
02_tmdb           → Fetch movie metadata for context ✅ Enabled
    │               (Cast, crew, character names)
    ↓
03_glossary_load  → Load character names, cultural terms
    ↓
04_source_sep     → Separate dialogue from music (optional)
    ↓
05_pyannote_vad   → Detect speech segments, speaker diarization
    ↓
06_whisperx_asr   → Transcribe with word-level timestamps
    ↓
07_alignment      → Refine word alignment (MLX on Apple Silicon)
    ↓
08_translate      → Generate multiple subtitle tracks:
    │               - Hindi (native)
    │               - English
    │               - Indic (Gujarati, Tamil, Telugu, etc.)
    │               - Non-Indic (Spanish, Russian, Chinese, Arabic)
    ↓
09_subtitle_gen   → Generate SRT/VTT with context awareness:
    │               - Apply glossary terms
    │               - Cultural context adaptation
    │               - Timing optimization
    ↓
10_mux            → Soft-embed all subtitle tracks
    ↓
Output: out/{date}/{user}/{job}/10_mux/{media_name}/
    ├── {media_name}_subtitled.mkv     # Original video + all subtitle tracks
    ├── subtitles/
    │   ├── {media_name}.hi.srt        # Hindi
    │   ├── {media_name}.en.srt        # English
    │   ├── {media_name}.gu.srt        # Gujarati
    │   ├── {media_name}.ta.srt        # Tamil
    │   ├── {media_name}.es.srt        # Spanish
    │   ├── {media_name}.ru.srt        # Russian
    │   ├── {media_name}.zh.srt        # Chinese
    │   └── {media_name}.ar.srt        # Arabic
    └── manifest.json                   # Processing metadata
```

**Context-Aware Features:**
1. **Character Names:** Preserved via glossary (Aditi, Jai, Meow, etc.)
2. **Cultural Terms:** Hindi idioms, relationship terms (beta, bhai, etc.)
3. **Tone Adaptation:** Formal vs. casual based on context
4. **Temporal Coherence:** Consistent terminology across subtitle blocks
5. **Speaker Attribution:** Diarization for multi-speaker scenes

**Quality Targets:**
- ASR Accuracy: ≥85% for Hinglish
- Subtitle Timing: ±200ms
- Translation Fluency: ≥88%
- Context Consistency: ≥80%
- Glossary Application: 100%

**Example Test Command:**
```bash
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar

./run-pipeline.sh --job-dir out/2025/12/03/user/0001
```

### 2. Transcribe Workflow (Context-Aware, Highest Accuracy)

**Purpose:** Create high-accuracy text transcript in source language with context awareness.

**Input:** Any media source (YouTube, podcasts, lectures, general content)
**Output:** Text transcript in SAME language as source audio
**Source Language:** Optional (auto-detects if not specified) 🆕 v3.1

**Pipeline Flow:**
```
Input Media (e.g., Energy Demand in AI.mp4, YouTube video)
    ↓
01_demux          → Extract audio
    ↓
03_glossary_load  → Load domain-specific terms
    ↓
04_source_sep     → Clean audio (optional)
    ↓
05_pyannote_vad   → Speech detection
    ↓
06_whisperx_asr   → Transcribe in source language:
    │               - English media → English transcript
    │               - Hindi media → Hindi transcript
    │               - Indic media → Same Indic language
    │               - Spanish media → Spanish transcript
    │               - Auto-detects if -s not specified 🆕
    ↓
07_alignment      → Word-level timestamp refinement
    ↓
Output: out/{date}/{user}/{job}/07_alignment/
    ├── transcript.txt                 # Plain text transcript
    ├── transcript.json                # With word-level timestamps
    └── manifest.json                  # Processing metadata
```

**Context-Aware Features:**
1. **Domain Terminology:** Technical, medical, legal terms preserved
2. **Proper Nouns:** Names, places, organizations
3. **Language-Specific:** Native script output (Devanagari for Hindi)
4. **Punctuation:** Context-aware sentence segmentation
5. **Capitalization:** Proper noun detection (English)

**Quality Targets:**
- English Technical: ≥95% WER
- Hindi/Indic: ≥85% WER
- Other Languages: ≥90% WER
- Proper Noun Accuracy: ≥90%
- Timestamp Precision: ±100ms

**Example Test Commands:**
```bash
# English technical content
./prepare-job.sh \
  --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

# Hindi content
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe \
  --source-language hi
```

### 3. Translate Workflow (Context-Aware, Highest Accuracy)

**Purpose:** Create high-accuracy text transcript in TARGET language with context preservation.

**Input:** Indian language media (IndicTrans2 constraint) 🆕 v3.1
**Output:** Text transcript in SPECIFIED target language
**Source Language:** Required (must be Indian language) 🆕 v3.1
**TMDB:** ❌ Disabled (not needed for non-movie content) 🆕 v3.1

**Pipeline Flow:**
```
Input Media (Hindi/Tamil/Telugu/etc. → Any target language)
    ↓
01_demux          → Extract audio
    ↓
03_glossary_load  → Load bilingual glossary
    ↓
04_source_sep     → Clean audio (optional)
    ↓
05_pyannote_vad   → Speech detection
    ↓
06_whisperx_asr   → Transcribe in source language
    ↓
07_alignment      → Refine timestamps
    ↓
08_translate      → Translate to target language:
    │               - Hindi → English ✅
    │               - Hindi → Spanish/Russian/Chinese/Arabic ✅
    │               - Hindi → Gujarati/Tamil (Indic-to-Indic) ✅
    │               - English → Hindi ❌ (NOT supported - use transcribe)
    │               - Preserve context, idioms, cultural nuances
    ↓
Output: out/{date}/{user}/{job}/08_translate/
    ├── transcript_{target_lang}.txt   # Translated transcript
    ├── transcript_{target_lang}.json  # With timestamps
    ├── translation_metadata.json      # Quality metrics
    └── manifest.json                  # Processing metadata
```

**Context-Aware Features:**
1. **Cultural Adaptation:** Idioms, metaphors localized
2. **Formality Levels:** Maintained across languages
3. **Named Entities:** Transliterated appropriately
4. **Glossary Terms:** Bilingual term preservation
5. **Temporal Consistency:** Same term translated consistently
6. **Numeric/Date Formats:** Localized per target culture

**Translation Routing:**
- **Indic Languages:** IndicTrans2 (AI4Bharat) - highest quality
- **Non-Indic:** NLLB-200 (Meta) - broad language support
- **Fallback:** Hybrid approach if primary fails

**Quality Targets:**
- Hindi → English: ≥90% BLEU score
- Indic-to-Indic: ≥88% BLEU score
- Hindi → Non-Indic: ≥85% BLEU score
- Glossary Application: 100%
- Cultural Adaptation: ≥80% appropriateness

**Example Test Commands:**
```bash
# Hindi → English
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language en

# Hindi → Spanish (non-Indic)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language es

# Hindi → Gujarati (Indic-to-Indic)
./prepare-job.sh \
  --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language gu
```

---

## Caching & ML Optimization

### Intelligent Caching System

**Purpose:** Enable subsequent workflows with similar media to perform optimally over time through intelligent caching and machine learning.

**Caching Layers:**

#### 1. Model Cache (Shared)
```
{cache_dir}/models/
├── whisperx/
│   ├── large-v2/                    # Downloaded model weights
│   └── large-v3/
├── indictrans2/
│   └── hi-en/                       # Translation model checkpoints
└── pyannote/
    └── speaker-diarization/
```

**Benefits:** Avoid re-downloading models (saves 1-5 GB per run)

#### 2. Audio Fingerprint Cache (Job-Specific)
```
{cache_dir}/fingerprints/
├── {audio_hash}.json                # Audio characteristics
│   ├── duration
│   ├── sample_rate
│   ├── channels
│   ├── language_detected
│   └── noise_profile
└── index.db                         # Fast lookup database
```

**Benefits:** Skip demux/analysis for identical media

#### 3. ASR Results Cache (Quality-Aware)
```
{cache_dir}/asr/
├── {audio_hash}_{model}_{lang}.json
│   ├── segments                     # Transcribed segments
│   ├── word_timestamps
│   ├── confidence_scores
│   └── language_probs
└── index.db
```

**Benefits:** Reuse ASR results for same audio (saves 2-10 minutes)

**Cache Key:** `SHA256(audio_content + model_version + language + config_params)`

**Invalidation Rules:**
- Model version change
- Configuration parameter change affecting ASR
- User explicitly requests fresh processing (`--no-cache` flag)

#### 4. Translation Cache (Contextual)
```
{cache_dir}/translations/
├── {source_hash}_{src_lang}_{tgt_lang}_{glossary_hash}.json
│   ├── translated_segments
│   ├── glossary_applied
│   ├── confidence_scores
│   └── context_metadata
└── index.db
```

**Benefits:** Reuse translations for similar content (saves 1-5 minutes)

**Context-Aware Matching:**
- Exact segment match: 100% reuse
- Similar segment (>80% similarity): Reuse with adjustment
- Different context: Fresh translation

#### 5. Glossary Learning Cache
```
{cache_dir}/glossary_learned/
├── {movie_id}/                      # Per-movie learned terms
│   ├── character_names.json
│   ├── cultural_terms.json
│   └── frequency_analysis.json
└── global/                          # Across all jobs
    ├── common_names.json
    ├── bollywood_terms.json
    └── technical_terms.json
```

**Benefits:** Improve accuracy on subsequent processing of same movie/genre

### ML-Based Optimization

#### 1. Adaptive Quality Prediction

**Purpose:** Predict optimal processing parameters based on media characteristics.

**ML Model:** Lightweight XGBoost classifier

**Features:**
- Audio quality metrics (SNR, clarity)
- Language detected
- Speech rate
- Background noise level
- Historical processing results

**Predictions:**
- Optimal Whisper model size (base/small/medium/large)
- Source separation needed? (yes/no)
- Expected ASR confidence
- Processing time estimate

**Benefits:** 
- 30% faster processing on clean audio (use smaller model)
- Better quality on noisy audio (enable source separation)
- Accurate time estimates

#### 2. Context Learning from History

**Purpose:** Learn patterns from previous jobs to improve context awareness.

**Learning Mechanisms:**

**A. Character Name Recognition:**
```python
# After processing "Jaane Tu Ya Jaane Na" once:
learned_names = {
    "Jai": {"frequency": 142, "speakers": ["male_01"], "contexts": ["casual"]},
    "Aditi": {"frequency": 98, "speakers": ["female_01"], "contexts": ["casual"]},
    "Meow": {"frequency": 34, "speakers": ["female_02"], "contexts": ["nickname"]}
}

# On next processing of same movie:
# - Pre-populate glossary
# - Higher confidence in name detection
# - Consistent speaker attribution
```

**B. Cultural Term Patterns:**
```python
# Learn common Bollywood/Hindi patterns:
cultural_patterns = {
    "beta": {"translation_context": "affectionate", "alternatives": ["dear", "son"]},
    "bhai": {"translation_context": "brother", "formal": False},
    "ji": {"translation_context": "respectful_suffix", "preserve": True}
}
```

**C. Translation Memory:**
```python
# Build translation memory from approved translations:
translation_memory = {
    "source_segment": "तुम मेरे लिए क्या हो?",
    "target_segment": "What am I to you?",
    "context": "romantic_dialogue",
    "confidence": 0.95,
    "reuse_count": 12
}
```

#### 3. Similarity-Based Optimization

**Purpose:** Detect similar media and reuse processing decisions.

**Similarity Metrics:**
- Audio fingerprint matching (chromaprint)
- Content-based similarity (same movie, different versions)
- Language/accent similarity
- Genre similarity

**Optimization Actions:**
```python
if similarity_score > 0.95:
    # Nearly identical media
    reuse_full_pipeline_config()
    apply_cached_glossary()
    
elif similarity_score > 0.80:
    # Similar content (e.g., same movie, different quality)
    reuse_glossary()
    reuse_model_selection()
    fresh_asr()  # Different audio quality
    
elif similarity_score > 0.60:
    # Similar genre/language
    reuse_language_settings()
    suggest_related_glossaries()
```

### Cache Configuration

**In config/.env.pipeline:**
```bash
# Caching Configuration
ENABLE_CACHING=true                          # Master switch
CACHE_DIR=~/.cp-whisperx/cache              # Cache location
CACHE_MAX_SIZE_GB=50                        # Total cache size limit
CACHE_ASR_RESULTS=true                      # Cache ASR outputs
CACHE_TRANSLATIONS=true                     # Cache translations
CACHE_AUDIO_FINGERPRINTS=true              # Cache audio analysis
CACHE_TTL_DAYS=90                          # Cache expiration (days)
CACHE_CLEANUP_ON_START=false               # Auto-cleanup old cache

# ML Optimization
ENABLE_ML_OPTIMIZATION=true                 # Enable ML predictions
ML_MODEL_SELECTION=adaptive                 # adaptive|fixed
ML_QUALITY_PREDICTION=true                 # Predict optimal settings
ML_LEARNING_FROM_HISTORY=true              # Learn from past jobs

# Performance Tuning
SIMILAR_CONTENT_THRESHOLD=0.80             # Similarity reuse threshold
GLOSSARY_LEARNING_ENABLED=true             # Learn terms over time
TRANSLATION_MEMORY_ENABLED=true            # Build translation memory
```

### Cache Management Commands

```bash
# View cache statistics
./tools/cache-manager.sh --stats

# Clear specific cache type
./tools/cache-manager.sh --clear asr
./tools/cache-manager.sh --clear translations

# Clear old cache (>90 days)
./tools/cache-manager.sh --cleanup

# Clear all cache
./tools/cache-manager.sh --clear all

# Disable caching for one job
./prepare-job.sh --media in/file.mp4 --no-cache
```

### Expected Performance Improvements

| Scenario | First Run | Subsequent Run | Improvement |
|----------|-----------|----------------|-------------|
| Identical media | 10 min | 30 sec | 95% faster |
| Same movie, different cut | 10 min | 6 min | 40% faster |
| Similar Bollywood movie | 10 min | 8 min | 20% faster |
| Similar language/genre | 10 min | 9 min | 10% faster |

**Cache Hit Rates (Target):**
- Audio fingerprint: 80% on re-processing
- ASR results: 70% on same media
- Translations: 60% on similar content
- Glossary terms: 90% on same movie/series

---

## Current State Analysis

### What We Have Today (v2.0)

**Active Pipeline (Works):**
```
Transcribe:  demux → asr
Translate:   demux → asr → translation  
Subtitle:    demux → asr → translation → subtitle_gen (inline) → mux
```

**Active Stage Scripts (v2.9 - Current State):**

| Stage | Current File | Status | Pattern | Manifest |
|-------|-------------|--------|---------|----------|
| 01 Demux | `01_demux.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 02 TMDB | `02_tmdb_enrichment.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 03 Glossary | `03_glossary_load.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 04 Source Sep | `04_source_separation.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 05 PyAnnote VAD | `05_pyannote_vad.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 06 WhisperX ASR | `06_whisperx_asr.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 07 Alignment | `07_alignment.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 08 Lyrics | `08_lyrics_detection.py` ✅ | **MANDATORY (subtitle)** | ✅ StageIO | ✅ Yes |
| 09 Hallucination | `09_hallucination_removal.py` ✅ | **MANDATORY (subtitle)** | ✅ StageIO | ✅ Yes |
| 10 Translation | `10_translation.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 11 Subtitle Gen | `11_subtitle_generation.py` ✅ | Active | ✅ StageIO | ✅ Yes |
| 12 Mux | `12_mux.py` ✅ | Active | ✅ StageIO | ✅ Yes |

**Optional/Experimental Stages:**

| Stage | Current File | Status | Pattern | Manifest |
|-------|-------------|--------|---------|----------|
| 11 NER | `11_ner.py` ✅ | Optional (not in workflows) | ✅ StageIO | ✅ Yes |

### What Works Well (v2.9)

1. ✅ **Multi-Environment Architecture** - MLX/CUDA/CPU with automatic routing
2. ✅ **Configuration Management** - Centralized, job-specific overrides working
3. ✅ **Logging System** - Dual logging (main + stage logs) implemented
4. ✅ **Translation Routing** - IndicTrans2/NLLB with fallback logic
5. ✅ **Code Quality** - 100% compliance with automated enforcement
6. ✅ **StageIO Pattern** - ALL 12 stages use standardized pattern
7. ✅ **Manifest Tracking** - Complete data lineage across all stages
8. ✅ **Context-Aware Subtitles** - Character names, cultural terms, lyrics handling
9. ✅ **Standard Test Media** - Two samples defined with quality baselines
10. ✅ **Stage-Based Output** - Proper isolation, no legacy directories

### Remaining Gaps (Final Sprint to v3.0)

1. ⚠️ **Caching System** - Planned but not yet implemented (Phase 5)
2. ⚠️ **ML Optimization** - Adaptive quality prediction not yet active (Phase 5)
3. ⚠️ **Advanced Monitoring** - Basic implementation, needs dashboard
4. ⚠️ **Integration Testing** - Need comprehensive end-to-end tests with standard media
5. ⚠️ **Performance Optimization** - Need to measure and optimize stage execution times
6. ❌ **Testing** - Only 35% unit, <10% integration coverage
7. ❌ **File Naming** - Inconsistent, doesn't match standards
8. ❌ **Stage Integration** - 5 stages exist but not in pipeline

---

## Target Architecture

### Vision: Context-Aware Modular 12-Stage Pipeline (v3.0)

```
┌─────────────────────────────────────────────────────────────┐
│     CP-WhisperX Pipeline v3.0 (12-Stage Context-Aware)      │
│         (Fully Modular + Caching + ML Optimization)         │
└─────────────────────────────────────────────────────────────┘

┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 01_demux    │→│ 02_tmdb     │→│ 03_glossary │
│ Audio extract│ │ Context     │ │ Terms load  │
│ + fingerprint│ │ metadata    │ │ + learning  │
└─────────────┘  └─────────────┘  └─────────────┘
       ↓                ↓                ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 04_source   │→│ 05_pyannote │→│ 06_whisperx │
│ Separation  │ │ VAD + diarize│ │ ASR (cached)│
│ (adaptive)  │ │              │ │             │
└─────────────┘  └─────────────┘  └─────────────┘
       ↓                ↓                ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 07_alignment│→│ 08_lyrics   │→│ 09_hallucin │
│ Word-level  │ │ Detection   │ │ Removal     │
│ MLX         │ │ (MANDATORY) │ │ (MANDATORY) │
└─────────────┘  └─────────────┘  └─────────────┘
       ↓                ↓                ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ 10_translate│→│ 11_subtitle │→│ 12_mux      │
│ Context-aware│ │ Multi-lang  │ │ Soft-embed  │
│ (cached)    │ │ generation  │ │ all tracks  │
└─────────────┘  └─────────────┘  └─────────────┘

[Cache Layer] - Intelligent caching across all stages
[ML Optimizer] - Adaptive quality and performance tuning
[Context Manager] - Cultural and temporal coherence

Each Stage Has:
  ✅ StageIO pattern implementation
  ✅ manifest.json (input/output tracking)
  ✅ Stage-specific log file
  ✅ Cache-aware processing
  ✅ Context propagation
  ✅ Written to own stage_dir only
  ✅ Enable/disable via config
  ✅ Comprehensive unit tests
  ✅ Integration test coverage
```

### Key Principles

1. **Stage Independence** - Self-contained, no shared state
2. **Data Lineage** - Complete tracking via manifests
3. **Configuration-Driven** - Enable/disable per job
4. **Context-Aware** - Cultural, temporal, speaker coherence
5. **Cache-Optimized** - Intelligent reuse of computations
6. **ML-Enhanced** - Adaptive quality and performance
7. **Fail-Safe** - Graceful degradation, automatic retry
8. **Testable** - Isolated testing per stage with standard samples

### Target Metrics

| Metric | Current | Target | Δ |
|--------|---------|--------|---|
| Architecture Alignment | 55% | 95% | +40% |
| StageIO Adoption | 10% | 100% | +90% |
| Manifest Tracking | 10% | 100% | +90% |
| Context Awareness | 40% | 90% | +50% |
| Cache Hit Rate | 0% | 70% | +70% |
| ML Optimization | 0% | 80% | +80% |
| Unit Test Coverage | 35% | 85% | +50% |
| Integration Tests | <10% | 75% | +65% |
| File Naming Compliance | 0% | 100% | +100% |
| Development Speed | 1x | 1.4x | +40% |
| Processing Speed (cached) | 1x | 2.0x | +100% |
| Subtitle Quality | 0.75 | 0.90 | +20% |

---

## Phase 0: Foundation ✅ COMPLETE

**Status:** ✅ 100% Complete (2025-12-03)  
**Duration:** 8 weeks  
**Effort:** 80 hours  
**Priority:** P0 Critical

### Achievements

**1. Code Quality Standards (100% Compliance)**
- ✅ Type hints: 140+ added
- ✅ Docstrings: 80+ added
- ✅ Logger usage: All print() converted
- ✅ Import organization: Standard/Third-party/Local
- ✅ Error handling: Proper try/except everywhere

**2. Configuration System**
- ✅ Cleaned config/.env.pipeline (1,078→1,052 lines)
- ✅ Removed 8 redundant parameters
- ✅ Marked 26 future parameters clearly
- ✅ Documented parameter lifecycle
- ✅ Job preparation flow documented

**3. Documentation**
- ✅ DEVELOPER_STANDARDS.md (+378 lines)
- ✅ copilot-instructions.md (+190 lines)
- ✅ File naming standards added
- ✅ Job preparation flow clarified

**4. Automation**
- ✅ Pre-commit hook active
- ✅ Automated validation working
- ✅ Blocks violations automatically

---

## Phase 1: File Naming & Standards

**Priority:** 🔴 P0 Critical  
**Duration:** 2 weeks  
**Effort:** 20 hours  
**Status:** 🟡 Ready to Start  
**Dependencies:** Phase 0 ✅  
**Blocks:** Phase 3

### Goal

Align all file names with documented `{NN}_{stage_name}.py` standard.

### Tasks

**1. Rename Stage Scripts (6 hours)**

```bash
# Active stages
git mv scripts/demux.py scripts/01_demux.py
git mv scripts/whisperx_asr.py scripts/06_whisperx_asr.py
git mv scripts/indictrans2_translator.py scripts/08_indictrans2_translation.py
git mv scripts/mux.py scripts/10_mux.py

# Existing stages
git mv scripts/tmdb_enrichment_stage.py scripts/02_tmdb_enrichment.py
git mv scripts/glossary_builder.py scripts/03_glossary_loader.py
git mv scripts/ner_extraction.py scripts/05_ner_extraction.py
git mv scripts/lyrics_detector.py scripts/06_lyrics_detection.py
git mv scripts/hallucination_removal.py scripts/07_hallucination_removal.py
```

**2. Update Imports (4 hours)**
- Update `run-pipeline.py`
- Update `prepare-job.py`
- Update test files
- Update documentation

**3. Testing & Validation (4 hours)**
- Run all tests
- Test each workflow
- Verify naming compliance

**4. Documentation (2 hours)**
- Update README.md
- Update all docs/ references
- Update examples

### Success Criteria

- [ ] All 10 stage scripts renamed
- [ ] All imports updated
- [ ] All tests passing
- [ ] Documentation current
- [ ] 100% naming compliance

---

## Phase 2: Testing Infrastructure

**Priority:** 🔴 P0 Critical (Updated)  
**Duration:** 3 weeks  
**Effort:** 50 hours (increased from 40)  
**Status:** 🟡 Ready to Start  
**Dependencies:** Phase 0 ✅  
**Blocks:** Phase 3

### Goal

Build comprehensive test infrastructure with standardized test media before refactoring.

### Tasks

**1. Test Media Setup (8 hours) 🆕**

- Create `in/test_media_index.json` with sample metadata
- Verify test samples exist and are accessible
- Create baseline quality metrics for each sample
- Document expected outputs for each workflow
- Create test data fixtures directory structure

**Test Sample Validation:**
```bash
# Verify samples
test -f "in/Energy Demand in AI.mp4" || echo "Missing Sample 1"
test -f "in/test_clips/jaane_tu_test_clip.mp4" || echo "Missing Sample 2"

# Get media info
ffprobe -v quiet -print_format json -show_format -show_streams "in/Energy Demand in AI.mp4"
ffprobe -v quiet -print_format json -show_format -show_streams "in/test_clips/jaane_tu_test_clip.mp4"
```

**2. Test Framework (10 hours)**

- Create `tests/conftest.py` with fixtures
- Add test media fixtures
- Add temp directory fixtures
- Add mock config fixtures
- Add cache fixtures for testing caching
- Add quality baseline fixtures

**3. Workflow Integration Tests (16 hours)**

**Sample 1 Tests (English Technical):**
```python
# tests/test_workflow_sample1.py

def test_transcribe_english_technical(test_media_sample1):
    """Test transcribe workflow on English technical content."""
    # Expected: High accuracy transcript in English
    pass

def test_translate_english_to_hindi(test_media_sample1):
    """Test translate workflow: English → Hindi."""
    # Expected: Accurate Hindi translation with technical terms
    pass

def test_translate_english_to_spanish(test_media_sample1):
    """Test translate workflow: English → Spanish."""
    pass
```

**Sample 2 Tests (Hinglish Bollywood):**
```python
# tests/test_workflow_sample2.py

def test_subtitle_hinglish_multilang(test_media_sample2):
    """Test subtitle workflow on Hinglish content with multiple output languages."""
    # Expected: Hindi, English, Gujarati, Tamil, Spanish subtitles
    # Output in organized subdirectory structure
    pass

def test_transcribe_hinglish(test_media_sample2):
    """Test transcribe workflow on Hinglish content."""
    # Expected: Accurate Hindi/Hinglish transcript
    pass

def test_translate_hindi_to_english(test_media_sample2):
    """Test translate workflow: Hindi → English."""
    pass

def test_context_awareness_subtitle(test_media_sample2):
    """Test context-aware features in subtitle generation."""
    # Test: Character names, cultural terms, speaker diarization
    pass
```

**4. Stage Unit Tests (12 hours)**

- Write 2+ tests per stage
- Test success cases
- Test error handling
- Test manifest tracking
- Test caching behavior
- Test context propagation

**5. Quality Baseline Tests (8 hours) 🆕**

```python
# tests/test_quality_baselines.py

def test_asr_accuracy_baseline_english():
    """Verify ASR accuracy meets ≥95% for English technical content."""
    pass

def test_asr_accuracy_baseline_hinglish():
    """Verify ASR accuracy meets ≥85% for Hinglish content."""
    pass

def test_subtitle_timing_accuracy():
    """Verify subtitle timing within ±200ms."""
    pass

def test_glossary_application_rate():
    """Verify glossary terms applied at 100% rate."""
    pass

def test_translation_fluency_baseline():
    """Verify translation fluency ≥88%."""
    pass
```

**6. Caching Tests (6 hours) 🆕**

```python
# tests/test_caching.py

def test_cache_identical_media():
    """Test cache hit on identical media processing."""
    # Expected: 95% time reduction
    pass

def test_cache_similar_media():
    """Test cache reuse on similar media."""
    # Expected: 40% time reduction
    pass

def test_cache_invalidation():
    """Test cache invalidation on config change."""
    pass

def test_glossary_learning():
    """Test glossary learning from previous jobs."""
    pass
```

**7. CI/CD Setup (4 hours)**

- Create GitHub Actions workflow
- Configure pytest with coverage
- Add coverage reporting
- Set up automated testing
- Add test sample download/setup in CI

### Success Criteria

- [ ] Test media index created
- [ ] Test framework established
- [ ] 30+ unit tests written (increased from 20)
- [ ] 10+ integration tests (increased from 5)
- [ ] Quality baseline tests implemented
- [ ] Caching tests implemented
- [ ] CI/CD pipeline running
- [ ] Coverage >65% (increased from 60%)

### Deliverables

- `in/test_media_index.json`
- `tests/conftest.py`
- `tests/fixtures/` directory
- `tests/test_NN_stage.py` (10 files)
- `tests/test_workflow_sample1.py`
- `tests/test_workflow_sample2.py`
- `tests/test_quality_baselines.py`
- `tests/test_caching.py`
- `.github/workflows/tests.yml`
- Coverage report
- Quality baseline report

---

## Phase 3: StageIO Migration

**Priority:** 🔴 P0 Critical  
**Duration:** 4 weeks  
**Effort:** 70 hours (increased from 60)  
**Status:** 🔴 Blocked by Phase 1-2  
**Dependencies:** Phase 1 ✅, Phase 2 ✅  
**Blocks:** Phase 4

### Goal

Migrate 5 active stages to StageIO pattern with manifest tracking and context propagation.

### Tasks

**1. Create Template (4 hours)**

- Create `shared/stage_template.py`
- Document StageIO pattern
- Add context-aware examples
- Add caching integration

**2. Migrate Stages (48 hours)**

- 01_demux.py (10 hours) - Add fingerprinting, cache lookup
- 06_whisperx_asr.py (12 hours, complex) - Add caching, context propagation
- 08_indictrans2_translation.py (10 hours) - Add translation memory, glossary
- 09_subtitle_generation.py (10 hours, new module) - Context-aware generation
- 10_mux.py (6 hours) - Organized output structure

**3. Context Management (10 hours) 🆕**

- Create `shared/context_manager.py`
- Implement context propagation between stages
- Add cultural context handling
- Add temporal coherence tracking
- Speaker/character tracking across stages

**4. Update Orchestrator (14 hours)**

- Update `run-pipeline.py`
- Add stage enable/disable logic
- Add manifest validation
- Add error recovery
- Add cache coordination
- Add context flow management

**5. Testing & Docs (4 hours)**

- Test all migrations
- Update documentation
- Write migration guide

### Success Criteria

- [ ] 5 stages use StageIO
- [ ] All have manifests
- [ ] All have dual logging
- [ ] Context propagation working
- [ ] Caching integrated
- [ ] Orchestrator updated
- [ ] All tests passing

---

## Phase 4: Stage Integration

**Priority:** 🟡 P2 Medium  
**Duration:** 8 weeks  
**Effort:** 105 hours (increased from 95)  
**Status:** 🔴 Blocked by Phase 3  
**Dependencies:** Phase 3 ✅  
**Blocks:** Phase 5

### Goal

Integrate 2 mandatory subtitle stages (lyrics detection, hallucination removal) for complete 12-stage context-aware pipeline.

### Tasks

**1. Integrate Stages (50 hours)**

- 02_tmdb_enrichment.py (10 hours) - Already uses StageIO, add context export
- 03_glossary_loader.py (10 hours) - Add learning capability
- 05_ner_extraction.py (10 hours) - Character/entity tracking
- 06_lyrics_detection.py (10 hours) - Music context for source separation
- 07_hallucination_removal.py (10 hours) - Context-aware filtering

**2. Dependency System (20 hours)**

- Create `shared/stage_dependencies.py`
- Add dependency validation
- Add required stage detection
- Test dependency logic
- Add conditional execution (e.g., skip source separation if clean audio)

**3. Configuration Enhancement (20 hours)**

- Add stage enable/disable config
- Add stage-specific parameters
- Add caching configuration per stage
- Add ML optimization settings
- Update config documentation

**4. Integration Testing with Test Media (15 hours) 🆕**

- Test 12-stage subtitle pipeline on Sample 1 (English)
- Test 12-stage subtitle pipeline on Sample 2 (Hinglish)
- Test selective execution
- Test dependency validation
- Test manifest end-to-end
- Test context propagation across all stages
- Test caching across full pipeline
- Validate quality baselines

### Success Criteria

- [ ] All 10 stages integrated
- [ ] Dependency system working
- [ ] Config-driven enable/disable
- [ ] Context flows through pipeline
- [ ] Caching works across stages
- [ ] 20+ integration tests (increased from 15)
- [ ] Documentation complete
- [ ] Quality targets met on test samples

---

## Phase 5: Advanced Features

**Priority:** 🟢 P3 Low  
**Duration:** 4 weeks  
**Effort:** 45 hours (increased from 30)  
**Status:** 🔴 Blocked by Phase 4  
**Dependencies:** Phase 4 ✅  
**Blocks:** None

### Goal

Add production-ready features for reliability, performance, and intelligent optimization.

### Tasks

**1. Retry Logic (10 hours)**

- Add `shared/retry_logic.py`
- Implement circuit breakers
- Add exponential backoff
- Test retry scenarios

**2. Performance Monitoring (10 hours)**

- Add `shared/performance_monitor.py`
- Collect timing metrics per stage
- Track memory usage
- Track cache hit rates
- Generate performance reports
- ML model performance tracking

**3. Caching System (15 hours) 🆕**

- Implement `shared/cache_manager.py`
- Audio fingerprint cache
- ASR results cache with quality-based keys
- Translation memory cache
- Glossary learning cache
- Cache cleanup and management
- Cache statistics and reporting

**4. ML Optimization (10 hours) 🆕**

- Implement `shared/ml_optimizer.py`
- Adaptive quality prediction model
- Model size selection based on audio quality
- Source separation decision logic
- Historical learning from job results
- Similarity-based optimization

**5. Cache Management Tools (5 hours) 🆕**

- Create `tools/cache-manager.sh`
- Cache statistics viewer
- Cache cleanup utilities
- Cache warmup for common scenarios
- Cache export/import for sharing

**6. Production Hardening (5 hours)**

- Add resource limits
- Add timeout handling
- Improve error messages
- Update documentation

### Success Criteria

- [ ] Retry logic working
- [ ] Circuit breakers active
- [ ] Performance metrics collected
- [ ] Caching system functional
- [ ] Cache hit rates >70%
- [ ] ML optimizer working
- [ ] Processing speed 2x faster (cached)
- [ ] Cache management tools working
- [ ] Documentation complete

### Deliverables

- `shared/retry_logic.py`
- `shared/performance_monitor.py`
- `shared/cache_manager.py`
- `shared/ml_optimizer.py`
- `shared/context_manager.py`
- `tools/cache-manager.sh`
- Production deployment guide
- Performance benchmarks
- Caching strategy guide
- ML optimization guide

---

## Success Metrics

### Technical Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Architecture Alignment | 55% | 95% | Code review |
| StageIO Adoption | 10% | 100% | Pattern usage |
| Manifest Tracking | 10% | 100% | Manifest presence |
| Context Awareness | 40% | 90% | Quality tests |
| Unit Test Coverage | 35% | 85% | pytest --cov |
| Integration Tests | <10% | 75% | Test execution |
| File Naming | 0% | 100% | Naming validator |
| Stage Integration | 50% | 100% | Pipeline test |
| Cache Hit Rate | 0% | 70% | Cache statistics |
| ML Optimization Active | 0% | 80% | Optimizer usage |

### Performance Metrics

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Dev Velocity | 1x | 1.4x | +40% |
| Debug Time | 1x | 0.4x | -60% |
| Integration Issues | 10/mo | 2/mo | -80% |
| Test Time | - | <10min | N/A |
| Processing (Clean Audio) | 10min | 5min | -50% |
| Processing (Cached) | 10min | 30sec | -95% |
| ASR Accuracy (English) | 90% | 95% | +5% |
| ASR Accuracy (Hindi) | 80% | 85% | +5% |
| Subtitle Quality | 75% | 90% | +20% |
| Context Preservation | 60% | 90% | +50% |

### Business Metrics

| Metric | Baseline | Target | Impact |
|--------|----------|--------|--------|
| Onboarding | 2 weeks | 1 week | -50% |
| Code Review | 4 hours | 2 hours | -50% |
| Incidents | - | <1/mo | High reliability |
| Releases | 1/mo | 2/wk | +8x |
| User Satisfaction | - | >4.5/5 | Quality target |
| Processing Cost | $1 | $0.50 | -50% (caching) |

### Quality Metrics (Test Media)

| Sample | Metric | Target | Validation |
|--------|--------|--------|------------|
| Sample 1 (English) | ASR WER | ≤5% | Automated test |
| Sample 1 (English) | Translation BLEU | ≥90% | Automated test |
| Sample 2 (Hinglish) | ASR WER | ≤15% | Automated test |
| Sample 2 (Hinglish) | Subtitle Quality | ≥88% | Human evaluation |
| Sample 2 (Hinglish) | Glossary Application | 100% | Automated test |
| Both | Subtitle Timing | ±200ms | Automated test |
| Both | Context Preservation | ≥80% | Human evaluation |

---

## Risk Management

### Identified Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking Changes | Medium | High | Comprehensive tests with standard samples |
| Timeline Overrun | Medium | Medium | Phased approach, can stop at Phase 3 |
| Scope Creep | Medium | Medium | Strict boundaries, defer features |
| Team Bandwidth | High | Medium | Part-time, 21-week timeline |
| Integration Failures | Low | High | Integration tests each phase |
| Performance Regression | Low | Medium | Benchmarks with test media |
| Cache Corruption | Low | High | Validation, checksums, auto-recovery |
| ML Model Drift | Low | Medium | Regular validation against baselines |
| Test Media Licensing | Low | Low | Use owned/licensed samples only |

### Mitigation Strategies

**1. Quality Assurance**
- Write tests before refactoring (Phase 2)
- Use standardized test media for consistency
- Test each stage independently
- Maintain backward compatibility
- Document breaking changes
- Validate against quality baselines

**2. Timeline Management**
- Weekly progress reviews
- Adjust scope if needed (Phase 5 optional)
- Can deploy after Phase 3 or 4
- 20% time buffer in estimates
- Track metrics against test samples

**3. Communication**
- Weekly status updates
- Document all changes
- Migration guides
- Clear rollback procedures
- Share test results regularly

**4. Caching Safety**
- Cache validation with checksums
- Automatic cache invalidation on errors
- Cache versioning
- Easy cache reset procedures
- Cache size limits and cleanup

---

## References

### Core Documentation

- [DEVELOPER_STANDARDS.md](developer/DEVELOPER_STANDARDS.md) - Code standards
- [copilot-instructions.md](../.github/copilot-instructions.md) - Quick reference
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Current status
- [ARCHITECTURE_INDEX.md](ARCHITECTURE_INDEX.md) - All architecture docs
- [AI_MODEL_ROUTING.md](AI_MODEL_ROUTING.md) - Model selection guide

### Related Documents

- [ARCHITECTURE_GAP_ANALYSIS.md](ARCHITECTURE_GAP_ANALYSIS.md) - Detailed gaps
- [CODE_EXAMPLES.md](CODE_EXAMPLES.md) - Pattern examples
- [LOGGING_ARCHITECTURE.md](logging/LOGGING_ARCHITECTURE.md) - Logging design
- [SUBTITLE_ACCURACY_ROADMAP.md](SUBTITLE_ACCURACY_ROADMAP.md) - Quality improvements

### Configuration

- `config/.env.pipeline` - 1,054 lines, 179 parameters
- `.github/copilot-instructions.md` - Development guidelines
- `.git/hooks/pre-commit` - Automated validation

---

## Appendix

### Phase Summary

| Phase | Weeks | Hours | Status | Key Deliverables |
|-------|-------|-------|--------|------------------|
| 0: Foundation | ✅ Done | 80 | Complete | Standards, config, hooks |
| 1: File Naming | 2 | 20 | Ready | Renamed scripts, imports |
| 2: Testing | 3 | 50 | Ready | Framework, test media, 30+ tests |
| 3: StageIO | 4 | 70 | Blocked | 5 migrated stages, context |
| 4: Integration | 8 | 105 | In Progress | 12-stage pipeline (lyrics/hallucination integrated) |
| 5: Advanced | 4 | 45 | Blocked | Caching, ML, monitoring |
| **TOTAL** | **21** | **370** | **22% Done** | **Complete v3.0** |

### Glossary

- **StageIO** - Standardized pattern with manifest tracking and dual logging
- **Manifest** - JSON file tracking inputs/outputs with SHA256 hashes
- **Data Lineage** - Complete audit trail of transformations
- **Stage Isolation** - No shared state, files only
- **Dual Logging** - Main pipeline log + per-stage log
- **Job Config** - Job-specific .env.pipeline with overrides
- **Context Awareness** - Cultural, temporal, speaker coherence
- **Caching** - Intelligent reuse of computation results
- **ML Optimization** - Adaptive quality and performance tuning
- **Test Media** - Standardized samples for validation

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-27 | Initial roadmap |
| 2.0 | 2025-12-03 | Updated with Phase 0 complete, config cleanup, file naming |
| 3.0 | 2025-12-03 | Added testing infrastructure, workflows, caching, ML optimization |

---

**Document Status:** ✅ Active  
**Next Review:** 2025-12-10  
**Owner:** Development Team  
**Last Updated:** 2025-12-03

---

**END OF DOCUMENT**
