"""
whisperx_integration.py - WhisperX integration for ASR + translation

Handles:
- Loading Whisper model with appropriate backend (WhisperX/MLX)
- Processing audio with rolling windowed bias prompts
- ASR + translation in single pass
- Word-level alignment
- Saving results to ASR directory

Backends:
- WhisperX (CTranslate2): CPU/CUDA only
- MLX-Whisper: Apple Silicon MPS/Metal acceleration
- Auto-detection based on device availability
"""

# Standard library
import os
# Fix OpenMP duplicate library issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import json
import warnings
from pathlib import Path
import logging
from typing import List, Dict, Optional, Any
from tqdm import tqdm

# Suppress version mismatch warnings
warnings.filterwarnings('ignore', message='Model was trained with pyannote')
warnings.filterwarnings('ignore', message='Model was trained with torch')
warnings.filterwarnings('ignore', category=UserWarning, module='pyannote')
warnings.filterwarnings('ignore', message='.*torchaudio._backend.list_audio_backends.*')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='torchaudio')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='speechbrain')

# Removed: device_selector imports (unused, causes cross-environment issues)
# Backend selection now handled by whisper_backends.py (see line 47)

# TODO: These modules moved to shared/ directory (Phase 5 implementation)
# Context-aware features for subtitle generation accuracy
from shared.bias_window_generator import BiasWindow, get_window_for_time
from shared.mps_utils import cleanup_mps_memory, log_mps_memory, optimize_batch_size_for_mps
from shared.asr_chunker import ChunkedASRProcessor

# Standard library
import sys
from pathlib import Path
from typing import List, Optional, Any

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from whisper_backends import create_backend, get_recommended_backend

# Local
from shared.logger import get_logger
from shared.config import load_config
logger = get_logger(__name__)

# Audio loading utility
try:
    from whisperx.audio import load_audio
except ImportError:
    # Fallback for MLX environment without whisperx
    import librosa
    def load_audio(file: str, sr: int = 16000) -> Any:
        """Load audio file and resample to target sample rate"""
        audio, _ = librosa.load(file, sr=sr, mono=True)
        return audio

# Import IndicTrans2 translator - LAZY LOADED
# Note: Only imported when actually needed to avoid cross-environment dependencies
# The MLX environment doesn't have transformers, so we can't import this at module level
_indictrans2_translator = None
_indictrans2_available = None

def _get_indictrans2() -> Any:
    """Lazy load IndicTrans2 translator to avoid import issues in ASR-only environments"""
    global _indictrans2_translator, _indictrans2_available
    
    if _indictrans2_translator is None:
        try:
            from indictrans2_translator import (
                translate_whisperx_result, 
                IndicTrans2Translator,
                can_use_indictrans2
            )
            _indictrans2_translator = {
                'translate_whisperx_result': translate_whisperx_result,
                'IndicTrans2Translator': IndicTrans2Translator,
                'can_use_indictrans2': can_use_indictrans2
            }
            _indictrans2_available = True
        except ImportError as e:
            _indictrans2_available = False
            _indictrans2_translator = None
    
    return _indictrans2_translator, _indictrans2_available


class WhisperXProcessor:
    """WhisperX processor with configurable transcription parameters and multiple backends"""

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "int8",
        backend: str = "auto",
        hf_token: Optional[str] = None,
        temperature: str = "0.0,0.2,0.4,0.6,0.8,1.0",
        beam_size: int = 5,
        best_of: int = 5,
        patience: float = 1.0,
        length_penalty: float = 1.0,
        no_speech_threshold: float = 0.6,
        logprob_threshold: float = -1.0,
        compression_ratio_threshold: float = 2.4,
        condition_on_previous_text: bool = False,  # False prevents hallucination loops
        initial_prompt: str = "",
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize WhisperX processor

        Args:
            model_name: Whisper model name (e.g., "large-v3", "medium")
            device: Device to use (cpu, cuda, mps)
            compute_type: Compute type (int8, float16, float32)
            backend: Backend to use (auto, whisperx, mlx, ctranslate2)
            hf_token: Hugging Face token for model access
            temperature: Sampling temperature(s), comma-separated
            beam_size: Beam size for beam search
            best_of: Number of candidates to consider
            patience: Beam search patience factor
            length_penalty: Length penalty for beam search
            no_speech_threshold: Threshold for no speech detection
            logprob_threshold: Log probability threshold for filtering
            compression_ratio_threshold: Compression ratio threshold
            condition_on_previous_text: Condition on previous text
            initial_prompt: Initial prompt for transcription
            logger: Logger instance
        """
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.backend_type = backend
        self.hf_token = hf_token
        self.logger = logger or self._create_default_logger()
        
        # NOTE: Backend-specific parameter support:
        # WhisperX (CTranslate2): Limited parameters (language, task, batch_size)
        # MLX-Whisper: More parameters supported
        # Store all for potential use
        
        self.temperature = self._parse_temperature(temperature)
        self.beam_size = beam_size
        self.best_of = best_of
        self.patience = patience
        self.length_penalty = length_penalty
        self.no_speech_threshold = no_speech_threshold
        self.logprob_threshold = logprob_threshold
        self.compression_ratio_threshold = compression_ratio_threshold
        self.condition_on_previous_text = condition_on_previous_text
        self.initial_prompt = initial_prompt

        # Backend instance
        self.backend = None
        self.align_model = None
        self.align_metadata = None
    
    def _parse_temperature(self, temperature: str) -> list:
        """Parse temperature string to list of floats"""
        if isinstance(temperature, (list, tuple)):
            return list(temperature)
        if isinstance(temperature, str):
            return [float(t.strip()) for t in temperature.split(',')]
        return [float(temperature)]

    def _create_default_logger(self) -> Any:
        """Create default logger if none provided"""
        from shared.logger import PipelineLogger
        return PipelineLogger("whisperx")

    def load_model(self) -> None:
        """Load Whisper model using appropriate backend"""
        self.logger.info(f"Loading Whisper model: {self.model_name}")
        self.logger.info(f"  Device requested: {self.device}")
        self.logger.info(f"  Backend: {self.backend_type}")
        
        # Get recommended backend if auto
        if self.backend_type == "auto":
            recommended = get_recommended_backend(self.device, self.logger)
            self.logger.info(f"  Auto-detected backend: {recommended}")
            backend_to_use = recommended
        else:
            backend_to_use = self.backend_type
        
        # Create backend instance
        self.backend = create_backend(
            backend_to_use,
            self.model_name,
            self.device,
            self.compute_type,
            self.logger,
            self.condition_on_previous_text,
            self.logprob_threshold,
            self.no_speech_threshold,
            self.compression_ratio_threshold
        )
        
        if not self.backend:
            raise RuntimeError(f"Failed to create backend: {backend_to_use}")
        
        # Load model with fallback support
        success = self.backend.load_model()
        
        # Handle fallback from MLX to WhisperX
        if success == "fallback_to_whisperx":
            self.logger.info("=" * 60)
            self.logger.info("MLX BACKEND FALLBACK")
            self.logger.info("=" * 60)
            self.logger.info("Recreating backend with WhisperX...")
            
            # Switch to WhisperX backend
            backend_to_use = "whisperx"
            self.backend_name = backend_to_use
            
            # Recreate backend (using module-level import)
            self.backend = create_backend(
                backend_to_use,
                self.model_name,
                self.device,
                self.compute_type,
                self.logger,
                self.condition_on_previous_text,
                self.logprob_threshold,
                self.no_speech_threshold,
                self.compression_ratio_threshold
            )
            
            if not self.backend:
                raise RuntimeError(f"Failed to create fallback backend: {backend_to_use}")
            
            # Try loading with WhisperX
            success = self.backend.load_model()
            
            if not success:
                raise RuntimeError(f"Failed to load model with fallback backend: {backend_to_use}")
            
            self.logger.info(f"  ✓ Successfully fell back to WhisperX backend")
        elif not success:
            raise RuntimeError(f"Failed to load model with backend: {self.backend.name}")
        
        # Update device to actual device used (may have fallen back)
        self.device = self.backend.device
        self.logger.info(f"  ✓ Model loaded with backend: {self.backend.name}")
        self.logger.info(f"  ✓ Active device: {self.device}")

    def load_align_model(self, language: str) -> None:
        """
        Load alignment model for word-level timestamps

        Args:
            language: Language code (e.g., "en", "hi")
        """
        if not self.backend:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        self.logger.info(f"Loading alignment model for language: {language}")
        success = self.backend.load_align_model(language)
        
        if success:
            self.logger.info("  ✓ Alignment model loaded")
        else:
            self.logger.warning("  ⚠ Alignment model not available")
    
    def cleanup(self) -> None:
        """Clean up resources"""
        if self.backend:
            self.backend.cleanup()
            self.backend = None
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            self.cleanup()
        except:
            pass

    def filter_low_confidence_segments(
        self,
        segments: List[Dict[str, Any]],
        min_logprob: float = -0.7,
        min_duration: float = 0.1
    ) -> List[Dict[str, Any]]:
        """
        Filter out low-confidence and zero-duration segments (Phase 1 optimization).

        This implements confidence-based filtering to remove:
        - Segments with low average log probability (likely hallucinations)
        - Zero-duration or very short segments (timing errors)
        - Empty text segments

        Args:
            segments: List of transcription segments
            min_logprob: Minimum average log probability (-0.7 recommended)
            min_duration: Minimum segment duration in seconds (0.1s recommended)

        Returns:
            Filtered segments list
        """
        if not segments:
            return segments

        filtered = []
        removed_count = 0
        removed_by_confidence = 0
        removed_by_duration = 0
        removed_by_empty = 0

        for seg in segments:
            # Check for empty text
            text = seg.get('text', '').strip()
            if not text:
                removed_by_empty += 1
                removed_count += 1
                continue

            # Check confidence (avg_logprob)
            avg_logprob = seg.get('avg_logprob', 0)
            if avg_logprob < min_logprob:
                removed_by_confidence += 1
                removed_count += 1
                self.logger.debug(f"  Filtered low confidence ({avg_logprob:.2f}): {text[:50]}")
                continue

            # Check duration
            start = seg.get('start', 0)
            end = seg.get('end', 0)
            duration = end - start

            if duration < min_duration:
                removed_by_duration += 1
                removed_count += 1
                self.logger.debug(f"  Filtered short duration ({duration:.3f}s): {text[:50]}")
                continue

            # Passed all filters
            filtered.append(seg)

        # Log filtering statistics
        if removed_count > 0:
            self.logger.info(f"  📊 Confidence filtering: Removed {removed_count}/{len(segments)} segments")
            self.logger.info(f"     - By confidence: {removed_by_confidence}")
            self.logger.info(f"     - By duration: {removed_by_duration}")
            self.logger.info(f"     - By empty text: {removed_by_empty}")
        else:
            self.logger.debug(f"  Confidence filtering: All {len(segments)} segments passed")

        return filtered

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
        Transcribe and translate audio with bias prompt injection.
        
        Supports multiple bias strategies:
        - global: Phase 1 - Global prompts (fast, good accuracy)
        - hybrid: Phase 2 - Global bias + contextual initial_prompt (best balance)
        - chunked_windows: Phase 3 - Window-specific prompts (most accurate, slower)
        - chunked: Large file chunking with checkpointing (for stability)

        Args:
            audio_file: Path to audio/video file
            source_lang: Source language (e.g., "hi")
            target_lang: Target language (e.g., "en")
            bias_windows: List of bias windows for prompt injection
            batch_size: Batch size for inference
            output_dir: Output directory for checkpoints (required for chunking)
            bias_strategy: Bias prompting strategy (global/hybrid/chunked_windows/chunked)
            workflow_mode: Workflow mode (transcribe/transcribe-only/translate-only/subtitle-gen)

        Returns:
            Whisper result dict with segments and word-level timestamps
        """
        self.logger.info(f"Transcribing: {audio_file}")
        self.logger.info(f"  Source: {source_lang}, Target: {target_lang}")
        self.logger.info(f"  Backend: {self.backend.name}")
        self.logger.info(f"  Bias strategy: {bias_strategy}")

        if not self.backend:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Optimize batch size for MPS
        original_batch_size = batch_size
        batch_size = optimize_batch_size_for_mps(batch_size, self.backend.device, 'large')
        if batch_size != original_batch_size:
            self.logger.info(f"  🎯 MPS optimization: batch_size {original_batch_size} → {batch_size}")

        # Determine task
        # For transcribe-only workflows, always transcribe (never translate)
        # For transcribe mode with target language, can translate
        # For other workflows, translate if source != target
        if workflow_mode == 'transcribe-only':
            task = "transcribe"
            self.logger.info(f"  Task: {task} (workflow_mode={workflow_mode}, keeping source language)")
        elif workflow_mode == 'transcribe':
            # Allow translation in transcribe mode if target is different
            task = "translate" if (source_lang != target_lang and target_lang != 'auto') else "transcribe"
            self.logger.info(f"  Task: {task} (workflow_mode={workflow_mode})")
        else:
            task = "translate" if source_lang != target_lang else "transcribe"
            self.logger.info(f"  Task: {task}")
        
        # Determine audio duration
        audio_duration = self._get_audio_duration(audio_file)
        self.logger.info(f"  Audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f} minutes)")
        
        # Strategy selection logic
        if bias_strategy == "chunked_windows":
            # Phase 3: Window-specific bias (most accurate)
            self.logger.info(f"  📊 PHASE 3: Chunked windows strategy")
            return self._transcribe_windowed_chunks(
                audio_file, source_lang, task,
                bias_windows, batch_size
            )
        
        elif bias_strategy == "hybrid":
            # Phase 2: Hybrid global + context (best balance)
            self.logger.info(f"  ⚡ PHASE 2: Hybrid strategy")
            return self._transcribe_hybrid(
                audio_file, source_lang, task,
                bias_windows, batch_size
            )
        
        elif bias_strategy == "chunked":
            # Large file chunking with checkpointing (for stability, not bias-specific)
            self.logger.info(f"  📦 Large file chunking strategy (with checkpointing)")
            return self._transcribe_chunked(
                audio_file, source_lang, task,
                bias_windows, batch_size, output_dir
            )
        
        else:
            # Phase 1: Global bias (default, fast)
            # Auto-decide between whole-file and chunked based on duration/device
            # TODO: Fix chunking API mismatch (dict vs object attributes)
            use_chunking = (
                audio_duration > 1800  # Only chunk if > 30 minutes (temporary until chunking fixed)
            )
            
            if use_chunking:
                self.logger.info(f"  📦 Using chunked processing (duration={audio_duration:.0f}s, device={self.backend.device})")
                return self._transcribe_chunked(
                    audio_file, source_lang, task, 
                    bias_windows, batch_size, output_dir
                )
            else:
                self.logger.info(f"  🚀 Whole-file processing (duration={audio_duration:.0f}s)")
                return self._transcribe_whole(
                    audio_file, source_lang, task,
                    bias_windows, batch_size
                )
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """Get audio duration in seconds"""
        # Use librosa to get duration directly (more efficient than loading full audio)
        try:
            import librosa
            duration = librosa.get_duration(path=audio_file)
            return duration
        except Exception as e:
            # Fallback: load and calculate duration
            try:
                audio = load_audio(audio_file)
                return len(audio) / 16000  # 16kHz sample rate
            except:
                # Last resort: use file size estimate (very rough)
                import os
                file_size = os.path.getsize(audio_file)
                # Rough estimate: 32-bit float at 16kHz stereo = ~128KB/sec
                return file_size / 128000
    
    def _transcribe_whole(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[Any],
        batch_size: int
    ) -> Dict[str, Any]:
        """Whole-file transcription with global bias prompting (for short files or CPU)"""
        
        # Load config for filtering thresholds
        config = load_config()
        
        # Create global bias prompts from bias windows
        initial_prompt = None
        
        if bias_windows:
            self.logger.info(f"  Bias windows available: {len(bias_windows)}")
            
            # Collect all unique bias terms across windows
            all_terms = set()
            for window in bias_windows:
                all_terms.update(window.bias_terms)
            
            # Create global bias prompts
            top_terms = list(all_terms)[:50]  # Limit to top 50 terms
            
            if top_terms:
                # initial_prompt: up to 50 terms as context (comma-separated sentence)
                # Note: WhisperX only supports initial_prompt, not hotwords
                initial_prompt = ", ".join(top_terms)
                
                self.logger.info(f"  🎯 Active bias prompting enabled:")
                self.logger.info(f"    Initial prompt: {len(top_terms)} terms")
                self.logger.debug(f"    Preview: {', '.join(top_terms[:5])}...")
        
        # Log parameters
        self.logger.info(f"  Transcription options:")
        self.logger.info(f"    Language: {source_lang}")
        self.logger.info(f"    Task: {task}")
        self.logger.info(f"    Batch size: {batch_size}")
        if initial_prompt:
            self.logger.info(f"    Bias: ACTIVE (global prompt)")
        
        # Log memory before
        log_mps_memory(self.logger, "  Before transcription - ")

        try:
            import time
            import threading
            
            start_time = time.time()
            self.logger.info(f"  🎙️ Starting transcription at {time.strftime('%H:%M:%S')}...")
            
            # Progress heartbeat for long-running transcriptions
            heartbeat_active = True
            def progress_heartbeat() -> None:
                """Log periodic progress to detect hangs"""
                last_log = start_time
                while heartbeat_active:
                    time.sleep(60)  # Every 60 seconds
                    if heartbeat_active:
                        elapsed = time.time() - last_log
                        total_elapsed = time.time() - start_time
                        self.logger.info(f"  ⏱️  Still transcribing... {total_elapsed/60:.1f} minutes elapsed")
                        last_log = time.time()
            
            # Start heartbeat thread
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
            finally:
                # Stop heartbeat
                heartbeat_active = False
                heartbeat_thread.join(timeout=1.0)
            
            elapsed = time.time() - start_time
            self.logger.info(f"  ✓ Transcription complete: {len(result.get('segments', []))} segments in {elapsed:.1f}s ({elapsed/60:.1f} min)")
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            self.logger.error(f"  ✗ Transcription failed after {elapsed:.1f}s: {e}", exc_info=True)
            self.logger.error(f"  Audio file: {audio_file}")
            self.logger.error(f"  Language: {source_lang}, Task: {task}")
            raise
        finally:
            # Always cleanup MPS memory
            cleanup_mps_memory(self.logger)
            log_mps_memory(self.logger, "  After transcription - ")

        # Phase 1: Apply confidence-based filtering
        segments = result.get('segments', [])
        min_logprob = float(config.get('WHISPER_LOGPROB_THRESHOLD', str(-0.7)))
        min_duration = float(config.get('WHISPER_MIN_DURATION', str(0.1)))
        filtered_segments = self.filter_low_confidence_segments(segments, min_logprob, min_duration)
        result['segments'] = filtered_segments

        # Apply bias window metadata to segments (for reference)
        if bias_windows:
            result = self._apply_bias_context(result, bias_windows)

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
        PHASE 2: Hybrid Strategy - Global bias + dynamic initial_prompt
        
        Best balance between speed and accuracy:
        - Uses global bias terms for comprehensive coverage
        - Uses first window's terms as initial context
        - Lets Whisper's condition_on_previous_text provide adaptation
        - Single transcription pass (fast like global, but more contextual)
        
        Args:
            audio_file: Path to audio file
            source_lang: Source language code
            task: 'transcribe' or 'translate'
            bias_windows: List of bias windows
            batch_size: Batch size for processing
            
        Returns:
            Transcription result with bias metadata
        """
        if not bias_windows:
            # Fall back to regular transcription without bias
            return self.backend.transcribe(
                audio_file, 
                language=source_lang, 
                task=task, 
                batch_size=batch_size
            )
        
        self.logger.info(f"  🎯 PHASE 2: Hybrid bias strategy")
        
        # Create global bias terms from all unique terms across windows
        all_terms = set()
        for window in bias_windows:
            all_terms.update(window.bias_terms)
        
        top_terms = list(all_terms)[:50]
        
        # Use first window's terms as initial prompt (provides early context)
        initial_prompt = None
        if bias_windows and bias_windows[0].bias_terms:
            # Get up to 50 terms from first window for initial context
            first_window_terms = list(bias_windows[0].bias_terms)[:50]
            initial_prompt = ", ".join(first_window_terms)
        
        self.logger.info(f"    • Initial prompt: {len(first_window_terms) if initial_prompt else 0} terms from first window")
        self.logger.info(f"    • Strategy: Early context + Whisper's adaptation")
        
        # Log memory before
        log_mps_memory(self.logger, "  Before hybrid transcription - ")
        
        try:
            result = self.backend.transcribe(
                audio_file,
                language=source_lang,
                task=task,
                batch_size=batch_size,
                initial_prompt=initial_prompt
            )

            self.logger.info(f"  ✓ Hybrid transcription complete: {len(result.get('segments', []))} segments")

        except Exception as e:
            self.logger.error(f"  ✗ Hybrid transcription failed: {e}", exc_info=True)
            raise
        finally:
            cleanup_mps_memory(self.logger)
            log_mps_memory(self.logger, "  After hybrid transcription - ")

        # Phase 1: Apply confidence-based filtering
        segments = result.get('segments', [])
        min_logprob = float(config.get('WHISPER_LOGPROB_THRESHOLD', str(-0.7)))
        min_duration = float(config.get('WHISPER_MIN_DURATION', str(0.1)))
        filtered_segments = self.filter_low_confidence_segments(segments, min_logprob, min_duration)
        result['segments'] = filtered_segments

        # Add window-specific metadata post-processing
        result = self._apply_bias_context(result, bias_windows)

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
        PHASE 3: Chunked Windows Strategy - Window-specific bias prompts
        
        Most accurate but slower:
        - Processes audio in chunks matching bias windows
        - Each chunk uses window-specific bias terms (10 terms per window)
        - Time-aware: different terms for different scenes
        - Handles overlapping windows with merging logic
        
        Args:
            audio_file: Path to audio file
            source_lang: Source language code
            task: 'transcribe' or 'translate'
            bias_windows: List of bias windows
            batch_size: Batch size for processing
            
        Returns:
            Transcription result with window-specific bias metadata
        """
        import whisperx
        import numpy as np
        
        # Import load_audio with fallback
        try:
            from whisperx.audio import load_audio as _load_audio
        except ImportError:
            import librosa
            def _load_audio(file: str, sr: int = 16000) -> Any:
                """ Load Audio."""
                audio, _ = librosa.load(file, sr=sr, mono=True)
                return audio
        
        if not bias_windows:
            # Fall back to regular transcription
            return self.backend.transcribe(
                audio_file,
                language=source_lang,
                task=task,
                batch_size=batch_size
            )
        
        self.logger.info(f"  🎯 PHASE 3: Chunked windows strategy")
        self.logger.info(f"    • Processing {len(bias_windows)} bias windows")
        self.logger.info(f"    • Window-specific bias terms (adaptive)")
        
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
                log_mps_memory(self.logger, f"    Before window {i} - ")
                
                chunk_result = self.backend.transcribe(
                    chunk_audio,  # NumPy array (WhisperX supports this)
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
            finally:
                cleanup_mps_memory(self.logger)
        
        self.logger.info(f"  Merging {len(all_segments)} segments from {total_windows} windows...")

        # Merge overlapping segments from adjacent windows
        merged_segments = self._merge_overlapping_segments(all_segments)

        # Phase 1: Apply confidence-based filtering
        min_logprob = float(config.get('WHISPER_LOGPROB_THRESHOLD', str(-0.7)))
        min_duration = float(config.get('WHISPER_MIN_DURATION', str(0.1)))
        filtered_segments = self.filter_low_confidence_segments(merged_segments, min_logprob, min_duration)

        self.logger.info(f"  ✓ Chunked transcription complete: {len(filtered_segments)} merged segments")

        return {
            "segments": filtered_segments,
            "language": source_lang,
            "bias_strategy": "chunked_windows",
            "num_windows": total_windows
        }
    
    def _merge_overlapping_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Merge duplicate segments from overlapping bias windows
        
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
        """Chunked transcription with window-specific bias and checkpointing"""
        
        if not output_dir:
            # Fallback to temp directory if no output_dir provided
            import tempfile
            output_dir = Path(tempfile.mkdtemp())
            self.logger.warning(f"  No output_dir provided, using temp: {output_dir}")
        
        chunker = ChunkedASRProcessor(self.logger, chunk_duration=300)  # 5 min chunks
        
        # Create chunks output directory
        chunks_dir = output_dir / 'chunks' / task
        chunks_dir.mkdir(parents=True, exist_ok=True)
        
        # Create chunks (audio_file, output_dir)
        chunks = chunker.create_chunks(audio_file, chunks_dir)
        
        # Process each chunk with checkpointing
        chunk_results = []
        checkpoint_dir = output_dir / 'chunks' / task
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        for i, chunk in enumerate(chunks):
            self.logger.info(f"  Processing chunk {i+1}/{len(chunks)}")
            
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
                    
                    # Memory cleanup after each chunk
                    cleanup_mps_memory(self.logger)
                    
                except Exception as e:
                    self.logger.error(f"    ✗ Chunk {chunk.chunk_id} failed: {e}", exc_info=True)
                    # Continue with other chunks, partial results better than none
                    continue
        
        # Merge all chunks
        self.logger.info(f"  Merging {len(chunk_results)} processed chunks...")
        merged_result = chunker.merge_chunk_results(chunk_results)

        # Phase 1: Apply confidence-based filtering
        segments = merged_result.get('segments', [])
        min_logprob = float(config.get('WHISPER_LOGPROB_THRESHOLD', str(-0.7)))
        min_duration = float(config.get('WHISPER_MIN_DURATION', str(0.1)))
        filtered_segments = self.filter_low_confidence_segments(segments, min_logprob, min_duration)
        merged_result['segments'] = filtered_segments

        return merged_result
    
    def _process_chunk_with_retry(
        self,
        chunker: ChunkedASRProcessor,
        chunk,
        language: str,
        task: str,
        batch_size: int,
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """Process a single chunk with retry logic"""
        from shared.mps_utils import retry_with_degradation
        
        # Simple retry wrapper - the decorator doesn't work well here
        # because we need to modify chunker's state
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
                    cleanup_mps_memory(self.logger)
                else:
                    raise
        
        raise RuntimeError(f"All {max_retries} retries failed")

    def _apply_bias_context(
        self,
        result: Dict[str, Any],
        bias_windows: Any
    ) -> Dict[str, Any]:
        """
        Apply bias window context to segments (metadata annotation)

        Args:
            result: WhisperX result
            bias_windows: List of bias windows

        Returns:
            Result with bias context metadata
        """
        segments = result.get("segments", [])

        for segment in segments:
            start_time = segment.get("start", 0)
            window = get_window_for_time(bias_windows, start_time)

            if window:
                # Add bias context as metadata
                segment["bias_window_id"] = window.window_id
                segment["bias_terms"] = window.bias_terms

        return result

    def align_with_whisperx_subprocess(
        self,
        segments: List[Dict[str, Any]],
        audio_file: str,
        language: str
    ) -> Dict[str, Any]:
        """
        Run WhisperX alignment in separate subprocess for stability
        
        DELEGATED to AlignmentEngine (Phase 6 extraction)
        
        Args:
            segments: Transcription segments
            audio_file: Path to audio file
            language: Language code
            
        Returns:
            Dict with aligned segments including word-level timestamps
        """
        from whisperx_module.alignment import AlignmentEngine
        
        engine = AlignmentEngine(
            backend=self.backend,
            device=self.device,
            logger=self.logger
        )
        
        return engine.align_subprocess(segments, audio_file, language)

    def align_segments(
        self,
        result: Dict[str, Any],
        audio_file: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Add word-level alignment to segments
        
        DELEGATED to AlignmentEngine (Phase 6 extraction)
        
        Args:
            result: Whisper transcription result
            audio_file: Path to audio/video file
            target_lang: Target language for alignment

        Returns:
            Result with word-level timestamps
        """
        from whisperx_module.alignment import AlignmentEngine
        
        engine = AlignmentEngine(
            backend=self.backend,
            device=self.device,
            logger=self.logger
        )
        
        return engine.align(result, audio_file, target_lang)

    def save_results(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        basename: str,
        target_lang: Optional[str] = None
    ):
        """
        Save WhisperX results to output directory

        Args:
            result: WhisperX result
            output_dir: Output directory (e.g., out/Movie/asr/)
            basename: Base filename
            target_lang: Target language for filename suffix (e.g., "en" -> "basename-English.srt")
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Language code to name mapping for readable filenames
        lang_names = {
            'en': 'English', 'es': 'Spanish', 'fr': 'French', 'de': 'German',
            'it': 'Italian', 'pt': 'Portuguese', 'ru': 'Russian', 'ja': 'Japanese',
            'ko': 'Korean', 'zh': 'Chinese', 'ar': 'Arabic', 'hi': 'Hindi',
            'ta': 'Tamil', 'te': 'Telugu', 'bn': 'Bengali', 'ur': 'Urdu'
        }
        
        # Create language suffix for filenames if target_lang is provided
        lang_suffix = ""
        if target_lang and target_lang != 'auto':
            lang_name = lang_names.get(target_lang, target_lang.lower())
            lang_suffix = f"_{lang_name}"

        # Save full JSON result with basename
        # Pattern: {stage}_{lang}_whisperx.json or {stage}_whisperx.json
        json_file = output_dir / f"{basename}{lang_suffix}_whisperx.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save segments as JSON (cleaner format) with basename
        # Pattern: {stage}_{lang}_segments.json or {stage}_segments.json
        segments_file = output_dir / f"{basename}{lang_suffix}_segments.json"
        segments = result.get("segments", [])
        with open(segments_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {segments_file}")

        # Save as plain text transcript with basename
        # Pattern: {stage}_{lang}_transcript.txt or {stage}_transcript.txt
        txt_file = output_dir / f"{basename}{lang_suffix}_transcript.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    f.write(f"{text}\n")
        self.logger.info(f"  Saved: {txt_file}")

        # Save as SRT with basename
        # Pattern: {stage}_{lang}_subtitles.srt or {stage}_subtitles.srt
        srt_file = output_dir / f"{basename}{lang_suffix}_subtitles.srt"
        self._save_as_srt(segments, srt_file)
        self.logger.info(f"  Saved: {srt_file}")
        
        # Save primary files with proper stage naming (Task #5)
        # Pattern: {stage}_transcript.json and {stage}_segments.json
        primary_json = output_dir / f"{basename}_transcript.json"
        with open(primary_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        self.logger.info(f"  Saved: {primary_json}")
        
        primary_segments = output_dir / f"{basename}_segments.json"
        with open(primary_segments, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
        self.logger.info(f"  Saved: {primary_segments}")
        
        # Also save with legacy names for backward compatibility
        # TODO: Remove after all stages updated to use new naming
        legacy_json = output_dir / "transcript.json"
        with open(legacy_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        legacy_segments = output_dir / "segments.json"
        with open(legacy_segments, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)

    def _save_as_srt(self, segments: List[Dict], srt_file: Path) -> None:
        """
        Save segments as SRT subtitle file

        Args:
            segments: List of WhisperX segments
            srt_file: Output SRT file path
        """
        with open(srt_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start = segment.get("start", 0)
                end = segment.get("end", start + 1)
                text = segment.get("text", "").strip()

                if not text:
                    continue

                # Format timestamps as HH:MM:SS,mmm
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n")
                f.write("\n")

    def _format_srt_time(self, seconds: float) -> str:
        """
        Format seconds as SRT timestamp (HH:MM:SS,mmm)

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def run_whisperx_pipeline(
    audio_file: str,
    output_dir: Path,
    basename: str,
    source_lang: str,
    target_lang: str,
    bias_windows: Optional[Any],
    model_name: str,
    device: str,
    compute_type: str,
    hf_token: Optional[str],
    logger: Optional[PipelineLogger] = None,
    bias_strategy: str = "global",
    backend: str = "whisperx",
    workflow_mode: str = "subtitle-gen",
    temperature: str = "0.0,0.2,0.4,0.6,0.8,1.0",
    beam_size: int = 5,
    no_speech_threshold: float = 0.6,
    logprob_threshold: float = -1.0,
    compression_ratio_threshold: float = 2.4
) -> Dict[str, Any]:
    """
    Run complete WhisperX pipeline

    Args:
        audio_file: Path to audio/video file
        output_dir: Output directory
        basename: Base filename
        source_lang: Source language
        target_lang: Target language
        bias_windows: Bias windows for prompt injection
        model_name: WhisperX model name
        device: Device to use
        compute_type: Compute type
        hf_token: HF token
        logger: Logger instance
        bias_strategy: Bias prompting strategy (global/hybrid/chunked_windows/chunked)
        backend: Backend to use (whisperx/mlx/auto)
        workflow_mode: Workflow mode (transcribe/transcribe-only/translate-only/subtitle-gen)
        temperature: Temperature values for sampling
        beam_size: Beam size for decoding
        no_speech_threshold: Threshold for no speech detection
        logprob_threshold: Log probability threshold
        compression_ratio_threshold: Compression ratio threshold

    Returns:
        WhisperX result dict
    """
    # Import extracted transcription orchestration engine
    from whisperx_module.transcription import TranscriptionEngine
    
    # Create processor instance
    processor = WhisperXProcessor(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        backend=backend,
        hf_token=hf_token,
        temperature=temperature,
        beam_size=beam_size,
        no_speech_threshold=no_speech_threshold,
        logprob_threshold=logprob_threshold,
        compression_ratio_threshold=compression_ratio_threshold,
        logger=logger
    )

    try:
        # Create transcription engine with processor and IndicTrans2 support
        engine = TranscriptionEngine(
            processor=processor,
            logger=logger,
            get_indictrans2_fn=_get_indictrans2
        )
        
        # Run the complete pipeline (handles two-step and single-step workflows)
        result = engine.run_pipeline(
            audio_file=audio_file,
            output_dir=output_dir,
            basename=basename,
            source_lang=source_lang,
            target_lang=target_lang,
            bias_windows=bias_windows,
            bias_strategy=bias_strategy,
            workflow_mode=workflow_mode
        )
        
        return result
        
    finally:
        # Clean up resources
        processor.cleanup()


def main() -> Any:
    """Main entry point for WhisperX ASR stage."""
    import sys
    import os
    import json
    from pathlib import Path
    from shared.stage_utils import StageIO
    from shared.config import load_config
    
    # Set up stage I/O with manifest tracking
    stage_io = StageIO("asr", enable_manifest=True)
    logger = stage_io.get_stage_logger("DEBUG")
    
    logger.info("=" * 60)
    logger.info("ASR STAGE: Automatic Speech Recognition")
    logger.info("=" * 60)
    
    # Get output directory from StageIO
    output_dir = stage_io.output_base
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        return 1
    
    # Get audio file from demux stage
    audio_file = stage_io.get_input_path("audio.wav", from_stage="demux")
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}", exc_info=True)
        stage_io.add_error(f"Audio file not found: {audio_file}")
        stage_io.finalize(status="failed", error="Input file not found")
        return 1
    
    # Track input in manifest
    stage_io.track_input(audio_file, "audio", format="wav")
    
    logger.info(f"Input audio: {audio_file}")
    logger.info(f"Output directory: {output_dir}")
    
    # Get configuration parameters (defaults from system config)
    model_name = getattr(config, 'whisper_model', 'large-v3')
    source_lang = getattr(config, 'whisper_language', 'hi')
    target_lang = getattr(config, 'target_language', 'en')
    device = getattr(config, 'device', 'cpu').lower()
    compute_type = getattr(config, 'whisper_compute_type', 'float16')
    
    # Get backend preference from config (whisperx, mlx, auto)
    # Default to 'whisperx' to ensure bias prompting support
    backend = getattr(config, 'whisper_backend', 'whisperx')
    
    # Get workflow and language overrides from job config (job.json)
    # Job-specific parameters take precedence over system defaults (AD-006)
    workflow_mode = 'transcribe'  # Default
    job_json_path = stage_io.output_base / "job.json"
    logger.info(f"Looking for job.json at: {job_json_path}")
    if job_json_path.exists():
        import json
        logger.info("Reading job-specific parameters from job.json...")
        with open(job_json_path) as f:
            job_data = json.load(f)
            workflow_mode = job_data.get('workflow', 'transcribe')
            # Override source/target languages from job if specified
            if 'source_language' in job_data and job_data['source_language']:
                old_source = source_lang
                source_lang = job_data['source_language']
                logger.info(f"  source_language override: {old_source} → {source_lang} (from job.json)")
            if 'target_languages' in job_data and job_data['target_languages']:
                # For translation, first target language is the target
                old_target = target_lang
                target_lang = job_data['target_languages'][0] if job_data['target_languages'] else target_lang
                logger.info(f"  target_language override: {old_target} → {target_lang} (from job.json)")
    else:
        logger.warning(f"job.json not found at {job_json_path}, using system defaults")
    
    # Get HF token from secrets or environment
    hf_token = None
    secrets_path = Path("config/secrets.json")
    if secrets_path.exists():
        try:
            with open(secrets_path, 'r') as f:
                secrets = json.load(f)
                hf_token = secrets.get('hf_token')
        except Exception as e:
            logger.warning(f"Could not load HF token from secrets: {e}")
    
    # Fallback to config if not in secrets
    if not hf_token:
        hf_token = getattr(config, 'hf_token', None)
    
    logger.info(f"Model: {model_name}")
    logger.info(f"Source language: {source_lang}")
    logger.info(f"Target language: {target_lang}")
    logger.info(f"Device: {device}")
    logger.info(f"Compute type: {compute_type}")
    logger.info(f"Backend: {backend}")
    logger.info(f"Workflow mode: {workflow_mode}")
    
    # Track configuration in manifest
    stage_io.set_config({
        "model": model_name,
        "source_language": source_lang,
        "target_language": target_lang,
        "device": device,
        "compute_type": compute_type,
        "backend": backend,
        "workflow_mode": workflow_mode
    })
    
    # Language-specific parameter tuning
    # For non-Hindi/English pairs, use stricter parameters for better quality
    use_enhanced_params = not ((source_lang == 'hi' and target_lang == 'en') or 
                               (source_lang == 'en' and target_lang == 'hi') or
                               (source_lang == target_lang and source_lang in ['hi', 'en']))
    
    # Load Whisper parameters from config
    # Enhanced defaults for non-Hindi/English languages
    if use_enhanced_params:
        temperature = getattr(config, 'whisper_temperature', '0.0')
        beam_size = getattr(config, 'whisper_beam_size', 10)
        no_speech_threshold = getattr(config, 'whisper_no_speech_threshold', 0.7)
        logprob_threshold = getattr(config, 'whisper_logprob_threshold', -0.5)
        logger.info("Using enhanced parameters for non-Hindi/English language pair")
    else:
        # Default parameters for Hindi/English
        temperature = getattr(config, 'whisper_temperature', '0.0,0.2,0.4,0.6,0.8,1.0')
        beam_size = getattr(config, 'whisper_beam_size', 5)
        no_speech_threshold = getattr(config, 'whisper_no_speech_threshold', 0.6)
        logprob_threshold = getattr(config, 'whisper_logprob_threshold', -1.0)
    
    compression_ratio_threshold = getattr(config, 'whisper_compression_ratio_threshold', 2.4)
    
    logger.info("Whisper parameters:")
    logger.info(f"  Temperature: {temperature}")
    logger.info(f"  Beam size: {beam_size}")
    logger.info(f"  No speech threshold: {no_speech_threshold}")
    logger.info(f"  Logprob threshold: {logprob_threshold}")
    logger.info(f"  Compression ratio threshold: {compression_ratio_threshold}")
    
    # Use stage name as basename for consistent file naming (Task #5)
    # Pattern: {stage_name}_{descriptor}.{ext} (e.g., asr_segments.json)
    basename = "asr"
    
    # Check for bias windows (from pre-NER or TMDB)
    bias_windows = None
    
    # Check if bias is enabled in config
    bias_enabled = getattr(config, 'bias_enabled', True) if config else True
    bias_strategy = getattr(config, 'bias_strategy', 'global') if config else 'global'
    
    logger.info(f"Bias configuration:")
    logger.info(f"  Enabled: {bias_enabled}")
    logger.info(f"  Strategy: {bias_strategy}")
    
    if bias_enabled:
        try:
            from shared.bias_window_generator import create_bias_windows, save_bias_windows
            import soundfile as sf
            
            # Collect entity names from multiple sources
            entity_names = []
            
            # Load NER entities
            ner_file = stage_io.get_input_path("entities.json", from_stage="pre_ner")
            if ner_file.exists():
                try:
                    with open(ner_file, 'r') as f:
                        ner_data = json.load(f)
                        entities = ner_data.get('entities', [])
                        for entity in entities:
                            entity_text = entity.get('text', '').strip()
                            if entity_text:
                                entity_names.append(entity_text)
                        logger.info(f"Loaded {len(entities)} NER entities")
                except Exception as e:
                    logger.warning(f"Could not load NER data: {e}")
            
            # Load TMDB metadata for cast and character names
            # Try tmdb_data.json first (contains actual cast/crew data)
            tmdb_file = stage_io.get_input_path("tmdb_data.json", from_stage="tmdb")
            if tmdb_file.exists():
                try:
                    with open(tmdb_file, 'r') as f:
                        tmdb_data = json.load(f)
                        
                        # Add cast names - tmdb_data.json has simple string arrays
                        cast = tmdb_data.get('cast', [])
                        for name in cast[:15]:  # Top 15 cast members
                            if isinstance(name, str) and name.strip():
                                entity_names.append(name.strip())
                        
                        # Add crew names (director, writer, etc.)
                        crew = tmdb_data.get('crew', [])
                        for name in crew[:5]:  # Top 5 crew members
                            if isinstance(name, str) and name.strip():
                                entity_names.append(name.strip())
                        
                        logger.info(f"Loaded {len(cast)} cast + {len(crew)} crew from TMDB")
                except Exception as e:
                    logger.warning(f"Could not load TMDB data: {e}")
            
            # Remove duplicates and empty strings
            entity_names = list(set(filter(None, entity_names)))
            
            if entity_names:
                # Get audio duration
                audio_file = stage_io.get_input_path("audio.wav", from_stage="demux")
                try:
                    audio_data, sr = sf.read(str(audio_file))
                    duration = len(audio_data) / sr
                except Exception as e:
                    logger.warning(f"Could not read audio duration: {e}, using default 3600s")
                    duration = 3600.0  # Default to 1 hour
                
                # Get bias parameters from config
                window_seconds = getattr(config, 'bias_window_seconds', 45) if config else 45
                stride_seconds = getattr(config, 'bias_stride_seconds', 15) if config else 15
                topk = getattr(config, 'bias_topk', 10) if config else 10
                
                # Create bias windows
                logger.info(f"Creating bias windows with {len(entity_names)} unique terms")
                logger.info(f"  Window size: {window_seconds}s, Stride: {stride_seconds}s, Top-K: {topk}")
                
                bias_windows = create_bias_windows(
                    duration_seconds=duration,
                    window_seconds=window_seconds,
                    stride_seconds=stride_seconds,
                    base_terms=entity_names,
                    topk=topk
                )
                
                # Save bias windows to stage directory
                bias_dir = stage_io.stage_dir / "bias_windows"
                save_bias_windows(bias_dir, bias_windows, basename)
                
                logger.info(f"✓ Created {len(bias_windows)} bias windows")
                logger.info(f"  Bias windows saved to: {bias_dir}")
            else:
                logger.info("No entities found for bias injection, proceeding without bias")
        
        except Exception as e:
            logger.warning(f"Bias window generation failed: {e}")
            logger.warning("Proceeding without bias injection")
            bias_windows = None
    else:
        logger.info("Bias injection disabled in configuration")
    
    try:
        # Run WhisperX pipeline
        logger.info("Starting WhisperX transcription...")
        result = run_whisperx_pipeline(
            audio_file=str(audio_file),
            output_dir=stage_io.stage_dir,
            basename=basename,
            source_lang=source_lang,
            target_lang=target_lang,
            bias_windows=bias_windows,
            model_name=model_name,
            device=device,
            compute_type=compute_type,
            hf_token=hf_token,
            logger=logger,
            bias_strategy=bias_strategy,
            backend=backend,
            workflow_mode=workflow_mode,
            temperature=temperature,
            beam_size=beam_size,
            no_speech_threshold=no_speech_threshold,
            logprob_threshold=logprob_threshold,
            compression_ratio_threshold=compression_ratio_threshold
        )
        
        logger.info(f"✓ ASR completed successfully")
        logger.info(f"  Segments: {len(result.get('segments', []))}")
        
        # Track outputs in manifest
        segments_file = output_dir / f"{basename}.json"
        if segments_file.exists():
            stage_io.track_output(segments_file, "transcript",
                                 format="json",
                                 segments=len(result.get('segments', [])),
                                 language=source_lang)
        
        # Track translation if it exists
        translation_file = output_dir / f"{basename}.{target_lang}.json"
        if translation_file.exists():
            stage_io.track_output(translation_file, "transcript",
                                 format="json",
                                 language=target_lang)
        
        # Finalize manifest with success
        stage_io.finalize(status="success",
                         segments_count=len(result.get('segments', [])),
                         model=model_name,
                         backend=backend)
        
        logger.info("=" * 60)
        logger.info("ASR STAGE COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
        logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}", exc_info=True)
        stage_io.add_error(f"File not found: {e}")
        stage_io.finalize(status="failed", error=str(e))
        return 1
    
    except IOError as e:
        logger.error(f"I/O error: {e}", exc_info=True)
        stage_io.add_error(f"I/O error: {e}")
        stage_io.finalize(status="failed", error=str(e))
        return 1
    
    except RuntimeError as e:
        logger.error(f"WhisperX runtime error: {e}", exc_info=True)
        stage_io.add_error(f"WhisperX error: {e}")
        stage_io.finalize(status="failed", error=str(e))
        return 1
    
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        stage_io.add_error("User interrupted")
        stage_io.finalize(status="failed", error="Interrupted")
        return 130
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        stage_io.add_error(f"Unexpected error: {e}")
        stage_io.finalize(status="failed", error=str(e))
        return 1


if __name__ == "__main__":
    import sys
    import gc
    try:
        exit_code = main()
    finally:
        # Clean up resources to avoid semaphore leaks
        gc.collect()
        try:
            import torch
            if hasattr(torch, 'mps') and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except:
            pass
    sys.exit(exit_code)
