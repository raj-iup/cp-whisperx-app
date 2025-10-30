#!/usr/bin/env python3
"""Stage 4: Silero VAD - Voice Activity Detection"""
import sys
import json
import argparse
from pathlib import Path

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest
from silero_vad_wrapper import SileroVAD

def run_vad(audio_file, device, logger, config=None):
    """
    Run Silero VAD for coarse speech segmentation.
    
    Args:
        audio_file: Path to audio file
        device: Device to run on (cpu, mps, cuda)
        logger: Logger instance
        config: Optional config dict with VAD parameters
        
    Returns:
        List of speech segments
    """
    # Default configuration
    default_config = {
        'threshold': 0.5,
        'min_speech_duration_ms': 250,
        'min_silence_duration_ms': 100,
        'merge_gap': 0.35,
        'min_segment_duration': 0.3
    }
    
    if config:
        default_config.update(config)
    
    logger.info(f"Running Silero VAD on {device}")
    logger.debug(f"Configuration: {default_config}")
    logger.debug(f"Processing audio file: {audio_file}")
    
    import time
    start = time.time()
    
    try:
        # Initialize VAD
        vad = SileroVAD(device=device, logger=logger)
        
        # Process audio
        segments, stats = vad.process(
            audio_file,
            threshold=default_config['threshold'],
            min_speech_duration_ms=default_config['min_speech_duration_ms'],
            min_silence_duration_ms=default_config['min_silence_duration_ms'],
            merge_gap=default_config['merge_gap'],
            min_segment_duration=default_config['min_segment_duration']
        )
        
        duration = time.time() - start
        
        # Log results
        logger.log_processing("VAD segmentation complete", duration)
        logger.log_metric("Speech segments detected", len(segments))
        logger.log_metric("Total duration", f"{stats['total_duration']:.2f}", "seconds")
        logger.log_metric("Speech duration", f"{stats['speech_duration']:.2f}", "seconds")
        logger.log_metric("Speech ratio", f"{stats['speech_ratio']:.1%}")
        
        # Log sample segments
        if segments and len(segments) > 0:
            logger.info(f"First segment: {segments[0]['start']:.2f}s - {segments[0]['end']:.2f}s")
            if len(segments) > 1:
                logger.info(f"Last segment: {segments[-1]['start']:.2f}s - {segments[-1]['end']:.2f}s")
        
        return segments, stats
        
    except Exception as e:
        logger.error(f"VAD processing failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--movie-dir', required=True)
    parser.add_argument('--threshold', type=float, default=0.5, help='Speech detection threshold')
    parser.add_argument('--min-speech-ms', type=int, default=250, help='Min speech duration (ms)')
    parser.add_argument('--merge-gap', type=float, default=0.35, help='Max gap to merge (seconds)')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    logger = NativePipelineLogger('silero-vad', movie_name)
    
    try:
        logger.log_stage_start("Silero VAD - Coarse speech segmentation")
        
        device = get_device(prefer_mps=True, stage_name='silero-vad')
        logger.log_model_load("Silero VAD v4", device)
        
        # Prepare config
        config = {
            'threshold': args.threshold,
            'min_speech_duration_ms': args.min_speech_ms,
            'merge_gap': args.merge_gap
        }
        
        with StageManifest('silero-vad', movie_dir, logger.logger) as manifest:
            audio_file = movie_dir / 'audio' / 'audio.wav'
            
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            logger.debug(f"Input audio: {audio_file}")
            logger.info(f"Audio file size: {audio_file.stat().st_size / (1024*1024):.1f} MB")
            
            # Run VAD
            segments, stats = run_vad(audio_file, device, logger, config)
            
            # Create output directory
            vad_dir = movie_dir / 'vad'
            vad_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created VAD directory: {vad_dir}")
            
            # Save segments
            output_file = vad_dir / 'silero_segments.json'
            output_data = {
                'segments': segments,
                'statistics': stats,
                'config': config
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2)
            
            logger.log_file_operation("Saved Silero VAD segments", output_file, success=True)
            
            # Add to manifest
            manifest.add_output('segments', output_file, 'Silero VAD segments')
            manifest.add_metadata('device', device)
            manifest.add_metadata('segment_count', len(segments))
            manifest.add_metadata('speech_ratio', stats['speech_ratio'])
            manifest.add_metadata('total_duration', stats['total_duration'])
            manifest.add_metadata('threshold', config['threshold'])
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise

if __name__ == '__main__':
    main()
