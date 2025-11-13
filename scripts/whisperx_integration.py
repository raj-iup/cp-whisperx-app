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

import os
# Fix OpenMP duplicate library issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import json
import warnings
from pathlib import Path
from typing import List, Dict, Optional, Any
from tqdm import tqdm

# Suppress version mismatch warnings
warnings.filterwarnings('ignore', message='Model was trained with pyannote')
warnings.filterwarnings('ignore', message='Model was trained with torch')
warnings.filterwarnings('ignore', category=UserWarning, module='pyannote')
warnings.filterwarnings('ignore', message='.*torchaudio._backend.list_audio_backends.*')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='torchaudio')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='speechbrain')

from device_selector import select_whisperx_device, validate_device_and_compute_type
from bias_injection import BiasWindow, get_window_for_time
from mps_utils import cleanup_mps_memory, log_mps_memory, optimize_batch_size_for_mps
from asr_chunker import ChunkedASRProcessor
import sys
from pathlib import Path

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.logger import PipelineLogger
from whisper_backends import create_backend, get_recommended_backend


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
        condition_on_previous_text: bool = True,
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

    def _create_default_logger(self):
        """Create default logger if none provided"""
        from shared.logger import PipelineLogger
        return PipelineLogger("whisperx")

    def load_model(self):
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
            self.logger
        )
        
        if not self.backend:
            raise RuntimeError(f"Failed to create backend: {backend_to_use}")
        
        # Load model
        success = self.backend.load_model()
        if not success:
            raise RuntimeError(f"Failed to load model with backend: {self.backend.name}")
        
        # Update device to actual device used (may have fallen back)
        self.device = self.backend.device
        self.logger.info(f"  ✓ Model loaded with backend: {self.backend.name}")
        self.logger.info(f"  ✓ Active device: {self.device}")

    def load_align_model(self, language: str):
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
    
    def cleanup(self):
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

    def transcribe_with_bias(
        self,
        audio_file: str,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[List[BiasWindow]] = None,
        batch_size: int = 16,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Transcribe and translate audio with bias prompt injection.
        
        Uses chunked processing for MPS devices or long files for stability.
        Passes bias prompts actively to WhisperX (not just metadata).

        Args:
            audio_file: Path to audio/video file
            source_lang: Source language (e.g., "hi")
            target_lang: Target language (e.g., "en")
            bias_windows: List of bias windows for prompt injection
            batch_size: Batch size for inference
            output_dir: Output directory for checkpoints (required for chunking)

        Returns:
            Whisper result dict with segments and word-level timestamps
        """
        self.logger.info(f"Transcribing: {audio_file}")
        self.logger.info(f"  Source: {source_lang}, Target: {target_lang}")
        self.logger.info(f"  Backend: {self.backend.name}")

        if not self.backend:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Optimize batch size for MPS
        original_batch_size = batch_size
        batch_size = optimize_batch_size_for_mps(batch_size, self.backend.device, 'large')
        if batch_size != original_batch_size:
            self.logger.info(f"  🎯 MPS optimization: batch_size {original_batch_size} → {batch_size}")

        # Determine task
        task = "translate" if source_lang != target_lang else "transcribe"
        
        # Determine if chunking should be used
        audio_duration = self._get_audio_duration(audio_file)
        use_chunking = (
            self.backend.device == 'mps' or  # Always chunk for MPS stability
            audio_duration > 600  # Always chunk if > 10 minutes
        )
        
        if use_chunking:
            self.logger.info(f"  📦 Using chunked processing (duration={audio_duration:.0f}s, device={self.backend.device})")
            return self._transcribe_chunked(
                audio_file, source_lang, task, 
                bias_windows, batch_size, output_dir
            )
        else:
            self.logger.info(f"  🚀 Using whole-file processing (duration={audio_duration:.0f}s)")
            return self._transcribe_whole(
                audio_file, source_lang, task,
                bias_windows, batch_size
            )
    
    def _get_audio_duration(self, audio_file: str) -> float:
        """Get audio duration in seconds"""
        import whisperx
        audio = whisperx.load_audio(audio_file)
        return len(audio) / 16000  # 16kHz sample rate
    
    def _transcribe_whole(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[List[BiasWindow]],
        batch_size: int
    ) -> Dict[str, Any]:
        """Whole-file transcription with global bias prompting (for short files or CPU)"""
        
        # Create global bias prompts from bias windows
        initial_prompt = None
        hotwords = None
        
        if bias_windows:
            self.logger.info(f"  Bias windows available: {len(bias_windows)}")
            
            # Collect all unique bias terms across windows
            all_terms = set()
            for window in bias_windows:
                all_terms.update(window.bias_terms)
            
            # Create global bias prompts
            top_terms = list(all_terms)[:50]  # Limit to top 50 terms
            
            if top_terms:
                # initial_prompt: first 20 terms as context (comma-separated sentence)
                initial_prompt = ", ".join(top_terms[:20])
                
                # hotwords: all 50 terms (comma-separated, no spaces for faster-whisper)
                hotwords = ",".join(top_terms)
                
                self.logger.info(f"  🎯 Active bias prompting enabled:")
                self.logger.info(f"    Initial prompt: {len(top_terms[:20])} terms")
                self.logger.info(f"    Hotwords: {len(top_terms)} terms")
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
            result = self.backend.transcribe(
                audio_file,
                language=source_lang,
                task=task,
                batch_size=batch_size,
                initial_prompt=initial_prompt,
                hotwords=hotwords
            )
            self.logger.info(f"  ✓ Transcription complete: {len(result.get('segments', []))} segments")
        except Exception as e:
            self.logger.error(f"  ✗ Transcription failed: {e}")
            raise
        finally:
            # Always cleanup MPS memory
            cleanup_mps_memory(self.logger)
            log_mps_memory(self.logger, "  After transcription - ")

        # Apply bias window metadata to segments (for reference)
        if bias_windows:
            result = self._apply_bias_context(result, bias_windows)

        return result
    
    def _transcribe_chunked(
        self,
        audio_file: str,
        source_lang: str,
        task: str,
        bias_windows: Optional[List[BiasWindow]],
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
        
        # Create chunks
        chunks = chunker.create_chunks(audio_file, bias_windows)
        
        # Process each chunk with checkpointing
        chunk_results = []
        checkpoint_dir = output_dir / 'chunks'
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
                    self.logger.error(f"    ✗ Chunk {chunk.chunk_id} failed: {e}")
                    # Continue with other chunks, partial results better than none
                    continue
        
        # Merge all chunks
        self.logger.info(f"  Merging {len(chunk_results)} processed chunks...")
        merged_result = chunker.merge_chunk_results(chunk_results)
        
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
        from mps_utils import retry_with_degradation
        
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
        bias_windows: List[BiasWindow]
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

    def align_segments(
        self,
        result: Dict[str, Any],
        audio_file: str,
        target_lang: str
    ) -> Dict[str, Any]:
        """
        Add word-level alignment to segments

        Args:
            result: Whisper transcription result
            audio_file: Path to audio/video file
            target_lang: Target language for alignment

        Returns:
            Result with word-level timestamps
        """
        if not self.backend:
            self.logger.warning("Backend not loaded, skipping alignment")
            return result

        self.logger.info("Aligning segments for word-level timestamps...")

        try:
            aligned_result = self.backend.align_segments(
                result.get("segments", []),
                audio_file,
                target_lang
            )
            self.logger.info("  ✓ Alignment complete")
            return aligned_result

        except Exception as e:
            self.logger.warning(f"  ⚠ Alignment failed: {e}")
            return result

    def save_results(
        self,
        result: Dict[str, Any],
        output_dir: Path,
        basename: str
    ):
        """
        Save WhisperX results to output directory

        Args:
            result: WhisperX result
            output_dir: Output directory (e.g., out/Movie/asr/)
            basename: Base filename
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save full JSON result with basename
        json_file = output_dir / f"{basename}.whisperx.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save segments as JSON (cleaner format) with basename
        segments_file = output_dir / f"{basename}.segments.json"
        segments = result.get("segments", [])
        with open(segments_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {segments_file}")

        # Save as plain text transcript with basename
        txt_file = output_dir / f"{basename}.transcript.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    f.write(f"{text}\n")
        self.logger.info(f"  Saved: {txt_file}")

        # Save as SRT with basename
        srt_file = output_dir / f"{basename}.srt"
        self._save_as_srt(segments, srt_file)
        self.logger.info(f"  Saved: {srt_file}")
        
        # ALSO save with standard names for downstream stages
        # These are the filenames that other stages expect
        standard_json = output_dir / "transcript.json"
        with open(standard_json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        standard_segments = output_dir / "segments.json"
        with open(standard_segments, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)

    def _save_as_srt(self, segments: List[Dict], srt_file: Path):
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
    bias_windows: Optional[List[BiasWindow]],
    model_name: str,
    device: str,
    compute_type: str,
    hf_token: Optional[str],
    logger: Optional[PipelineLogger] = None
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

    Returns:
        WhisperX result dict
    """
    processor = WhisperXProcessor(
        model_name=model_name,
        device=device,
        compute_type=compute_type,
        hf_token=hf_token,
        logger=logger
    )

    try:
        # Load models
        processor.load_model()
        processor.load_align_model(target_lang)

        # Transcribe with bias
        result = processor.transcribe_with_bias(
            audio_file,
            source_lang,
            target_lang,
            bias_windows,
            output_dir=output_dir  # Pass output_dir for checkpointing
        )

        # Align for word-level timestamps
        result = processor.align_segments(result, audio_file, target_lang)

        # Save results
        processor.save_results(result, output_dir, basename)

        return result
    finally:
        # Clean up resources
        processor.cleanup()


def main():
    """Main entry point for WhisperX ASR stage."""
    import sys
    import os
    import json
    from pathlib import Path
    from shared.stage_utils import StageIO, get_stage_logger
    from shared.config import load_config
    
    # Set up stage I/O and logging
    stage_io = StageIO("asr")
    logger = get_stage_logger("asr", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("ASR STAGE: Automatic Speech Recognition")
    logger.info("=" * 60)
    
    # Get output directory from StageIO
    output_dir = stage_io.output_base
    
    # Load configuration
    config_path_env = os.environ.get('CONFIG_PATH')
    if config_path_env:
        logger.debug(f"Loading configuration from: {config_path_env}")
        config = load_config(config_path_env)
    else:
        logger.warning("No config path specified, using defaults")
        config = None
    
    # Get audio file from demux stage
    audio_file = stage_io.get_input_path("audio.wav", from_stage="demux")
    if not audio_file.exists():
        logger.error(f"Audio file not found: {audio_file}")
        return 1
    
    logger.info(f"Input audio: {audio_file}")
    logger.info(f"Input audio: {audio_file}")
    logger.info(f"Output directory: {output_dir}")
    
    # Get configuration parameters
    model_name = getattr(config, 'whisper_model', 'large-v3') if config else 'large-v3'
    source_lang = getattr(config, 'whisper_language', 'hi') if config else 'hi'
    target_lang = getattr(config, 'target_language', 'en') if config else 'en'
    device = os.environ.get('DEVICE_OVERRIDE', getattr(config, 'device', 'cpu') if config else 'cpu').lower()
    compute_type = getattr(config, 'whisper_compute_type', 'float16') if config else 'float16'
    
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
    
    if not hf_token:
        hf_token = os.environ.get('HF_TOKEN')
    
    logger.info(f"Model: {model_name}")
    logger.info(f"Source language: {source_lang}")
    logger.info(f"Target language: {target_lang}")
    logger.info(f"Device: {device}")
    logger.info(f"Compute type: {compute_type}")
    
    # Get basename from config or use default
    basename = getattr(config, 'job_id', 'transcript') if config else 'transcript'
    
    # Check for bias windows (from pre-NER or TMDB)
    bias_windows = None
    
    # Check if bias is enabled in config
    bias_enabled = getattr(config, 'bias_enabled', True) if config else True
    
    if bias_enabled:
        try:
            from bias_injection import create_bias_windows, save_bias_windows
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
            logger=logger
        )
        
        logger.info(f"✓ ASR completed successfully")
        logger.info(f"  Segments: {len(result.get('segments', []))}")
        logger.info("=" * 60)
        logger.info("ASR STAGE COMPLETED")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"WhisperX pipeline failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
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
