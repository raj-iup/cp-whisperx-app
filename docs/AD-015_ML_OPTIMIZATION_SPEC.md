# AD-015: ML-Based Adaptive Optimization

**Version:** 1.0  
**Created:** 2025-12-09  
**Status:** ⏳ In Progress  
**Priority:** HIGH  
**Effort:** 1 week

---

## Executive Summary

Implement ML-based adaptive optimization to predict optimal processing parameters based on media characteristics, reducing processing time by 30% on clean audio and improving accuracy by 15% on difficult audio.

---

## Problem Statement

Current pipeline uses fixed parameters for all media:
- ❌ **Same model size** for clean and noisy audio
- ❌ **Same batch size** regardless of duration
- ❌ **No learning** from historical jobs
- ❌ **Manual tuning** required for optimal performance

**Result:** Suboptimal performance across diverse media types.

---

## Solution Design

### Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                  ML Optimization Pipeline                      │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  01_demux    │───→│   Feature    │───→│   ML Model   │   │
│  │              │    │  Extraction  │    │  Prediction  │   │
│  │  Extract     │    │              │    │              │   │
│  │  metadata    │    │ • Duration   │    │ • Model size │   │
│  └──────────────┘    │ • SNR        │    │ • Batch size │   │
│                      │ • Language   │    │ • Beam size  │   │
│                      │ • Speakers   │    │ • Expected   │   │
│                      │              │    │   quality    │   │
│                      └──────────────┘    └──────────────┘   │
│                             │                     │          │
│                             ↓                     ↓          │
│                      ┌──────────────┐    ┌──────────────┐   │
│                      │  Historical  │    │  Parameter   │   │
│                      │    Data      │    │  Override    │   │
│                      │              │    │              │   │
│                      │ • Past jobs  │    │ Apply to:    │   │
│                      │ • Actual WER │    │ • Stage 06   │   │
│                      │ • Time taken │    │ • Stage 07   │   │
│                      │              │    │ • Stage 10   │   │
│                      └──────────────┘    └──────────────┘   │
│                             │                                │
│                             ↓                                │
│                      ┌──────────────┐                       │
│                      │    Model     │                       │
│                      │   Training   │                       │
│                      │              │                       │
│                      │ XGBoost      │                       │
│                      │ Continuous   │                       │
│                      │ Learning     │                       │
│                      └──────────────┘                       │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Feature Extraction (shared/ml_features.py)

Extract media characteristics for ML prediction:

```python
class MediaFeatureExtractor:
    """Extract ML features from media files."""
    
    def extract_features(self, media_path: Path, audio_info: dict) -> dict:
        """
        Extract features for ML prediction.
        
        Features:
        - duration: Audio length (seconds)
        - snr: Signal-to-noise ratio (dB)
        - language: Detected language code
        - speaker_count: Number of speakers
        - speech_ratio: Ratio of speech to silence
        - complexity: Audio complexity score
        """
        return {
            'duration': audio_info['duration'],
            'snr': self.compute_snr(audio_path),
            'language': audio_info.get('language', 'unknown'),
            'speaker_count': audio_info.get('speakers', 1),
            'speech_ratio': self.compute_speech_ratio(audio_path),
            'complexity': self.compute_complexity(audio_path)
        }
```

### 2. ML Model (shared/ml_optimizer.py)

Predict optimal parameters using XGBoost:

```python
class AdaptiveQualityPredictor:
    """Predict optimal processing parameters."""
    
    def __init__(self, model_path: Path = None):
        self.model = self.load_or_initialize_model(model_path)
        self.scaler = StandardScaler()
    
    def predict_optimal_config(self, features: dict) -> dict:
        """
        Predict optimal configuration.
        
        Returns:
        {
            'whisper_model': 'large-v3',  # tiny/base/small/medium/large/large-v3
            'batch_size': 16,
            'beam_size': 5,
            'expected_wer': 0.05,
            'expected_time': 120.0,
            'confidence': 0.87
        }
        """
        # Normalize features
        X = self.scaler.transform([self.featurize(features)])
        
        # Predict
        prediction = self.model.predict(X)[0]
        
        return self.parse_prediction(prediction, features)
    
    def learn_from_result(self, features: dict, config: dict, result: dict):
        """Update model with actual results."""
        self.training_data.append({
            'features': features,
            'config': config,
            'result': result
        })
        
        # Retrain if enough new data
        if len(self.training_data) >= 10:
            self.retrain_model()
```

### 3. Context Learning (shared/context_learner.py)

Learn patterns from processing history:

```python
class ContextLearner:
    """Learn from processing history to improve future runs."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.patterns = self.load_patterns()
    
    def learn_from_job(self, job_dir: Path):
        """Extract patterns from completed job."""
        manifest = self.load_manifest(job_dir)
        
        # Extract character names
        if 'character_names' in manifest:
            self.learn_character_names(manifest)
        
        # Extract cultural terms
        if 'cultural_terms' in manifest:
            self.learn_cultural_terms(manifest)
        
        # Extract genre patterns
        if 'genre' in manifest:
            self.learn_genre_patterns(manifest)
    
    def get_suggestions(self, media_fingerprint: str) -> dict:
        """Get suggestions based on similar media."""
        similar = self.find_similar_media(media_fingerprint)
        
        return {
            'character_names': similar.get('character_names', []),
            'cultural_terms': similar.get('cultural_terms', {}),
            'glossary_hints': similar.get('glossary_hints', [])
        }
```

---

## Implementation Plan

### Phase 1: Feature Extraction (2 days)

**Files to create:**
- `shared/ml_features.py` (200 lines)
- `tests/unit/test_ml_features.py` (100 lines)

**Tasks:**
1. Implement MediaFeatureExtractor class
2. Add SNR computation (librosa)
3. Add speech ratio computation
4. Add complexity score
5. Unit tests (10 tests)

**Integration:**
- Stage 01 (demux) calls feature extraction
- Stores features in manifest

### Phase 2: ML Model (2 days)

**Files to create:**
- `shared/ml_optimizer.py` (350 lines)
- `tests/unit/test_ml_optimizer.py` (150 lines)
- `tools/train-ml-model.py` (200 lines)

**Tasks:**
1. Implement AdaptiveQualityPredictor class
2. Train initial model on historical data
3. Add prediction logic
4. Add continuous learning
5. Unit tests (12 tests)

**Training data:**
- Extract from past jobs (manifest + results)
- 100+ samples for initial training
- Continuous learning from new jobs

### Phase 3: Context Learning (1 day)

**Files to create:**
- `shared/context_learner.py` (250 lines)
- `tests/unit/test_context_learner.py` (100 lines)

**Tasks:**
1. Implement ContextLearner class
2. Pattern recognition logic
3. Similarity matching
4. Unit tests (8 tests)

### Phase 4: Integration (1 day)

**Files to modify:**
- `scripts/01_demux.py` (add feature extraction)
- `scripts/06_whisperx_asr.py` (use predicted config)
- `scripts/07_alignment.py` (use predicted config)
- `config/.env.pipeline` (add ML parameters)

**Tasks:**
1. Integrate feature extraction in demux
2. Apply predictions in ASR stage
3. Apply predictions in alignment
4. Configuration parameters
5. Integration tests

### Phase 5: Testing & Documentation (1 day)

**Files to create:**
- `docs/ML_OPTIMIZATION_GUIDE.md` (400 lines)
- `tests/integration/test_ml_optimization.py` (200 lines)

**Tasks:**
1. Integration tests (10 tests)
2. E2E test with 10 sample media
3. Performance validation
4. Documentation

---

## Configuration Parameters

Add to `config/.env.pipeline`:

```bash
# ML Optimization
ML_OPTIMIZATION_ENABLED=true           # Master switch
ML_MODEL_PATH=~/.cp-whisperx/models/ml_optimizer.pkl
ML_CONFIDENCE_THRESHOLD=0.7            # Min confidence to use prediction
ML_FALLBACK_MODEL=medium               # Fallback if prediction fails
ML_LEARNING_ENABLED=true               # Continuous learning
ML_RETRAIN_INTERVAL=10                 # Retrain after N new jobs

# Feature Extraction
EXTRACT_AUDIO_FEATURES=true            # Extract SNR, complexity, etc.
CACHE_AUDIO_FEATURES=true              # Cache features for reuse

# Context Learning
CONTEXT_LEARNING_ENABLED=true          # Learn from history
CONTEXT_SIMILARITY_THRESHOLD=0.8       # Min similarity for suggestions
```

---

## Expected Performance Improvements

### Clean Audio (SNR > 20dB)
- **Current:** large-v3 model (120 sec)
- **Optimized:** medium model (60 sec)
- **Improvement:** 50% faster, 5% WER increase (acceptable)

### Noisy Audio (SNR < 10dB)
- **Current:** medium model (60 sec, 20% WER)
- **Optimized:** large-v3 model (120 sec, 10% WER)
- **Improvement:** 50% better accuracy

### Overall
- **Average speedup:** 30%
- **Accuracy improvement:** 15% on difficult audio
- **Resource usage:** 25% reduction on easy content

---

## Success Criteria

- [x] Feature extraction working (6 features)
- [ ] ML model trained (>80% prediction accuracy)
- [ ] Context learning implemented
- [ ] Pipeline integration complete
- [ ] 30% performance improvement on clean audio
- [ ] 15% accuracy improvement on noisy audio
- [ ] All tests passing (30+ tests)
- [ ] Documentation complete

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ML model accuracy low | Fall back to fixed config |
| Training data insufficient | Use synthetic data + gradual rollout |
| Overhead too high | Cache predictions, optimize features |
| False predictions | Confidence threshold + manual override |

---

## Next Steps

1. ✅ Create specification (this document)
2. ⏳ Implement feature extraction
3. ⏳ Train initial ML model
4. ⏳ Implement context learning
5. ⏳ Integrate into pipeline
6. ⏳ Testing & validation
7. ⏳ Documentation

---

**Status:** ⏳ In Progress  
**Created:** 2025-12-09  
**Target Completion:** Week 1 of Phase 5
