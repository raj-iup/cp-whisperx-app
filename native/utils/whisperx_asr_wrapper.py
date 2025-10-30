"""
WhisperX ASR wrapper for native MPS pipeline.
Provides speech-to-text transcription with forced alignment using WhisperX.
"""
import torch
import json
import gc
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class WhisperXASR:
    """
    WhisperX Automatic Speech Recognition wrapper.
    
    Uses WhisperX for transcription and word-level forced alignment.
    """
    
    def __init__(
        self,
        model_name: str = "large-v2",
        device: str = "cpu",
        compute_type: str = "float32",
        language: str = None,
        logger=None
    ):
        """
        Initialize WhisperX ASR.
        
        Args:
            model_name: Whisper model size (tiny, base, small, medium, large-v2, large-v3)
            device: Device to run on (cpu, cuda, mps)
            compute_type: Computation precision (float16, float32, int8)
            language: Language code (None for auto-detection)
            logger: Logger instance
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.language = language
        self.logger = logger
        self.model = None
        self.align_model = None
        self.align_metadata = None
        
    def load_model(self):
        """Load WhisperX model."""
        if self.logger:
            self.logger.info(f"Loading WhisperX model: {self.model_name} on {self.device}")
        
        try:
            import whisperx
            
            # Adjust device for MPS
            device_str = self.device
            if self.device == "mps":
                if self.logger:
                    self.logger.warning("MPS may have limited support, consider using CPU for stability")
                # WhisperX/faster-whisper doesn't support MPS directly, use CPU
                device_str = "cpu"
            
            # Load Whisper model
            self.model = whisperx.load_model(
                self.model_name,
                device=device_str,
                compute_type=self.compute_type,
                language=self.language
            )
            
            if self.logger:
                self.logger.info("✓ WhisperX model loaded successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load WhisperX model: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return False
    
    def load_align_model(self, language_code: str):
        """
        Load alignment model for forced alignment.
        
        Args:
            language_code: Language code for alignment model
        """
        if self.logger:
            self.logger.info(f"Loading alignment model for language: {language_code}")
        
        try:
            import whisperx
            
            device_str = "cpu" if self.device == "mps" else self.device
            
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code=language_code,
                device=device_str
            )
            
            if self.logger:
                self.logger.info("✓ Alignment model loaded successfully")
            
            return True
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load alignment model: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return False
    
    def transcribe(
        self,
        audio_path: Path,
        batch_size: int = 16,
        vad_segments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Transcribe audio file.
        
        Args:
            audio_path: Path to audio file
            batch_size: Batch size for inference
            vad_segments: Optional VAD segments to guide transcription
            
        Returns:
            Transcription result dictionary
        """
        if self.model is None:
            if not self.load_model():
                raise RuntimeError("Failed to load WhisperX model")
        
        if self.logger:
            self.logger.info(f"Transcribing audio: {audio_path}")
            self.logger.info(f"Batch size: {batch_size}")
        
        try:
            import whisperx
            
            # Load audio
            audio = whisperx.load_audio(str(audio_path))
            
            # Transcribe
            result = self.model.transcribe(
                audio,
                batch_size=batch_size,
                language=self.language
            )
            
            # Detect language if not specified
            detected_language = result.get('language', self.language)
            
            if self.logger:
                self.logger.info(f"Language detected: {detected_language}")
                self.logger.info(f"Generated {len(result.get('segments', []))} segments")
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Transcription failed: {e}")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            raise
    
    def align(
        self,
        transcript_result: Dict,
        audio_path: Path
    ) -> Dict:
        """
        Perform forced alignment on transcript.
        
        Args:
            transcript_result: Transcription result from transcribe()
            audio_path: Path to audio file
            
        Returns:
            Aligned result with word-level timestamps
        """
        language_code = transcript_result.get('language', 'en')
        
        # Load alignment model if not loaded
        if self.align_model is None:
            if not self.load_align_model(language_code):
                if self.logger:
                    self.logger.warning("Alignment model failed to load, skipping alignment")
                return transcript_result
        
        if self.logger:
            self.logger.info("Performing forced alignment...")
        
        try:
            import whisperx
            
            # Load audio
            audio = whisperx.load_audio(str(audio_path))
            
            # Align
            result_aligned = whisperx.align(
                transcript_result["segments"],
                self.align_model,
                self.align_metadata,
                audio,
                device="cpu" if self.device == "mps" else self.device,
                return_char_alignments=False
            )
            
            if self.logger:
                aligned_count = sum(1 for seg in result_aligned["segments"] if "words" in seg)
                self.logger.info(f"Aligned {aligned_count} segments with word-level timestamps")
            
            return result_aligned
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Alignment failed: {e}")
                self.logger.warning("Continuing without alignment")
            import traceback
            if self.logger:
                self.logger.debug(traceback.format_exc())
            return transcript_result
    
    def assign_speakers(
        self,
        aligned_result: Dict,
        speaker_segments: List[Dict]
    ) -> Dict:
        """
        Assign speakers to transcribed segments.
        
        Args:
            aligned_result: Aligned transcription result
            speaker_segments: Speaker segments from diarization
            
        Returns:
            Transcription with speaker labels
        """
        if self.logger:
            self.logger.info("Assigning speakers to transcription segments...")
        
        segments = aligned_result.get("segments", [])
        
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
            if best_speaker:
                segment["speaker"] = best_speaker
            else:
                segment["speaker"] = "UNKNOWN"
        
        if self.logger:
            speakers_assigned = sum(1 for seg in segments if seg.get("speaker") != "UNKNOWN")
            self.logger.info(f"Assigned speakers to {speakers_assigned}/{len(segments)} segments")
        
        return aligned_result
    
    def calculate_statistics(
        self,
        result: Dict
    ) -> Dict:
        """
        Calculate transcription statistics.
        
        Args:
            result: Transcription result
            
        Returns:
            Statistics dictionary
        """
        segments = result.get("segments", [])
        
        total_words = 0
        total_chars = 0
        speakers = set()
        
        for segment in segments:
            text = segment.get("text", "")
            total_chars += len(text)
            
            if "words" in segment:
                total_words += len(segment["words"])
            else:
                # Estimate word count
                total_words += len(text.split())
            
            if "speaker" in segment:
                speakers.add(segment["speaker"])
        
        return {
            "num_segments": len(segments),
            "total_words": total_words,
            "total_characters": total_chars,
            "num_speakers": len(speakers),
            "language": result.get("language", "unknown"),
            "has_alignment": any("words" in seg for seg in segments),
            "has_speakers": any("speaker" in seg for seg in segments)
        }
    
    def process(
        self,
        audio_path: Path,
        speaker_segments: Optional[List[Dict]] = None,
        batch_size: int = 16,
        perform_alignment: bool = True
    ) -> Tuple[Dict, Dict]:
        """
        Full WhisperX ASR pipeline.
        
        Args:
            audio_path: Path to audio file
            speaker_segments: Optional speaker segments for speaker assignment
            batch_size: Batch size for inference
            perform_alignment: Whether to perform forced alignment
            
        Returns:
            Tuple of (transcription_result, statistics)
        """
        # Transcribe
        result = self.transcribe(
            audio_path=audio_path,
            batch_size=batch_size
        )
        
        # Align
        if perform_alignment:
            result = self.align(result, audio_path)
        
        # Assign speakers
        if speaker_segments:
            result = self.assign_speakers(result, speaker_segments)
        
        # Calculate statistics
        stats = self.calculate_statistics(result)
        
        # Add configuration
        stats["model_name"] = self.model_name
        stats["device"] = self.device
        stats["compute_type"] = self.compute_type
        stats["alignment_performed"] = perform_alignment
        
        if self.logger:
            self.logger.info(f"Transcription complete:")
            self.logger.info(f"  Segments: {stats['num_segments']}")
            self.logger.info(f"  Words: {stats['total_words']}")
            self.logger.info(f"  Language: {stats['language']}")
            self.logger.info(f"  Alignment: {stats['has_alignment']}")
            self.logger.info(f"  Speakers: {stats['has_speakers']}")
        
        return result, stats
    
    def cleanup(self):
        """Cleanup models to free memory."""
        if self.model is not None:
            del self.model
            self.model = None
        
        if self.align_model is not None:
            del self.align_model
            self.align_model = None
        
        if self.align_metadata is not None:
            del self.align_metadata
            self.align_metadata = None
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


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
