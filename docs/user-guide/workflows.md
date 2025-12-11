# Workflows Guide

**Version:** 3.0  
**Date:** 2025-12-03  
**Status:** ✅ Active - Aligned with Architecture v3.0

Complete guide to context-aware workflows in CP-WhisperX-App with intelligent caching and ML optimization.

---

## Table of Contents

1. [Overview](#overview)
2. [Standard Test Media](#standard-test-media)
3. [Subtitle Workflow](#subtitle-workflow)
4. [Transcribe Workflow](#transcribe-workflow)
5. [Translate Workflow](#translate-workflow)
6. [Quality Targets](#quality-targets)
7. [Caching & Performance](#caching--performance)
8. [Advanced Usage](#advanced-usage)
9. [Troubleshooting](#troubleshooting)

---

## Overview

CP-WhisperX-App supports three **context-aware** workflows with intelligent caching and ML-based optimization:

| Workflow | Input | Output | Use Case | Context Features |
|----------|-------|--------|----------|------------------|
| **Subtitle** | Indic/Hinglish media | Multi-language soft-embedded subtitles | Bollywood/regional content | Character names, cultural terms, speaker diarization |
| **Transcribe** | Any media | Transcript in SOURCE language | ASR in native language | Domain terms, proper nouns, native script |
| **Translate** | Any media | Transcript in TARGET language | Cross-language content | Cultural adaptation, glossary, formality |

### Key Innovations

**Context-Aware Processing:**
- Cultural term preservation (beta, bhai, ji, etc.)
- Character name consistency (via glossary)
- Temporal coherence (same term throughout)
- Speaker attribution (multi-speaker scenes)

**Intelligent Caching:**
- Audio fingerprinting (skip identical media)
- ASR results cache (70% hit rate target)
- Translation memory (60% hit rate)
- Glossary learning (improve over time)

**ML Optimization:**
- Adaptive quality prediction
- Model size selection based on audio quality
- Source separation decision logic
- Similarity-based optimization

---

## Standard Test Media

Use these samples for testing and baseline validation:

### Sample 1: English Technical Content
**File:** `in/Energy Demand in AI.mp4`  
**Language:** English  
**Type:** Technical/Educational  
**Duration:** ~2-5 minutes  
**Workflows:** Transcribe, Translate

**Quality Baselines:**
- ASR Accuracy: ≥95% WER
- Translation BLEU: ≥90%
- Technical term preservation: 100%

**Test Commands:**
```bash
# Transcribe: English → English
./prepare-job.sh --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe --source-language en
./run-pipeline.sh --job-dir out/LATEST

# Translate: English → Hindi
./prepare-job.sh --media "in/Energy Demand in AI.mp4" \
  --workflow translate --source-language en --target-language hi
./run-pipeline.sh --job-dir out/LATEST
```

### Sample 2: Hinglish Bollywood Content
**File:** `in/test_clips/jaane_tu_test_clip.mp4`  
**Language:** Hindi/Hinglish (mixed)  
**Type:** Entertainment (Bollywood)  
**Duration:** ~1-3 minutes  
**Workflows:** Subtitle, Transcribe, Translate

**Quality Baselines:**
- ASR Accuracy: ≥85% WER (Hinglish)
- Subtitle Quality: ≥88%
- Context Awareness: ≥80%
- Glossary Application: 100%

**Test Commands:**
```bash
# Subtitle: Hindi → Multiple languages
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle --source-language hi \
  --target-languages en,gu,ta,es,ru,zh,ar
./run-pipeline.sh --job-dir out/LATEST

# Transcribe: Hindi → Hindi
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe --source-language hi
./run-pipeline.sh --job-dir out/LATEST

# Translate: Hindi → English
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate --source-language hi --target-language en
./run-pipeline.sh --job-dir out/LATEST
```

---

## Subtitle Workflow

**Purpose:** Generate context-aware, high-accuracy multilingual subtitles for Bollywood/Indic media with soft-embedding.

### Use Case

Perfect for:
- Bollywood movies and web series
- Regional Indic language content
- Code-mixed Hinglish content
- Content requiring cultural adaptation

### Pipeline Flow

```
Input Media (jaane_tu_test_clip.mp4)
    ↓
01_demux          → Extract audio + fingerprint
    ↓
02_tmdb           → Fetch movie metadata for context
    ↓
03_glossary_load  → Load character names, cultural terms
    ↓
04_source_sep     → Separate dialogue from music (optional, adaptive)
    ↓
05_pyannote_vad   → Detect speech segments, speaker diarization
    ↓
06_whisperx_asr   → Transcribe with word-level timestamps (cached)
    ↓
07_alignment      → Refine word alignment (MLX on Apple Silicon)
    ↓
08_translate      → Generate multiple subtitle tracks (cached):
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

### Basic Usage

```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow subtitle \
  --source-language hi \
  --target-languages en,gu,ta,es

./run-pipeline.sh --job-dir out/LATEST
```

### Context-Aware Features

**1. Character Names (via Glossary)**
```
Example: "Jaane Tu Ya Jaane Na"
- Character: Jai, Aditi, Meow
- Preserved consistently across all subtitle tracks
- Applied with 100% accuracy
```

**2. Cultural Terms**
```
Hindi Idioms & Terms:
- "beta" → Context: affectionate (not literal "son")
- "bhai" → Brother (informal, friendly)
- "ji" → Respectful suffix (preserve in translation)
```

**3. Speaker Diarization**
```
Multi-speaker scenes:
- Speaker 01 (Jai): "Tum mere liye kya ho?"
- Speaker 02 (Aditi): "Main tumhari best friend hoon"
- Consistent attribution throughout scene
```

**4. Temporal Coherence**
```
Terminology consistency:
- Scene 1: "Best friend" (established)
- Scene 2: "Best friend" (maintained, not "close friend")
- Scene 3: "Best friend" (consistent throughout)
```

**5. Tone Adaptation**
```
Formal vs. Casual:
- Romantic dialogue: Casual, intimate tone
- Family scenes: Respectful, formal tone
- Friend banter: Casual, colloquial
```

### Quality Targets

| Metric | Target | Validation |
|--------|--------|------------|
| ASR Accuracy (Hinglish) | ≥85% WER | Automated test |
| Subtitle Timing | ±200ms | Automated test |
| Translation Fluency | ≥88% | Human evaluation |
| Context Consistency | ≥80% | Human evaluation |
| Glossary Application | 100% | Automated test |

### Output Structure

```
out/2025/12/03/user/0001/
├── 10_mux/
│   └── jaane_tu_test_clip/
│       ├── jaane_tu_test_clip_subtitled.mkv  # Video with all subtitle tracks
│       ├── subtitles/
│       │   ├── jaane_tu_test_clip.hi.srt     # Hindi (source)
│       │   ├── jaane_tu_test_clip.en.srt     # English
│       │   ├── jaane_tu_test_clip.gu.srt     # Gujarati
│       │   ├── jaane_tu_test_clip.ta.srt     # Tamil
│       │   ├── jaane_tu_test_clip.es.srt     # Spanish
│       │   ├── jaane_tu_test_clip.ru.srt     # Russian
│       │   ├── jaane_tu_test_clip.zh.srt     # Chinese
│       │   └── jaane_tu_test_clip.ar.srt     # Arabic
│       └── manifest.json                      # Metadata
├── 01_demux/
│   ├── audio.wav                              # Extracted audio
│   ├── stage.log                              # Stage execution log
│   └── manifest.json                          # I/O tracking
├── 02_tmdb/
│   ├── metadata.json                          # Movie context
│   ├── stage.log
│   └── manifest.json
├── 03_glossary_load/
│   ├── glossary.json                          # Character names, cultural terms
│   ├── stage.log
│   └── manifest.json
└── logs/
    └── 99_pipeline_TIMESTAMP.log              # Main pipeline log
```

### Advanced Options

```bash
# Custom glossary
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en,gu \
  --glossary glossary/my_movie_terms.txt

# Disable source separation (clean audio)
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en \
  --config SOURCE_SEPARATION_ENABLED=false

# Disable caching (force fresh processing)
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en \
  --no-cache

# Enable debug logging
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en \
  --log-level DEBUG
```

---

## Transcribe Workflow

**Purpose:** Create high-accuracy text transcript in SAME language as source audio with context awareness.

### Use Case

Perfect for:
- Technical content transcription (English)
- Hindi/Indic language transcription (native script)
- Multi-language content (each in its own language)
- Domain-specific content (medical, legal, etc.)

### Pipeline Flow

```
Input Media (Energy Demand in AI.mp4 or jaane_tu_test_clip.mp4)
    ↓
01_demux          → Extract audio + fingerprint
    ↓
02_tmdb           → Fetch metadata if applicable (optional)
    ↓
03_glossary_load  → Load domain-specific terms
    ↓
04_source_sep     → Clean audio (optional, adaptive)
    ↓
05_pyannote_vad   → Speech detection
    ↓
06_whisperx_asr   → Transcribe in source language (cached):
    │               - English media → English transcript
    │               - Hindi media → Hindi transcript (Devanagari)
    │               - Indic media → Same Indic language
    │               - Spanish media → Spanish transcript
    ↓
07_alignment      → Word-level timestamp refinement (±100ms)
    ↓
Output: out/{date}/{user}/{job}/07_alignment/
    ├── transcript.txt                 # Plain text transcript
    ├── transcript.json                # With word-level timestamps
    ├── stage.log                      # Stage execution log
    └── manifest.json                  # Processing metadata
```

### Basic Usage

**English Technical Content:**
```bash
./prepare-job.sh --media "in/Energy Demand in AI.mp4" \
  --workflow transcribe \
  --source-language en

./run-pipeline.sh --job-dir out/LATEST
```

**Hindi/Hinglish Content:**
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow transcribe \
  --source-language hi

./run-pipeline.sh --job-dir out/LATEST
```

### Context-Aware Features

**1. Domain Terminology**
```
Technical Content:
- "AI" → Artificial Intelligence (preserved)
- "energy demand" → Technical term (not generic)
- "neural networks" → Capitalized properly
```

**2. Proper Nouns**
```
Names, Places, Organizations:
- "OpenAI" → Correctly capitalized
- "Silicon Valley" → Proper noun detection
- "Google" → Brand name preservation
```

**3. Language-Specific**
```
Hindi/Indic:
- Output in Devanagari script (native)
- Proper punctuation (।, ?)
- Code-mixed handling (Hindi + English)
```

**4. Punctuation**
```
Context-aware sentence segmentation:
- Technical: "The model achieves 95% accuracy."
- Casual: "Really? That's amazing!"
- Questions: "What is the energy demand?"
```

**5. Capitalization (English)**
```
Proper noun detection:
- Sentence start: "The model..."
- Names: "Dr. Smith..."
- Acronyms: "AI, GPU, CPU"
```

### Quality Targets

| Content Type | Target WER | Timestamp Precision | Proper Noun Accuracy |
|-------------|-----------|-------------------|---------------------|
| English Technical | ≥95% | ±100ms | ≥90% |
| Hindi/Indic | ≥85% | ±100ms | ≥85% |
| Other Languages | ≥90% | ±100ms | ≥90% |

### Output Structure

```
out/2025/12/03/user/0001/
├── 07_alignment/
│   ├── transcript.txt                # Human-readable transcript
│   ├── transcript.json               # With word-level timestamps
│   ├── stage.log                     # Stage execution log
│   └── manifest.json                 # I/O tracking
├── 06_whisperx_asr/
│   ├── segments.json                 # ASR output (cached)
│   ├── stage.log
│   └── manifest.json
├── 01_demux/
│   ├── audio.wav                     # Extracted audio
│   ├── fingerprint.json              # Audio characteristics (cached)
│   ├── stage.log
│   └── manifest.json
└── logs/
    └── 99_pipeline_TIMESTAMP.log     # Main pipeline log
```

### transcript.json Format

```json
{
  "language": "en",
  "duration": 180.5,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "The energy demand in AI has grown exponentially.",
      "words": [
        {"word": "The", "start": 0.0, "end": 0.2},
        {"word": "energy", "start": 0.2, "end": 0.6},
        {"word": "demand", "start": 0.6, "end": 1.0},
        ...
      ]
    }
  ]
}
```

### Advanced Options

```bash
# Custom glossary for domain terms
./prepare-job.sh --media in/medical_lecture.mp4 \
  --workflow transcribe --source-language en \
  --glossary glossary/medical_terms.txt

# Process specific time range
./prepare-job.sh --media in/long_video.mp4 \
  --workflow transcribe --source-language hi \
  --start-time 00:10:00 --end-time 00:15:00

# Use larger model for higher accuracy
./prepare-job.sh --media in/audio.mp4 \
  --workflow transcribe --source-language en \
  --config WHISPERX_MODEL=large-v3

# Disable caching
./prepare-job.sh --media in/audio.mp4 \
  --workflow transcribe --source-language en \
  --no-cache
```

---

## Translate Workflow

**Purpose:** Create high-accuracy transcript in SPECIFIED target language with context preservation and cultural adaptation.

### Use Case

Perfect for:
- Hindi → English translation (Bollywood content)
- Hindi → Spanish/Russian/Chinese (global distribution)
- Hindi → Gujarati/Tamil (Indic-to-Indic, regional content)
- English → Hindi/Gujarati (localization)

### Pipeline Flow

```
Input Media
    ↓
01_demux          → Extract audio + fingerprint
    ↓
02_tmdb           → Fetch metadata for cultural context
    ↓
03_glossary_load  → Load bilingual glossary
    ↓
04_source_sep     → Clean audio (optional, adaptive)
    ↓
05_pyannote_vad   → Speech detection
    ↓
06_whisperx_asr   → Transcribe in source language (cached)
    ↓
07_alignment      → Refine timestamps
    ↓
08_translate      → Translate to target language (cached):
    │               - Hindi → English (IndicTrans2)
    │               - Hindi → Spanish/Russian/Chinese/Arabic (NLLB-200)
    │               - Hindi → Gujarati/Tamil (IndicTrans2, Indic-to-Indic)
    │               - English → Hindi/Gujarati (IndicTrans2)
    │               - Preserve context, idioms, cultural nuances
    ↓
Output: out/{date}/{user}/{job}/08_translate/
    ├── transcript_{target_lang}.txt   # Translated transcript
    ├── transcript_{target_lang}.json  # With timestamps
    ├── translation_metadata.json      # Quality metrics
    ├── stage.log                      # Stage execution log
    └── manifest.json                  # Processing metadata
```

### Basic Usage

**Hindi → English:**
```bash
./prepare-job.sh --media in/test_clips/jaane_tu_test_clip.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language en

./run-pipeline.sh --job-dir out/LATEST
```

**Hindi → Spanish (Non-Indic):**
```bash
./prepare-job.sh --media in/hindi_movie.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language es

./run-pipeline.sh --job-dir out/LATEST
```

**Hindi → Gujarati (Indic-to-Indic):**
```bash
./prepare-job.sh --media in/hindi_content.mp4 \
  --workflow translate \
  --source-language hi \
  --target-language gu

./run-pipeline.sh --job-dir out/LATEST
```

### Context-Aware Features

**1. Cultural Adaptation**
```
Idioms & Metaphors:
- Source (Hindi): "दिल से" (dil se, literally "from heart")
- Target (English): "Sincerely" (cultural adaptation)
- Context: Formal vs. casual maintained
```

**2. Bilingual Glossary**
```
Character Names:
- Hindi: जय (Jai) → English: Jai (preserved)
- Hindi: अदिति (Aditi) → English: Aditi (preserved)
- 100% glossary term application
```

**3. Formality Levels**
```
Hindi Respect Markers:
- "आप" (aap, formal you) → English: Formal tone
- "तुम" (tum, casual you) → English: Casual tone
- Context maintained across languages
```

**4. Temporal Consistency**
```
Same Term Throughout:
- Segment 1: "best friend" (established)
- Segment 2: "best friend" (maintained)
- Segment 3: "best friend" (not "close friend")
```

**5. Named Entities**
```
Transliteration:
- Hindi: मुंबई → English: Mumbai (standard)
- Hindi: राज → English: Raj (name preserved)
- Place names: Standard transliteration
```

**6. Numeric/Date Formats**
```
Localized Formatting:
- English: December 3, 2025 → Hindi: ३ दिसंबर २०२५
- Numbers: 1,000 → 1000 (Indian number system)
- Time: 12:30 PM → दोपहर १२:३० (cultural format)
```

### Translation Routing

**Model Selection (Automatic):**

| Source | Target | Model | Quality Target |
|--------|--------|-------|---------------|
| Hindi | English | IndicTrans2 | ≥90% BLEU |
| Hindi | Gujarati/Tamil (Indic) | IndicTrans2 | ≥88% BLEU |
| Hindi | Spanish/Russian/Chinese (Non-Indic) | NLLB-200 | ≥85% BLEU |
| English | Hindi/Gujarati | IndicTrans2 | ≥88% BLEU |

**Fallback Logic:**
- Primary: IndicTrans2 (Indic languages)
- Fallback: NLLB-200 (if IndicTrans2 fails)
- Emergency: Hybrid approach

### Quality Targets

| Translation Type | BLEU Score | Glossary Application | Cultural Adaptation |
|-----------------|-----------|---------------------|---------------------|
| Hindi → English | ≥90% | 100% | ≥80% |
| Indic-to-Indic | ≥88% | 100% | ≥85% |
| Hindi → Non-Indic | ≥85% | 100% | ≥75% |

### Output Structure

```
out/2025/12/03/user/0001/
├── 08_translate/
│   ├── transcript_en.txt             # Translated transcript (English)
│   ├── transcript_en.json            # With timestamps
│   ├── translation_metadata.json     # Quality metrics
│   ├── stage.log                     # Stage execution log
│   └── manifest.json                 # I/O tracking
├── 07_alignment/
│   ├── transcript.txt                # Source transcript (Hindi)
│   ├── transcript.json               # With word-level timestamps
│   └── manifest.json
├── 03_glossary_load/
│   ├── glossary.json                 # Bilingual glossary (cached)
│   └── manifest.json
└── logs/
    └── 99_pipeline_TIMESTAMP.log     # Main pipeline log
```

### translation_metadata.json Format

```json
{
  "source_language": "hi",
  "target_language": "en",
  "model_used": "IndicTrans2",
  "total_segments": 42,
  "glossary_terms_applied": 8,
  "glossary_application_rate": 1.0,
  "estimated_bleu_score": 0.92,
  "processing_time_seconds": 12.5,
  "cached": false,
  "cache_hit_rate": 0.0
}
```

### Advanced Options

```bash
# Bilingual glossary
./prepare-job.sh --media in/movie.mp4 \
  --workflow translate --source-language hi --target-language en \
  --glossary glossary/bilingual_terms.txt

# Force specific translation model
./prepare-job.sh --media in/audio.mp4 \
  --workflow translate --source-language hi --target-language en \
  --config TRANSLATION_MODEL=IndicTrans2

# Multiple target languages (use subtitle workflow instead)
# For multiple translations, use subtitle workflow

# Disable caching
./prepare-job.sh --media in/audio.mp4 \
  --workflow translate --source-language hi --target-language en \
  --no-cache
```

---

## Quality Targets

### Overall Quality Metrics

| Workflow | Metric | Target | Validation Method |
|----------|--------|--------|------------------|
| Subtitle | ASR WER (Hinglish) | ≤15% | Automated test |
| Subtitle | Subtitle Quality | ≥88% | Human evaluation |
| Subtitle | Timing Accuracy | ±200ms | Automated test |
| Subtitle | Context Preservation | ≥80% | Human evaluation |
| Subtitle | Glossary Application | 100% | Automated test |
| Transcribe | ASR WER (English) | ≤5% | Automated test |
| Transcribe | ASR WER (Hindi) | ≤15% | Automated test |
| Transcribe | Timestamp Precision | ±100ms | Automated test |
| Transcribe | Proper Noun Accuracy | ≥90% | Automated test |
| Translate | BLEU (Hindi→English) | ≥90% | Automated test |
| Translate | BLEU (Indic-to-Indic) | ≥88% | Automated test |
| Translate | BLEU (Hindi→Non-Indic) | ≥85% | Automated test |
| Translate | Glossary Application | 100% | Automated test |
| Translate | Cultural Adaptation | ≥80% | Human evaluation |

### Validation Commands

```bash
# Run quality baseline tests
pytest tests/test_quality_baselines.py -v

# Test specific workflow
pytest tests/test_workflow_sample1.py::test_transcribe_english_technical -v
pytest tests/test_workflow_sample2.py::test_subtitle_hinglish_multilang -v

# Test caching
pytest tests/test_caching.py -v

# Generate quality report
./tools/quality-report.sh --job-dir out/LATEST
```

---

## Caching & Performance

### Caching Layers

**1. Audio Fingerprint Cache**
- **Purpose:** Skip processing for identical media
- **Cache Key:** `SHA256(audio_content)`
- **Benefit:** 95% time reduction on identical media
- **Location:** `~/.cp-whisperx/cache/fingerprints/`

**2. ASR Results Cache**
- **Purpose:** Reuse transcriptions
- **Cache Key:** `SHA256(audio + model + language + config)`
- **Benefit:** 70% time reduction on same audio
- **Target Hit Rate:** 70%
- **Location:** `~/.cp-whisperx/cache/asr/`

**3. Translation Memory Cache**
- **Purpose:** Reuse translations
- **Cache Key:** `SHA256(source + src_lang + tgt_lang + glossary)`
- **Benefit:** 60% time reduction on similar content
- **Target Hit Rate:** 60%
- **Location:** `~/.cp-whisperx/cache/translations/`

**4. Glossary Learning Cache**
- **Purpose:** Improve accuracy on similar content
- **Storage:** Per-movie learned terms
- **Benefit:** 90% glossary hit rate on same movie/series
- **Location:** `~/.cp-whisperx/cache/glossary_learned/`

### Performance Improvements

| Scenario | First Run | Subsequent Run | Improvement |
|----------|-----------|----------------|-------------|
| Identical media | 10 min | 30 sec | 95% faster |
| Same movie, different cut | 10 min | 6 min | 40% faster |
| Similar Bollywood movie | 10 min | 8 min | 20% faster |
| Similar language/genre | 10 min | 9 min | 10% faster |

### ML Optimization

**Adaptive Quality Prediction:**
- Audio quality metrics (SNR, clarity)
- Optimal Whisper model size selection
- Source separation decision (yes/no)
- Expected processing time estimate

**Context Learning:**
- Character name recognition from history
- Cultural term patterns
- Translation memory from approved translations

**Similarity-Based:**
- Audio fingerprint matching (chromaprint)
- Content-based similarity (same movie)
- Language/accent similarity
- Genre similarity

### Cache Management

**View Cache Statistics:**
```bash
./tools/cache-manager.sh --stats

# Output:
# Cache Statistics:
# - Total Size: 12.5 GB / 50 GB (25%)
# - ASR Cache: 8.2 GB (1,234 entries)
# - Translation Cache: 3.1 GB (567 entries)
# - Fingerprint Cache: 1.2 GB (89 entries)
# - Oldest Entry: 45 days ago
# - Cache Hit Rate (last 30 days): 72%
```

**Clear Specific Cache:**
```bash
# Clear ASR cache only
./tools/cache-manager.sh --clear asr

# Clear translations only
./tools/cache-manager.sh --clear translations

# Clear old cache (>90 days)
./tools/cache-manager.sh --cleanup

# Clear all cache
./tools/cache-manager.sh --clear all
```

**Disable Caching for One Job:**
```bash
./prepare-job.sh --media in/file.mp4 --workflow transcribe \
  --source-language en --no-cache
```

### Configuration

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

---

## Advanced Usage

### Custom Glossary

**Create Glossary File:**
```
# glossary/my_movie_terms.txt
Jai:Jai
Aditi:Aditi
Meow:Meow
beta:dear
bhai:brother
```

**Use in Workflow:**
```bash
./prepare-job.sh --media in/movie.mp4 --workflow subtitle \
  --source-language hi --target-languages en \
  --glossary glossary/my_movie_terms.txt
```

### Time Range Processing

```bash
# Process specific time range (useful for testing)
./prepare-job.sh --media in/long_movie.mp4 \
  --workflow subtitle --source-language hi --target-languages en \
  --start-time 00:10:00 --end-time 00:15:00
```

### Debug Logging

```bash
# Enable debug logging for troubleshooting
./prepare-job.sh --media in/audio.mp4 \
  --workflow transcribe --source-language en \
  --log-level DEBUG
```

### Configuration Overrides

```bash
# Override specific parameters
./prepare-job.sh --media in/audio.mp4 \
  --workflow transcribe --source-language en \
  --config WHISPERX_MODEL=large-v3 \
  --config WHISPERX_BATCH_SIZE=16 \
  --config ENABLE_CACHING=false
```

### Multiple Jobs in Parallel

```bash
# Job 1: Subtitle workflow
./prepare-job.sh --media in/movie1.mp4 --workflow subtitle \
  --source-language hi --target-languages en
./run-pipeline.sh --job-dir out/LATEST &

# Job 2: Transcribe workflow
./prepare-job.sh --media in/movie2.mp4 --workflow transcribe \
  --source-language en
./run-pipeline.sh --job-dir out/LATEST &

# Wait for both to complete
wait
```

---

## Troubleshooting

### Common Issues

**1. Low ASR Accuracy**

**Symptoms:**
- WER > 20% on English content
- WER > 30% on Hindi content
- Many incorrect words

**Solutions:**
```bash
# Use larger model
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language en --config WHISPERX_MODEL=large-v3

# Enable source separation (clean audio)
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language hi --config SOURCE_SEPARATION_ENABLED=true

# Add custom glossary for domain terms
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language en --glossary glossary/technical_terms.txt
```

**2. Subtitle Timing Issues**

**Symptoms:**
- Subtitles appear too early/late
- Timing accuracy > ±200ms

**Solutions:**
```bash
# Check alignment stage logs
cat out/LATEST/07_alignment/stage.log

# Verify audio quality
./tools/audio-quality-check.sh --media in/audio.mp4

# Adjust subtitle timing manually (post-processing)
./tools/adjust-subtitle-timing.sh --input out/LATEST/10_mux/movie/subtitles/movie.en.srt --offset +0.5
```

**3. Glossary Terms Not Applied**

**Symptoms:**
- Character names incorrect
- Cultural terms translated literally
- Glossary application rate < 100%

**Solutions:**
```bash
# Check glossary format (tab-separated, one per line)
cat glossary/my_terms.txt

# Verify glossary loaded
cat out/LATEST/03_glossary_load/glossary.json

# Check translation metadata
cat out/LATEST/08_translate/translation_metadata.json

# Debug glossary application
./prepare-job.sh --media in/audio.mp4 --workflow subtitle \
  --source-language hi --target-languages en \
  --glossary glossary/my_terms.txt --log-level DEBUG
```

**4. Cache Not Working**

**Symptoms:**
- Identical media re-processing takes full time
- Cache hit rate = 0%

**Solutions:**
```bash
# Verify caching enabled
grep "ENABLE_CACHING" config/.env.pipeline

# Check cache statistics
./tools/cache-manager.sh --stats

# Clear corrupted cache
./tools/cache-manager.sh --clear all

# Test with fresh cache
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language en
./run-pipeline.sh --job-dir out/LATEST  # First run (cache miss)
./run-pipeline.sh --job-dir out/LATEST  # Second run (cache hit expected)
```

**5. Translation Quality Issues**

**Symptoms:**
- BLEU score < target
- Cultural context lost
- Formality incorrect

**Solutions:**
```bash
# Use IndicTrans2 for Indic languages explicitly
./prepare-job.sh --media in/audio.mp4 --workflow translate \
  --source-language hi --target-language en \
  --config TRANSLATION_MODEL=IndicTrans2

# Add bilingual glossary
./prepare-job.sh --media in/audio.mp4 --workflow translate \
  --source-language hi --target-language en \
  --glossary glossary/bilingual_terms.txt

# Enable context-aware translation
./prepare-job.sh --media in/audio.mp4 --workflow translate \
  --source-language hi --target-language en \
  --config TRANSLATION_CONTEXT_AWARE=true
```

### Getting Help

**Check Logs:**
```bash
# Main pipeline log
cat out/LATEST/logs/99_pipeline_TIMESTAMP.log

# Stage-specific logs
cat out/LATEST/01_demux/stage.log
cat out/LATEST/06_whisperx_asr/stage.log
cat out/LATEST/08_translate/stage.log

# Stage manifests (I/O tracking)
cat out/LATEST/*/manifest.json
```

**Run Validation:**
```bash
# Test quality baselines
pytest tests/test_quality_baselines.py -v

# Test specific workflow
pytest tests/test_workflow_sample2.py -v

# Validate configuration
./tools/validate-config.sh
```

**Report Issue:**
- Include: Pipeline log, stage logs, manifests
- Specify: Workflow, language pair, media type
- Attach: Sample media (if possible)

---

## See Also

- [Architecture Implementation Roadmap](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) - Full system design
- [Configuration Guide](configuration.md) - Configuration reference
- [Troubleshooting Guide](troubleshooting.md) - Problem solving
- [Developer Standards](../developer/DEVELOPER_STANDARDS.md) - Code standards
- [Testing Guide](../developer/testing.md) - Test infrastructure

---

**Document Version:** 3.0  
**Last Updated:** 2025-12-03  
**Status:** ✅ Active - Aligned with Architecture v3.0
