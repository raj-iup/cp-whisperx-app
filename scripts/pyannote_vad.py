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

# Load environment variables from CONFIG_PATH if available
if 'CONFIG_PATH' in os.environ:
    try:
        from dotenv import dotenv_values
        config_values = dotenv_values(os.environ['CONFIG_PATH'])
        for key, value in config_values.items():
            if key not in os.environ and value is not None:
                os.environ[key] = value
    except Exception:
        pass

if __name__ == "__main__":
    # Set up stage I/O and logging
    stage_io = StageIO("pyannote_vad")
    logger = get_stage_logger("pyannote_vad", log_level="DEBUG", stage_io=stage_io)
    
    logger.info("=" * 60)
    logger.info("PYANNOTE VAD STAGE: Voice Activity Detection")
    logger.info("=" * 60)
    
    # Get input audio from demux stage
    audio_input = stage_io.get_input_path("audio.wav", from_stage="demux")
    logger.info(f"Input audio: {audio_input}")
    
    # Set output paths
    output_json = stage_io.get_output_path("speech_segments.json")
    logger.info(f"Output JSON: {output_json}")
    
    # Get device from environment (stage-specific or global)
    device = os.environ.get("PYANNOTE_DEVICE", 
                           os.environ.get("DEVICE_OVERRIDE", 
                                        os.environ.get("DEVICE", "cpu"))).lower()
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
