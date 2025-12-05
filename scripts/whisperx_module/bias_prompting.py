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
        
        TODO: Implement window-specific chunking
        Currently falls back to hybrid strategy.
        """
        self.logger.warning("  ⚠️  Windowed chunks not yet implemented, using hybrid")
        return self._transcribe_hybrid(audio_file, source_lang, task, bias_windows, batch_size)
    
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
        
        Splits large files into manageable chunks with checkpointing
        for stability. Best for files > 30 minutes.
        
        TODO: Implement chunked processing with checkpoints
        Currently falls back to whole-file strategy.
        """
        self.logger.warning("  ⚠️  Chunked strategy not yet implemented, using whole-file")
        return self._transcribe_whole(audio_file, source_lang, task, bias_windows, batch_size)
    
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
