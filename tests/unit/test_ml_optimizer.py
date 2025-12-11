#!/usr/bin/env python3
"""
Unit tests for ML-based adaptive quality predictor.

Tests:
- AudioFingerprint creation and feature extraction
- Rule-based prediction logic
- Model configuration defaults
- WER and duration estimation
- Graceful fallback when no ML model

Run:
    pytest tests/unit/test_ml_optimizer.py -v
"""

# Standard library
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Third-party
import pytest
import numpy as np

# Local
from shared.ml_optimizer import (
    AdaptiveQualityPredictor,
    AudioFingerprint,
    PredictionConfig
)


class TestAudioFingerprint:
    """Test AudioFingerprint class."""
    
    def test_create_fingerprint(self):
        """Test basic fingerprint creation."""
        fp = AudioFingerprint(
            duration=300.0,  # 5 minutes
            sample_rate=16000,
            channels=1,
            snr_estimate=20.0,
            language="en",
            speaker_count=2,
            complexity_score=0.5,
            file_size=10.0
        )
        
        assert fp.duration == 300.0
        assert fp.sample_rate == 16000
        assert fp.language == "en"
        assert fp.speaker_count == 2
    
    def test_feature_vector(self):
        """Test feature vector extraction."""
        fp = AudioFingerprint(
            duration=300.0,
            sample_rate=16000,
            snr_estimate=25.0,
            language="en",
            speaker_count=1
        )
        
        features = fp.to_features()
        
        # Check shape
        assert len(features) == 12  # 7 numeric + 5 language one-hot
        
        # Check values
        assert features[0] == 300.0  # duration
        assert features[1] == 16.0  # sample_rate in kHz
        assert features[7] == 1.0  # English one-hot
        
        # Check numpy array
        assert isinstance(features, np.ndarray)
        assert features.dtype == np.float32
    
    def test_language_encoding(self):
        """Test language one-hot encoding."""
        # English
        fp_en = AudioFingerprint(duration=100.0, language="en")
        features_en = fp_en.to_features()
        assert features_en[7] == 1.0  # English
        assert features_en[8] == 0.0  # Hindi
        
        # Hindi
        fp_hi = AudioFingerprint(duration=100.0, language="hi")
        features_hi = fp_hi.to_features()
        assert features_hi[7] == 0.0  # English
        assert features_hi[8] == 1.0  # Hindi
        
        # Unknown language
        fp_unk = AudioFingerprint(duration=100.0, language="fr")
        features_unk = fp_unk.to_features()
        assert features_unk[7] == 0.0  # All zeros
        assert features_unk[8] == 0.0


class TestAdaptiveQualityPredictor:
    """Test AdaptiveQualityPredictor class."""
    
    def test_create_predictor(self):
        """Test predictor initialization."""
        predictor = AdaptiveQualityPredictor(
            model_path=Path("/tmp/test_model.pkl"),
            min_training_samples=50,
            confidence_threshold=0.7
        )
        
        assert predictor.model_path == Path("/tmp/test_model.pkl")
        assert predictor.min_training_samples == 50
        assert predictor.confidence_threshold == 0.7
        assert predictor.model is None  # No model file exists
    
    def test_rule_based_clean_audio_short(self):
        """Test rule-based prediction for clean, short audio."""
        predictor = AdaptiveQualityPredictor()
        
        # Clean audio (SNR > 25), short duration (<5 min)
        fp = AudioFingerprint(
            duration=240.0,  # 4 minutes
            snr_estimate=30.0,
            speaker_count=1
        )
        
        config = predictor.predict_optimal_config(fp)
        
        assert config.whisper_model == "small"
        assert config.confidence == 0.6  # Rule-based confidence
        assert "Clean audio" in config.reasoning
    
    def test_rule_based_clean_audio_medium(self):
        """Test rule-based prediction for clean, medium audio."""
        predictor = AdaptiveQualityPredictor()
        
        # Clean audio (SNR > 25), medium duration (5-15 min)
        fp = AudioFingerprint(
            duration=600.0,  # 10 minutes
            snr_estimate=28.0,
            speaker_count=1
        )
        
        config = predictor.predict_optimal_config(fp)
        
        assert config.whisper_model == "medium"
        assert "Clean audio" in config.reasoning
    
    def test_rule_based_noisy_audio(self):
        """Test rule-based prediction for noisy audio."""
        predictor = AdaptiveQualityPredictor()
        
        # Noisy audio (SNR < 15)
        fp = AudioFingerprint(
            duration=300.0,
            snr_estimate=10.0,
            speaker_count=1
        )
        
        config = predictor.predict_optimal_config(fp)
        
        assert config.whisper_model == "large-v3"
        assert "Challenging audio" in config.reasoning
    
    def test_rule_based_multiple_speakers(self):
        """Test rule-based prediction for multi-speaker audio."""
        predictor = AdaptiveQualityPredictor()
        
        # Multiple speakers (>2)
        fp = AudioFingerprint(
            duration=300.0,
            snr_estimate=20.0,
            speaker_count=3
        )
        
        config = predictor.predict_optimal_config(fp)
        
        assert config.whisper_model == "large-v3"
        assert "3 speakers" in config.reasoning
    
    def test_wer_estimation_clean(self):
        """Test WER estimation for clean audio."""
        predictor = AdaptiveQualityPredictor()
        
        fp = AudioFingerprint(
            duration=300.0,
            snr_estimate=30.0,  # Very clean
            speaker_count=1
        )
        
        wer_small = predictor._estimate_wer(fp, "small")
        wer_large = predictor._estimate_wer(fp, "large-v3")
        
        # Larger models should have lower WER
        assert wer_large < wer_small
        
        # Clean audio should have low WER
        assert wer_large < 0.05
    
    def test_wer_estimation_noisy(self):
        """Test WER estimation for noisy audio."""
        predictor = AdaptiveQualityPredictor()
        
        fp = AudioFingerprint(
            duration=300.0,
            snr_estimate=10.0,  # Noisy
            speaker_count=1
        )
        
        wer = predictor._estimate_wer(fp, "large-v3")
        
        # Noisy audio should have higher WER (2x base rate due to SNR < 15)
        assert wer >= 0.05  # At least base rate for large-v3
    
    def test_duration_estimation(self):
        """Test processing duration estimation."""
        predictor = AdaptiveQualityPredictor()
        
        fp = AudioFingerprint(duration=600.0)  # 10 minutes
        
        duration_small = predictor._estimate_duration(fp, "small")
        duration_large = predictor._estimate_duration(fp, "large-v3")
        
        # Larger models should take longer
        assert duration_large > duration_small
        
        # Should be faster than realtime
        assert duration_small < fp.duration
        assert duration_large < fp.duration
    
    def test_default_configs(self):
        """Test default configuration parameters."""
        predictor = AdaptiveQualityPredictor()
        
        # Check all model sizes have configs
        for model_size in predictor.MODEL_SIZES:
            assert model_size in predictor.DEFAULT_CONFIGS
            config = predictor.DEFAULT_CONFIGS[model_size]
            assert "batch_size" in config
            assert "beam_size" in config
            assert config["batch_size"] > 0
            assert config["beam_size"] > 0
    
    def test_learn_from_result(self, tmp_path):
        """Test learning from processing results."""
        predictor = AdaptiveQualityPredictor(model_path=tmp_path / "model.pkl")
        
        fp = AudioFingerprint(duration=300.0)
        config_used = {"whisper_model": "large-v3", "batch_size": 8}
        actual_result = {"processing_duration": 90.0, "estimated_wer": 0.03}
        
        # Should not raise exception
        predictor.learn_from_result(fp, config_used, actual_result)
        
        # Check training data directory created
        training_dir = predictor.model_path.parent / "training_data"
        assert training_dir.exists()
        
        # Check result file created
        result_files = list(training_dir.glob("result_*.json"))
        assert len(result_files) > 0


class TestPredictionConfig:
    """Test PredictionConfig dataclass."""
    
    def test_create_config(self):
        """Test configuration creation."""
        config = PredictionConfig(
            whisper_model="large-v3",
            batch_size=8,
            beam_size=5,
            expected_wer=0.03,
            expected_duration=120.0,
            confidence=0.85,
            reasoning="ML prediction based on clean audio"
        )
        
        assert config.whisper_model == "large-v3"
        assert config.batch_size == 8
        assert config.beam_size == 5
        assert config.expected_wer == 0.03
        assert config.expected_duration == 120.0
        assert config.confidence == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
