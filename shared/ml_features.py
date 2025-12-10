#!/usr/bin/env python3
"""
ML Feature Extraction for Adaptive Optimization.

This module extracts media characteristics for ML-based parameter prediction.
"""

# Standard library
import json
import logging
from pathlib import Path
from typing import Dict, Optional

# Third-party
import numpy as np

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


class MediaFeatureExtractor:
    """
    Extract ML features from media files for adaptive optimization.
    
    Features extracted:
    - duration: Audio length in seconds
    - snr: Signal-to-noise ratio in dB
    - language: Detected language code
    - speaker_count: Number of speakers detected
    - speech_ratio: Ratio of speech to total audio
    - complexity: Audio complexity score (0-1)
    """
    
    def __init__(self):
        """Initialize feature extractor."""
        self.logger = logger
    
    def extract_features(
        self,
        audio_path: Path,
        audio_info: Optional[Dict] = None
    ) -> Dict:
        """
        Extract ML features from audio file.
        
        Args:
            audio_path: Path to audio file (WAV)
            audio_info: Optional pre-computed audio info from demux
        
        Returns:
            Dictionary of features:
            {
                'duration': 300.0,           # seconds
                'snr': 18.5,                 # dB
                'language': 'en',            # language code
                'speaker_count': 2,          # number of speakers
                'speech_ratio': 0.85,        # 0-1
                'complexity': 0.42,          # 0-1
                'sample_rate': 16000,        # Hz
                'channels': 1                # mono/stereo
            }
        
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If audio file is invalid
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        if not audio_path.is_file():
            raise ValueError(f"Not a file: {audio_path}")
        
        self.logger.info(f"Extracting features from: {audio_path.name}")
        
        # Initialize features with defaults
        features = {
            'duration': 0.0,
            'snr': 15.0,  # Default moderate SNR
            'language': 'unknown',
            'speaker_count': 1,
            'speech_ratio': 0.8,  # Default estimate
            'complexity': 0.5,  # Default moderate complexity
            'sample_rate': 16000,
            'channels': 1
        }
        
        # Use pre-computed audio info if available
        if audio_info:
            features.update({
                'duration': audio_info.get('duration', 0.0),
                'language': audio_info.get('language', 'unknown'),
                'speaker_count': audio_info.get('speakers', 1),
                'sample_rate': audio_info.get('sample_rate', 16000),
                'channels': audio_info.get('channels', 1)
            })
        
        # Compute advanced features
        try:
            # Import librosa for audio analysis
            import librosa
            
            # Load audio (use first 30 seconds for efficiency)
            y, sr = librosa.load(str(audio_path), sr=None, duration=30)
            
            # Update sample rate if loaded
            features['sample_rate'] = sr
            
            # Compute SNR (signal-to-noise ratio)
            features['snr'] = self._compute_snr(y, sr)
            
            # Compute speech ratio (energy-based estimate)
            features['speech_ratio'] = self._compute_speech_ratio(y, sr)
            
            # Compute complexity (spectral complexity)
            features['complexity'] = self._compute_complexity(y, sr)
            
            self.logger.info(f"Features extracted: duration={features['duration']:.1f}s, "
                           f"SNR={features['snr']:.1f}dB, "
                           f"speech_ratio={features['speech_ratio']:.2f}")
        
        except ImportError:
            self.logger.warning("librosa not available, using basic features only")
        
        except Exception as e:
            self.logger.warning(f"Error extracting advanced features: {e}")
            self.logger.debug("Using default feature values")
        
        return features
    
    def _compute_snr(self, audio: np.ndarray, sr: int) -> float:
        """
        Compute signal-to-noise ratio.
        
        Args:
            audio: Audio samples
            sr: Sample rate
        
        Returns:
            SNR in dB
        """
        try:
            # Split into frames
            frame_length = int(sr * 0.025)  # 25ms frames
            hop_length = int(sr * 0.010)    # 10ms hop
            
            # Compute RMS energy per frame
            import librosa
            rms = librosa.feature.rms(
                y=audio,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Estimate signal (top 75% of energy)
            signal_threshold = np.percentile(rms, 25)
            signal_frames = rms[rms > signal_threshold]
            
            # Estimate noise (bottom 25% of energy)
            noise_frames = rms[rms <= signal_threshold]
            
            if len(signal_frames) == 0 or len(noise_frames) == 0:
                return 15.0  # Default moderate SNR
            
            # Compute SNR
            signal_power = np.mean(signal_frames ** 2)
            noise_power = np.mean(noise_frames ** 2)
            
            if noise_power == 0:
                return 30.0  # Very clean signal
            
            snr = 10 * np.log10(signal_power / noise_power)
            
            # Clamp to reasonable range
            snr = np.clip(snr, 0, 40)
            
            return float(snr)
        
        except Exception as e:
            self.logger.debug(f"SNR computation failed: {e}")
            return 15.0  # Default
    
    def _compute_speech_ratio(self, audio: np.ndarray, sr: int) -> float:
        """
        Estimate ratio of speech to total audio (energy-based).
        
        Args:
            audio: Audio samples
            sr: Sample rate
        
        Returns:
            Speech ratio (0-1)
        """
        try:
            # Compute RMS energy
            import librosa
            frame_length = int(sr * 0.025)
            hop_length = int(sr * 0.010)
            
            rms = librosa.feature.rms(
                y=audio,
                frame_length=frame_length,
                hop_length=hop_length
            )[0]
            
            # Threshold for speech detection (adaptive)
            threshold = np.percentile(rms, 30)
            
            # Count frames above threshold
            speech_frames = np.sum(rms > threshold)
            total_frames = len(rms)
            
            if total_frames == 0:
                return 0.8  # Default
            
            ratio = speech_frames / total_frames
            
            # Clamp to reasonable range
            ratio = np.clip(ratio, 0.3, 1.0)
            
            return float(ratio)
        
        except Exception as e:
            self.logger.debug(f"Speech ratio computation failed: {e}")
            return 0.8  # Default
    
    def _compute_complexity(self, audio: np.ndarray, sr: int) -> float:
        """
        Compute audio complexity score (spectral complexity).
        
        High complexity = multiple speakers, music, noise
        Low complexity = single speaker, clear speech
        
        Args:
            audio: Audio samples
            sr: Sample rate
        
        Returns:
            Complexity score (0-1)
        """
        try:
            import librosa
            
            # Compute spectral features
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)[0]
            
            # Normalize and combine
            centroid_var = np.std(spectral_centroid) / (np.mean(spectral_centroid) + 1e-6)
            bandwidth_mean = np.mean(spectral_bandwidth) / (sr / 2)
            rolloff_var = np.std(spectral_rolloff) / (np.mean(spectral_rolloff) + 1e-6)
            
            # Weighted average
            complexity = (
                0.4 * centroid_var +
                0.3 * bandwidth_mean +
                0.3 * rolloff_var
            )
            
            # Clamp to 0-1
            complexity = np.clip(complexity, 0, 1)
            
            return float(complexity)
        
        except Exception as e:
            self.logger.debug(f"Complexity computation failed: {e}")
            return 0.5  # Default moderate complexity
    
    def save_features(self, features: Dict, output_path: Path) -> None:
        """
        Save features to JSON file.
        
        Args:
            features: Feature dictionary
            output_path: Path to save JSON
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(features, f, indent=2)
        
        self.logger.debug(f"Features saved to: {output_path}")
    
    def load_features(self, input_path: Path) -> Dict:
        """
        Load features from JSON file.
        
        Args:
            input_path: Path to JSON file
        
        Returns:
            Feature dictionary
        
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If JSON is invalid
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Features file not found: {input_path}")
        
        with open(input_path, 'r') as f:
            features = json.load(f)
        
        self.logger.debug(f"Features loaded from: {input_path}")
        
        return features


def extract_features(
    audio_path: Path,
    audio_info: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to extract features.
    
    Args:
        audio_path: Path to audio file
        audio_info: Optional pre-computed audio info
    
    Returns:
        Feature dictionary
    """
    extractor = MediaFeatureExtractor()
    return extractor.extract_features(audio_path, audio_info)


def extract_audio_fingerprint(
    audio_file: str,
    language: str = "en"
) -> 'AudioFingerprint':
    """
    Extract audio fingerprint for ML optimization (Task #16).
    
    Lightweight wrapper that extracts features and converts to AudioFingerprint.
    
    Args:
        audio_file: Path to audio WAV file
        language: ISO 639-1 language code
        
    Returns:
        AudioFingerprint with extracted features
    """
    from shared.ml_optimizer import AudioFingerprint
    
    audio_path = Path(audio_file)
    
    # Extract features using existing extractor
    features = extract_features(audio_path)
    
    # Convert to AudioFingerprint (correct field names)
    file_size_mb = audio_path.stat().st_size / (1024 * 1024)
    
    return AudioFingerprint(
        duration=features['duration'],
        sample_rate=features['sample_rate'],
        channels=features['channels'],
        file_size=file_size_mb,
        snr_estimate=features['snr'],
        speaker_count=features['speaker_count'],
        complexity_score=features['complexity'],
        language=language
    )


if __name__ == '__main__':
    # Test feature extraction
    import sys
    
    if len(sys.argv) < 2:
        logger.info("Usage: python3 ml_features.py <audio_file>")
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    
    logger.info(f"Extracting features from: {audio_file}")
    features = extract_features(audio_file)
    
    logger.info("\nExtracted features:")
    for key, value in features.items():
        logger.info(f"  {key}: {value}")
