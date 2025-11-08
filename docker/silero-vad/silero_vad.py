#!/usr/bin/env python3
"""
Silero VAD Step
Ultra-fast rough speech cuts using Silero Voice Activity Detection.
Trims long silences and non-speech segments with minimal compute (CPU-friendly).

Input: 16kHz mono audio from demux stage
Output: speech timestamps JSON for PyAnnote refinement

Execution Modes:
- Docker: PyTorch in container image
- Native: PyTorch from host .bollyenv
"""
import sys
import json
import os
from pathlib import Path

# ============================================================================
# EXECUTION MODE DETECTION
# ============================================================================
def get_execution_mode():
    """Detect execution mode: docker, native, or auto."""
    mode = os.getenv('EXECUTION_MODE', 'auto')
    
    # Auto-detect based on environment
    if mode == 'auto':
        # If running in Docker container
        if os.path.exists('/.dockerenv') or os.path.exists('/run/.containerenv'):
            mode = 'docker'
        else:
            mode = 'native'
    
    return mode

execution_mode = get_execution_mode()

# ============================================================================
# PYTORCH VERIFICATION
# ============================================================================
def verify_pytorch_availability():
    """Verify PyTorch is available.
    
    Execution modes:
    - docker: PyTorch in container image (check and fail if missing)
    - native: PyTorch from .bollyenv (assume available, let import fail naturally)
    """
    try:
        import torch
        
        # Verify CUDA availability if expected
        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
        
        print(f"[OK] PyTorch {torch.__version__} available")
        print(f"[OK] Execution mode: {execution_mode}")
        print(f"[OK] Device: {device_name}")
        
        return True
        
    except ImportError as e:
        if execution_mode == 'docker':
            # Docker mode requires PyTorch in image
            print("=" * 70)
            print("ERROR: PyTorch not available in Docker image")
            print("=" * 70)
            print(f"Execution mode: {execution_mode}")
            print("")
            print("This image requires PyTorch:")
            print("  - Build with docker-cpu or docker-gpu mode")
            print("  - Or use native execution mode")
            print("=" * 70)
            sys.exit(1)
        else:
            # Native mode - let Python's natural import error show
            # (PyTorch should be in .bollyenv)
            raise

# Verify PyTorch before proceeding
if execution_mode == 'docker':
    verify_pytorch_availability()
# ============================================================================

import torch
import numpy as np
import soundfile as sf

sys.path.insert(0, '/app/shared')
from config import load_config
from logger import setup_logger
from utils import save_json, get_movie_dir, load_json


def load_silero_model():
    """Load Silero VAD model from torch.hub"""
    import os
    
    # Set cache directory based on execution mode
    execution_mode = get_execution_mode()
    if execution_mode == 'docker':
        # Docker: use /app/LLM/torch
        cache_dir = '/app/LLM/torch'
    else:
        # Native: use project root cache
        project_root = Path(__file__).resolve().parents[2]
        cache_dir = str(project_root / 'shared' / 'model-cache' / 'torch')
        os.makedirs(cache_dir, exist_ok=True)
    
    os.environ['TORCH_HOME'] = cache_dir
    
    model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False,
        onnx=False,
        trust_repo=True
    )
    return model, utils


def get_speech_timestamps_silero(audio_path: Path, model, utils, config):
    """
    Get speech timestamps using Silero VAD.
    
    Args:
        audio_path: Path to 16kHz mono audio file
        model: Silero VAD model
        utils: Silero utils (get_speech_timestamps, etc.)
        config: Pipeline configuration
    
    Returns:
        List of speech timestamp dictionaries
    """
    logger = setup_logger(
        "silero_vad",
        log_level=config.log_level,
        log_format=config.log_format,
        log_to_console=config.log_to_console,
        log_to_file=config.log_to_file,
        log_dir=config.log_root
    )
    
    logger.info(f"Loading audio: {audio_path}")
    
    # Load audio using soundfile
    wav, sr = sf.read(str(audio_path), dtype='float32')
    
    # Convert to torch tensor
    wav = torch.from_numpy(wav)
    
    # Ensure mono
    if len(wav.shape) > 1:
        wav = wav.mean(dim=1)
    
    # Ensure 16kHz
    if sr != 16000:
        logger.warning(f"Audio is {sr}Hz, resampling to 16kHz")
        # Simple resampling using numpy
        import scipy.signal
        num_samples = int(len(wav) * 16000 / sr)
        wav = torch.from_numpy(scipy.signal.resample(wav.numpy(), num_samples))
        sr = 16000
    
    # Ensure 1D tensor
    wav = wav.squeeze()
    
    # Get speech timestamps
    logger.info("Running Silero VAD...")
    logger.info(f"VAD threshold: {config.silero_threshold}")
    logger.info(f"Min speech duration: {config.silero_min_speech_duration_ms}ms")
    logger.info(f"Min silence duration: {config.silero_min_silence_duration_ms}ms")
    
    get_speech_timestamps = utils[0]
    
    speech_timestamps = get_speech_timestamps(
        wav,
        model,
        sampling_rate=sr,
        threshold=config.silero_threshold,
        min_speech_duration_ms=config.silero_min_speech_duration_ms,
        min_silence_duration_ms=config.silero_min_silence_duration_ms,
        return_seconds=False
    )
    
    # Convert to seconds and add metadata
    results = []
    for ts in speech_timestamps:
        start_sec = ts['start'] / sr
        end_sec = ts['end'] / sr
        duration = end_sec - start_sec
        
        results.append({
            'start': start_sec,
            'end': end_sec,
            'duration': duration,
            'start_sample': ts['start'],
            'end_sample': ts['end']
        })
    
    logger.info(f"Found {len(results)} speech segments")
    
    if results:
        total_speech = sum(r['duration'] for r in results)
        audio_duration = len(wav) / sr
        coverage = (total_speech / audio_duration) * 100 if audio_duration > 0 else 0
        
        logger.info(f"Total speech: {total_speech:.2f}s")
        logger.info(f"Audio duration: {audio_duration:.2f}s")
        logger.info(f"Speech coverage: {coverage:.1f}%")
    
    return results


def merge_close_segments(segments, max_gap_sec=0.35):
    """
    Merge segments that are close together (hysteresis).
    
    Args:
        segments: List of segment dictionaries with 'start' and 'end'
        max_gap_sec: Maximum gap in seconds to merge
    
    Returns:
        List of merged segments
    """
    if not segments:
        return []
    
    # Sort by start time
    sorted_segs = sorted(segments, key=lambda x: x['start'])
    
    merged = [sorted_segs[0].copy()]
    
    for seg in sorted_segs[1:]:
        last = merged[-1]
        gap = seg['start'] - last['end']
        
        if gap <= max_gap_sec:
            # Merge segments
            last['end'] = seg['end']
            last['duration'] = last['end'] - last['start']
        else:
            merged.append(seg.copy())
    
    return merged


def main():
    """Main execution"""
    try:
        # Load configuration
        config = load_config()
        
        logger = setup_logger(
            "silero_vad",
            log_level=config.log_level,
            log_format=config.log_format,
            log_to_console=config.log_to_console,
            log_to_file=config.log_to_file,
            log_dir=config.log_root
        )
        
        logger.info("=" * 60)
        logger.info("SILERO VAD STAGE")
        logger.info("=" * 60)
        
        # Accept movie directory as command-line argument
        if len(sys.argv) > 1:
            movie_dir = Path(sys.argv[1])
            logger.info(f"Using movie directory from argument: {movie_dir}")
        else:
            # Fallback: Try to use output_root or find movie directory
            output_root = Path(config.output_root)
            
            # Always use output_root directly when it's set (should be job-specific)
            if (output_root / "audio").exists():
                movie_dir = output_root
                logger.info(f"Using output_root as movie directory: {movie_dir}")
            else:
                # Search for any audio.wav in output directory
                logger.info("Searching for audio files in output directory...")
                audio_files = list(output_root.glob("**/audio/audio.wav"))
                if audio_files:
                    audio_file = audio_files[0]
                    movie_dir = audio_file.parent.parent
                    logger.info(f"Found audio file: {audio_file}")
                else:
                    logger.error("No audio files found in output directory")
                    logger.error("Run demux stage first to extract audio")
                    sys.exit(1)
        
        audio_file = movie_dir / "audio" / "audio.wav"
        
        if not audio_file.exists():
            logger.error(f"Audio file not found: {audio_file}")
            sys.exit(1)
        
        logger.info(f"Movie directory: {movie_dir}")
        logger.info(f"Audio file: {audio_file}")
        
        # Create VAD output directory
        vad_dir = movie_dir / "vad"
        vad_dir.mkdir(exist_ok=True)
        
        # Load Silero model
        logger.info("Loading Silero VAD model...")
        model, utils = load_silero_model()
        logger.info("Model loaded successfully")
        
        # Get speech timestamps
        segments = get_speech_timestamps_silero(audio_file, model, utils, config)
        
        # Merge close segments
        logger.info(f"Merging segments with gaps < {config.silero_merge_gap_sec}s")
        merged_segments = merge_close_segments(segments, config.silero_merge_gap_sec)
        logger.info(f"After merging: {len(merged_segments)} segments")
        
        # Save results
        output_file = vad_dir / "silero_segments.json"
        output_data = {
            "audio_file": str(audio_file),
            "model": "silero_vad",
            "parameters": {
                "threshold": config.silero_threshold,
                "min_speech_duration_ms": config.silero_min_speech_duration_ms,
                "min_silence_duration_ms": config.silero_min_silence_duration_ms,
                "merge_gap_sec": config.silero_merge_gap_sec
            },
            "segments": merged_segments,
            "segment_count": len(merged_segments),
            "total_speech_duration": sum(s['duration'] for s in merged_segments)
        }
        
        save_json(output_data, output_file)
        logger.info(f"Saved speech segments to: {output_file}")
        
        logger.info("=" * 60)
        logger.info("SILERO VAD COMPLETE")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Silero VAD failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
