"""
diarization.py - Speaker diarization using pyannote-audio

Handles:
- Loading pyannote diarization model
- Running speaker diarization on audio
- Assigning speaker labels to transcript segments
- Optional speaker name mapping
- Saving diarized results
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
import whisperx
from pyannote.audio import Pipeline
from .logger import PipelineLogger


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
        from .logger import PipelineLogger
        return PipelineLogger("diarization")

    def load_model(self):
        """Load pyannote diarization model"""
        import torch
        
        self.logger.info("Loading pyannote diarization model...")
        self.logger.info(f"  Model: {self.model_name}")
        self.logger.info(f"  Device requested: {self.device}")

        # Auto-detect best available device if needed
        original_device = self.device
        if self.device.upper() == "MPS" and not torch.backends.mps.is_available():
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
                    self.logger.info(f"  Model moved to {self.device}")
                except Exception as e:
                    self.logger.warning(f"  Could not move to {self.device}: {e}")
                    self.logger.warning("  Using CPU instead (will be slow!)")
                    self.device = "cpu"
            self.logger.info("  Diarization model loaded successfully")
        except Exception as e:
            self.logger.error(f"  Failed to load diarization model: {e}")
            raise

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
            result = whisperx.assign_word_speakers(diarize_segments, segments)
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
        with open(speaker_map_path) as f:
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
