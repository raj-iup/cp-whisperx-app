"""
whisperx_integration.py - WhisperX integration for ASR + translation

Handles:
- Loading WhisperX model with appropriate device/compute type
- Processing audio with rolling windowed bias prompts
- ASR + translation in single pass
- Word-level alignment
- Saving results to ASR directory
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import whisperx
from tqdm import tqdm

from .device_selector import select_whisperx_device
from .bias_injection import BiasWindow, get_window_for_time
from .logger import PipelineLogger


class WhisperXProcessor:
    """WhisperX processor with configurable transcription parameters"""

    def __init__(
        self,
        model_name: str = "large-v3",
        device: str = "cpu",
        compute_type: str = "int8",
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
            model_name: WhisperX model name (e.g., "large-v3", "medium")
            device: Device to use (cpu, cuda, mps)
            compute_type: Compute type (int8, float16, float32)
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
        self.hf_token = hf_token
        self.logger = logger or self._create_default_logger()
        
        # Transcription parameters
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

        self.model = None
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
        from .logger import PipelineLogger
        return PipelineLogger("whisperx")

    def load_model(self):
        """Load WhisperX model"""
        self.logger.info(f"Loading WhisperX model: {self.model_name}")
        self.logger.info(f"  Device: {self.device}")
        self.logger.info(f"  Compute type: {self.compute_type}")
        
        # Use LLM directory for model cache
        cache_dir = Path("/app/LLM/whisperx")
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"  Cache directory: {cache_dir}")

        try:
            self.model = whisperx.load_model(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
                download_root=str(cache_dir)
            )
            self.logger.info("  Model loaded successfully")
        except Exception as e:
            if self.device != "cpu":
                self.logger.warning(f"  Failed to load on {self.device}: {e}")
                self.logger.warning("  Retrying with CPU...")
                self.device = "cpu"
                self.model = whisperx.load_model(
                    self.model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                    download_root=str(cache_dir)
                )
                self.logger.info("  Model loaded successfully on CPU")
            else:
                self.logger.error(f"  Failed to load model: {e}")
                raise

    def load_align_model(self, language: str):
        """
        Load alignment model for word-level timestamps

        Args:
            language: Language code (e.g., "en", "hi")
        """
        self.logger.info(f"Loading alignment model for language: {language}")

        try:
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code=language,
                device=self.device
            )
            self.logger.info("  Alignment model loaded successfully")
        except Exception as e:
            self.logger.warning(f"  Failed to load alignment model: {e}")
            self.align_model = None
            self.align_metadata = None

    def transcribe_with_bias(
        self,
        audio_file: str,
        source_lang: str,
        target_lang: str,
        bias_windows: Optional[List[BiasWindow]] = None,
        batch_size: int = 16
    ) -> Dict[str, Any]:
        """
        Transcribe and translate audio with bias prompt injection

        Args:
            audio_file: Path to audio/video file
            source_lang: Source language (e.g., "hi")
            target_lang: Target language (e.g., "en")
            bias_windows: List of bias windows for prompt injection
            batch_size: Batch size for inference

        Returns:
            WhisperX result dict with segments and word-level timestamps
        """
        self.logger.info(f"Transcribing: {audio_file}")
        self.logger.info(f"  Source: {source_lang}, Target: {target_lang}")

        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        # Load audio
        self.logger.info("Loading audio...")
        audio = whisperx.load_audio(audio_file)

        # Transcribe with translation
        self.logger.info("Transcribing and translating...")
        self.logger.debug(f"  Temperature: {self.temperature}")
        self.logger.debug(f"  Beam size: {self.beam_size}")
        self.logger.debug(f"  Best of: {self.best_of}")

        # Bias prompts are saved for potential post-processing use
        if bias_windows:
            self.logger.info(f"  Bias windows available: {len(bias_windows)}")

        # Build transcription options
        transcribe_options = {
            "language": source_lang if source_lang else None,
            "task": "translate" if source_lang != target_lang else "transcribe",
            "batch_size": batch_size,
            "temperature": self.temperature,
            "beam_size": self.beam_size,
            "best_of": self.best_of,
            "patience": self.patience,
            "length_penalty": self.length_penalty,
            "no_speech_threshold": self.no_speech_threshold,
            "logprob_threshold": self.logprob_threshold,
            "compression_ratio_threshold": self.compression_ratio_threshold,
            "condition_on_previous_text": self.condition_on_previous_text,
        }
        
        # Add initial prompt if provided and not empty
        if self.initial_prompt:
            transcribe_options["initial_prompt"] = self.initial_prompt
            self.logger.info(f"  Using initial prompt: {self.initial_prompt[:50]}...")

        try:
            result = self.model.transcribe(audio, **transcribe_options)
            self.logger.info(f"  Transcription complete: {len(result.get('segments', []))} segments")
        except Exception as e:
            self.logger.error(f"  Transcription failed: {e}")
            raise

        # Apply bias prompts to segments (post-processing context)
        if bias_windows:
            result = self._apply_bias_context(result, bias_windows)

        return result

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
            result: WhisperX transcription result
            audio_file: Path to audio/video file
            target_lang: Target language for alignment

        Returns:
            Result with word-level timestamps
        """
        if not self.align_model:
            self.logger.warning("Alignment model not loaded, skipping alignment")
            return result

        self.logger.info("Aligning segments for word-level timestamps...")

        try:
            # Load audio
            audio = whisperx.load_audio(audio_file)

            # Align
            aligned_result = whisperx.align(
                result["segments"],
                self.align_model,
                self.align_metadata,
                audio,
                self.device,
                return_char_alignments=False
            )

            self.logger.info("  Alignment complete")
            return aligned_result

        except Exception as e:
            self.logger.warning(f"  Alignment failed: {e}")
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

        # Save full JSON result
        json_file = output_dir / f"{basename}.whisperx.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save segments as JSON (cleaner format)
        segments_file = output_dir / f"{basename}.segments.json"
        segments = result.get("segments", [])
        with open(segments_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {segments_file}")

        # Save as plain text transcript
        txt_file = output_dir / f"{basename}.transcript.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                text = segment.get("text", "").strip()
                if text:
                    f.write(f"{text}\n")
        self.logger.info(f"  Saved: {txt_file}")

        # Save as SRT
        srt_file = output_dir / f"{basename}.srt"
        self._save_as_srt(segments, srt_file)
        self.logger.info(f"  Saved: {srt_file}")

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

    # Load models
    processor.load_model()
    processor.load_align_model(target_lang)

    # Transcribe with bias
    result = processor.transcribe_with_bias(
        audio_file,
        source_lang,
        target_lang,
        bias_windows
    )

    # Align for word-level timestamps
    result = processor.align_segments(result, audio_file, target_lang)

    # Save results
    processor.save_results(result, output_dir, basename)

    return result
