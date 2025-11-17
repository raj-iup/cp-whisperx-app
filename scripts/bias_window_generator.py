"""
bias_injection.py - Rolling windowed prompt injection for WhisperX

Creates compact bias prompts for each rolling window to stabilize
proper nouns within scene context.
"""

import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass
import sys
import os
from datetime import datetime

# Add project root to path for shared imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.stage_utils import StageIO


@dataclass
class BiasWindow:
    """A single bias window"""
    window_id: int
    start_time: float
    end_time: float
    bias_terms: List[str]
    bias_prompt: str


def create_bias_windows(
    duration_seconds: float,
    window_seconds: int,
    stride_seconds: int,
    base_terms: List[str],
    topk: int = 10,
    decay: float = 0.9
) -> List[BiasWindow]:
    """
    Create rolling bias windows for the video

    Args:
        duration_seconds: Total video duration
        window_seconds: Window size (e.g., 45s)
        stride_seconds: Stride between windows (e.g., 15s)
        base_terms: Base list of terms (names, places) from era/TMDB
        topk: Number of top terms to include per window
        decay: Decay factor for term weighting (future use)

    Returns:
        List of BiasWindow objects
    """
    windows = []
    window_id = 0
    start_time = 0.0

    while start_time < duration_seconds:
        end_time = min(start_time + window_seconds, duration_seconds)

        # For now, use top-k terms uniformly
        # In future: implement dynamic weighting based on recent mentions
        bias_terms = base_terms[:topk]

        # Create compact bias prompt
        bias_prompt = ", ".join(bias_terms)

        windows.append(BiasWindow(
            window_id=window_id,
            start_time=start_time,
            end_time=end_time,
            bias_terms=bias_terms,
            bias_prompt=bias_prompt
        ))

        window_id += 1
        start_time += stride_seconds

    return windows


def save_bias_windows(
    bias_dir: Path,
    windows: List[BiasWindow],
    basename: str
):
    """
    Save bias windows to JSON files

    Args:
        bias_dir: Directory to save bias windows
        windows: List of BiasWindow objects
        basename: Base filename for output
    """
    bias_dir.mkdir(parents=True, exist_ok=True)

    # Save each window as separate JSON
    for window in windows:
        window_file = bias_dir / f"{basename}.bias.window.{window.window_id:04d}.json"

        window_data = {
            "window_id": window.window_id,
            "start_time": window.start_time,
            "end_time": window.end_time,
            "bias_terms": window.bias_terms,
            "bias_prompt": window.bias_prompt
        }

        with open(window_file, "w", encoding='utf-8') as f:
            json.dump(window_data, f, indent=2)

    # Also save summary of all windows
    summary_file = bias_dir / f"{basename}.bias.summary.json"
    summary_data = {
        "total_windows": len(windows),
        "windows": [
            {
                "window_id": w.window_id,
                "start_time": w.start_time,
                "end_time": w.end_time,
                "num_terms": len(w.bias_terms)
            }
            for w in windows
        ]
    }

    with open(summary_file, "w", encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)


def get_window_for_time(windows: List[BiasWindow], time_seconds: float) -> BiasWindow:
    """
    Get bias window for a specific timestamp

    Args:
        windows: List of BiasWindow objects
        time_seconds: Timestamp in seconds

    Returns:
        Closest BiasWindow
    """
    for window in windows:
        if window.start_time <= time_seconds < window.end_time:
            return window

    # Fallback to last window if time exceeds all windows
    return windows[-1] if windows else None


def main():
    """Main entry point for lyrics detection stage."""
    import sys
    import os
    import json
    from pathlib import Path
    
    # Add project root for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from scripts.lyrics_detection_core import run_lyrics_detection
    from shared.logger import PipelineLogger
    from shared.config import load_config
    
    # Get output directory and config from environment or command line
    output_dir_env = os.environ.get('OUTPUT_DIR')
    config_path_env = os.environ.get('CONFIG_PATH')
    
    if output_dir_env:
        output_dir = Path(output_dir_env)
    elif len(sys.argv) > 1:
        output_dir = Path(sys.argv[1])
    else:
        print("ERROR: No output directory specified", file=sys.stderr)
        return 1
    
    # Initialize StageIO for lyrics_detection
    stage_io = StageIO("lyrics_detection", output_base=output_dir)
    
    # Load configuration
    if config_path_env:
        config = load_config(config_path_env)
    else:
        config = None
    
    # Setup logger with numbered log file
    log_file = stage_io.get_log_path()
    logger = PipelineLogger("lyrics_detection", log_file)
    
    logger.info("Running lyrics detection")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Stage directory: {stage_io.stage_dir}")
    
    # Check if lyrics detection is enabled
    lyric_enabled = getattr(config, 'lyric_detect_enabled', True) if config else True
    if not lyric_enabled:
        logger.info("Lyrics detection disabled, skipping")
        # Create empty output using StageIO
        result_data = {"lyric_segments": [], "detected": False, "disabled": True}
        stage_io.save_json(result_data, "segments.json")
        
        metadata = {
            "status": "completed",
            "detected": False,
            "disabled": True,
            "stage": "lyrics_detection",
            "stage_number": stage_io.stage_number,
            "timestamp": datetime.now().isoformat()
        }
        stage_io.save_json(metadata, "metadata.json")
        return 0
    
    # Get configuration parameters
    threshold = getattr(config, 'lyric_threshold', 0.5) if config else 0.5
    min_duration = getattr(config, 'lyric_min_duration', 30.0) if config else 30.0
    device = os.environ.get('DEVICE_OVERRIDE', getattr(config, 'device', 'cpu') if config else 'cpu').lower()
    
    logger.info(f"Threshold: {threshold}")
    logger.info(f"Min duration: {min_duration}s")
    logger.info(f"Device: {device}")
    
    # Get audio file using StageIO
    audio_file = stage_io.get_input_path("audio.wav", from_stage="demux")
    if not audio_file.exists():
        logger.warning(f"Audio file not found: {audio_file}")
        logger.warning("Creating empty lyrics output")
        result_data = {"lyric_segments": [], "detected": False, "error": "audio_not_found"}
        stage_io.save_json(result_data, "segments.json")
        
        metadata = {
            "status": "completed",
            "detected": False,
            "error": "audio_not_found",
            "stage": "lyrics_detection",
            "stage_number": stage_io.stage_number,
            "timestamp": datetime.now().isoformat()
        }
        stage_io.save_json(metadata, "metadata.json")
        return 0
    
    # Load VAD segments using StageIO
    vad_segments = []
    vad_file = stage_io.get_input_path("vad_segments.json", from_stage="silero_vad")
    if not vad_file.exists():
        vad_file = stage_io.get_input_path("vad_segments.json", from_stage="pyannote_vad")
    
    if vad_file.exists():
        try:
            with open(vad_file, 'r') as f:
                vad_data = json.load(f)
                vad_segments = vad_data if isinstance(vad_data, list) else []
            logger.info(f"Loaded {len(vad_segments)} VAD segments")
        except Exception as e:
            logger.warning(f"Could not load VAD segments: {e}")
    
    # Load ASR transcript using StageIO
    asr_segments = []
    asr_file = stage_io.get_input_path("transcript.json", from_stage="asr")
    
    if asr_file.exists():
        try:
            with open(asr_file, 'r') as f:
                asr_data = json.load(f)
                asr_segments = asr_data.get('segments', [])
            logger.info(f"Loaded {len(asr_segments)} ASR segments")
        except Exception as e:
            logger.warning(f"Could not load ASR segments: {e}")
    
    # Run lyrics detection
    try:
        result = run_lyrics_detection(
            audio_file=audio_file,
            output_dir=stage_io.stage_dir,  # Use stage directory
            vad_segments=vad_segments,
            asr_segments=asr_segments,
            threshold=threshold,
            min_duration=min_duration,
            device=device,
            logger=logger
        )
        
        # Save metadata
        metadata = {
            "status": "completed",
            "detected": result['detected'],
            "total_segments": result['total_segments'],
            "total_duration": result.get('total_duration', 0),
            "detection_methods": result.get('detection_methods', []),
            "stage": "lyrics_detection",
            "stage_number": stage_io.stage_number,
            "timestamp": datetime.now().isoformat()
        }
        stage_io.save_json(metadata, "metadata.json")
        
        logger.info(f"✓ Lyrics detection completed")
        logger.info(f"  Detected: {result['detected']}")
        logger.info(f"  Segments: {result['total_segments']}")
        if result['total_segments'] > 0:
            logger.info(f"  Total duration: {result['total_duration']:.1f}s")
            logger.info(f"  Detection methods: {result['detection_methods']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Lyrics detection failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Create minimal output using StageIO
        result_data = {"lyric_segments": [], "detected": False, "error": str(e)}
        stage_io.save_json(result_data, "segments.json")
        
        metadata = {
            "status": "failed",
            "error": str(e),
            "stage": "lyrics_detection",
            "stage_number": stage_io.stage_number,
            "timestamp": datetime.now().isoformat()
        }
        stage_io.save_json(metadata, "metadata.json")
        
        logger.info("Created empty lyrics output (stage skipped)")
        return 0  # Non-critical, don't fail pipeline


if __name__ == "__main__":
    import sys
    sys.exit(main())
