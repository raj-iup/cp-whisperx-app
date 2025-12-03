#!/usr/bin/env python3
"""
Demux stage: Extract audio from video file
"""
# Standard library
import sys
import os
import subprocess
from pathlib import Path
import json

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

# Local
from shared.logger import get_logger
logger = get_logger(__name__)


def run_stage(job_dir: Path, stage_name: str = "01_demux") -> int:
    """
    Demux stage: Extract audio from video
    
    Args:
        job_dir: Job directory containing input video
        stage_name: Stage name for logging (default: "01_demux")
        
    Returns:
        0 on success, 1 on failure
    """
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger = io.get_stage_logger()
    
    try:
        logger.info("=" * 60)
        logger.info("DEMUX STAGE: Extract Audio from Video")
        logger.info("=" * 60)
        
        # Load configuration
        config = load_config()
        
        # Get input file
        input_file = getattr(config, 'in_root', getattr(config, 'input_media', ''))
        if not input_file or not Path(input_file).exists():
            raise FileNotFoundError(f"Input media not found: {input_file}")
        
        # Track input
        input_path = Path(input_file)
        io.track_input(input_path, "video", format=input_path.suffix)
        
        logger.info(f"Input media: {input_file}")
        
        # Check if we're processing a clip or full media
        media_mode = getattr(config, 'media_processing_mode', 'full')
        start_time = getattr(config, 'media_start_time', None)
        end_time = getattr(config, 'media_end_time', None)
        
        if media_mode == "clip" and (start_time or end_time):
            logger.info(f"Processing mode: CLIP")
            if start_time:
                logger.info(f"  Start time: {start_time}")
            if end_time:
                logger.info(f"  End time: {end_time}")
        else:
            logger.info(f"Processing mode: FULL")
        
        # Add config to manifest
        io.add_config("media_mode", media_mode)
        io.add_config("start_time", start_time)
        io.add_config("end_time", end_time)
        io.add_config("sample_rate", 16000)
        io.add_config("channels", 1)
        
        # Output audio file
        audio_file = io.stage_dir / "audio.wav"
        logger.info(f"Output audio: {audio_file}")
        
        # Build ffmpeg command
        cmd = ["ffmpeg"]
        
        # Add start time if specified (must come before -i)
        if start_time:
            cmd.extend(["-ss", start_time])
        
        # Input file
        cmd.extend(["-i", str(input_file)])
        
        # Add end time if specified (more accurate when after -i)
        if end_time:
            cmd.extend(["-to", end_time])
        
        # Audio extraction parameters
        cmd.extend([
            "-vn",  # No video
            "-acodec", "pcm_s16le",  # 16-bit PCM
            "-ar", "16000",  # 16kHz sample rate (required by Whisper)
            "-ac", "1",  # Mono
            "-y",  # Overwrite
            str(audio_file)
        ])
        
        logger.debug(f"Running ffmpeg: {' '.join(cmd)}")
        logger.info("Extracting audio...")
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"ffmpeg failed with code {result.returncode}")
            logger.error(f"stderr: {result.stderr}")
            raise RuntimeError(f"ffmpeg extraction failed: {result.stderr}")
        
        # Track output
        io.track_output(audio_file, "audio", format="wav", sample_rate=16000, channels=1)
        
        logger.info(f"✓ Audio extracted successfully: {audio_file}")
        logger.debug(f"File size: {audio_file.stat().st_size / (1024*1024):.2f} MB")
        
        logger.info("=" * 60)
        logger.info("DEMUX STAGE COMPLETED")
        logger.info("=" * 60)
        
        io.finalize(status="success")
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1
    except RuntimeError as e:
        logger.error(f"Demux failed: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        io.add_error(str(e), e)
        io.finalize(status="failed")
        return 1


def main() -> int:
    """
    Legacy wrapper for backward compatibility.
    Calls run_stage() with default output directory from environment.
    """
    # Get output directory from environment or use default
    output_dir = Path(os.environ.get('OUTPUT_DIR', 'out'))
    return run_stage(output_dir, "01_demux")


if __name__ == "__main__":
    sys.exit(main())
