#!/usr/bin/env python3
"""
PyAnnote VAD stage: Voice Activity Detection using PyAnnote
"""
import warnings
# Suppress torchaudio warnings early before imports
warnings.filterwarnings('ignore', message='.*torchaudio._backend.*')
warnings.filterwarnings('ignore', message='.*torchcodec.*')
warnings.filterwarnings('ignore', category=UserWarning, module='torchaudio')

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

if __name__ == "__main__":
    # Set up stage I/O and logging
    stage_io = StageIO("pyannote_vad")
    logger = get_stage_logger("pyannote_vad", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("PYANNOTE VAD STAGE: Voice Activity Detection")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Get input audio using StageIO
    audio_input = stage_io.get_input_path("audio.wav", from_stage="demux")
    
    if not audio_input.exists():
        logger.error(f"Audio file not found: {audio_input}")
        sys.exit(1)
    
    logger.info(f"Input audio: {audio_input}")
    
    # Get output path using StageIO
    output_json = stage_io.get_output_path("speech_segments.json")
    logger.info(f"Output JSON: {output_json}")
    
    # Get device from config
    device = getattr(config, 'pyannote_device', 
                    getattr(config, 'device', 'cpu')).lower()
    logger.info(f"Device: {device}")
    
    # Construct arguments for VAD chunker
    sys.argv = [
        "pyannote_vad",
        str(audio_input),
        "--device", device,
        "--out-json", str(output_json),
        "--merge-gap", "0.2"
    ]
    
    logger.info("Running PyAnnote VAD chunker...")
    
    # Import and run the main VAD chunker
    from pyannote_vad_chunker import main
    exit_code = main()
    
    # Handle None exit code (should not happen with fixed chunker)
    if exit_code is None:
        logger.error("✗ PyAnnote VAD returned None - treating as failure")
        exit_code = 1
    
    if exit_code == 0:
        logger.info("✓ PyAnnote VAD completed successfully")
    else:
        logger.error(f"✗ PyAnnote VAD failed with exit code {exit_code}")
    
    logger.info("=" * 60)
    logger.info("PYANNOTE VAD STAGE COMPLETED")
    logger.info("=" * 60)
    
    sys.exit(exit_code)
