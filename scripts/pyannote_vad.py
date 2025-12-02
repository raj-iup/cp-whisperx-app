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
    # Set up stage I/O with manifest tracking
    stage_io = StageIO("pyannote_vad", enable_manifest=True)
    logger = stage_io.get_stage_logger("INFO")
    
    logger.info("=" * 60)
    logger.info("PYANNOTE VAD STAGE: Voice Activity Detection")
    logger.info("=" * 60)
    
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        stage_io.add_error(f"Config load failed: {e}", e)
        stage_io.finalize(status="failed", error=str(e))
        sys.exit(1)
    
    # Get input audio using StageIO
    audio_input = stage_io.get_input_path("audio.wav", from_stage="demux")
    
    if not audio_input.exists():
        logger.error(f"Audio file not found: {audio_input}")
        stage_io.add_error(f"Audio file not found: {audio_input}")
        stage_io.finalize(status="failed", error="Input file missing")
        sys.exit(1)
    
    # Track input
    stage_io.track_input(audio_input, "audio", format="wav")
    
    logger.info(f"Input audio: {audio_input}")
    
    # Get output path using StageIO
    output_json = stage_io.get_output_path("speech_segments.json")
    logger.info(f"Output JSON: {output_json}")
    
    # Get device from config
    device = getattr(config, 'pyannote_device', 
                    getattr(config, 'device', 'cpu')).lower()
    logger.info(f"Device: {device}")
    
    # Track configuration
    stage_io.set_config({
        "device": device,
        "merge_gap": 0.2,
        "model": "pyannote/segmentation"
    })
    
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
    try:
        from pyannote_vad_chunker import main as vad_main
        exit_code = vad_main()
    except FileNotFoundError as e:
        logger.error(f"✗ File not found: {e}", exc_info=True)
        stage_io.add_error(f"File not found: {e}")
        stage_io.finalize(status="failed", error=str(e))
        sys.exit(1)
    except IOError as e:
        logger.error(f"✗ I/O error: {e}", exc_info=True)
        stage_io.add_error(f"I/O error: {e}")
        stage_io.finalize(status="failed", error=str(e))
        sys.exit(1)
    except ImportError as e:
        logger.error(f"✗ Failed to import pyannote_vad_chunker: {e}")
        logger.error("Make sure PyAnnote is installed in the correct environment")
        stage_io.add_error(f"Import failed: {e}")
        stage_io.finalize(status="failed", error="Missing dependency")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"✗ Model error: {e}", exc_info=True)
        stage_io.add_error(f"PyAnnote model error: {e}")
        stage_io.finalize(status="failed", error=str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("✗ VAD interrupted by user")
        stage_io.add_error("Interrupted by user")
        stage_io.finalize(status="failed", error="KeyboardInterrupt")
        sys.exit(130)
    except Exception as e:
        logger.error(f"✗ VAD failed with unexpected error: {e}", exc_info=True)
        stage_io.add_error(f"Unexpected error: {e}")
        stage_io.finalize(status="failed", error=str(e))
        sys.exit(1)
    
    # Handle None exit code (should not happen with fixed chunker)
    if exit_code is None:
        logger.error("✗ PyAnnote VAD returned None - treating as failure")
        stage_io.add_error("VAD returned None")
        stage_io.finalize(status="failed", error="Invalid return code")
        exit_code = 1
    
    if exit_code == 0:
        logger.info("✓ PyAnnote VAD completed successfully")
        
        # Track output
        if output_json.exists():
            import json
            try:
                with open(output_json, 'r') as f:
                    segments_data = json.load(f)
                segments_count = len(segments_data) if isinstance(segments_data, list) else 0
                stage_io.track_output(output_json, "segments",
                                     format="json",
                                     segments_count=segments_count)
                
                # Finalize with success
                stage_io.finalize(status="success",
                                 segments_count=segments_count,
                                 device=device)
            except Exception as e:
                logger.warning(f"Could not read output segments: {e}")
                stage_io.track_output(output_json, "segments", format="json")
                stage_io.finalize(status="success", device=device)
        else:
            logger.warning("Output file not found after successful completion")
            stage_io.add_warning("Output file not found")
            stage_io.finalize(status="success", device=device)
    else:
        logger.error(f"✗ PyAnnote VAD failed with exit code {exit_code}")
        stage_io.add_error(f"VAD failed with exit code {exit_code}")
        stage_io.finalize(status="failed", exit_code=exit_code)
    
    logger.info("=" * 60)
    logger.info("PYANNOTE VAD STAGE COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
    logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
    
    sys.exit(exit_code)
