#!/usr/bin/env python3
"""Stage 7: WhisperX ASR + Forced Alignment

NOTE: Due to WhisperX dependency conflicts, this uses faster-whisper directly.
Provides transcription without word-level alignment but avoids dependency issues.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

sys.path.insert(0, 'native/utils')
from device_manager import get_device
from native_logger import NativePipelineLogger
from manifest import StageManifest
from simplified_asr_wrapper import SimplifiedASR, load_secrets


def run_asr(
    audio_file: Path,
    speaker_segments_file: Optional[Path],
    device: str,
    logger,
    config: dict = None
):
    """
    Run WhisperX ASR for speech-to-text transcription.
    
    Args:
        audio_file: Path to audio file
        speaker_segments_file: Path to speaker segments JSON
        device: Device to run on (cpu, mps, cuda)
        logger: Logger instance
        config: Optional config dict
        
    Returns:
        Tuple of (transcription_result, statistics)
    """
    # Default configuration
    default_config = {
        'model_name': 'base',
        'compute_type': 'float32',
        'language': None,  # Auto-detect
        'batch_size': 16
    }
    
    if config:
        default_config.update(config)
    
    logger.info(f"Running Faster-Whisper ASR on {device}")
    logger.info("Note: Using simplified ASR (faster-whisper) due to WhisperX dependency conflicts")
    logger.debug(f"Configuration: {default_config}")
    logger.info(f"Model: {default_config['model_name']}")
    
    # Load speaker segments if available
    speaker_segments = None
    if speaker_segments_file and speaker_segments_file.exists():
        with open(speaker_segments_file, 'r') as f:
            speaker_data = json.load(f)
        speaker_segments = speaker_data.get('segments', [])
        logger.info(f"Loaded {len(speaker_segments)} speaker segments")
    else:
        logger.warning("No speaker segments found, transcription will not have speaker labels")
    
    import time
    start = time.time()
    
    try:
        # Initialize Simplified ASR
        asr = SimplifiedASR(
            model_name=default_config['model_name'],
            device=device,
            compute_type=default_config['compute_type'],
            language=default_config['language'],
            logger=logger
        )
        
        # Process audio
        result, stats = asr.process(
            audio_path=audio_file,
            speaker_segments=speaker_segments,
            batch_size=default_config['batch_size']
        )
        
        # Cleanup
        asr.cleanup()
        
        duration = time.time() - start
        
        # Log results
        logger.log_processing("ASR and alignment complete", duration)
        logger.log_metric("Transcribed segments", stats['num_segments'])
        logger.log_metric("Total words", stats['total_words'])
        logger.log_metric("Language", stats['language'])
        
        return result, stats
        
    except Exception as e:
        logger.error(f"ASR processing failed: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input video file')
    parser.add_argument('--movie-dir', required=True, help='Movie output directory')
    parser.add_argument('--model', default='base', 
                       choices=['tiny', 'base', 'small', 'medium', 'large-v2', 'large-v3'],
                       help='Whisper model size')
    parser.add_argument('--language', help='Language code (e.g., en, hi, es)')
    parser.add_argument('--batch-size', type=int, default=16, help='Batch size')
    parser.add_argument('--compute-type', default='float32',
                       choices=['float16', 'float32', 'int8'],
                       help='Computation precision')
    parser.add_argument('--log-level', default=None,
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Logging level')
    args = parser.parse_args()
    
    movie_dir = Path(args.movie_dir)
    movie_name = movie_dir.name
    
    # Use LOG_LEVEL from environment or argument
    log_level = args.log_level or os.getenv('LOG_LEVEL', 'INFO')
    logger = NativePipelineLogger('asr', movie_name, log_level=log_level)
    
    try:
        logger.log_stage_start("Faster-Whisper ASR (Simplified)")
        
        device = get_device(prefer_mps=False, stage_name='asr')  # Prefer CPU for faster-whisper
        logger.log_model_load(f"Faster-Whisper ({args.model})", device)
        
        # Prepare config
        config = {
            'model_name': args.model,
            'compute_type': args.compute_type,
            'language': args.language,
            'batch_size': args.batch_size
        }
        
        with StageManifest('asr', movie_dir, logger.logger) as manifest:
            audio_file = movie_dir / 'audio' / 'audio.wav'
            speaker_segments_file = movie_dir / 'diarization' / 'speaker_segments.json'
            
            if not audio_file.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")
            
            logger.debug(f"Input audio: {audio_file}")
            logger.info(f"Audio file size: {audio_file.stat().st_size / (1024*1024):.1f} MB")
            
            # Run ASR
            result, stats = run_asr(
                audio_file=audio_file,
                speaker_segments_file=speaker_segments_file,
                device=device,
                logger=logger,
                config=config
            )
            
            # Create output directory
            trans_dir = movie_dir / 'transcription'
            trans_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Transcription directory: {trans_dir}")
            
            # Save transcript
            output_file = trans_dir / 'transcript.json'
            output_data = {
                'segments': result.get('segments', []),
                'language': result.get('language', 'unknown'),
                'statistics': stats,
                'config': config
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            logger.log_file_operation("Saved transcript", output_file, success=True)
            
            # Save human-readable transcript
            txt_file = trans_dir / 'transcript.txt'
            with open(txt_file, 'w', encoding='utf-8') as f:
                for segment in result.get('segments', []):
                    speaker = segment.get('speaker', 'UNKNOWN')
                    text = segment.get('text', '').strip()
                    start = segment.get('start', 0)
                    f.write(f"[{start:.2f}s] {speaker}: {text}\n")
            
            logger.log_file_operation("Saved text transcript", txt_file, success=True)
            
            # Add to manifest
            manifest.add_output('transcript', output_file, 'Full transcript with timestamps')
            manifest.add_output('transcript_txt', txt_file, 'Human-readable transcript')
            manifest.add_metadata('device', device)
            manifest.add_metadata('model_name', config['model_name'])
            manifest.add_metadata('language', stats['language'])
            manifest.add_metadata('num_segments', stats['num_segments'])
            manifest.add_metadata('total_words', stats['total_words'])
            manifest.add_metadata('has_alignment', stats['has_alignment'])
            manifest.add_metadata('has_speakers', stats['has_speakers'])
        
        logger.log_stage_end(success=True)
        
    except Exception as e:
        logger.error(f"Stage failed with error: {e}")
        logger.log_stage_end(success=False)
        raise


if __name__ == '__main__':
    main()
