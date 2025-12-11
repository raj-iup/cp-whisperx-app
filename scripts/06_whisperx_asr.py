#!/usr/bin/env python3
"""
WhisperX ASR stage: Automatic Speech Recognition

This is a thin wrapper around whisperx_integration.py which contains
the actual ASR logic. The separation allows for easier testing and
maintains compatibility with the pipeline architecture.

AD-006 Compliance: Parameter override logic is implemented in
whisperx_integration.py (delegated implementation pattern).

Stage: 04_asr (Stage 4)
Input: audio.wav from demux or source_separation
Output: transcript.json with word-level timestamps
"""
# Standard library
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from whisperx_integration import main as whisperx_main

# Local
from shared.logger import get_logger
from shared.stage_utils import StageIO
from shared.config_loader import load_config
from shared.cost_tracker import CostTracker

logger = get_logger(__name__)


def run_stage(job_dir: Path, stage_name: str = "04_asr") -> int:
    """
    WhisperX ASR Stage - run_stage() wrapper
    
    Provides StageIO interface for legacy whisperx_integration.py
    
    Args:
        job_dir: Job directory path
        stage_name: Stage name for logging/manifest
        
    Returns:
        0 on success, 1 on failure
    """
    io = StageIO(stage_name, job_dir, enable_manifest=True)
    logger_stage = io.get_stage_logger()
    
    try:
        logger_stage.info("=" * 80)
        logger_stage.info("STAGE: WhisperX ASR")
        logger_stage.info("=" * 80)
        
        # Check if ASR is enabled
        config = load_config()
        asr_enabled = config.get("STAGE_04_ASR_ENABLED", "true").lower() == "true"
        
        if not asr_enabled:
            logger_stage.info("ASR stage disabled in configuration, skipping")
            io.finalize(status="success")
            return 0
        
        # Find input audio
        input_audio = None
        for potential_dir in ["04_source_separation", "01_demux"]:
            candidate = job_dir / potential_dir / "audio.wav"
            if candidate.exists():
                input_audio = candidate
                break
        
        if not input_audio:
            logger_stage.error("No input audio found")
            io.finalize(status="failed")
            return 1
        
        logger_stage.info(f"Input audio: {input_audio}")
        io.track_input(input_audio, "audio")
        
        # Set OUTPUT_DIR environment variable for whisperx_integration
        import os
        os.environ['OUTPUT_DIR'] = str(job_dir)
        
        # Call legacy whisperx_integration main
        # It will use the job_dir environment and create outputs in standard locations
        logger_stage.info("Running WhisperX ASR...")
        exit_code = whisperx_main()
        
        if exit_code != 0:
            logger_stage.error(f"WhisperX ASR failed with exit code {exit_code}")
            io.finalize(status="failed")
            return exit_code
        
        # Track outputs (ASR creates these in job_dir/06_asr/)
        output_locations = [
            io.stage_dir / "transcript.json",
            io.stage_dir / "whisperx_output.json",
            io.stage_dir / "segments.json",
            io.stage_dir / "asr_segments.json",
            io.stage_dir / "asr_transcript.txt"
        ]
        
        for output_file in output_locations:
            if output_file.exists():
                io.track_output(output_file, "transcript")
                logger_stage.info(f"Created output: {output_file}")
        
        logger_stage.info("=" * 80)
        logger_stage.info("WhisperX ASR Complete")
        logger_stage.info("=" * 80)
        
        # Track cost (Phase 6 - Task #21)
        # WhisperX with MLX backend is local processing - no API cost
        # Get user_id from job.json
        user_id = 1
        job_json_path = job_dir / "job.json"
        if job_json_path.exists():
            try:
                import json
                with open(job_json_path, 'r') as f:
                    job_data = json.load(f)
                    user_id = int(job_data.get('user_id', 1))
            except Exception:
                pass
        
        tracker = CostTracker(job_dir=job_dir, user_id=user_id)
        
        # Get audio duration for metadata
        audio_duration_sec = 0
        try:
            import wave
            with wave.open(str(input_audio), 'rb') as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                audio_duration_sec = frames / float(rate)
        except Exception:
            pass
        
        # Get backend info from config
        backend_type = config.get("WHISPER_BACKEND", "mlx").lower()
        model_name = config.get("WHISPERX_MODEL", "large-v3")
        
        # Log local processing cost ($0 for local MLX)
        cost = tracker.log_usage(
            service="local",
            model=f"mlx-whisper" if backend_type == "mlx" else f"whisperx-{model_name}",
            tokens_input=0,
            tokens_output=0,
            stage=stage_name,
            metadata={
                "workflow": config.get("WORKFLOW", "transcribe"),
                "audio_duration_sec": audio_duration_sec,
                "backend": backend_type,
                "model": model_name
            }
        )
        logger_stage.info(f"💰 Stage cost: ${cost:.4f} (local processing)")
        
        io.finalize(status="success")
        return 0
        
    except Exception as e:
        logger_stage.error(f"ASR stage failed: {e}", exc_info=True)
        io.finalize(status="failed")
        return 1


def main() -> int:
    """
    Main entry point for ASR stage.
    
    Delegates to whisperx_integration.main() which handles:
    - Backend selection (WhisperX/MLX)
    - Model loading
    - Audio transcription
    - Word-level alignment
    - Translation (if enabled)
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    import os
    import sys
    
    # Parse command-line arguments
    if len(sys.argv) > 1:
        job_dir = Path(sys.argv[1])
        # Set OUTPUT_DIR environment variable for whisperx_integration
        os.environ['OUTPUT_DIR'] = str(job_dir)
        logger.info(f"Set OUTPUT_DIR={job_dir}")
    
    try:
        return whisperx_main()
    except KeyboardInterrupt:
        logger.error("\n✗ ASR stage interrupted by user", exc_info=True)
        return 130
    except Exception as e:
        import traceback
        error_msg = f"\n✗ ASR stage failed with unexpected error: {e}"
        logger.error(error_msg, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
