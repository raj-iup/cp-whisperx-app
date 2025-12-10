#!/usr/bin/env python3
"""
ML-Based Adaptive Quality Prediction

This module implements machine learning-based prediction of optimal
Whisper model parameters based on audio characteristics.

Key Features:
- Audio fingerprint extraction (duration, SNR, language, speaker count)
- XGBoost-based model prediction
- Continuous learning from processing results
- Graceful fallback to defaults when no training data

Usage:
    from shared.ml_optimizer import AdaptiveQualityPredictor
    
    predictor = AdaptiveQualityPredictor()
    audio_features = predictor.extract_features(audio_file)
    config = predictor.predict_optimal_config(audio_features)
    
    # Use predicted config
    whisper_model = config['whisper_model']
    batch_size = config['batch_size']
"""

# Standard library
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Third-party
import numpy as np

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AudioFingerprint:
    """
    Audio characteristics used for ML prediction.
    
    Attributes:
        duration: Audio duration in seconds
        sample_rate: Audio sample rate (Hz)
        channels: Number of audio channels
        snr_estimate: Signal-to-noise ratio estimate (dB)
        language: Detected or specified language code
        speaker_count: Number of speakers detected (0 = unknown)
        complexity_score: Audio complexity score (0-1)
        file_size: Audio file size in MB
    """
    duration: float
    sample_rate: int = 16000
    channels: int = 1
    snr_estimate: float = 20.0  # Default: reasonable quality
    language: str = "auto"
    speaker_count: int = 0
    complexity_score: float = 0.5
    file_size: float = 0.0
    
    def to_features(self) -> np.ndarray:
        """
        Convert fingerprint to feature vector for ML model.
        
        Returns:
            Feature vector as numpy array
        """
        features = [
            self.duration,
            self.sample_rate / 1000.0,  # Normalize to kHz
            self.channels,
            self.snr_estimate,
            self.speaker_count,
            self.complexity_score,
            self.file_size,
            # Language encoding (one-hot top 5 languages)
            1.0 if self.language == 'en' else 0.0,
            1.0 if self.language == 'hi' else 0.0,
            1.0 if self.language == 'es' else 0.0,
            1.0 if self.language == 'zh' else 0.0,
            1.0 if self.language == 'ar' else 0.0,
        ]
        return np.array(features, dtype=np.float32)
    
    @classmethod
    def from_audio_file(cls, audio_file: Path, job_dir: Path) -> "AudioFingerprint":
        """
        Extract audio fingerprint from audio file.
        
        Args:
            audio_file: Path to audio file
            job_dir: Job directory for finding metadata
        
        Returns:
            AudioFingerprint instance
        """
        import librosa
        
        logger.info(f"📊 Extracting audio fingerprint from {audio_file.name}")
        
        # Get file size
        file_size_mb = audio_file.stat().st_size / (1024 * 1024)
        
        # Load audio metadata (fast)
        try:
            duration = librosa.get_duration(path=str(audio_file))
            sr = librosa.get_samplerate(path=str(audio_file))
        except Exception as e:
            logger.warning(f"Failed to extract audio metadata: {e}")
            duration = 0.0
            sr = 16000
        
        # Try to load VAD manifest for speaker count
        speaker_count = 0
        vad_manifest = job_dir / "05_pyannote_vad" / "vad_manifest.json"
        if vad_manifest.exists():
            try:
                with open(vad_manifest) as f:
                    vad_data = json.load(f)
                    # Count unique speakers
                    speakers = set()
                    for seg in vad_data.get("outputs", {}).get("segments", []):
                        if "speaker" in seg:
                            speakers.add(seg["speaker"])
                    speaker_count = len(speakers)
            except Exception as e:
                logger.debug(f"Could not load VAD manifest: {e}")
        
        # Estimate SNR and complexity (simplified)
        # In production, this would analyze audio samples
        snr_estimate = 20.0  # Default: reasonable quality
        complexity_score = 0.5  # Default: medium complexity
        
        # Try to detect language from job config
        language = "auto"
        try:
            job_json = job_dir / "job.json"
            if job_json.exists():
                with open(job_json) as f:
                    job_data = json.load(f)
                    language = job_data.get("source_language", "auto")
        except Exception as e:
            logger.debug(f"Could not load job config: {e}")
        
        fingerprint = cls(
            duration=duration,
            sample_rate=sr,
            channels=1,  # Always mono after demux
            snr_estimate=snr_estimate,
            language=language,
            speaker_count=speaker_count,
            complexity_score=complexity_score,
            file_size=file_size_mb
        )
        
        logger.info(f"✅ Fingerprint: {duration:.1f}s, {speaker_count} speakers, lang={language}")
        return fingerprint


@dataclass
class PredictionConfig:
    """
    Predicted optimal configuration for Whisper ASR.
    
    Attributes:
        whisper_model: Model size (tiny/base/small/medium/large/large-v2/large-v3)
        batch_size: Batch size for processing
        beam_size: Beam size for decoding
        expected_wer: Expected Word Error Rate
        expected_duration: Expected processing duration (seconds)
        confidence: Prediction confidence (0-1)
        reasoning: Human-readable reasoning for prediction
    """
    whisper_model: str
    batch_size: int
    beam_size: int
    expected_wer: float
    expected_duration: float
    confidence: float
    reasoning: str


class AdaptiveQualityPredictor:
    """
    Predicts optimal Whisper model parameters using ML.
    
    This class uses XGBoost to predict the best model configuration
    based on audio characteristics. It learns from historical job
    results to continuously improve predictions.
    
    Features:
    - Audio fingerprint extraction
    - Model size prediction
    - Parameter optimization
    - Continuous learning
    - Graceful fallback
    
    Example:
        predictor = AdaptiveQualityPredictor()
        
        # Extract features
        audio_fp = AudioFingerprint.from_audio_file(audio_path, job_dir)
        
        # Get prediction
        config = predictor.predict_optimal_config(audio_fp)
        
        # Use prediction
        model = config.whisper_model
        batch = config.batch_size
    """
    
    # Model size options in order of resource requirements
    MODEL_SIZES = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    
    # Default configurations by model size
    DEFAULT_CONFIGS = {
        "tiny": {"batch_size": 32, "beam_size": 3},
        "base": {"batch_size": 24, "beam_size": 4},
        "small": {"batch_size": 16, "beam_size": 5},
        "medium": {"batch_size": 12, "beam_size": 5},
        "large": {"batch_size": 8, "beam_size": 5},
        "large-v2": {"batch_size": 8, "beam_size": 5},
        "large-v3": {"batch_size": 8, "beam_size": 5},
    }
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        min_training_samples: int = 100,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize adaptive quality predictor.
        
        Args:
            model_path: Path to trained model file (None = default)
            min_training_samples: Minimum samples needed for training
            confidence_threshold: Minimum confidence to use prediction
        """
        self.model_path = model_path or Path.home() / ".cp-whisperx" / "models" / "ml_optimizer.pkl"
        self.min_training_samples = min_training_samples
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.training_stats = {}
        
        # Try to load existing model
        if self.model_path.exists():
            self._load_model()
        else:
            logger.info("📚 No trained model found, will use rule-based heuristics")
    
    def _load_model(self) -> None:
        """Load trained ML model from disk."""
        try:
            import joblib
            self.model = joblib.load(self.model_path)
            logger.info(f"✅ Loaded ML model from {self.model_path}")
            
            # Load training stats
            stats_path = self.model_path.with_suffix('.stats.json')
            if stats_path.exists():
                with open(stats_path) as f:
                    self.training_stats = json.load(f)
                logger.info(f"📊 Model trained on {self.training_stats.get('num_samples', 0)} samples")
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")
            self.model = None
    
    def _save_model(self) -> None:
        """Save trained ML model to disk."""
        try:
            import joblib
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            joblib.dump(self.model, self.model_path)
            
            # Save training stats
            stats_path = self.model_path.with_suffix('.stats.json')
            with open(stats_path, 'w') as f:
                json.dump(self.training_stats, f, indent=2)
            
            logger.info(f"✅ Saved ML model to {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to save ML model: {e}")
    
    def predict_optimal_config(
        self,
        audio_fp: AudioFingerprint,
        fallback_model: str = "large-v3"
    ) -> PredictionConfig:
        """
        Predict optimal Whisper configuration for audio.
        
        Args:
            audio_fp: Audio fingerprint
            fallback_model: Model to use if prediction fails
        
        Returns:
            Predicted configuration
        """
        logger.info("🔮 Predicting optimal Whisper configuration...")
        
        # If no trained model, use rule-based heuristics
        if self.model is None:
            return self._rule_based_prediction(audio_fp, fallback_model)
        
        # Extract features
        features = audio_fp.to_features().reshape(1, -1)
        
        try:
            # Predict model size (0-6 index)
            model_idx = self.model.predict(features)[0]
            confidence = float(np.max(self.model.predict_proba(features)[0]))
            
            # If confidence too low, fall back to rules
            if confidence < self.confidence_threshold:
                logger.info(f"⚠️  Low confidence ({confidence:.2f}), using rule-based fallback")
                return self._rule_based_prediction(audio_fp, fallback_model)
            
            # Get model size
            model_size = self.MODEL_SIZES[int(model_idx)]
            config = self.DEFAULT_CONFIGS[model_size]
            
            # Estimate WER and duration based on model and audio characteristics
            expected_wer = self._estimate_wer(audio_fp, model_size)
            expected_duration = self._estimate_duration(audio_fp, model_size)
            
            reasoning = f"ML prediction (confidence={confidence:.2f}): " \
                       f"{model_size} optimal for {audio_fp.duration:.0f}s audio, " \
                       f"{audio_fp.speaker_count} speakers, SNR={audio_fp.snr_estimate:.1f}dB"
            
            logger.info(f"✅ Predicted: {model_size} (confidence={confidence:.2f})")
            
            return PredictionConfig(
                whisper_model=model_size,
                batch_size=config["batch_size"],
                beam_size=config["beam_size"],
                expected_wer=expected_wer,
                expected_duration=expected_duration,
                confidence=confidence,
                reasoning=reasoning
            )
        
        except Exception as e:
            logger.error(f"ML prediction failed: {e}, using rule-based fallback")
            return self._rule_based_prediction(audio_fp, fallback_model)
    
    def _rule_based_prediction(
        self,
        audio_fp: AudioFingerprint,
        fallback_model: str
    ) -> PredictionConfig:
        """
        Rule-based heuristic prediction (fallback).
        
        Rules:
        - Clean audio (SNR > 25dB), short (<5 min) → small/medium
        - Clean audio (SNR > 25dB), long → medium/large
        - Noisy audio (SNR < 15dB) → large
        - Multiple speakers (>2) → large
        - Default → large-v3
        
        Args:
            audio_fp: Audio fingerprint
            fallback_model: Default model if no clear rule
        
        Returns:
            Predicted configuration
        """
        duration_min = audio_fp.duration / 60.0
        snr = audio_fp.snr_estimate
        speakers = audio_fp.speaker_count
        
        # Rule-based decision tree
        if snr > 25 and duration_min < 5:
            model_size = "small"
            reasoning = f"Clean audio ({snr:.1f}dB), short duration ({duration_min:.1f}min)"
        elif snr > 25 and duration_min < 15:
            model_size = "medium"
            reasoning = f"Clean audio ({snr:.1f}dB), medium duration ({duration_min:.1f}min)"
        elif snr < 15 or speakers > 2:
            model_size = "large-v3"
            reasoning = f"Challenging audio: SNR={snr:.1f}dB, {speakers} speakers"
        else:
            model_size = fallback_model
            reasoning = f"Default: moderate audio quality, {duration_min:.1f}min"
        
        config = self.DEFAULT_CONFIGS[model_size]
        expected_wer = self._estimate_wer(audio_fp, model_size)
        expected_duration = self._estimate_duration(audio_fp, model_size)
        
        logger.info(f"📋 Rule-based: {model_size} ({reasoning})")
        
        return PredictionConfig(
            whisper_model=model_size,
            batch_size=config["batch_size"],
            beam_size=config["beam_size"],
            expected_wer=expected_wer,
            expected_duration=expected_duration,
            confidence=0.6,  # Medium confidence for rule-based
            reasoning=f"Rule-based: {reasoning}"
        )
    
    def _estimate_wer(self, audio_fp: AudioFingerprint, model_size: str) -> float:
        """
        Estimate Word Error Rate for model and audio.
        
        Better models and cleaner audio = lower WER.
        
        Args:
            audio_fp: Audio fingerprint
            model_size: Whisper model size
        
        Returns:
            Estimated WER (0-1)
        """
        # Base WER by model size
        base_wer = {
            "tiny": 0.15,
            "base": 0.10,
            "small": 0.07,
            "medium": 0.05,
            "large": 0.04,
            "large-v2": 0.03,
            "large-v3": 0.025,
        }
        
        wer = base_wer.get(model_size, 0.05)
        
        # Adjust for audio quality
        if audio_fp.snr_estimate < 15:
            wer *= 2.0  # Noisy audio doubles WER
        elif audio_fp.snr_estimate > 25:
            wer *= 0.7  # Clean audio reduces WER
        
        # Adjust for speaker count
        if audio_fp.speaker_count > 2:
            wer *= 1.3  # Multiple speakers increases WER
        
        return min(wer, 0.50)  # Cap at 50%
    
    def _estimate_duration(self, audio_fp: AudioFingerprint, model_size: str) -> float:
        """
        Estimate processing duration for model and audio.
        
        Larger models are slower. Duration scales with audio length.
        
        Args:
            audio_fp: Audio fingerprint
            model_size: Whisper model size
        
        Returns:
            Estimated duration in seconds
        """
        # Processing speed (seconds per audio second)
        # Based on MLX backend on Apple Silicon M2
        speed_multiplier = {
            "tiny": 0.05,    # 20x realtime
            "base": 0.07,    # 14x realtime
            "small": 0.10,   # 10x realtime
            "medium": 0.15,  # 7x realtime
            "large": 0.20,   # 5x realtime
            "large-v2": 0.25,  # 4x realtime
            "large-v3": 0.30,  # 3.3x realtime
        }
        
        multiplier = speed_multiplier.get(model_size, 0.30)
        return audio_fp.duration * multiplier
    
    def learn_from_result(
        self,
        audio_fp: AudioFingerprint,
        config_used: Dict[str, Any],
        actual_result: Dict[str, Any]
    ) -> None:
        """
        Learn from actual processing result to improve predictions.
        
        This method stores the result for future model retraining.
        
        Args:
            audio_fp: Audio fingerprint
            config_used: Configuration used for processing
            actual_result: Actual processing results (WER, duration, etc.)
        """
        # Store result in training data directory
        training_dir = self.model_path.parent / "training_data"
        training_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = training_dir / f"result_{timestamp}.json"
        
        training_sample = {
            "timestamp": timestamp,
            "audio_fingerprint": asdict(audio_fp),
            "config_used": config_used,
            "actual_result": actual_result,
        }
        
        try:
            with open(result_file, 'w') as f:
                json.dump(training_sample, f, indent=2)
            logger.debug(f"📝 Stored training sample: {result_file.name}")
        except Exception as e:
            logger.warning(f"Failed to store training sample: {e}")
    
    def train_model(self, training_data: List[Dict[str, Any]]) -> bool:
        """
        Train ML model on historical data.
        
        Args:
            training_data: List of training samples
        
        Returns:
            True if training successful
        """
        if len(training_data) < self.min_training_samples:
            logger.warning(
                f"Insufficient training data: {len(training_data)} < {self.min_training_samples}"
            )
            return False
        
        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
            from sklearn.metrics import accuracy_score
            
            logger.info(f"🎓 Training ML model on {len(training_data)} samples...")
            
            # Prepare features and labels
            X = []
            y = []
            
            for sample in training_data:
                fp_dict = sample["audio_fingerprint"]
                fp = AudioFingerprint(**fp_dict)
                X.append(fp.to_features())
                
                # Label is model size index
                model_used = sample["config_used"].get("whisper_model", "large-v3")
                y.append(self.MODEL_SIZES.index(model_used))
            
            X = np.array(X)
            y = np.array(y)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Train XGBoost classifier
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                objective='multi:softprob',
                num_class=len(self.MODEL_SIZES),
                random_state=42
            )
            
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            accuracy = accuracy_score(y_test, y_pred)
            
            logger.info(f"✅ Model training complete! Accuracy: {accuracy:.2%}")
            
            # Store training stats
            self.training_stats = {
                "num_samples": len(training_data),
                "accuracy": float(accuracy),
                "trained_at": datetime.now().isoformat(),
                "model_sizes": self.MODEL_SIZES,
            }
            
            # Save model
            self._save_model()
            
            return True
        
        except ImportError:
            logger.error("XGBoost not installed! Install with: pip install xgboost scikit-learn")
            return False
        except Exception as e:
            logger.error(f"Model training failed: {e}", exc_info=True)
            return False


def get_predictor() -> AdaptiveQualityPredictor:
    """
    Get singleton instance of adaptive quality predictor.
    
    Returns:
        AdaptiveQualityPredictor instance
    """
    global _predictor_instance
    
    if '_predictor_instance' not in globals():
        _predictor_instance = AdaptiveQualityPredictor()
    
    return _predictor_instance
