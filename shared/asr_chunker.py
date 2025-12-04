#!/usr/bin/env python3
"""
ASR Chunker - Large Audio File Processing with Checkpointing

Handles processing of large audio files (>1 hour) by:
- Splitting into manageable chunks (default: 5 minutes)
- Checkpointing progress for resume capability
- Aggregating results with correct timestamps
- Memory-efficient processing

Part of Phase 5: Advanced Features (Reliability & Performance)
See: docs/ARCHITECTURE_IMPLEMENTATION_ROADMAP.md § Phase 5

Module: shared/asr_chunker.py
Status: ✅ Implemented for large file processing
"""

# Standard library
import json
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple

# Local
from shared.logger import get_logger

logger = get_logger(__name__)


class ChunkedASRProcessor:
    """
    Processor for handling large audio files in chunks.
    
    Features:
    - Audio file chunking with overlap
    - Progress checkpointing for resume
    - Result aggregation with timestamp adjustment
    - Memory-efficient processing
    
    Example:
        >>> chunker = ChunkedASRProcessor(logger, chunk_duration=300.0)
        >>> chunks = chunker.create_chunks(audio_file, output_dir)
        >>> # Process each chunk...
        >>> results = chunker.aggregate_results(chunk_results)
    """
    
    def __init__(
        self,
        logger_instance: Optional[Any] = None,
        chunk_duration: float = 300.0,  # 5 minutes
        overlap_duration: float = 1.0    # 1 second overlap
    ):
        """
        Initialize chunked ASR processor.
        
        Args:
            logger_instance: Logger for output
            chunk_duration: Duration of each chunk in seconds
            overlap_duration: Overlap between chunks in seconds
        """
        self.logger = logger_instance or logger
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.chunks: List[Dict[str, Any]] = []
    
    def create_chunks(
        self,
        audio_file: Path,
        output_dir: Path
    ) -> List[Dict[str, Any]]:
        """
        Create audio chunks from a large file.
        
        Args:
            audio_file: Path to input audio file
            output_dir: Directory for chunk outputs
            
        Returns:
            List of chunk metadata dicts with:
            - index: int - Chunk index
            - file: Path - Chunk file path
            - start_time: float - Start time in original audio
            - end_time: float - End time in original audio
            - duration: float - Chunk duration
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            ImportError: If librosa/soundfile not installed
        """
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        try:
            import librosa
            import soundfile as sf
            
            # Load audio
            self.logger.info(f"Loading audio: {audio_file}")
            audio, sr = librosa.load(str(audio_file), sr=None, mono=True)
            duration = len(audio) / sr
            
            self.logger.info(f"Audio duration: {duration:.1f}s")
            self.logger.info(f"Chunk duration: {self.chunk_duration}s")
            self.logger.info(f"Overlap: {self.overlap_duration}s")
            
            # Calculate chunk parameters
            chunks = []
            chunk_samples = int(self.chunk_duration * sr)
            overlap_samples = int(self.overlap_duration * sr)
            step_samples = chunk_samples - overlap_samples
            
            num_chunks = max(1, int((len(audio) - overlap_samples) / step_samples) + 1)
            
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for i in range(num_chunks):
                start_sample = i * step_samples
                end_sample = min(start_sample + chunk_samples, len(audio))
                
                if start_sample >= len(audio):
                    break
                
                chunk_audio = audio[start_sample:end_sample]
                chunk_file = output_dir / f"chunk_{i:03d}.wav"
                
                # Save chunk
                sf.write(str(chunk_file), chunk_audio, sr)
                
                chunk_info = {
                    "index": i,
                    "file": chunk_file,
                    "start_time": start_sample / sr,
                    "end_time": end_sample / sr,
                    "duration": len(chunk_audio) / sr,
                    "sample_rate": sr,
                    "has_overlap": i > 0  # First chunk has no overlap
                }
                chunks.append(chunk_info)
                
                self.logger.debug(
                    f"Created chunk {i}: "
                    f"{chunk_info['start_time']:.1f}s - {chunk_info['end_time']:.1f}s "
                    f"({chunk_info['duration']:.1f}s)"
                )
            
            self.chunks = chunks
            self.logger.info(f"Created {len(chunks)} chunks")
            
            return chunks
            
        except ImportError as e:
            self.logger.error(
                f"Chunking requires librosa and soundfile: {e}",
                exc_info=True
            )
            raise ImportError(
                "Install librosa and soundfile: pip install librosa soundfile"
            )
        except Exception as e:
            self.logger.error(f"Failed to create chunks: {e}", exc_info=True)
            raise
    
    def save_checkpoint(
        self,
        checkpoint_file: Path,
        processed_chunks: List[int],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Save processing checkpoint.
        
        Args:
            checkpoint_file: Path to checkpoint file
            processed_chunks: List of processed chunk indices
            metadata: Optional additional metadata
        """
        checkpoint_data = {
            "version": "1.0",
            "processed_chunks": processed_chunks,
            "total_chunks": len(self.chunks),
            "chunk_duration": self.chunk_duration,
            "overlap_duration": self.overlap_duration,
            "metadata": metadata or {}
        }
        
        checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            self.logger.info(
                f"Checkpoint saved: {len(processed_chunks)}/{len(self.chunks)} chunks"
            )
        except Exception as e:
            self.logger.error(f"Failed to save checkpoint: {e}", exc_info=True)
            raise
    
    def load_checkpoint(self, checkpoint_file: Path) -> Tuple[List[int], Dict[str, Any]]:
        """
        Load processing checkpoint.
        
        Args:
            checkpoint_file: Path to checkpoint file
            
        Returns:
            Tuple of (processed_chunks, metadata)
        """
        if not checkpoint_file.exists():
            return [], {}
        
        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            processed = checkpoint_data.get("processed_chunks", [])
            metadata = checkpoint_data.get("metadata", {})
            
            self.logger.info(
                f"Checkpoint loaded: {len(processed)} chunks already processed"
            )
            
            return processed, metadata
            
        except Exception as e:
            self.logger.warning(f"Failed to load checkpoint: {e}")
            return [], {}
    
    def aggregate_results(
        self,
        chunk_results: List[Dict[str, Any]],
        remove_overlap_duplicates: bool = True
    ) -> Dict[str, Any]:
        """
        Aggregate results from multiple chunks.
        
        Adjusts timestamps to match original audio and optionally
        removes duplicate segments from overlap regions.
        
        Args:
            chunk_results: List of results from each chunk
            remove_overlap_duplicates: Remove duplicate segments in overlap
            
        Returns:
            Aggregated result dictionary with:
            - segments: List of all segments
            - language: Detected language
            - word_segments: List of all word-level segments
        """
        aggregated = {
            "segments": [],
            "language": None,
            "word_segments": []
        }
        
        for chunk_idx, chunk_result in enumerate(chunk_results):
            if not chunk_result:
                self.logger.warning(f"Chunk {chunk_idx} has no results")
                continue
            
            if chunk_idx >= len(self.chunks):
                self.logger.warning(f"Chunk {chunk_idx} not in metadata")
                continue
            
            # Get chunk time offset
            chunk_info = self.chunks[chunk_idx]
            time_offset = chunk_info["start_time"]
            
            # Set language from first chunk
            if aggregated["language"] is None and "language" in chunk_result:
                aggregated["language"] = chunk_result["language"]
            
            # Process segments
            if "segments" in chunk_result:
                for segment in chunk_result["segments"]:
                    adjusted_segment = segment.copy()
                    adjusted_segment["start"] += time_offset
                    adjusted_segment["end"] += time_offset
                    
                    # Skip if in overlap region and duplicate
                    if remove_overlap_duplicates and chunk_info.get("has_overlap"):
                        # Check if this segment is in overlap region
                        if segment["start"] < self.overlap_duration:
                            # Check if already added from previous chunk
                            if self._is_duplicate_segment(
                                adjusted_segment,
                                aggregated["segments"]
                            ):
                                continue
                    
                    # Adjust word timestamps if present
                    if "words" in adjusted_segment:
                        adjusted_segment["words"] = [
                            {
                                **word,
                                "start": word["start"] + time_offset,
                                "end": word["end"] + time_offset
                            }
                            for word in adjusted_segment["words"]
                        ]
                    
                    aggregated["segments"].append(adjusted_segment)
            
            # Process word segments
            if "word_segments" in chunk_result:
                for word in chunk_result["word_segments"]:
                    adjusted_word = word.copy()
                    adjusted_word["start"] += time_offset
                    adjusted_word["end"] += time_offset
                    aggregated["word_segments"].append(adjusted_word)
        
        self.logger.info(
            f"Aggregated {len(chunk_results)} chunks into "
            f"{len(aggregated['segments'])} segments"
        )
        
        return aggregated
    
    def _is_duplicate_segment(
        self,
        segment: Dict[str, Any],
        existing_segments: List[Dict[str, Any]],
        threshold: float = 0.5
    ) -> bool:
        """
        Check if segment is duplicate of existing segment.
        
        Args:
            segment: Segment to check
            existing_segments: List of existing segments
            threshold: Time overlap threshold (seconds)
            
        Returns:
            True if duplicate found
        """
        for existing in existing_segments[-5:]:  # Check last 5 segments
            # Check time overlap
            overlap = min(segment["end"], existing["end"]) - max(segment["start"], existing["start"])
            
            if overlap > threshold:
                # Check text similarity
                if segment.get("text", "").strip() == existing.get("text", "").strip():
                    return True
        
        return False
    
    def cleanup_chunks(self, output_dir: Path) -> None:
        """
        Clean up temporary chunk files.
        
        Args:
            output_dir: Directory containing chunk files
        """
        try:
            for chunk_info in self.chunks:
                chunk_file = chunk_info["file"]
                if chunk_file.exists():
                    chunk_file.unlink()
            
            self.logger.info(f"Cleaned up {len(self.chunks)} chunk files")
            
        except Exception as e:
            self.logger.warning(f"Failed to cleanup chunks: {e}")
