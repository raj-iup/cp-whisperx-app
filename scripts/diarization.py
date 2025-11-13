"""
diarization.py - Speaker diarization using pyannote-audio

Handles:
- Loading pyannote diarization model
- Running speaker diarization on audio
- Assigning speaker labels to transcript segments
- Optional speaker name mapping
- Saving diarized results
"""

import sys
import warnings
from pathlib import Path

# Suppress deprecation warnings
warnings.filterwarnings('ignore', message='.*torchaudio._backend.list_audio_backends.*')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='pyannote')
warnings.filterwarnings('ignore', message='.*has been deprecated.*', module='torchaudio')

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import json
from typing import List, Dict, Optional, Any
import whisperx
from pyannote.audio import Pipeline
from shared.logger import PipelineLogger


class DiarizationProcessor:
    """Speaker diarization processor"""

    def __init__(
        self,
        hf_token: str,
        device: str = "cpu",
        model_name: str = "pyannote/speaker-diarization-3.1",
        logger: Optional[PipelineLogger] = None
    ):
        """
        Initialize diarization processor

        Args:
            hf_token: Hugging Face token for pyannote model access
            device: Device to use (cpu, cuda, mps)
            model_name: Pyannote model to use
            logger: Logger instance
        """
        self.hf_token = hf_token
        self.device = device
        self.model_name = model_name
        self.logger = logger or self._create_default_logger()
        self.diarize_model = None

    def _create_default_logger(self):
        """Create default logger if none provided"""
        from shared.logger import PipelineLogger
        return PipelineLogger("diarization")

    def load_model(self):
        """Load pyannote diarization model"""
        import torch
        
        self.logger.info("Loading pyannote diarization model...")
        self.logger.info(f"  Model: {self.model_name}")
        self.logger.info(f"  Device requested: {self.device}")

        # Auto-detect best available device if needed
        original_device = self.device
        if self.device.lower() in ["auto", "cpu", ""]:
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = "mps"
                self.logger.info("  Auto-detected MPS (Apple Silicon GPU)")
            elif torch.cuda.is_available():
                self.device = "cuda"
                self.logger.info("  Auto-detected CUDA GPU")
            else:
                self.device = "cpu"
                self.logger.info("  No GPU detected, using CPU")
        elif self.device.upper() == "MPS" and not torch.backends.mps.is_available():
            self.logger.warning("  MPS not available on this system")
            if torch.cuda.is_available():
                self.device = "cuda"
                self.logger.info(f"  Falling back to CUDA")
            else:
                self.device = "cpu"
                self.logger.warning("  Falling back to CPU (will be slow!)")
        elif self.device.upper() == "CUDA" and not torch.cuda.is_available():
            self.logger.warning("  CUDA not available on this system")
            self.device = "cpu"
            self.logger.warning("  Falling back to CPU (will be slow!)")
        
        if self.device == "cpu":
            self.logger.warning("  ⚠️  Running diarization on CPU is VERY SLOW")
            self.logger.warning("  ⚠️  This may take hours for long audio files")
            self.logger.warning("  ⚠️  Consider using GPU acceleration or Docker mode")

        try:
            # Use pyannote.audio Pipeline directly
            self.diarize_model = Pipeline.from_pretrained(
                self.model_name,
                use_auth_token=self.hf_token
            )
            # Move to specified device
            if self.device != "cpu":
                try:
                    # Convert device string to torch.device object
                    device_obj = torch.device(self.device.lower())
                    self.diarize_model.to(device_obj)
                    self.logger.info(f"  ✓ Diarization model moved to {self.device.upper()}")
                    if self.device.lower() == 'mps':
                        self.logger.info("    → Using Metal Performance Shaders (Apple Silicon)")
                    elif self.device.lower() == 'cuda':
                        self.logger.info("    → Using NVIDIA CUDA acceleration")
                except Exception as e:
                    self.logger.warning(f"  Could not move to {self.device}: {e}")
                    self.logger.warning("  Using CPU instead (will be slow!)")
                    self.device = "cpu"
            else:
                self.logger.info("  Diarization running on CPU")
                
            self.logger.info("  Diarization model loaded successfully")
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"  Failed to load diarization model: {e}")
            
            # Check for HuggingFace authentication errors
            if "401" in error_msg or "expired" in error_msg.lower() or "unauthorized" in error_msg.lower():
                self.logger.error("  ✗ HuggingFace token is invalid or expired")
                self.logger.error("  → Get a new token from: https://huggingface.co/settings/tokens")
                self.logger.error("  → Accept model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
                self.logger.error("  → Set HF_TOKEN environment variable or update config/.env.pipeline")
            elif "repository not found" in error_msg.lower() or "404" in error_msg:
                self.logger.error("  ✗ Model not found or not accessible")
                self.logger.error("  → Make sure you have accepted the model terms at:")
                self.logger.error("  → https://huggingface.co/pyannote/speaker-diarization-3.1")
            
            raise RuntimeError(f"Diarization model initialization failed - see errors above") from e

    def diarize_audio(
        self,
        audio_file: str,
        min_speakers: Optional[int] = None,
        max_speakers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Run speaker diarization on audio file

        Args:
            audio_file: Path to audio/video file
            min_speakers: Minimum number of speakers (optional)
            max_speakers: Maximum number of speakers (optional)

        Returns:
            Diarization result dict
        """
        if not self.diarize_model:
            raise RuntimeError("Diarization model not loaded. Call load_model() first.")

        self.logger.info(f"Running diarization on: {audio_file}")
        if min_speakers is not None:
            self.logger.info(f"  Min speakers: {min_speakers}")
        if max_speakers is not None:
            self.logger.info(f"  Max speakers: {max_speakers}")

        try:
            # Run pyannote diarization
            diarization = self.diarize_model(
                audio_file,
                min_speakers=min_speakers,
                max_speakers=max_speakers
            )

            # Convert pyannote output to whisperx-compatible format
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    "start": turn.start,
                    "end": turn.end,
                    "speaker": speaker
                })

            result = {"segments": segments}
            self.logger.info(f"  Diarization complete: {len(segments)} speaker turns")
            return result

        except Exception as e:
            self.logger.error(f"  Diarization failed: {e}")
            raise

    def assign_speakers_to_segments(
        self,
        segments: List[Dict],
        diarize_segments: Dict[str, Any],
        speaker_map: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Assign speaker labels to transcript segments

        Args:
            segments: WhisperX transcript segments
            diarize_segments: Diarization result from pyannote
            speaker_map: Optional mapping of SPEAKER_XX to character names

        Returns:
            Segments with speaker labels assigned
        """
        self.logger.info("Assigning speaker labels to segments...")

        try:
            # Use whisperx's assign_word_speakers utility
            # Note: correct parameter order is (segments, diarize_segments)
            result = whisperx.assign_word_speakers(segments, diarize_segments)
            labeled_segments = result.get("segments", segments)

            # Apply speaker name mapping if provided
            if speaker_map:
                self.logger.info(f"  Applying speaker name mapping: {len(speaker_map)} speakers")
                for segment in labeled_segments:
                    if "speaker" in segment:
                        original_speaker = segment["speaker"]
                        if original_speaker in speaker_map:
                            segment["speaker"] = speaker_map[original_speaker]
                            segment["speaker_original"] = original_speaker

            # Count speakers
            speakers = set()
            for segment in labeled_segments:
                if "speaker" in segment:
                    speakers.add(segment["speaker"])

            self.logger.info(f"  Speaker assignment complete: {len(speakers)} unique speakers")
            return labeled_segments

        except Exception as e:
            self.logger.warning(f"  Speaker assignment failed: {e}")
            self.logger.warning("  Returning segments without speaker labels")
            return segments

    def save_results(
        self,
        segments: List[Dict],
        output_dir: Path,
        basename: str
    ):
        """
        Save diarized segments to output directory

        Args:
            segments: Segments with speaker labels
            output_dir: Output directory (e.g., out/Movie/diarization/)
            basename: Base filename
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save diarized segments as JSON
        json_file = output_dir / f"{basename}.diarized.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(segments, f, indent=2, ensure_ascii=False)
        self.logger.info(f"  Saved: {json_file}")

        # Save as plain text with speaker labels
        txt_file = output_dir / f"{basename}.diarized.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            for segment in segments:
                speaker = segment.get("speaker", "UNKNOWN")
                text = segment.get("text", "").strip()
                if text:
                    f.write(f"[{speaker}] {text}\n")
        self.logger.info(f"  Saved: {txt_file}")

        # Save as SRT with speaker labels
        srt_file = output_dir / f"{basename}.diarized.srt"
        self._save_as_srt(segments, srt_file)
        self.logger.info(f"  Saved: {srt_file}")

    def _save_as_srt(self, segments: List[Dict], srt_file: Path):
        """
        Save segments as SRT subtitle file with speaker labels

        Args:
            segments: List of segments with speaker labels
            srt_file: Output SRT file path
        """
        with open(srt_file, "w", encoding="utf-8") as f:
            for i, segment in enumerate(segments, 1):
                start = segment.get("start", 0)
                end = segment.get("end", start + 1)
                text = segment.get("text", "").strip()
                speaker = segment.get("speaker", "")

                if not text:
                    continue

                # Format timestamps as HH:MM:SS,mmm
                start_time = self._format_srt_time(start)
                end_time = self._format_srt_time(end)

                # Add speaker prefix if available
                if speaker:
                    text = f"[{speaker}] {text}"

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


def load_speaker_map(speaker_map_file: Optional[str]) -> Optional[Dict[str, str]]:
    """
    Load speaker name mapping from JSON file

    Args:
        speaker_map_file: Path to speaker map JSON file

    Returns:
        Speaker mapping dict or None
    """
    if not speaker_map_file:
        return None

    speaker_map_path = Path(speaker_map_file)
    if not speaker_map_path.exists():
        return None

    try:
        with open(speaker_map_path, 'r', encoding='utf-8', errors='replace') as f:
            speaker_map = json.load(f)
        return speaker_map
    except Exception as e:
        print(f"Warning: Failed to load speaker map: {e}")
        return None


def run_diarization_pipeline(
    audio_file: str,
    segments: List[Dict],
    output_dir: Path,
    basename: str,
    hf_token: str,
    device: str,
    speaker_map_file: Optional[str] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    logger: Optional[PipelineLogger] = None
) -> List[Dict]:
    """
    Run complete diarization pipeline

    Args:
        audio_file: Path to audio/video file
        segments: WhisperX transcript segments
        output_dir: Output directory
        basename: Base filename
        hf_token: Hugging Face token
        device: Device to use
        speaker_map_file: Optional speaker name mapping file
        min_speakers: Minimum number of speakers
        max_speakers: Maximum number of speakers
        logger: Logger instance

    Returns:
        Diarized segments
    """
    processor = DiarizationProcessor(
        hf_token=hf_token,
        device=device,
        logger=logger
    )

    # Load diarization model
    processor.load_model()

    # Run diarization
    diarize_segments = processor.diarize_audio(
        audio_file,
        min_speakers=min_speakers,
        max_speakers=max_speakers
    )

    # Load speaker name mapping if provided
    speaker_map = load_speaker_map(speaker_map_file)

    # Assign speakers to segments
    labeled_segments = processor.assign_speakers_to_segments(
        segments,
        diarize_segments,
        speaker_map=speaker_map
    )

    # Save results
    processor.save_results(labeled_segments, output_dir, basename)

    return labeled_segments


def main():
    """Main entry point for diarization stage."""
    import os
    from shared.stage_utils import StageIO, get_stage_logger
    from shared.config import load_config
    
    # Set up stage I/O and logging
    stage_io = StageIO("diarization")
    logger = get_stage_logger("diarization", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("DIARIZATION STAGE: Speaker Diarization")
    logger.info("=" * 60)
    
    # Load configuration
    config_path = os.environ.get('CONFIG_PATH', 'config/.env.pipeline')
    logger.debug(f"Loading configuration from: {config_path}")
    
    try:
        config = load_config(config_path)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Get input files
    audio_input = stage_io.get_input_path("audio.wav", from_stage="demux")
    logger.info(f"Input audio: {audio_input}")
    
    # Check if ASR has been completed - if not, skip diarization
    try:
        # Try whisperx_asr stage first, then fallback to asr
        asr_results_path = None
        for stage_name in ["whisperx_asr", "asr"]:
            try:
                path = stage_io.get_input_path("transcript.json", from_stage=stage_name)
                if path.exists():
                    asr_results_path = path
                    logger.debug(f"Found ASR results in stage: {stage_name}")
                    break
            except Exception:
                continue
        
        if not asr_results_path or not asr_results_path.exists():
            logger.warning("ASR results not found - diarization requires transcript")
            logger.warning("Skipping diarization stage")
            return 0
        
        # Load ASR segments
        import json
        with open(asr_results_path, 'r', encoding='utf-8') as f:
            asr_data = json.load(f)
        segments = asr_data.get("segments", [])
        logger.info(f"Loaded {len(segments)} segments from ASR")
    except Exception as e:
        logger.warning(f"Could not load ASR results: {e}")
        logger.warning("Skipping diarization stage")
        return 0
    
    # Get device from environment (stage-specific or global)
    device = os.environ.get("DIARIZATION_DEVICE",
                           os.environ.get("DEVICE_OVERRIDE", 
                                        os.environ.get("DEVICE", "cpu"))).lower()
    logger.info(f"Device: {device}")
    
    # Get HuggingFace token
    hf_token = os.environ.get("HF_TOKEN", getattr(config, 'hf_token', ''))
    if not hf_token:
        logger.error("HF_TOKEN not set - required for PyAnnote diarization")
        logger.error("Set HF_TOKEN environment variable or update config/.env.pipeline")
        return 1
    
    # Get speaker settings
    min_speakers = getattr(config, 'min_speakers', None)
    max_speakers = getattr(config, 'max_speakers', None)
    speaker_map_file = getattr(config, 'speaker_map', None)
    
    # Get output basename from config
    basename = getattr(config, 'job_id', 'output')
    
    logger.info("Running diarization pipeline...")
    
    try:
        # Run diarization
        labeled_segments = run_diarization_pipeline(
            audio_file=str(audio_input),
            segments=segments,
            output_dir=stage_io.stage_dir,
            basename=basename,
            hf_token=hf_token,
            device=device,
            speaker_map_file=speaker_map_file,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            logger=logger
        )
        
        # Save the diarized segments as the main output
        output_json = stage_io.get_output_path("diarized.json")
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump({"segments": labeled_segments}, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved diarized segments: {output_json}")
        
        logger.info("✓ Diarization completed successfully")
        logger.info("=" * 60)
        logger.info("DIARIZATION STAGE COMPLETED")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
