#!/usr/bin/env python3
"""Stage 5: Pyannote VAD - Refined Voice Activity Detection

NOTE: This is currently using a simplified implementation that passes through
Silero VAD segments due to pyannote.audio dependency conflicts.

For full Pyannote VAD functionality, install in a separate environment:
  pip install torch==2.0.1 torchaudio==2.0.2 pyannote.audio==3.0.0
"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest


def load_secrets(secrets_path: Path = None) -> dict:
    """Load secrets from config/secrets.json."""
    if secrets_path is None:
        secrets_path = Path("config/secrets.json")
    
    if not secrets_path.exists():
        raise FileNotFoundError(f"Secrets file not found: {secrets_path}")
    
    with open(secrets_path, 'r') as f:
        secrets = json.load(f)
    
    return secrets


def run_simplified_vad(
    coarse_segments_file: Path,
    logger
):
    """
    Simplified VAD implementation that uses Silero segments.
    
    TODO: Replace with full Pyannote.audio implementation once dependencies are resolved.
    
    Args:
        coarse_segments_file: Path to Silero VAD segments JSON
        logger: Logger instance
        
    Returns:
        Tuple of (refined_segments, statistics)
    """
    logger.warning("Using simplified VAD implementation (Silero segments pass-through)")
    logger.info("Full Pyannote VAD requires resolving dependency conflicts")
    
    # Load coarse segments from Silero VAD
    if not coarse_segments_file.exists():
        raise FileNotFoundError(f"Coarse segments file not found: {coarse_segments_file}")
    
    with open(coarse_segments_file, 'r') as f:
        silero_data = json.load(f)
    
    coarse_segments = silero_data['segments']
    total_duration = silero_data['statistics']['total_duration']
    
    logger.info(f"Loaded {len(coarse_segments)} segments from Silero VAD")
    logger.info(f"Total audio duration: {total_duration:.2f} seconds")
    
    # For now, use Silero segments as-is
    refined_segments = coarse_segments
    
    # Calculate statistics
    speech_duration = sum(seg['end'] - seg['start'] for seg in refined_segments)
    speech_ratio = speech_duration / total_duration if total_duration > 0 else 0.0
    
    stats = {
        'total_duration': total_duration,
        'num_segments': len(refined_segments),
        'speech_duration': speech_duration,
        'speech_ratio': speech_ratio,
        'avg_segment_duration': speech_duration / len(refined_segments) if refined_segments else 0.0,
        'device': 'cpu',
        'method': 'silero_passthrough',
        'note': 'Using Silero VAD segments directly due to Pyannote dependency issues'
    }
    
    logger.info(f"Refined segments: {len(refined_segments)}")
    logger.info(f"Speech ratio: {stats['speech_ratio']:.1%}")
    
    return refined_segments, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('pyannote-vad', movie_name)
    
    try:
        logger.log_stage_start("Pyannote VAD - Refined speech segmentation")
        
        # Load secrets for documentation (not used in simplified version)
        try:
            secrets = load_secrets()
            hf_token = secrets.get('hf_token') or secrets.get('pyannote_token')
            if hf_token:
                logger.info(f"HuggingFace token available (not used in simplified version)")
        except Exception as e:
            logger.warning(f"Could not load secrets: {e}")
        
        device = get_device(prefer_mps=False, stage_name='pyannote-vad')
        logger.log_model_load("Pyannote VAD (simplified)", device)
        
        import time
        start = time.time()
        
        with StageManifest('pyannote-vad', movie_dir, logger.logger) as manifest:
            coarse_segments_file = movie_dir / 'vad' / 'silero_segments.json'
            
            if not coarse_segments_file.exists():
                raise FileNotFoundError(f"Silero segments file not found: {coarse_segments_file}")
            
            logger.debug(f"Coarse segments: {coarse_segments_file}")
            
            # Run simplified VAD
            refined_segments, stats = run_simplified_vad(
                coarse_segments_file=coarse_segments_file,
                logger=logger
            )
            
            duration = time.time() - start
            
            # Log results
            logger.log_processing("VAD refinement complete", duration)
            logger.log_metric("Refined segments", len(refined_segments))
            logger.log_metric("Total duration", f"{stats['total_duration']:.2f}", "seconds")
            logger.log_metric("Speech duration", f"{stats['speech_duration']:.2f}", "seconds")
            logger.log_metric("Speech ratio", f"{stats['speech_ratio']:.1%}")
            
            # Create output directory
            vad_dir = movie_dir / 'vad'
            vad_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"VAD directory: {vad_dir}")
            
            # Save refined segments
            output_file = vad_dir / 'pyannote_segments.json'
            output_data = {
                'segments': refined_segments,
                'statistics': stats,
                'config': {
                    'method': 'silero_passthrough',
                    'note': 'Simplified implementation pending Pyannote dependency resolution'
                }
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            
            logger.log_file_operation("Saved Pyannote VAD segments", output_file, success=True)
            
            # Add to manifest
            manifest.add_output('segments', output_file, 'Pyannote VAD refined segments')
            manifest.add_metadata('device', device)
            manifest.add_metadata('segment_count', len(refined_segments))
            manifest.add_metadata('speech_ratio', stats['speech_ratio'])
            manifest.add_metadata('total_duration', stats['total_duration'])
            manifest.add_metadata('method', 'silero_passthrough')
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
