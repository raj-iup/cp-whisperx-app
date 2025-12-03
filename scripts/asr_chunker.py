#!/usr/bin/env python3
"""
Chunked ASR Processing for MPS Stability and Bias Injection

This module handles:
1. Splitting audio into manageable chunks (5-10 min)
2. Aligning chunks with bias windows
3. Processing each chunk with appropriate bias prompts
4. Merging results with proper timestamps
5. Checkpoint/resume functionality

Used by whisperx_integration.py for stable MPS processing on long files.
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Use lightweight audio loader with lazy loading support
from shared.audio_utils import load_audio, load_audio_segment, get_audio_duration

import numpy as np
import json
import tempfile
import soundfile as sf
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


@dataclass
class AudioChunk:
    """Represents a chunk of audio for processing"""
    chunk_id: int
    start_time: float
    end_time: float
    duration: float
    audio_data: np.ndarray
    sample_rate: int
    bias_windows: List[Any]  # List of BiasWindow objects for this chunk


class ChunkedASRProcessor:
    """
    Process audio in chunks for MPS stability and bias injection.
    
    Key features:
    - Splits long audio into chunks (default 300s = 5min)
    - Aligns chunks with bias windows
    - Applies window-specific bias prompts
    - Saves checkpoints for resume capability
    - Merges results with proper timestamps
    """
    
    def __init__(self, logger: logging.Logger, chunk_duration: int = 300, use_lazy_loading: bool = True):
        """
        Args:
            logger: Logger instance
            chunk_duration: Chunk size in seconds (default 300 = 5min)
            use_lazy_loading: Use lazy loading for memory efficiency (default True)
                            When True: Loads only required audio segments (99.6% memory reduction)
                            When False: Loads full audio (legacy behavior)
        """
        self.logger = logger
        self.chunk_duration = chunk_duration
        self.use_lazy_loading = use_lazy_loading
        
    def create_chunks(
        self,
        audio_file: str,
        bias_windows: Optional[List] = None
    ) -> List[AudioChunk]:
        """
        Split audio into processable chunks.
        
        Args:
            audio_file: Path to audio file
            bias_windows: Optional list of BiasWindow objects
            
        Returns:
            List of AudioChunk objects
        """
        self.logger.info(f"Creating audio chunks (chunk_duration={self.chunk_duration}s)...")
        
        if self.use_lazy_loading:
            # Get duration without loading full audio
            from shared.audio_utils import get_audio_duration
            duration = get_audio_duration(audio_file)
            self.logger.info(f"  Using lazy loading (memory efficient mode)")
            self.logger.info(f"  Audio duration: {duration:.1f}s")
        else:
            # Legacy: Load full audio to get duration
            audio = load_audio(audio_file)
            sample_rate = 16000  # Whisper standard
            duration = len(audio) / sample_rate
            self.logger.info(f"  Using full audio loading (legacy mode)")
            self.logger.info(f"  Audio duration: {duration:.1f}s")
        
        chunks = []
        chunk_id = 0
        start_time = 0.0
        
        while start_time < duration:
            end_time = min(start_time + self.chunk_duration, duration)
            
            if self.use_lazy_loading:
                # Lazy loading: Load only this chunk's audio segment
                audio_data = load_audio_segment(audio_file, start_time, end_time)
                sample_rate = 16000
            else:
                # Legacy: Extract from pre-loaded audio
                start_sample = int(start_time * sample_rate)
                end_sample = int(end_time * sample_rate)
                audio_data = audio[start_sample:end_sample]
            
            # Find bias windows that overlap with this chunk
            chunk_bias_windows = []
            if bias_windows:
                chunk_bias_windows = [
                    w for w in bias_windows
                    if w.start_time < end_time and w.end_time > start_time
                ]
            
            chunk = AudioChunk(
                chunk_id=chunk_id,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                audio_data=audio_data,
                sample_rate=sample_rate,
                bias_windows=chunk_bias_windows
            )
            chunks.append(chunk)
            
            self.logger.debug(
                f"  Chunk {chunk_id}: {start_time:.1f}s - {end_time:.1f}s "
                f"({len(chunk_bias_windows)} bias windows)"
            )
            
            chunk_id += 1
            start_time = end_time
        
        self.logger.info(f"  Created {len(chunks)} chunks")
        if self.use_lazy_loading:
            memory_per_chunk = len(chunks[0].audio_data) * 4 / 1024 / 1024 if chunks else 0  # MB
            self.logger.info(f"  Memory per chunk: {memory_per_chunk:.1f} MB (lazy loading enabled)")
        return chunks
    
    def process_chunk_with_bias(
        self,
        chunk: AudioChunk,
        backend,
        language: str,
        task: str,
        batch_size: int
    ) -> Dict[str, Any]:
        """
        Process a single chunk with bias prompting.
        
        This method:
        1. Collects all bias terms from windows in this chunk
        2. Creates initial_prompt for bias
        3. Saves chunk audio to temp file
        4. Transcribes with bias
        5. Adjusts timestamps to global timeline
        6. Adds bias metadata to segments
        
        Args:
            chunk: AudioChunk object
            backend: WhisperX backend instance
            language: Source language code
            task: Transcription task ('transcribe' or 'translate')
            batch_size: Batch size for inference
            
        Returns:
            Transcription result dict with segments
        """
        self.logger.info(
            f"Processing chunk {chunk.chunk_id} "
            f"({chunk.start_time:.1f}s - {chunk.end_time:.1f}s)"
        )
        
        # Prepare bias prompts for this chunk
        initial_prompt = None
        
        if chunk.bias_windows:
            # Collect all unique bias terms from windows in this chunk
            all_terms = set()
            for window in chunk.bias_windows:
                all_terms.update(window.bias_terms)
            
            # Convert to list and limit to top 50 terms
            terms_list = list(all_terms)[:50]
            
            # Create initial_prompt with terms
            initial_prompt = ", ".join(terms_list)
            
            self.logger.info(f"  🎯 Bias: {len(terms_list)} unique terms")
            self.logger.debug(f"     Preview: {', '.join(terms_list[:5])}...")
        
        # Save chunk audio to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            tmp_path = tmp.name
            sf.write(tmp_path, chunk.audio_data, chunk.sample_rate)
        
        try:
            # Transcribe chunk with bias
            self.logger.debug(f"  Transcribing chunk with batch_size={batch_size}")
            
            result = backend.transcribe(
                tmp_path,
                language=language,
                task=task,
                batch_size=batch_size,
                initial_prompt=initial_prompt
            )
            
            # Adjust segment timestamps to global timeline
            segments = result.get('segments', [])
            self.logger.info(f"  ✓ Got {len(segments)} segments from chunk")
            
            for segment in segments:
                # Adjust timestamps
                segment['start'] += chunk.start_time
                segment['end'] += chunk.start_time
                
                # Add chunk metadata
                segment['chunk_id'] = chunk.chunk_id
                
                # Find exact bias window for this segment
                if chunk.bias_windows:
                    seg_start = segment['start']
                    matching_window = next(
                        (w for w in chunk.bias_windows 
                         if w.start_time <= seg_start < w.end_time),
                        None
                    )
                    if matching_window:
                        segment['bias_window_id'] = matching_window.window_id
                        segment['bias_terms'] = matching_window.bias_terms
            
            return result
            
        finally:
            # Cleanup temp file
            Path(tmp_path).unlink(missing_ok=True)
    
    def merge_chunk_results(
        self,
        chunk_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge results from all chunks into single result.
        
        Args:
            chunk_results: List of result dicts from each chunk
            
        Returns:
            Merged result dict with all segments
        """
        self.logger.info(f"Merging results from {len(chunk_results)} chunks...")
        
        if not chunk_results:
            return {'segments': [], 'language': None}
        
        merged = {
            'segments': [],
            'language': chunk_results[0].get('language') if chunk_results else None
        }
        
        # Collect all segments
        for result in chunk_results:
            merged['segments'].extend(result.get('segments', []))
        
        # Sort by start time
        merged['segments'].sort(key=lambda s: s['start'])
        
        self.logger.info(f"  Total segments: {len(merged['segments'])}")
        
        return merged
    
    def save_checkpoint(
        self,
        chunk_id: int,
        result: Dict[str, Any],
        checkpoint_dir: Path
    ):
        """
        Save chunk result as checkpoint.
        
        Args:
            chunk_id: Chunk identifier
            result: Transcription result
            checkpoint_dir: Directory to save checkpoints
        """
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        checkpoint_file = checkpoint_dir / f'chunk_{chunk_id:04d}.json'
        
        with open(checkpoint_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        self.logger.debug(f"  💾 Saved checkpoint: {checkpoint_file.name}")
    
    def load_checkpoint(
        self,
        chunk_id: int,
        checkpoint_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Load chunk result from checkpoint.
        
        Args:
            chunk_id: Chunk identifier
            checkpoint_dir: Directory containing checkpoints
            
        Returns:
            Transcription result or None if not found
        """
        checkpoint_file = checkpoint_dir / f'chunk_{chunk_id:04d}.json'
        
        if checkpoint_file.exists():
            with open(checkpoint_file) as f:
                return json.load(f)
        
        return None
