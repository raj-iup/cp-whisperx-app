#!/usr/bin/env python3
"""
PyAnnote VAD Step
Context-aware voice activity detection refinement.
Uses local PyAnnote.audio for VAD processing with chunking support.

Input: Silero VAD segments JSON + 16kHz mono audio
Output: Refined speech segments JSON

Phase 2 Enhancement: Native PyTorch execution support
"""
import sys
import warnings

# Suppress known deprecation warnings from dependencies
warnings.filterwarnings('ignore', message='.*speechbrain.pretrained.*deprecated.*')
warnings.filterwarnings('ignore', message='.*pytorch_lightning.*ModelCheckpoint.*')
import json
from pathlib import Path
import time
import soundfile as sf
import numpy as np
import tempfile
import os

# ============================================================================
# PHASE 2: Native Execution Mode Check
# ============================================================================
def verify_pytorch_availability():
    """Verify PyTorch is available in native or Docker environment.
    
    Phase 2 Enhancement: Containers no longer include PyTorch in image.
    PyTorch is provided by native .bollyenv environment for optimal performance.
    """
    execution_mode = os.getenv('EXECUTION_MODE', 'docker')
    
    try:
        import torch
        
        # Set UTF-8 encoding for Windows console output
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        
        # Verify CUDA availability if expected
        cuda_available = torch.cuda.is_available()
        device_name = torch.cuda.get_device_name(0) if cuda_available else "CPU"
        
        print(f"[OK] PyTorch {torch.__version__} available")
        print(f"[OK] Execution mode: {execution_mode}")
        print(f"[OK] Device: {device_name}")
        
        return True
        
    except ImportError as e:
        print("=" * 70)
        print("ERROR: PyTorch not available")
        print("=" * 70)
        print(f"Execution mode: {execution_mode}")
        print("")
        
        if execution_mode == 'native':
            print("Native execution mode requires bootstrap:")
            print("  1. Run: ./scripts/bootstrap.ps1")
            print("  2. Ensure .bollyenv volume mounted in docker-compose.yml")
            print("  3. Check PATH includes: /app/.bollyenv/bin")
        else:
            print("Docker execution mode requires PyTorch in image:")
            print("  - This image is SLIM (no PyTorch)")
            print("  - Use native mode or rebuild with full image")
        
        print("=" * 70)
        sys.exit(1)

# Verify PyTorch before proceeding
verify_pytorch_availability()
# ============================================================================

sys.path.insert(0, '/app/shared')
from config import load_config
from logger import setup_logger
from utils import save_json, get_movie_dir, load_json


def chunk_spans(duration: float, win: float, pad: float):
    """Generate chunk spans for audio processing."""
    spans = []
    t = 0.0
    while t < duration:
        s = max(0.0, t - pad)
        e = min(duration, t + win + pad)
        spans.append((s, e))
        t += win
    return spans


def write_wav_slice(audio: np.ndarray, sr: int, s: float, e: float):
    """Write audio slice to temporary WAV file."""
    si, ei = int(s*sr), int(e*sr)
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(path, audio[si:ei], sr)
    return path


def run_vad_local_chunk(chunk_path: Path, pipeline, logger):
    """
    Run local PyAnnote VAD on a single chunk.
    
    Args:
        chunk_path: Path to audio chunk file
        pipeline: PyAnnote VAD pipeline
        logger: Logger instance
    
    Returns:
        List of speech segments with timestamps (relative to chunk)
    """
    try:
        # Run VAD on chunk
        vad_result = pipeline(str(chunk_path))
        
        # Extract segments
        segments = []
        for segment in vad_result.itersegments():
            segments.append((float(segment.start), float(segment.end)))
        
        return segments
        
    except Exception as e:
        raise RuntimeError(f"Local PyAnnote VAD failed: {e}")


def run_vad_local_chunked(audio_path: Path, pipeline, logger, chunk_win=45.0, chunk_pad=0.25):
    """
    Run local PyAnnote VAD with chunking to handle large files.
    
    Args:
        audio_path: Path to audio file
        pipeline: PyAnnote VAD pipeline
        logger: Logger instance
        chunk_win: Chunk window size in seconds
        chunk_pad: Chunk padding in seconds
    
    Returns:
        List of speech segments with timestamps
    """
    # Load audio
    audio_data, sr = sf.read(str(audio_path))
    if audio_data.ndim > 1:
        audio_data = audio_data.mean(axis=1)
    audio_data = audio_data.astype("float32")
    
    duration = len(audio_data) / sr
    logger.info(f"Audio: {duration:.2f}s @ {sr} Hz (mono)")
    
    # Generate chunks
    spans = chunk_spans(duration, chunk_win, chunk_pad)
    logger.info(f"Processing in {len(spans)} chunks (win={chunk_win}s, pad={chunk_pad}s)")
    
    all_segments = []
    for idx, (s, e) in enumerate(spans, 1):
        tmp = write_wav_slice(audio_data, sr, s, e)
        try:
            logger.info(f"Processing chunk {idx}/{len(spans)} ({s:.1f}s-{e:.1f}s)...")
            segs = run_vad_local_chunk(Path(tmp), pipeline, logger)
            
            # Rebase segments to absolute time
            rebased = [(s + a, s + b) for a, b in segs]
            all_segments.extend(rebased)
            
            logger.info(f"Chunk {idx}/{len(spans)}: {len(segs)} segment(s)")
        except Exception as ex:
            logger.warning(f"Chunk {idx} failed: {ex}")
        finally:
            try:
                os.remove(tmp)
            except Exception:
                pass
    
    return all_segments


def convert_segments_to_dict_format(segments: list) -> list:
    """
    Convert tuple segments to dictionary format.
    
    Args:
        segments: List of (start, end) tuples
    
    Returns:
        List of segment dictionaries
    """
    result = []
    for start, end in segments:
        result.append({
            'start': start,
            'end': end,
            'duration': end - start,
            'confidence': 1.0,
            'source': 'pyannote_local'
        })
    return result


def expand_segment(segment, pad_sec=0.25):
    """Expand segment boundaries by padding"""
    return {
        'start': max(0, segment['start'] - pad_sec),
        'end': segment['end'] + pad_sec,
        'original_start': segment['start'],
        'original_end': segment['end']
    }


def refine_segment_with_pyannote_local(audio_path: Path, segments: list, pipeline, logger, chunk_win=45.0, chunk_pad=0.25):
    """
    Refine segments using local PyAnnote VAD with chunking.
    
    Args:
        audio_path: Path to audio file
        segments: List of Silero segments (not used, processes full audio)
        pipeline: PyAnnote VAD pipeline
        logger: Logger instance
        chunk_win: Chunk window size in seconds
        chunk_pad: Chunk padding in seconds
    
    Returns:
        List of refined segments from local VAD
    """
    # Run local VAD with chunking
    segment_tuples = run_vad_local_chunked(audio_path, pipeline, logger, chunk_win, chunk_pad)
    
    # Convert to dictionary format
    refined_segments = convert_segments_to_dict_format(segment_tuples)
    
    return refined_segments


def refine_segment_with_pyannote(audio_path: Path, segment: dict, pipeline, config):
    """
    Refine a single segment using PyAnnote VAD.
    DEPRECATED: Kept for compatibility, no longer used with API approach.
    """
    pass


def merge_close_segments(segments, max_gap_sec=0.2):
    """
    Merge segments that are close together.
    
    Args:
        segments: List of segment dictionaries
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
            # Keep the higher confidence
            if 'confidence' in seg and 'confidence' in last:
                last['confidence'] = max(last['confidence'], seg['confidence'])
        else:
            merged.append(seg.copy())
    
    return merged


def main():
    """Main execution"""
    try:
        # Load configuration
        config = load_config()
        
        logger = setup_logger(
            "pyannote_vad",
            log_level=config.log_level,
            log_format=config.log_format,
            log_to_console=config.log_to_console,
            log_to_file=config.log_to_file,
            log_dir=config.log_root
        )
        
        logger.info("=" * 60)
        logger.info("PYANNOTE VAD STAGE (Local Processing)")
        logger.info("=" * 60)
        
        # Initialize device (will be set based on config or fallback to CPU)
        device = config.get('pyannote_device', config.get('device', 'cpu'))
        
        # Load PyAnnote VAD pipeline
        logger.info("Loading PyAnnote VAD pipeline...")
        try:
            from pyannote.audio import Pipeline
            
            # Use HF_HOME and TORCH_HOME from environment (set by bootstrap)
            # This allows bootstrap to control cache location
            import os
            # Environment variables are already set by bootstrap scripts
            # Just log what we're using
            hf_home = os.environ.get('HF_HOME', str(Path.home() / '.cache' / 'huggingface'))
            torch_home = os.environ.get('TORCH_HOME', str(Path.home() / '.cache' / 'torch'))
            logger.info(f"Using HF_HOME: {hf_home}")
            logger.info(f"Using TORCH_HOME: {torch_home}")
            
            # Get HuggingFace token from config secrets
            hf_token = None
            if hasattr(config, 'hf_token'):
                hf_token = config.hf_token
                logger.info("Using HuggingFace token from config")
            else:
                logger.warning("No HuggingFace token found in config")
                logger.warning("Note: PyAnnote models are gated and require HF authentication")
            
            # Load VAD pipeline with auth token
            # Note: newer huggingface_hub uses 'token' parameter instead of 'use_auth_token'
            if hf_token:
                try:
                    vad_pipeline = Pipeline.from_pretrained(
                        "pyannote/voice-activity-detection",
                        token=hf_token,
                        cache_dir=hf_home
                    )
                except TypeError:
                    # Fallback for older versions that still use use_auth_token
                    vad_pipeline = Pipeline.from_pretrained(
                        "pyannote/voice-activity-detection",
                        use_auth_token=hf_token,
                        cache_dir=hf_home
                    )
            else:
                # Try without token (may fail for gated models)
                vad_pipeline = Pipeline.from_pretrained(
                    "pyannote/voice-activity-detection",
                    cache_dir=hf_home
                )
            
            # Configure pipeline with hyperparameters
            try:
                vad_pipeline.instantiate({
                    "onset": config.get('pyannote_onset', 0.5),
                    "offset": config.get('pyannote_offset', 0.5),
                    "min_duration_on": config.get('pyannote_min_duration_on', 0.0),
                    "min_duration_off": config.get('pyannote_min_duration_off', 0.0)
                })
                logger.info(f"Configured PyAnnote VAD pipeline with onset={config.get('pyannote_onset', 0.5)}, "
                           f"offset={config.get('pyannote_offset', 0.5)}, "
                           f"min_duration_on={config.get('pyannote_min_duration_on', 0.0)}, "
                           f"min_duration_off={config.get('pyannote_min_duration_off', 0.0)}")
            except Exception as e:
                logger.warning(f"Could not configure pipeline hyperparameters: {e}")
                logger.info("Using default hyperparameters")
            
            # Try to move to GPU if available
            if device and device.lower() != 'cpu':
                try:
                    vad_pipeline.to(device)
                    logger.info(f"PyAnnote VAD pipeline loaded on device: {device}")
                except Exception as e:
                    logger.warning(f"Could not move pipeline to {device}: {e}")
                    logger.info("Using CPU instead")
                    device = "cpu"
            else:
                logger.info(f"PyAnnote VAD pipeline loaded on device: cpu")
                device = "cpu"
        except Exception as e:
            logger.error(f"Failed to load PyAnnote VAD pipeline: {e}")
            logger.warning("=" * 60)
            logger.warning("FALLBACK: Using Silero segments")
            logger.warning("=" * 60)
            logger.warning(f"PyAnnote VAD pipeline loading failed: {e}")
            logger.warning("Falling back to Silero VAD segments.")
            logger.warning("=" * 60)
            vad_pipeline = None
        
        # Accept movie directory as command-line argument
        if len(sys.argv) > 1:
            movie_dir = Path(sys.argv[1])
            logger.info(f"Using movie directory from argument: {movie_dir}")
        else:
            # Fallback: Try to use output_root or find movie directory
            output_root = Path(config.output_root)
            
            # Always use output_root directly when it's set (should be job-specific)
            if (output_root / "vad").exists():
                movie_dir = output_root
                logger.info(f"Using output_root as movie directory: {movie_dir}")
            else:
                # Try to find VAD directory with Silero segments
                vad_dirs = list(output_root.glob("**/vad"))
                if not vad_dirs:
                    logger.error("No VAD directory found in output")
                    logger.error("Run Silero VAD stage first")
                    sys.exit(1)
                
                vad_dir = vad_dirs[0]
                movie_dir = vad_dir.parent
                logger.info(f"Found VAD directory: {vad_dir}")
        
        logger.info(f"Movie directory: {movie_dir}")
        vad_dir = movie_dir / "vad"
        
        # Load Silero segments (for statistics comparison)
        silero_file = vad_dir / "silero_segments.json"
        silero_segments = []
        if silero_file.exists():
            silero_data = load_json(silero_file)
            if silero_data:
                silero_segments = silero_data.get('segments', [])
                logger.info(f"Loaded {len(silero_segments)} Silero segments for comparison")
            else:
                logger.warning("Silero segments file is empty or invalid - will process full audio")
        else:
            logger.warning("Silero segments not found - will process full audio")
        
        # Get audio file
        audio_file = movie_dir / "audio" / "audio.wav"
        if not audio_file.exists():
            logger.error(f"Audio file not found: {audio_file}")
            sys.exit(1)
        
        logger.info(f"Audio file: {audio_file}")
        
        # Get audio duration for statistics
        audio_info = sf.info(str(audio_file))
        total_duration = audio_info.duration
        logger.info(f"Audio duration: {total_duration:.2f}s")
        
        # Process with local PyAnnote VAD (with chunking)
        if vad_pipeline is not None:
            logger.info("Processing with local PyAnnote VAD (chunked)...")
            
            start_time = time.time()
            try:
                # Get chunking parameters from config or use defaults
                chunk_win = config.get('pyannote_chunk_win', 45.0)
                chunk_pad = config.get('pyannote_chunk_pad', 0.25)
                
                # Process audio with local PyAnnote VAD using chunking
                refined_segments = refine_segment_with_pyannote_local(
                    audio_file, 
                    silero_segments,
                    vad_pipeline,
                    logger,
                    chunk_win=chunk_win,
                    chunk_pad=chunk_pad
                )
                process_time = time.time() - start_time
                
            except Exception as e:
                logger.error(f"PyAnnote local VAD processing failed: {e}")
                logger.warning("=" * 60)
                logger.warning("FALLBACK: Using Silero segments")
                logger.warning("=" * 60)
                logger.warning(f"PyAnnote local VAD processing failed: {e}")
                logger.warning("Falling back to Silero VAD segments.")
                logger.warning("=" * 60)
                
                # Convert Silero segments to PyAnnote format
                refined_segments = []
                for seg in silero_segments:
                    refined_segments.append({
                        'start': seg.get('start', 0),
                        'end': seg.get('end', 0),
                        'duration': seg.get('duration', seg.get('end', 0) - seg.get('start', 0)),
                        'confidence': seg.get('confidence', 1.0),
                        'source': 'silero_vad_fallback'
                    })
                process_time = 0.0
        else:
            # Pipeline not loaded - use Silero segments
            logger.info("Using Silero segments as fallback...")
            refined_segments = []
            for seg in silero_segments:
                refined_segments.append({
                    'start': seg.get('start', 0),
                    'end': seg.get('end', 0),
                    'duration': seg.get('duration', seg.get('end', 0) - seg.get('start', 0)),
                    'confidence': seg.get('confidence', 1.0),
                    'source': 'silero_vad_fallback'
                })
            process_time = 0.0
        
        logger.info(f"API processing completed in {process_time:.2f}s")
        logger.info(f"Generated {len(refined_segments)} refined segments")
        
        # Merge close segments
        merge_gap = config.get('pyannote_merge_gap', 0.2)
        logger.info(f"Merging segments with gaps < {merge_gap}s")
        merged_segments = merge_close_segments(refined_segments, merge_gap)
        logger.info(f"After merging: {len(merged_segments)} segments")
        
        # Calculate statistics
        total_speech = sum(s['duration'] for s in merged_segments)
        
        # Save results
        output_file = vad_dir / "pyannote_segments.json"
        # Determine model name based on source
        model_name = "PyAnnote.audio (local)"
        if merged_segments and merged_segments[0].get('source') == 'silero_vad_fallback':
            model_name = "Silero VAD (fallback)"
        elif vad_pipeline is not None:
            model_name = f"PyAnnote.audio (local, {device})"
        
        output_data = {
            "audio_file": str(audio_file),
            "model": model_name,
            "source_segments": str(silero_file) if silero_file.exists() else None,
            "parameters": {
                "onset": config.get('pyannote_onset', 0.5),
                "offset": config.get('pyannote_offset', 0.5),
                "min_duration_on": config.get('pyannote_min_duration_on', 0.0),
                "min_duration_off": config.get('pyannote_min_duration_off', 0.0),
                "device": device,
                "merge_gap_sec": merge_gap,
                "api_process_time": process_time,
                "chunk_win": config.get('pyannote_chunk_win', 45.0),
                "chunk_pad": config.get('pyannote_chunk_pad', 0.25)
            },
            "segments": merged_segments,
            "segment_count": len(merged_segments),
            "total_speech_duration": total_speech,
            "total_audio_duration": total_duration,
            "speech_ratio": total_speech / total_duration if total_duration > 0 else 0,
            "silero_segment_count": len(silero_segments),
            "comparison_ratio": len(merged_segments) / len(silero_segments) if silero_segments else 1.0
        }
        
        save_json(output_data, output_file)
        logger.info(f"Saved refined segments to: {output_file}")
        
        logger.info("=" * 60)
        logger.info(f"PYANNOTE VAD COMPLETE ({model_name})")
        logger.info("=" * 60)
        logger.info(f"Total speech duration: {total_speech:.2f}s ({output_data['speech_ratio']*100:.1f}%)")
        logger.info(f"Segment count: {len(merged_segments)}")
        logger.info(f"Silero segments: {len(silero_segments)}")
        logger.info(f"Processing time: {process_time:.2f}s")
        
        return 0
        
    except Exception as e:
        logger.error(f"PyAnnote VAD failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    sys.exit(main())
