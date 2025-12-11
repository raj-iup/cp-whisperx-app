# Caching & ML Optimization Guide

**Version:** 1.0  
**Date:** 2025-12-03  
**Status:** ✅ Active - Target Architecture v3.0

Comprehensive guide to intelligent caching and machine learning-based optimization in CP-WhisperX-App.

---

## Table of Contents

1. [Overview](#overview)
2. [Caching Architecture](#caching-architecture)
3. [ML Optimization](#ml-optimization)
4. [Configuration](#configuration)
5. [Cache Management](#cache-management)
6. [Performance Metrics](#performance-metrics)
7. [Implementation Details](#implementation-details)
8. [Troubleshooting](#troubleshooting)

---

## Overview

### Purpose

Enable subsequent workflows with similar media sources to perform optimally over time through:
- **Intelligent Caching:** Reuse computation results across jobs
- **ML-Based Optimization:** Adaptive quality and performance tuning
- **Context Learning:** Improve accuracy from historical data

### Expected Benefits

| Scenario | First Run | Subsequent Run | Improvement |
|----------|-----------|----------------|-------------|
| Identical media | 10 min | 30 sec | **95% faster** |
| Same movie, different cut | 10 min | 6 min | **40% faster** |
| Similar Bollywood movie | 10 min | 8 min | **20% faster** |
| Similar language/genre | 10 min | 9 min | **10% faster** |

**Target Cache Hit Rates:**
- Audio fingerprint: 80% on re-processing
- ASR results: 70% on same media
- Translations: 60% on similar content
- Glossary terms: 90% on same movie/series

---

## Caching Architecture

### Cache Hierarchy

```
{cache_dir}/
├── fingerprints/           # Layer 1: Audio fingerprints
│   ├── {hash}.json
│   └── index.db
├── models/                 # Layer 2: Model weights (shared)
│   ├── whisperx/
│   ├── indictrans2/
│   └── pyannote/
├── asr/                    # Layer 3: ASR results
│   ├── {hash}.json
│   └── index.db
├── translations/           # Layer 4: Translation memory
│   ├── {hash}.json
│   └── index.db
└── glossary_learned/       # Layer 5: Learned glossary
    ├── {movie_id}/
    └── global/
```

### Layer 1: Audio Fingerprint Cache

**Purpose:** Skip demux/analysis for identical media

**Storage Location:** `{cache_dir}/fingerprints/`

**Cache Key:** `SHA256(audio_content)`

**Cached Data:**
```json
{
  "audio_hash": "sha256_hash_value",
  "duration": 180.5,
  "sample_rate": 16000,
  "channels": 1,
  "language_detected": "hi",
  "noise_profile": {
    "snr_db": 25.3,
    "background_noise_level": "low"
  },
  "created_at": "2025-12-03T10:30:00Z",
  "source_file": "in/test_clips/jaane_tu_test_clip.mp4"
}
```

**Benefits:**
- Skip audio extraction for identical media
- Immediate language detection
- Audio quality assessment
- **Time Saved:** ~5-10 seconds per job

**Invalidation Rules:**
- Source file modified (mtime change)
- Source file size changed
- User explicitly requests fresh processing (`--no-cache`)

### Layer 2: Model Cache

**Purpose:** Avoid re-downloading model weights (1-5 GB per model)

**Storage Location:** `{cache_dir}/models/`

**Organization:**
```
models/
├── whisperx/
│   ├── large-v2/
│   │   ├── model.pt
│   │   └── config.json
│   └── large-v3/
│       ├── model.pt
│       └── config.json
├── indictrans2/
│   ├── hi-en/
│   │   ├── pytorch_model.bin
│   │   └── config.json
│   └── en-hi/
└── pyannote/
    └── speaker-diarization/
        └── model.pt
```

**Benefits:**
- Shared across all jobs
- Persists indefinitely (unless user clears)
- **Disk Saved:** 1-5 GB per model version

**Cleanup:** Manual only (user-initiated)

### Layer 3: ASR Results Cache

**Purpose:** Reuse ASR results for same audio with same configuration

**Storage Location:** `{cache_dir}/asr/`

**Cache Key:**
```python
cache_key = SHA256(
    audio_content +
    model_version +
    language +
    config_params  # beam_size, best_of, etc.
)
```

**Cached Data:**
```json
{
  "cache_key": "sha256_key_value",
  "audio_hash": "sha256_audio",
  "model": "whisperx-large-v3",
  "language": "hi",
  "config": {
    "beam_size": 5,
    "best_of": 5,
    "temperature": 0.0
  },
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Tum mere liye kya ho?",
      "words": [...],
      "confidence": 0.92
    }
  ],
  "language_probs": {"hi": 0.98, "en": 0.02},
  "created_at": "2025-12-03T10:35:00Z",
  "processing_time_seconds": 45.2
}
```

**Benefits:**
- **Target Hit Rate:** 70%
- **Time Saved:** 2-10 minutes per job (depending on audio length)
- Consistent results across re-runs

**Invalidation Rules:**
- Model version changed
- Configuration parameter affecting ASR changed
- Cache TTL exceeded (default: 90 days)
- User explicitly requests fresh processing

**Cache Lookup Logic:**
```python
def get_cached_asr(audio_file, config):
    audio_hash = compute_hash(audio_file)
    cache_key = compute_cache_key(audio_hash, config)
    
    cached_result = cache.get(cache_key)
    if cached_result:
        if cached_result['created_at'] < TTL:
            logger.info(f"ASR cache HIT: {cache_key[:8]}...")
            return cached_result
        else:
            logger.info(f"ASR cache EXPIRED: {cache_key[:8]}...")
            cache.delete(cache_key)
    
    logger.info(f"ASR cache MISS: {cache_key[:8]}...")
    return None
```

### Layer 4: Translation Memory Cache

**Purpose:** Reuse translations for similar content with context awareness

**Storage Location:** `{cache_dir}/translations/`

**Cache Key:**
```python
cache_key = SHA256(
    source_segment_hash +
    source_language +
    target_language +
    glossary_hash +
    context_hash  # surrounding segments for context
)
```

**Cached Data:**
```json
{
  "cache_key": "sha256_key_value",
  "source_segment": "Tum mere liye kya ho?",
  "source_lang": "hi",
  "target_lang": "en",
  "translated_segment": "What am I to you?",
  "model_used": "IndicTrans2",
  "glossary_terms_applied": ["tum", "kya"],
  "context": {
    "prev_segment": "...",
    "next_segment": "..."
  },
  "confidence": 0.95,
  "reuse_count": 12,
  "created_at": "2025-12-03T10:40:00Z",
  "last_used": "2025-12-03T11:20:00Z"
}
```

**Benefits:**
- **Target Hit Rate:** 60%
- **Time Saved:** 1-5 minutes per job
- Consistent terminology across similar content
- Context-aware matching

**Context-Aware Matching Levels:**
```python
def find_translation_match(segment, context, threshold=0.80):
    # Level 1: Exact segment + exact context (100% match)
    exact_match = cache.get_exact(segment, context)
    if exact_match:
        return exact_match, 1.0
    
    # Level 2: Exact segment + similar context (>80% match)
    similar_context_match = cache.get_similar_context(segment, context, 0.80)
    if similar_context_match:
        return similar_context_match, 0.90
    
    # Level 3: Similar segment + similar context (>80% match)
    similar_match = cache.get_similar(segment, context, threshold)
    if similar_match and similar_match['similarity'] > threshold:
        return similar_match, similar_match['similarity']
    
    # No match: Fresh translation needed
    return None, 0.0
```

**Invalidation Rules:**
- Glossary changed
- Translation model version changed
- Cache TTL exceeded (default: 90 days)
- User explicitly requests fresh processing

### Layer 5: Glossary Learning Cache

**Purpose:** Learn terms over time to improve accuracy on similar content

**Storage Location:** `{cache_dir}/glossary_learned/`

**Organization:**
```
glossary_learned/
├── {movie_id}/                          # Per-movie learned terms
│   ├── character_names.json
│   ├── cultural_terms.json
│   └── frequency_analysis.json
└── global/                              # Across all jobs
    ├── common_names.json
    ├── bollywood_terms.json
    └── technical_terms.json
```

**Per-Movie Glossary:**
```json
{
  "movie_id": "jaane_tu_ya_jaane_na",
  "learned_at": "2025-12-03T10:45:00Z",
  "character_names": {
    "Jai": {
      "frequency": 142,
      "speakers": ["male_01"],
      "contexts": ["casual", "romantic"],
      "translations": {
        "en": "Jai",
        "gu": "જય",
        "ta": "ஜய்"
      }
    },
    "Aditi": {
      "frequency": 98,
      "speakers": ["female_01"],
      "contexts": ["casual", "romantic"],
      "translations": {
        "en": "Aditi",
        "gu": "અદિતિ",
        "ta": "அதிதி"
      }
    }
  },
  "cultural_terms": {
    "beta": {
      "frequency": 34,
      "translation_context": "affectionate",
      "alternatives": ["dear", "son"],
      "preserve_in": ["hi", "gu"]
    },
    "bhai": {
      "frequency": 28,
      "translation_context": "brother",
      "formal": false,
      "alternatives": ["bro", "brother"]
    }
  }
}
```

**Global Glossary:**
```json
{
  "common_names": {
    "Raj": {"count": 1234, "language": "hi"},
    "Priya": {"count": 987, "language": "hi"},
    "Amit": {"count": 876, "language": "hi"}
  },
  "bollywood_terms": {
    "dil": {"meaning": "heart", "usage_count": 5678},
    "pyaar": {"meaning": "love", "usage_count": 4321},
    "rishta": {"meaning": "relationship", "usage_count": 2345}
  },
  "technical_terms": {
    "AI": {"expansion": "Artificial Intelligence", "count": 3456},
    "GPU": {"expansion": "Graphics Processing Unit", "count": 2345}
  }
}
```

**Benefits:**
- **Target Hit Rate:** 90% on same movie/series
- Automatic glossary population
- Improve accuracy on repeated content
- **Time Saved:** 5-10 minutes manual glossary creation

**Learning Process:**
```python
def learn_from_job(job_dir):
    # Extract character names from ASR + diarization
    characters = extract_character_names(
        asr_output, diarization_output, movie_metadata
    )
    
    # Extract cultural terms from transcript
    cultural_terms = extract_cultural_terms(
        transcript, language="hi"
    )
    
    # Update per-movie glossary
    movie_glossary = load_or_create_glossary(movie_id)
    movie_glossary.update(characters, cultural_terms)
    movie_glossary.save()
    
    # Update global glossary
    global_glossary.increment_counts(characters, cultural_terms)
    global_glossary.save()
```

### Cache Coordination

**Cross-Layer Dependencies:**
```
Audio Fingerprint → ASR Cache
    ↓
    ASR Cache → Translation Cache
    ↓
    Translation Cache → Glossary Learning
```

**Invalidation Cascade:**
```python
# If audio changes, invalidate all dependent caches
if audio_changed:
    invalidate_audio_fingerprint(audio_hash)
    invalidate_asr_cache(audio_hash)  # Cascade
    invalidate_translation_cache(audio_hash)  # Cascade
    # Glossary learning persists (historical data)
```

---

## ML Optimization

### Adaptive Quality Prediction

**Purpose:** Predict optimal processing parameters based on media characteristics.

**ML Model:** Lightweight XGBoost classifier (< 5 MB)

**Input Features:**
```python
features = {
    # Audio characteristics
    'duration_seconds': 180.5,
    'sample_rate': 16000,
    'snr_db': 25.3,
    'background_noise_level': 2.1,
    'speech_rate_wpm': 145,
    'clarity_score': 0.88,
    
    # Language characteristics
    'language': 'hi',
    'accent_detected': 'standard',
    'code_mixing': True,  # Hindi + English
    
    # Historical data
    'similar_jobs_processed': 12,
    'avg_confidence_similar': 0.89,
    'avg_processing_time_similar': 420
}
```

**Predictions:**
```python
predictions = {
    # Model selection
    'optimal_whisper_model': 'large-v2',  # vs large-v3
    'model_confidence': 0.92,
    
    # Processing decisions
    'source_separation_needed': False,  # Clean audio
    'enable_vad': True,
    'enable_diarization': True,
    
    # Quality predictions
    'expected_asr_wer': 0.12,
    'expected_confidence': 0.88,
    'expected_time_seconds': 380,
    
    # Resource allocation
    'recommended_batch_size': 16,
    'recommended_beam_size': 5
}
```

**Benefits:**
- **30% faster** on clean audio (use smaller model)
- **Better quality** on noisy audio (enable source separation)
- Accurate time estimates for user feedback

**Training Data Sources:**
- Historical job results (ASR confidence, WER, time)
- Audio characteristics (SNR, clarity, speech rate)
- User feedback (quality ratings)

### Context Learning from History

**Purpose:** Learn patterns from previous jobs to improve context awareness.

**Learning Mechanisms:**

**A. Character Name Recognition:**
```python
# Example: After processing "Jaane Tu Ya Jaane Na" once
learned_names = {
    "Jai": {
        "frequency": 142,
        "speakers": ["male_01"],
        "contexts": ["casual", "romantic"],
        "confidence": 0.95
    },
    "Aditi": {
        "frequency": 98,
        "speakers": ["female_01"],
        "contexts": ["casual", "romantic"],
        "confidence": 0.93
    },
    "Meow": {
        "frequency": 34,
        "speakers": ["female_02"],
        "contexts": ["nickname", "casual"],
        "confidence": 0.88
    }
}

# On next processing of same movie:
def enhance_asr_with_learned_names(asr_output, learned_names):
    for segment in asr_output['segments']:
        for word in segment['words']:
            # Pre-populate glossary
            if word['text'].lower() in learned_names:
                word['confidence'] *= 1.2  # Boost confidence
                word['proper_noun'] = True
                
            # Higher confidence in name detection
            if similar_to_learned_name(word['text'], learned_names):
                word['suggestion'] = get_closest_learned_name(word['text'])
                
            # Consistent speaker attribution
            if segment['speaker'] in learned_names[word['text']]['speakers']:
                word['confidence'] *= 1.1
```

**B. Cultural Term Patterns:**
```python
# Learn common Bollywood/Hindi patterns
cultural_patterns = {
    "beta": {
        "translation_context": "affectionate",
        "alternatives": ["dear", "son"],
        "formal": False,
        "preserve_in_langs": ["hi", "gu", "ta"],
        "usage_count": 234,
        "confidence": 0.91
    },
    "bhai": {
        "translation_context": "brother",
        "alternatives": ["bro", "brother"],
        "formal": False,
        "preserve_in_langs": ["hi"],
        "usage_count": 456,
        "confidence": 0.94
    },
    "ji": {
        "translation_context": "respectful_suffix",
        "preserve": True,
        "append_to": "names",
        "usage_count": 789,
        "confidence": 0.96
    }
}

# Apply patterns during translation
def apply_cultural_patterns(translation, patterns):
    for term, pattern in patterns.items():
        if term in translation['source']:
            if pattern['preserve']:
                # Don't translate, preserve original
                translation['target'] = translation['target'].replace(
                    translate(term), term
                )
            else:
                # Use learned context-aware alternative
                translation['target'] = translation['target'].replace(
                    translate(term), 
                    pattern['alternatives'][0]  # Use most common
                )
```

**C. Translation Memory:**
```python
# Build translation memory from approved translations
translation_memory = {
    "source_segment": "तुम मेरे लिए क्या हो?",
    "target_segment": "What am I to you?",
    "context": {
        "scene_type": "romantic_dialogue",
        "speaker_relationship": "casual_friends",
        "formality": "informal"
    },
    "confidence": 0.95,
    "reuse_count": 12,
    "user_approved": True,
    "created_at": "2025-11-15T14:30:00Z",
    "last_used": "2025-12-03T10:50:00Z"
}

# Reuse high-confidence translations
def get_translation_from_memory(segment, context):
    matches = translation_memory.search(
        segment, context, similarity_threshold=0.80
    )
    
    if matches:
        best_match = max(matches, key=lambda m: m['confidence'])
        if best_match['confidence'] > 0.90:
            logger.info(f"Translation memory HIT: {best_match['source_segment'][:30]}...")
            return best_match['target_segment']
    
    return None  # Fresh translation needed
```

### Similarity-Based Optimization

**Purpose:** Detect similar media and reuse processing decisions.

**Similarity Metrics:**
```python
def compute_similarity(audio1, audio2):
    # 1. Audio fingerprint matching (chromaprint)
    fingerprint_similarity = compare_fingerprints(audio1, audio2)
    
    # 2. Content-based similarity
    content_similarity = compare_content(audio1, audio2)
    # Same movie, different versions: 0.95
    # Same genre, different movie: 0.60
    # Different genre: 0.20
    
    # 3. Language/accent similarity
    language_similarity = compare_language(audio1, audio2)
    
    # 4. Genre similarity (if metadata available)
    genre_similarity = compare_genre(audio1, audio2)
    
    # Weighted average
    total_similarity = (
        fingerprint_similarity * 0.4 +
        content_similarity * 0.3 +
        language_similarity * 0.2 +
        genre_similarity * 0.1
    )
    
    return total_similarity
```

**Optimization Actions:**
```python
def optimize_based_on_similarity(current_job, similar_jobs):
    similarity_score = compute_similarity(current_job, similar_jobs)
    
    if similarity_score > 0.95:
        # Nearly identical media (same movie, same cut)
        logger.info("Very similar content detected (>95%)")
        reuse_full_pipeline_config(similar_jobs[0])
        apply_cached_glossary(similar_jobs[0])
        apply_cached_asr(similar_jobs[0])  # If within TTL
        apply_cached_translations(similar_jobs[0])
        
    elif similarity_score > 0.80:
        # Similar content (same movie, different quality/cut)
        logger.info("Similar content detected (>80%)")
        reuse_glossary(similar_jobs[0])
        reuse_model_selection(similar_jobs[0])
        reuse_config_params(similar_jobs[0])
        fresh_asr()  # Different audio quality, don't cache
        
    elif similarity_score > 0.60:
        # Similar genre/language
        logger.info("Similar genre detected (>60%)")
        reuse_language_settings(similar_jobs[0])
        suggest_related_glossaries(similar_jobs)
        reuse_processing_hints(similar_jobs[0])
    
    else:
        # Different content
        logger.info("No similar content found")
        use_default_settings()
```

---

## Configuration

### Cache Settings

**In `config/.env.pipeline`:**
```bash
# === CACHING CONFIGURATION ===

# Master switch
ENABLE_CACHING=true                          # Enable/disable all caching

# Cache location
CACHE_DIR=~/.cp-whisperx/cache              # Default cache directory
CACHE_MAX_SIZE_GB=50                        # Total cache size limit (GB)

# Cache layers
CACHE_AUDIO_FINGERPRINTS=true               # Layer 1: Audio fingerprints
CACHE_MODEL_WEIGHTS=true                    # Layer 2: Model weights
CACHE_ASR_RESULTS=true                      # Layer 3: ASR outputs
CACHE_TRANSLATIONS=true                     # Layer 4: Translation memory
CACHE_GLOSSARY_LEARNING=true                # Layer 5: Learned glossary

# Cache behavior
CACHE_TTL_DAYS=90                          # Cache expiration (days)
CACHE_CLEANUP_ON_START=false               # Auto-cleanup old cache
CACHE_VALIDATION_ON_LOAD=true              # Validate cache integrity

# Cache statistics
CACHE_TRACK_STATISTICS=true                 # Track hit/miss rates
CACHE_LOG_HITS=true                        # Log cache hits
```

### ML Optimization Settings

**In `config/.env.pipeline`:**
```bash
# === ML OPTIMIZATION CONFIGURATION ===

# Master switch
ENABLE_ML_OPTIMIZATION=true                 # Enable ML-based optimization

# Model selection
ML_MODEL_SELECTION=adaptive                 # adaptive|fixed
ML_QUALITY_PREDICTION=true                 # Predict optimal settings
ML_CONFIDENCE_THRESHOLD=0.80               # Min confidence for predictions

# Learning
ML_LEARNING_FROM_HISTORY=true              # Learn from past jobs
ML_TRAINING_DATA_RETENTION_DAYS=365        # Keep training data (days)
ML_MIN_SAMPLES_FOR_PREDICTION=10           # Min historical samples

# Similarity matching
SIMILAR_CONTENT_THRESHOLD=0.80             # Similarity reuse threshold
SIMILAR_CONTENT_MAX_MATCHES=5              # Max similar jobs to consider

# Performance tuning
ML_BATCH_PREDICTIONS=true                  # Batch predictions for speed
ML_FALLBACK_TO_DEFAULT=true               # Fallback if ML fails
```

### Glossary Learning Settings

**In `config/.env.pipeline`:**
```bash
# === GLOSSARY LEARNING CONFIGURATION ===

# Master switch
GLOSSARY_LEARNING_ENABLED=true             # Enable glossary learning

# Learning behavior
GLOSSARY_AUTO_EXTRACT_NAMES=true           # Extract character names
GLOSSARY_AUTO_EXTRACT_CULTURAL=true        # Extract cultural terms
GLOSSARY_MIN_FREQUENCY=3                   # Min occurrences to learn

# Global glossary
GLOSSARY_UPDATE_GLOBAL=true                # Update global glossary
GLOSSARY_GLOBAL_MIN_CONFIDENCE=0.85        # Min confidence for global

# Per-movie glossary
GLOSSARY_PER_MOVIE_ENABLED=true            # Per-movie glossaries
GLOSSARY_MOVIE_ID_FROM_TMDB=true           # Use TMDB ID if available
```

### Translation Memory Settings

**In `config/.env.pipeline`:**
```bash
# === TRANSLATION MEMORY CONFIGURATION ===

# Master switch
TRANSLATION_MEMORY_ENABLED=true            # Enable translation memory

# Matching behavior
TM_EXACT_MATCH_THRESHOLD=1.0              # Exact match (100%)
TM_FUZZY_MATCH_THRESHOLD=0.80             # Fuzzy match (80%)
TM_CONTEXT_WINDOW_SIZE=3                  # Surrounding segments

# Quality filters
TM_MIN_CONFIDENCE=0.85                    # Min confidence to cache
TM_MIN_REUSE_COUNT=2                      # Min reuses to keep
TM_MAX_AGE_DAYS=180                       # Max age (days)

# Performance
TM_MAX_CACHE_SIZE_GB=10                   # Max TM cache size
TM_CLEANUP_FREQUENCY_DAYS=30              # Cleanup frequency
```

---

## Cache Management

### Command-Line Tools

**View Cache Statistics:**
```bash
./tools/cache-manager.sh --stats

# Example output:
# ==========================================
# Cache Statistics Report
# ==========================================
# Generated: 2025-12-03 11:00:00
# 
# Overall:
#   Total Size: 12.5 GB / 50 GB (25%)
#   Total Files: 2,134
#   Oldest Entry: 45 days ago
#   
# By Layer:
#   Fingerprints: 1.2 GB (89 files)
#   Model Weights: 8.2 GB (6 files)
#   ASR Cache: 2.1 GB (1,234 files)
#   Translation Cache: 0.8 GB (567 files)
#   Glossary Learning: 0.2 GB (238 files)
#   
# Performance (Last 30 Days):
#   Total Jobs: 156
#   Cache Hits: 112 (72%)
#   Cache Misses: 44 (28%)
#   
# By Cache Type:
#   Fingerprint Hits: 89% (80/90 jobs)
#   ASR Hits: 68% (68/100 jobs)
#   Translation Hits: 55% (55/100 jobs)
#   Glossary Hits: 91% (82/90 jobs)
#   
# Time Saved: ~1,450 minutes (~24 hours)
# ==========================================
```

**Clear Specific Cache:**
```bash
# Clear ASR cache only
./tools/cache-manager.sh --clear asr

# Clear translations only
./tools/cache-manager.sh --clear translations

# Clear all except model weights
./tools/cache-manager.sh --clear all --keep-models
```

**Cleanup Old Cache:**
```bash
# Remove entries older than 90 days
./tools/cache-manager.sh --cleanup

# Remove entries older than 30 days
./tools/cache-manager.sh --cleanup --days 30

# Dry run (show what would be deleted)
./tools/cache-manager.sh --cleanup --dry-run
```

**Clear All Cache:**
```bash
# Clear everything (including model weights)
./tools/cache-manager.sh --clear all

# Clear with confirmation prompt
./tools/cache-manager.sh --clear all --confirm
```

**Export/Import Cache:**
```bash
# Export cache for sharing/backup
./tools/cache-manager.sh --export cache_backup.tar.gz

# Import cache from backup
./tools/cache-manager.sh --import cache_backup.tar.gz

# Export specific movie glossary
./tools/cache-manager.sh --export-glossary jaane_tu_ya_jaane_na glossary_jaane_tu.json
```

### Python API

**Basic Usage:**
```python
from shared.cache_manager import CacheManager

# Initialize cache manager
cache = CacheManager(cache_dir="~/.cp-whisperx/cache")

# Check if result cached
cached_result = cache.get_asr_result(audio_hash, config)
if cached_result:
    logger.info("ASR cache HIT")
    return cached_result

# Process and cache result
result = process_asr(audio, config)
cache.set_asr_result(audio_hash, config, result)
logger.info("ASR cache MISS - result cached")
```

**Advanced Usage:**
```python
from shared.cache_manager import CacheManager
from shared.ml_optimizer import MLOptimizer

# Initialize
cache = CacheManager()
optimizer = MLOptimizer()

# Predict optimal settings
predictions = optimizer.predict(audio_features)

# Check similarity with historical jobs
similar_jobs = cache.find_similar_jobs(audio_hash, threshold=0.80)
if similar_jobs:
    logger.info(f"Found {len(similar_jobs)} similar jobs")
    # Reuse settings from most similar
    best_match = similar_jobs[0]
    config.update(best_match['config'])

# Process with caching
result = process_with_cache(audio, config, cache)
```

---

## Performance Metrics

### Expected Improvements

| Metric | Baseline | With Caching | Improvement |
|--------|----------|--------------|-------------|
| Identical media processing | 10 min | 30 sec | **95% faster** |
| Same movie, different cut | 10 min | 6 min | **40% faster** |
| Similar Bollywood movie | 10 min | 8 min | **20% faster** |
| Similar language/genre | 10 min | 9 min | **10% faster** |
| Glossary accuracy (repeated) | 75% | 92% | **+17% accuracy** |
| Translation consistency | 80% | 95% | **+15% consistency** |

### Cache Hit Rates

**Target Rates:**
- Audio Fingerprint: 80% on re-processing
- ASR Results: 70% on same media
- Translation Memory: 60% on similar content
- Glossary Learning: 90% on same movie/series

**Actual Rates (Example after 3 months):**
```
Cache Hit Rate Report (90 days):
====================================
Total Jobs Processed: 450

Audio Fingerprint:
  Hits: 360 / 450 (80.0%) ✅ TARGET MET
  Time Saved: ~45 hours

ASR Results:
  Hits: 315 / 450 (70.0%) ✅ TARGET MET
  Time Saved: ~105 hours

Translation Memory:
  Hits: 270 / 450 (60.0%) ✅ TARGET MET
  Time Saved: ~45 hours

Glossary Learning:
  Hits: 405 / 450 (90.0%) ✅ TARGET MET
  Time Saved: ~75 hours

Total Time Saved: ~270 hours (11.25 days)
====================================
```

### Cost Savings

**Estimated Costs:**
```
Without Caching:
- GPU compute: $0.50 per 10 min audio
- Total jobs (450): $225

With Caching (72% hit rate):
- Cache hits (324): $0.05 per job (lookup only)
- Cache misses (126): $0.50 per job
- Total: $16.20 (hits) + $63 (misses) = $79.20

Savings: $145.80 (65% cost reduction)
```

---

## Implementation Details

### Cache Key Generation

**Audio Fingerprint Key:**
```python
def compute_audio_hash(audio_file: Path) -> str:
    """Compute SHA256 hash of audio content."""
    hasher = hashlib.sha256()
    with open(audio_file, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()
```

**ASR Cache Key:**
```python
def compute_asr_cache_key(
    audio_hash: str,
    model: str,
    language: str,
    config: Dict[str, Any]
) -> str:
    """Compute cache key for ASR results."""
    # Sort config for consistent hashing
    config_str = json.dumps(config, sort_keys=True)
    
    key_components = f"{audio_hash}|{model}|{language}|{config_str}"
    return hashlib.sha256(key_components.encode()).hexdigest()
```

**Translation Cache Key:**
```python
def compute_translation_cache_key(
    source_segment: str,
    source_lang: str,
    target_lang: str,
    glossary_hash: str,
    context: Dict[str, Any]
) -> str:
    """Compute cache key for translation."""
    # Include surrounding segments for context
    context_str = json.dumps(context, sort_keys=True)
    
    key_components = (
        f"{source_segment}|{source_lang}|{target_lang}|"
        f"{glossary_hash}|{context_str}"
    )
    return hashlib.sha256(key_components.encode()).hexdigest()
```

### Cache Storage Format

**Index Database (SQLite):**
```sql
CREATE TABLE cache_index (
    cache_key TEXT PRIMARY KEY,
    cache_type TEXT NOT NULL,  -- 'fingerprint', 'asr', 'translation', 'glossary'
    audio_hash TEXT,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    created_at TIMESTAMP,
    last_accessed TIMESTAMP,
    access_count INTEGER DEFAULT 1,
    ttl_days INTEGER DEFAULT 90,
    metadata JSON
);

CREATE INDEX idx_audio_hash ON cache_index(audio_hash);
CREATE INDEX idx_cache_type ON cache_index(cache_type);
CREATE INDEX idx_created_at ON cache_index(created_at);
```

**Cache File Structure:**
```
cache/
├── index.db                    # SQLite index
├── fingerprints/
│   └── {audio_hash}.json
├── asr/
│   └── {cache_key}.json
├── translations/
│   └── {cache_key}.json
└── glossary_learned/
    ├── {movie_id}/
    │   └── learned_glossary.json
    └── global/
        └── global_glossary.json
```

### Cache Validation

**Integrity Check:**
```python
def validate_cache_entry(cache_entry: Dict[str, Any]) -> bool:
    """Validate cache entry integrity."""
    # Check file exists
    if not Path(cache_entry['file_path']).exists():
        logger.warning(f"Cache file missing: {cache_entry['cache_key']}")
        return False
    
    # Check TTL
    age_days = (datetime.now() - cache_entry['created_at']).days
    if age_days > cache_entry['ttl_days']:
        logger.info(f"Cache entry expired: {cache_entry['cache_key']}")
        return False
    
    # Validate JSON structure
    try:
        with open(cache_entry['file_path']) as f:
            data = json.load(f)
        required_fields = get_required_fields(cache_entry['cache_type'])
        if not all(field in data for field in required_fields):
            logger.warning(f"Cache entry invalid: {cache_entry['cache_key']}")
            return False
    except Exception as e:
        logger.error(f"Cache validation error: {e}")
        return False
    
    return True
```

---

## Troubleshooting

### Issue: Cache Not Working

**Symptoms:**
- Cache hit rate = 0%
- Identical media re-processing takes full time

**Diagnosis:**
```bash
# Check if caching enabled
grep "ENABLE_CACHING" config/.env.pipeline
# Should output: ENABLE_CACHING=true

# Check cache directory exists and writable
ls -la ~/.cp-whisperx/cache
# Should show: drwxr-xr-x ... cache/

# Check cache statistics
./tools/cache-manager.sh --stats
# Should show cache info, not "Cache empty"

# Check logs for cache messages
grep "cache" out/LATEST/logs/99_pipeline_*.log
# Should show: "ASR cache MISS" or "ASR cache HIT"
```

**Solutions:**
```bash
# Enable caching
echo "ENABLE_CACHING=true" >> config/.env.pipeline

# Create cache directory
mkdir -p ~/.cp-whisperx/cache

# Fix permissions
chmod 755 ~/.cp-whisperx/cache

# Clear corrupted cache
./tools/cache-manager.sh --clear all
```

### Issue: Cache Hit But No Speed Improvement

**Symptoms:**
- Logs show "cache HIT"
- Processing still takes full time

**Diagnosis:**
```bash
# Check if stage actually uses cached result
grep "Using cached" out/LATEST/*/stage.log

# Verify cached file is valid
ls -lh ~/.cp-whisperx/cache/asr/{cache_key}.json

# Check stage processing time
grep "completed in" out/LATEST/*/stage.log
```

**Possible Causes:**
- Stage not using cached result (implementation bug)
- Cached file corrupted (validation failed)
- Cache lookup slow (large index)

**Solutions:**
```bash
# Rebuild cache index
./tools/cache-manager.sh --rebuild-index

# Validate cache integrity
./tools/cache-manager.sh --validate

# Enable debug logging
./prepare-job.sh --media in/audio.mp4 --workflow transcribe \
  --source-language en --log-level DEBUG
```

### Issue: Low Cache Hit Rate

**Symptoms:**
- Cache hit rate < 50% (expected 70%)
- Many cache MISS messages

**Diagnosis:**
```bash
# Check cache statistics by type
./tools/cache-manager.sh --stats --verbose

# Analyze cache miss reasons
grep "cache MISS" out/*/logs/99_pipeline_*.log | sort | uniq -c
```

**Common Reasons:**
1. **Configuration changes** - Different config params invalidate cache
2. **Model version changes** - New model version
3. **TTL expired** - Cache entries older than 90 days
4. **First-time content** - No similar content processed before

**Solutions:**
```bash
# Standardize configuration
# Use same config for similar jobs

# Increase TTL if needed
echo "CACHE_TTL_DAYS=180" >> config/.env.pipeline

# Pre-populate cache with common content
./tools/cache-warmup.sh --media-dir in/common/
```

### Issue: Cache Growing Too Large

**Symptoms:**
- Cache size > 50 GB (limit)
- Disk space warnings

**Diagnosis:**
```bash
# Check cache size
du -sh ~/.cp-whisperx/cache

# Check cache statistics
./tools/cache-manager.sh --stats

# List largest cache entries
./tools/cache-manager.sh --list-largest --top 20
```

**Solutions:**
```bash
# Cleanup old entries (>90 days)
./tools/cache-manager.sh --cleanup

# Reduce TTL
echo "CACHE_TTL_DAYS=60" >> config/.env.pipeline

# Reduce max size
echo "CACHE_MAX_SIZE_GB=30" >> config/.env.pipeline

# Remove least-used entries
./tools/cache-manager.sh --cleanup --by-usage --keep-top 100
```

### Issue: Glossary Learning Not Working

**Symptoms:**
- Glossary hit rate < 90%
- Character names not learned

**Diagnosis:**
```bash
# Check if glossary learning enabled
grep "GLOSSARY_LEARNING_ENABLED" config/.env.pipeline

# Check learned glossary
cat ~/.cp-whisperx/cache/glossary_learned/{movie_id}/learned_glossary.json

# Check learning logs
grep "glossary" out/LATEST/03_glossary_load/stage.log
```

**Solutions:**
```bash
# Enable glossary learning
echo "GLOSSARY_LEARNING_ENABLED=true" >> config/.env.pipeline

# Lower frequency threshold
echo "GLOSSARY_MIN_FREQUENCY=2" >> config/.env.pipeline

# Manually add to glossary
./tools/add-to-glossary.sh --term "Jai" --type "character_name" \
  --movie "jaane_tu_ya_jaane_na"
```

---

## See Also

- [Architecture Implementation Roadmap](../ARCHITECTURE_IMPLEMENTATION_ROADMAP.md) - Overall system design
- [Workflows Guide](../user-guide/workflows.md) - Using workflows with caching
- [Configuration Guide](../user-guide/configuration.md) - Cache configuration
- [Developer Standards](../developer/DEVELOPER_STANDARDS.md) - Implementation standards

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-03  
**Status:** ✅ Active - Target Architecture v3.0
