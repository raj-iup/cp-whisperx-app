# Task #16: Adaptive Quality Prediction - Implementation Plan

**Duration:** 3 days  
**Priority:** HIGH  
**Status:** 🚀 Starting  
**Date:** 2025-12-09

## Objective
Implement ML-based prediction of optimal Whisper model parameters based on audio characteristics.

## Components to Build

### 1. Core ML Optimizer (Day 1)
**File:** `shared/ml_optimizer.py`

**Classes:**
- `AdaptiveQualityPredictor` - Main predictor class
- `AudioFingerprint` - Audio characteristic extraction
- `ModelTrainer` - Train XGBoost model on historical data

**Features:**
- Extract features: duration, SNR, language, speaker count
- Predict: model size, batch size, beam size
- Learn from results: continuous improvement

### 2. Historical Data Extraction (Day 1)
**Script:** `tools/extract-ml-training-data.py`

**Extract from manifests:**
- Audio duration (from stage 01)
- Processing time (from stage 06)
- Model used (from job config)
- Quality metrics (from stage 07)
- Extract from 100+ past jobs

### 3. Integration (Day 2)
**Update:** `scripts/06_whisperx_asr.py`

**Changes:**
- Call ML optimizer before ASR
- Use predicted config
- Add override flag (FORCE_MODEL_SIZE)
- Log predictions vs. actual

### 4. Testing (Day 3)
**Files:**
- `tests/unit/test_ml_optimizer.py`
- `tests/integration/test_ml_prediction.py`

**Test scenarios:**
- Clean audio → predicts smaller model
- Noisy audio → predicts larger model
- Unknown audio → falls back to default

### 5. Documentation (Day 3)
**File:** `docs/ML_OPTIMIZATION.md`

**Sections:**
- How it works
- Training data requirements
- Configuration options
- Override mechanisms

## Success Criteria
- [ ] ML optimizer predicts correct model 85% of time
- [ ] 30% faster on clean audio (small model)
- [ ] 15% better accuracy on noisy audio (large model)
- [ ] Graceful fallback when no training data
- [ ] Full test coverage (>80%)

## Implementation Steps

### Day 1: Core Implementation (6-8 hours)
1. ✅ Create implementation plan (this file)
2. ⏳ Create `shared/ml_optimizer.py` skeleton
3. ⏳ Implement `AudioFingerprint` class
4. ⏳ Implement `AdaptiveQualityPredictor` class
5. ⏳ Create `tools/extract-ml-training-data.py`
6. ⏳ Extract historical data from manifests
7. ⏳ Train initial model

### Day 2: Integration (6-8 hours)
8. ⏳ Update `scripts/06_whisperx_asr.py`
9. ⏳ Add configuration parameters
10. ⏳ Test with sample media
11. ⏳ Validate predictions
12. ⏳ Document integration

### Day 3: Testing & Documentation (4-6 hours)
13. ⏳ Create unit tests
14. ⏳ Create integration tests
15. ⏳ Write ML_OPTIMIZATION.md
16. ⏳ Update IMPLEMENTATION_TRACKER.md
17. ⏳ Update copilot-instructions.md

## Configuration
```bash
# config/.env.pipeline

# ML Optimization
ML_OPTIMIZATION_ENABLED=true
ML_MODEL_PATH=~/.cp-whisperx/models/ml_optimizer.pkl
ML_TRAINING_THRESHOLD=100  # Min jobs for training
ML_CONFIDENCE_THRESHOLD=0.7  # Use prediction if confidence > 0.7

# Model Selection Override
FORCE_MODEL_SIZE=  # Empty = use ML prediction, or force: tiny/base/small/medium/large-v3
```

## Dependencies
- xgboost==2.0.3 (new)
- scikit-learn==1.4.0 (new)
- numpy==1.26.0 (existing)
- joblib==1.3.2 (for model persistence)

## Risk Mitigation
- **Insufficient training data:** Start with rule-based heuristics, improve over time
- **Poor predictions:** Add confidence threshold, fall back to defaults
- **Model drift:** Retrain monthly with new data
- **Overhead:** Cache predictions, minimal overhead (<1s)

## Next Actions
1. Review plan with user
2. Start Day 1 implementation
3. Extract historical data first
4. Build core ML optimizer

---
**Status:** Ready to start  
**Estimated completion:** 2025-12-11
