"""
Silero VAD implementation for native MPS pipeline.
Provides coarse-grained voice activity detection using Silero VAD model.
"""
import torch
import torchaudio
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class SileroVAD:
    """
    Silero Voice Activity Detection.
    
    Uses the Silero VAD model for fast, accurate speech detection.
    Optimized for MPS (Apple Silicon) acceleration.
    """
    
    def __init__(self, device: str = "cpu", logger=None):
        """
        Initialize Silero VAD.
        
        Args:
            device: Device to run on (cpu, cuda, mps)
            logger: Logger instance
        """
        self.device = device
        self.logger = logger
        self.model = None
        self.sample_rate = 16000  # Silero VAD requires 16kHz
        
    def load_model(self):
        """Load Silero VAD model from torch hub."""
        if self.logger:
            self.logger.info(f"Loading Silero VAD model on {self.device}")
        
        try:
            # Load model from torch hub with proper settings
            torch.set_num_threads(1)
            
            model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False,
                trust_repo=True
            )
            
            # Move to device
            device_str = self.device
            if self.device == "mps" and torch.backends.mps.is_available():
                # MPS sometimes has issues, fallback to CPU for VAD
                if self.logger:
                    self.logger.warning("Using CPU instead of MPS for better compatibility")
                device_str = "cpu"
                
            model = model.to(device_str)
            
            self.model = model
            
            # Get utility function for speech timestamps
            (get_speech_timestamps, _, _, _, _) = utils
            
            self.get_speech_timestamps = get_speech_timestamps
            
            if self.logger:
                self.logger.info("✓ Silero VAD model loaded successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load Silero VAD model: {e}")
            return False
    
    def read_audio_file(self, audio_path: Path, target_sr: int = 16000) -> torch.Tensor:
        """
        Read and resample audio file to target sample rate.
        
        Args:
            audio_path: Path to audio file
            target_sr: Target sample rate (default: 16000)
            
        Returns:
            Audio tensor at target sample rate
        """
        import soundfile as sf
        
        # Load audio with soundfile (more reliable than torchaudio for newer versions)
        waveform, sample_rate = sf.read(str(audio_path), dtype='float32')
        
        # Convert to torch tensor
        waveform = torch.from_numpy(waveform)
        
        # If stereo, convert to mono
        if waveform.ndim > 1:
            waveform = torch.mean(waveform, dim=-1)
        
        # Add channel dimension if needed
        if waveform.ndim == 1:
            waveform = waveform.unsqueeze(0)
        
        # Resample if needed
        if sample_rate != target_sr:
            resampler = torchaudio.transforms.Resample(sample_rate, target_sr)
            waveform = resampler(waveform)
        
        # Return as 1D tensor
        return waveform.squeeze()
    
    def detect_speech(
        self,
        audio_path: Path,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
        speech_pad_ms: int = 30
    ) -> List[Dict[str, float]]:
        """
        Detect speech segments in audio file.
        
        Args:
            audio_path: Path to audio file (16kHz WAV)
            threshold: Speech probability threshold (0-1)
            min_speech_duration_ms: Minimum speech duration in ms
            min_silence_duration_ms: Minimum silence duration in ms
            speech_pad_ms: Padding around speech segments in ms
            
        Returns:
            List of speech segments with start/end times
        """
        if self.model is None:
            if not self.load_model():
                raise RuntimeError("Failed to load Silero VAD model")
        
        if self.logger:
            self.logger.debug(f"Processing audio: {audio_path}")
            self.logger.debug(f"Threshold: {threshold}, min_speech: {min_speech_duration_ms}ms")
        
        # Read audio using our own method (compatible with new torchaudio)
        wav = self.read_audio_file(audio_path, target_sr=self.sample_rate)
        
        # Get speech timestamps
        speech_timestamps = self.get_speech_timestamps(
            wav,
            self.model,
            threshold=threshold,
            min_speech_duration_ms=min_speech_duration_ms,
            min_silence_duration_ms=min_silence_duration_ms,
            speech_pad_ms=speech_pad_ms,
            return_seconds=True
        )
        
        if self.logger:
            self.logger.debug(f"Detected {len(speech_timestamps)} speech segments")
        
        return speech_timestamps
    
    def merge_segments(
        self,
        segments: List[Dict[str, float]],
        max_gap: float = 0.5
    ) -> List[Dict[str, float]]:
        """
        Merge close speech segments.
        
        Args:
            segments: List of speech segments
            max_gap: Maximum gap in seconds to merge
            
        Returns:
            Merged segments
        """
        if not segments:
            return []
        
        merged = []
        current = segments[0].copy()
        
        for segment in segments[1:]:
            gap = segment['start'] - current['end']
            
            if gap <= max_gap:
                # Merge segments
                current['end'] = segment['end']
            else:
                # Save current and start new
                merged.append(current)
                current = segment.copy()
        
        # Add last segment
        merged.append(current)
        
        if self.logger:
            self.logger.debug(f"Merged {len(segments)} → {len(merged)} segments")
        
        return merged
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """Get audio file duration in seconds."""
        try:
            # Use soundfile to get duration (most reliable)
            import soundfile as sf
            info = sf.info(str(audio_path))
            duration = info.duration
            return duration
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get audio duration with soundfile: {e}")
            # Fallback: try with wave module
            try:
                import wave
                with wave.open(str(audio_path), 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    duration = frames / float(rate)
                return duration
            except Exception as e2:
                if self.logger:
                    self.logger.error(f"Failed with wave module too: {e2}")
                pass
            return 0.0
    
    def calculate_speech_ratio(
        self,
        segments: List[Dict[str, float]],
        total_duration: float
    ) -> float:
        """
        Calculate ratio of speech to total audio.
        
        Args:
            segments: Speech segments
            total_duration: Total audio duration
            
        Returns:
            Speech ratio (0-1)
        """
        if total_duration == 0:
            return 0.0
        
        speech_duration = sum(seg['end'] - seg['start'] for seg in segments)
        ratio = speech_duration / total_duration
        
        return ratio
    
    def filter_short_segments(
        self,
        segments: List[Dict[str, float]],
        min_duration: float = 0.3
    ) -> List[Dict[str, float]]:
        """
        Filter out very short segments.
        
        Args:
            segments: Speech segments
            min_duration: Minimum duration in seconds
            
        Returns:
            Filtered segments
        """
        filtered = [
            seg for seg in segments
            if (seg['end'] - seg['start']) >= min_duration
        ]
        
        if self.logger and len(filtered) < len(segments):
            removed = len(segments) - len(filtered)
            self.logger.debug(f"Filtered {removed} short segments (< {min_duration}s)")
        
        return filtered
    
    def process(
        self,
        audio_path: Path,
        threshold: float = 0.5,
        min_speech_duration_ms: int = 250,
        min_silence_duration_ms: int = 100,
        merge_gap: float = 0.5,
        min_segment_duration: float = 0.3
    ) -> Tuple[List[Dict[str, float]], Dict[str, any]]:
        """
        Full VAD processing pipeline.
        
        Args:
            audio_path: Path to audio file
            threshold: Speech detection threshold
            min_speech_duration_ms: Min speech duration
            min_silence_duration_ms: Min silence duration
            merge_gap: Max gap to merge segments
            min_segment_duration: Min final segment duration
            
        Returns:
            Tuple of (segments, statistics)
        """
        # Get total duration
        total_duration = self.get_audio_duration(audio_path)
        
        if self.logger:
            self.logger.info(f"Audio duration: {total_duration:.2f} seconds")
        
        # Detect speech
        segments = self.detect_speech(
            audio_path,
            threshold=threshold,
            min_speech_duration_ms=min_speech_duration_ms,
            min_silence_duration_ms=min_silence_duration_ms
        )
        
        # Merge close segments
        segments = self.merge_segments(segments, max_gap=merge_gap)
        
        # Filter short segments
        segments = self.filter_short_segments(segments, min_duration=min_segment_duration)
        
        # Calculate statistics
        speech_ratio = self.calculate_speech_ratio(segments, total_duration)
        
        stats = {
            'total_duration': total_duration,
            'num_segments': len(segments),
            'speech_duration': sum(seg['end'] - seg['start'] for seg in segments),
            'speech_ratio': speech_ratio,
            'threshold': threshold,
            'device': str(self.device)
        }
        
        if self.logger:
            self.logger.info(f"Detected {len(segments)} speech segments")
            self.logger.info(f"Speech ratio: {speech_ratio:.1%}")
        
        return segments, stats


def format_time(seconds: float) -> str:
    """Format seconds as HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
