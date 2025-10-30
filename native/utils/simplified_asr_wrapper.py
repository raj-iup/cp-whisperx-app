"""
Simplified ASR wrapper using faster-whisper directly.
Provides speech-to-text transcription without the WhisperX dependency issues.
"""
import json
import gc
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class SimplifiedASR:
    """
    Simplified ASR using faster-whisper.
    
    Provides transcription without word-level alignment but avoids
    dependency conflicts.
    """
    
    def __init__(
        self,
        model_name: str = "base",
        device: str = "cpu",
        compute_type: str = "float32",
        language: str = None,
        logger=None
    ):
        """
        Initialize Simplified ASR.
        
        Args:
            model_name: Whisper model size
            device: Device to run on
            compute_type: Computation precision
            language: Language code
            logger: Logger instance
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.logger = logger
        self.model = None
        
    def load_model(self):
        """Load faster-whisper model."""
        if self.logger:
            self.logger.info(f"Loading faster-whisper model: {self.model_name} on {self.device}")
        
        try:
            from faster_whisper import WhisperModel
            
            # faster-whisper uses 'cuda' or 'cpu', not 'mps'
            device_str = "cpu" if self.device in ["mps", "cpu"] else self.device
            
            self.model = WhisperModel(
                self.model_name,
                device=device_str,
                compute_type=self.compute_type
            )
            
            if self.logger:
                self.logger.info("✓ Faster-whisper model loaded successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load faster-whisper model: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return False
    
    def transcribe(
        self,
        audio_path: Path,
        batch_size: int = 16
    ) -> Dict:
        """
        Transcribe audio file.
        
        Args:
            audio_path: Path to audio file
            batch_size: Batch size for inference
            
        Returns:
            Transcription result dictionary
        """
        if self.model is None:
            if not self.load_model():
                raise RuntimeError("Failed to load faster-whisper model")
        
        if self.logger:
            self.logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            # Transcribe
            segments, info = self.model.transcribe(
                str(audio_path),
                language=self.language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Convert to our format
            result_segments = []
            for segment in segments:
                result_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text,
                    "id": segment.id
                })
            
            result = {
                "segments": result_segments,
                "language": info.language,
                "language_probability": info.language_probability
            }
            
            if self.logger:
                self.logger.info(f"Language detected: {info.language} (prob: {info.language_probability:.2f})")
                self.logger.info(f"Generated {len(result_segments)} segments")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Transcription failed: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            raise
    
    def assign_speakers(
        self,
        result: Dict,
        speaker_segments: List[Dict]
    ) -> Dict:
        """
        Assign speakers to transcribed segments.
        
        Args:
            result: Transcription result
            speaker_segments: Speaker segments from diarization
            
        Returns:
            Transcription with speaker labels
        """
        if self.logger:
            self.logger.info("Assigning speakers to transcription segments...")
        
        segments = result.get("segments", [])
        
        for segment in segments:
            seg_start = segment.get("start", 0)
            seg_end = segment.get("end", 0)
            
            # Find best matching speaker segment
            best_speaker = None
            best_overlap = 0.0
            
            for speaker_seg in speaker_segments:
                # Calculate overlap
                overlap_start = max(seg_start, speaker_seg["start"])
                overlap_end = min(seg_end, speaker_seg["end"])
                overlap_duration = max(0, overlap_end - overlap_start)
                
                seg_duration = seg_end - seg_start
                if seg_duration > 0:
                    overlap_ratio = overlap_duration / seg_duration
                    
                    if overlap_ratio > best_overlap:
                        best_overlap = overlap_ratio
                        best_speaker = speaker_seg["speaker"]
            
            # Assign speaker
            if best_speaker and best_overlap >= 0.3:
                segment["speaker"] = best_speaker
            else:
                segment["speaker"] = "UNKNOWN"
        
        if self.logger:
            speakers_assigned = sum(1 for seg in segments if seg.get("speaker") != "UNKNOWN")
            self.logger.info(f"Assigned speakers to {speakers_assigned}/{len(segments)} segments")
        
        return result
    
    def calculate_statistics(
        self,
        result: Dict
    ) -> Dict:
        """Calculate transcription statistics."""
        segments = result.get("segments", [])
        
        total_words = 0
        total_chars = 0
        speakers = set()
        
        for segment in segments:
            text = segment.get("text", "")
            total_chars += len(text)
            total_words += len(text.split())
            
            if "speaker" in segment:
                speakers.add(segment["speaker"])
        
        return {
            "num_segments": len(segments),
            "total_words": total_words,
            "total_characters": total_chars,
            "num_speakers": len(speakers),
            "language": result.get("language", "unknown"),
            "has_alignment": False,  # Simplified version doesn't have word-level alignment
            "has_speakers": any("speaker" in seg for seg in segments)
        }
    
    def process(
        self,
        audio_path: Path,
        speaker_segments: Optional[List[Dict]] = None,
        batch_size: int = 16
    ) -> Tuple[Dict, Dict]:
        """
        Full ASR pipeline.
        
        Args:
            audio_path: Path to audio file
            speaker_segments: Optional speaker segments
            batch_size: Batch size for inference
            
        Returns:
            Tuple of (transcription_result, statistics)
        """
        # Transcribe
        result = self.transcribe(
            audio_path=audio_path,
            batch_size=batch_size
        )
        
        # Assign speakers
        if speaker_segments:
            result = self.assign_speakers(result, speaker_segments)
        
        # Calculate statistics
        stats = self.calculate_statistics(result)
        
        # Add configuration
        stats["model_name"] = self.model_name
        stats["device"] = self.device
        stats["compute_type"] = self.compute_type
        stats["method"] = "faster-whisper"
        
        if self.logger:
            self.logger.info(f"Transcription complete:")
            self.logger.info(f"  Segments: {stats['num_segments']}")
            self.logger.info(f"  Words: {stats['total_words']}")
            self.logger.info(f"  Language: {stats['language']}")
            self.logger.info(f"  Speakers: {stats['has_speakers']}")
        
        return result, stats
    
    def cleanup(self):
        """Cleanup model to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
        
        gc.collect()


def load_secrets(secrets_path: Path = None) -> Dict:
    """Load secrets from config/secrets.json."""
    if secrets_path is None:
        secrets_path = Path("config/secrets.json")
    
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")
    
    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
    
    return secrets
