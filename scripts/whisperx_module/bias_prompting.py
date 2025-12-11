"""
bias_prompting.py - Bias prompting strategies for ASR

Handles context-aware bias prompting for improved transcription accuracy:
- Global: Fast, comprehensive coverage (all terms as initial prompt)
- Hybrid: Balanced (first window terms + Whisper's adaptation)
- Chunked Windows: Most accurate (window-specific terms per chunk)
- Chunked: Large file support with checkpointing

Extracted from whisperx_integration.py per AD-002 and AD-009.
Direct extraction with optimization (no compatibility layer).

Version: 2.0.0
"""

# Standard library
import sys
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local
from shared.logger import get_logger
from shared.config_loader import load_config


class BiasPromptingStrategy:
    """
    Manages bias prompting strategies for context-aware transcription.
    
    Provides multiple strategies optimized for different scenarios:
    - global: Best for short files (< 30min), single pass
    - hybrid: Best balance of speed/accuracy
    - chunked_windows: Best accuracy, time-aware prompts
    - chunked: Best for large files (> 30min), with checkpointing
    """
    
    def __init__(self, backend: Any, logger: Any):
        """
        Initialize bias prompting strategy manager
        
        Args:
            backend: Whisper backend instance (MLX, WhisperX, CUDA)
            logger: Logger instance
        """
        self.backend = backend
        self.logger = logger
        self.config = load_config()
    
    def transcribe_with_bias(
        self,
        audio_file: str,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any] = None,
        batch_size: int = 16,
        output_dir: Optional[Path] = None,
        bias_strategy: str = "global",
        workflow_mode: str = "subtitle-gen"
    ) -> Dict[str, Any]:
        """
        Main entry point for bias-aware transcription.
        
        This is the DIRECT implementation (AD-009 - no delegation).
        Optimized for quality and clarity.
        
        Args:
            audio_file: Path to audio/video file
            source_lang: Source language code (e.g., "hi")
            target_lang: Target language code (e.g., "en")
            bias_windows: List of bias windows for context-aware prompting
            batch_size: Batch size for inference
            output_dir: Output directory for checkpoints (required for chunked)
            bias_strategy: Strategy to use (global/hybrid/chunked_windows/chunked)
            workflow_mode: Workflow mode (transcribe/transcribe-only/translate-only/subtitle-gen)
            
        Returns:
            Transcription result with segments and word-level timestamps
        """
        self.logger.info(f"Transcribing with bias: {audio_file}")
        self.logger.info(f"  Source: {source_lang}, Target: {target_lang}")
        self.logger.info(f"  Backend: {self.backend.name}")
        self.logger.info(f"  Bias strategy: {bias_strategy}")
        
        if not self.backend:
            raise RuntimeError("Backend not initialized")
        
        # Optimize batch size for MPS (Apple Silicon)
        batch_size = self._optimize_batch_size(batch_size)
        
        # Determine task (transcribe vs translate)
        task = self._determine_task(source_lang, target_lang, workflow_mode)
        self.logger.info(f"  Task: {task}")
        
        # Get audio duration for strategy selection
        audio_duration = self._get_audio_duration(audio_file)
        self.logger.info(f"  Duration: {audio_duration:.1f}s ({audio_duration/60:.1f} min)")
        
        # Route to appropriate strategy
        if bias_strategy == "chunked_windows":
            return self._transcribe_windowed_chunks(
                audio_file, source_lang, task, bias_windows, batch_size
            )
        elif bias_strategy == "hybrid":
            return self._transcribe_hybrid(
                audio_file, source_lang, task, bias_windows, batch_size
            )
        elif bias_strategy == "chunked":
            return self._transcribe_chunked(
                audio_file, source_lang, task, bias_windows, batch_size, output_dir
            )
        else:
            # Global strategy with auto-chunking for very long files
            if audio_duration > 1800:  # > 30 minutes
                self.logger.info(f"  📦 Auto-chunking (long file)")
                return self._transcribe_chunked(
                    audio_file, source_lang, task, bias_windows, batch_size, output_dir
                )
            else:
                return self._transcribe_whole(
                    audio_file, source_lang, task, bias_windows, batch_size
                )
    
    # ─────────────────────────────────────────────────────────────────────
    # Helper Methods
    # ─────────────────────────────────────────────────────────────────────
    
    def _optimize_batch_size(self, batch_size: int) -> int:
        """Optimize batch size for MPS device"""
        if self.backend.device == "mps":
            optimized = min(batch_size, 8)  # MPS works best with smaller batches
            if optimized != batch_size:
                self.logger.info(f"  🎯 MPS optimization: batch_size {batch_size} → {optimized}")
            return optimized
        return batch_size
    
    def _determine_task(self, source_lang: str, target_lang: str, workflow_mode: str) -> str:
        """Determine transcription task (transcribe vs translate)"""
        if workflow_mode == 'transcribe-only':
            return "transcribe"
        elif workflow_mode == 'transcribe':
            # Allow translation if target differs
            return "translate" if (source_lang != target_lang and target_lang != 'auto') else "transcribe"
        else:
            return "translate" if source_lang != target_lang else "transcribe"
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """Get audio duration in seconds"""
        try:
            import librosa
            return librosa.get_duration(path=audio_file)
        except Exception:
            # Fallback: load and calculate
            try:
                from whisperx.audio import load_audio
                audio = load_audio(audio_file)
                return len(audio) / 16000  # 16kHz sample rate
            except:
                # Last resort: file size estimate
                import os
                file_size = os.path.getsize(audio_file)
                return file_size / 128000  # Very rough estimate
    
    # ─────────────────────────────────────────────────────────────────────
    # Strategy Implementations
    # ─────────────────────────────────────────────────────────────────────
    
    def _transcribe_whole(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[Any],
        batch_size: int
    ) -> Dict[str, Any]:
        """
        Global bias strategy - Fast, single-pass transcription.
        
        Best for:
        - Short to medium files (< 30 minutes)
        - CPU/MPS inference
        - When speed is priority
        
        Uses all unique bias terms as initial_prompt for comprehensive coverage.
        """
        # Create global bias prompt from all windows
        initial_prompt = None
        if bias_windows:
            all_terms = set()
            for window in bias_windows:
                all_terms.update(window.bias_terms)
            
            top_terms = list(all_terms)[:50]  # Limit to 50 terms
            if top_terms:
                initial_prompt = ", ".join(top_terms)
                self.logger.info(f"  🎯 Global bias: {len(top_terms)} terms")
                self.logger.debug(f"    Preview: {', '.join(top_terms[:5])}...")
        
        # Progress heartbeat for long transcriptions
        start_time = time.time()
        self.logger.info(f"  🎙️ Starting transcription at {time.strftime('%H:%M:%S')}...")
        
        heartbeat_active = True
        def progress_heartbeat() -> None:
            """Log progress every 60s to detect hangs"""
            while heartbeat_active:
                time.sleep(60)
                if heartbeat_active:
                    elapsed = time.time() - start_time
                    self.logger.info(f"  ⏱️  Still transcribing... {elapsed/60:.1f} min elapsed")
        
        heartbeat_thread = threading.Thread(target=progress_heartbeat, daemon=True)
        heartbeat_thread.start()
        
        try:
            result = self.backend.transcribe(
                audio_file,
                language=source_lang,
                task=task,
                batch_size=batch_size,
                initial_prompt=initial_prompt
            )
            
            elapsed = time.time() - start_time
            self.logger.info(f"  ✓ Complete: {len(result.get('segments', []))} segments in {elapsed:.1f}s")
            
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            self.logger.error(f"  ✗ Failed after {elapsed:.1f}s: {e}", exc_info=True)
            raise
        finally:
            heartbeat_active = False
            heartbeat_thread.join(timeout=1.0)
        
        # Filter low-confidence segments
        result = self._filter_segments(result)
        
        # Add bias context metadata
        if bias_windows:
            result = self._apply_bias_metadata(result, bias_windows)
        
        return result
    
    def _transcribe_hybrid(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[Any],
        batch_size: int
    ) -> Dict[str, Any]:
        """
        Hybrid strategy - Best balance of speed and accuracy.
        
        Uses first window's terms as initial context, then relies on
        Whisper's condition_on_previous_text for adaptation.
        """
        if not bias_windows:
            return self.backend.transcribe(audio_file, language=source_lang, task=task, batch_size=batch_size)
        
        self.logger.info(f"  ⚡ PHASE 2: Hybrid strategy")
        
        # Use first window's terms as initial prompt
        initial_prompt = None
        if bias_windows and bias_windows[0].bias_terms:
            first_window_terms = list(bias_windows[0].bias_terms)[:50]
            initial_prompt = ", ".join(first_window_terms)
            self.logger.info(f"    • Initial prompt: {len(first_window_terms)} terms from first window")
        
        result = self.backend.transcribe(
            audio_file,
            language=source_lang,
            task=task,
            batch_size=batch_size,
            initial_prompt=initial_prompt
        )
        
        self.logger.info(f"  ✓ Hybrid complete: {len(result.get('segments', []))} segments")
        
        # Filter and add metadata
        result = self._filter_segments(result)
        result = self._apply_bias_metadata(result, bias_windows)
        
        return result
    
    def _transcribe_windowed_chunks(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[Any],
        batch_size: int
    ) -> Dict[str, Any]:
        """
        Windowed chunks strategy - Highest accuracy, time-aware.
        
        Processes audio in chunks matching bias windows, using window-specific
        bias terms for each chunk. Best accuracy but slower.
        
        Best for:
        - High-accuracy requirements
        - Context-aware transcription (subtitles, character names)
        - Time-specific terminology (scene-dependent)
        
        Process:
        - Split audio into chunks matching bias windows
        - Each chunk uses window-specific bias terms
        - Merge overlapping segments intelligently
        """
        # Import load_audio with fallback
        try:
            from whisperx.audio import load_audio as _load_audio
        except ImportError:
            try:
                import librosa
                def _load_audio(file: str, sr: int = 16000) -> Any:
                    """Load audio with librosa fallback"""
                    audio, _ = librosa.load(file, sr=sr, mono=True)
                    return audio
            except ImportError:
                self.logger.error("  ✗ Cannot load audio (no whisperx or librosa)", exc_info=True)
                raise ImportError("Need whisperx or librosa for audio loading")
        
        if not bias_windows:
            # Fall back to regular transcription
            return self.backend.transcribe(
                audio_file,
                language=source_lang,
                task=task,
                batch_size=batch_size
            )
        
        self.logger.info(f"  🎯 Windowed chunks strategy")
        self.logger.info(f"    • Processing {len(bias_windows)} bias windows")
        self.logger.info(f"    • Window-specific bias terms (time-aware)")
        
        # Load full audio
        audio = _load_audio(audio_file)
        sample_rate = 16000  # Whisper standard sample rate
        
        all_segments = []
        total_windows = len(bias_windows)
        
        # Process each bias window
        for i, window in enumerate(bias_windows, 1):
            self.logger.info(f"  Window {i}/{total_windows}: {window.start_time:.1f}s - {window.end_time:.1f}s")
            
            # Extract audio chunk for this window
            start_sample = int(window.start_time * sample_rate)
            end_sample = int(window.end_time * sample_rate)
            chunk_audio = audio[start_sample:end_sample]
            
            # Skip if chunk is too short
            if len(chunk_audio) < sample_rate * 0.5:  # Skip chunks < 0.5 seconds
                self.logger.warning(f"    ⚠️  Skipping window (too short)")
                continue
            
            # Create window-specific bias prompt
            window_terms = list(window.bias_terms)[:50]  # Up to 50 terms
            initial_prompt = ", ".join(window_terms) if window_terms else None
            
            self.logger.info(f"    • Bias: {len(window_terms)} terms")
            self.logger.debug(f"    • Preview: {', '.join(window_terms[:3])}...")
            
            # Transcribe chunk with window-specific bias
            try:
                chunk_result = self.backend.transcribe(
                    chunk_audio,  # NumPy array (WhisperX/MLX supports this)
                    language=source_lang,
                    task=task,
                    batch_size=batch_size,
                    initial_prompt=initial_prompt
                )
                
                # Adjust timestamps to global timeline
                for segment in chunk_result.get('segments', []):
                    segment['start'] += window.start_time
                    segment['end'] += window.start_time
                    # Add window-specific metadata
                    segment['bias_window_id'] = window.window_id
                    segment['bias_terms'] = window.bias_terms
                    segment['bias_strategy'] = 'chunked_windows'
                
                all_segments.extend(chunk_result.get('segments', []))
                self.logger.info(f"    ✓ Window complete: {len(chunk_result.get('segments', []))} segments")
                
            except Exception as e:
                self.logger.error(f"    ✗ Window {i} failed: {e}", exc_info=True)
                # Continue with other windows - partial results better than none
                continue
        
        self.logger.info(f"  Merging {len(all_segments)} segments from {total_windows} windows...")
        
        # Merge overlapping segments from adjacent windows
        merged_segments = self._merge_overlapping_segments(all_segments)
        
        # Apply confidence-based filtering
        filtered_segments = self._filter_segments({'segments': merged_segments})['segments']
        
        self.logger.info(f"  ✓ Windowed transcription complete: {len(filtered_segments)} merged segments")
        
        return {
            "segments": filtered_segments,
            "language": source_lang,
            "bias_strategy": "chunked_windows",
            "num_windows": total_windows
        }
    
    def _merge_overlapping_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Merge duplicate segments from overlapping bias windows.
        
        When windows overlap (stride < window_size), we get duplicate transcriptions
        for the overlapping region. This merges them intelligently.
        
        Args:
            segments: List of segments from multiple windows
            
        Returns:
            Merged list with duplicates removed
        """
        if not segments:
            return []
        
        # Sort by start time
        sorted_segments = sorted(segments, key=lambda s: s.get('start', 0))
        
        merged = []
        for segment in sorted_segments:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            
            # Check if this segment overlaps significantly with the last merged segment
            if merged:
                last = merged[-1]
                last_end = last.get('end', 0)
                
                # If significant overlap (>50% of current segment)
                overlap = min(last_end, end) - max(last.get('start', 0), start)
                segment_duration = end - start
                
                if overlap > 0 and segment_duration > 0:
                    overlap_ratio = overlap / segment_duration
                    
                    if overlap_ratio > 0.5:
                        # Merge: choose segment with higher confidence or longer text
                        last_text = last.get('text', '').strip()
                        curr_text = segment.get('text', '').strip()
                        
                        # Prefer segment with more text (likely more complete)
                        if len(curr_text) > len(last_text):
                            # Replace last with current
                            merged[-1] = segment
                            self.logger.debug(f"    Merged overlap: kept newer segment")
                        # else: keep existing segment
                        continue
            
            # No significant overlap, add as new segment
            merged.append(segment)
        
        return merged
    
    def _transcribe_chunked(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[Any],
        batch_size: int,
        output_dir: Optional[Path]
    ) -> Dict[str, Any]:
        """
        Chunked strategy with checkpointing - For very large files.
        
        Best for:
        - Very large files (> 30 minutes)
        - Stability over speed
        - Resume-able processing
        
        Process:
        - Split into 5-minute chunks
        - Process with checkpointing (resume on failure)
        - Merge all chunks into final result
        """
        from shared.asr_chunker import ChunkedASRProcessor
        
        if not output_dir:
            # Fallback to temp directory if no output_dir provided
            import tempfile
            output_dir = Path(tempfile.mkdtemp())
            self.logger.warning(f"  No output_dir provided, using temp: {output_dir}")
        
        self.logger.info(f"  📦 Chunked strategy (large file support)")
        
        chunker = ChunkedASRProcessor(self.logger, chunk_duration=300)  # 5 min chunks
        
        # Create chunks output directory
        chunks_dir = output_dir / 'chunks' / task
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        # Create chunks (audio_file, output_dir)
        chunks = chunker.create_chunks(audio_file, chunks_dir)
        self.logger.info(f"    • Created {len(chunks)} chunks")
        
        # Process each chunk with checkpointing
        chunk_results = []
        checkpoint_dir = output_dir / 'chunks' / task
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        for i, chunk in enumerate(chunks):
            self.logger.info(f"  Chunk {i+1}/{len(chunks)}: {chunk.start_time:.1f}s - {chunk.end_time:.1f}s")
            
            # Try to load from checkpoint
            cached_result = chunker.load_checkpoint(chunk.chunk_id, checkpoint_dir)
            
            if cached_result:
                self.logger.info(f"    ✓ Loading cached chunk {chunk.chunk_id}")
                chunk_results.append(cached_result)
            else:
                # Process chunk with retry
                try:
                    result = self._process_chunk_with_retry(
                        chunker, chunk, source_lang, task, batch_size
                    )
                    
                    # Save checkpoint
                    chunker.save_checkpoint(chunk.chunk_id, result, checkpoint_dir)
                    chunk_results.append(result)
                    
                    self.logger.info(f"    ✓ Chunk complete: {len(result.get('segments', []))} segments")
                    
                except Exception as e:
                    self.logger.error(f"    ✗ Chunk {chunk.chunk_id} failed: {e}", exc_info=True)
                    # Continue with other chunks, partial results better than none
                    continue
        
        # Merge all chunks
        self.logger.info(f"  Merging {len(chunk_results)} processed chunks...")
        merged_result = chunker.merge_chunk_results(chunk_results)
        
        # Apply confidence-based filtering
        filtered_result = self._filter_segments(merged_result)
        
        self.logger.info(f"  ✓ Chunked transcription complete: {len(filtered_result['segments'])} segments")
        
        return filtered_result
    
    def _process_chunk_with_retry(
        self,
        chunker: Any,
        chunk: Any,
        language: str,
        task: str,
        batch_size: int,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Process a single chunk with retry logic.
        
        Args:
            chunker: ChunkedASRProcessor instance
            chunk: Chunk to process
            language: Language code
            task: Task type (transcribe/translate)
            batch_size: Batch size for processing
            max_retries: Maximum retry attempts
            
        Returns:
            Chunk transcription result
        """
        for attempt in range(max_retries):
            try:
                return chunker.process_chunk_with_bias(
                    chunk, self.backend, language, task, batch_size
                )
            except Exception as e:
                self.logger.warning(f"    ⚠️  Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Reduce batch size for retry
                    batch_size = max(batch_size // 2, 4)
                    self.logger.warning(f"    🔄 Retrying with batch_size={batch_size}")
                else:
                    raise
        
        raise RuntimeError(f"All {max_retries} retries failed")
    
    # ─────────────────────────────────────────────────────────────────────
    # Post-Processing
    # ─────────────────────────────────────────────────────────────────────
    
    def _filter_segments(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Filter low-confidence segments"""
        segments = result.get('segments', [])
        min_logprob = float(self.config.get('WHISPER_LOGPROB_THRESHOLD', str(-0.7)))
        min_duration = float(self.config.get('WHISPER_MIN_DURATION', str(0.1)))
        
        filtered = []
        for seg in segments:
            text = seg.get('text', '').strip()
            if not text:
                continue
            
            avg_logprob = seg.get('avg_logprob', 0)
            if avg_logprob < min_logprob:
                continue
            
            duration = seg.get('end', 0) - seg.get('start', 0)
            if duration < min_duration:
                continue
            
            filtered.append(seg)
        
        removed = len(segments) - len(filtered)
        if removed > 0:
            self.logger.info(f"  🧹 Filtered {removed} low-quality segments")
        
        result['segments'] = filtered
        return result
    
    def _apply_bias_metadata(self, result: Dict[str, Any], bias_windows: Any) -> Dict[str, Any]:
        """Add bias window metadata to segments"""
        # TODO: Implement bias window matching
        # For now, just return result as-is
        return result


__all__ = ['BiasPromptingStrategy']
