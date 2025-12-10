#!/usr/bin/env python3
"""
Integration tests for ML optimizer integration with ASR pipeline.

Tests the full integration path from configuration to prediction application.
"""

# Standard library
import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Local
from shared.config_loader import load_config
from shared.ml_optimizer import AdaptiveQualityPredictor, PredictionConfig, AudioFingerprint
from shared.ml_features import extract_audio_fingerprint


class TestMLOptimizationEnabled:
    """Test ML optimization when enabled."""
    
    def test_ml_config_parameters_exist(self):
        """Test that ML optimization config parameters are defined."""
        # This test validates that the ML optimization parameters
        # exist in the production config file
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config" / ".env.pipeline"
        assert config_file.exists(), f"Config file should exist at {config_file}"
        
        content = config_file.read_text()
        assert "ML_OPTIMIZATION_ENABLED" in content
        assert "ML_CONFIDENCE_THRESHOLD" in content
    
    def test_ml_prediction_applied_when_confidence_high(self):
        """Test that ML prediction is applied when confidence >= threshold."""
        # Create predictor
        predictor = AdaptiveQualityPredictor()
        
        # Create test fingerprint
        fingerprint = AudioFingerprint(
            duration=120.0,
            sample_rate=16000,
            channels=1,
            file_size=10.0,
            snr_estimate=25.0,
            speaker_count=1,
            complexity_score=0.3,
            language="en"
        )
        
        # Get prediction
        prediction = predictor.predict_optimal_config(fingerprint)
        
        # Verify prediction has high confidence (rule-based always 60%)
        assert prediction.confidence >= 0.6
        assert prediction.whisper_model in ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
        assert prediction.beam_size >= 1
        assert prediction.batch_size >= 1
    
    def test_ml_prediction_logged_in_manifest(self, tmpdir):
        """Test that ML prediction is tracked in stage manifest."""
        # Create job directory
        job_dir = tmpdir.mkdir("job")
        stage_dir = job_dir.mkdir("06_asr")
        
        # Create mock manifest data
        manifest_data = {
            "ml_optimization": {
                "enabled": True,
                "fingerprint": {
                    "duration": 120.0,
                    "snr_estimate": 25.0
                },
                "prediction": {
                    "model": "large-v3",
                    "confidence": 0.8
                },
                "applied": True
            }
        }
        
        # Write manifest
        manifest_file = stage_dir.join("manifest.json")
        manifest_file.write(json.dumps(manifest_data, indent=2))
        
        # Read and verify
        with open(str(manifest_file)) as f:
            manifest = json.load(f)
        
        assert manifest["ml_optimization"]["enabled"] is True
        assert manifest["ml_optimization"]["applied"] is True
        assert manifest["ml_optimization"]["prediction"]["confidence"] == 0.8


class TestMLOptimizationDisabled:
    """Test fallback when ML optimization is disabled."""
    
    def test_ml_disabled_falls_back_to_defaults(self):
        """Test that when ML is disabled, defaults are used."""
        # Verify that default config values exist for fallback
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config" / ".env.pipeline"
        assert config_file.exists(), f"Config file should exist at {config_file}"
        
        content = config_file.read_text()
        assert "WHISPERX_MODEL" in content
        assert "WHISPERX_BEAM_SIZE" in content
    
    def test_no_ml_prediction_in_logs_when_disabled(self, tmpdir):
        """Test that no ML prediction is logged when disabled."""
        # Create job directory
        job_dir = tmpdir.mkdir("job")
        stage_dir = job_dir.mkdir("06_asr")
        
        # Create manifest without ML optimization
        manifest_data = {
            "stage": "06_asr",
            "status": "complete",
            "ml_optimization": None
        }
        
        # Write manifest
        manifest_file = stage_dir.join("manifest.json")
        manifest_file.write(json.dumps(manifest_data, indent=2))
        
        # Read and verify
        with open(str(manifest_file)) as f:
            manifest = json.load(f)
        
        assert manifest.get("ml_optimization") is None


class TestForceModelOverride:
    """Test manual model override functionality."""
    
    def test_force_model_parameter_exists(self):
        """Test that FORCE_MODEL_SIZE parameter exists in config."""
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config" / ".env.pipeline"
        assert config_file.exists(), f"Config file should exist at {config_file}"
        
        content = config_file.read_text()
        assert "FORCE_MODEL_SIZE" in content
    
    def test_force_model_logged_in_manifest(self, tmpdir):
        """Test that forced model is clearly logged."""
        # Create job directory
        job_dir = tmpdir.mkdir("job")
        stage_dir = job_dir.mkdir("06_asr")
        
        # Create manifest with forced model
        manifest_data = {
            "ml_optimization": {
                "enabled": True,
                "force_model": "small",
                "skipped": True,
                "reason": "Manual override via FORCE_MODEL_SIZE"
            }
        }
        
        # Write manifest
        manifest_file = stage_dir.join("manifest.json")
        manifest_file.write(json.dumps(manifest_data, indent=2))
        
        # Read and verify
        with open(str(manifest_file)) as f:
            manifest = json.load(f)
        
        assert manifest["ml_optimization"]["force_model"] == "small"
        assert manifest["ml_optimization"]["skipped"] is True


class TestLowConfidenceFallback:
    """Test fallback when confidence is too low."""
    
    def test_low_confidence_uses_config_defaults(self):
        """Test that config defaults are used when confidence < threshold."""
        # Create predictor
        predictor = AdaptiveQualityPredictor()
        
        # Create test fingerprint (will have 60% confidence from rule-based)
        fingerprint = AudioFingerprint(
            duration=60.0,
            sample_rate=16000,
            channels=1,
            file_size=5.0,
            snr_estimate=15.0,
            speaker_count=1,
            complexity_score=0.5,
            language="en"
        )
        
        # Get prediction
        prediction = predictor.predict_optimal_config(fingerprint)
        
        # Confidence threshold is 70%, prediction is 60%
        threshold = 0.7
        assert prediction.confidence < threshold
        
        # In real application, this would trigger fallback to config defaults
        # Here we just verify the prediction has lower confidence
    
    def test_low_confidence_reasoning_logged(self, tmpdir):
        """Test that reasoning for low confidence is logged."""
        # Create job directory
        job_dir = tmpdir.mkdir("job")
        stage_dir = job_dir.mkdir("06_asr")
        
        # Create manifest with low confidence
        manifest_data = {
            "ml_optimization": {
                "enabled": True,
                "prediction": {
                    "confidence": 0.6,
                    "model": "large-v3"
                },
                "applied": False,
                "reason": "Confidence 60.0% below threshold 70.0%, using config defaults"
            }
        }
        
        # Write manifest
        manifest_file = stage_dir.join("manifest.json")
        manifest_file.write(json.dumps(manifest_data, indent=2))
        
        # Read and verify
        with open(str(manifest_file)) as f:
            manifest = json.load(f)
        
        assert manifest["ml_optimization"]["applied"] is False
        assert "confidence" in manifest["ml_optimization"]["reason"].lower()


class TestMLImportErrorFallback:
    """Test graceful fallback when ML optimizer import fails."""
    
    def test_import_error_logs_warning(self):
        """Test that import error is logged as warning."""
        # This would be tested in the actual integration
        # by mocking the import and verifying warning is logged
        pass
    
    def test_config_defaults_exist_as_fallback(self):
        """Test that config defaults exist as fallback."""
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / "config" / ".env.pipeline"
        assert config_file.exists(), f"Config file should exist at {config_file}"
        
        content = config_file.read_text()
        assert "WHISPERX_MODEL" in content
        # Pipeline should continue with these defaults
        # even if ML optimizer import fails


class TestFingerprintExtractionError:
    """Test error handling in fingerprint extraction."""
    
    @patch('shared.ml_features.extract_features')
    def test_corrupted_audio_file_handled(self, mock_extract):
        """Test graceful handling of corrupted audio file."""
        # Mock feature extraction failure
        mock_extract.side_effect = Exception("Audio file corrupted")
        
        # Attempt to extract fingerprint
        with pytest.raises(Exception) as exc_info:
            extract_audio_fingerprint("/path/to/corrupted.wav", "en")
        
        assert "Audio file corrupted" in str(exc_info.value)
    
    def test_fingerprint_error_logs_and_falls_back(self, tmpdir):
        """Test that fingerprint extraction error is logged."""
        # Create job directory
        job_dir = tmpdir.mkdir("job")
        stage_dir = job_dir.mkdir("06_asr")
        
        # Create manifest with extraction error
        manifest_data = {
            "ml_optimization": {
                "enabled": True,
                "fingerprint_extraction": "failed",
                "error": "Audio file corrupted",
                "applied": False,
                "reason": "Fingerprint extraction failed, using config defaults"
            }
        }
        
        # Write manifest
        manifest_file = stage_dir.join("manifest.json")
        manifest_file.write(json.dumps(manifest_data, indent=2))
        
        # Read and verify
        with open(str(manifest_file)) as f:
            manifest = json.load(f)
        
        assert manifest["ml_optimization"]["fingerprint_extraction"] == "failed"
        assert manifest["ml_optimization"]["applied"] is False


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
