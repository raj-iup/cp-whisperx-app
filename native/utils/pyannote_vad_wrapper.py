"""
Pyannote VAD wrapper for native MPS pipeline.
Provides refined voice activity detection using Pyannote.audio segmentation model.
"""
import torch
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np


class PyannoteVAD:
    """
    Pyannote Voice Activity Detection wrapper.
    
    Uses pyannote.audio's segmentation model for refined VAD.
    This stage refines the coarse Silero VAD segments with more precise boundaries.
    """
    
    def __init__(self, hf_token: str, device: str = "cpu", logger=None):
        """
        Initialize Pyannote VAD.
        
        Args:
            hf_token: HuggingFace API token for model access
            device: Device to run on (cpu, cuda, mps)
            logger: Logger instance
        """
        self.hf_token = hf_token
        self.device = device
        self.logger = logger
        self.pipeline = None
        self.sample_rate = 16000
        
    def load_model(self):
        """Load Pyannote VAD pipeline from HuggingFace."""
        if self.logger:
            self.logger.info(f"Loading Pyannote VAD pipeline on {self.device}")
        
        try:
            from pyannote.audio import Pipeline
            
            # Load the VAD pipeline
            # Note: Using segmentation-3.0 which is the latest VAD model
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/voice-activity-detection",
                use_auth_token=self.hf_token
            )
            
            # Move to device (MPS might have compatibility issues, prefer CPU)
            device_str = self.device
            if self.device == "mps":
                if self.logger:
                    self.logger.warning("MPS not fully supported by Pyannote, using CPU for stability")
                device_str = "cpu"
            
            # Set device
            if device_str != "cpu":
                self.pipeline = self.pipeline.to(torch.device(device_str))
            
            if self.logger:
                self.logger.info("✓ Pyannote VAD pipeline loaded successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load Pyannote VAD pipeline: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return False
    
    def refine_segments(
        self,
        audio_path: Path,
        coarse_segments: List[Dict[str, float]],
        onset: float = 0.5,
        offset: float = 0.5,
        min_duration_on: float = 0.0,
        min_duration_off: float = 0.0
    ) -> List[Dict[str, float]]:
        """
        Refine coarse segments using Pyannote VAD.
        
        Args:
            audio_path: Path to audio file
            coarse_segments: Coarse segments from Silero VAD
            onset: Onset threshold for speech detection
            offset: Offset threshold for speech detection
            min_duration_on: Minimum duration of speech segments
            min_duration_off: Minimum duration of silence between segments
            
        Returns:
            List of refined speech segments
        """
        if self.pipeline is None:
            if not self.load_model():
                raise RuntimeError("Failed to load Pyannote VAD pipeline")
        
        if self.logger:
            self.logger.info(f"Refining {len(coarse_segments)} coarse segments")
            self.logger.debug(f"Processing audio: {audio_path}")
        
        try:
            # Configure pipeline parameters
            self.pipeline.instantiate({
                "onset": onset,
                "offset": offset,
                "min_duration_on": min_duration_on,
                "min_duration_off": min_duration_off,
            })
            
            # Process audio file
            vad_output = self.pipeline(str(audio_path))
            
            # Convert pyannote Timeline to our format
            refined_segments = []
            for segment in vad_output.get_timeline():
                refined_segments.append({
                    "start": float(segment.start),
                    "end": float(segment.end)
                })
            
            if self.logger:
                self.logger.info(f"Refined to {len(refined_segments)} segments")
            
            return refined_segments
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Refinement failed: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            raise
    
    def filter_by_coarse_segments(
        self,
        refined_segments: List[Dict[str, float]],
        coarse_segments: List[Dict[str, float]],
        overlap_threshold: float = 0.5
    ) -> List[Dict[str, float]]:
        """
        Filter refined segments to only keep those overlapping with coarse segments.
        
        Args:
            refined_segments: Refined segments from Pyannote
            coarse_segments: Coarse segments from Silero
            overlap_threshold: Minimum overlap ratio to keep segment
            
        Returns:
            Filtered segments
        """
        filtered = []
        
        for refined in refined_segments:
            for coarse in coarse_segments:
                # Calculate overlap
                overlap_start = max(refined['start'], coarse['start'])
                overlap_end = min(refined['end'], coarse['end'])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                refined_duration = refined['end'] - refined['start']
                if refined_duration > 0:
                    overlap_ratio = overlap_duration / refined_duration
                    
                    if overlap_ratio >= overlap_threshold:
                        filtered.append(refined)
                        break
        
        if self.logger:
            removed = len(refined_segments) - len(filtered)
            if removed > 0:
                self.logger.debug(f"Filtered {removed} segments outside coarse boundaries")
        
        return filtered
    
    def calculate_statistics(
        self,
        segments: List[Dict[str, float]],
        total_duration: float
    ) -> Dict:
        """
        Calculate statistics for refined segments.
        
        Args:
            segments: Refined segments
            total_duration: Total audio duration
            
        Returns:
            Statistics dictionary
        """
        if not segments:
            return {
                'total_duration': total_duration,
                'num_segments': 0,
                'speech_duration': 0.0,
                'speech_ratio': 0.0
            }
        
        speech_duration = sum(seg['end'] - seg['start'] for seg in segments)
        speech_ratio = speech_duration / total_duration if total_duration > 0 else 0.0
        
        return {
            'total_duration': total_duration,
            'num_segments': len(segments),
            'speech_duration': speech_duration,
            'speech_ratio': speech_ratio,
            'avg_segment_duration': speech_duration / len(segments) if segments else 0.0
        }
    
    def process(
        self,
        audio_path: Path,
        coarse_segments: List[Dict[str, float]],
        total_duration: float,
        onset: float = 0.5,
        offset: float = 0.5,
        min_duration_on: float = 0.0,
        min_duration_off: float = 0.0,
        filter_by_coarse: bool = True
    ) -> Tuple[List[Dict[str, float]], Dict]:
        """
        Full Pyannote VAD refinement pipeline.
        
        Args:
            audio_path: Path to audio file
            coarse_segments: Coarse segments from Silero VAD
            total_duration: Total audio duration
            onset: Speech onset threshold
            offset: Speech offset threshold
            min_duration_on: Minimum speech duration
            min_duration_off: Minimum silence duration
            filter_by_coarse: Whether to filter by coarse segment boundaries
            
        Returns:
            Tuple of (refined_segments, statistics)
        """
        # Refine segments
        refined_segments = self.refine_segments(
            audio_path=audio_path,
            coarse_segments=coarse_segments,
            onset=onset,
            offset=offset,
            min_duration_on=min_duration_on,
            min_duration_off=min_duration_off
        )
        
        # Optionally filter by coarse segments
        if filter_by_coarse and coarse_segments:
            refined_segments = self.filter_by_coarse_segments(
                refined_segments,
                coarse_segments
            )
        
        # Calculate statistics
        stats = self.calculate_statistics(refined_segments, total_duration)
        
        # Add configuration to stats
        stats['onset'] = onset
        stats['offset'] = offset
        stats['min_duration_on'] = min_duration_on
        stats['min_duration_off'] = min_duration_off
        stats['device'] = str(self.device)
        stats['filtered_by_coarse'] = filter_by_coarse
        
        if self.logger:
            self.logger.info(f"Refinement complete: {len(refined_segments)} segments")
            self.logger.info(f"Speech ratio: {stats['speech_ratio']:.1%}")
        
        return refined_segments, stats


def load_secrets(secrets_path: Path = None) -> Dict:
    """
    Load secrets from config/secrets.json.
    
    Args:
        secrets_path: Optional path to secrets file
        
    Returns:
        Dictionary of secrets
    """
    if secrets_path is None:
        secrets_path = Path("config/secrets.json")
    
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")
    
    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
    
    return secrets
