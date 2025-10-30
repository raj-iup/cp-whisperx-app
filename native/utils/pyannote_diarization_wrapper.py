"""
Pyannote Diarization wrapper for native MPS pipeline.
Provides speaker diarization using Pyannote.audio speaker diarization pipeline.
"""
import torch
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class PyannoteDiarization:
    """
    Pyannote Speaker Diarization wrapper.
    
    Uses pyannote.audio's speaker-diarization pipeline to identify
    and label different speakers in the audio.
    """
    
    def __init__(self, hf_token: str, device: str = "cpu", logger=None):
        """
        Initialize Pyannote Diarization.
        
        Args:
            hf_token: HuggingFace API token for model access
            device: Device to run on (cpu, cuda, mps)
            logger: Logger instance
        """
        self.hf_token = hf_token
        self.device = device
        self.logger = logger
        self.pipeline = None
        
    def load_model(self):
        """Load Pyannote diarization pipeline from HuggingFace."""
        if self.logger:
            self.logger.info(f"Loading Pyannote diarization pipeline on {self.device}")
        
        try:
            from pyannote.audio import Pipeline
            
            # Load the speaker diarization pipeline
            # This will download models from HuggingFace if not cached
            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=self.hf_token
            )
            
            # Move to device (prefer CPU for stability with pyannote)
            device_str = self.device
            if self.device == "mps":
                if self.logger:
                    self.logger.warning("MPS not fully supported by Pyannote, using CPU for stability")
                device_str = "cpu"
            
            # Set device
            if device_str != "cpu":
                self.pipeline = self.pipeline.to(torch.device(device_str))
            
            if self.logger:
                self.logger.info("✓ Pyannote diarization pipeline loaded successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load Pyannote diarization pipeline: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return False
    
    def diarize(
        self,
        audio_path: Path,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> List[Dict]:
        """
        Perform speaker diarization on audio file.
        
        Args:
            audio_path: Path to audio file
            num_speakers: Exact number of speakers (if known)
            min_speakers: Minimum number of speakers
            max_speakers: Maximum number of speakers
            
        Returns:
            List of speaker segments with labels
        """
        if self.pipeline is None:
            if not self.load_model():
                raise RuntimeError("Failed to load Pyannote diarization pipeline")
        
        if self.logger:
            self.logger.info(f"Running diarization on: {audio_path}")
            if num_speakers:
                self.logger.info(f"Expected speakers: {num_speakers}")
            elif min_speakers or max_speakers:
                self.logger.info(f"Speaker range: {min_speakers or 1} - {max_speakers or 'unlimited'}")
        
        try:
            # Prepare parameters
            params = {}
            if num_speakers:
                params['num_speakers'] = num_speakers
            else:
                if min_speakers:
                    params['min_speakers'] = min_speakers
                if max_speakers:
                    params['max_speakers'] = max_speakers
            
            # Run diarization
            diarization = self.pipeline(str(audio_path), **params)
            
            # Convert to our format
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": float(turn.start),
                    "end": float(turn.end),
                    "speaker": str(speaker),
                    "duration": float(turn.end - turn.start)
                })
            
            if self.logger:
                unique_speakers = len(set(seg['speaker'] for seg in segments))
                self.logger.info(f"Detected {unique_speakers} unique speakers")
                self.logger.info(f"Generated {len(segments)} speaker segments")
            
            return segments
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Diarization failed: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            raise
    
    def merge_with_vad(
        self,
        diarization_segments: List[Dict],
        vad_segments: List[Dict],
        overlap_threshold: float = 0.5
    ) -> List[Dict]:
        """
        Merge diarization results with VAD segments.
        
        Args:
            diarization_segments: Speaker segments from diarization
            vad_segments: Speech segments from VAD
            overlap_threshold: Minimum overlap ratio to merge
            
        Returns:
            Merged segments with speaker labels
        """
        merged = []
        
        for vad_seg in vad_segments:
            vad_start = vad_seg['start']
            vad_end = vad_seg['end']
            vad_duration = vad_end - vad_start
            
            # Find overlapping diarization segments
            best_speaker = None
            best_overlap = 0.0
            
            for diar_seg in diarization_segments:
                # Calculate overlap
                overlap_start = max(vad_start, diar_seg['start'])
                overlap_end = min(vad_end, diar_seg['end'])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                if vad_duration > 0:
                    overlap_ratio = overlap_duration / vad_duration
                    
                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_speaker = diar_seg['speaker']
            
            # Add segment if it has sufficient overlap
            if best_speaker and best_overlap >= overlap_threshold:
                merged.append({
                    'start': vad_start,
                    'end': vad_end,
                    'speaker': best_speaker,
                    'duration': vad_duration,
                    'overlap_ratio': best_overlap
                })
        
        if self.logger:
            assigned = len(merged)
            total = len(vad_segments)
            self.logger.debug(f"Assigned speakers to {assigned}/{total} VAD segments")
        
        return merged
    
    def calculate_statistics(
        self,
        segments: List[Dict],
        total_duration: float
    ) -> Dict:
        """
        Calculate diarization statistics.
        
        Args:
            segments: Speaker segments
            total_duration: Total audio duration
            
        Returns:
            Statistics dictionary
        """
        if not segments:
            return {
                'total_duration': total_duration,
                'num_segments': 0,
                'num_speakers': 0,
                'speaker_stats': {}
            }
        
        # Count speakers
        speakers = {}
        for seg in segments:
            speaker = seg['speaker']
            if speaker not in speakers:
                speakers[speaker] = {
                    'segments': 0,
                    'duration': 0.0,
                    'ratio': 0.0
                }
            speakers[speaker]['segments'] += 1
            speakers[speaker]['duration'] += seg['duration']
        
        # Calculate ratios
        for speaker in speakers:
            speakers[speaker]['ratio'] = speakers[speaker]['duration'] / total_duration
        
        return {
            'total_duration': total_duration,
            'num_segments': len(segments),
            'num_speakers': len(speakers),
            'speaker_stats': speakers
        }
    
    def process(
        self,
        audio_path: Path,
        vad_segments: List[Dict],
        total_duration: float,
        num_speakers: Optional[int] = None,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None,
        merge_with_vad_enabled: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Full diarization pipeline.
        
        Args:
            audio_path: Path to audio file
            vad_segments: Speech segments from VAD
            total_duration: Total audio duration
            num_speakers: Exact number of speakers
            min_speakers: Minimum speakers
            max_speakers: Maximum speakers
            merge_with_vad_enabled: Whether to merge with VAD segments
            
        Returns:
            Tuple of (speaker_segments, statistics)
        """
        # Run diarization
        diar_segments = self.diarize(
            audio_path=audio_path,
            num_speakers=num_speakers,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        
        # Optionally merge with VAD
        if merge_with_vad_enabled and vad_segments:
            final_segments = self.merge_with_vad(diar_segments, vad_segments)
            if self.logger:
                self.logger.info(f"Merged diarization with VAD: {len(diar_segments)} → {len(final_segments)} segments")
        else:
            final_segments = diar_segments
        
        # Calculate statistics
        stats = self.calculate_statistics(final_segments, total_duration)
        
        # Add configuration
        stats['num_speakers_param'] = num_speakers
        stats['min_speakers_param'] = min_speakers
        stats['max_speakers_param'] = max_speakers
        stats['device'] = str(self.device)
        stats['merged_with_vad'] = merge_with_vad_enabled
        
        if self.logger:
            self.logger.info(f"Diarization complete: {stats['num_speakers']} speakers, {len(final_segments)} segments")
        
        return final_segments, stats


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
