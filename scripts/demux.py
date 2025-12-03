#!/usr/bin/env python3
"""
Demux stage: Extract audio from video file
"""
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


def main():
    """Extract audio from video file."""
    # Initialize stage I/O
    stage_io = StageIO("demux")
    logger = get_stage_logger("demux", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("DEMUX STAGE: Extract Audio from Video")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1
    
    # Get input file
    input_file = getattr(config, 'in_root', getattr(config, 'input_media', ''))
    if not input_file or not Path(input_file).exists():
        logger.error(f"Input media not found: {input_file}")
        return 1
    
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
    
    # Output audio file
    audio_file = stage_io.get_output_path("audio.wav")
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
        return 1
    
    logger.info(f"✓ Audio extracted successfully: {audio_file}")
    logger.debug(f"File size: {audio_file.stat().st_size / (1024*1024):.2f} MB")
    
    # Save metadata
    metadata = {
        'status': 'completed',
        'input_file': str(input_file),
        'audio_file': str(audio_file),
        'sample_rate': 16000,
        'channels': 1,
        'format': 'pcm_s16le',
        'processing_mode': media_mode,
        'start_time': start_time,
        'end_time': end_time
    }
    
    metadata_path = stage_io.save_metadata(metadata)
    logger.debug(f"Metadata saved: {metadata_path}")
    
    logger.info("=" * 60)
    logger.info("DEMUX STAGE COMPLETED")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
