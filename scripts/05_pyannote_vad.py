#!/usr/bin/env python3
"""
PyAnnote VAD stage: Voice Activity Detection using PyAnnote
"""
# Standard library
import warnings
# Suppress torchaudio warnings early before imports
warnings.filterwarnings('ignore', message='.*torchaudio._backend.*')
warnings.filterwarnings('ignore', message='.*torchcodec.*')
warnings.filterwarnings('ignore', category=UserWarning, module='torchaudio')

import sys
import os
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.stage_utils import StageIO, get_stage_logger
from shared.config import load_config

# Local
from shared.logger import get_logger
logger = get_logger(__name__)

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
        logger.error(f"Failed to load configuration: {e}", exc_info=True)
        stage_io.add_error(f"Config load failed: {e}", e)
        stage_io.finalize(status="failed", error=str(e))
        sys.exit(1)
    
    # Get VAD enabled flag from config (use dict access with defaults)
    vad_enabled = True  # Default: enabled
    vad_threshold = 0.5  # Default: 0.5
    
    # Try to get from config if available
    if hasattr(config, 'get'):
        vad_enabled = config.get('PYANNOTE_VAD_ENABLED', 'true').lower() == 'true'
        vad_threshold = float(config.get('PYANNOTE_VAD_THRESHOLD', '0.5'))
    
    # Override with job.json parameters (AD-006)
    job_json_path = stage_io.output_base / "job.json"
    if job_json_path.exists():
        logger.info("Reading job-specific parameters from job.json...")
        try:
            with open(job_json_path) as f:
                job_data = json.load(f)
                
                # Override VAD parameters
                if 'vad' in job_data:
                    vad_config = job_data['vad']
                    if 'enabled' in vad_config and vad_config['enabled'] is not None:
                        old_enabled = vad_enabled
                        vad_enabled = vad_config['enabled']
                        logger.info(f"  vad.enabled override: {old_enabled} → {vad_enabled} (from job.json)")
                    if 'threshold' in vad_config and vad_config['threshold']:
                        old_threshold = vad_threshold
                        vad_threshold = float(vad_config['threshold'])
                        logger.info(f"  vad.threshold override: {old_threshold} → {vad_threshold} (from job.json)")
        except Exception as e:
            logger.warning(f"Failed to read job.json parameters: {e}")
    else:
        logger.warning(f"job.json not found at {job_json_path}, using system defaults")
    
    logger.info(f"Using VAD enabled: {vad_enabled}")
    logger.info(f"Using VAD threshold: {vad_threshold}")
    
    # Check if VAD is disabled
    if not vad_enabled:
        logger.info("PyAnnote VAD disabled, skipping")
        stage_io.finalize(status="skipped")
        sys.exit(0)
    
    # Get input audio using StageIO
    audio_input = stage_io.get_input_path("audio.wav", from_stage="demux")
    
    if not audio_input.exists():
        logger.error(f"Audio file not found: {audio_input}", exc_info=True)
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
        "model": "pyannote/voice-activity-detection"
    })
    
    logger.info("Running PyAnnote VAD...")
    
    # Run PyAnnote VAD directly
    exit_code = 1
    try:
        import json
        import torch
        from pyannote.audio import Pipeline
        
        # Load the VAD pipeline
        logger.info("Loading PyAnnote VAD model...")
        pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection")
        
        # Move to device
        if device in ["cuda", "mps"]:
            try:
                pipeline.to(torch.device(device))
                logger.info(f"Using device: {device}")
            except Exception as e:
                logger.warning(f"Could not use {device}, falling back to CPU: {e}")
                device = "cpu"
        
        # Run VAD on audio
        logger.info(f"Processing audio file: {audio_input}")
        vad_result = pipeline(str(audio_input))
        
        # Convert to segments list
        segments = []
        for speech in vad_result.get_timeline().support():
            segments.append({
                "start": float(speech.start),
                "end": float(speech.end),
                "duration": float(speech.end - speech.start)
            })
        
        logger.info(f"Detected {len(segments)} speech segments")
        
        # Merge close segments if merge_gap is set
        merge_gap = 0.2
        if merge_gap > 0 and len(segments) > 1:
            merged_segments = []
            current = segments[0]
            
            for next_seg in segments[1:]:
                if next_seg["start"] - current["end"] <= merge_gap:
                    # Merge segments
                    current["end"] = next_seg["end"]
                    current["duration"] = current["end"] - current["start"]
                else:
                    merged_segments.append(current)
                    current = next_seg
            
            merged_segments.append(current)
            logger.info(f"Merged to {len(merged_segments)} segments (gap threshold: {merge_gap}s)")
            segments = merged_segments
        
        # Save to JSON with proper format expected by pipeline
        # Pipeline expects {"segments": [...]} not just [...]
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_data = {"segments": segments}
        with open(output_json, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"✓ Saved speech segments to: {output_json}")
        exit_code = 0
        
    except ImportError as e:
        logger.error(f"✗ Failed to import PyAnnote: {e}", exc_info=True)
        logger.error("Make sure PyAnnote is installed in the correct environment")
        stage_io.add_error(f"Import failed: {e}")
        stage_io.finalize(status="failed", error="Missing dependency")
        sys.exit(1)
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
        logger.error(f"✗ PyAnnote VAD failed with exit code {exit_code}", exc_info=True)
        stage_io.add_error(f"VAD failed with exit code {exit_code}")
        stage_io.finalize(status="failed", exit_code=exit_code)
    
    logger.info("=" * 60)
    logger.info("PYANNOTE VAD STAGE COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Stage log: {stage_io.stage_log.relative_to(stage_io.output_base)}")
    logger.info(f"Stage manifest: {stage_io.manifest_path.relative_to(stage_io.output_base)}")
    
    sys.exit(exit_code)
