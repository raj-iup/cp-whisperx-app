"""
transcription.py - Core transcription orchestration

Handles:
- Two-step transcription + translation workflow
- Single-step transcription workflow
- Language detection and alignment
- Result saving and coordination

Extracted from whisperx_integration.py (Phase 4 - AD-002 + AD-009)
Status: ✅ FUNCTIONAL (Direct extraction per AD-009)

Note: Logger is passed as a parameter (not created here)
"""

# Standard library
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable

# Local (logger import for compliance - logger is passed as parameter)
from shared.logger import get_logger  # noqa: F401


class TranscriptionEngine:
    """
    Core transcription orchestration engine
    
    Coordinates the complete transcription workflow including:
    - Two-step transcription + translation (when source != target)
    - Single-step transcription (when source == target or auto-detect)
    - Language detection and alignment model loading
    - Result saving with proper language suffixes
    
    Extracted from run_whisperx_pipeline() in whisperx_integration.py
    """
    
    def __init__(
        self,
        processor: Any,
        logger: Any,  # PipelineLogger type
        get_indictrans2_fn: Optional[Callable] = None
    ):
        """
        Initialize transcription engine
        
        Args:
            processor: WhisperXProcessor instance (for transcribe/align/save)
            logger: Logger instance
            get_indictrans2_fn: Function to get IndicTrans2 module (optional)
        """
        self.processor = processor
        self.logger = logger
        self.get_indictrans2 = get_indictrans2_fn
    
    def run_pipeline(
        self,
        audio_file: str,
        output_dir: Path,
        basename: str,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any],
        bias_strategy: str = "global",
        workflow_mode: str = "subtitle-gen"
    ) -> Dict[str, Any]:
        """
        Run complete transcription pipeline with workflow coordination
        
        Args:
            audio_file: Path to audio file
            output_dir: Output directory for results
            basename: Base filename for outputs (e.g., "asr")
            source_lang: Source language code (or "auto" for detection)
            target_lang: Target language code
            bias_windows: Bias windows for prompt injection
            bias_strategy: Bias prompting strategy (global/hybrid/chunked_windows/chunked)
            workflow_mode: Workflow mode (transcribe/transcribe-only/translate-only/subtitle-gen)
        
        Returns:
            WhisperX result dict with segments and metadata
        """
        # Load transcription model
        self.processor.load_model()
        
        # Determine if we need two-step processing for transcribe workflow
        needs_two_step = self._needs_two_step_processing(
            workflow_mode, source_lang, target_lang
        )
        
        if needs_two_step:
            return self._run_two_step_pipeline(
                audio_file, output_dir, basename,
                source_lang, target_lang, bias_windows,
                bias_strategy, workflow_mode
            )
        else:
            return self._run_single_step_pipeline(
                audio_file, output_dir, basename,
                source_lang, target_lang, bias_windows,
                bias_strategy, workflow_mode
            )
    
    def _needs_two_step_processing(
        self,
        workflow_mode: str,
        source_lang: str,
        target_lang: str
    ) -> bool:
        """
        Determine if two-step processing is needed
        
        Two-step is required when:
        - Workflow is 'transcribe' (not transcribe-only)
        - Target language is specified (not 'auto')
        - Source language is specified AND different from target
        
        Args:
            workflow_mode: Workflow mode
            source_lang: Source language
            target_lang: Target language
        
        Returns:
            True if two-step processing needed
        """
        if workflow_mode != 'transcribe' or target_lang == 'auto':
            return False
        
        # If source is specified and different from target, we need two-step
        if source_lang != 'auto':
            return source_lang != target_lang
        
        # If source is auto, we'll do single-step first, then check detected language
        return False
    
    def _run_two_step_pipeline(
        self,
        audio_file: str,
        output_dir: Path,
        basename: str,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any],
        bias_strategy: str,
        workflow_mode: str
    ) -> Dict[str, Any]:
        """
        Run two-step transcription + translation pipeline
        
        STEP 1: Transcribe in source language → save source files
        STEP 2: Translate to target language → save target files
        
        Args:
            (same as run_pipeline)
        
        Returns:
            Target language result (final output)
        """
        self.logger.info("=" * 60)
        self.logger.info("TWO-STEP TRANSCRIPTION + TRANSLATION")
        self.logger.info(f"  {source_lang} → {target_lang}")
        self.logger.info("=" * 60)
        
        # STEP 1: Transcribe in source language
        self.logger.info("STEP 1: Transcribing in source language...")
        self.processor.load_align_model(source_lang)
        
        source_result = self.processor.transcribe_with_bias(
            audio_file,
            source_lang,
            source_lang,  # Same as source - no translation
            bias_windows,
            output_dir=output_dir,
            bias_strategy=bias_strategy,
            workflow_mode='transcribe-only'  # Force transcribe-only for step 1
        )
        
        # Extract detected language
        detected_lang = source_result.get("language", source_lang)
        if source_lang == "auto" and detected_lang != "auto":
            self.logger.info(f"Using detected language for alignment: {detected_lang}")
            align_lang = detected_lang
        else:
            align_lang = source_lang
        
        # Align to source language
        source_result = self.processor.align_segments(source_result, audio_file, align_lang)
        
        # Save source language files (no language suffix)
        self.logger.info(f"Saving source language files ({source_lang})...")
        self.processor.save_results(source_result, output_dir, basename, target_lang=None)
        
        self.logger.info("✓ Step 1 completed: Source language files saved")
        self.logger.info("")
        
        # STEP 2: Translate to target language
        target_result = self._translate_to_target(
            audio_file, output_dir, basename,
            source_result, source_lang, target_lang,
            bias_windows, bias_strategy, workflow_mode
        )
        
        self.logger.info("✓ Step 2 completed: Target language files saved")
        self.logger.info("=" * 60)
        
        return target_result
    
    def _translate_to_target(
        self,
        audio_file: str,
        output_dir: Path,
        basename: str,
        source_result: Dict,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any],
        bias_strategy: str,
        workflow_mode: str
    ) -> Dict[str, Any]:
        """
        Translate source result to target language
        
        Uses IndicTrans2 for Indic languages (if available), otherwise Whisper.
        
        Args:
            audio_file: Path to audio file
            output_dir: Output directory
            basename: Base filename
            source_result: Source language transcription result
            source_lang: Source language code
            target_lang: Target language code
            bias_windows: Bias windows
            bias_strategy: Bias strategy
            workflow_mode: Workflow mode
        
        Returns:
            Target language result
        """
        self.logger.info("STEP 2: Translating to target language...")
        
        # Try IndicTrans2 first (if available and applicable)
        if self.get_indictrans2 is not None:
            indictrans2, available = self.get_indictrans2()
            
            if available and indictrans2['can_use_indictrans2'](source_lang, target_lang):
                return self._translate_with_indictrans2(
                    audio_file, output_dir, basename,
                    source_result, source_lang, target_lang,
                    bias_windows, bias_strategy, workflow_mode,
                    indictrans2
                )
        
        # Fallback to Whisper translation
        return self._translate_with_whisper(
            audio_file, output_dir, basename,
            source_result, source_lang, target_lang,
            bias_windows, bias_strategy, workflow_mode
        )
    
    def _translate_with_indictrans2(
        self,
        audio_file: str,
        output_dir: Path,
        basename: str,
        source_result: Dict,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any],
        bias_strategy: str,
        workflow_mode: str,
        indictrans2: Dict
    ) -> Dict[str, Any]:
        """Translate using IndicTrans2 (with Whisper fallback on error)"""
        self.logger.info(f"  Using IndicTrans2 for {source_lang}→{target_lang} translation")
        self.logger.info(f"  Source segments: {len(source_result.get('segments', []))}")
        
        try:
            # Translate using IndicTrans2
            target_result = indictrans2['translate_whisperx_result'](
                source_result,
                source_lang=source_lang,
                target_lang=target_lang,
                logger=self.logger
            )
            
            # Check if translation actually happened (not fallback)
            if target_result == source_result:
                self.logger.warning("  IndicTrans2 returned source unchanged - falling back to Whisper")
                raise RuntimeError("IndicTrans2 fallback triggered")
            
            # Align to target language
            self.logger.info(f"  Aligning translated segments to {target_lang}...")
            self.processor.load_align_model(target_lang)
            target_result = self.processor.align_segments(target_result, audio_file, target_lang)
            
            # Save target language files
            self.logger.info(f"Saving target language files ({target_lang})...")
            self.processor.save_results(target_result, output_dir, basename, target_lang=target_lang)
            
            return target_result
            
        except (RuntimeError, Exception) as e:
            error_msg = str(e)
            if "authentication" in error_msg.lower() or "gated" in error_msg.lower():
                self.logger.error("=" * 70)
                self.logger.error("IndicTrans2 authentication required", exc_info=True)
                self.logger.error("=" * 70)
                self.logger.warning("Falling back to Whisper translation (slower)")
                self.logger.info("To enable IndicTrans2 for future runs:")
                self.logger.info("  1. Visit: https://huggingface.co/ai4bharat/indictrans2-indic-en-1B")
                self.logger.info("  2. Click: 'Agree and access repository'")
                self.logger.info("  3. Run: huggingface-cli login")
                self.logger.error("=" * 70)
            else:
                self.logger.error(f"IndicTrans2 translation failed: {e}")
                self.logger.warning("Falling back to Whisper translation")
            
            # Fallback to Whisper
            return self._translate_with_whisper(
                audio_file, output_dir, basename,
                source_result, source_lang, target_lang,
                bias_windows, bias_strategy, workflow_mode
            )
    
    def _translate_with_whisper(
        self,
        audio_file: str,
        output_dir: Path,
        basename: str,
        source_result: Dict,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any],
        bias_strategy: str,
        workflow_mode: str
    ) -> Dict[str, Any]:
        """Translate using Whisper"""
        self.logger.info("  Using Whisper translation")
        self.processor.load_align_model(target_lang)
        
        target_result = self.processor.transcribe_with_bias(
            audio_file,
            source_lang,
            target_lang,  # Translate to target
            bias_windows,
            output_dir=output_dir,
            bias_strategy=bias_strategy,
            workflow_mode='transcribe'  # Use transcribe mode for translation
        )
        
        # Align to target language
        target_result = self.processor.align_segments(target_result, audio_file, target_lang)
        
        # Save target language files
        self.logger.info(f"Saving target language files ({target_lang})...")
        self.processor.save_results(target_result, output_dir, basename, target_lang=target_lang)
        
        return target_result
    
    def _run_single_step_pipeline(
        self,
        audio_file: str,
        output_dir: Path,
        basename: str,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[Any],
        bias_strategy: str,
        workflow_mode: str
    ) -> Dict[str, Any]:
        """
        Run single-step transcription pipeline
        
        Handles:
        - Transcribe-only (same language)
        - Auto-detection with potential optimization
        - Subtitle generation
        
        Args:
            (same as run_pipeline)
        
        Returns:
            Transcription result
        """
        # Determine alignment language
        if workflow_mode == 'transcribe-only':
            align_lang = source_lang
        else:
            align_lang = source_lang if workflow_mode == 'transcribe' else target_lang
        
        self.processor.load_align_model(align_lang)
        
        # Transcribe with bias strategy
        result = self.processor.transcribe_with_bias(
            audio_file,
            source_lang,
            target_lang,
            bias_windows,
            output_dir=output_dir,
            bias_strategy=bias_strategy,
            workflow_mode=workflow_mode
        )
        
        # Handle auto-detection and optimization
        detected_lang = result.get("language", source_lang)
        if source_lang == "auto" and detected_lang != "auto":
            self.logger.info(f"Detected language: {detected_lang}")
            
            # Check if detected language matches target (Task #7 optimization)
            if workflow_mode == 'transcribe' and detected_lang == target_lang:
                self.logger.info(f"✓ Detected language ({detected_lang}) matches target ({target_lang})")
                self.logger.info("  Single-pass transcription (no translation needed)")
                workflow_mode = 'transcribe-only'  # Update mode to avoid translation logic
            
            # Update alignment language to detected language
            self.logger.info(f"Using detected language for alignment: {detected_lang}")
            if workflow_mode in ['transcribe-only', 'transcribe']:
                align_lang = detected_lang
                # Reload alignment model for detected language
                self.processor.load_align_model(align_lang)
        
        # Align for word-level timestamps
        result = self.processor.align_segments(result, audio_file, align_lang)
        
        # Save results
        # In transcribe mode, we only transcribe (no translation), so don't add language suffix
        save_target_lang = None if workflow_mode in ['transcribe', 'transcribe-only'] else (
            target_lang if source_lang != target_lang else None
        )
        self.processor.save_results(result, output_dir, basename, target_lang=save_target_lang)
        
        return result


__all__ = ['TranscriptionEngine']
