# Technical Requirement Document (TRD): ML-Based Quality Prediction

**ID:** TRD-2025-12-09-06  
**Created:** 2025-12-09  
**Status:** ✅ Implemented  
**Related BRD:** [BRD-2025-12-09-06-ml-quality-prediction.md](../brd/BRD-2025-12-09-06-ml-quality-prediction.md)  
**Related PRD:** [PRD-2025-12-09-06-ml-quality-prediction.md](../prd/PRD-2025-12-09-06-ml-quality-prediction.md)

---

## Technical Overview

Implement ML-based automatic parameter optimization using audio fingerprinting and XGBoost classification to predict optimal Whisper model configuration.

---

## Architecture

### System Design

```
┌──────────────────────────────────────────────────────────┐
│                     ASR Stage (06)                       │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │  Load Configuration           │
       │  - ML_OPTIMIZATION_ENABLED    │
       │  - FORCE_MODEL_SIZE           │
       │  - ML_CONFIDENCE_THRESHOLD    │
       └───────────┬───────────────────┘
                   │
        ┌──────────▼──────────┐
        │  Optimization        │
        │  Enabled?            │
        └──┬───────────────┬──┘
    YES    │               │    NO
           ▼               ▼
    ┌──────────────┐  ┌────────────┐
    │  Extract     │  │  Use       │
    │  Audio       │  │  Defaults  │
    │  Fingerprint │  └────────────┘
    └──────┬───────┘
           │
           ▼
    ┌──────────────────────┐
    │  ML Predictor        │
    │  (AdaptiveQuality    │
    │   Predictor)         │
    │                      │
    │  XGBoost Model       │
    │  + Rule-Based        │
    │    Fallback          │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │  Confidence Check    │
    │  ≥ Threshold?        │
    └──┬──────────────┬────┘
  YES  │              │  NO
       ▼              ▼
┌─────────────┐  ┌────────────┐
│  Apply ML   │  │  Use       │
│  Prediction │  │  Defaults  │
└─────┬───────┘  └────────────┘
      │
      ▼
┌───────────────────┐
│  Log Prediction   │
│  + Reasoning      │
└───────┬───────────┘
        │
        ▼
┌───────────────────────────┐
│  Execute ASR with         │
│  Predicted Parameters     │
└───────────────────────────┘
```

---

## Implementation Requirements

### New Files

**File 1: `shared/ml_optimizer.py`** (650 lines)

```python
from typing import Dict, Optional, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass

@dataclass
class AudioFingerprint:
    """Audio characteristics for ML prediction."""
    duration_seconds: float
    snr_db: float
    speaker_count: int
    complexity: str  # "low", "medium", "high"
    language_hint: Optional[str] = None
    silence_ratio: float = 0.0
    
    def to_features(self) -> np.ndarray:
        """Convert to ML features vector."""
        complexity_map = {"low": 0, "medium": 1, "high": 2}
        return np.array([
            self.duration_seconds / 3600,  # Normalize
            self.snr_db / 50.0,
            float(self.speaker_count),
            float(complexity_map[self.complexity]),
            self.silence_ratio
        ])

class AdaptiveQualityPredictor:
    """ML-based predictor for optimal ASR parameters."""
    
    def __init__(self, model_path: Optional[Path] = None, logger=None):
        self.model_path = model_path
        self.logger = logger or get_logger(__name__)
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load XGBoost model or fall back to rules."""
        try:
            import xgboost as xgb
            if self.model_path and self.model_path.exists():
                self.model = xgb.Booster()
                self.model.load_model(str(self.model_path))
                self.logger.info("✅ ML model loaded")
            else:
                self.logger.info("⏭️  No ML model, using rule-based")
        except ImportError:
            self.logger.warning("XGBoost not installed, using rules")
    
    def predict(
        self, 
        fingerprint: AudioFingerprint,
        confidence_threshold: float = 0.75
    ) -> Tuple[Dict[str, any], float, str]:
        """
        Predict optimal parameters.
        
        Returns:
            (params, confidence, reasoning)
        """
        if self.model:
            return self._predict_ml(fingerprint, confidence_threshold)
        else:
            return self._predict_rules(fingerprint)
    
    def _predict_ml(
        self, 
        fingerprint: AudioFingerprint,
        threshold: float
    ) -> Tuple[Dict[str, any], float, str]:
        """ML-based prediction."""
        import xgboost as xgb
        
        features = fingerprint.to_features().reshape(1, -1)
        dmatrix = xgb.DMatrix(features)
        
        # Predict probabilities
        probs = self.model.predict(dmatrix)[0]
        confidence = float(np.max(probs))
        
        if confidence < threshold:
            # Low confidence - fall back to rules
            return self._predict_rules(fingerprint)
        
        # Map prediction to model size
        model_sizes = ["tiny", "base", "small", "medium", "large-v3"]
        predicted_idx = int(np.argmax(probs))
        model_size = model_sizes[predicted_idx]
        
        # Predict beam size based on confidence
        beam_size = 5 if confidence > 0.9 else 3
        
        # Predict batch size based on model
        batch_size = {
            "tiny": 32,
            "base": 24,
            "small": 16,
            "medium": 16,
            "large-v3": 8
        }[model_size]
        
        params = {
            "model_size": model_size,
            "beam_size": beam_size,
            "batch_size": batch_size
        }
        
        reasoning = f"ML prediction (confidence: {confidence:.0%})"
        return params, confidence, reasoning
    
    def _predict_rules(
        self, 
        fingerprint: AudioFingerprint
    ) -> Tuple[Dict[str, any], float, str]:
        """Rule-based fallback prediction."""
        
        # Rule 1: Duration-based
        if fingerprint.duration_seconds < 600:  # <10 min
            if fingerprint.snr_db > 25:  # Clean
                model = "small"
                reasoning = "Short + clean audio"
            elif fingerprint.snr_db > 15:  # Moderate
                model = "medium"
                reasoning = "Short + moderate noise"
            else:  # Noisy
                model = "large-v3"
                reasoning = "Short + noisy"
        else:  # Long audio
            if fingerprint.snr_db > 25:  # Clean
                model = "small"
                reasoning = "Long + clean (small sufficient)"
            else:  # Not clean
                model = "medium"
                reasoning = "Long + noisy (balance speed/quality)"
        
        # Rule 2: Complexity override
        if fingerprint.complexity == "high":
            if model in ["tiny", "base"]:
                model = "medium"
                reasoning += " → medium (high complexity)"
        
        # Rule 3: Speaker count
        if fingerprint.speaker_count > 4:
            if model == "small":
                model = "medium"
                reasoning += " → medium (many speakers)"
        
        beam_size = 5 if model in ["large-v3", "medium"] else 3
        batch_size = {"small": 16, "medium": 16, "large-v3": 8}.get(model, 16)
        
        params = {
            "model_size": model,
            "beam_size": beam_size,
            "batch_size": batch_size
        }
        
        confidence = 0.8  # Rules are fairly confident
        return params, confidence, reasoning

def extract_audio_fingerprint(
    audio_path: Path,
    logger=None
) -> AudioFingerprint:
    """Extract audio characteristics."""
    import librosa
    import soundfile as sf
    
    logger = logger or get_logger(__name__)
    
    try:
        # Load audio
        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration = len(y) / sr
        
        # Compute SNR
        signal_power = np.mean(y ** 2)
        noise_estimate = np.median(np.abs(y)) ** 2
        snr_db = 10 * np.log10(signal_power / noise_estimate) if noise_estimate > 0 else 30.0
        
        # Estimate speaker count (simplified)
        rms = librosa.feature.rms(y=y)[0]
        segments = len([r for r in rms if r > 0.02])
        speaker_count = min(int(segments / 100) + 1, 5)
        
        # Compute complexity
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        complexity_score = np.std(spectral_centroid) / np.mean(spectral_centroid)
        if complexity_score < 0.3:
            complexity = "low"
        elif complexity_score < 0.6:
            complexity = "medium"
        else:
            complexity = "high"
        
        # Compute silence ratio
        silence_threshold = 0.01
        silence_ratio = np.sum(np.abs(y) < silence_threshold) / len(y)
        
        return AudioFingerprint(
            duration_seconds=duration,
            snr_db=snr_db,
            speaker_count=speaker_count,
            complexity=complexity,
            silence_ratio=silence_ratio
        )
    
    except Exception as e:
        logger.error(f"Audio fingerprint extraction failed: {e}", exc_info=True)
        # Return safe defaults
        return AudioFingerprint(
            duration_seconds=300,
            snr_db=20.0,
            speaker_count=2,
            complexity="medium",
            silence_ratio=0.1
        )
```

---

### Modified Files

**File: `scripts/06_whisperx_asr.py`** (105 new lines)

```python
from shared.ml_optimizer import (
    AdaptiveQualityPredictor, 
    extract_audio_fingerprint
)

def run_stage(job_dir: Path, stage_name: str = "06_whisperx_asr") -> int:
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    config = load_config()
    
    # Check if ML optimization enabled
    ml_enabled = config.get("ML_OPTIMIZATION_ENABLED", "true").lower() == "true"
    force_model = config.get("FORCE_MODEL_SIZE")
    
    # Get audio file
    audio_file = io.job_dir / "04_source_separation" / "vocals.wav"
    if not audio_file.exists():
        audio_file = io.job_dir / "01_demux" / "audio.wav"
    
    # Determine model parameters
    if force_model:
        # Manual override
        model_size = force_model
        beam_size = int(config.get("FORCE_BEAM_SIZE", 5))
        logger.info(f"⚙️  Manual override: model={model_size}")
    
    elif ml_enabled:
        # ML-based optimization
        logger.info("🔍 Analyzing audio for ML optimization...")
        
        # Extract fingerprint
        fingerprint = extract_audio_fingerprint(audio_file, logger)
        logger.info(f"   Duration: {fingerprint.duration_seconds/60:.1f} min")
        logger.info(f"   SNR: {fingerprint.snr_db:.1f} dB")
        logger.info(f"   Speakers: {fingerprint.speaker_count}")
        logger.info(f"   Complexity: {fingerprint.complexity}")
        
        # Get prediction
        predictor = AdaptiveQualityPredictor(logger=logger)
        threshold = float(config.get("ML_CONFIDENCE_THRESHOLD", 0.75))
        params, confidence, reasoning = predictor.predict(fingerprint, threshold)
        
        model_size = params["model_size"]
        beam_size = params["beam_size"]
        batch_size = params["batch_size"]
        
        logger.info(f"🤖 ML Prediction (confidence: {confidence:.0%}):")
        logger.info(f"   Model: {model_size}")
        logger.info(f"   Beam size: {beam_size}")
        logger.info(f"   Batch size: {batch_size}")
        logger.info(f"   Reasoning: {reasoning}")
    
    else:
        # Use defaults from config
        model_size = config.get("WHISPERX_MODEL", "medium")
        beam_size = int(config.get("WHISPERX_BEAM_SIZE", 5))
        logger.info(f"⏭️  ML disabled, using defaults: {model_size}")
    
    # Continue with ASR using determined parameters...
    # (existing ASR code)
```

---

### Configuration Changes

**File: `config/.env.pipeline`** (7 new parameters)

```bash
# ML Optimization
ML_OPTIMIZATION_ENABLED=true              # Enable/disable ML predictions
ML_CONFIDENCE_THRESHOLD=0.75              # Minimum confidence to apply (0.0-1.0)
ML_MODEL_PATH=models/quality_predictor.xgb  # Path to trained model

# Manual Overrides
FORCE_MODEL_SIZE=                         # Override ML: tiny/base/small/medium/large-v3
FORCE_BEAM_SIZE=                          # Override ML beam size
FORCE_BATCH_SIZE=                         # Override ML batch size
```

---

## Testing Requirements

### Unit Tests

**File: `tests/unit/test_ml_optimizer.py`** (250 lines)

```python
import pytest
from shared.ml_optimizer import (
    AudioFingerprint,
    AdaptiveQualityPredictor,
    extract_audio_fingerprint
)

class TestAudioFingerprint:
    def test_to_features(self):
        """Test feature vector conversion."""
        fp = AudioFingerprint(
            duration_seconds=600,
            snr_db=25.0,
            speaker_count=2,
            complexity="low",
            silence_ratio=0.1
        )
        features = fp.to_features()
        assert len(features) == 5
        assert features[0] == 600 / 3600  # Normalized duration

class TestAdaptiveQualityPredictor:
    def test_predict_clean_audio(self):
        """Clean audio → small model."""
        predictor = AdaptiveQualityPredictor()
        fp = AudioFingerprint(
            duration_seconds=300,
            snr_db=30.0,
            speaker_count=1,
            complexity="low"
        )
        params, confidence, reasoning = predictor.predict(fp)
        assert params["model_size"] == "small"
        assert confidence >= 0.7
    
    def test_predict_noisy_audio(self):
        """Noisy audio → large model."""
        predictor = AdaptiveQualityPredictor()
        fp = AudioFingerprint(
            duration_seconds=600,
            snr_db=10.0,
            speaker_count=3,
            complexity="high"
        )
        params, confidence, reasoning = predictor.predict(fp)
        assert params["model_size"] in ["medium", "large-v3"]
```

### Integration Tests

**File: `tests/integration/test_ml_integration.py`** (150 lines)

```python
def test_ml_optimization_enabled():
    """Test ML optimization in full pipeline."""
    config = {
        "ML_OPTIMIZATION_ENABLED": "true",
        "FORCE_MODEL_SIZE": None
    }
    result = run_asr_stage(test_audio, config)
    assert "ml_prediction" in result
    assert result["model_size"] in ["tiny", "base", "small", "medium", "large-v3"]

def test_force_model_override():
    """Test manual override."""
    config = {
        "ML_OPTIMIZATION_ENABLED": "true",
        "FORCE_MODEL_SIZE": "large-v3"
    }
    result = run_asr_stage(test_audio, config)
    assert result["model_size"] == "large-v3"
    assert result["override"] == True
```

---

## Performance Considerations

**Expected Performance:**
- Audio fingerprint extraction: 2-4 seconds (acceptable overhead)
- ML prediction: <1 second (fast XGBoost inference)
- Total overhead: 3-5 seconds per job
- Processing speedup: 20-40% for 60% of jobs
- Net benefit: 15-30% average speedup

**Optimization:**
- Cache fingerprints (reuse for same media)
- Lazy load XGBoost model (once per process)
- Vectorized numpy operations (fast feature extraction)

---

## Related Documents

- **BRD:** [BRD-2025-12-09-06-ml-quality-prediction.md](../brd/BRD-2025-12-09-06-ml-quality-prediction.md)
- **PRD:** [PRD-2025-12-09-06-ml-quality-prediction.md](../prd/PRD-2025-12-09-06-ml-quality-prediction.md)
- **Implementation:** TASK16_COMPLETE.md
- **Documentation:** docs/ML_OPTIMIZATION.md

---

**Version:** 1.0  
**Status:** ✅ Implemented (2025-12-09)  
**Effort:** 16 hours estimated, 6 hours actual (67% under budget)
