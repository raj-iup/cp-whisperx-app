#!/usr/bin/env python3
"""Stage 5: Pyannote VAD - Refined Voice Activity Detection"""
import sys
import json
import argparse
import os
from pathlib import Path

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest
from pyannote_vad_wrapper import PyannoteVAD, load_secrets


def load_env_config() -> dict:
    """Load configuration from environment variables."""
    return {
        'onset': float(os.getenv('PYANNOTE_ONSET', '0.5')),
        'offset': float(os.getenv('PYANNOTE_OFFSET', '0.5')),
        'min_duration_on': float(os.getenv('PYANNOTE_MIN_DURATION_ON', '0.0')),
        'min_duration_off': float(os.getenv('PYANNOTE_MIN_DURATION_OFF', '0.0')),
        'device': os.getenv('PYANNOTE_DEVICE', 'cpu')
    }


def run_pyannote_vad(
    audio_file: Path,
    coarse_segments_file: Path,
    device: str,
    logger,
    config: dict = None
):
    """
    Run Pyannote VAD for refined speech segmentation.
    
    Args:
        audio_file: Path to audio file
        coarse_segments_file: Path to Silero VAD segments JSON
        device: Device to run on
        logger: Logger instance
        config: Configuration dict with VAD parameters
        
    Returns:
        Tuple of (refined_segments, statistics)
    """
    # Default configuration
    default_config = {
        'onset': 0.5,
        'offset': 0.5,
        'min_duration_on': 0.0,
        'min_duration_off': 0.0,
        'filter_by_coarse': True
    }
    
    if config:
        default_config.update(config)
    
    logger.info(f"Running Pyannote VAD on {device}")
    logger.debug(f"Configuration: {default_config}")
    
    # Load coarse segments from Silero VAD
    if not coarse_segments_file.exists():
        raise FileNotFoundError(f"Coarse segments file not found: {coarse_segments_file}")
    
    with open(coarse_segments_file, 'r') as f:
        silero_data = json.load(f)
    
    coarse_segments = silero_data['segments']
    total_duration = silero_data['statistics']['total_duration']
    
    logger.info(f"Loaded {len(coarse_segments)} segments from Silero VAD")
    logger.info(f"Total audio duration: {total_duration:.2f} seconds")
    
    # Load secrets for HF token
    try:
        secrets = load_secrets()
        hf_token = secrets.get('hf_token') or secrets.get('pyannote_token')
        if not hf_token:
            logger.error("HuggingFace token not found in secrets.json")
            raise ValueError("HuggingFace token required for Pyannote VAD")
    except Exception as e:
        logger.error(f"Failed to load secrets: {e}")
        raise
    
    # Initialize Pyannote VAD
    vad = PyannoteVAD(hf_token=hf_token, device=device, logger=logger)
    
    # Load model
    if not vad.load_model():
        raise RuntimeError("Failed to load Pyannote VAD model")
    
    # Process audio with configuration
    refined_segments, stats = vad.process(
        audio_path=audio_file,
        coarse_segments=coarse_segments,
        total_duration=total_duration,
        onset=default_config['onset'],
        offset=default_config['offset'],
        min_duration_on=default_config['min_duration_on'],
        min_duration_off=default_config['min_duration_off'],
        filter_by_coarse=default_config['filter_by_coarse']
    )
    
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
        
        # Load configuration from environment
        env_config = load_env_config()
        logger.info(f"Configuration: onset={env_config['onset']}, offset={env_config['offset']}, "
                   f"min_duration_on={env_config['min_duration_on']}, "
                   f"min_duration_off={env_config['min_duration_off']}")
        
        # Get device - use env config if specified, otherwise detect
        if env_config['device'].upper() not in ['CPU', 'MPS', 'CUDA']:
            device = get_device(prefer_mps=False, stage_name='pyannote-vad')
        else:
            device = env_config['device'].lower()
        
        logger.log_model_load("Pyannote VAD", device)
        
        import time
        start = time.time()
        
        with StageManifest('pyannote-vad', movie_dir, logger.logger) as manifest:
            # Get paths
            audio_file = movie_dir / 'audio' / 'audio.wav'
            coarse_segments_file = movie_dir / 'vad' / 'silero_segments.json'
            
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            if not coarse_segments_file.exists():
                raise FileNotFoundError(f"Silero segments file not found: {coarse_segments_file}")
            
            logger.debug(f"Audio file: {audio_file}")
            logger.debug(f"Coarse segments: {coarse_segments_file}")
            
            # Run Pyannote VAD with configuration
            refined_segments, stats = run_pyannote_vad(
                audio_file=audio_file,
                coarse_segments_file=coarse_segments_file,
                device=device,
                logger=logger,
                config=env_config
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
                    'onset': env_config['onset'],
                    'offset': env_config['offset'],
                    'min_duration_on': env_config['min_duration_on'],
                    'min_duration_off': env_config['min_duration_off'],
                    'device': device,
                    'method': 'pyannote_vad'
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
            manifest.add_metadata('onset', env_config['onset'])
            manifest.add_metadata('offset', env_config['offset'])
            manifest.add_metadata('method', 'pyannote_vad')
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
